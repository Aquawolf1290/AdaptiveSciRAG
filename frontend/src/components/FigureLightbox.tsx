import { useEffect } from "react";
import type { FigureCitation } from "../api";
import { figureUrl } from "../api";

interface FigureLightboxProps {
  figure: FigureCitation;
  onClose: () => void;
}

export default function FigureLightbox({ figure, onClose }: FigureLightboxProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="lightbox-backdrop" onClick={onClose} role="presentation">
      <div className="lightbox" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <button type="button" className="lightbox-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <img src={figureUrl(figure.url)} alt={figure.caption ?? `Figure ${figure.id}`} />
        <div className="lightbox-caption">
          <span className="lightbox-page">Page {figure.page}</span>
          {figure.caption && <span>{figure.caption}</span>}
        </div>
      </div>
    </div>
  );
}
