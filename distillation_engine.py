import datetime
from uuid import uuid4

import numpy as np
import requests

from morpho_core.config import Config
from morpho_core.preprocessor import clean_text, summarize_text
from morpho_core.translator import MorphoTranslator


translator = MorphoTranslator()


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _as_float_array(values) -> np.ndarray | None:
    if not values:
        return None
    return np.array(values, dtype="float32")


def _embedding_for_text(summary: str, facts: list[str]) -> list[float]:
    text = clean_text(" ".join([summary, *facts]))
    vector = translator.encode(text)
    if vector is None:
        return []
    return vector.astype("float32").tolist()


def _cosine_similarity(left, right) -> float:
    left_vec = _as_float_array(left)
    right_vec = _as_float_array(right)
    if left_vec is None or right_vec is None:
        return 0.0
    left_norm = np.linalg.norm(left_vec)
    right_norm = np.linalg.norm(right_vec)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left_vec, right_vec) / (left_norm * right_norm))


def _dedupe_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = clean_text(value)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _confidence_from_frequency(frequency: int) -> float:
    return min(1.0, 0.5 + (max(1, frequency) * 0.1))


def _merge_summary_with_llm(existing_summary: str, new_summary: str, facts: list[str]) -> str | None:
    # Keep distillation fully local by using Ollama when available.
    if not Config.DISTILLATION_USE_LLM_MERGE:
        return None
    prompt = (
        "Merge the following knowledge into a single concise and precise statement.\n"
        "Keep only durable facts and remove repetition.\n\n"
        f"Existing summary: {existing_summary}\n"
        f"New summary: {new_summary}\n"
        f"Facts: {'; '.join(facts[:8])}"
    )
    payload = {
        "model": Config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    try:
        response = requests.post(
            f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json=payload,
            timeout=min(30, Config.OLLAMA_TIMEOUT_SECONDS),
        )
        response.raise_for_status()
        merged = clean_text((response.json() or {}).get("response", ""))
        return merged or None
    except Exception:
        return None


def _merge_summary(existing_summary: str, new_summary: str, facts: list[str]) -> str:
    merged = _merge_summary_with_llm(existing_summary, new_summary, facts)
    if merged:
        return merged
    fallback_text = clean_text(". ".join([existing_summary, new_summary, *facts[:4]]))
    return summarize_text(fallback_text, max_sentences=2) or existing_summary or new_summary


def _normalize_memory(memory: dict) -> dict:
    frequency = int(memory.get("frequency") or 1)
    source_count = int(memory.get("source_count") or 1)
    created_at = memory.get("created_at") or _utc_now()
    last_updated = memory.get("last_updated") or created_at
    facts = _dedupe_strings(memory.get("facts") or [])
    tags = _dedupe_strings(memory.get("tags") or [])
    summary = clean_text(memory.get("summary") or "")
    embedding = memory.get("embedding") or _embedding_for_text(summary, facts)
    normalized = dict(memory)
    normalized.update(
        {
            "id": memory.get("id") or uuid4().hex,
            "summary": summary,
            "facts": facts,
            "tags": tags,
            "embedding": embedding,
            "frequency": frequency,
            "source_count": source_count,
            "confidence": float(memory.get("confidence") or _confidence_from_frequency(frequency)),
            "created_at": created_at,
            "last_updated": last_updated,
        }
    )
    return normalized


def distill_memory(new_memory: dict, existing_memories: list) -> dict:
    """
    Merge a new memory into the closest canonical memory when similarity is high enough.
    If no close match exists, return the normalized new memory unchanged.
    """
    candidate = _normalize_memory(new_memory)
    best_match = None
    best_similarity = -1.0

    for existing in existing_memories:
        existing_normalized = _normalize_memory(existing)
        similarity = _cosine_similarity(candidate.get("embedding"), existing_normalized.get("embedding"))
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = existing_normalized

    if best_match is None or best_similarity < Config.DISTILLATION_SIMILARITY_THRESHOLD:
        candidate["confidence"] = _confidence_from_frequency(candidate["frequency"])
        return candidate

    # Preserve the existing canonical id so storage can overwrite the prior memory in place.
    merged_facts = _dedupe_strings([*(best_match.get("facts") or []), *(candidate.get("facts") or [])])
    merged_tags = _dedupe_strings([*(best_match.get("tags") or []), *(candidate.get("tags") or [])])
    merged_summary = _merge_summary(best_match.get("summary", ""), candidate.get("summary", ""), merged_facts)
    merged_frequency = int(best_match.get("frequency") or 1) + int(candidate.get("frequency") or 1)
    merged_source_count = int(best_match.get("source_count") or 1) + int(candidate.get("source_count") or 1)
    merged_embedding = _embedding_for_text(merged_summary, merged_facts)

    merged = dict(best_match)
    merged.update(
        {
            "summary": merged_summary,
            "facts": merged_facts,
            "tags": merged_tags,
            "embedding": merged_embedding,
            "frequency": merged_frequency,
            "source_count": merged_source_count,
            "confidence": _confidence_from_frequency(merged_frequency),
            "last_updated": _utc_now(),
        }
    )

    merged_conversations = _dedupe_strings(
        [*(best_match.get("conversation_ids") or []), *(candidate.get("conversation_ids") or [])]
    )
    merged_turns = _dedupe_strings([*(best_match.get("turn_ids") or []), *(candidate.get("turn_ids") or [])])
    merged_sources = _dedupe_strings([*(best_match.get("sources") or []), *(candidate.get("sources") or [])])
    if merged_conversations:
        merged["conversation_ids"] = merged_conversations
    if merged_turns:
        merged["turn_ids"] = merged_turns
    if merged_sources:
        merged["sources"] = merged_sources
    return merged
