"""Jev client wrapper with mock mode for offline development."""

from __future__ import annotations

import hashlib
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from typesafe_sdk import (
    Choice,
    ChoiceAnswer,
    Noul,
    NoulAnswer,
    Question,
    Score,
    ScoreAnswer,
    SystemOneResponse,
    TypeSafeClient,
    Usage,
)

from jev_triage.rubric import Rubric


def _state_text(state: Any) -> str:
    if isinstance(state, str):
        return state
    if isinstance(state, dict):
        return " ".join(str(v) for v in state.values())
    if isinstance(state, list):
        return " ".join(str(v) for v in state)
    return str(state)


class JevEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        state: Any,
        questions: dict[str, Question],
        *,
        model: str = "jev-latest",
    ) -> SystemOneResponse:
        ...


class LiveJevEvaluator(JevEvaluator):
    def __init__(self, api_key: str | None = None) -> None:
        self._client = TypeSafeClient(api_key=api_key)

    def evaluate(
        self,
        state: Any,
        questions: dict[str, Question],
        *,
        model: str = "jev-latest",
    ) -> SystemOneResponse:
        return self._client.system_one(state=state, questions=questions, model=model)


class MockJevEvaluator(JevEvaluator):
    """Heuristic mock for tests and demos without an API key."""

    _URGENT = re.compile(
        r"\b(asap|urgent|immediately|right away|three days|charged twice|duplicate|refund)\b",
        re.I,
    )
    _BILLING = re.compile(r"\b(charge|charged|refund|billing|invoice|payment|subscription|duplicate)\b", re.I)
    _TECH = re.compile(r"\b(error|bug|fail|broken|500|integration|connect|deploy|checkout)\b", re.I)
    _SALES = re.compile(r"\b(pricing|enterprise|plan|seats|upgrade|demo)\b", re.I)

    def _seed(self, text: str, salt: str) -> float:
        h = hashlib.sha256(f"{salt}:{text}".encode()).hexdigest()
        return int(h[:8], 16) / 0xFFFFFFFF

    def evaluate(
        self,
        state: Any,
        questions: dict[str, Question],
        *,
        model: str = "jev-latest",
    ) -> SystemOneResponse:
        text = _state_text(state)
        answers: dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer] = {}

        lower = text.lower()
        for name, q in questions.items():
            if isinstance(q, Noul):
                base = 0.88  # default: plausible yes for quality gates
                if name in ("transcript_valid", "label_plausible"):
                    if "garbled" in lower or "hallucin" in lower:
                        base = 0.06
                    elif len(text.strip()) < 12:
                        base = 0.20
                    else:
                        base = 0.96
                elif name == "is_ambiguous":
                    base = 0.15
                    if "ambiguous" in lower or "might be" in lower or " or maybe " in lower:
                        base = 0.78
                elif self._URGENT.search(text):
                    base = 0.92
                noise = (self._seed(text, name) - 0.5) * 0.06
                prob = max(0.01, min(0.99, base + noise))
                answers[name] = NoulAnswer(noul=prob)
            elif isinstance(q, Choice):
                labels = list(q.criteria.keys())
                scores = {}
                for label in labels:
                    s = 0.05 + self._seed(text, f"{name}:{label}") * 0.08
                    if label == "billing" and self._BILLING.search(text):
                        s += 2.0
                    if label == "technical" and self._TECH.search(text):
                        s += 2.0
                    if label == "sales" and self._SALES.search(text):
                        s += 2.0
                    if label == "other" and len(text.strip()) < 20:
                        s += 1.2
                    elif label == "other":
                        s += 0.15
                    scores[label] = s
                total = sum(scores.values()) or 1.0
                probs = {k: v / total for k, v in scores.items()}
                winner = max(probs, key=probs.get)  # type: ignore[arg-type]
                answers[name] = ChoiceAnswer(
                    choice=winner,
                    confidence=max(probs.values()),
                    probabilities=probs,
                )
            elif isinstance(q, Score):
                n = len(q.criteria)
                dist: dict[int, float] = {}
                center = 0
                if self._URGENT.search(text):
                    center = min(n - 1, 2)
                elif len(text.strip()) > 40:
                    center = 1
                for i in range(n):
                    dist[i] = 0.03 + (0.85 if i == center else 0.04) + self._seed(text, f"{name}:{i}") * 0.03
                total = sum(dist.values())
                probs = {k: v / total for k, v in dist.items()}
                score = sum(k * p for k, p in probs.items())
                legend = {i: q.criteria[i] for i in range(n)}
                answers[name] = ScoreAnswer(
                    score=score,
                    confidence=probs.get(center, 0.5),
                    probabilities=probs,
                    legend=legend,
                )

        return SystemOneResponse(
            model=model,
            usage=Usage(input_tokens=len(text.split()), output_tokens=0),
            answers=answers,
        )


def make_evaluator(*, mock: bool | None = None) -> JevEvaluator:
    if mock is True:
        return MockJevEvaluator()
    if mock is False:
        return LiveJevEvaluator()
    # Auto: mock when no API key
    if os.environ.get("TYPESAFE_API_KEY"):
        return LiveJevEvaluator()
    return MockJevEvaluator()


def evaluate_rubric(
    evaluator: JevEvaluator,
    rubric: Rubric,
    state: Any,
) -> dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer]:
    response = evaluator.evaluate(
        state=state,
        questions=rubric.to_jev_questions(),
        model=rubric.model,
    )
    return response.answers
