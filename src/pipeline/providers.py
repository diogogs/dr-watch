"""LLM providers behind one minimal interface, with an ordered fallback chain.

Free-tier strategy (charter): Gemini Flash is the workhorse, Groq the fallback. Models are
PINNED (energia-forecast lesson — "latest" aliases change under you); override via env when
a migration is deliberate. Providers return the raw JSON text; validation belongs to the
pipeline step, so a provider swap can never silently change the output contract.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from typing import Any, Protocol

import httpx

from src.config import Settings

logger = logging.getLogger("providers")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Free tiers rate-limit per MINUTE, not just per day (learned live on 2026-07-13: a 12-act
# day fired 24 requests in ~40s and got 429s). A 429 is transient by definition — wait out
# the window and retry before ever considering the provider failed.
MAX_429_RETRIES = 3


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    retry_after = response.headers.get("retry-after")
    if retry_after and retry_after.isdigit():
        return float(retry_after)
    return float(15 * 2**attempt)  # 15s, 30s, 60s


class ProviderError(RuntimeError):
    """The provider failed to produce a completion (transport, HTTP or shape errors)."""


class LlmProvider(Protocol):
    name: str

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> str: ...


class GeminiProvider:
    """Google Gemini via the REST API, with server-side JSON schema enforcement."""

    def __init__(
        self, api_key: str, model: str = "gemini-2.5-flash", client: httpx.Client | None = None
    ) -> None:
        self.name = f"gemini:{model}"
        self._api_key = api_key
        self._model = model
        self._client = client

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> str:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }
        owns = self._client is None
        client = self._client or httpx.Client(timeout=60)
        try:
            for attempt in range(MAX_429_RETRIES + 1):
                # Key goes in a HEADER, never the URL: exception messages and access logs
                # carry URLs, and a query-string key leaks straight into them.
                response = client.post(
                    GEMINI_URL.format(model=self._model),
                    headers={"x-goog-api-key": self._api_key},
                    json=body,
                )
                if response.status_code == 429 and attempt < MAX_429_RETRIES:
                    delay = _retry_delay(response, attempt)
                    logger.warning("%s: 429, retrying in %.0fs", self.name, delay)
                    time.sleep(delay)
                    continue
                response.raise_for_status()
                payload = response.json()
                return str(payload["candidates"][0]["content"]["parts"][0]["text"])
            raise ProviderError(f"{self.name}: exhausted 429 retries")  # pragma: no cover
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"{self.name}: {exc!r}") from exc
        finally:
            if owns:
                client.close()


class GroqProvider:
    """Groq's OpenAI-compatible API. JSON mode only (no server-side schema) — the pipeline's
    validation layer is what actually guarantees the contract, for every provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        client: httpx.Client | None = None,
    ) -> None:
        self.name = f"groq:{model}"
        self._api_key = api_key
        self._model = model
        self._client = client

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> str:
        body = {
            "model": self._model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        owns = self._client is None
        client = self._client or httpx.Client(timeout=60)
        try:
            response = client.post(
                GROQ_URL, headers={"Authorization": f"Bearer {self._api_key}"}, json=body
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
            return str(text)
        except Exception as exc:
            raise ProviderError(f"{self.name}: {exc!r}") from exc
        finally:
            if owns:
                client.close()


class FallbackChain:
    """Try providers in order; surface every failure if all of them fall over."""

    def __init__(self, providers: Sequence[LlmProvider]) -> None:
        if not providers:
            raise ValueError("FallbackChain needs at least one provider")
        self._providers = list(providers)
        self.name = " -> ".join(p.name for p in providers)

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> str:
        failures: list[str] = []
        for provider in self._providers:
            try:
                return provider.complete_json(prompt, schema)
            except ProviderError as exc:
                failures.append(str(exc))
        raise ProviderError(f"all providers failed: {failures}")


def provider_from_settings(settings: Settings) -> LlmProvider:
    """Build the configured chain: Gemini first, Groq as fallback, whichever keys exist."""
    chain: list[LlmProvider] = []
    if settings.gemini_api_key:
        chain.append(GeminiProvider(settings.gemini_api_key, settings.gemini_model))
    if settings.groq_api_key:
        chain.append(GroqProvider(settings.groq_api_key, settings.groq_model))
    if not chain:
        raise RuntimeError("No LLM provider configured — set GEMINI_API_KEY (and/or GROQ_API_KEY).")
    return FallbackChain(chain)
