import json
import os
import time

from morpho_core.celery_app import celery
from morpho_core.config import Config


@celery.task(name="morpho_core.tasks.post_process")
def post_process_task(payload):
    print("[tasks] running post_process_task", payload)
    time.sleep(2)
    processed_dir = Config.ensure_storage_dirs()["processed"]
    out = {"status": "done", "input": payload}
    out_path = os.path.join(processed_dir, f"post_{int(time.time())}.json")
    with open(out_path, "w", encoding="utf-8") as file:
        json.dump(out, file, indent=2)
    return out_path


def enqueue_background_task(task_name, payload):
    try:
        if task_name == "post_process":
            post_process_task.apply_async(args=[payload])
            return True
    except Exception as exc:
        print("[tasks] enqueue error", exc)
        return False
    return False
