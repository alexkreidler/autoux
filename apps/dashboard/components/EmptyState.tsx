"use client";

import { useEffect, useRef, useState } from "react";
import AvatarChip from "./AvatarChip";
import type { Persona } from "@/lib/types";
import { colorIndex } from "@/lib/utils";

interface Props {
  personas: Record<string, Persona>;
  onNewRun: () => void;
}

const ACCENT_COLORS = ["#B5A368", "#8FA37C", "#C19A6B", "#A8624A", "#C29440"] as const;

function PersonaPopover({ id, persona, onClose }: { id: string; persona: Persona; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const accent = ACCENT_COLORS[colorIndex(id)];

  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") onClose(); }
    function onClick(e: MouseEvent) { if (ref.current && !ref.current.contains(e.target as Node)) onClose(); }
    window.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => { window.removeEventListener("keydown", onKey); document.removeEventListener("mousedown", onClick); };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/20">
      <div
        ref={ref}
        className="bg-cream border w-[300px] p-5 flex flex-col gap-3"
        style={{ borderColor: accent }}
      >
        {/* avatar + archetype */}
        <div className="flex flex-col items-center gap-2">
          <div className="overflow-hidden" style={{ width: 96, height: 96, border: `2px solid ${accent}` }}>
            <AvatarChip personaId={id} size={96} />
          </div>
          <p className="text-[13px] font-medium text-ink lowercase text-center leading-tight">{persona.archetype}</p>
        </div>

        {/* metadata row */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 border-t border-line-soft pt-3">
          {[
            ["tech", persona.tech_literacy],
            ["age", persona.age_range],
            ["device", persona.device],
            ["fluency", persona.language_fluency],
          ].map(([k, v]) => (
            <div key={k} className="flex items-baseline gap-1.5">
              <span className="text-[10px] text-muted lowercase tracking-[0.04em] shrink-0">{k}</span>
              <span className="text-[11px] text-ink-soft lowercase">{v}</span>
            </div>
          ))}
        </div>

        {/* patience */}
        <div className="flex items-baseline gap-1.5 border-t border-line-soft pt-2">
          <span className="text-[10px] text-muted lowercase tracking-[0.04em]">patience</span>
          <span className="text-[11px] text-ink-soft">{persona.patience_steps} steps</span>
        </div>

        {/* quirks */}
        {persona.quirks.length > 0 && (
          <div className="border-t border-line-soft pt-2">
            <p className="text-[10px] text-muted lowercase tracking-[0.04em] mb-1">quirks</p>
            <ul className="flex flex-col gap-0.5">
              {persona.quirks.map((q, i) => (
                <li key={i} className="text-[11px] text-ink-soft lowercase flex gap-1.5">
                  <span style={{ color: accent }}>·</span>{q}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* prior experience */}
        {persona.prior_experience.length > 0 && (
          <div className="border-t border-line-soft pt-2">
            <p className="text-[10px] text-muted lowercase tracking-[0.04em] mb-1">prior experience</p>
            <ul className="flex flex-col gap-0.5">
              {persona.prior_experience.map((e, i) => (
                <li key={i} className="text-[11px] text-ink-soft lowercase flex gap-1.5">
                  <span style={{ color: accent }}>·</span>{e}
                </li>
              ))}
            </ul>
          </div>
        )}

        <button
          type="button"
          onClick={onClose}
          className="mt-1 text-[11px] text-muted lowercase hover:text-ink transition-colors text-right"
        >
          close ×
        </button>
      </div>
    </div>
  );
}

export default function EmptyState({ personas, onNewRun }: Props) {
  const ids = Object.keys(personas);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-0 py-10 select-none">
      {/* casting reel grid */}
      {ids.length > 0 && (
        <div className="flex flex-wrap justify-center gap-3 max-w-[680px] mb-10">
          {ids.slice(0, 25).map((id) => {
            const p = personas[id];
            const accent = ACCENT_COLORS[colorIndex(id)];
            return (
              <div
                key={id}
                className="flex flex-col items-center gap-1.5 group cursor-pointer"
                onClick={() => setSelectedId(id)}
              >
                <div
                  className="ring-1 ring-line group-hover:ring-2 transition-all duration-150 rounded"
                  style={{ "--tw-ring-color": accent } as React.CSSProperties}
                >
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

      {/* persona popover */}
      {selectedId && personas[selectedId] && (
        <PersonaPopover
          id={selectedId}
          persona={personas[selectedId]}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
