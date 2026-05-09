"use client";

import AvatarChip from "./AvatarChip";
import type { ActiveRollout, Persona } from "@/lib/types";
import { actionLabel } from "@/lib/utils";

interface Props {
  session: ActiveRollout;
  persona?: Persona;
  onClose: () => void;
}

const STATUS_BADGE: Record<string, string> = {
  running: "border-line text-ink-soft bg-white",
  success_dom: "border-sage bg-sage text-white",
  success_url: "border-sage bg-sage text-white",
  stuck: "border-amber bg-amber text-white",
  abandoned: "border-rust bg-rust text-white",
  error: "border-rust bg-rust text-white",
};

/**
 * Full-screen focused view of a single rollout. Triggered by clicking a
 * cell's expand button. Esc dismisses (handled by Dashboard).
 *
 * Layout: dark backdrop → cream paper card → 16:9 iframe + side panel with
 * persona, recent reasoning, action history. The side panel is the part the
 * grid view can't show.
 */
export default function FocusedCell({ session: s, persona, onClose }: Props) {
  const status = s.stage1_status ?? "running";
  const badgeStyle = STATUS_BADGE[status] ?? STATUS_BADGE.running;

  const name = persona?.archetype ?? s.persona_id;
  const meta = [
    persona?.tech_literacy,
    persona?.device,
    persona?.age_range,
    persona?.language_fluency,
  ]
    .filter(Boolean)
    .join(" · ");

  const tok = s.cumulative_tokens;
  const totalTok = (tok?.prompt_tokens ?? 0) + (tok?.completion_tokens ?? 0);

  return (
    <div
      className="fixed inset-0 z-40 flex items-stretch justify-stretch bg-ink/40 backdrop-blur-sm p-6 animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex w-full h-full bg-cream border border-line shadow-2xl">
        {/* main: large iframe */}
        <div className="relative flex-1 bg-cream border-r border-line">
          {s.live_view_url ? (
            <iframe
              src={s.live_view_url}
              className="w-full h-full border-0 bg-cream"
              sandbox="allow-scripts allow-same-origin"
              allow="clipboard-read; clipboard-write"
              title={`focused ${s.browser_session_id}`}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <AvatarChip personaId={s.persona_id} size={128} />
            </div>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="exit focus"
            title="exit focus (esc)"
            className="absolute top-3 left-3 px-3 py-1.5 bg-white/90 backdrop-blur-sm border border-line text-[12px] text-ink-soft lowercase hover:bg-ink hover:text-cream transition-colors"
          >
            ← back
          </button>
        </div>

        {/* side panel */}
        <aside className="w-[360px] flex flex-col bg-cream">
          {/* persona header */}
          <div className="flex items-start gap-3 p-4 border-b border-line-soft">
            <div className="ring-2 ring-white shadow-sm rounded shrink-0">
              <AvatarChip personaId={s.persona_id} size={56} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-[14px] font-medium text-ink lowercase">{name}</div>
              <div className="text-[11px] text-muted mt-0.5">{meta}</div>
              <div className="text-[11px] text-muted mt-0.5 font-mono truncate">
                task: {s.task_id}
              </div>
            </div>
            <span
              className={`px-2 py-0.5 text-[10px] font-semibold lowercase tracking-[0.05em] border ${badgeStyle} shrink-0`}
            >
              {status.replace("_", " ")}
            </span>
          </div>

          {/* live stats */}
          <div className="grid grid-cols-3 gap-px bg-line-soft border-b border-line-soft">
            <div className="bg-cream px-3 py-2.5">
              <div className="text-[10px] text-muted lowercase tracking-[0.05em]">turn</div>
              <div className="text-[18px] font-medium tnum mt-0.5">{s.current_turn}</div>
            </div>
            <div className="bg-cream px-3 py-2.5">
              <div className="text-[10px] text-muted lowercase tracking-[0.05em]">tokens</div>
              <div className="text-[18px] font-medium tnum mt-0.5">
                {totalTok.toLocaleString()}
              </div>
            </div>
            <div className="bg-cream px-3 py-2.5">
              <div className="text-[10px] text-muted lowercase tracking-[0.05em]">stalled</div>
              <div className="text-[18px] font-medium tnum mt-0.5">
                {s.consecutive_unchanged ?? 0}
              </div>
            </div>
          </div>

          {/* last action */}
          <div className="px-4 py-3 border-b border-line-soft">
            <div className="text-[10px] text-muted lowercase tracking-[0.05em] mb-1">
              last action
            </div>
            <div className="text-[12px] font-mono text-ink-soft break-all">
              {actionLabel(s.last_action) || "—"}
            </div>
          </div>

          {/* reasoning */}
          <div className="flex-1 overflow-y-auto px-4 py-3 min-h-0">
            <div className="text-[10px] text-muted lowercase tracking-[0.05em] mb-2">
              model reasoning
            </div>
            {s.last_reasoning ? (
              <p className="text-[12px] text-ink-soft italic leading-relaxed">
                &ldquo;{s.last_reasoning}&rdquo;
              </p>
            ) : (
              <p className="text-[11px] text-muted">no reasoning emitted on this turn.</p>
            )}
          </div>

          {/* footer: ids */}
          <div className="px-4 py-2 border-t border-line-soft text-[10px] text-muted font-mono">
            <div className="truncate">session: {s.browser_session_id.slice(0, 16)}…</div>
            <div className="truncate">target: {s.current_url ?? s.target_url}</div>
          </div>
        </aside>
      </div>
    </div>
  );
}
