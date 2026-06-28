"""RAG orchestration: ingestion + multimodal retrieval + answer generation."""

from __future__ import annotations

import uuid
from pathlib import Path

from .config import settings
from .embeddings import get_image_embedder, get_text_embedder
from .ingestion import ingest_pdf
from .llm.factory import get_llm_provider
from .vector_store import get_vector_store

ANSWER_SYSTEM = (
    "You are a research assistant answering questions about a scientific paper. "
    "Use ONLY the provided text context and figures to answer. Cite the page "
    "number(s) you used in the form (p. N). If the answer is not in the context, "
    "say so. Be concise and precise."
)


def ingest_paper(pdf_path: str, original_filename: str | None = None) -> dict:
    paper_id = uuid.uuid4().hex[:12]
    result = ingest_pdf(paper_id, pdf_path)

    store = get_vector_store()

    text_records = [c.to_dict() for c in result.text_chunks]
    if text_records:
        text_embedder = get_text_embedder()
        text_vecs = text_embedder.embed([r["text"] for r in text_records])
        store.add_text_chunks(text_records, text_vecs, title=result.title)

    figure_records = [f.to_dict() for f in result.figures]
    if figure_records:
        image_embedder = get_image_embedder()
        image_vecs = image_embedder.embed_images([r["path"] for r in figure_records])
        store.add_figures(figure_records, image_vecs, title=result.title)

    meta = result.to_dict()
    meta["original_filename"] = original_filename
    return meta


def _load_image_bytes(path: str) -> bytes | None:
    try:
        return Path(path).read_bytes()
    except OSError:
        return None


def _build_prompt(question: str, text_hits: list[dict]) -> str:
    context_blocks = []
    for hit in text_hits:
        page = hit["metadata"].get("page", "?")
        context_blocks.append(f"[Page {page}] {hit['document']}")
    context = "\n\n".join(context_blocks) if context_blocks else "(no text retrieved)"
    return (
        f"{ANSWER_SYSTEM}\n\n"
        f"=== TEXT CONTEXT ===\n{context}\n\n"
        f"=== FIGURES ===\n"
        f"The attached images are figures/pages retrieved from the paper, in order.\n\n"
        f"=== QUESTION ===\n{question}\n\n"
        f"Answer using the context and figures above, citing pages."
    )


def answer_question(question: str, paper_id: str | None = None) -> dict:
    store = get_vector_store()

    text_embedder = get_text_embedder()
    image_embedder = get_image_embedder()

    text_qvec = text_embedder.embed([question])[0]
    text_hits = store.query_text(text_qvec, settings.top_k_text, paper_id=paper_id)

    image_qvec = image_embedder.embed_text([question])[0]
    figure_hits = store.query_images(image_qvec, settings.top_k_images, paper_id=paper_id)

    images: list[bytes] = []
    figure_citations: list[dict] = []
    for hit in figure_hits:
        meta = hit["metadata"]
        path = meta.get("path", "")
        img_bytes = _load_image_bytes(path)
        if img_bytes is not None:
            images.append(img_bytes)
        figure_citations.append(
            {
                "id": hit["id"],
                "page": meta.get("page"),
                "path": path,
                "kind": meta.get("kind"),
                "caption": meta.get("caption", ""),
                "url": f"/figures/{hit['id']}",
            }
        )

    text_citations = [
        {
            "id": hit["id"],
            "page": hit["metadata"].get("page"),
            "snippet": (hit["document"] or "")[:300],
        }
        for hit in text_hits
    ]

    prompt = _build_prompt(question, text_hits)

    answer: str
    error: str | None = None
    try:
        provider = get_llm_provider()
        answer = provider.generate(prompt, images=images or None)
    except Exception as exc:  # noqa: BLE001
        answer = ""
        error = str(exc)

    return {
        "answer": answer,
        "error": error,
        "text_citations": text_citations,
        "figure_citations": figure_citations,
    }
