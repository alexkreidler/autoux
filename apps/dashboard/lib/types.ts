// Mirror of usersim/schemas.py — keep in sync with backend models

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
