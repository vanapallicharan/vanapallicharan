import datetime
import logging

from morpho_core.preprocessor import analyze_content
from morpho_core.storage_manager import store_processed_data
from morpho_core.translator import MorphoTranslator
from morpho_core.vector_store import VectorStore


logger = logging.getLogger("morpho.processor")

translator = MorphoTranslator()
vstore = VectorStore(dim=translator.dim)


def process_input(payload: dict):
    """Main ingest pipeline with best-effort storage and indexing."""
    analyzed = analyze_content(payload)
    if not analyzed.get("cleaned"):
        raise ValueError("content is empty after preprocessing")

    file_path = store_processed_data(analyzed)
    if not file_path:
        raise RuntimeError("failed to persist processed payload")

    summary_text = analyzed.get("summary") or analyzed.get("cleaned", "")[:300]
    embedding = translator.encode(summary_text)

    metadata = {
        "type": analyzed.get("type"),
        "source": analyzed.get("source"),
        "local_path": file_path,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "tags": analyzed.get("tags", []),
        "summary": analyzed.get("summary", ""),
    }

    doc_id = None
    warnings = []
    try:
        doc_id = vstore.add(metadata, embedding)
        logger.info("[processor] Added document %s to vector store", doc_id)
    except Exception as exc:
        warnings.append("vector_index_unavailable")
        logger.error("[processor] Vector add error: %s", exc)

    logger.info("[processor] Background task skipped (Celery disabled)")

    return {
        "status": "success",
        "digest": "processed and stored",
        "local_path": file_path,
        "doc_id": doc_id,
        "tags": metadata["tags"],
        "summary": metadata["summary"],
        "warnings": warnings,
    }
