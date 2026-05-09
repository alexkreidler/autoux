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
}

export default function Cell({ session: s, persona }: Props) {
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

  return (
    <div className={`relative bg-white border ${borderColor} overflow-hidden flex flex-col h-full transition-colors duration-150 group`}>
      {/* top strip — avatar, name, status pill */}
      <div className="flex items-center gap-2.5 px-3 py-2.5 border-b border-line-soft bg-cream">
        <AvatarChip personaId={s.persona_id} size={36} />
        <div className="flex-1 min-w-0">
          <div className="text-[13px] font-medium text-ink lowercase truncate">{name}</div>
          <div className="text-[11px] text-muted mt-px truncate">{meta}</div>
        </div>
        <span
          className={`inline-block px-2 py-0.5 text-[10px] font-semibold lowercase tracking-[0.05em] border ${badgeStyle}`}
        >
          {status.replace("_", " ")}
        </span>
      </div>

      {/* iframe (or idle avatar). Takes the rest of the cell at 16:10. */}
      {s.live_view_url ? (
        <iframe
          src={s.live_view_url}
          className="w-full flex-1 border-0 bg-cream"
          sandbox="allow-scripts allow-same-origin"
          allow="clipboard-read; clipboard-write"
          title={`session ${s.browser_session_id}`}
        />
      ) : (
        <div className="w-full flex-1 bg-cream flex items-center justify-center">
          <AvatarChip personaId={s.persona_id} size={64} />
        </div>
      )}

      {/* corner overlay: tiny turn/tok footer + speech-bubble on hover */}
      <div className="absolute bottom-0 left-0 right-0 px-2 py-1 bg-white/90 backdrop-blur-sm border-t border-line-soft text-[10px] flex justify-between items-center gap-2 pointer-events-none">
        <span className="text-ink-soft font-mono truncate">
          turn {s.current_turn} · {actionLabel(s.last_action)}
        </span>
        <span className="text-muted tnum shrink-0">{totalTok.toLocaleString()} tok</span>
      </div>

      {/* speech bubble — appears on cell hover. Anchored top-right of the
          iframe area, points at the avatar in the top strip. */}
      {reasoning && (
        <div className="pointer-events-none absolute left-3 top-[58px] max-w-[80%] opacity-0 group-hover:opacity-100 transition-opacity duration-150 z-10">
          <div className="relative bg-ink text-cream text-[11px] leading-snug px-3 py-2 rounded-lg shadow-lg max-h-[120px] overflow-hidden">
            {/* tail — points up-left toward avatar */}
            <div className="absolute -top-1.5 left-3 w-3 h-3 bg-ink rotate-45" />
            <span className="relative italic">"{reasoning.length > 200 ? reasoning.slice(0, 200) + "…" : reasoning}"</span>
          </div>
        </div>
      )}
    </div>
  );
}
