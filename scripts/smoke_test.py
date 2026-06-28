"""End-to-end smoke test: ingest a sample PDF, run text + figure queries.

Validates the RAG pipeline (ingestion -> embeddings -> vector store -> retrieval).
Generation via the LLM provider is exercised but treated as optional: if the
Ollama model isn't pulled / server is down, the test still PASSES on retrieval
and clearly SKIPS the generation check.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app import rag  # noqa: E402
from backend.app.vector_store import get_vector_store  # noqa: E402

SAMPLE_DIR = REPO_ROOT / "sample_papers"
SAMPLE_ID = "1706.03762"
SAMPLE_FILE = SAMPLE_DIR / "attention_is_all_you_need.pdf"


def ensure_sample() -> Path:
    if SAMPLE_FILE.exists() and SAMPLE_FILE.stat().st_size > 0:
        return SAMPLE_FILE
    print("Sample PDF missing; downloading...")
    import httpx

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://arxiv.org/pdf/{SAMPLE_ID}"
    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        resp = client.get(url, headers={"User-Agent": "multimodal-rag-smoke/0.1"})
        resp.raise_for_status()
        SAMPLE_FILE.write_bytes(resp.content)
    return SAMPLE_FILE


def main() -> int:
    failures: list[str] = []
    skips: list[str] = []

    print("== Multimodal RAG smoke test ==")

    pdf = ensure_sample()
    print(f"Sample: {pdf}")

    print("\n[1/4] Ingesting PDF...")
    meta = rag.ingest_paper(str(pdf), original_filename=pdf.name)
    print(f"  paper_id={meta['paper_id']} title={meta['title']!r}")
    print(f"  pages={meta['n_pages']} text_chunks={meta['n_text_chunks']} figures={meta['n_figures']}")
    paper_id = meta["paper_id"]

    if meta["n_text_chunks"] <= 0:
        failures.append("No text chunks produced during ingestion.")
    if meta["n_figures"] <= 0:
        failures.append("No figures produced during ingestion.")

    print("\n[2/4] Verifying paper is listed...")
    papers = get_vector_store().list_papers()
    if not any(p["paper_id"] == paper_id for p in papers):
        failures.append("Ingested paper not found in list_papers().")
    else:
        print(f"  list_papers() reports {len(papers)} paper(s).")

    print("\n[3/4] Text-only query...")
    res_text = rag.answer_question(
        "What is the core architecture proposed in this paper?", paper_id=paper_id
    )
    if not res_text["text_citations"]:
        failures.append("Text query returned no text_citations.")
    else:
        print(f"  text_citations={len(res_text['text_citations'])} "
              f"(pages: {[c['page'] for c in res_text['text_citations']]})")

    print("\n[4/4] Figure-referencing query...")
    res_fig = rag.answer_question("What does Figure 1 show?", paper_id=paper_id)
    if not res_fig["figure_citations"]:
        failures.append("Figure query returned no figure_citations.")
    else:
        first = res_fig["figure_citations"][0]
        print(f"  figure_citations={len(res_fig['figure_citations'])} "
              f"first url={first['url']}")
        if not Path(first["path"]).is_file():
            failures.append(f"Figure path does not exist: {first['path']}")
        else:
            print(f"  figure file exists: {first['path']}")

    # Generation is optional.
    gen_error = res_text.get("error") or res_fig.get("error")
    if gen_error:
        skips.append(f"LLM generation skipped (provider unavailable): {gen_error}")
    elif not (res_text["answer"] or res_fig["answer"]):
        skips.append("LLM returned empty answer; generation not verified.")
    else:
        print(f"\n  LLM answer (text query): {res_text['answer'][:200]}...")

    print("\n== Summary ==")
    for s in skips:
        print(f"[SKIP] {s}")
    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        print("\nRESULT: FAIL")
        return 1
    print("\nRESULT: PASS (retrieval pipeline validated)")
    if skips:
        print("Note: generation step skipped; pull the Ollama model to test it end-to-end.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
