import json
import logging
import os
import shutil

import requests

from morpho_core.config import Config


logger = logging.getLogger("morpho.ai")


class MockAdapter:
    def call(
        self,
        prompt: str,
        context=None,
        previous_response_id: str | None = None,
        system_prompt: str | None = None,
    ):
        ctx = context or []
        return {
            "mode": "mock",
            "response_text": f"[MOCK] Prompt='{prompt[:200]}' | ctx_count={len(ctx)}",
            "context_items": len(ctx),
            "previous_response_id": previous_response_id,
            "system_prompt": system_prompt,
        }


class OpenAIAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def call(
        self,
        prompt: str,
        context=None,
        previous_response_id: str | None = None,
        system_prompt: str | None = None,
    ):
        if not self.api_key:
            raise RuntimeError("OpenAI key not set")

        url = f"{Config.OPENAI_BASE_URL.rstrip('/')}/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        context = context or []
        system_prompt = system_prompt or Config.OPENAI_SYSTEM_PROMPT
        if context:
            context_block = "\n\n".join(f"- {item}" for item in context if item)
            user_prompt = f"Context:\n{context_block}\n\nUser request:\n{prompt}"
        else:
            user_prompt = prompt

        input_items = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_prompt,
                    }
                ],
            }
        ]
        payload = {
            "model": Config.OPENAI_MODEL,
            "instructions": system_prompt,
            "input": input_items,
            "max_output_tokens": 512,
        }
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=Config.OPENAI_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
        output_text = body.get("output_text", "")
        if not output_text:
            try:
                output = body.get("output") or []
                texts = []
                for item in output:
                    for content_item in item.get("content", []):
                        if content_item.get("type") == "output_text" and content_item.get("text"):
                            texts.append(content_item["text"])
                output_text = "\n".join(texts).strip()
            except Exception:
                output_text = ""
        return {
            "mode": "external",
            "provider": "openai",
            "model": body.get("model", Config.OPENAI_MODEL),
            "response_id": body.get("id"),
            "response_text": output_text,
            "context_items": len(context),
            "raw": body,
        }


class OllamaAdapter:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _build_prompt(self, prompt: str, context=None, system_prompt: str | None = None) -> str:
        context = [
            str(item)[: Config.OLLAMA_CONTEXT_CHARS]
            for item in (context or [])[: Config.OLLAMA_CONTEXT_ITEMS]
            if item
        ]
        parts = []
        if system_prompt:
            parts.append(f"System:\n{system_prompt}")
        if context:
            context_block = "\n\n".join(f"- {item}" for item in context if item)
            parts.append(f"Relevant context:\n{context_block}")
        parts.append(f"User request:\n{prompt}")
        return "\n\n".join(parts)

    def call(
        self,
        prompt: str,
        context=None,
        previous_response_id: str | None = None,
        system_prompt: str | None = None,
    ):
        payload = {
            "model": self.model,
            "prompt": self._build_prompt(prompt, context=context, system_prompt=system_prompt or Config.OPENAI_SYSTEM_PROMPT),
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": Config.OLLAMA_NUM_PREDICT,
                "num_ctx": 2048,
            },
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=Config.OLLAMA_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            body = response.json()
        except requests.exceptions.Timeout:
            logger.warning("Ollama timed out for model %s", self.model)
            return {
                "mode": "local",
                "provider": "ollama",
                "model": self.model,
                "response_id": None,
                "response_text": "Morpho reached the local Llama server, but it took too long to answer. Try a shorter prompt or restart Ollama if this repeats.",
                "context_items": len(context or []),
                "previous_response_id": previous_response_id,
                "raw": {"error": "ollama_timeout"},
            }
        return {
            "mode": "local",
            "provider": "ollama",
            "model": body.get("model", self.model),
            "response_id": body.get("created_at"),
            "response_text": body.get("response", "").strip(),
            "context_items": len(context or []),
            "previous_response_id": previous_response_id,
            "raw": body,
        }


def _ollama_available() -> bool:
    if not (Config.has_ollama_binary() or shutil.which("ollama")):
        return False
    try:
        response = requests.get(f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=2)
        response.raise_for_status()
        return True
    except Exception:
        return False


def ai_talk(
    prompt: str,
    use_external: bool = False,
    previous_response_id: str | None = None,
    system_prompt: str | None = None,
    additional_context: list[str] | None = None,
    include_processed_context: bool = True,
    max_context_items: int | None = None,
):
    processed_dir = Config.ensure_storage_dirs()["processed"]
    ctx = []
    if include_processed_context and os.path.isdir(processed_dir):
        files = sorted(os.listdir(processed_dir), reverse=True)[:6]
        for filename in files:
            try:
                with open(os.path.join(processed_dir, filename), "r", encoding="utf-8") as file:
                    doc = json.load(file)
                    ctx.append((doc.get("summary") or doc.get("cleaned", "")[:300])[: Config.OLLAMA_CONTEXT_CHARS])
            except Exception:
                logger.debug("Skipping malformed context file %s", filename, exc_info=True)
                continue
    if additional_context:
        ctx = [str(item)[: Config.OLLAMA_CONTEXT_CHARS] for item in additional_context if item] + ctx
    if max_context_items is not None:
        ctx = ctx[:max_context_items]
    provider = (Config.AI_PROVIDER or "auto").strip().lower()
    adapter = None

    if provider in {"ollama", "local"} or (provider == "auto" and not use_external and _ollama_available()):
        adapter = OllamaAdapter(Config.OLLAMA_BASE_URL, Config.OLLAMA_MODEL)
    elif (provider == "openai" or use_external or provider == "auto") and Config.OPENAI_API_KEY:
        adapter = OpenAIAdapter(Config.OPENAI_API_KEY)
    else:
        adapter = MockAdapter()

    return adapter.call(
        (prompt or "").strip(),
        context=ctx,
        previous_response_id=previous_response_id,
        system_prompt=system_prompt,
    )
