export const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

export interface Paper {
  paper_id: string;
  title: string;
  n_pages?: number;
  n_chunks?: number;
  n_figures?: number;
}

export interface TextCitation {
  page: number;
  text: string;
  paper_id?: string;
}

export interface FigureCitation {
  id: string;
  page: number;
  caption?: string;
  url: string;
}

export interface ChatResponse {
  answer: string;
  text_citations: TextCitation[];
  figure_citations: FigureCitation[];
}

export interface HealthResponse {
  status: string;
  provider: string;
}

function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export function figureUrl(citationUrl: string): string {
  if (/^https?:\/\//.test(citationUrl)) return citationUrl;
  return apiUrl(citationUrl);
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = JSON.parse(text);
      if (data && typeof data.detail === "string") message = data.detail;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }
  return text ? (JSON.parse(text) as T) : ({} as T);
}

export async function health(): Promise<HealthResponse> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 15000);
      try {
        const res = await fetch(apiUrl("/health"), { signal: controller.signal });
        const data = await parseJson<Partial<HealthResponse>>(res);
        return {
          status: data.status ?? "ok",
          provider: data.provider ?? "unknown",
        };
      } finally {
        window.clearTimeout(timeout);
      }
    } catch (error) {
      lastError = error;
      if (attempt < 2) {
        await new Promise((resolve) => window.setTimeout(resolve, 3000));
      }
    }
  }
  throw lastError instanceof Error ? lastError : new Error("Backend health check failed");
}

function normalizePaper(raw: Record<string, unknown>): Paper {
  const get = (...keys: string[]): unknown => {
    for (const key of keys) {
      if (raw[key] !== undefined && raw[key] !== null) return raw[key];
    }
    return undefined;
  };
  const num = (v: unknown): number | undefined =>
    typeof v === "number" ? v : typeof v === "string" && v.trim() !== "" ? Number(v) : undefined;

  return {
    paper_id: String(get("paper_id", "id", "paperId") ?? ""),
    title: String(get("title", "name", "filename") ?? "Untitled paper"),
    n_pages: num(get("n_pages", "num_pages", "pages")),
    n_chunks: num(get("n_chunks", "num_chunks", "chunks")),
    n_figures: num(get("n_figures", "num_figures", "figures")),
  };
}

export async function listPapers(): Promise<Paper[]> {
  const res = await fetch(apiUrl("/papers"));
  const data = await parseJson<unknown>(res);
  const arr = Array.isArray(data) ? data : [];
  return arr.map((p) => normalizePaper(p as Record<string, unknown>));
}

export async function uploadPaper(file: File): Promise<Paper> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(apiUrl("/papers"), { method: "POST", body: form });
  const data = await parseJson<Record<string, unknown>>(res);
  return normalizePaper(data);
}

export async function deletePaper(paperId: string): Promise<void> {
  const res = await fetch(apiUrl(`/papers/${encodeURIComponent(paperId)}`), {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Failed to delete paper (${res.status})`);
  }
}

export async function chat(question: string, paperId?: string): Promise<ChatResponse> {
  const body: { question: string; paper_id?: string } = { question };
  if (paperId) body.paper_id = paperId;
  const res = await fetch(apiUrl("/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await parseJson<Partial<ChatResponse>>(res);
  return {
    answer: data.answer ?? "",
    text_citations: Array.isArray(data.text_citations) ? data.text_citations : [],
    figure_citations: Array.isArray(data.figure_citations) ? data.figure_citations : [],
  };
}
