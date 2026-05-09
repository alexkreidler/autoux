"use client";

import { useMemo, useRef, useState, useEffect } from "react";
import Cell from "./Cell";
import type { ActiveRollout, Persona } from "@/lib/types";

// Cell aspect ratio: 16:10 = 1.6 (matches the iframe)
const CELL_AR = 16 / 10;
// Minimum readable cell width. Cells thinner than this are unusable; we'd
// rather have fewer columns + scrolling-free overflow than micro-stripes.
const MIN_CELL_W = 240;
// Reserve for the header strip in each cell (avatar + name + badge).
const TOP_STRIP_PX = 56;

interface Props {
  sessions: ActiveRollout[];
  personas: Record<string, Persona>;
}

/**
 * Pick (cols, rows) so that:
 *   1. each cell has width >= MIN_CELL_W (anti-stripe guard)
 *   2. cells render at the cell's natural aspect ratio (no stretching to
 *      fill a tall container — that's why we got 25 stripes earlier)
 *   3. we maximise on-screen visibility — prefer fitting all cells without
 *      scroll, falling back to vertical scroll when N is large.
 *
 * Returns layout suitable for a grid where the cell height = top_strip +
 * cell_width / aspect_ratio (no vertical stretching).
 */
function computeLayout(n: number, containerW: number, containerH: number): {
  cols: number;
  rows: number;
  cellH: number;
} {
  if (n === 0 || containerW < 1) return { cols: 1, rows: 1, cellH: 200 };

  // Most columns we can fit without going below MIN_CELL_W. Account for ~14px gap.
  const gap = 14;
  const maxCols = Math.max(1, Math.floor((containerW + gap) / (MIN_CELL_W + gap)));

  // Try cols from maxCols down; pick the first one whose total height fits
  // the container. If none fits, accept maxCols (will scroll vertically).
  for (let cols = Math.min(maxCols, n); cols >= 1; cols--) {
    const rows = Math.ceil(n / cols);
    const cellW = (containerW - gap * (cols - 1)) / cols;
    const cellH = cellW / CELL_AR + TOP_STRIP_PX;
    const totalH = cellH * rows + gap * (rows - 1);
    if (totalH <= containerH) {
      return { cols, rows, cellH };
    }
  }
  // Doesn't fit — use maxCols, accept scroll.
  const cols = Math.min(maxCols, n);
  const rows = Math.ceil(n / cols);
  const cellW = (containerW - gap * (cols - 1)) / cols;
  const cellH = cellW / CELL_AR + TOP_STRIP_PX;
  return { cols, rows, cellH };
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

  const { cols, cellH } = useMemo(
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
    // Allow vertical scroll when N is large enough that even MIN_CELL_W can't
    // tile in one screen — better than micro-stripes.
    <div ref={containerRef} className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
      <div
        className="grid gap-[14px]"
        style={{
          gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
          gridAutoRows: `${cellH}px`,
        }}
      >
        {sessions.map((s) => (
          <Cell key={s.browser_session_id} session={s} persona={personas[s.persona_id]} />
        ))}
      </div>
    </div>
  );
}
