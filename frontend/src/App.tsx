import { useCallback, useEffect, useMemo, useState } from "react";
import type { HealthResponse, Paper } from "./api";
import { deletePaper, health as fetchHealth, listPapers } from "./api";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [papersLoading, setPapersLoading] = useState(true);
  const [papersError, setPapersError] = useState<string | null>(null);
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  const refreshPapers = useCallback(async () => {
    setPapersError(null);
    try {
      const data = await listPapers();
      setPapers(data);
    } catch (e) {
      setPapersError(e instanceof Error ? e.message : "Failed to load papers");
    } finally {
      setPapersLoading(false);
    }
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshPapers();
    refreshHealth();
    const interval = setInterval(refreshHealth, 15000);
    return () => clearInterval(interval);
  }, [refreshPapers, refreshHealth]);

  const handleDelete = useCallback(
    async (paperId: string) => {
      try {
        await deletePaper(paperId);
        setSelectedPaperId((prev) => (prev === paperId ? null : prev));
        await refreshPapers();
      } catch (e) {
        setPapersError(e instanceof Error ? e.message : "Failed to delete paper");
      }
    },
    [refreshPapers],
  );

  const selectedPaperTitle = useMemo(
    () => papers.find((p) => p.paper_id === selectedPaperId)?.title ?? null,
    [papers, selectedPaperId],
  );

  return (
    <div className="app">
      <Header health={health} healthLoading={healthLoading} />
      <div className="layout">
        <Sidebar
          papers={papers}
          loading={papersLoading}
          error={papersError}
          selectedPaperId={selectedPaperId}
          onSelect={setSelectedPaperId}
          onDelete={handleDelete}
          onUploaded={refreshPapers}
        />
        <main className="main">
          <ChatPanel selectedPaperId={selectedPaperId} selectedPaperTitle={selectedPaperTitle} />
        </main>
      </div>
    </div>
  );
}
