"use client";

import { useMemo, useRef, useState, useEffect, useCallback } from "react";
import Cell from "./Cell";
import type { ActiveRollout, Persona } from "@/lib/types";

// Cell aspect ratio: 16:10 = 1.6 (the iframe fills the entire cell now;
// avatar/status/turn-info are overlays on top, no header strip).
const CELL_AR = 16 / 10;
// Minimum readable cell width. Cells thinner than this are unusable; we'd
// rather have fewer columns + scrolling-free overflow than micro-stripes.
const MIN_CELL_W = 260;
// No fixed chrome anymore — cell height = cellW / aspectRatio.
const CHROME_PX = 0;

interface Props {
  sessions: ActiveRollout[];
  personas: Record<string, Persona>;
  selection: Set<string>;
  selectMode: boolean;
  onSelectionChange: (next: Set<string>) => void;
  onFocus: (id: string) => void;
}

interface MarqueeState {
  active: boolean;
  startX: number;
  startY: number;
  curX: number;
  curY: number;
  additive: boolean; // shift held → add to existing selection
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
    const cellH = cellW / CELL_AR + CHROME_PX;
    const totalH = cellH * rows + gap * (rows - 1);
    if (totalH <= containerH) {
      return { cols, rows, cellH };
    }
  }
  // Doesn't fit — use maxCols, accept scroll.
  const cols = Math.min(maxCols, n);
  const rows = Math.ceil(n / cols);
  const cellW = (containerW - gap * (cols - 1)) / cols;
  const cellH = cellW / CELL_AR + CHROME_PX;
  return { cols, rows, cellH };
}

export default function Grid({
  sessions,
  personas,
  selection,
  selectMode,
  onSelectionChange,
  onFocus,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 0, h: 0 });
  const [marquee, setMarquee] = useState<MarqueeState | null>(null);

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

  // ---- toggle a single cell's selection (used by Cell click in select-mode)
  const toggleSelection = useCallback(
    (id: string) => {
      const next = new Set(selection);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      onSelectionChange(next);
    },
    [selection, onSelectionChange]
  );

  // ---- marquee drag-select
  // Active when (a) we're in select-mode, OR (b) the user is holding shift.
  // Starts on mousedown over the grid container background.
  const onContainerMouseDown = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const enabled = selectMode || e.shiftKey;
      if (!enabled || e.button !== 0) return;
      // Only kick off when mousedown lands on the grid container itself, not
      // on a cell's interactive child. In select-mode the cell overlays
      // already block iframe events, so click-on-cell still works.
      const target = e.target as HTMLElement;
      const cellRoot = target.closest("[data-cell-id]");
      if (cellRoot && !selectMode) return; // shift-drag only marquees from background
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setMarquee({
        active: true,
        startX: e.clientX - rect.left,
        startY: e.clientY - rect.top,
        curX: e.clientX - rect.left,
        curY: e.clientY - rect.top,
        additive: e.shiftKey || e.metaKey || e.ctrlKey,
      });
      e.preventDefault();
    },
    [selectMode]
  );

  // Window-level move/up so the user can drag past the container without losing the marquee.
  useEffect(() => {
    if (!marquee?.active) return;
    function onMove(e: MouseEvent) {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setMarquee((m) =>
        m && m.active
          ? { ...m, curX: e.clientX - rect.left, curY: e.clientY - rect.top }
          : m
      );
    }
    function onUp() {
      // Commit selection: any cell whose bounding rect intersects the marquee.
      const rect = containerRef.current?.getBoundingClientRect();
      const m = marquee;
      if (!rect || !m) {
        setMarquee(null);
        return;
      }
      const left = Math.min(m.startX, m.curX);
      const right = Math.max(m.startX, m.curX);
      const top = Math.min(m.startY, m.curY);
      const bottom = Math.max(m.startY, m.curY);

      const next = new Set(m.additive ? selection : []);
      const cellEls = gridRef.current?.querySelectorAll<HTMLElement>("[data-cell-id]");
      cellEls?.forEach((el) => {
        const r = el.getBoundingClientRect();
        const cellLeft = r.left - rect.left;
        const cellTop = r.top - rect.top;
        const cellRight = cellLeft + r.width;
        const cellBottom = cellTop + r.height;
        // intersection test
        const intersects =
          cellLeft < right && cellRight > left && cellTop < bottom && cellBottom > top;
        // ignore zero-area drags (treat as no-op so a plain click in select
        // mode can still fall through to Cell's own click handler).
        const dragged = Math.abs(m.curX - m.startX) > 4 || Math.abs(m.curY - m.startY) > 4;
        if (dragged && intersects) {
          const id = el.dataset.cellId;
          if (id) next.add(id);
        }
      });
      // Only update selection if we actually dragged — otherwise click semantics handle it.
      if (Math.abs(m.curX - m.startX) > 4 || Math.abs(m.curY - m.startY) > 4) {
        onSelectionChange(next);
      }
      setMarquee(null);
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [marquee, selection, onSelectionChange]);

  const marqueeBox = marquee
    ? {
        left: Math.min(marquee.startX, marquee.curX),
        top: Math.min(marquee.startY, marquee.curY),
        width: Math.abs(marquee.curX - marquee.startX),
        height: Math.abs(marquee.curY - marquee.startY),
      }
    : null;

  return (
    <div
      ref={containerRef}
      onMouseDown={onContainerMouseDown}
      className={`relative flex-1 min-h-0 overflow-y-auto overflow-x-hidden ${
        selectMode ? "cursor-crosshair select-none" : ""
      }`}
    >
      {sessions.length === 0 ? (
        <div className="border border-dashed border-line bg-white text-center p-[60px] text-muted lowercase">
          <p className="text-[15px]">no active rollouts.</p>
          <p className="text-[13px] mt-1">click + new run to start one.</p>
        </div>
      ) : (
        <div
          ref={gridRef}
          className="grid gap-[14px]"
          style={{
            gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
            gridAutoRows: `${cellH}px`,
          }}
        >
          {sessions.map((s) => (
            <Cell
              key={s.browser_session_id}
              session={s}
              persona={personas[s.persona_id]}
              selected={selection.has(s.browser_session_id)}
              selectMode={selectMode}
              onFocus={onFocus}
              onToggleSelect={toggleSelection}
            />
          ))}
        </div>
      )}

      {/* marquee box — visible during an active drag-select */}
      {marqueeBox && (
        <div
          className="absolute pointer-events-none border border-olive bg-olive/15 backdrop-blur-[1px]"
          style={{
            left: marqueeBox.left,
            top: marqueeBox.top,
            width: marqueeBox.width,
            height: marqueeBox.height,
          }}
        />
      )}
    </div>
  );
}
