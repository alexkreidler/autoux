"use client";

import { useCallback, useEffect, useState } from "react";
import { apiUrl, fetchJson } from "@/lib/api";
import { useSessions } from "./useSessions";
import MetricBar from "./MetricBar";
import Grid from "./Grid";
import RunModal from "./RunModal";
import FocusedCell from "./FocusedCell";
import EmptyState from "./EmptyState";
import PastRunsBrowser from "./PastRunsBrowser";
import ResultsView from "./ResultsView";
import type { ActiveRollout, HistoricalRun, HistoricalSession, Persona } from "@/lib/types";

export default function Dashboard() {
  const liveSessions = useSessions();
  const [personas, setPersonas] = useState<Record<string, Persona>>({});
  const [showModal, setShowModal] = useState(false);
  const [reaping, setReaping] = useState(false);

  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [selectMode, setSelectMode] = useState(false);
  const [focusedId, setFocusedId] = useState<string | null>(null);

  // Historical run state
  const [activeHistoricalRun, setActiveHistoricalRun] = useState<HistoricalRun | null>(null);
  const [historicalSessions, setHistoricalSessions] = useState<HistoricalSession[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // Derived: which sessions are shown in the grid
  const isHistoryMode = activeHistoricalRun !== null;
  // Cast HistoricalSession to ActiveRollout — shape is compatible by design
  const sessions: ActiveRollout[] = isHistoryMode
    ? (historicalSessions as unknown as ActiveRollout[])
    : liveSessions;

  useEffect(() => {
    function load() {
      fetchJson<Record<string, Persona>>("/api/personas")
        .then(setPersonas)
        .catch(() => {});
    }
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (focusedId) setFocusedId(null);
        else if (showResults) setShowResults(false);
        else if (selectMode) {
          setSelectMode(false);
          setSelection(new Set());
        } else if (selection.size > 0) {
          setSelection(new Set());
        }
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "a" && selectMode) {
        e.preventDefault();
        setSelection(new Set(sessions.map((s) => s.browser_session_id)));
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusedId, showResults, selectMode, selection.size, sessions]);

  // Drop selections that no longer exist
  useEffect(() => {
    if (isHistoryMode) return; // historical sessions are stable
    const live = new Set(sessions.map((s) => s.browser_session_id));
    if (Array.from(selection).some((id) => !live.has(id))) {
      setSelection(new Set(Array.from(selection).filter((id) => live.has(id))));
    }
  }, [sessions, selection, isHistoryMode]);

  // Snapshot focused session so it survives being pruned from live registry
  const [focusedSnapshot, setFocusedSnapshot] = useState<ActiveRollout | null>(null);
  useEffect(() => {
    if (!focusedId) {
      setFocusedSnapshot(null);
      return;
    }
    const live = sessions.find((s) => s.browser_session_id === focusedId);
    if (live) setFocusedSnapshot(live);
  }, [focusedId, sessions]);

  const focused = focusedSnapshot;
  const focusedIsLive = isHistoryMode
    ? false
    : !!focused && liveSessions.some((s) => s.browser_session_id === focused.browser_session_id);

  const handleFocus = useCallback((id: string) => {
    setFocusedId(id);
    setSelectMode(false);
  }, []);

  async function handleHistoricalRunSelect(run: HistoricalRun) {
    setLoadingHistory(true);
    setShowResults(false);
    setFocusedId(null);
    setSelection(new Set());
    setSelectMode(false);
    try {
      const data = await fetchJson<HistoricalSession[]>(
        `/api/runs/historical/${encodeURIComponent(run.run_dir)}/sessions`
      );
      setHistoricalSessions(data);
      setActiveHistoricalRun(run);
    } catch (e) {
      alert(`failed to load run: ${e instanceof Error ? e.message : "unknown"}`);
    } finally {
      setLoadingHistory(false);
    }
  }

  function handleClearHistory() {
    setActiveHistoricalRun(null);
    setHistoricalSessions([]);
    setShowResults(false);
    setFocusedId(null);
    setSelection(new Set());
  }

  async function handleReap() {
    if (!confirm("kill all live kernel sessions and clear the registry?\n\nthis will terminate any in-flight runs.")) return;
    setReaping(true);
    try {
      const res = await fetch(apiUrl("/api/registry/reap"), { method: "POST" });
      const body = await res.json();
      alert(`reaped ${body.kernel_sessions_reaped ?? 0} kernel sessions; registry cleared.`);
      setSelection(new Set());
      setSelectMode(false);
    } catch (e) {
      alert(`reap failed: ${e instanceof Error ? e.message : "unknown"}`);
    } finally {
      setReaping(false);
    }
  }

  const showEmptyState = !isHistoryMode && sessions.length === 0;

  return (
    <div className="h-screen flex flex-col px-7 py-6 overflow-hidden">
      {/* header */}
      <header className="flex justify-between items-baseline border-b border-line pb-[14px] mb-[18px]">
        <h1 className="m-0 text-[20px] font-medium tracking-[-0.01em] lowercase flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-olive" />
          autoux · live rollouts
        </h1>
        <div className="flex items-center gap-3">
          {isHistoryMode && (
            <span className="text-[11px] text-clay lowercase border border-clay px-2 py-0.5">
              history: {activeHistoricalRun.display_name}
            </span>
          )}
          <span className="text-muted text-[13px]">
            {isHistoryMode
              ? `${historicalSessions.length} replays`
              : `${sessions.length} active`}
          </span>
        </div>
      </header>

      {/* metric bar — only show for live mode */}
      {!isHistoryMode && <MetricBar />}

      {/* action bar */}
      <div className="flex justify-end items-center gap-3 mb-[14px]">
        {/* past runs browser — always visible */}
        <PastRunsBrowser
          activeRunDir={activeHistoricalRun?.run_dir ?? null}
          onSelect={handleHistoricalRunSelect}
          onClearHistory={handleClearHistory}
        />

        {/* results toggle — visible when history loaded or run finished */}
        {(isHistoryMode && historicalSessions.length > 0) && (
          <button
            type="button"
            onClick={() => setShowResults((v) => !v)}
            className={`px-3 py-2 border text-[12px] lowercase tracking-[0.02em] transition-colors ${
              showResults
                ? "border-olive bg-olive text-white"
                : "border-line text-ink-soft hover:border-olive hover:text-olive"
            }`}
          >
            {showResults ? "grid view" : "results"}
          </button>
        )}

        {/* live-only controls */}
        {!isHistoryMode && sessions.length > 0 && (
          <>
            <button
              type="button"
              onClick={() => {
                setSelectMode((on) => !on);
                if (selectMode) setSelection(new Set());
              }}
              className={`px-3 py-2 border text-[12px] lowercase tracking-[0.02em] transition-colors ${
                selectMode
                  ? "border-olive bg-olive text-white"
                  : "border-line text-ink-soft hover:border-olive hover:text-olive"
              }`}
              title="toggle select-mode (or hold shift and drag to marquee)"
            >
              {selectMode ? "exit select" : "select"}
            </button>
            <button
              type="button"
              onClick={handleReap}
              disabled={reaping}
              className="px-3 py-2 border border-rust text-rust text-[12px] lowercase tracking-[0.02em] hover:bg-rust hover:text-white transition-colors disabled:opacity-40"
              title="terminate all live kernel sessions and clear the registry"
            >
              {reaping ? "reaping…" : `kill all (${sessions.length})`}
            </button>
          </>
        )}

        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="px-4 py-2 border border-olive text-olive text-[13px] lowercase tracking-[0.02em] hover:bg-olive hover:text-white transition-colors"
        >
          + new run
        </button>
      </div>

      {/* loading indicator for history fetch */}
      {loadingHistory && (
        <div className="flex-1 flex items-center justify-center text-[13px] text-muted lowercase animate-pulse">
          loading run…
        </div>
      )}

      {/* empty state — casting reel when no live sessions */}
      {!loadingHistory && showEmptyState && (
        <EmptyState personas={personas} onNewRun={() => setShowModal(true)} />
      )}

      {/* results view (historical only, when toggled) */}
      {!loadingHistory && isHistoryMode && showResults && (
        <ResultsView
          sessions={historicalSessions}
          personas={personas}
          onSelectPersona={(personaId) => {
            // scroll to first matching cell; for now just exit results view
            setShowResults(false);
            const first = historicalSessions.find((s) => s.persona_id === personaId);
            if (first) handleFocus(first.browser_session_id);
          }}
          onClose={() => setShowResults(false)}
        />
      )}

      {/* grid — shown when not loading, not empty, and not in results view */}
      {!loadingHistory && !showEmptyState && !showResults && (
        <Grid
          sessions={sessions}
          personas={personas}
          selection={selection}
          selectMode={selectMode && !isHistoryMode}
          onSelectionChange={setSelection}
          onFocus={handleFocus}
        />
      )}

      {/* selection toolbar */}
      {selection.size > 0 && (
        <div className="fixed left-1/2 -translate-x-1/2 bottom-6 z-30 flex items-center gap-2 bg-ink text-cream px-4 py-2 shadow-lg border border-ink rounded">
          <span className="text-[12px] lowercase tracking-[0.05em] text-cream/80">
            {selection.size} selected
          </span>
          <span className="w-px h-4 bg-cream/30 mx-1" />
          <button
            type="button"
            onClick={() => handleFocus(Array.from(selection)[0])}
            className="text-[12px] lowercase tracking-[0.02em] hover:text-olive transition-colors"
            title={selection.size > 1 ? "focuses the first selected cell" : "focus this cell"}
          >
            focus
          </button>
          <button
            type="button"
            onClick={() => setSelection(new Set())}
            className="text-[12px] lowercase tracking-[0.02em] hover:text-olive transition-colors"
          >
            clear
          </button>
        </div>
      )}

      {/* focus mode */}
      {focused && (
        <FocusedCell
          session={focused}
          persona={personas[focused.persona_id]}
          isLive={focusedIsLive}
          onClose={() => setFocusedId(null)}
        />
      )}

      {/* run modal */}
      {showModal && (
        <RunModal personas={personas} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
