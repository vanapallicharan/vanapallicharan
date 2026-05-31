from copy import deepcopy

from morpho_core.action_router import action_router


class ExecutorAgent:
    """Executes planned steps through the centralized action router."""

    async def execute(self, plan: dict, context: dict | None = None) -> dict:
        context = context or {}
        results = []
        for step in plan.get("steps", []):
            if step.get("kind") != "execute":
                results.append({"step_id": step.get("id"), "status": "completed", "detail": step})
                continue
            routed = await action_router.route(
                action_type=step.get("action_type"),
                payload=deepcopy(step.get("payload") or {}),
                context=context,
                plan=plan,
            )
            routed["step_id"] = step.get("id")
            results.append(routed)
            if routed.get("status") not in {"success", "completed", "cached"}:
                break
        overall_status = "success" if all(item.get("status") in {"success", "completed", "cached"} for item in results) else "failed"
        return {"status": overall_status, "results": results}


executor_agent = ExecutorAgent()
