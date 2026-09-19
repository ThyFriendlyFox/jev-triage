"""Load labeling rubrics (Jev questions + triage thresholds) from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from typesafe_sdk import Choice, Noul, Question, Score


@dataclass(frozen=True)
class QuestionSpec:
    name: str
    kind: str  # noul | choice | score
    instructions: str
    criteria: dict[str, str | None] | list[str] | None = None
    accept_confidence: float = 0.85
    teacher_confidence: float = 0.50
    # Below teacher_confidence → human review


@dataclass(frozen=True)
class Rubric:
    name: str
    state_field: str
    questions: tuple[QuestionSpec, ...]
    model: str = "jev-latest"

    def to_jev_questions(self) -> dict[str, Question]:
        out: dict[str, Question] = {}
        for q in self.questions:
            if q.kind == "noul":
                out[q.name] = Noul(instructions=q.instructions)
            elif q.kind == "choice":
                criteria = q.criteria
                if not isinstance(criteria, dict):
                    raise ValueError(f"Choice question {q.name!r} requires dict criteria")
                out[q.name] = Choice(instructions=q.instructions, criteria=criteria)
            elif q.kind == "score":
                criteria = q.criteria
                if not isinstance(criteria, list):
                    raise ValueError(f"Score question {q.name!r} requires list criteria")
                out[q.name] = Score(instructions=q.instructions, criteria=criteria)
            else:
                raise ValueError(f"Unknown question kind: {q.kind!r}")
        return out


def _parse_question(raw: dict[str, Any]) -> QuestionSpec:
    return QuestionSpec(
        name=raw["name"],
        kind=raw["type"],
        instructions=raw["instructions"],
        criteria=raw.get("criteria"),
        accept_confidence=float(raw.get("accept_confidence", 0.85)),
        teacher_confidence=float(raw.get("teacher_confidence", 0.50)),
    )


def load_rubric(path: str | Path) -> Rubric:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError("Rubric YAML must be a mapping")

    questions = tuple(_parse_question(q) for q in data.get("questions", []))
    if not questions:
        raise ValueError("Rubric must define at least one question")

    return Rubric(
        name=data.get("name", Path(path).stem),
        state_field=data.get("state_field", "text"),
        questions=questions,
        model=data.get("model", "jev-latest"),
    )
