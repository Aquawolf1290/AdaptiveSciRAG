# Backend

FastAPI backend for the Multimodal RAG project.

## Install & run

```bash
# from repo root
uv sync
cp .env.example .env   # optional; defaults work for local Ollama

uv run uvicorn backend.app.main:app --reload --port 8000
```

The API is then available at http://localhost:8000 (docs at `/docs`).

## LLM provider

Default provider is **Ollama** (local, free). Pull a vision model first:

```bash
ollama pull qwen3-vl:8b
```

Set `LLM_PROVIDER=bedrock` (plus `AWS_REGION` / `BEDROCK_MODEL_ID` and AWS creds) to
use AWS Bedrock Claude instead.

## Key environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama` or `bedrock` |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `OLLAMA_VISION_MODEL` | `qwen3-vl:8b` | Vision model name |
| `TEXT_EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | Text embedding model |
| `CLIP_MODEL` / `CLIP_PRETRAINED` | `ViT-B-32` / `laion2b_s34b_b79k` | CLIP image+text model |
| `TOP_K_TEXT` / `TOP_K_IMAGES` | `5` / `3` | Retrieval depth |
| `DATA_DIR` / `CHROMA_DIR` | `data` / `data/chroma` | Storage paths |

## Endpoints

- `POST /papers` — upload a PDF (multipart `file`), ingests + indexes it.
- `GET /papers` — list ingested papers.
- `DELETE /papers/{paper_id}` — remove a paper.
- `POST /chat` — `{question, paper_id?}` → answer with text + figure citations.
- `GET /figures/{figure_id}` — serve a figure PNG.
- `GET /health` — health + active provider.

## Scripts

```bash
uv run python scripts/fetch_sample_papers.py   # download sample arXiv PDFs
uv run python scripts/smoke_test.py            # ingest + retrieve end-to-end
```

The smoke test validates ingestion/retrieval even when no Ollama model is pulled
(it skips the generation assertion with a clear message in that case).
