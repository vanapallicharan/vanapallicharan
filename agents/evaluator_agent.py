class EvaluatorAgent:
    """Evaluates execution results and recommends follow-up improvement."""

    async def evaluate(self, suggestion: dict, plan: dict, execution: dict) -> dict:
        results = execution.get("results", [])
        failed = [item for item in results if item.get("status") not in {"success", "completed", "cached"}]
        if failed:
            return {
                "status": "needs_attention",
                "summary": f"Execution for {suggestion.get('action_type')} needs attention.",
                "improvement": "Review the failed step output and consider lowering automation level or asking a clarifying question.",
                "success_score": 0.25,
            }
        return {
            "status": "successful",
            "summary": f"Execution for {suggestion.get('action_type')} completed successfully.",
            "improvement": "If this repeats often, raise confidence for safe auto-execution.",
            "success_score": 0.9,
        }


evaluator_agent = EvaluatorAgent()
