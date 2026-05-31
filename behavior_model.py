import datetime
import json
from pathlib import Path

from morpho_core.config import Config


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


class BehaviorModel:
    """Learns which actions the user tends to approve and how often suggestions should appear."""

    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.state_path = Path(dirs["state"]) / "behavior_model.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        default_state = {
            "actions": {},
            "executions": {},
            "feedback": [],
            "suggestion_cooldown_seconds": Config.SUGGESTION_COOLDOWN_SECONDS,
            "last_suggestion_at": None,
        }
        if self.state_path.exists():
            try:
                loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
                for key, value in default_state.items():
                    loaded.setdefault(key, value)
                return loaded
            except json.JSONDecodeError:
                pass
        return default_state

    def _save(self) -> None:
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def observe_decision(self, action: str, approved: bool, detail: dict | None = None) -> dict:
        bucket = self.state["actions"].setdefault(
            action,
            {"approvals": 0, "rejections": 0, "last_result": None, "last_updated": None},
        )
        if approved:
            bucket["approvals"] += 1
        else:
            bucket["rejections"] += 1
        bucket["last_result"] = "approved" if approved else "rejected"
        bucket["last_updated"] = _utc_now()
        if not approved:
            self.state["suggestion_cooldown_seconds"] = min(
                300,
                int(self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS) * 1.2),
            )
        else:
            self.state["suggestion_cooldown_seconds"] = max(
                15,
                int(self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS) * 0.95),
            )
        self._save()
        return bucket

    def record_feedback(self, payload: dict) -> dict:
        entry = dict(payload)
        entry["timestamp"] = _utc_now()
        self.state["feedback"].append(entry)
        self.state["feedback"] = self.state["feedback"][-200:]
        rating = int(payload.get("rating", 0) or 0)
        if rating < 0:
            self.state["suggestion_cooldown_seconds"] = min(
                300, self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS) + 15
            )
        elif rating > 0:
            self.state["suggestion_cooldown_seconds"] = max(
                15, self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS) - 5
            )
        self._save()
        return entry

    def action_preference(self, action: str) -> dict:
        bucket = self.state["actions"].get(action, {})
        approvals = int(bucket.get("approvals", 0))
        rejections = int(bucket.get("rejections", 0))
        total = approvals + rejections
        approval_rate = approvals / total if total else 0.5
        confidence_adjustment = (approval_rate - 0.5) * 0.4
        return {
            "approvals": approvals,
            "rejections": rejections,
            "approval_rate": round(approval_rate, 3),
            "confidence_adjustment": confidence_adjustment,
            "cooldown_seconds": self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS),
        }

    def observe_execution(self, action: str, success: bool, detail: dict | None = None) -> dict:
        bucket = self.state["executions"].setdefault(
            action,
            {"successes": 0, "failures": 0, "last_result": None, "last_updated": None},
        )
        if success:
            bucket["successes"] += 1
        else:
            bucket["failures"] += 1
        bucket["last_result"] = "success" if success else "failure"
        bucket["last_updated"] = _utc_now()
        if success:
            self.state["suggestion_cooldown_seconds"] = max(
                15, int(self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS) * 0.98)
            )
        else:
            self.state["suggestion_cooldown_seconds"] = min(
                300, int(self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS) * 1.1)
            )
        self._save()
        return bucket

    def can_emit_suggestion(self) -> bool:
        last = self.state.get("last_suggestion_at")
        if not last:
            return True
        try:
            last_dt = datetime.datetime.fromisoformat(last.replace("Z", "+00:00"))
        except ValueError:
            return True
        delta = datetime.datetime.now(datetime.UTC) - last_dt
        return delta.total_seconds() >= self.state.get("suggestion_cooldown_seconds", Config.SUGGESTION_COOLDOWN_SECONDS)

    def mark_suggestion_emitted(self) -> None:
        self.state["last_suggestion_at"] = _utc_now()
        self._save()

    def summary(self) -> dict:
        return {
            "actions": self.state.get("actions", {}),
            "executions": self.state.get("executions", {}),
            "suggestion_cooldown_seconds": self.state.get("suggestion_cooldown_seconds"),
            "last_suggestion_at": self.state.get("last_suggestion_at"),
            "feedback_count": len(self.state.get("feedback", [])),
        }


behavior_model = BehaviorModel()
