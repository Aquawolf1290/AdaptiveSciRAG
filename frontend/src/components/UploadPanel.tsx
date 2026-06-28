import { useRef, useState } from "react";
import { uploadPaper } from "../api";

interface UploadPanelProps {
  onUploaded: () => void;
}

export default function UploadPanel({ onUploaded }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUploaded, setLastUploaded] = useState<string | null>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const file = files[0];
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }
    setError(null);
    setUploading(true);
    setLastUploaded(null);
    try {
      const paper = await uploadPaper(file);
      setLastUploaded(paper.title || file.name);
      onUploaded();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="upload">
      <div
        className={`dropzone ${dragging ? "dropzone-active" : ""} ${uploading ? "dropzone-busy" : ""}`}
        role="button"
        tabIndex={0}
        onClick={() => !uploading && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !uploading) inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!uploading) handleFiles(e.dataTransfer.files);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
        {uploading ? (
          <div className="dropzone-inner">
            <span className="spinner" />
            <span className="dropzone-title">Ingesting paper…</span>
          </div>
        ) : (
          <div className="dropzone-inner">
            <svg viewBox="0 0 24 24" width="26" height="26" fill="none" aria-hidden="true">
              <path
                d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
            <span className="dropzone-title">Drop a PDF or click to upload</span>
            <span className="dropzone-sub">Scientific papers only · .pdf</span>
          </div>
        )}
      </div>

      {error && <p className="upload-error">{error}</p>}
      {lastUploaded && !error && <p className="upload-ok">Added “{lastUploaded}”.</p>}
    </div>
  );
}
