import datetime
import json
import logging
import os
from uuid import uuid4

from morpho_core.config import Config


logger = logging.getLogger("morpho.storage")


def store_processed_data(data: dict, base_dir: str = None):
    base = base_dir or Config.ensure_storage_dirs()["base"]
    processed_dir = os.path.join(base, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S_%f")
    fname = f"{timestamp}_{uuid4().hex[:8]}.json"
    file_path = os.path.join(processed_dir, fname)
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        logger.info("[storage_manager] stored processed data at: %s", file_path)
        return file_path
    except Exception as exc:
        logger.exception("[storage_manager] error storing: %s", exc)
        return None
