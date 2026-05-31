from morpho_core.activity_monitor import activity_monitor
from morpho_core.conversation_memory import ConversationMemory
from morpho_core.screen_observer import screen_observer


class ContextEngine:
    def __init__(self):
        self.memory = ConversationMemory()

    def estimate_intent(self, conversation_id: str | None = None, query: str | None = None) -> dict:
        activity = activity_monitor.capture_activity()
        screen = screen_observer.capture_snapshot() if screen_observer.enabled else {"enabled": False}
        recent_memory = self.memory.recall(query or "", conversation_id=conversation_id, top_k=3) if query else []

        intent = "general_assistance"
        suggestions = []
        if activity.get("activity_type") == "coding":
            intent = "coding_help"
            suggestions.append("I see coding activity. Want me to analyze the codebase or run tests?")
        elif activity.get("activity_type") == "browsing":
            intent = "research_help"
            suggestions.append("You seem to be browsing. Want me to summarize a page or capture notes?")
        if screen.get("visible_text"):
            suggestions.append("I can use the visible screen text to refine suggestions if you want.")
        if recent_memory:
            suggestions.append("I found relevant prior memories that can improve continuity.")

        return {
            "activity": activity,
            "screen": screen,
            "recent_memory": recent_memory,
            "intent": intent,
            "suggestions": suggestions[:5],
        }


context_engine = ContextEngine()
