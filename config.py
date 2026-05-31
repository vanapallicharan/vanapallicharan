import os
from pathlib import Path
import shutil

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    PACKAGE_ROOT = Path(__file__).resolve().parent
    STORAGE_BASE = str(
        Path(os.getenv("MORPHO_STORAGE_BASE") or PACKAGE_ROOT / "data").expanduser()
    )
    AI_PROVIDER = os.getenv("MORPHO_AI_PROVIDER", "auto")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_SYSTEM_PROMPT = os.getenv(
        "OPENAI_SYSTEM_PROMPT",
        "You are Morpho assistant. Be accurate, concise, and helpful.",
    )
    OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")
    OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
    OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "160"))
    OLLAMA_CONTEXT_ITEMS = int(os.getenv("OLLAMA_CONTEXT_ITEMS", "4"))
    OLLAMA_CONTEXT_CHARS = int(os.getenv("OLLAMA_CONTEXT_CHARS", "600"))
    DASHBOARD_FAST_CHAT = _as_bool(os.getenv("MORPHO_DASHBOARD_FAST_CHAT"), default=True)
    MEMORY_TOP_K = int(os.getenv("MORPHO_MEMORY_TOP_K", "5"))
    MEMORY_HISTORY_WINDOW = int(os.getenv("MORPHO_HISTORY_WINDOW", "6"))
    MEMORY_FACT_LIMIT = int(os.getenv("MORPHO_FACT_LIMIT", "4"))
    DISTILLATION_SIMILARITY_THRESHOLD = float(os.getenv("MORPHO_DISTILLATION_SIMILARITY_THRESHOLD", "0.85"))
    DISTILLATION_USE_LLM_MERGE = _as_bool(os.getenv("MORPHO_DISTILLATION_USE_LLM_MERGE"), default=True)
    SAFE_MODE = _as_bool(os.getenv("MORPHO_SAFE_MODE"), default=True)
    AUTO_MODE = _as_bool(os.getenv("MORPHO_AUTO_MODE"), default=False)
    ACTIVITY_MONITOR_DEFAULT = _as_bool(os.getenv("MORPHO_ACTIVITY_MONITOR_DEFAULT"), default=False)
    SCREEN_OBSERVER_DEFAULT = _as_bool(os.getenv("MORPHO_SCREEN_OBSERVER_DEFAULT"), default=False)
    SCREEN_CAPTURE_INTERVAL_SECONDS = int(os.getenv("MORPHO_SCREEN_CAPTURE_INTERVAL_SECONDS", "30"))
    OCR_ENABLED = _as_bool(os.getenv("MORPHO_OCR_ENABLED"), default=False)
    CODE_AGENT_MAX_FILE_BYTES = int(os.getenv("MORPHO_CODE_AGENT_MAX_FILE_BYTES", "200000"))
    REALTIME_LOOP_INTERVAL_SECONDS = int(os.getenv("MORPHO_REALTIME_LOOP_INTERVAL_SECONDS", "20"))
    SUGGESTION_COOLDOWN_SECONDS = int(os.getenv("MORPHO_SUGGESTION_COOLDOWN_SECONDS", "45"))
    SUGGESTION_MAX_VISIBLE = int(os.getenv("MORPHO_SUGGESTION_MAX_VISIBLE", "6"))
    ACTION_CACHE_TTL_SECONDS = int(os.getenv("MORPHO_ACTION_CACHE_TTL_SECONDS", "120"))
    DEDUPE_DISTANCE = float(os.getenv("DEDUPE_DISTANCE", "0.35"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "1000000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    MORPHO_DEBUG = _as_bool(os.getenv("MORPHO_DEBUG"), default=False)

    @classmethod
    def ensure_storage_dirs(cls) -> dict[str, str]:
        base = Path(cls.STORAGE_BASE)
        raw = base / "raw"
        processed = base / "processed"
        conversations = base / "conversations"
        memories = base / "memories"
        knowledge = base / "knowledge"
        logs = base / "logs"
        screens = base / "screens"
        state = base / "state"
        base.mkdir(parents=True, exist_ok=True)
        raw.mkdir(parents=True, exist_ok=True)
        processed.mkdir(parents=True, exist_ok=True)
        conversations.mkdir(parents=True, exist_ok=True)
        memories.mkdir(parents=True, exist_ok=True)
        knowledge.mkdir(parents=True, exist_ok=True)
        logs.mkdir(parents=True, exist_ok=True)
        screens.mkdir(parents=True, exist_ok=True)
        state.mkdir(parents=True, exist_ok=True)
        return {
            "base": str(base),
            "raw": str(raw),
            "processed": str(processed),
            "conversations": str(conversations),
            "memories": str(memories),
            "knowledge": str(knowledge),
            "logs": str(logs),
            "screens": str(screens),
            "state": str(state),
        }

    @classmethod
    def has_ollama_binary(cls) -> bool:
        return shutil.which("ollama") is not None
