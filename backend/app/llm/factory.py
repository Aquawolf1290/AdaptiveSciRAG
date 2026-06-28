"""LLM provider factory based on settings.llm_provider."""

from __future__ import annotations

from ..config import settings
from .base import LLMProvider


def get_llm_provider() -> LLMProvider:
    provider = (settings.llm_provider or "ollama").lower()
    if provider == "ollama":
        from .ollama_provider import OllamaProvider

        return OllamaProvider()
    if provider == "bedrock":
        from .bedrock_provider import BedrockProvider

        return BedrockProvider()
    raise ValueError(
        f"Unknown LLM provider '{settings.llm_provider}'. Use 'ollama' or 'bedrock'."
    )
