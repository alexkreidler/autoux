"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "@/lib/api";
import type { Feedback } from "@/lib/types";
import { fmtPct, fmtSigned } from "@/lib/utils";

interface MetricCellProps {
  label: string;
  value: string;
  sub?: string;
  valueClass?: string;
}

function MetricCell({ label, value, sub, valueClass = "" }: MetricCellProps) {
  return (
    <div className="px-[18px] py-[14px] border-r border-line-soft last:border-r-0">
      <div className="text-[11px] text-muted lowercase tracking-[0.05em] mb-1">{label}</div>
      <div className={`text-[22px] font-medium tracking-[-0.02em] tnum ${valueClass}`}>{value}</div>
      {sub && <div className="text-[11px] text-muted mt-0.5">{sub}</div>}
    </div>
  );
}

export default function MetricBar() {
  const [fb, setFb] = useState<Feedback | null>(null);

  useEffect(() => {
    let alive = true;
    async function poll() {
      try {
        const data = await fetchJson<Feedback | null>("/api/feedback");
        if (alive) setFb(data);
      } catch {
        // ignore — backend may not be reachable yet
      }
    }
    poll();
    const id = setInterval(poll, 4000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  const m = fb?.metrics;
  const delta = m?.delta_gameable_vs_heldout ?? null;
  const deltaClass =
    typeof delta === "number" && delta > 0.05 ? "text-rust" : "text-sage";

  return (
    <div className="grid grid-cols-5 border border-line bg-white mb-[22px]">
      <MetricCell label="iteration" value={fb ? String(fb.iteration) : "—"} />
      <MetricCell label="gameable" value={fmtPct(m?.success_rate_gameable)} />
      <MetricCell
        label="held-out"
        value={fmtPct(m?.success_rate_heldout)}
        valueClass={m?.success_rate_heldout == null ? "text-muted" : ""}
      />
      <MetricCell
        label="δ hack"
        value={fmtSigned(delta)}
        sub="gameable − held-out"
        valueClass={deltaClass}
      />
      <MetricCell label="abandoned" value={fmtPct(m?.abandonment_rate)} />
    </div>
  );
}
