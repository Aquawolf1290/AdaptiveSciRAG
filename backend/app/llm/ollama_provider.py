"""Ollama LLM provider (local, default)."""

from __future__ import annotations

import base64

import httpx

from ..config import settings


class OllamaError(RuntimeError):
    pass


class OllamaProvider:
    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self._host = (host or settings.ollama_host).rstrip("/")
        self._model = model or settings.ollama_vision_model
        self._timeout = timeout

    def generate(self, prompt: str, images: list[bytes] | None = None) -> str:
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            # The default Ollama context (4096) is too small for multi-chunk RAG
            # prompts that also carry figure context, so widen it.
            "options": {"num_ctx": 8192},
        }
        if images:
            payload["images"] = [base64.b64encode(img).decode("ascii") for img in images]

        url = f"{self._host}/api/generate"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url, json=payload)
        except httpx.ConnectError as exc:
            raise OllamaError(
                f"Could not connect to Ollama at {self._host}. "
                "Is `ollama serve` running?"
            ) from exc

        if resp.status_code == 404:
            raise OllamaError(
                f"Ollama model '{self._model}' not found. "
                f"Pull it first: `ollama pull {self._model}`."
            )
        if resp.status_code >= 400:
            detail = resp.text
            if self._model in detail and "not found" in detail.lower():
                raise OllamaError(
                    f"Ollama model '{self._model}' is not pulled. "
                    f"Run: `ollama pull {self._model}`."
                )
            raise OllamaError(f"Ollama request failed ({resp.status_code}): {detail}")

        data = resp.json()
        return (data.get("response") or "").strip()
