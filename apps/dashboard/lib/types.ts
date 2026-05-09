// Mirror of usersim/schemas.py — keep in sync with backend models

export interface TrajectoryRecord {
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

export interface TurnMeta {
  model_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  cached_tokens: number;
  cost_usd: number;
}

export interface Action {
  type: string;
  args: Record<string, unknown>;
}

export type Stage1Status =
  | "running"
  | "success_dom"
  | "success_url"
  | "abandoned"
  | "stuck"
  | "error";

export interface ActiveRollout {
  browser_session_id: string;
  persona_id: string;
  task_id: string;
  target_url: string;
  started_at: string;
  live_view_url: string;
  current_turn: number;
  last_action: Action | null;
  last_reasoning: string | null;
  current_url: string | null;
  current_title: string | null;
  current_dom_hash: string | null;
  consecutive_unchanged: number;
  cumulative_tokens: TurnMeta;
  cumulative_ms: number;
  stage1_status: Stage1Status;
}

export interface Persona {
  id: string;
  archetype: string;
  tech_literacy: "low" | "medium" | "high";
  patience_steps: number;
  quirks: string[];
  age_range: "18-25" | "26-40" | "41-60" | "61+";
  device: "desktop" | "mobile" | "tablet";
  language_fluency: "native" | "proficient" | "limited";
  prior_experience: string[];
  temperature: number;
  avatar_path: string | null;
}

export interface Metrics {
  success_rate_gameable: number;
  success_rate_heldout: number | null;
  delta_gameable_vs_heldout: number | null;
  median_steps_to_success: number | null;
  abandonment_rate: number;
  errors_per_iteration: number;
}

export interface Feedback {
  iteration: number;
  target_commit: string;
  n_trajectories: number;
  metrics: Metrics;
  top_friction_clusters: unknown[];
  regressions_vs_prev: unknown[];
  raw_trajectory_dir: string;
}

export interface TaskDef {
  id: string;
  description: string;
}

export interface ConfigDef {
  path: string;
  target_url: string;
  tasks: TaskDef[];
}

// Historical run entry from /api/runs/historical
export interface HistoricalRun {
  run_dir: string;          // e.g. "sweep_open_20260509_144457"
  display_name: string;     // human-readable label
  layout: "flat" | "sweep"; // flat = iter_X, sweep = multi-app nested
  apps: string[];           // for sweep: list of app sub-dirs
  n_trajectories: number;
  started_at: string | null;
  has_feedback: boolean;
  has_grid_mp4: boolean;
  target_summary: string | null;
}

// A "loaded" historical run — sessions reconstructed from trajectory footers
export interface HistoricalSession {
  browser_session_id: string; // synthetic: run_dir + "__" + persona + "__" + task
  persona_id: string;
  task_id: string;
  target_url: string;
  started_at: string;
  live_view_url: string;       // empty — no live view for historical
  current_turn: number;
  last_action: null;
  last_reasoning: string | null;
  current_url: string | null;
  current_title: string | null;
  current_dom_hash: string | null;
  consecutive_unchanged: number;
  cumulative_tokens: {
    model_ms: number; prompt_tokens: number;
    completion_tokens: number; cached_tokens: number; cost_usd: number;
  };
  cumulative_ms: number;
  stage1_status: "running" | "success_dom" | "success_url" | "abandoned" | "stuck" | "error";
  // extra historical fields
  run_dir: string;
  app?: string;               // set for sweep sub-dirs
  terminal_reason?: string;
  replay_path?: string | null; // relative to runs/ if available
  trajectory_records?: TrajectoryRecord[]; // pre-fetched for scrubber playback
  n_steps?: number;           // total step count (from trajectory footer or records)
}

// Per-persona result summary (from feedback.json or computed from trajectories)
export interface PersonaResult {
  persona_id: string;
  archetype?: string;
  n_trajectories: number;
  n_success: number;
  success_rate: number;
  avg_steps: number;
  terminal_reasons: Record<string, number>;
  distinctive_quote: string | null;
}

// Mirror of usersim/web/server.py:RunRequest
export interface RunPayload {
  config: string;
  personas?: string[];
  tasks?: string[];
  concurrency: number;
  max_turns?: number;
  iteration: number;
  agent?: string;
  agent_endpoint?: string;
  label?: string;
  stuck_threshold?: number;  // 0 disables the stuck-loop terminator
  patience?: number;         // 0 disables persona-patience abandonment
}
