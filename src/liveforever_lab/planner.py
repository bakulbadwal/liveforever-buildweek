"""Create an auditable experiment scaffold from deterministic analysis."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any


def build_plan(analysis: dict[str, Any], *, seed: int = 56) -> dict[str, Any]:
    """Build a balanced 14-day replication plan without prescribing treatment."""
    start = date.fromisoformat(analysis["dataset"]["end_date"]) + timedelta(days=1)
    conditions = ["Cutoff by 2 PM"] * 7 + ["Usual timing"] * 7
    random.Random(seed).shuffle(conditions)
    schedule = [
        {"date": (start + timedelta(days=index)).isoformat(), "condition": condition}
        for index, condition in enumerate(conditions)
    ]
    primary = analysis["primary_effect"]
    return {
        "title": "14-day caffeine timing replication",
        "status": "Ready to review",
        "hypothesis": analysis["question"],
        "design": "Balanced randomized daily conditions with next-day outcome measurement.",
        "primary_outcome": "Next-day nightly HRV (ms)",
        "secondary_outcomes": ["Sleep duration", "Resting heart rate", "Self-rated energy"],
        "observed_signal": {
            "effect": primary["effect"], "ci_low": primary["ci_low"],
            "ci_high": primary["ci_high"], "paired_days": primary["n_on"] + primary["n_off"],
        },
        "schedule": schedule,
        "controls": [
            "Keep total daily caffeine within the participant's usual range.",
            "Record alcohol, illness, travel, and unusually hard training.",
            "Use the same wearable and nightly measurement method.",
            "Do not change medication or supplements for this experiment.",
        ],
        "decision_rule": "Treat the result as a replication candidate only if both groups reach seven observed nights and the uncertainty interval excludes zero; otherwise label it inconclusive.",
        "stop_conditions": [
            "Stop and seek appropriate professional care for severe or concerning symptoms.",
            "Pause when illness, travel, or device failure makes the comparison unreliable.",
        ],
        "model_instruction": "GPT-5.6 may explain this plan and ask clarifying questions, but it must not change calculated values or convert association into medical advice.",
    }

