"""Confidence-gated routing: accept, teacher, or human."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from typesafe_sdk import ChoiceAnswer, NoulAnswer, ScoreAnswer

from jev_triage.rubric import QuestionSpec, Rubric
from jev_triage.soft_labels import answer_confidence, serialize_answer


class Route(str, Enum):
    ACCEPT = "accept"      # high confidence — take Jev label free
    TEACHER = "teacher"    # middling — send to expensive teacher
    HUMAN = "human"        # low / near boundary — human review


@dataclass(frozen=True)
class QuestionVerdict:
    name: str
    route: Route
    confidence: float
    answer: dict[str, Any]


@dataclass(frozen=True)
class TriageResult:
    example_id: str
    overall_route: Route
    question_verdicts: tuple[QuestionVerdict, ...]
    answers: dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.example_id,
            "route": self.overall_route.value,
            "questions": {
                v.name: {
                    "route": v.route.value,
                    "confidence": v.confidence,
                    "answer": v.answer,
                }
                for v in self.question_verdicts
            },
        }


def _route_question(
    spec: QuestionSpec,
    answer: NoulAnswer | ChoiceAnswer | ScoreAnswer,
) -> tuple[Route, float]:
    conf = answer_confidence(answer)

    # Near decision boundary on binary / choice → human even if confidence is ok
    if isinstance(answer, NoulAnswer) and 0.45 <= answer.noul <= 0.55:
        return Route.HUMAN, conf
    if isinstance(answer, ChoiceAnswer):
        probs = sorted(answer.probabilities.values(), reverse=True)
        if len(probs) >= 2 and (probs[0] - probs[1]) < 0.15:
            return Route.HUMAN, conf

    if conf >= spec.accept_confidence:
        return Route.ACCEPT, conf
    if conf >= spec.teacher_confidence:
        return Route.TEACHER, conf
    return Route.HUMAN, conf


_ROUTE_PRIORITY = {Route.HUMAN: 0, Route.TEACHER: 1, Route.ACCEPT: 2}


def triage_example(
    example_id: str,
    rubric: Rubric,
    answers: dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer],
) -> TriageResult:
    spec_by_name = {q.name: q for q in rubric.questions}
    verdicts: list[QuestionVerdict] = []
    worst = Route.ACCEPT

    for q in rubric.questions:
        ans = answers[q.name]
        route, conf = _route_question(spec_by_name[q.name], ans)
        if _ROUTE_PRIORITY[route] < _ROUTE_PRIORITY[worst]:
            worst = route
        verdicts.append(
            QuestionVerdict(
                name=q.name,
                route=route,
                confidence=conf,
                answer=serialize_answer(ans),
            )
        )

    return TriageResult(
        example_id=example_id,
        overall_route=worst,
        question_verdicts=tuple(verdicts),
        answers=answers,
    )
