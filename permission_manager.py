import datetime
import json
import threading
from pathlib import Path
from uuid import uuid4

from morpho_core.behavior_model import behavior_model
from morpho_core.config import Config
from morpho_core.decision_explainer import decision_explainer


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


class PermissionManager:
    """Central gatekeeper for sensitive actions."""

    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.logs_path = Path(dirs["logs"]) / "permissions.jsonl"
        self.state_path = Path(dirs["state"]) / "permissions_state.json"
        self.lock = threading.RLock()
        self.pending_requests: dict[str, dict] = {}
        self.mode = "SAFE_MODE" if Config.SAFE_MODE else "AUTO_MODE"

    def _write_log(self, entry: dict) -> None:
        with self.logs_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _save_state(self) -> None:
        state = {"mode": self.mode, "pending": list(self.pending_requests.values())}
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_mode(self, mode: str) -> dict:
        normalized = mode.upper().strip()
        if normalized not in {"SAFE_MODE", "AUTO_MODE"}:
            raise ValueError("mode must be SAFE_MODE or AUTO_MODE")
        with self.lock:
            self.mode = normalized
            self._save_state()
        return {"mode": self.mode}

    def log_action(self, action: str, detail: dict, status: str = "info") -> dict:
        entry = {
            "id": uuid4().hex,
            "timestamp": _utc_now(),
            "action": action,
            "status": status,
            "detail": detail,
        }
        with self.lock:
            self._write_log(entry)
        return entry

    def request_permission(self, action: str, detail: dict, destructive: bool = False, context: dict | None = None) -> dict:
        with self.lock:
            preference = behavior_model.action_preference(action)
            explanation = decision_explainer.explain(
                action,
                context=context,
                confidence=0.55 + preference["confidence_adjustment"],
                destructive=destructive,
            )
            if self.mode == "AUTO_MODE" and not destructive:
                behavior_model.observe_decision(action, approved=True, detail=detail)
                entry = self.log_action(action, {"detail": detail, "explanation": explanation}, status="auto-approved")
                return {"approved": True, "mode": self.mode, "request": None, "log": entry}

            request_id = uuid4().hex
            request = {
                "id": request_id,
                "timestamp": _utc_now(),
                "action": action,
                "detail": detail,
                "destructive": destructive,
                "status": "pending",
                "prompt": f"Allow Morpho to execute this action? {action}",
                "confidence": explanation["confidence"],
                "risk": explanation["risk"],
                "explanation": explanation,
            }
            self.pending_requests[request_id] = request
            self._write_log(
                {
                    "id": request_id,
                    "timestamp": request["timestamp"],
                    "action": action,
                    "status": "pending",
                    "detail": detail,
                    "confidence": request["confidence"],
                    "risk": request["risk"],
                }
            )
            self._save_state()
            return {"approved": False, "mode": self.mode, "request": request}

    def resolve_permission(self, request_id: str, approved: bool) -> dict:
        with self.lock:
            request = self.pending_requests.get(request_id)
            if not request:
                raise KeyError("permission request not found")
            request["status"] = "approved" if approved else "denied"
            request["resolved_at"] = _utc_now()
            behavior_model.observe_decision(request["action"], approved=approved, detail=request["detail"])
            self._write_log(
                {
                    "id": request_id,
                    "timestamp": request["resolved_at"],
                    "action": request["action"],
                    "status": request["status"],
                    "detail": request["detail"],
                }
            )
            del self.pending_requests[request_id]
            self._save_state()
            return request

    def list_pending(self) -> list[dict]:
        with self.lock:
            return list(self.pending_requests.values())

    def read_logs(self, limit: int = 100) -> list[dict]:
        if not self.logs_path.exists():
            return []
        lines = self.logs_path.read_text(encoding="utf-8").splitlines()[-limit:]
        result = []
        for line in lines:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return result


permission_manager = PermissionManager()
