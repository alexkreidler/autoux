"""Failure clustering: rule-based pattern detection (primary) + HDBSCAN residual.

Why rule-based first: with N=10–100 trajectories per iteration, statistical
clustering on bag-of-words doesn't have enough signal. Concrete patterns —
"form clears on submit", "stuck on button at (200,500)" — map 1:1 to coding-
agent fixes. Statistical clustering catches the long tail that doesn't match
any known pattern.

Output: list[FrictionCluster], one per detected pattern (with all matching
trajectories grouped) plus residual clusters from HDBSCAN.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Protocol

import numpy as np

from usersim.reduce.patterns import PatternMatch, detect_all
from usersim.schemas import FrictionCluster, Outcome, Trajectory


class Embedder(Protocol):
    def fit_transform(self, texts: list[str]) -> np.ndarray: ...


def cluster_failures(
    outcomes: list[Outcome],
    trajectories: list[Trajectory],
    *,
    embedder: Embedder | None = None,
    min_cluster_size: int = 2,
    max_clusters_returned: int = 8,
) -> list[FrictionCluster]:
    """Returns top friction clusters. Pattern matches first, then HDBSCAN residual.

    A trajectory matched by N patterns appears in N pattern clusters. Trajectories
    matched by zero patterns flow into the residual HDBSCAN bucket.
    """
    failed = [o for o in outcomes if not o.success_gameable]
    if not failed:
        return []

    by_key = {(t.persona_id, t.task_id): t for t in trajectories}
    failed_traj = [
        (o, by_key[(o.persona_id, o.task_id)])
        for o in failed
        if (o.persona_id, o.task_id) in by_key
    ]

    # Pattern detection — group trajectories by which pattern they matched.
    pattern_groups: dict[str, list[tuple[Outcome, Trajectory, PatternMatch]]] = defaultdict(list)
    matched_keys: set[tuple[str, str]] = set()
    for outcome, traj in failed_traj:
        matches = detect_all(traj)
        for m in matches:
            pattern_groups[m.pattern_id].append((outcome, traj, m))
            matched_keys.add((outcome.persona_id, outcome.task_id))

    clusters: list[FrictionCluster] = []
    for pattern_id, members in sorted(pattern_groups.items(), key=lambda kv: -len(kv[1])):
        clusters.append(_cluster_from_pattern(pattern_id, members))

    # Residual: failures not matching any pattern.
    residual = [
        (o, t) for (o, t) in failed_traj
        if (o.persona_id, o.task_id) not in matched_keys
    ]
    if len(residual) >= min_cluster_size:
        clusters.extend(_residual_clusters(residual, embedder, min_cluster_size))

    return clusters[:max_clusters_returned]


# =============================================================================
# Pattern → FrictionCluster
# =============================================================================

def _cluster_from_pattern(
    pattern_id: str,
    members: list[tuple[Outcome, Trajectory, PatternMatch]],
) -> FrictionCluster:
    sample_match = members[0][2]
    trajs = [m[1] for m in members]

    # Description: prefer the pattern's specific text. If multiple trajectories
    # match the same pattern but with different evidence (different coords, etc.),
    # surface the variation count.
    n = len(members)
    base = sample_match.description
    description = f"[{pattern_id}] {base}"
    if n > 1:
        # If multiple trajectories matched, append a count
        description = f"[{pattern_id}] {base} (× {n} trajectories)"

    excerpts = _gather_excerpts(members)
    suggested = _gather_dom_targets(pattern_id, members)

    return FrictionCluster(
        id=f"pattern_{pattern_id}",
        description=description,
        n_affected=n,
        example_persona_ids=sorted({m[0].persona_id for m in members})[:5],
        evidence_screenshots=_gather_screenshots(trajs, members),
        suggested_dom_targets=suggested,
        reasoning_excerpts=excerpts,
        suggested_fix=sample_match.suggested_fix,
    )


def _gather_excerpts(
    members: list[tuple[Outcome, Trajectory, PatternMatch]],
    k: int = 3,
) -> list[str]:
    """Reasoning lines from the EVIDENCE STEPS each detector flagged. Specific
    is better than generic — a quote from a step the detector pointed at is far
    more useful than the last reasoning line."""
    out: list[str] = []
    for _, traj, match in members:
        for turn in match.evidence_steps:
            step = next((s for s in traj.steps if s.turn == turn), None)
            if step and step.reasoning:
                out.append(step.reasoning[-1][:240].strip())
                break
        if len(out) >= k:
            break
    return out


def _gather_dom_targets(
    pattern_id: str,
    members: list[tuple[Outcome, Trajectory, PatternMatch]],
) -> list[str]:
    """Concrete DOM hints. For coordinate-based patterns, return specific pixel
    centroids. For non-coordinate patterns, return semantic hints."""
    if pattern_id == "stuck_on_button":
        # Each match's first evidence step has the coords.
        coords = []
        for _, traj, match in members:
            if not match.evidence_steps:
                continue
            step = next((s for s in traj.steps if s.turn == match.evidence_steps[0]), None)
            if step:
                x = step.action.args.get("x")
                y = step.action.args.get("y")
                if isinstance(x, int) and isinstance(y, int):
                    coords.append((x, y))
        if coords:
            cx = sum(c[0] for c in coords) // len(coords)
            cy = sum(c[1] for c in coords) // len(coords)
            return [f"element at viewport ({cx}, {cy})"]

    if pattern_id == "dead_click_storm":
        coords = []
        for _, traj, match in members:
            for turn in match.evidence_steps:
                step = next((s for s in traj.steps if s.turn == turn), None)
                if step:
                    x = step.action.args.get("x")
                    y = step.action.args.get("y")
                    if isinstance(x, int) and isinstance(y, int):
                        coords.append((x, y))
        if coords:
            xs, ys = [c[0] for c in coords], [c[1] for c in coords]
            return [f"region x∈[{min(xs)},{max(xs)}] y∈[{min(ys)},{max(ys)}]"]

    return []


def _gather_screenshots(
    trajs: list[Trajectory],
    members: list[tuple[Outcome, Trajectory, PatternMatch]],
    k: int = 3,
) -> list[str]:
    """Prefer screenshots from the EVIDENCE step of each pattern match."""
    out: list[str] = []
    for _, traj, match in members:
        for turn in match.evidence_steps:
            step = next((s for s in traj.steps if s.turn == turn), None)
            if step and step.observation.screenshot_path:
                out.append(step.observation.screenshot_path)
                break
        if len(out) >= k:
            break
    return out


# =============================================================================
# Residual: HDBSCAN over reasoning of pattern-unmatched failures
# =============================================================================

def _residual_clusters(
    residual: list[tuple[Outcome, Trajectory]],
    embedder: Embedder | None,
    min_cluster_size: int,
) -> list[FrictionCluster]:
    """For trajectories matching no known pattern, fall back to embedding +
    HDBSCAN over reasoning. Output is labeled 'unmatched_*' so the coding
    agent knows these are unstructured signals to investigate."""
    docs = [(o, t, _doc(t)) for o, t in residual if _doc(t)]
    if len(docs) < min_cluster_size:
        return []

    if embedder is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=256, ngram_range=(1, 2), stop_words="english", min_df=1)
        X = np.asarray(vec.fit_transform([d[2] for d in docs]).toarray())  # type: ignore[union-attr]
    else:
        X = embedder.fit_transform([d[2] for d in docs])
    if X.shape[0] < min_cluster_size:
        return []

    labels = _hdbscan_labels(X, min_cluster_size)

    by_label: dict[int, list[tuple[Outcome, Trajectory, str]]] = defaultdict(list)
    for label, doc in zip(labels, docs):
        if label == -1:
            continue
        by_label[label].append(doc)

    clusters: list[FrictionCluster] = []
    for i, (_, members) in enumerate(sorted(by_label.items(), key=lambda kv: -len(kv[1]))):
        outcomes = [m[0] for m in members]
        trajs = [m[1] for m in members]
        reasoning_excerpts = []
        for t in trajs[:3]:
            for s in reversed(t.steps):
                if s.reasoning:
                    reasoning_excerpts.append(s.reasoning[-1][:200].strip())
                    break
        clusters.append(FrictionCluster(
            id=f"unmatched_{i}",
            description=(
                f"Unmatched failure cluster ({len(members)} trajectories) — "
                f"no known pattern detected; investigate excerpts."
            ),
            n_affected=len(members),
            example_persona_ids=sorted({o.persona_id for o in outcomes})[:5],
            evidence_screenshots=[],
            suggested_dom_targets=[],
            reasoning_excerpts=reasoning_excerpts,
        ))
    return clusters


def _hdbscan_labels(X: np.ndarray, min_cluster_size: int) -> np.ndarray:
    try:
        import hdbscan  # type: ignore[import-untyped]
    except ImportError:
        return np.zeros(X.shape[0], dtype=int)
    eff = max(2, min(min_cluster_size, X.shape[0] - 1))
    return hdbscan.HDBSCAN(min_cluster_size=eff, metric="euclidean").fit_predict(X)


def _doc(t: Trajectory) -> str:
    return " ".join(r for s in t.steps for r in s.reasoning)
