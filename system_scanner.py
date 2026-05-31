import os
import shutil
from pathlib import Path

import psutil


class SystemScanner:
    def installed_tools(self, tool_names: list[str] | None = None) -> list[dict]:
        tool_names = tool_names or ["python", "pip", "git", "ollama", "node", "npm", "pytest"]
        results = []
        for name in tool_names:
            location = shutil.which(name)
            if location:
                results.append({"name": name, "path": location})
        return results

    def running_processes(self, limit: int = 30) -> list[dict]:
        processes = []
        for process in psutil.process_iter(["pid", "name", "exe"]):
            try:
                info = process.info
                processes.append({"pid": info.get("pid"), "name": info.get("name"), "exe": info.get("exe")})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes[:limit]

    def scan_directories(self, root: str, limit: int = 50) -> list[str]:
        root_path = Path(root)
        if not root_path.exists():
            return []
        results = []
        for path in root_path.rglob("*"):
            results.append(str(path))
            if len(results) >= limit:
                break
        return results

    def system_map(self, root: str | None = None) -> dict:
        root = root or os.getcwd()
        return {
            "apps": self.running_processes(),
            "files": self.scan_directories(root),
            "tools": self.installed_tools(),
        }


system_scanner = SystemScanner()
