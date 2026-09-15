"""FastAPI application exposing the multimodal RAG backend."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import rag
from .config import settings
from .vector_store import get_vector_store

app = FastAPI(title="Multimodal RAG for Scientific Papers", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.frontend_origin.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    settings.ensure_dirs()


class PaperMeta(BaseModel):
    paper_id: str
    title: str
    n_pages: int
    n_text_chunks: int
    n_figures: int
    original_filename: str | None = None


class PaperSummary(BaseModel):
    paper_id: str
    title: str
    n_text_chunks: int
    n_figures: int


class ChatRequest(BaseModel):
    question: str
    paper_id: str | None = None


class TextCitation(BaseModel):
    id: str
    page: int | None = None
    snippet: str


class FigureCitation(BaseModel):
    id: str
    page: int | None = None
    path: str
    kind: str | None = None
    caption: str = ""
    url: str


class ChatResponse(BaseModel):
    answer: str
    error: str | None = None
    text_citations: list[TextCitation]
    figure_citations: list[FigureCitation]


class HealthResponse(BaseModel):
    status: str
    provider: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", provider=settings.llm_provider)


@app.post("/papers", response_model=PaperMeta)
async def upload_paper(file: UploadFile = File(...)) -> PaperMeta:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    settings.ensure_dirs()
    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
    dest = settings.pdfs_path / safe_name
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        meta = rag.ingest_paper(str(dest), original_filename=file.filename)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return PaperMeta(**meta)


@app.get("/papers", response_model=list[PaperSummary])
def list_papers() -> list[PaperSummary]:
    return [PaperSummary(**p) for p in get_vector_store().list_papers()]


@app.delete("/papers/{paper_id}")
def delete_paper(paper_id: str) -> dict:
    get_vector_store().delete_paper(paper_id)
    return {"status": "deleted", "paper_id": paper_id}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")
    result = rag.answer_question(req.question, paper_id=req.paper_id)
    return ChatResponse(**result)


@app.get("/figures/{figure_id}")
def get_figure(figure_id: str) -> FileResponse:
    path = get_vector_store().get_figure_path(figure_id)
    if not path:
        raise HTTPException(status_code=404, detail="Figure not found.")

    figures_root = settings.figures_path.resolve()
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(figures_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden path.") from None
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Figure file missing.")

    return FileResponse(str(resolved), media_type="image/png")
