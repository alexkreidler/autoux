import type { Action } from "./types";

export function actionLabel(action: Action | null): string {
  if (!action) return "";
  const args = action.args ?? {};
  if (action.type === "click" || action.type === "double_click") {
    return `${action.type}(${args.x},${args.y})`;
  }
  if (action.type === "type") {
    const txt = String(args.text ?? "");
    return `type("${txt.length > 20 ? txt.slice(0, 20) + "…" : txt}")`;
  }
  if (action.type === "scroll") {
    return `scroll(${args.x},${args.y} Δ${args.scroll_x},${args.scroll_y})`;
  }
  if (action.type === "keypress") {
    return `keypress(${(args.keys as string[] | undefined ?? []).join("+")})`;
  }
  const raw = JSON.stringify(args);
  return `${action.type}(${raw.length > 40 ? raw.slice(0, 40) + "…" : raw})`;
}

export function initials(s: string): string {
  if (!s) return "?";
  return (
    s
      .split(/[\s_-]+/)
      .slice(0, 2)
      .map((w) => w[0])
      .join("")
      .toUpperCase() || "?"
  );
}

// Stable color index 0-4 from a string — used for avatar fallback
export function colorIndex(s: string): number {
  let h = 0;
  for (const c of s) h = ((h * 31 + c.charCodeAt(0)) | 0);
  return Math.abs(h) % 5;
}

export function fmtPct(x: number | null | undefined): string {
  return typeof x === "number" ? `${(x * 100).toFixed(1)}%` : "—";
}

export function fmtSigned(x: number | null | undefined): string {
  if (typeof x !== "number") return "—";
  return `${x >= 0 ? "+" : ""}${(x * 100).toFixed(1)}%`;
}
