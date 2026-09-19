"""Integration tests for the resumable pipeline."""

import json
from pathlib import Path

from jev_triage.pipeline import PipelineConfig, TriagePipeline, summarize_output
from jev_triage.rubric import load_rubric


def test_pipeline_mock_run(tmp_path: Path):
    rubric_path = Path(__file__).resolve().parents[1] / "examples" / "rubric.yaml"
    input_path = tmp_path / "in.jsonl"
    input_path.write_text(
        json.dumps({"id": "a", "text": "charged twice please refund ASAP"}) + "\n"
        + json.dumps({"id": "b", "text": "garbled hallucinated silence music"}) + "\n"
    )
    out = tmp_path / "out"
    pipeline = TriagePipeline(
        PipelineConfig(
            rubric=load_rubric(rubric_path),
            input_path=input_path,
            output_dir=out,
            mock=True,
        )
    )
    stats = pipeline.run()
    assert stats.processed == 2
    summary = summarize_output(out)
    assert summary["total_routed"] == 2
    assert (out / "soft_labels.jsonl").exists()


def test_pipeline_resumes(tmp_path: Path):
    rubric_path = Path(__file__).resolve().parents[1] / "examples" / "rubric.yaml"
    input_path = tmp_path / "in.jsonl"
    input_path.write_text(json.dumps({"id": "only", "text": "integration error 500"}) + "\n")
    out = tmp_path / "out"
    cfg = PipelineConfig(rubric=load_rubric(rubric_path), input_path=input_path, output_dir=out, mock=True)
    p1 = TriagePipeline(cfg)
    p1.run()
    p2 = TriagePipeline(cfg)
    stats = p2.run()
    assert stats.skipped == 1
    assert stats.processed == 0
