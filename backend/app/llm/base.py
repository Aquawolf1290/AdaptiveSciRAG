"""LLM provider interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    def generate(self, prompt: str, images: list[bytes] | None = None) -> str:
        """Generate a text response, optionally conditioned on image bytes (PNG)."""
        ...
