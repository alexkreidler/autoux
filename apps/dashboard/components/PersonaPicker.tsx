"use client";

import AvatarChip from "./AvatarChip";
import type { Persona } from "@/lib/types";

const ACCENT_CLASSES = [
  "border-olive text-olive",
  "border-sage text-sage",
  "border-clay text-clay",
  "border-rust text-rust",
  "border-amber text-amber",
];

interface Props {
  personas: Record<string, Persona>;
  selected: Set<string>;
  onChange: (next: Set<string>) => void;
}

export default function PersonaPicker({ personas, selected, onChange }: Props) {
  const ids = Object.keys(personas);

  function toggle(id: string) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(next);
  }

  return (
    <div>
      <div className="flex gap-3 text-[12px] text-muted mb-2">
        <button
          type="button"
          className="hover:text-ink underline underline-offset-2"
          onClick={() => onChange(new Set(ids))}
        >
          select all
        </button>
        <button
          type="button"
          className="hover:text-ink underline underline-offset-2"
          onClick={() => onChange(new Set())}
        >
          clear all
        </button>
      </div>
      <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto pr-1">
        {ids.map((id, i) => {
          const p = personas[id];
          const active = selected.has(id);
          const accent = ACCENT_CLASSES[i % ACCENT_CLASSES.length];
          return (
            <button
              key={id}
              type="button"
              onClick={() => toggle(id)}
              className={`inline-flex items-center gap-1.5 px-2 py-1 border text-[11px] lowercase transition-colors ${
                active ? accent + " bg-white" : "border-line text-muted bg-white"
              }`}
            >
              <AvatarChip personaId={id} size={18} />
              <span className="truncate max-w-[120px]">{p.archetype}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
