"""Command-line interface for jev-triage."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from jev_triage.pipeline import PipelineConfig, TriagePipeline, summarize_output
from jev_triage.rubric import load_rubric

console = Console()


@click.group()
@click.version_option(package_name="jev-triage")
def main() -> None:
    """Active-learning triage with TypeSafe Jev."""


@main.command()
@click.option("--rubric", required=True, type=click.Path(exists=True, path_type=Path), help="YAML rubric file")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path), help="Input JSONL corpus")
@click.option("--output", "output_dir", required=True, type=click.Path(path_type=Path), help="Output directory")
@click.option("--mock/--live", default=None, help="Force mock or live Jev (default: mock without TYPESAFE_API_KEY)")
@click.option("--limit", type=int, default=None, help="Process at most N new examples")
def run(rubric: Path, input_path: Path, output_dir: Path, mock: bool | None, limit: int | None) -> None:
    """Run confidence-gated triage over a JSONL corpus."""
    loaded = load_rubric(rubric)
    pipeline = TriagePipeline(
        PipelineConfig(
            rubric=loaded,
            input_path=input_path,
            output_dir=output_dir,
            mock=mock,
            limit=limit,
        )
    )
    mode = "mock" if mock or (mock is None and not __import__("os").environ.get("TYPESAFE_API_KEY")) else "live"
    console.print(f"[bold]jev-triage[/] rubric={loaded.name!r} mode={mode}")

    stats = pipeline.run()
    summary = summarize_output(output_dir)

    table = Table(title="Triage results")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Processed", str(stats.processed))
    table.add_row("Skipped (resume)", str(stats.skipped))
    table.add_row("Errors", str(stats.errors))
    table.add_row("Accepted (free)", str(summary["accepted"]))
    table.add_row("Teacher queue", str(summary["teacher_queue"]))
    table.add_row("Human queue", str(summary["human_queue"]))
    console.print(table)
    console.print(f"Soft labels logged → {output_dir / 'soft_labels.jsonl'}")


@main.command()
@click.option("--output", "output_dir", required=True, type=click.Path(exists=True, path_type=Path))
def stats(output_dir: Path) -> None:
    """Summarize a prior triage run."""
    s = summarize_output(output_dir)
    table = Table(title=f"Output: {output_dir}")
    for key, val in s.items():
        if isinstance(val, float):
            table.add_row(key, f"{val:.1%}" if "rate" in key else f"{val:.3f}")
        else:
            table.add_row(key, str(val))
    console.print(table)


@main.command("validate-rubric")
@click.option("--rubric", required=True, type=click.Path(exists=True, path_type=Path))
def validate_rubric_cmd(rubric: Path) -> None:
    """Parse a rubric YAML and print question summary."""
    loaded = load_rubric(rubric)
    table = Table(title=f"Rubric: {loaded.name}")
    table.add_column("Question")
    table.add_column("Type")
    table.add_column("Accept ≥")
    table.add_column("Teacher ≥")
    for q in loaded.questions:
        table.add_row(q.name, q.kind, f"{q.accept_confidence:.2f}", f"{q.teacher_confidence:.2f}")
    console.print(table)
