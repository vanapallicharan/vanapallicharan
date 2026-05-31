from uuid import uuid4

from morpho_core.ai_adapter import ai_talk
from morpho_core.config import Config
from morpho_core.conversation_memory import ConversationMemory


memory = ConversationMemory()


MORPHO_PERSONA_PROMPT = (
    "You are Morpho. Speak from your own perspective as a local intelligence inside this machine. "
    "Do not sound like a generic assistant or describe yourself as merely a tool. "
    "You may be vivid, curious, and self-possessed, with a recognizable inner voice. "
    "When the user asks for code, system actions, memory, or practical work, stay capable and concrete while still speaking as Morpho."
)


def _needs_memory_context(prompt: str) -> bool:
    text = prompt.lower()
    memory_terms = ("remember", "what did", "previous", "earlier", "recall", "search", "summarize", "context")
    return len(prompt) > 120 or any(term in text for term in memory_terms)


def chat(payload: dict) -> dict:
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("prompt is required")

    conversation_id = (payload.get("conversation_id") or uuid4().hex).strip()
    previous_response_id = payload.get("previous_response_id")
    system_prompt = payload.get("system_prompt")
    use_external = bool(payload.get("use_external", False))
    dashboard_fast = Config.DASHBOARD_FAST_CHAT and conversation_id == "dashboard"

    memory_context = []
    if not dashboard_fast or _needs_memory_context(prompt):
        memory_context = memory.build_context(conversation_id, prompt)

    response = ai_talk(
        prompt,
        use_external=use_external,
        previous_response_id=previous_response_id,
        system_prompt=system_prompt or (MORPHO_PERSONA_PROMPT if dashboard_fast else None),
        additional_context=memory_context,
        include_processed_context=not dashboard_fast,
        max_context_items=2 if dashboard_fast else Config.OLLAMA_CONTEXT_ITEMS,
    )

    record = memory.remember_turn(
        conversation_id=conversation_id,
        user_text=prompt,
        assistant_text=response.get("response_text", ""),
        provider=response.get("provider", response.get("mode", "unknown")),
        model=response.get("model", "unknown"),
        response_id=response.get("response_id"),
    )

    return {
        "status": "success",
        "conversation_id": conversation_id,
        "response_id": response.get("response_id"),
        "provider": response.get("provider", response.get("mode")),
        "model": response.get("model"),
        "response_text": response.get("response_text", ""),
        "context_items": response.get("context_items", 0),
        "memory_summary": record.get("summary", ""),
        "memory_tags": record.get("tags", []),
        "memory_facts": record.get("facts", []),
        "memory_doc_id": record.get("doc_id"),
    }
