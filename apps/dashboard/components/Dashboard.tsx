"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiUrl, fetchJson } from "@/lib/api";
import { useSessions } from "./useSessions";
import MetricBar from "./MetricBar";
import Grid from "./Grid";
import RunModal from "./RunModal";
import FocusedCell from "./FocusedCell";
import type { Persona } from "@/lib/types";

export default function Dashboard() {
  const sessions = useSessions();
  const [personas, setPersonas] = useState<Record<string, Persona>>({});
  const [showModal, setShowModal] = useState(false);
  const [reaping, setReaping] = useState(false);

  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [selectMode, setSelectMode] = useState(false);
  const [focusedId, setFocusedId] = useState<string | null>(null);

  useEffect(() => {
    function load() {
      fetchJson<Record<string, Persona>>("/api/personas")
        .then(setPersonas)
        .catch(() => {});
    }
    load();
    // Refresh periodically — new personas might be generated mid-run
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, []);

  // Keyboard: Esc closes focus or exits select-mode
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (focusedId) setFocusedId(null);
        else if (selectMode) {
          setSelectMode(false);
          setSelection(new Set());
        } else if (selection.size > 0) {
          setSelection(new Set());
        }
      }
      // ⌘A in select mode → select all
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "a" && selectMode) {
        e.preventDefault();
        setSelection(new Set(sessions.map((s) => s.browser_session_id)));
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusedId, selectMode, selection.size, sessions]);

  // Drop selections that no longer exist (run finished, registry pruned)
  useEffect(() => {
    const live = new Set(sessions.map((s) => s.browser_session_id));
    if (Array.from(selection).some((id) => !live.has(id))) {
      const next = new Set(Array.from(selection).filter((id) => live.has(id)));
      setSelection(next);
    }
    if (focusedId && !live.has(focusedId)) setFocusedId(null);
  }, [sessions, selection, focusedId]);

  const focused = useMemo(
    () => sessions.find((s) => s.browser_session_id === focusedId) ?? null,
    [sessions, focusedId]
  );

  const handleFocus = useCallback((id: string) => {
    setFocusedId(id);
    setSelectMode(false);
  }, []);

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

  return (
    // Full-viewport flex column — nothing scrolls except the modal
    <div className="h-screen flex flex-col px-7 py-6 overflow-hidden">
      {/* header */}
      <header className="flex justify-between items-baseline border-b border-line pb-[14px] mb-[18px]">
        <h1 className="m-0 text-[20px] font-medium tracking-[-0.01em] lowercase flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-olive" />
          autoux · live rollouts
        </h1>
        <span className="text-muted text-[13px]">{sessions.length} active</span>
      </header>

      {/* metric bar */}
      <MetricBar />

      {/* action bar */}
      <div className="flex justify-end items-center gap-3 mb-[14px]">
        {sessions.length > 0 && (
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
        )}
        {sessions.length > 0 && (
          <button
            type="button"
            onClick={handleReap}
            disabled={reaping}
            className="px-3 py-2 border border-rust text-rust text-[12px] lowercase tracking-[0.02em] hover:bg-rust hover:text-white transition-colors disabled:opacity-40"
            title="terminate all live kernel sessions and clear the registry"
          >
            {reaping ? "reaping…" : `kill all (${sessions.length})`}
          </button>
        )}
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="px-4 py-2 border border-olive text-olive text-[13px] lowercase tracking-[0.02em] hover:bg-olive hover:text-white transition-colors"
        >
          + new run
        </button>
      </div>

      {/* autoscale grid — takes remaining height */}
      <Grid
        sessions={sessions}
        personas={personas}
        selection={selection}
        selectMode={selectMode}
        onSelectionChange={setSelection}
        onFocus={handleFocus}
      />

      {/* selection toolbar — slides up from bottom when selection is non-empty */}
      {selection.size > 0 && (
        <div className="fixed left-1/2 -translate-x-1/2 bottom-6 z-30 flex items-center gap-2 bg-ink text-cream px-4 py-2 shadow-lg border border-ink rounded">
          <span className="text-[12px] lowercase tracking-[0.05em] text-cream/80">
            {selection.size} selected
          </span>
          <span className="w-px h-4 bg-cream/30 mx-1" />
          <button
            type="button"
            onClick={() => {
              // Focus a sub-grid: clear selection except the chosen ids and
              // turn off select mode. (Real "focus group" view = future work.)
              if (selection.size === 1) {
                handleFocus(Array.from(selection)[0]);
              } else {
                // For now, focus the first; multi-cell focus needs a layout.
                handleFocus(Array.from(selection)[0]);
              }
            }}
            className="text-[12px] lowercase tracking-[0.02em] hover:text-olive transition-colors"
            title={selection.size > 1 ? "focuses the first selected cell — multi-cell focus coming" : "focus this cell"}
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

      {/* focus mode — full-screen single cell */}
      {focused && (
        <FocusedCell
          session={focused}
          persona={personas[focused.persona_id]}
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
