import datetime
import json
import threading
from collections import Counter
from pathlib import Path

import psutil

from morpho_core.config import Config
from morpho_core.permission_manager import permission_manager

try:
    import pygetwindow as gw
except Exception:
    gw = None


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _classify_activity(app_name: str, title: str) -> str:
    text = f"{app_name} {title}".lower()
    if any(term in text for term in ["code", "pycharm", "cursor", "visual studio", "terminal", "powershell"]):
        return "coding"
    if any(term in text for term in ["chrome", "firefox", "edge", "browser"]):
        return "browsing"
    if any(term in text for term in ["word", "docs", "notepad"]):
        return "writing"
    return "general"


class ActivityMonitor:
    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.enabled = Config.ACTIVITY_MONITOR_DEFAULT
        self.events_path = Path(dirs["logs"]) / "activity.jsonl"
        self.state_path = Path(dirs["state"]) / "activity_monitor.json"
        self.lock = threading.Lock()
        self._last_window = None
        self._last_timestamp = None

    def set_enabled(self, enabled: bool) -> dict:
        self.enabled = bool(enabled)
        self.state_path.write_text(json.dumps({"enabled": self.enabled}, indent=2), encoding="utf-8")
        permission_manager.log_action("activity_monitor.toggle", {"enabled": self.enabled}, status="updated")
        return {"enabled": self.enabled}

    def _active_window(self) -> tuple[str, str]:
        if gw is not None:
            try:
                window = gw.getActiveWindow()
                if window:
                    title = (window.title or "").strip()
                    app_name = title.split("-")[-1].strip() if "-" in title else title[:80]
                    return app_name or "unknown", title or "unknown"
            except Exception:
                pass
        return "unknown", "unknown"

    def capture_activity(self) -> dict:
        app_name, title = self._active_window()
        now = datetime.datetime.now(datetime.UTC)
        with self.lock:
            duration_seconds = 0
            if self._last_window == title and self._last_timestamp is not None:
                duration_seconds = int((now - self._last_timestamp).total_seconds())
            self._last_window = title
            self._last_timestamp = now

        event = {
            "timestamp": now.isoformat(),
            "active_app": app_name,
            "window_title": title,
            "duration": duration_seconds,
            "activity_type": _classify_activity(app_name, title),
            "process_count": len(psutil.pids()),
        }
        if self.enabled:
            with self.events_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def usage_patterns(self, limit: int = 200) -> dict:
        if not self.events_path.exists():
            return {"apps": [], "activity_types": []}
        lines = self.events_path.read_text(encoding="utf-8").splitlines()[-limit:]
        app_counter = Counter()
        type_counter = Counter()
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            app_counter[event.get("active_app", "unknown")] += 1
            type_counter[event.get("activity_type", "general")] += 1
        return {
            "apps": [{"name": name, "count": count} for name, count in app_counter.most_common(10)],
            "activity_types": [{"name": name, "count": count} for name, count in type_counter.most_common(10)],
        }


activity_monitor = ActivityMonitor()
