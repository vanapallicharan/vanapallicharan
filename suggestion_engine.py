import datetime
from uuid import uuid4

from morpho_core.behavior_model import behavior_model
from morpho_core.context_engine import context_engine
from morpho_core.decision_explainer import decision_explainer


class SuggestionEngine:
    def _make_suggestion(self, action: str, title: str, detail: str, payload: dict, context: dict, confidence: float) -> dict:
        explanation = decision_explainer.explain(action, context=context, confidence=confidence, destructive=False)
        auto_execute = explanation["confidence"] > 0.9 and explanation["risk"] == "low"
        return {
            "id": uuid4().hex,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "action": action,
            "action_type": action,
            "payload": payload,
            "title": title,
            "detail": detail,
            "confidence": explanation["confidence"],
            "risk": explanation["risk"],
            "auto_execute": auto_execute,
            "explanation": explanation["summary"],
            "explanation_detail": explanation,
        }

    def generate(self, conversation_id: str | None = None, query: str | None = None) -> dict:
        context = context_engine.estimate_intent(conversation_id=conversation_id, query=query)
        suggestions = []
        intent = context.get("intent")
        activity = (context.get("activity") or {}).get("activity_type")
        screen_enabled = bool((context.get("screen") or {}).get("enabled"))
        query_text = (query or "").lower()

        if intent == "coding_help" or activity == "coding" or any(term in query_text for term in ["python", "code", "bug", "test", "flask"]):
            pref = behavior_model.action_preference("code_agent.analyze_codebase")
            suggestions.append(
                self._make_suggestion(
                    "code_agent.analyze_codebase",
                    "Analyze Current Project",
                    "I can scan the current project structure and point out bugs, test gaps, or refactor opportunities.",
                    {"path": "."},
                    context,
                    0.62 + pref["confidence_adjustment"],
                )
            )
            pref = behavior_model.action_preference("code_agent.run_project_tests")
            suggestions.append(
                self._make_suggestion(
                    "code_agent.run_project_tests",
                    "Run Project Tests",
                    "If you want, I can run tests and summarize failures before you change more code.",
                    {"path": "."},
                    context,
                    0.58 + pref["confidence_adjustment"],
                )
            )
        if intent == "research_help":
            pref = behavior_model.action_preference("fetch_url")
            suggestions.append(
                self._make_suggestion(
                    "fetch_url",
                    "Summarize Current Research",
                    "I can fetch and summarize relevant sources based on what you're browsing.",
                    {"url": "https://example.com"},
                    context,
                    0.55 + pref["confidence_adjustment"],
                )
            )
        if screen_enabled and (context.get("screen") or {}).get("visible_text"):
            pref = behavior_model.action_preference("screen_observer.capture")
            suggestions.append(
                self._make_suggestion(
                    "screen_observer.capture",
                    "Capture Screen Context",
                    "I can use the visible screen text to build a better explanation or note.",
                    {},
                    context,
                    0.5 + pref["confidence_adjustment"],
                )
            )
        if context.get("recent_memory"):
            pref = behavior_model.action_preference("memory.search")
            suggestions.append(
                self._make_suggestion(
                    "memory.search",
                    "Use Prior Knowledge",
                    "I found related memories and can answer with better continuity if you want.",
                    {"query": query or "", "conversation_id": conversation_id},
                    context,
                    0.57 + pref["confidence_adjustment"],
                )
            )
        if not suggestions:
            pref = behavior_model.action_preference("assistant.context")
            suggestions.append(
                self._make_suggestion(
                    "assistant.context",
                    "Refresh Context Snapshot",
                    "I can inspect the current context and suggest the next best safe action.",
                    {"conversation_id": conversation_id, "query": query or ""},
                    context,
                    0.5 + pref["confidence_adjustment"],
                )
            )

        suggestions.sort(key=lambda item: (item["confidence"], item["auto_execute"], 0 if item["risk"] == "high" else 1), reverse=True)
        return {"context": context, "suggestions": suggestions[:6], "can_emit": behavior_model.can_emit_suggestion()}


suggestion_engine = SuggestionEngine()
