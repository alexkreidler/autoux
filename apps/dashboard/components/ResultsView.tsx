"use client";

import AvatarChip from "./AvatarChip";
import type { HistoricalSession, PersonaResult, Persona } from "@/lib/types";

interface Props {
  sessions: HistoricalSession[];
  personas: Record<string, Persona>;
  onSelectPersona?: (personaId: string) => void;
  onClose: () => void;
}

function buildResults(sessions: HistoricalSession[], personas: Record<string, Persona>): PersonaResult[] {
  const byPersona = new Map<string, HistoricalSession[]>();
  for (const s of sessions) {
    const existing = byPersona.get(s.persona_id) ?? [];
    existing.push(s);
    byPersona.set(s.persona_id, existing);
  }

  return Array.from(byPersona.entries()).map(([persona_id, rows]) => {
    const successes = rows.filter((r) =>
      r.stage1_status === "success_dom" || r.stage1_status === "success_url"
    );
    const terminalReasons: Record<string, number> = {};
    for (const r of rows) {
      const t = r.terminal_reason ?? r.stage1_status;
      terminalReasons[t] = (terminalReasons[t] ?? 0) + 1;
    }
    const avgSteps = rows.length > 0
      ? Math.round(rows.reduce((a, r) => a + r.current_turn, 0) / rows.length)
      : 0;

    // Pick a distinctive quote from last_reasoning of any step
    const quotes = rows.flatMap((r) => (r.last_reasoning ? [r.last_reasoning] : []));
    const quote = quotes.length > 0 ? quotes[Math.floor(quotes.length / 2)] : null;

    return {
      persona_id,
      archetype: personas[persona_id]?.archetype,
      n_trajectories: rows.length,
      n_success: successes.length,
      success_rate: rows.length > 0 ? successes.length / rows.length : 0,
      avg_steps: avgSteps,
      terminal_reasons: terminalReasons,
      distinctive_quote: quote ? (quote.length > 120 ? quote.slice(0, 120) + "…" : quote) : null,
    };
  });
}

const STATUS_COLOR: Record<string, string> = {
  success_dom: "text-sage",
  success_url: "text-sage",
  abandoned: "text-rust",
  stuck: "text-amber",
  error: "text-rust",
  running: "text-ink-soft",
};

export default function ResultsView({ sessions, personas, onSelectPersona, onClose }: Props) {
  const results = buildResults(sessions, personas);
  const totalSuccess = results.reduce((a, r) => a + r.n_success, 0);
  const totalRuns = results.reduce((a, r) => a + r.n_trajectories, 0);
  const overallRate = totalRuns > 0 ? ((totalSuccess / totalRuns) * 100).toFixed(1) : "—";

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-line bg-white">
        <div className="flex items-baseline gap-4">
          <span className="text-[13px] font-medium lowercase text-ink">per-persona results</span>
          <span className="text-[11px] text-muted">{totalRuns} runs · {overallRate}% success</span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-[12px] text-muted hover:text-ink lowercase transition-colors"
        >
          ← grid view
        </button>
      </div>

      {/* table */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {/* column headers */}
        <div className="grid gap-px sticky top-0 bg-cream border-b border-line z-10"
          style={{ gridTemplateColumns: "160px 60px 60px 80px 1fr" }}>
          {["persona", "runs", "steps", "success", "quote / reason"].map((h) => (
            <div key={h} className="px-3 py-2 text-[10px] text-muted lowercase tracking-[0.05em]">{h}</div>
          ))}
        </div>

        <div className="divide-y divide-line-soft">
          {results.map((r) => {
            const topReason = Object.entries(r.terminal_reasons).sort((a, b) => b[1] - a[1])[0];
            const reasonColor = STATUS_COLOR[topReason?.[0] ?? "error"] ?? "text-muted";

            return (
              <button
                key={r.persona_id}
                type="button"
                onClick={() => onSelectPersona?.(r.persona_id)}
                className="w-full text-left grid gap-px hover:bg-line-soft/30 transition-colors items-start"
                style={{ gridTemplateColumns: "160px 60px 60px 80px 1fr" }}
              >
                {/* persona */}
                <div className="px-3 py-3 flex items-center gap-2 min-w-0">
                  <AvatarChip personaId={r.persona_id} size={24} />
                  <span className="text-[12px] text-ink lowercase truncate">
                    {r.archetype ?? r.persona_id}
                  </span>
                </div>

                {/* runs */}
                <div className="px-3 py-3 text-[12px] tnum text-ink-soft">{r.n_trajectories}</div>

                {/* avg steps */}
                <div className="px-3 py-3 text-[12px] tnum text-ink-soft">{r.avg_steps}</div>

                {/* success rate */}
                <div className="px-3 py-3">
                  <div
                    className={`text-[12px] tnum font-medium ${
                      r.success_rate > 0.7 ? "text-sage" : r.success_rate > 0.3 ? "text-amber" : "text-rust"
                    }`}
                  >
                    {(r.success_rate * 100).toFixed(0)}%
                  </div>
                  <div className="mt-1 h-1 bg-line-soft rounded overflow-hidden w-12">
                    <div
                      className={`h-full rounded ${r.success_rate > 0.7 ? "bg-sage" : r.success_rate > 0.3 ? "bg-amber" : "bg-rust"}`}
                      style={{ width: `${r.success_rate * 100}%` }}
                    />
                  </div>
                </div>

                {/* quote / reason */}
                <div className="px-3 py-3 min-w-0">
                  {r.distinctive_quote ? (
                    <p className="text-[11px] text-ink-soft italic leading-snug line-clamp-2">
                      &ldquo;{r.distinctive_quote}&rdquo;
                    </p>
                  ) : topReason ? (
                    <span className={`text-[11px] lowercase ${reasonColor}`}>
                      {topReason[0].replace(/_/g, " ")} ×{topReason[1]}
                    </span>
                  ) : null}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
