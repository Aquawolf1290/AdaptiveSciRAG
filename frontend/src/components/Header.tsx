import type { HealthResponse } from "../api";

interface HeaderProps {
  health: HealthResponse | null;
  healthLoading: boolean;
}

export default function Header({ health, healthLoading }: HeaderProps) {
  const online = !healthLoading && health !== null;

  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
            <path
              d="M4 5.5A1.5 1.5 0 0 1 5.5 4h9A1.5 1.5 0 0 1 16 5.5v13A1.5 1.5 0 0 0 17.5 20H6a2 2 0 0 1-2-2z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinejoin="round"
            />
            <path d="M7 8h6M7 11h6M7 14h3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </div>
        <div className="header-titles">
          <h1>Multimodal RAG</h1>
          <p>Question answering over scientific papers</p>
        </div>
      </div>

      <div className={`status-pill ${online ? "status-online" : "status-offline"}`}>
        <span className="status-dot" />
        {healthLoading ? (
          <span>Connecting…</span>
        ) : online ? (
          <span>
            Backend online
            {health?.provider && <span className="status-provider"> · {health.provider}</span>}
          </span>
        ) : (
          <span>Backend offline</span>
        )}
      </div>
    </header>
  );
}
