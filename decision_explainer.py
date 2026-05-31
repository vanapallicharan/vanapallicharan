from morpho_core.behavior_model import behavior_model


class DecisionExplainer:
    def classify_risk(self, action: str, destructive: bool = False) -> str:
        if destructive or any(term in action for term in ["delete", "remove", "install", "run_command"]):
            return "high"
        if any(term in action for term in ["modify", "generate", "fetch", "tests", "automation"]):
            return "medium"
        return "low"

    def explain(self, action: str, context: dict | None = None, confidence: float | None = None, destructive: bool = False) -> dict:
        preference = behavior_model.action_preference(action)
        risk = self.classify_risk(action, destructive=destructive)
        context = context or {}
        reasons = []
        if context.get("intent"):
            reasons.append(f"Detected intent: {context['intent']}")
        activity = (context.get("activity") or {}).get("activity_type")
        if activity:
            reasons.append(f"Observed activity: {activity}")
        if context.get("recent_memory"):
            reasons.append("Relevant prior memory exists")
        reasons.append(f"Past approval rate for this action: {preference['approval_rate']:.0%}")
        confidence_value = max(0.0, min(1.0, confidence if confidence is not None else 0.5 + preference["confidence_adjustment"]))
        return {
            "action": action,
            "confidence": round(confidence_value, 3),
            "risk": risk,
            "why": reasons,
            "summary": f"Morpho suggests '{action}' with {risk} risk because the current context and past decisions support it.",
        }


decision_explainer = DecisionExplainer()
