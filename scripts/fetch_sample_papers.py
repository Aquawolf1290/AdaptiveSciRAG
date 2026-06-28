"""Download a couple of open-access arXiv PDFs into sample_papers/."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "sample_papers"

# arXiv id -> output filename. Both are open access with clear figures.
PAPERS: dict[str, str] = {
    "1706.03762": "attention_is_all_you_need.pdf",  # Transformer (Figure 1 architecture)
    "1512.03385": "resnet.pdf",  # ResNet (clear architecture figures)
}


def arxiv_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}"


def download(arxiv_id: str, filename: str) -> Path:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    dest = SAMPLE_DIR / filename
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {filename} already exists ({dest.stat().st_size} bytes)")
        return dest

    url = arxiv_url(arxiv_id)
    print(f"[get ] {url} -> {dest}")
    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        resp = client.get(url, headers={"User-Agent": "multimodal-rag-sample/0.1"})
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    print(f"[ok  ] wrote {dest.stat().st_size} bytes")
    return dest


def main(argv: list[str]) -> int:
    papers = dict(PAPERS)
    # allow `python fetch_sample_papers.py <arxiv_id> [<arxiv_id> ...]`
    if len(argv) > 1:
        papers = {aid: f"{aid}.pdf" for aid in argv[1:]}

    for arxiv_id, filename in papers.items():
        try:
            download(arxiv_id, filename)
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] {arxiv_id}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
