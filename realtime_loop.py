import json
import threading
import time
from pathlib import Path

from morpho_core.behavior_model import behavior_model
from morpho_core.config import Config
from morpho_core.permission_manager import permission_manager
from morpho_core.suggestion_engine import suggestion_engine


class RealtimeLoop:
    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.state_path = Path(dirs["state"]) / "realtime_loop.json"
        self.log_path = Path(dirs["logs"]) / "suggestions.jsonl"
        self.thread = None
        self.stop_event = threading.Event()
        self.latest = {
            "running": False,
            "context": {},
            "suggestions": [],
            "timeline": [],
            "executions": [],
        }
        self.lock = threading.RLock()

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self.latest, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_log(self, payload: dict) -> None:
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def tick(self, conversation_id: str | None = None, query: str | None = None) -> dict:
        result = suggestion_engine.generate(conversation_id=conversation_id, query=query)
        with self.lock:
            self.latest["context"] = result["context"]
            if result["can_emit"] and result["suggestions"]:
                self.latest["suggestions"] = result["suggestions"][: Config.SUGGESTION_MAX_VISIBLE]
                self.latest["timeline"].append(
                    {
                        "timestamp": result["suggestions"][0]["timestamp"],
                        "event": "suggestions_refreshed",
                        "count": len(result["suggestions"]),
                    }
                )
                self.latest["timeline"] = self.latest["timeline"][-50:]
                behavior_model.mark_suggestion_emitted()
                self._append_log({"timestamp": result["suggestions"][0]["timestamp"], "suggestions": self.latest["suggestions"]})
            self._save_state()
        return self.snapshot()

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception as exc:
                permission_manager.log_action("realtime_loop.error", {"error": str(exc)}, status="failed")
            self.stop_event.wait(Config.REALTIME_LOOP_INTERVAL_SECONDS)

    def start(self) -> dict:
        with self.lock:
            if self.thread and self.thread.is_alive():
                return self.snapshot()
            self.stop_event.clear()
            self.latest["running"] = True
            self.thread = threading.Thread(target=self._run, daemon=True, name="MorphoRealtimeLoop")
            self.thread.start()
            self._save_state()
        return self.snapshot()

    def stop(self) -> dict:
        with self.lock:
            self.stop_event.set()
            self.latest["running"] = False
            self._save_state()
        return self.snapshot()

    def snapshot(self) -> dict:
        with self.lock:
            return dict(self.latest)

    def add_timeline_event(self, event: dict) -> None:
        with self.lock:
            self.latest["timeline"].append(event)
            self.latest["timeline"] = self.latest["timeline"][-50:]
            self._save_state()

    def add_execution(self, execution: dict) -> None:
        with self.lock:
            self.latest["executions"].append(execution)
            self.latest["executions"] = self.latest["executions"][-20:]
            self.latest["timeline"].append(
                {
                    "timestamp": execution.get("timestamp"),
                    "event": "execution",
                    "status": execution.get("status"),
                    "action_type": execution.get("action_type"),
                }
            )
            self.latest["timeline"] = self.latest["timeline"][-50:]
            self._save_state()

    def read_logs(self, limit: int = 100) -> list[dict]:
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text(encoding="utf-8").splitlines()[-limit:]
        result = []
        for line in lines:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return result


realtime_loop = RealtimeLoop()
