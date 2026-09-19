"""Unit tests for triage routing logic."""

from typesafe_sdk import ChoiceAnswer, NoulAnswer, ScoreAnswer

from jev_triage.rubric import QuestionSpec, Rubric
from jev_triage.soft_labels import noul_confidence, serialize_answer
from jev_triage.triage import Route, triage_example


def _minimal_rubric() -> Rubric:
    return Rubric(
        name="test",
        state_field="text",
        questions=(
            QuestionSpec(name="valid", kind="noul", instructions="valid?", accept_confidence=0.85),
            QuestionSpec(name="dept", kind="choice", instructions="dept?", accept_confidence=0.85),
        ),
    )


def test_noul_confidence_extremes():
    assert noul_confidence(0.99) > 0.9
    assert noul_confidence(0.51) < 0.1


def test_high_confidence_routes_to_accept():
    rubric = _minimal_rubric()
    answers = {
        "valid": NoulAnswer(noul=0.97),
        "dept": ChoiceAnswer(
            choice="billing",
            confidence=0.95,
            probabilities={"billing": 0.95, "other": 0.05},
        ),
    }
    result = triage_example("x1", rubric, answers)
    assert result.overall_route == Route.ACCEPT


def test_boundary_noul_routes_to_human():
    rubric = _minimal_rubric()
    answers = {
        "valid": NoulAnswer(noul=0.50),
        "dept": ChoiceAnswer(
            choice="billing",
            confidence=0.95,
            probabilities={"billing": 0.95, "other": 0.05},
        ),
    }
    result = triage_example("x2", rubric, answers)
    assert result.overall_route == Route.HUMAN


def test_close_choice_routes_to_human():
    rubric = _minimal_rubric()
    answers = {
        "valid": NoulAnswer(noul=0.97),
        "dept": ChoiceAnswer(
            choice="billing",
            confidence=0.52,
            probabilities={"billing": 0.52, "technical": 0.48},
        ),
    }
    result = triage_example("x3", rubric, answers)
    assert result.overall_route == Route.HUMAN


def test_middling_confidence_routes_to_teacher():
    rubric = Rubric(
        name="test",
        state_field="text",
        questions=(QuestionSpec(name="valid", kind="noul", instructions="?", accept_confidence=0.90, teacher_confidence=0.50),),
    )
    answers = {"valid": NoulAnswer(noul=0.72)}  # conf ≈ 0.44 → human; use 0.78 → conf 0.56
    answers = {"valid": NoulAnswer(noul=0.78)}
    result = triage_example("x4", rubric, answers)
    assert result.overall_route == Route.TEACHER


def test_serialize_preserves_distribution():
    ans = ChoiceAnswer(
        choice="a",
        confidence=0.7,
        probabilities={"a": 0.7, "b": 0.3},
    )
    out = serialize_answer(ans)
    assert out["soft_target"] == {"a": 0.7, "b": 0.3}


def test_score_serialization():
    ans = ScoreAnswer(
        score=1.5,
        confidence=0.8,
        probabilities={0: 0.1, 1: 0.4, 2: 0.5},
        legend={0: "low", 1: "mid", 2: "high"},
    )
    out = serialize_answer(ans)
    assert out["type"] == "score"
    assert "2" in out["soft_target"]
