"""ChromaDB persistent vector store for text chunks and figures."""

from __future__ import annotations

from typing import Any

import chromadb

from .config import settings

TEXT_COLLECTION = "text_chunks"
FIGURES_COLLECTION = "figures"


class VectorStore:
    def __init__(self) -> None:
        settings.ensure_dirs()
        self._client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self._text = self._client.get_or_create_collection(
            name=TEXT_COLLECTION, metadata={"hnsw:space": "cosine"}
        )
        self._figures = self._client.get_or_create_collection(
            name=FIGURES_COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def add_text_chunks(
        self, records: list[dict], embeddings: list[list[float]], title: str = ""
    ) -> None:
        if not records:
            return
        ids = [r["id"] for r in records]
        documents = [r["text"] for r in records]
        metadatas = [
            {
                "paper_id": r["paper_id"],
                "page": r["page"],
                "title": title,
                "kind": "text",
            }
            for r in records
        ]
        self._text.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def add_figures(
        self, records: list[dict], embeddings: list[list[float]], title: str = ""
    ) -> None:
        if not records:
            return
        ids = [r["id"] for r in records]
        documents = [r.get("caption", "") or "" for r in records]
        metadatas = [
            {
                "paper_id": r["paper_id"],
                "page": r["page"],
                "path": r["path"],
                "kind": r["kind"],
                "caption": r.get("caption", "") or "",
                "title": title,
            }
            for r in records
        ]
        self._figures.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    @staticmethod
    def _where(paper_id: str | None) -> dict | None:
        return {"paper_id": paper_id} if paper_id else None

    def query_text(
        self, query_embedding: list[float], k: int, paper_id: str | None = None
    ) -> list[dict]:
        res = self._text.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=self._where(paper_id),
            include=["documents", "metadatas", "distances"],
        )
        return self._unpack(res)

    def query_images(
        self, query_embedding: list[float], k: int, paper_id: str | None = None
    ) -> list[dict]:
        res = self._figures.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=self._where(paper_id),
            include=["documents", "metadatas", "distances"],
        )
        return self._unpack(res)

    @staticmethod
    def _unpack(res: dict) -> list[dict]:
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        out: list[dict] = []
        for i, _id in enumerate(ids):
            meta = metas[i] if i < len(metas) else {}
            out.append(
                {
                    "id": _id,
                    "document": docs[i] if i < len(docs) else "",
                    "metadata": meta or {},
                    "distance": dists[i] if i < len(dists) else None,
                }
            )
        return out

    def get_figure_path(self, figure_id: str) -> str | None:
        res = self._figures.get(ids=[figure_id], include=["metadatas"])
        metas = res.get("metadatas") or []
        if not metas:
            return None
        return (metas[0] or {}).get("path")

    def list_papers(self) -> list[dict]:
        papers: dict[str, dict[str, Any]] = {}

        text_res = self._text.get(include=["metadatas"])
        for meta in text_res.get("metadatas") or []:
            meta = meta or {}
            pid = meta.get("paper_id")
            if pid is None:
                continue
            entry = papers.setdefault(
                pid, {"paper_id": pid, "title": "", "n_text_chunks": 0, "n_figures": 0}
            )
            entry["n_text_chunks"] += 1
            if not entry["title"] and meta.get("title"):
                entry["title"] = meta["title"]

        fig_res = self._figures.get(include=["metadatas"])
        for meta in fig_res.get("metadatas") or []:
            meta = meta or {}
            pid = meta.get("paper_id")
            if pid is None:
                continue
            entry = papers.setdefault(
                pid, {"paper_id": pid, "title": "", "n_text_chunks": 0, "n_figures": 0}
            )
            entry["n_figures"] += 1
            if not entry["title"] and meta.get("title"):
                entry["title"] = meta["title"]

        return list(papers.values())

    def delete_paper(self, paper_id: str) -> None:
        where = {"paper_id": paper_id}
        self._text.delete(where=where)
        self._figures.delete(where=where)


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
