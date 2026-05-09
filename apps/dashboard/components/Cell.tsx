"use client";

import AvatarChip from "./AvatarChip";
import type { ActiveRollout, Persona } from "@/lib/types";
import { actionLabel } from "@/lib/utils";

const STATUS_BORDER: Record<string, string> = {
  running: "border-line",
  success_dom: "border-sage",
  success_url: "border-sage",
  stuck: "border-amber",
  abandoned: "border-rust",
  error: "border-rust",
};

const STATUS_BADGE: Record<string, string> = {
  running: "border-line text-ink-soft bg-white",
  success_dom: "border-sage bg-sage text-white",
  success_url: "border-sage bg-sage text-white",
  stuck: "border-amber bg-amber text-white",
  abandoned: "border-rust bg-rust text-white",
  error: "border-rust bg-rust text-white",
};

interface Props {
  session: ActiveRollout;
  persona?: Persona;
  selected?: boolean;
  selectMode?: boolean;
  onFocus?: (id: string) => void;
  onToggleSelect?: (id: string) => void;
}

export default function Cell({
  session: s,
  persona,
  selected = false,
  selectMode = false,
  onFocus,
  onToggleSelect,
}: Props) {
  const status = s.stage1_status ?? "running";
  const borderColor = STATUS_BORDER[status] ?? "border-line";
  const badgeStyle = STATUS_BADGE[status] ?? STATUS_BADGE.running;

  const name = persona?.archetype ?? s.persona_id;
  const meta = [
    persona?.tech_literacy,
    persona?.device,
    persona?.age_range,
    `task: ${s.task_id}`,
  ]
    .filter(Boolean)
    .join(" · ");

  const tok = s.cumulative_tokens;
  const totalTok = (tok?.prompt_tokens ?? 0) + (tok?.completion_tokens ?? 0);
  const reasoning = s.last_reasoning ?? "";

  // Selection ring: olive when selected, transparent otherwise. Outer wrapper
  // animates ring + scale so the cell pops when picked from a marquee.
  const ringClasses = selected
    ? "ring-2 ring-olive ring-offset-2 ring-offset-cream scale-[0.98]"
    : "";

  return (
    <div
      data-cell-id={s.browser_session_id}
      className={`relative bg-white border ${borderColor} overflow-hidden h-full transition-all duration-150 group ${ringClasses}`}
    >
      {/* iframe takes the entire cell at natural 16:10 */}
      {s.live_view_url ? (
        <iframe
          src={s.live_view_url}
          className="w-full h-full border-0 bg-cream block"
          sandbox="allow-scripts allow-same-origin"
          allow="clipboard-read; clipboard-write"
          title={`session ${s.browser_session_id}`}
        />
      ) : (
        <div className="w-full h-full bg-cream flex items-center justify-center">
          <AvatarChip personaId={s.persona_id} size={64} />
        </div>
      )}

      {/* Click-blocker overlay — only active in select-mode. Captures mouse
          so the iframe doesn't eat clicks while the user is picking cells. */}
      {selectMode && (
        <button
          type="button"
          aria-label={selected ? "deselect" : "select"}
          onClick={(e) => {
            e.stopPropagation();
            onToggleSelect?.(s.browser_session_id);
          }}
          className={`absolute inset-0 z-10 cursor-crosshair ${
            selected ? "bg-olive/10" : "bg-transparent hover:bg-olive/5"
          } transition-colors`}
        />
      )}

      {/* Hover-only "expand" button — focus this cell. Top-right, just below
          the status pill. Hidden in select mode (different interaction). */}
      {!selectMode && onFocus && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onFocus(s.browser_session_id);
          }}
          aria-label="focus this rollout"
          title="focus (click) · esc to exit"
          className="absolute top-2 right-2 mt-7 z-20 w-7 h-7 flex items-center justify-center bg-white/90 backdrop-blur-sm border border-line text-ink-soft hover:bg-ink hover:text-cream transition-colors opacity-0 group-hover:opacity-100"
        >
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 9V3h6M21 9V3h-6M3 15v6h6M21 15v6h-6" />
          </svg>
        </button>
      )}

      {/* avatar chip — top-left. Hover reveals title + meta tooltip below. */}
      <div className="absolute top-2 left-2 group/avatar">
        <div className="ring-2 ring-white shadow-sm rounded">
          <AvatarChip personaId={s.persona_id} size={32} />
        </div>
        {/* tooltip — title + meta on avatar hover */}
        <div className="pointer-events-none absolute top-full left-0 mt-1 px-2 py-1.5 bg-ink text-cream text-[11px] leading-tight rounded shadow-lg opacity-0 group-hover/avatar:opacity-100 transition-opacity duration-150 whitespace-nowrap z-20">
          <div className="font-medium lowercase">{name}</div>
          <div className="text-[10px] opacity-75 mt-0.5">{meta}</div>
        </div>
      </div>

      {/* status pill — top-right, no border */}
      <span
        className={`absolute top-2 right-2 px-2 py-0.5 text-[10px] font-semibold lowercase tracking-[0.05em] border ${badgeStyle} shadow-sm`}
      >
        {status.replace("_", " ")}
      </span>

      {/* bottom overlay: turn/action/tokens. Always visible. */}
      <div className="absolute bottom-0 left-0 right-0 px-2 py-1 bg-white/90 backdrop-blur-sm border-t border-line-soft text-[10px] flex justify-between items-center gap-2 pointer-events-none">
        <span className="text-ink-soft font-mono truncate">
          turn {s.current_turn} · {actionLabel(s.last_action)}
        </span>
        <span className="text-muted tnum shrink-0">{totalTok.toLocaleString()} tok</span>
      </div>

      {/* speech bubble — model reasoning on cell hover (group). */}
      {reasoning && (
        <div className="pointer-events-none absolute left-2 top-12 max-w-[85%] opacity-0 group-hover:opacity-100 transition-opacity duration-150 z-10">
          <div className="relative bg-ink text-cream text-[11px] leading-snug px-3 py-2 rounded-lg shadow-lg max-h-[140px] overflow-hidden">
            {/* tail — points up-left toward the avatar */}
            <div className="absolute -top-1.5 left-3 w-3 h-3 bg-ink rotate-45" />
            <span className="relative italic">&ldquo;{reasoning.length > 220 ? reasoning.slice(0, 220) + "…" : reasoning}&rdquo;</span>
          </div>
        </div>
      )}
    </div>
  );
}
