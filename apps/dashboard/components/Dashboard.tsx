"use client";

import { useEffect, useState } from "react";
import { apiUrl, fetchJson } from "@/lib/api";
import { useSessions } from "./useSessions";
import MetricBar from "./MetricBar";
import Grid from "./Grid";
import RunModal from "./RunModal";
import type { Persona } from "@/lib/types";

export default function Dashboard() {
  const sessions = useSessions();
  const [personas, setPersonas] = useState<Record<string, Persona>>({});
  const [showModal, setShowModal] = useState(false);
  const [reaping, setReaping] = useState(false);

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

  async function handleReap() {
    if (!confirm("kill all live kernel sessions and clear the registry?\n\nthis will terminate any in-flight runs.")) return;
    setReaping(true);
    try {
      const res = await fetch(apiUrl("/api/registry/reap"), { method: "POST" });
      const body = await res.json();
      alert(`reaped ${body.kernel_sessions_reaped ?? 0} kernel sessions; registry cleared.`);
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
      <Grid sessions={sessions} personas={personas} />

      {/* run modal */}
      {showModal && (
        <RunModal personas={personas} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
