"use client";

import { useEffect, useRef, useState } from "react";
import { fetchJson } from "@/lib/api";
import type { HistoricalRun } from "@/lib/types";

interface Props {
  activeRunDir: string | null;
  onSelect: (run: HistoricalRun) => void;
  onClearHistory: () => void;
}

export default function PastRunsBrowser({ activeRunDir, onSelect, onClearHistory }: Props) {
  const [runs, setRuns] = useState<HistoricalRun[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchJson<HistoricalRun[]>("/api/runs/historical").then(setRuns).catch(() => {});
  }, [open]); // refetch when dropdown opens

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  const active = runs.find((r) => r.run_dir === activeRunDir);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-2 px-3 py-2 border text-[12px] lowercase tracking-[0.02em] transition-colors ${
          activeRunDir
            ? "border-clay text-clay bg-white"
            : "border-line text-ink-soft hover:border-clay hover:text-clay"
        }`}
        title="browse past runs"
      >
        <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor">
          <path d="M1 2.5A1.5 1.5 0 0 1 2.5 1h3A1.5 1.5 0 0 1 7 2.5v3A1.5 1.5 0 0 1 5.5 7h-3A1.5 1.5 0 0 1 1 5.5v-3zm8 0A1.5 1.5 0 0 1 10.5 1h3A1.5 1.5 0 0 1 15 2.5v3A1.5 1.5 0 0 1 13.5 7h-3A1.5 1.5 0 0 1 9 5.5v-3zm-8 8A1.5 1.5 0 0 1 2.5 9h3A1.5 1.5 0 0 1 7 10.5v3A1.5 1.5 0 0 1 5.5 15h-3A1.5 1.5 0 0 1 1 13.5v-3zm8 0A1.5 1.5 0 0 1 10.5 9h3A1.5 1.5 0 0 1 15 10.5v3A1.5 1.5 0 0 1 13.5 15h-3A1.5 1.5 0 0 1 9 13.5v-3z" />
        </svg>
        {active ? (
          <span className="max-w-[140px] truncate">{active.display_name}</span>
        ) : (
          "past runs"
        )}
        <svg viewBox="0 0 10 6" width="8" height="6" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M1 1l4 4 4-4" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-[320px] bg-cream border border-line z-50 shadow-lg max-h-[60vh] overflow-y-auto">
          {activeRunDir && (
            <div className="px-3 py-2 border-b border-line-soft flex items-center justify-between">
              <span className="text-[10px] text-muted lowercase tracking-[0.05em]">viewing history</span>
              <button
                type="button"
                onClick={() => { onClearHistory(); setOpen(false); }}
                className="text-[11px] text-rust hover:underline lowercase"
              >
                back to live
              </button>
            </div>
          )}
          {runs.length === 0 && (
            <div className="px-4 py-6 text-center text-[12px] text-muted lowercase">
              no past runs found in runs/
            </div>
          )}
          <div className="divide-y divide-line-soft">
            {runs.map((r) => (
              <button
                key={r.run_dir}
                type="button"
                onClick={() => { onSelect(r); setOpen(false); }}
                className={`w-full text-left px-4 py-3 hover:bg-line-soft/40 transition-colors ${
                  r.run_dir === activeRunDir ? "bg-cream border-l-2 border-clay" : ""
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[12px] font-medium text-ink truncate">{r.display_name}</span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {r.has_grid_mp4 && (
                      <span className="text-[9px] px-1 py-0.5 border border-sage text-sage uppercase tracking-wider">mp4</span>
                    )}
                    {r.has_feedback && (
                      <span className="text-[9px] px-1 py-0.5 border border-olive text-olive uppercase tracking-wider">fb</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-muted">
                    {r.layout === "sweep" ? `sweep · ${r.apps.length} apps` : "flat"} · {r.n_trajectories} runs
                  </span>
                  {r.target_summary && (
                    <span className="text-[10px] text-muted truncate">· {r.target_summary}</span>
                  )}
                </div>
                {r.started_at && (
                  <div className="text-[10px] text-muted/70 mt-0.5">
                    {new Date(r.started_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
