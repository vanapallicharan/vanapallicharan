import json
import os
import threading
from pathlib import Path
from uuid import uuid4

import faiss
import numpy as np

from morpho_core.config import Config


STORAGE_DIRS = Config.ensure_storage_dirs()
INDEX_PATH = Path(STORAGE_DIRS["base"]) / "faiss.index"
META_PATH = Path(STORAGE_DIRS["base"]) / "faiss_meta.json"


class VectorStore:
    def __init__(self, dim: int = 384, dedupe_threshold: float = None):
        self.dim = dim
        self.dedupe_threshold = dedupe_threshold if dedupe_threshold is not None else Config.DEDUPE_DISTANCE
        self.lock = threading.Lock()
        os.makedirs(STORAGE_DIRS["base"], exist_ok=True)
        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            try:
                self.index = faiss.read_index(str(INDEX_PATH))
                with open(META_PATH, "r", encoding="utf-8") as file:
                    self.meta = json.load(file)
                if self.index.d != self.dim:
                    raise ValueError(f"index dimension {self.index.d} != translator dimension {self.dim}")
            except Exception:
                self._new_index()
        else:
            self._new_index()
        self.next_id = len(self.meta)

    def _new_index(self):
        self.index = faiss.IndexFlatL2(self.dim)
        self.meta = {}

    def add(self, metadata: dict, vector: np.ndarray):
        if vector is None:
            raise ValueError("vector is None")
        vec = vector.reshape(1, -1).astype("float32")
        if vec.shape[1] != self.dim:
            raise ValueError(f"vector dimension {vec.shape[1]} does not match index dimension {self.dim}")

        if self.index.ntotal > 0:
            distances, indices = self.index.search(vec, 1)
            if distances[0][0] < self.dedupe_threshold:
                idx = int(indices[0][0])
                entry = self.meta.get(str(idx), {})
                existing_meta = entry.get("metadata", {})
                sources = set(existing_meta.get("sources", []))
                if metadata.get("source"):
                    sources.add(metadata.get("source"))
                tags = set(existing_meta.get("tags", []))
                tags.update(metadata.get("tags", []))
                existing_meta["sources"] = sorted(sources)
                existing_meta["tags"] = sorted(tags)
                existing_meta.setdefault("summary", metadata.get("summary", ""))
                entry["metadata"] = existing_meta
                self.meta[str(idx)] = entry
                self._persist()
                return entry.get("doc_id")

        with self.lock:
            self.index.add(vec)
            doc_id = uuid4().hex
            enriched_metadata = dict(metadata)
            enriched_metadata["sources"] = [metadata.get("source")] if metadata.get("source") else []
            enriched_metadata["tags"] = sorted(set(metadata.get("tags", [])))
            self.meta[str(self.next_id)] = {"doc_id": doc_id, "metadata": enriched_metadata}
            self.next_id += 1
            self._persist()
        return doc_id

    def search(self, vector: np.ndarray, top_k: int = 5):
        if vector is None or self.index.ntotal == 0:
            return []
        vec = vector.reshape(1, -1).astype("float32")
        if vec.shape[1] != self.dim:
            raise ValueError(f"vector dimension {vec.shape[1]} does not match index dimension {self.dim}")
        top_k = max(1, min(top_k, self.index.ntotal))
        distances, indices = self.index.search(vec, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            entry = self.meta.get(str(idx), {})
            results.append(
                {"doc_id": entry.get("doc_id"), "metadata": entry.get("metadata"), "distance": float(dist)}
            )
        return results

    def _persist(self):
        faiss.write_index(self.index, str(INDEX_PATH))
        with open(META_PATH, "w", encoding="utf-8") as file:
            json.dump(self.meta, file, indent=2)
