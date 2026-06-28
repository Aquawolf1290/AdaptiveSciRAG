import type { Paper } from "../api";
import UploadPanel from "./UploadPanel";

interface SidebarProps {
  papers: Paper[];
  loading: boolean;
  error: string | null;
  selectedPaperId: string | null;
  onSelect: (paperId: string | null) => void;
  onDelete: (paperId: string) => void;
  onUploaded: () => void;
}

function paperMeta(paper: Paper): string {
  const parts: string[] = [];
  if (typeof paper.n_chunks === "number") parts.push(`${paper.n_chunks} chunks`);
  if (typeof paper.n_figures === "number") parts.push(`${paper.n_figures} figures`);
  return parts.join(" · ");
}

export default function Sidebar({
  papers,
  loading,
  error,
  selectedPaperId,
  onSelect,
  onDelete,
  onUploaded,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <UploadPanel onUploaded={onUploaded} />

      <div className="sidebar-section">
        <h2 className="sidebar-heading">Library</h2>

        <button
          type="button"
          className={`paper-item paper-all ${selectedPaperId === null ? "paper-active" : ""}`}
          onClick={() => onSelect(null)}
        >
          <span className="paper-title">All papers</span>
          <span className="paper-meta">{papers.length} ingested</span>
        </button>

        {loading && <p className="sidebar-hint">Loading papers…</p>}
        {error && <p className="sidebar-error">{error}</p>}
        {!loading && !error && papers.length === 0 && (
          <p className="sidebar-hint">No papers yet. Upload a PDF to get started.</p>
        )}

        <ul className="paper-list">
          {papers.map((paper) => {
            const active = paper.paper_id === selectedPaperId;
            const meta = paperMeta(paper);
            return (
              <li key={paper.paper_id}>
                <div className={`paper-item ${active ? "paper-active" : ""}`}>
                  <button type="button" className="paper-select" onClick={() => onSelect(paper.paper_id)}>
                    <span className="paper-title">{paper.title}</span>
                    {meta && <span className="paper-meta">{meta}</span>}
                  </button>
                  <button
                    type="button"
                    className="paper-delete"
                    title="Delete paper"
                    aria-label={`Delete ${paper.title}`}
                    onClick={() => onDelete(paper.paper_id)}
                  >
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" aria-hidden="true">
                      <path
                        d="M5 7h14M10 7V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}
