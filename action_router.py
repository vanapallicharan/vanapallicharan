import asyncio
import datetime
import json
from pathlib import Path

import requests

from morpho_core.code_agent import code_agent
from morpho_core.config import Config
from morpho_core.context_engine import context_engine
from morpho_core.permission_manager import permission_manager
from morpho_core.screen_observer import screen_observer


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


class ActionRouter:
    """Routes executable action types to concrete local capabilities."""

    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.logs_path = Path(dirs["logs"]) / "executions.jsonl"
        self.cache: dict[str, dict] = {}

    def _cache_key(self, action_type: str, payload: dict) -> str:
        return json.dumps({"action_type": action_type, "payload": payload}, sort_keys=True, ensure_ascii=False)

    def _read_cache(self, key: str) -> dict | None:
        item = self.cache.get(key)
        if not item:
            return None
        created = datetime.datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        age = datetime.datetime.now(datetime.UTC) - created
        if age.total_seconds() > Config.ACTION_CACHE_TTL_SECONDS:
            self.cache.pop(key, None)
            return None
        return item["result"]

    def _write_cache(self, key: str, result: dict) -> None:
        self.cache[key] = {"timestamp": _utc_now(), "result": result}

    def _log(self, entry: dict) -> None:
        with self.logs_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    async def route(self, action_type: str, payload: dict, context: dict | None = None, plan: dict | None = None) -> dict:
        context = context or {}
        key = self._cache_key(action_type, payload)
        cached = self._read_cache(key)
        if cached is not None:
            return {"status": "cached", "action_type": action_type, "result": cached}

        if action_type == "code_agent.analyze_codebase":
            result = await asyncio.to_thread(code_agent.analyze_codebase, payload.get("path", "."))
        elif action_type == "code_agent.run_project_tests":
            result = await asyncio.to_thread(code_agent.run_project_tests, payload.get("path"))
        elif action_type == "screen_observer.capture":
            result = await asyncio.to_thread(screen_observer.capture_snapshot)
        elif action_type == "assistant.context":
            result = await asyncio.to_thread(
                context_engine.estimate_intent,
                payload.get("conversation_id"),
                payload.get("query"),
            )
        elif action_type == "memory.search":
            result = {"status": "noop", "message": "Memory search is handled through the existing memory endpoints."}
        elif action_type == "fetch_url":
            def fetch():
                response = requests.get(payload["url"], timeout=20)
                return {"status_code": response.status_code, "preview": response.text[:1000], "url": payload["url"]}
            result = await asyncio.to_thread(fetch)
        else:
            result = {"status": "unsupported", "action_type": action_type, "payload": payload}

        wrapped = {
            "timestamp": _utc_now(),
            "action_type": action_type,
            "status": "success" if result.get("status") not in {"pending_permission", "unsupported"} else result.get("status"),
            "result": result,
            "plan_metadata": (plan or {}).get("metadata", {}),
        }
        self._write_cache(key, result)
        self._log(wrapped)
        permission_manager.log_action("action_router.execute", {"action_type": action_type, "payload": payload}, status=wrapped["status"])
        return wrapped

    def read_logs(self, limit: int = 100) -> list[dict]:
        if not self.logs_path.exists():
            return []
        lines = self.logs_path.read_text(encoding="utf-8").splitlines()[-limit:]
        items = []
        for line in lines:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return items


action_router = ActionRouter()
