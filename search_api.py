from morpho_core.translator import MorphoTranslator
from morpho_core.vector_store import VectorStore


translator = MorphoTranslator()


def semantic_search(query: str, top_k: int = 5):
    query = (query or "").strip()
    if not query:
        raise ValueError("query is required")
    top_k = max(1, min(int(top_k), 20))
    qv = translator.encode(query)
    vstore = VectorStore(dim=translator.dim)
    results = vstore.search(qv, top_k=top_k)
    return {"query": query, "count": len(results), "results": results}
