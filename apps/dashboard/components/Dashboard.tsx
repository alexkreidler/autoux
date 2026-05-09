"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "@/lib/api";
import { useSessions } from "./useSessions";
import MetricBar from "./MetricBar";
import Grid from "./Grid";
import RunModal from "./RunModal";
import type { Persona } from "@/lib/types";

export default function Dashboard() {
  const sessions = useSessions();
  const [personas, setPersonas] = useState<Record<string, Persona>>({});
  const [showModal, setShowModal] = useState(false);

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
      <div className="flex justify-end mb-[14px]">
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
