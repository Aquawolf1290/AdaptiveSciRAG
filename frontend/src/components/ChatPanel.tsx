import { useEffect, useRef, useState } from "react";
import type { ChatResponse, FigureCitation } from "../api";
import { chat, figureUrl } from "../api";
import FigureLightbox from "./FigureLightbox";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  response?: ChatResponse;
  error?: boolean;
}

interface ChatPanelProps {
  selectedPaperId: string | null;
  selectedPaperTitle: string | null;
}

function makeId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function ChatPanel({ selectedPaperId, selectedPaperTitle }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [lightbox, setLightbox] = useState<FigureCitation | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  async function send() {
    const question = input.trim();
    if (!question || pending) return;

    const userMessage: ChatMessage = { id: makeId(), role: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setPending(true);

    try {
      const response = await chat(question, selectedPaperId ?? undefined);
      setMessages((prev) => [
        ...prev,
        { id: makeId(), role: "assistant", text: response.answer, response },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "assistant",
          text: e instanceof Error ? e.message : "Something went wrong.",
          error: true,
        },
      ]);
    } finally {
      setPending(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const scopeLabel = selectedPaperId
    ? selectedPaperTitle ?? "selected paper"
    : "all papers";

  return (
    <section className="chat">
      <div className="chat-scope">
        Asking across <strong>{scopeLabel}</strong>
      </div>

      <div className="chat-history" ref={scrollRef}>
        {messages.length === 0 && !pending && (
          <div className="chat-empty">
            <div className="chat-empty-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="30" height="30" fill="none">
                <path
                  d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H9l-4 4z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <h3>Ask a question about your papers</h3>
            <p>
              Upload a PDF, then ask things like “What dataset was used?” or “Summarize the main
              result.” Answers cite the source text and figures.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} onFigureClick={setLightbox} />
        ))}

        {pending && (
          <div className="message message-assistant">
            <div className="message-avatar">AI</div>
            <div className="message-body">
              <div className="typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        <textarea
          className="composer-input"
          placeholder="Ask a question…  (Enter to send, Shift+Enter for newline)"
          value={input}
          rows={1}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={pending}
        />
        <button type="button" className="composer-send" onClick={send} disabled={pending || !input.trim()}>
          {pending ? <span className="spinner spinner-sm" /> : "Send"}
        </button>
      </div>

      {lightbox && <FigureLightbox figure={lightbox} onClose={() => setLightbox(null)} />}
    </section>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
  onFigureClick: (figure: FigureCitation) => void;
}

function MessageBubble({ message, onFigureClick }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const response = message.response;
  const hasTextCitations = response && response.text_citations.length > 0;
  const hasFigureCitations = response && response.figure_citations.length > 0;

  return (
    <div className={`message ${isUser ? "message-user" : "message-assistant"}`}>
      <div className="message-avatar">{isUser ? "You" : "AI"}</div>
      <div className="message-body">
        <div className={`message-text ${message.error ? "message-error" : ""}`}>
          {message.text || (message.error ? "Error" : "")}
        </div>

        {(hasTextCitations || hasFigureCitations) && (
          <div className="sources">
            <div className="sources-label">Sources</div>

            {hasTextCitations && (
              <ul className="text-citations">
                {response!.text_citations.map((citation, i) => (
                  <li key={`t-${i}`} className="text-citation">
                    <span className="citation-page">p.{citation.page}</span>
                    <blockquote>{citation.text}</blockquote>
                  </li>
                ))}
              </ul>
            )}

            {hasFigureCitations && (
              <div className="figure-citations">
                {response!.figure_citations.map((figure) => (
                  <button
                    type="button"
                    key={`f-${figure.id}`}
                    className="figure-thumb"
                    onClick={() => onFigureClick(figure)}
                    title={figure.caption ?? `Figure ${figure.id}`}
                  >
                    <img src={figureUrl(figure.url)} alt={figure.caption ?? `Figure ${figure.id}`} />
                    <span className="figure-caption">
                      <span className="citation-page">p.{figure.page}</span>
                      {figure.caption && <span className="figure-caption-text">{figure.caption}</span>}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
