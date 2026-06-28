"""PDF ingestion: text chunking and figure extraction using PyMuPDF."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

import fitz  # PyMuPDF

from .config import settings

CHUNK_TARGET = 1000
CHUNK_OVERLAP = 150
PAGE_RENDER_ZOOM = 2.0


@dataclass
class TextChunk:
    id: str
    paper_id: str
    page: int
    text: str

    def to_dict(self) -> dict:
        return {"id": self.id, "paper_id": self.paper_id, "page": self.page, "text": self.text}


@dataclass
class Figure:
    id: str
    paper_id: str
    page: int
    path: str
    kind: str  # "embedded" | "page"
    caption: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "page": self.page,
            "path": self.path,
            "kind": self.kind,
            "caption": self.caption,
        }


@dataclass
class IngestResult:
    paper_id: str
    title: str
    n_pages: int
    text_chunks: list[TextChunk] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "n_pages": self.n_pages,
            "n_text_chunks": len(self.text_chunks),
            "n_figures": len(self.figures),
        }


def _short_id() -> str:
    return uuid.uuid4().hex[:12]


def _normalize_ws(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_units(text: str) -> list[str]:
    """Split text into reasonably sized units on paragraph/sentence boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[str] = []
    for para in paragraphs:
        if len(para) <= CHUNK_TARGET:
            units.append(para)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para)
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(sent) <= CHUNK_TARGET:
                units.append(sent)
            else:
                for i in range(0, len(sent), CHUNK_TARGET):
                    units.append(sent[i : i + CHUNK_TARGET])
    return units


def chunk_text(text: str) -> list[str]:
    """Greedily pack text units into ~CHUNK_TARGET chunks with overlap."""
    text = _normalize_ws(text)
    if not text:
        return []
    units = _split_units(text)
    chunks: list[str] = []
    current = ""
    for unit in units:
        if not current:
            current = unit
        elif len(current) + 1 + len(unit) <= CHUNK_TARGET:
            current = f"{current} {unit}"
        else:
            chunks.append(current)
            tail = current[-CHUNK_OVERLAP:] if CHUNK_OVERLAP else ""
            current = f"{tail} {unit}".strip() if tail else unit
    if current:
        chunks.append(current)
    return chunks


def _extract_title(doc: fitz.Document) -> str:
    meta_title = (doc.metadata or {}).get("title") or ""
    meta_title = meta_title.strip()
    if meta_title and len(meta_title) > 4:
        return meta_title
    if doc.page_count == 0:
        return "Untitled"
    page = doc.load_page(0)
    blocks = page.get_text("dict").get("blocks", [])
    best_text = ""
    best_size = 0.0
    for block in blocks:
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            size = max(s.get("size", 0.0) for s in spans)
            line_text = "".join(s.get("text", "") for s in spans).strip()
            if not line_text or len(line_text) < 4:
                continue
            # Skip arXiv/journal stamps that are rendered in a large vertical font.
            if re.match(r"^(arxiv:|doi:|https?://)", line_text, flags=re.IGNORECASE):
                continue
            if size > best_size:
                best_size = size
                best_text = line_text
    return best_text or "Untitled"


def _find_caption(page: fitz.Page) -> str:
    """Best-effort: first text line on the page starting with Fig/Figure."""
    text = page.get_text("text")
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^(fig\.?|figure)\b", stripped, flags=re.IGNORECASE):
            return stripped[:300]
    return ""


def _extract_embedded_images(
    doc: fitz.Document, page: fitz.Page, paper_id: str, page_num: int, caption: str
) -> list[Figure]:
    figures: list[Figure] = []
    seen_xrefs: set[int] = set()
    for img in page.get_images(full=True):
        xref = img[0]
        if xref in seen_xrefs:
            continue
        seen_xrefs.add(xref)
        try:
            base = doc.extract_image(xref)
        except Exception:
            continue
        if not base:
            continue
        try:
            pix = fitz.Pixmap(doc, xref)
            if pix.n - pix.alpha >= 4:  # CMYK -> RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
            smask = img[1]
            if smask:
                try:
                    mask = fitz.Pixmap(doc, smask)
                    pix = fitz.Pixmap(pix, mask)
                except Exception:
                    pass
            if pix.width < 32 or pix.height < 32:
                pix = None
                continue
            fig_id = _short_id()
            out_path = settings.figures_path / f"{paper_id}_{fig_id}.png"
            pix.save(str(out_path))
            pix = None
        except Exception:
            continue
        figures.append(
            Figure(
                id=fig_id,
                paper_id=paper_id,
                page=page_num,
                path=str(out_path),
                kind="embedded",
                caption=caption,
            )
        )
    return figures


def _render_page(
    page: fitz.Page, paper_id: str, page_num: int, caption: str
) -> Figure:
    fig_id = _short_id()
    out_path = settings.figures_path / f"{paper_id}_page{page_num}_{fig_id}.png"
    matrix = fitz.Matrix(PAGE_RENDER_ZOOM, PAGE_RENDER_ZOOM)
    pix = page.get_pixmap(matrix=matrix)
    pix.save(str(out_path))
    return Figure(
        id=fig_id,
        paper_id=paper_id,
        page=page_num,
        path=str(out_path),
        kind="page",
        caption=caption,
    )


def ingest_pdf(paper_id: str, pdf_path: str) -> IngestResult:
    """Extract text chunks and figures from a PDF."""
    settings.ensure_dirs()
    doc = fitz.open(pdf_path)
    try:
        title = _extract_title(doc)
        result = IngestResult(paper_id=paper_id, title=title, n_pages=doc.page_count)

        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            page_num = page_index + 1
            page_text = page.get_text("text")
            for chunk in chunk_text(page_text):
                result.text_chunks.append(
                    TextChunk(
                        id=_short_id(),
                        paper_id=paper_id,
                        page=page_num,
                        text=chunk,
                    )
                )

            caption = _find_caption(page)
            result.figures.extend(
                _extract_embedded_images(doc, page, paper_id, page_num, caption)
            )
            result.figures.append(_render_page(page, paper_id, page_num, caption))

        return result
    finally:
        doc.close()
