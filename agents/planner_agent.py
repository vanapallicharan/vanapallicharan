from copy import deepcopy


class PlannerAgent:
    """Turns a suggestion into an explicit execution plan."""

    async def plan(self, suggestion: dict) -> dict:
        suggestion = deepcopy(suggestion)
        payload = suggestion.get("payload") or {}
        action_type = suggestion.get("action_type") or suggestion.get("action")
        plan = {
            "suggestion_id": suggestion.get("id"),
            "action_type": action_type,
            "steps": [
                {
                    "id": f"{suggestion.get('id', 'suggestion')}:prepare",
                    "kind": "prepare",
                    "description": f"Validate payload for {action_type}",
                    "payload": payload,
                },
                {
                    "id": f"{suggestion.get('id', 'suggestion')}:execute",
                    "kind": "execute",
                    "description": f"Execute {action_type}",
                    "action_type": action_type,
                    "payload": payload,
                },
                {
                    "id": f"{suggestion.get('id', 'suggestion')}:verify",
                    "kind": "verify",
                    "description": f"Verify result of {action_type}",
                    "payload": {"expectation": suggestion.get("title") or action_type},
                },
            ],
            "metadata": {
                "confidence": suggestion.get("confidence", 0.0),
                "risk": suggestion.get("risk", "medium"),
                "auto_execute": bool(suggestion.get("auto_execute")),
            },
        }
        return plan


planner_agent = PlannerAgent()
