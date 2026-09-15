"""Application configuration loaded from environment / .env.

All settings are overridable via environment variables. Defaults target a
free, fully-local stack (Ollama + sentence-transformers + CLIP) so the project
runs with no API keys or cost.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "ollama"
    frontend_origin: str = "http://localhost:5173"

    ollama_host: str = "http://localhost:11434"
    ollama_vision_model: str = "qwen3-vl:8b"

    text_embed_model: str = "BAAI/bge-small-en-v1.5"
    clip_model: str = "ViT-B-32"
    clip_pretrained: str = "laion2b_s34b_b79k"

    top_k_text: int = 5
    top_k_images: int = 3

    data_dir: str = "data"
    chroma_dir: str = "data/chroma"

    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    @property
    def data_path(self) -> Path:
        p = (REPO_ROOT / self.data_dir) if not Path(self.data_dir).is_absolute() else Path(self.data_dir)
        return p

    @property
    def figures_path(self) -> Path:
        return self.data_path / "figures"

    @property
    def pdfs_path(self) -> Path:
        return self.data_path / "pdfs"

    @property
    def chroma_path(self) -> Path:
        p = (REPO_ROOT / self.chroma_dir) if not Path(self.chroma_dir).is_absolute() else Path(self.chroma_dir)
        return p

    def ensure_dirs(self) -> None:
        for d in (self.data_path, self.figures_path, self.pdfs_path, self.chroma_path):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
