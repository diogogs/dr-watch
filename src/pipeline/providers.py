"""LLM providers behind one minimal interface, with an ordered fallback chain.

Free-tier strategy (charter): Gemini Flash is the workhorse, Groq the fallback. Models are
PINNED (energia-forecast lesson — "latest" aliases change under you); override via env when
a migration is deliberate. Providers return the raw JSON text; validation belongs to the
pipeline step, so a provider swap can never silently change the output contract.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import httpx

from src.config import Settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


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
            # Key goes in a HEADER, never the URL: exception messages and access logs carry
            # URLs, and a query-string key leaks straight into them (learned the hard way).
            response = client.post(
                GEMINI_URL.format(model=self._model),
                headers={"x-goog-api-key": self._api_key},
                json=body,
            )
            response.raise_for_status()
            payload = response.json()
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            return str(text)
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
