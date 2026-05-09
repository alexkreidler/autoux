"use client";

import { useEffect, useRef, useState } from "react";
import AvatarChip from "./AvatarChip";
import { apiUrl, fetchJson } from "@/lib/api";
import type { ActiveRollout, Persona } from "@/lib/types";
import { actionLabel } from "@/lib/utils";

interface Props {
  session: ActiveRollout;
  persona?: Persona;
  isLive: boolean;        // false → session disappeared from registry
  onClose: () => void;
}

interface TrajectoryRecord {
  kind: "header" | "step" | "footer";
  // header
  agent_model?: string;
  started_at?: string;
  // step
  turn?: number;
  action?: { type: string; args: Record<string, unknown> };
  reasoning?: string[];
  observation?: { page_url?: string; page_title?: string; screenshot_path?: string };
  delta?: { dom_changed?: boolean; is_dead_click?: boolean; consecutive_unchanged?: number };
  timing?: { model_ms?: number; total_ms?: number };
  tokens?: { prompt_tokens?: number; completion_tokens?: number };
  // footer
  ended_at?: string;
  terminal_reason?: string;
  final_url?: string;
  error?: string;
}

interface TrajectoryPayload {
  path: string;
  records: TrajectoryRecord[];
}

const STATUS_BADGE: Record<string, string> = {
  running: "border-line text-ink-soft bg-white",
  success_dom: "border-sage bg-sage text-white",
  success_url: "border-sage bg-sage text-white",
  stuck: "border-amber bg-amber text-white",
  abandoned: "border-rust bg-rust text-white",
  error: "border-rust bg-rust text-white",
};

export default function FocusedCell({ session: s, persona, isLive, onClose }: Props) {
  const status = s.stage1_status ?? "running";
  const badgeStyle = STATUS_BADGE[status] ?? STATUS_BADGE.running;

  const name = persona?.archetype ?? s.persona_id;
  const meta = [persona?.tech_literacy, persona?.device, persona?.age_range, persona?.language_fluency]
    .filter(Boolean)
    .join(" · ");

  const tok = s.cumulative_tokens;
  const totalTok = (tok?.prompt_tokens ?? 0) + (tok?.completion_tokens ?? 0);

  // ---- Fetch trajectory + poll while live ----
  const [traj, setTraj] = useState<TrajectoryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const params = new URLSearchParams({
          persona_id: s.persona_id,
          task_id: s.task_id,
          browser_session_id: s.browser_session_id,
        });
        const data = await fetchJson<TrajectoryPayload>(`/api/trajectory?${params}`);
        if (!cancelled) setTraj(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "trajectory not available");
      }
    }
    load();
    // Poll every 2s while live so the transcript stays current
    if (isLive) {
      const id = setInterval(load, 2000);
      return () => {
        cancelled = true;
        clearInterval(id);
      };
    }
    return () => {
      cancelled = true;
    };
  }, [s.persona_id, s.task_id, s.browser_session_id, isLive]);

  // Auto-scroll transcript to bottom on new step
  useEffect(() => {
    const el = transcriptRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [traj?.records.length]);

  const steps = traj?.records.filter((r) => r.kind === "step") ?? [];
  const footer = traj?.records.find((r) => r.kind === "footer");

  return (
    <div
      className="fixed inset-0 z-40 flex items-stretch justify-stretch bg-ink/40 backdrop-blur-sm p-6 animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex w-full h-full bg-cream border border-line shadow-2xl overflow-hidden">
        {/* main: large iframe (or end-state placeholder) */}
        <div className="relative flex-1 bg-cream border-r border-line">
          {isLive && s.live_view_url ? (
            <iframe
              src={s.live_view_url}
              className="w-full h-full border-0 bg-cream"
              sandbox="allow-scripts allow-same-origin"
              allow="clipboard-read; clipboard-write"
              title={`focused ${s.browser_session_id}`}
            />
          ) : (
            // session ended — show last-known screenshot if we have one
            <div className="w-full h-full bg-cream flex flex-col items-center justify-center gap-3">
              <AvatarChip personaId={s.persona_id} size={96} />
              <div className="text-center">
                <div className="text-[14px] font-medium lowercase text-ink-soft">
                  session ended
                </div>
                {footer?.terminal_reason && (
                  <div className="text-[11px] text-muted mt-1 lowercase">
                    {footer.terminal_reason.replace("_", " ")}
                    {footer.error && <span className="text-rust"> · {footer.error.slice(0, 80)}</span>}
                  </div>
                )}
              </div>
              {steps.length > 0 && steps[steps.length - 1].observation?.screenshot_path && (
                <img
                  src={apiUrl(`/api/thumbnail?path=${encodeURIComponent(
                    findRunRelPath(traj?.path ?? "", steps[steps.length - 1].observation!.screenshot_path!)
                  )}`)}
                  alt="last screenshot"
                  className="max-h-[60%] max-w-[80%] border border-line shadow"
                />
              )}
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

        {/* side panel — fixed width transcript */}
        <aside className="w-[420px] flex flex-col bg-cream min-h-0">
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
            <Stat label="turn" value={s.current_turn} />
            <Stat label="tokens" value={totalTok.toLocaleString()} />
            <Stat label="stalled" value={s.consecutive_unchanged ?? 0} />
          </div>

          {/* transcript */}
          <div ref={transcriptRef} className="flex-1 overflow-y-auto min-h-0">
            <div className="px-4 py-2 sticky top-0 bg-cream border-b border-line-soft text-[10px] text-muted lowercase tracking-[0.05em] flex justify-between">
              <span>transcript ({steps.length} step{steps.length === 1 ? "" : "s"})</span>
              {isLive && (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-olive rounded-full animate-pulse" />
                  live
                </span>
              )}
            </div>

            {error && !traj && (
              <div className="px-4 py-3 text-[11px] text-muted italic">
                {error}
              </div>
            )}

            {steps.length === 0 && !error && (
              <div className="px-4 py-3 text-[11px] text-muted italic">
                waiting for first action…
              </div>
            )}

            <div className="divide-y divide-line-soft">
              {steps.map((step) => (
                <Step key={step.turn} step={step} runRel={traj?.path ?? ""} />
              ))}
              {footer && (
                <div className="px-4 py-3 bg-line-soft/40 text-[11px]">
                  <div className="text-[10px] text-muted lowercase tracking-[0.05em] mb-1">
                    terminal
                  </div>
                  <div className="font-mono text-ink-soft">{footer.terminal_reason}</div>
                  {footer.error && (
                    <div className="text-rust text-[10px] mt-1 break-all">{footer.error}</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-cream px-3 py-2.5">
      <div className="text-[10px] text-muted lowercase tracking-[0.05em]">{label}</div>
      <div className="text-[18px] font-medium tnum mt-0.5">{value}</div>
    </div>
  );
}

function Step({ step, runRel }: { step: TrajectoryRecord; runRel: string }) {
  const action = step.action;
  const reasoning = (step.reasoning ?? []).join(" ");
  const url = step.observation?.page_url;
  const dead = step.delta?.is_dead_click;
  const shotPath = step.observation?.screenshot_path;

  return (
    <div className="px-4 py-3">
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <div className="flex items-baseline gap-2 min-w-0">
          <span className="text-[10px] font-mono text-muted shrink-0">turn {step.turn}</span>
          <span className="text-[12px] font-mono text-ink-soft truncate">
            {action ? actionLabel({ type: action.type, args: action.args }) : "—"}
          </span>
        </div>
        {dead && (
          <span className="text-[9px] uppercase tracking-wider text-rust shrink-0">
            dead-click
          </span>
        )}
      </div>
      {reasoning && (
        <p className="text-[11px] text-ink-soft italic leading-snug">
          &ldquo;{reasoning.length > 240 ? reasoning.slice(0, 240) + "…" : reasoning}&rdquo;
        </p>
      )}
      {shotPath && (
        <img
          src={apiUrl(`/api/thumbnail?path=${encodeURIComponent(findRunRelPath(runRel, shotPath))}`)}
          alt={`step ${step.turn}`}
          loading="lazy"
          className="mt-2 w-full max-h-32 object-cover object-top border border-line-soft"
        />
      )}
      {url && (
        <div className="text-[10px] text-muted font-mono mt-1 truncate">{url}</div>
      )}
    </div>
  );
}

/**
 * The trajectory's screenshot_path is relative to its run dir (the dir that
 * holds both `trajectories/` and `thumbnails/`). Our /api/thumbnail expects
 * a path relative to runs/, so we glue the dir-portion of the trajectory
 * path back on.
 *
 *   trajectory path:           "runs/iter_001/trajectories/foo__bar.jsonl"
 *   step.screenshot_path:      "thumbnails/foo__bar/step_03.jpg"
 *   → "iter_001/thumbnails/foo__bar/step_03.jpg"
 *
 *   sweep trajectory path:     "runs/apps_sweep_X/kanboard/trajectories/foo__bar.jsonl"
 *   step.screenshot_path:      "thumbnails/foo__bar/step_03.jpg"
 *   → "apps_sweep_X/kanboard/thumbnails/foo__bar/step_03.jpg"
 */
function findRunRelPath(trajectoryPath: string, screenshotRel: string): string {
  // Capture everything between `runs/` and `/trajectories/`.
  const m = trajectoryPath.match(/(?:^|\/)runs\/(.+?)\/trajectories\//);
  const runDir = m ? m[1] : "";
  return runDir ? `${runDir}/${screenshotRel}` : screenshotRel;
}
