"""Serialize Jev probability distributions for distillation training."""

from __future__ import annotations

from typing import Any

from typesafe_sdk import ChoiceAnswer, NoulAnswer, ScoreAnswer


def noul_confidence(probability: float) -> float:
    """Noul has no confidence field; distance from 0.5 is the belief strength."""
    return abs(probability - 0.5) * 2.0


def answer_confidence(answer: NoulAnswer | ChoiceAnswer | ScoreAnswer) -> float:
    if isinstance(answer, NoulAnswer):
        return noul_confidence(answer.noul)
    return answer.confidence


def serialize_answer(answer: NoulAnswer | ChoiceAnswer | ScoreAnswer) -> dict[str, Any]:
    if isinstance(answer, NoulAnswer):
        return {
            "type": "noul",
            "probability": answer.noul,
            "confidence": noul_confidence(answer.noul),
            "soft_target": {"yes": answer.noul, "no": 1.0 - answer.noul},
        }
    if isinstance(answer, ChoiceAnswer):
        return {
            "type": "choice",
            "choice": answer.choice,
            "confidence": answer.confidence,
            "probabilities": dict(answer.probabilities),
            "soft_target": dict(answer.probabilities),
        }
    # ScoreAnswer
    return {
        "type": "score",
        "score": answer.score,
        "confidence": answer.confidence,
        "probabilities": {str(k): v for k, v in answer.probabilities.items()},
        "legend": {str(k): v for k, v in answer.legend.items()},
        "soft_target": {str(k): v for k, v in answer.probabilities.items()},
    }


def training_record(
    example_id: str,
    state: Any,
    answers: dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer],
    route: str,
) -> dict[str, Any]:
    """One JSONL row suitable for KL / soft-label distillation."""
    return {
        "id": example_id,
        "state": state,
        "route": route,
        "labels": {name: serialize_answer(ans) for name, ans in answers.items()},
    }
