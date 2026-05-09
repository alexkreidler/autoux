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
    <div className={`bg-white border ${borderColor} overflow-hidden flex flex-col transition-colors duration-150`}>
      {/* top strip */}
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

      {/* live iframe — fills cell width, 16:10 */}
      {s.live_view_url ? (
        <iframe
          src={s.live_view_url}
          className="w-full border-0 bg-cream"
          style={{ aspectRatio: "16/10" }}
          sandbox="allow-scripts allow-same-origin"
          allow="clipboard-read; clipboard-write"
          title={`session ${s.browser_session_id}`}
        />
      ) : (
        // idle placeholder
        <div
          className="w-full bg-cream flex items-center justify-center"
          style={{ aspectRatio: "16/10" }}
        >
          <AvatarChip personaId={s.persona_id} size={64} />
        </div>
      )}

      {/* bottom strip */}
      <div className="px-3 py-2.5 border-t border-line-soft text-[11px]">
        <div className="flex justify-between gap-2 mb-1 text-muted tnum">
          <span className="text-ink-soft font-mono">
            turn {s.current_turn} · {actionLabel(s.last_action)}
          </span>
          <span>{totalTok.toLocaleString()} tok</span>
        </div>
        <div className="text-ink-soft italic overflow-hidden text-ellipsis whitespace-nowrap">
          {reasoning}
        </div>
      </div>
    </div>
  );
}
