"use client";

import AvatarChip from "./AvatarChip";
import type { Persona } from "@/lib/types";

interface Props {
  personas: Record<string, Persona>;
  onNewRun: () => void;
}

export default function EmptyState({ personas, onNewRun }: Props) {
  const ids = Object.keys(personas);

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-0 py-10 select-none">
      {/* casting reel grid */}
      {ids.length > 0 && (
        <div className="flex flex-wrap justify-center gap-3 max-w-[680px] mb-10">
          {ids.slice(0, 25).map((id) => {
            const p = personas[id];
            return (
              <div key={id} className="flex flex-col items-center gap-1.5 group">
                <div className="ring-1 ring-line group-hover:ring-olive transition-all duration-150 rounded">
                  <AvatarChip personaId={id} size={52} />
                </div>
                <span className="text-[9px] text-muted lowercase text-center w-[62px] truncate group-hover:text-ink transition-colors">
                  {p.archetype}
                </span>
              </div>
            );
          })}
          {ids.length > 25 && (
            <div className="flex flex-col items-center gap-1.5">
              <div className="w-[52px] h-[52px] border border-dashed border-line flex items-center justify-center">
                <span className="text-[11px] text-muted">+{ids.length - 25}</span>
              </div>
              <span className="text-[9px] text-muted">more</span>
            </div>
          )}
        </div>
      )}

      {/* CTA */}
      <div className="text-center">
        <p className="text-[14px] text-ink-soft lowercase mb-1">
          {ids.length > 0
            ? `${ids.length} personas loaded, ready to roll`
            : "no active rollouts"}
        </p>
        <p className="text-[12px] text-muted lowercase mb-5">
          kick off a run to see the grid populate live
        </p>
        <button
          type="button"
          onClick={onNewRun}
          className="px-6 py-2.5 bg-olive text-white text-[13px] lowercase tracking-[0.02em] hover:opacity-90 transition-opacity"
        >
          + new run
        </button>
      </div>
    </div>
  );
}
