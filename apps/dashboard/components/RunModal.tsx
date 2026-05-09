"use client";

import { useEffect, useState, useCallback } from "react";
import { apiUrl, fetchJson } from "@/lib/api";
import PersonaPicker from "./PersonaPicker";
import type { Persona, ConfigDef, RunPayload } from "@/lib/types";

// Fallback config when /api/configs is not yet implemented
const FALLBACK_CONFIG: ConfigDef = {
  path: "configs/taxcaster.yaml",
  target_url: "https://turbotax.intuit.com/tax-tools/calculators/taxcaster/",
  tasks: [
    { id: "single_w2_basic", description: "Single filer, $65k W-2 — estimate refund" },
    { id: "married_kids", description: "Married filing jointly, 2 kids, $120k" },
    { id: "freelancer_1099", description: "Freelancer, $80k 1099 — estimate refund" },
  ],
};

interface Props {
  personas: Record<string, Persona>;
  onClose: () => void;
}

export default function RunModal({ personas, onClose }: Props) {
  const [configs, setConfigs] = useState<ConfigDef[]>([FALLBACK_CONFIG]);
  const [agents, setAgents] = useState<string[]>(["northstar"]);
  const [selectedConfig, setSelectedConfig] = useState<ConfigDef>(FALLBACK_CONFIG);
  const [targetUrl, setTargetUrl] = useState(FALLBACK_CONFIG.target_url);
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(
    new Set(FALLBACK_CONFIG.tasks.map((t) => t.id))
  );
  const [selectedPersonas, setSelectedPersonas] = useState<Set<string>>(
    new Set(Object.keys(personas))
  );
  const [concurrency, setConcurrency] = useState(20);
  const [maxTurns, setMaxTurns] = useState(20);
  const [stuckThreshold, setStuckThreshold] = useState(3);
  const [patience, setPatience] = useState<number | "">("");
  const [iterLabel, setIterLabel] = useState("");
  const [runLabel, setRunLabel] = useState("");
  const [agent, setAgent] = useState("northstar");
  const [agentEndpoint, setAgentEndpoint] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Try to load real configs + agents; fall back silently
    fetchJson<ConfigDef[]>("/api/configs")
      .then((data) => {
        if (data?.length) {
          setConfigs(data);
          setSelectedConfig(data[0]);
          setTargetUrl(data[0].target_url);
          setSelectedTasks(new Set(data[0].tasks.map((t) => t.id)));
        }
      })
      .catch(() => {});
    fetchJson<string[]>("/api/agents")
      .then((data) => { if (data?.length) setAgents(data); })
      .catch(() => {});
  }, []);

  function handleConfigChange(path: string) {
    const cfg = configs.find((c) => c.path === path) ?? configs[0];
    setSelectedConfig(cfg);
    setTargetUrl(cfg.target_url);
    setSelectedTasks(new Set(cfg.tasks.map((t) => t.id)));
  }

  function toggleTask(id: string) {
    const next = new Set(selectedTasks);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedTasks(next);
  }

  const handleBackdrop = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose]
  );

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const payload: RunPayload = {
      config: selectedConfig.path,
      personas: [...selectedPersonas],
      tasks: [...selectedTasks],
      concurrency,
      max_turns: maxTurns,
      iteration: iterLabel ? parseInt(iterLabel, 10) : 0,
      agent,
      agent_endpoint: agentEndpoint || undefined,
      label: runLabel || undefined,
      stuck_threshold: stuckThreshold,
      patience: patience === "" ? undefined : patience,
    };
    try {
      const res = await fetch(apiUrl("/api/run"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const detail = await res.text().catch(() => "");
        throw new Error(`${res.status} ${res.statusText}${detail ? ` — ${detail}` : ""}`);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "unknown error");
    } finally {
      setSubmitting(false);
    }
  }

  const labelClass = "block text-[11px] text-muted lowercase tracking-[0.05em] mb-1";
  const inputClass =
    "w-full border border-line bg-white px-3 py-2 text-[13px] text-ink placeholder:text-muted focus:outline-none focus:border-olive";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30"
      onClick={handleBackdrop}
    >
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-cream border border-line p-8">
        <div className="flex items-baseline justify-between mb-6">
          <h2 className="text-[16px] font-medium lowercase tracking-[-0.01em]">new run</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-[13px] text-muted hover:text-ink lowercase"
          >
            cancel
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {/* config */}
          <div>
            <label className={labelClass}>config</label>
            <select
              className={inputClass}
              value={selectedConfig.path}
              onChange={(e) => handleConfigChange(e.target.value)}
            >
              {configs.map((c) => (
                <option key={c.path} value={c.path}>{c.path}</option>
              ))}
            </select>
          </div>

          {/* target url */}
          <div>
            <label className={labelClass}>target url</label>
            <input
              type="url"
              className={inputClass}
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
            />
          </div>

          {/* tasks */}
          <div>
            <label className={labelClass}>tasks</label>
            <div className="flex flex-col gap-1.5">
              {selectedConfig.tasks.map((t) => (
                <label key={t.id} className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedTasks.has(t.id)}
                    onChange={() => toggleTask(t.id)}
                    className="mt-0.5 accent-olive"
                  />
                  <span className="text-[12px] text-ink-soft">
                    <span className="font-medium text-ink">{t.id}</span> — {t.description}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* personas */}
          <div>
            <label className={labelClass}>
              personas ({selectedPersonas.size} selected)
            </label>
            <PersonaPicker
              personas={personas}
              selected={selectedPersonas}
              onChange={setSelectedPersonas}
            />
          </div>

          {/* concurrency */}
          <div>
            <label className={labelClass}>
              concurrency — {concurrency}
              {concurrency > 50 && <span className="ml-2 text-rust">(may hit kernel/tzafon quotas)</span>}
            </label>
            <input
              type="range"
              min={1}
              max={Math.max(100, Object.keys(personas).length)}
              value={concurrency}
              onChange={(e) => setConcurrency(Number(e.target.value))}
              className="w-full accent-olive"
            />
          </div>

          {/* max turns */}
          <div>
            <label className={labelClass}>max turns — {maxTurns}</label>
            <input
              type="range"
              min={5}
              max={100}
              value={maxTurns}
              onChange={(e) => setMaxTurns(Number(e.target.value))}
              className="w-full accent-olive"
            />
          </div>

          {/* stuck threshold */}
          <div>
            <label className={labelClass}>
              stuck threshold — {stuckThreshold === 0 ? "disabled" : `${stuckThreshold} turns of no DOM change`}
            </label>
            <input
              type="range"
              min={0}
              max={20}
              value={stuckThreshold}
              onChange={(e) => setStuckThreshold(Number(e.target.value))}
              className="w-full accent-olive"
            />
          </div>

          {/* patience override */}
          <div>
            <label className={labelClass}>
              patience override —{" "}
              {patience === "" ? "use persona's own patience_steps" : patience === 0 ? "disabled (no abandonment)" : `${patience} turns`}
            </label>
            <input
              type="range"
              min={0}
              max={50}
              value={patience === "" ? -1 : patience}
              onChange={(e) => {
                const v = Number(e.target.value);
                setPatience(v < 0 ? "" : v);
              }}
              className="w-full accent-olive"
            />
            <div className="text-[10px] text-muted mt-1">
              drag to leftmost (-1) to use each persona&apos;s own patience.
            </div>
          </div>

          {/* run label */}
          <div>
            <label className={labelClass}>run label (optional, slugifies into out_dir)</label>
            <input
              type="text"
              className={inputClass}
              placeholder="e.g. taxcaster_100p"
              value={runLabel}
              onChange={(e) => setRunLabel(e.target.value)}
            />
          </div>

          {/* iteration number override */}
          <div>
            <label className={labelClass}>iteration number (optional, default auto)</label>
            <input
              type="text"
              className={inputClass}
              placeholder="auto"
              value={iterLabel}
              onChange={(e) => setIterLabel(e.target.value)}
            />
          </div>

          {/* agent */}
          <div>
            <label className={labelClass}>agent provider</label>
            <select
              className={inputClass}
              value={agent}
              onChange={(e) => setAgent(e.target.value)}
            >
              {agents.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          {agent !== "northstar" && (
            <div>
              <label className={labelClass}>agent endpoint</label>
              <input
                type="url"
                className={inputClass}
                placeholder="https://..."
                value={agentEndpoint}
                onChange={(e) => setAgentEndpoint(e.target.value)}
              />
            </div>
          )}

          {error && (
            <p className="text-[12px] text-rust">{error}</p>
          )}

          <div className="flex items-center justify-end gap-4 pt-2 border-t border-line-soft">
            <button
              type="button"
              onClick={onClose}
              className="text-[13px] text-muted hover:text-ink lowercase"
            >
              cancel
            </button>
            <button
              type="submit"
              disabled={submitting || selectedPersonas.size === 0 || selectedTasks.size === 0}
              className="px-5 py-2 bg-olive text-white text-[13px] lowercase tracking-[0.02em] hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              {submitting ? "starting…" : "kick off"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
