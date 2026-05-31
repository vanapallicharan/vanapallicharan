import datetime
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np

from morpho_core.config import Config
from morpho_core.distillation_engine import distill_memory
from morpho_core.preprocessor import clean_text, extract_tags, summarize_text
from morpho_core.translator import MorphoTranslator


translator = MorphoTranslator()


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def _safe_parse_timestamp(value: str | None) -> datetime.datetime:
    if not value:
        return datetime.datetime.now(datetime.UTC)
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.datetime.now(datetime.UTC)


def _cosine_similarity(left, right) -> float:
    if not left or not right:
        return 0.0
    left_vec = np.array(left, dtype="float32")
    right_vec = np.array(right, dtype="float32")
    left_norm = np.linalg.norm(left_vec)
    right_norm = np.linalg.norm(right_vec)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left_vec, right_vec) / (left_norm * right_norm))


def _recency_score(timestamp: str | None) -> float:
    age = datetime.datetime.now(datetime.UTC) - _safe_parse_timestamp(timestamp)
    age_days = max(0.0, age.total_seconds() / 86400.0)
    return 1.0 / (1.0 + age_days)


class ConversationMemory:
    def __init__(self):
        dirs = Config.ensure_storage_dirs()
        self.conversations_dir = Path(dirs["conversations"])
        self.memories_dir = Path(dirs["memories"])
        self.knowledge_dir = Path(dirs["knowledge"])

    def _conversation_path(self, conversation_id: str) -> Path:
        return self.conversations_dir / f"{conversation_id}.jsonl"

    def _memory_path(self, conversation_id: str, turn_id: str) -> Path:
        conversation_dir = self.memories_dir / conversation_id
        conversation_dir.mkdir(parents=True, exist_ok=True)
        return conversation_dir / f"{turn_id}.json"

    def _knowledge_path(self, memory_id: str) -> Path:
        return self.knowledge_dir / f"{memory_id}.json"

    def _extract_facts(self, user_text: str, assistant_text: str) -> list[str]:
        combined = clean_text(f"{user_text}. {assistant_text}")
        sentences = [segment.strip() for segment in combined.split(".") if segment.strip()]
        facts = []
        for sentence in sentences:
            if len(sentence) < 20:
                continue
            facts.append(sentence)
            if len(facts) >= Config.MEMORY_FACT_LIMIT:
                break
        if not facts and combined:
            facts.append(combined[:240])
        return facts

    def _embedding_text(self, summary: str, facts: list[str], tags: list[str] | None = None) -> str:
        return clean_text(" ".join([summary, *facts, *(tags or [])]))

    def _machine_record(
        self,
        conversation_id: str,
        turn_id: str,
        user_text: str,
        assistant_text: str,
        provider: str,
        model: str,
        response_id: str | None = None,
    ) -> dict:
        user_clean = clean_text(user_text)
        assistant_clean = clean_text(assistant_text)
        summary = assistant_clean if len(assistant_clean) >= 20 else summarize_text(f"{user_clean}. {assistant_clean}", max_sentences=2)
        tags = extract_tags(f"{user_clean} {assistant_clean}")
        facts = self._extract_facts(user_clean, assistant_clean)
        checksum = hashlib.sha256(f"{user_clean}|{assistant_clean}".encode("utf-8")).hexdigest()[:16]
        created_at = _utc_now()
        embedding = translator.encode(self._embedding_text(summary, facts, tags))
        return {
            "schema": "morpho.memory.v1",
            "kind": "conversation_memory",
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "timestamp": created_at,
            "provider": provider,
            "model": model,
            "response_id": response_id,
            "summary": summary,
            "tags": tags,
            "facts": facts,
            "machine": {
                "u": user_clean,
                "a": assistant_clean,
                "s": summary,
                "k": tags,
                "f": facts,
                "h": checksum,
            },
            "knowledge_memory": {
                "id": uuid4().hex,
                "summary": summary,
                "facts": facts,
                "tags": tags,
                "embedding": embedding.astype("float32").tolist() if embedding is not None else [],
                "frequency": 1,
                "source_count": 1,
                "confidence": 0.6,
                "created_at": created_at,
                "last_updated": created_at,
                "conversation_ids": [conversation_id],
                "turn_ids": [turn_id],
                "sources": [f"conversation:{conversation_id}"],
                "provider": provider,
                "model": model,
            },
        }

    def load_recent_history(self, conversation_id: str, limit: int | None = None) -> list[dict]:
        path = self._conversation_path(conversation_id)
        if not path.exists():
            return []
        limit = limit or Config.MEMORY_HISTORY_WINDOW
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
        history = []
        for line in lines:
            try:
                history.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return history

    def load_all_memories(self) -> list[dict]:
        # Distilled memories are stored separately from raw turn logs so the knowledge base stays compact.
        memories = []
        for path in sorted(self.knowledge_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as file:
                    memory = json.load(file)
                    memory["local_path"] = str(path)
                    memories.append(memory)
            except Exception:
                continue
        return memories

    def save_memory(self, memory: dict) -> dict:
        path = self._knowledge_path(memory["id"])
        with path.open("w", encoding="utf-8") as file:
            json.dump(memory, file, ensure_ascii=False, indent=2)
        memory["local_path"] = str(path)
        return memory

    def recall(self, query: str, conversation_id: str | None = None, top_k: int | None = None) -> list[dict]:
        query_vector = translator.encode(clean_text(query))
        if query_vector is None:
            return []

        ranked = []
        for memory in self.load_all_memories():
            conversation_ids = set(memory.get("conversation_ids") or [])
            if conversation_id and conversation_ids and conversation_id not in conversation_ids and "global" not in conversation_ids:
                continue
            similarity = _cosine_similarity(query_vector.tolist(), memory.get("embedding"))
            confidence = float(memory.get("confidence") or 0.0)
            recency = _recency_score(memory.get("last_updated"))
            # Retrieval favors semantic similarity first, then reliability, then freshness.
            score = (similarity * 0.6) + (confidence * 0.2) + (recency * 0.2)
            ranked.append(
                {
                    "doc_id": memory.get("id"),
                    "score": score,
                    "similarity": similarity,
                    "confidence": confidence,
                    "recency": recency,
                    "metadata": {
                        "type": "conversation_memory",
                        "conversation_id": conversation_id,
                        "summary": memory.get("summary"),
                        "facts": memory.get("facts", []),
                        "tags": memory.get("tags", []),
                        "frequency": memory.get("frequency", 1),
                        "source_count": memory.get("source_count", 1),
                        "confidence": confidence,
                        "last_updated": memory.get("last_updated"),
                        "local_path": memory.get("local_path"),
                    },
                }
            )
        ranked.sort(
            key=lambda item: (
                item["score"],
                item["metadata"]["confidence"],
                item["metadata"]["frequency"],
                item["metadata"]["last_updated"] or "",
            ),
            reverse=True,
        )
        return ranked[: (top_k or Config.MEMORY_TOP_K)]

    def build_context(self, conversation_id: str, query: str) -> list[str]:
        context = []
        history = self.load_recent_history(conversation_id)
        for item in history[-Config.MEMORY_HISTORY_WINDOW :]:
            user_text = clean_text(item.get("user", ""))
            assistant_text = clean_text(item.get("assistant", ""))
            if user_text:
                context.append(f"Recent user: {user_text}")
            if assistant_text:
                context.append(f"Recent assistant: {assistant_text}")

        for match in self.recall(query, conversation_id=conversation_id):
            metadata = match.get("metadata") or {}
            summary = metadata.get("summary")
            facts = metadata.get("facts") or []
            frequency = metadata.get("frequency", 1)
            confidence = metadata.get("confidence", 0.0)
            if summary:
                context.append(f"Knowledge summary (confidence={confidence:.2f}, frequency={frequency}): {summary}")
            for fact in facts[: Config.MEMORY_FACT_LIMIT]:
                context.append(f"Knowledge fact: {fact}")
        return context

    def remember_turn(
        self,
        conversation_id: str,
        user_text: str,
        assistant_text: str,
        provider: str,
        model: str,
        response_id: str | None = None,
    ) -> dict:
        turn_id = uuid4().hex
        record = self._machine_record(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_text=user_text,
            assistant_text=assistant_text,
            provider=provider,
            model=model,
            response_id=response_id,
        )

        conversation_entry = {
            "turn_id": turn_id,
            "timestamp": record["timestamp"],
            "user": record["machine"]["u"],
            "assistant": record["machine"]["a"],
            "summary": record["summary"],
            "tags": record["tags"],
        }
        conversation_path = self._conversation_path(conversation_id)
        with conversation_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(conversation_entry, ensure_ascii=False) + "\n")

        memory_path = self._memory_path(conversation_id, turn_id)
        with memory_path.open("w", encoding="utf-8") as file:
            json.dump(record, file, ensure_ascii=False, indent=2)

        existing_memories = self.load_all_memories()
        final_memory = distill_memory(record["knowledge_memory"], existing_memories)
        # save_memory overwrites the old canonical file when distillation keeps the same id.
        saved_memory = self.save_memory(final_memory)

        record["doc_id"] = saved_memory["id"]
        record["knowledge_memory"] = saved_memory
        return record
