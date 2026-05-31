from celery import Celery

from morpho_core.config import Config


celery = Celery("morpho_tasks", broker=Config.REDIS_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)
celery.conf.task_routes = {"morpho_core.tasks.*": {"queue": "morpho_tasks"}}
