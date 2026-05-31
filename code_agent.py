import json
import subprocess
from pathlib import Path

from morpho_core.ai_adapter import ai_talk
from morpho_core.config import Config
from morpho_core.permission_manager import permission_manager


class CodeAgent:
    def _safe_read(self, path: Path) -> str:
        data = path.read_text(encoding="utf-8", errors="ignore")
        return data[: Config.CODE_AGENT_MAX_FILE_BYTES]

    def analyze_codebase(self, path: str) -> dict:
        root = Path(path)
        if not root.exists():
            raise FileNotFoundError("path not found")
        files = []
        for item in root.rglob("*"):
            if item.is_file():
                files.append({"path": str(item), "size": item.stat().st_size})
            if len(files) >= 100:
                break
        summary_prompt = (
            "Analyze this codebase snapshot and describe structure, likely stack, risks, and next improvements.\n"
            f"Files: {json.dumps(files[:40])}"
        )
        analysis = ai_talk(summary_prompt, use_external=False, system_prompt="You are a precise local code review assistant.")
        permission_manager.log_action("code_agent.analyze_codebase", {"path": path, "file_count": len(files)}, status="completed")
        return {"path": path, "files": files, "analysis": analysis.get("response_text", "")}

    def modify_file(self, path: str, changes: dict) -> dict:
        file_path = Path(path)
        original = self._safe_read(file_path) if file_path.exists() else ""
        permission = permission_manager.request_permission(
            "modify_file",
            {"path": path, "changes": changes},
            destructive=False,
        )
        if not permission["approved"]:
            return {"status": "pending_permission", "permission": permission["request"]}

        mode = changes.get("mode", "replace")
        content = changes.get("content", "")
        if mode == "append":
            new_content = original + content
        elif mode == "prepend":
            new_content = content + original
        else:
            new_content = content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(new_content, encoding="utf-8")
        permission_manager.log_action("code_agent.modify_file", {"path": path, "mode": mode}, status="completed")
        return {"status": "success", "path": path, "bytes_written": len(new_content.encode("utf-8"))}

    def generate_module(self, description: str, output_path: str | None = None) -> dict:
        prompt = (
            "Generate a clean Python module with comments and safe defaults for this description:\n"
            f"{description}"
        )
        result = ai_talk(prompt, use_external=False, system_prompt="You are a senior Python engineer generating production-ready modules.")
        module_text = result.get("response_text", "")
        payload = {"description": description, "output_path": output_path}
        permission = permission_manager.request_permission("generate_module", payload, destructive=False)
        if not permission["approved"]:
            return {"status": "pending_permission", "permission": permission["request"], "draft": module_text}
        if output_path:
            Path(output_path).write_text(module_text, encoding="utf-8")
        permission_manager.log_action("code_agent.generate_module", payload, status="completed")
        return {"status": "success", "output_path": output_path, "module": module_text}

    def run_project_tests(self, path: str | None = None) -> dict:
        workdir = path or "."
        permission = permission_manager.request_permission("run_project_tests", {"path": workdir}, destructive=False)
        if not permission["approved"]:
            return {"status": "pending_permission", "permission": permission["request"]}
        command = ["python", "-m", "pytest"]
        completed = subprocess.run(command, cwd=workdir, capture_output=True, text=True, timeout=120)
        permission_manager.log_action(
            "code_agent.run_project_tests",
            {"path": workdir, "returncode": completed.returncode},
            status="completed" if completed.returncode == 0 else "failed",
        )
        return {"status": "success", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


code_agent = CodeAgent()
