"use client";

import { useMemo, useRef, useState, useEffect } from "react";
import Cell from "./Cell";
import type { ActiveRollout, Persona } from "@/lib/types";

// Cell aspect ratio: 16:10 = 1.6
const CELL_AR = 16 / 10;
// Approximate fixed vertical height consumed by top strip + bottom strip inside each cell (px).
const CELL_CHROME_PX = 80;

interface Props {
  sessions: ActiveRollout[];
  personas: Record<string, Persona>;
}

function computeLayout(n: number, containerW: number, containerH: number): { cols: number; rows: number } {
  if (n === 0) return { cols: 1, rows: 1 };

  let bestCols = 1;
  let bestScore = Infinity;

  // Try every column count from 1 to n and pick the one whose cell size best fills the container.
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols);
    const cellW = containerW / cols;
    // The iframe inside the cell takes aspectRatio 16:10, plus strips above/below.
    const cellH = cellW / CELL_AR + CELL_CHROME_PX;
    const totalH = cellH * rows;
    // Score: how much we exceed or underuse container height. Penalise overflow heavily.
    const overflow = Math.max(0, totalH - containerH);
    const unused = Math.max(0, containerH - totalH);
    const score = overflow * 3 + unused;
    if (score < bestScore) {
      bestScore = score;
      bestCols = cols;
    }
  }

  return { cols: bestCols, rows: Math.ceil(n / bestCols) };
}

export default function Grid({ sessions, personas }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 0, h: 0 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setDims({ w: Math.floor(width), h: Math.floor(height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { cols } = useMemo(
    () => computeLayout(sessions.length, dims.w, dims.h),
    [sessions.length, dims.w, dims.h]
  );

  if (sessions.length === 0) {
    return (
      <div className="border border-dashed border-line bg-white text-center p-[60px] text-muted lowercase">
        <p className="text-[15px]">no active rollouts.</p>
        <p className="text-[13px] mt-1">click + new run to start one.</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="flex-1 min-h-0 overflow-hidden">
      <div
        className="grid gap-[14px] h-full"
        style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
      >
        {sessions.map((s) => (
          <Cell key={s.browser_session_id} session={s} persona={personas[s.persona_id]} />
        ))}
      </div>
    </div>
  );
}
