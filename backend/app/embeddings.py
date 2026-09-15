"""Embedding models: text (sentence-transformers) and image/text (CLIP).

Models are lazily loaded as module-level singletons so importing this module is
cheap and does not download weights until first use.
"""

from __future__ import annotations

import threading
import hashlib
import math
import re
from pathlib import Path

from PIL import Image

from .config import settings

_text_lock = threading.Lock()
_image_lock = threading.Lock()


class TextEmbedder:
    """Sentence-transformers embedder with normalized embeddings."""

    _instance: "TextEmbedder | None" = None

    def __init__(self) -> None:
        if settings.lightweight_embeddings:
            self._model = None
            return
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(settings.text_embed_model)

    @classmethod
    def instance(cls) -> "TextEmbedder":
        if cls._instance is None:
            with _text_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            return [self._hash_embed(text) for text in texts]
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    @staticmethod
    def _hash_embed(text: str, dimensions: int = 384) -> list[float]:
        """Create deterministic local vectors without downloading a model."""
        vector = [0.0] * dimensions
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class ImageEmbedder:
    """open_clip embedder mapping images and text into a shared CLIP space."""

    _instance: "ImageEmbedder | None" = None

    def __init__(self) -> None:
        import open_clip
        import torch

        self._torch = torch
        model, _, preprocess = open_clip.create_model_and_transforms(
            settings.clip_model, pretrained=settings.clip_pretrained
        )
        model.eval()
        self._model = model
        self._preprocess = preprocess
        self._tokenizer = open_clip.get_tokenizer(settings.clip_model)
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model.to(self._device)

    @classmethod
    def instance(cls) -> "ImageEmbedder":
        if cls._instance is None:
            with _image_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @staticmethod
    def _load_image(item: "Image.Image | str | Path") -> Image.Image:
        if isinstance(item, Image.Image):
            return item.convert("RGB")
        return Image.open(item).convert("RGB")

    def embed_images(self, images: list["Image.Image | str | Path"]) -> list[list[float]]:
        if not images:
            return []
        torch = self._torch
        tensors = [self._preprocess(self._load_image(img)) for img in images]
        batch = torch.stack(tensors).to(self._device)
        with torch.no_grad():
            features = self._model.encode_image(batch)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().tolist()

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        torch = self._torch
        tokens = self._tokenizer(texts).to(self._device)
        with torch.no_grad():
            features = self._model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().tolist()


def get_text_embedder() -> TextEmbedder:
    return TextEmbedder.instance()


def get_image_embedder() -> ImageEmbedder:
    return ImageEmbedder.instance()
