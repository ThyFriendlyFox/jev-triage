# Goals — jev-triage

## What this repo is for

**jev-triage** is a batch pipeline that uses [TypeSafe Jev](https://typesafe.ai) to **split unlabeled (or weakly labeled) data into three queues** based on calibrated confidence — so you spend human and frontier-model budget only where it changes the outcome.

It is **not** a trainer, not a hosting stack, and not a replacement for ground-truth labels. It is the **routing layer** between raw corpus and expensive labeling.

## Primary goals

1. **Reduce labeling cost** — Auto-accept high-confidence Jev judgments; send middling cases to a teacher; send low-confidence or boundary cases to humans.
2. **Log soft labels** — Every example gets full probability distributions in `soft_labels.jsonl` for optional local distillation (bootstrap path).
3. **Run at corpus scale** — Resumable JSONL in/out; one Jev call per row (many questions in parallel per call).
4. **Stay honest about Jev** — Jev filters and routes; **real outcome labels** (human, emulator, shop cost, etc.) remain what you train on.

## What success looks like

You have used **jev-triage successfully** when all of the following are true:

| # | Success criterion | How you verify |
|---|-------------------|----------------|
| 1 | You defined a **rubric** (YAML) whose questions match decisions you would otherwise ask an LLM judge | `jev-triage validate-rubric --rubric …` |
| 2 | You ran the pipeline over your corpus (live Jev in production; mock only for CI/local plumbing) | `accepted.jsonl` + queues non-empty or intentionally empty with documented thresholds |
| 3 | **Most rows** landed in `accepted.jsonl` or `teacher_queue.jsonl`, not `human_queue.jsonl` — unless your domain is inherently ambiguous | `jev-triage stats --output …` |
| 4 | You processed **teacher** and **human** queues and obtained **ground-truth** (or authoritative) labels for those rows | Your labeling tool / spreadsheet / DB |
| 5 | Training data = `accepted` (Jev labels you trust at threshold) **plus** teacher/human-labeled rows — **not** Jev alone for the whole set if quality matters | Dataset manifest |
| 6 | (Optional bootstrap) You logged `soft_labels.jsonl` and later compared a **local student** vs Jev on a **held-out set with real outcomes** | ECE / accuracy on real labels |
| 7 | You can **re-run** after a crash without duplicating work | Second run shows `Skipped (resume) > 0` |

### Anti-goals (this repo does not claim success if…)

- You trained a model **only** on Jev argmax labels with no human/teacher/outcome validation.
- You expect Jev to label **audio/acoustic** properties without a transcript or caption in `state`.
- You use mock mode output as production curation/triage decisions.

## Typical placement in a training pipeline

```
Raw corpus
    → [jev-curate] optional: drop garbage / mislabeled rows
    → [jev-triage]  route: accept | teacher | human
    → Label teacher + human queues (expensive)
    → Train on accepted + relabeled rows; targets = real outcomes
    → (Optional) distill from soft_labels.jsonl to a local head
```

## Mock vs live Jev

| Mode | Purpose |
|------|---------|
| **Live** (`TYPESAFE_API_KEY` set, no `--mock`) | Production triage; thresholds and routes are meaningful |
| **Mock** (`--mock` or no key in jev-triage default) | Learn the CLI, CI tests, dry-run pipeline wiring — **not** for publishing dataset decisions |

See [examples/README.md](examples/README.md) for worked scenarios and expected queue shapes.
