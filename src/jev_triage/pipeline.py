"""Resumable batch triage over JSONL corpora."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from jev_triage.client import JevEvaluator, evaluate_rubric, make_evaluator
from jev_triage.rubric import Rubric
from jev_triage.soft_labels import training_record
from jev_triage.triage import Route, TriageResult, triage_example


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON") from exc


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_done_ids(*paths: Path) -> set[str]:
    done: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for row in read_jsonl(path):
            if "id" in row:
                done.add(str(row["id"]))
    return done


@dataclass
class PipelineStats:
    processed: int = 0
    skipped: int = 0
    routes: Counter = field(default_factory=Counter)
    errors: int = 0


@dataclass
class PipelineConfig:
    rubric: Rubric
    input_path: Path
    output_dir: Path
    mock: bool | None = None
    limit: int | None = None


def _example_id(row: dict[str, Any], index: int) -> str:
    return str(row.get("id", index))


def _extract_state(row: dict[str, Any], rubric: Rubric) -> Any:
    if "state" in row:
        return row["state"]
    if rubric.state_field in row:
        primary = row[rubric.state_field]
        extra = {k: v for k, v in row.items() if k not in ("id", "meta", rubric.state_field)}
        if extra and isinstance(primary, str):
            return {rubric.state_field: primary, **extra}
        return primary
    return {k: v for k, v in row.items() if k not in ("id", "meta")}


class TriagePipeline:
    def __init__(self, config: PipelineConfig, evaluator: JevEvaluator | None = None) -> None:
        self.config = config
        self.evaluator = evaluator or make_evaluator(mock=config.mock)
        self.output_dir = config.output_dir
        self.accept_path = self.output_dir / "accepted.jsonl"
        self.teacher_path = self.output_dir / "teacher_queue.jsonl"
        self.human_path = self.output_dir / "human_queue.jsonl"
        self.soft_labels_path = self.output_dir / "soft_labels.jsonl"
        self.errors_path = self.output_dir / "errors.jsonl"

    def run(self) -> PipelineStats:
        stats = PipelineStats()
        done = load_done_ids(
            self.accept_path,
            self.teacher_path,
            self.human_path,
            self.errors_path,
        )

        for index, row in enumerate(read_jsonl(self.config.input_path)):
            if self.config.limit is not None and stats.processed >= self.config.limit:
                break

            ex_id = _example_id(row, index)
            if ex_id in done:
                stats.skipped += 1
                continue

            try:
                state = _extract_state(row, self.config.rubric)
                answers = evaluate_rubric(self.evaluator, self.config.rubric, state)
                result = triage_example(ex_id, self.config.rubric, answers)
                self._write_result(row, state, result)
                stats.processed += 1
                stats.routes[result.overall_route.value] += 1
            except Exception as exc:  # noqa: BLE001 — log and continue batch
                append_jsonl(
                    self.errors_path,
                    {"id": ex_id, "error": str(exc), "row": row},
                )
                stats.errors += 1

        return stats

    def _write_result(self, row: dict[str, Any], state: Any, result: TriageResult) -> None:
        payload = {
            **result.to_dict(),
            "source": row,
            "state": state,
        }
        route_paths = {
            Route.ACCEPT: self.accept_path,
            Route.TEACHER: self.teacher_path,
            Route.HUMAN: self.human_path,
        }
        append_jsonl(route_paths[result.overall_route], payload)
        append_jsonl(
            self.soft_labels_path,
            training_record(result.example_id, state, result.answers, result.overall_route.value),
        )


def summarize_output(output_dir: Path) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for name in ("accepted", "teacher_queue", "human_queue", "errors", "soft_labels"):
        path = output_dir / f"{name}.jsonl"
        if path.exists():
            counts[name] = sum(1 for _ in read_jsonl(path))
        else:
            counts[name] = 0
    total = counts["accepted"] + counts["teacher_queue"] + counts["human_queue"]
    return {
        **counts,
        "total_routed": total,
        "accept_rate": counts["accepted"] / total if total else 0.0,
        "teacher_rate": counts["teacher_queue"] / total if total else 0.0,
        "human_rate": counts["human_queue"] / total if total else 0.0,
    }
