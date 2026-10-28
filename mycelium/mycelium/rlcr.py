"""P2: RLCR (Reinforcement Learning with Calibration Rewards), GRPO-style.

Reward = correctness minus a Brier penalty on the stated confidence, following
"Beyond Binary Rewards: Training LMs to Reason About Their Uncertainty" (arXiv 2507.16806).
Groups where every sample earns the same reward carry no learning signal and are
dropped (dynamic sampling, as in DAPO).
"""

from __future__ import annotations

import numpy as np

from mycelium.evals import metrics
from mycelium.evals.judges import judge
from mycelium.models.base import RLCRSample, TrainableBackend
from mycelium.types import Problem


def rlcr_reward(correct: bool, confidence: float) -> float:
    y = float(correct)
    return y - (confidence - y) ** 2


def group_advantages(rewards: list[float], eps: float = 1e-6) -> np.ndarray:
    r = np.asarray(rewards, dtype=float)
    return (r - r.mean()) / (r.std() + eps)


def learnable_problems(
    model: TrainableBackend, problems: list[Problem], *, k: int = 4, low: float = 0.2, high: float = 0.8, max_loops: int = 4
) -> list[Problem]:
    """Keep problems the model gets right sometimes (most learning signal), plus every
    unanswerable one, since those teach the model to lower its confidence."""
    kept = []
    for problem in problems:
        if not problem.answerable:
            kept.append(problem)
            continue
        rate = np.mean([judge(problem, model.answer(problem, max_loops=max_loops, sample=100 + s)) for s in range(k)])
        if low <= rate <= high:
            kept.append(problem)
    return kept


def run_rlcr(
    model: TrainableBackend,
    problems: list[Problem],
    *,
    steps: int = 10,
    batch_size: int = 32,
    group_size: int = 8,
    max_loops: int = 4,
    seed: int = 0,
) -> list[dict]:
    rng = np.random.default_rng(seed)
    history = []
    for step in range(steps):
        batch = [problems[i] for i in rng.choice(len(problems), size=min(batch_size, len(problems)), replace=False)]
        samples: list[RLCRSample] = []
        kept_groups = 0
        for problem in batch:
            group = []
            for g in range(group_size):
                answer = model.answer(problem, max_loops=max_loops, sample=1000 * (step + 1) + g)
                correct = judge(problem, answer)
                group.append((answer, correct, rlcr_reward(correct, answer.confidence)))
            rewards = [r for _, _, r in group]
            if np.std(rewards) < 1e-9:
                continue
            kept_groups += 1
            for (answer, correct, reward), advantage in zip(group, group_advantages(rewards), strict=True):
                samples.append(RLCRSample(problem, answer, correct, reward, float(advantage)))
        if samples:
            model.learn_rlcr(samples)
        confidence = [s.answer.confidence for s in samples]
        correct = [s.correct for s in samples]
        history.append(
            {
                "step": step,
                "groups_kept": kept_groups,
                "mean_reward": float(np.mean([s.reward for s in samples])) if samples else float("nan"),
                "ece": metrics.expected_calibration_error(confidence, correct) if samples else float("nan"),
            }
        )
    return history
