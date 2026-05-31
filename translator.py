import hashlib
import re

import numpy as np
from sentence_transformers import SentenceTransformer


class MorphoTranslator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.dim = 384

    def _load_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.model_name, local_files_only=True)
            self.dim = self.model.get_sentence_embedding_dimension()
        return self.model

    def _fallback_encode(self, text: str):
        vector = np.zeros(self.dim, dtype="float32")
        tokens = re.findall(r"\b[a-z0-9]{2,}\b", text.lower())
        if not tokens:
            tokens = [text.lower()]
        features = list(tokens)
        features.extend(f"{left}_{right}" for left, right in zip(tokens, tokens[1:]))
        for token in features:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], byteorder="big", signed=False) % self.dim
            vector[bucket] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

    def encode(self, text: str):
        if not text:
            return None
        try:
            model = self._load_model()
            vector = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
            return np.array(vector, dtype="float32")
        except Exception:
            return self._fallback_encode(text)
