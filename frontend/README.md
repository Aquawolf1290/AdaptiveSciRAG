# Multimodal RAG — Frontend

A clean, modern React UI for a **Multimodal RAG over scientific papers** system. Upload PDFs,
scope questions to one paper or the whole library, and get answers with **text citations** and
**clickable figure thumbnails**.

Built with **Vite + React + TypeScript**, minimal dependencies, plain CSS (dark-mode aware).

## Prerequisites

- Node 20+ and npm 10+
- The FastAPI backend running on `http://localhost:8000`

## Run

```bash
npm install
npm run dev
```

The dev server runs on **http://localhost:5173**. Requests to `/papers`, `/chat`, `/figures`,
and `/health` are proxied to `http://localhost:8000` (configured in `vite.config.ts`), so there
are no CORS issues in development.

> The backend must be running on **port 8000**. If it's offline, the header shows a
> "Backend offline" indicator and the rest of the UI degrades gracefully.

## Build

```bash
npm run build
```

This runs `tsc --noEmit` (type check) followed by `vite build`. Output is written to `dist/`.

## Configuration

By default the app uses relative URLs and relies on the Vite dev proxy. To point at a backend
directly (e.g. a deployed API), set `VITE_API_BASE`:

```bash
# .env
VITE_API_BASE=https://api.example.com
```

When `VITE_API_BASE` is empty (the default), the proxy is used.

## API contract

| Method | Path                 | Purpose                                  |
| ------ | -------------------- | ---------------------------------------- |
| GET    | `/health`            | `{ status, provider }`                   |
| GET    | `/papers`            | List ingested papers                     |
| POST   | `/papers`            | Multipart upload, field `file` (PDF)     |
| DELETE | `/papers/{paper_id}` | Remove a paper                           |
| POST   | `/chat`              | `{ question, paper_id? }` → answer + cites |
| GET    | `/figures/{id}`      | Figure PNG bytes                         |

## Project structure

```
src/
  api.ts                  Typed API client + interfaces
  App.tsx                 App shell, papers/health state
  main.tsx                Entry point
  styles.css              All styling (CSS variables, dark mode)
  components/
    Header.tsx            App name + backend provider / status pill
    Sidebar.tsx           Upload + paper library + selector
    UploadPanel.tsx       Drag-or-click PDF upload with progress
    ChatPanel.tsx         Message history, composer, sources rendering
    FigureLightbox.tsx    Figure modal / lightbox
```
