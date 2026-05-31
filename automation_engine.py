import datetime
import json
import subprocess
import threading
from pathlib import Path

import requests

from morpho_core.code_agent import code_agent
from morpho_core.config import Config
from morpho_core.permission_manager import permission_manager


class AutomationEngine:
    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.logs_path = Path(dirs["logs"]) / "automation.jsonl"
        self.stop_event = threading.Event()

    def _log(self, workflow: str, step: str, status: str, detail: dict) -> dict:
        entry = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "workflow": workflow,
            "step": step,
            "status": status,
            "detail": detail,
        }
        with self.logs_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        permission_manager.log_action("automation_engine.step", entry, status=status)
        return entry

    def stop(self) -> dict:
        self.stop_event.set()
        return {"status": "stopping"}

    def execute_workflow(self, workflow_name: str, steps: list[dict]) -> dict:
        self.stop_event.clear()
        results = []
        for step in steps:
            if self.stop_event.is_set():
                results.append(self._log(workflow_name, step.get("action", "unknown"), "stopped", step))
                break
            action = step.get("action")
            if action == "create_folder":
                permission = permission_manager.request_permission("create_folder", step, destructive=False)
                if not permission["approved"]:
                    return {"status": "pending_permission", "permission": permission["request"], "results": results}
                Path(step["path"]).mkdir(parents=True, exist_ok=True)
                results.append(self._log(workflow_name, action, "completed", step))
            elif action == "create_file":
                response = code_agent.modify_file(step["path"], {"mode": "replace", "content": step.get("content", "")})
                if response.get("status") == "pending_permission":
                    return {"status": "pending_permission", "permission": response["permission"], "results": results}
                results.append(self._log(workflow_name, action, "completed", response))
            elif action == "run_command":
                permission = permission_manager.request_permission("run_command", step, destructive=False)
                if not permission["approved"]:
                    return {"status": "pending_permission", "permission": permission["request"], "results": results}
                completed = subprocess.run(step["command"], cwd=step.get("cwd"), capture_output=True, text=True, shell=False, timeout=120)
                results.append(
                    self._log(
                        workflow_name,
                        action,
                        "completed" if completed.returncode == 0 else "failed",
                        {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr},
                    )
                )
            elif action == "fetch_url":
                permission = permission_manager.request_permission("fetch_url", step, destructive=False)
                if not permission["approved"]:
                    return {"status": "pending_permission", "permission": permission["request"], "results": results}
                response = requests.get(step["url"], timeout=20)
                results.append(self._log(workflow_name, action, "completed", {"url": step["url"], "status_code": response.status_code}))
            else:
                results.append(self._log(workflow_name, action or "unknown", "skipped", step))
        return {"status": "success", "workflow": workflow_name, "results": results}

    def setup_python_project(self, path: str, package_name: str = "app") -> dict:
        steps = [
            {"action": "create_folder", "path": path},
            {"action": "create_folder", "path": str(Path(path) / package_name)},
            {"action": "create_file", "path": str(Path(path) / "README.md"), "content": f"# {package_name}\n"},
            {"action": "create_file", "path": str(Path(path) / package_name / "__init__.py"), "content": ""},
            {"action": "create_file", "path": str(Path(path) / "requirements.txt"), "content": "pytest\n"},
        ]
        return self.execute_workflow("setup_python_project", steps)

    def read_logs(self, limit: int = 100) -> list[dict]:
        if not self.logs_path.exists():
            return []
        lines = self.logs_path.read_text(encoding="utf-8").splitlines()[-limit:]
        results = []
        for line in lines:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return results


automation_engine = AutomationEngine()
