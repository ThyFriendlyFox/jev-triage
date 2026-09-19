# jev-triage

**Active-learning triage pipeline using [TypeSafe Jev](https://typesafe.ai)** — route unlabeled data by calibrated confidence, log full probability distributions for local distillation, and spend expensive labeling budget only where it changes the outcome.

This repo implements **pattern #3** from the Jev-for-training playbook:

| Confidence | Route | Cost |
|------------|-------|------|
| High | Accept Jev label | ~$0.042/MTok input |
| Middling | Queue for expensive teacher (VLM, audio LM, frontier LLM) | Your teacher cost |
| Low / near boundary | Queue for human review | Your annotator cost |

It also logs **soft labels** (full distributions, not argmax) to `soft_labels.jsonl` for the bootstrap path: train a local head on logged pairs, measure against real outcome labels, cut the cord when the local model wins.

## Why Jev here (and not as your teacher)

Jev is a **System One** model: typed questions in, calibrated probabilities out, no text generation. That makes it ~400× cheaper than an LLM judge at corpus scale and fast enough to filter millions of examples.

**Use Jev to decide what enters the training set. Do not distill Jev as your teacher of record** — its ~68% ceiling compounds errors. Real outcome labels (shop costs, emulator pass/fail, human adjudication) remain the training targets.

## Quick start

```bash
pip install -e ".[dev]"
export TYPESAFE_API_KEY="sk-..."   # optional; omit to run in mock mode

jev-triage run \
  --rubric examples/rubric.yaml \
  --input examples/corpus.jsonl \
  --output .output/run1
```

Without an API key, the pipeline runs in **mock mode** (deterministic heuristics) so you can develop and test offline.

### Outputs

| File | Contents |
|------|----------|
| `accepted.jsonl` | High-confidence examples — Jev labels accepted free |
| `teacher_queue.jsonl` | Middling confidence — send to your expensive teacher |
| `human_queue.jsonl` | Low confidence or near decision boundary |
| `soft_labels.jsonl` | Full probability distributions for distillation |
| `errors.jsonl` | Failed rows (pipeline is resumable; re-run skips completed ids) |

```bash
jev-triage stats --output .output/run1
jev-triage validate-rubric --rubric examples/rubric.yaml
```

## Rubric format

Questions map directly to Jev primitives (`noul`, `choice`, `score`). Per-question thresholds control routing:

```yaml
name: support_ticket_curation
state_field: text
model: jev-latest

questions:
  - name: transcript_valid
    type: noul
    instructions: Does this read like a coherent message, not garbled output?
    accept_confidence: 0.80
    teacher_confidence: 0.55

  - name: department
    type: choice
    instructions: Which team should handle this?
    criteria:
      billing: Payment or refund issues
      technical: Bugs or outages
      other: Anything else
    accept_confidence: 0.85
    teacher_confidence: 0.55
```

- **Noul** has no native confidence field; this pipeline uses `|p − 0.5| × 2` as belief strength.
- **Choice / Score** use Jev's returned `confidence`.
- Examples with Noul near 0.5 or Choice top-two probabilities within 0.15 route to **human** regardless of confidence.

## Soft-label distillation (next step)

Each row in `soft_labels.jsonl` includes:

```json
{
  "id": "t001",
  "state": "...",
  "route": "accept",
  "labels": {
    "department": {
      "type": "choice",
      "choice": "billing",
      "confidence": 0.94,
      "probabilities": {"billing": 0.94, "technical": 0.04, "other": 0.02},
      "soft_target": {"billing": 0.94, "technical": 0.04, "other": 0.02}
    }
  }
}
```

Train a local student with:

- **Choice** → KL divergence against `soft_target`
- **Noul** → BCE against `probability`
- **Score** → ordinal / distribution loss against level probabilities

Compare reliability (ECE) and accuracy against **real outcome labels** on a held-out set. When the local head wins, stop calling Jev for that question.

## Audio / multimodal path

Jev is text-only. For audio corpora:

```
audio → Whisper → transcript → Jev triage → soft labels
                     ↓
         student: audio → encoder → heads (never sees transcript at inference)
```

Use Jev for **lexical** questions on transcripts. For **acoustic** questions (prosody, noise, overlap), label a small expensive set with an audio LM or humans and multi-task train separate heads — transcript labels cannot teach acoustics.

Validate captions against source on a sample before batch runs; Jev judges only what you put in `state`.

## Cost sketch

| Step | 1M × 500-token examples |
|------|---------------------------|
| Jev filter pass | ~$21 |
| LLM judge (400×) | ~$8,400 |
| Jev on 1M × 30s audio transcripts (~100 tok) | ~$4.20 |

Whisper transcription dominates wall time for audio, not Jev.

## Architecture

```
corpus.jsonl
    │
    ▼
┌─────────────┐     ┌──────────────────────────────────────┐
│ Jev evaluate│────▶│ Per-question confidence + distributions │
└─────────────┘     └──────────────────────────────────────┘
    │
    ├── accept ──────▶ accepted.jsonl (+ soft_labels.jsonl)
    ├── teacher ─────▶ teacher_queue.jsonl
    └── human ───────▶ human_queue.jsonl
```

Pipeline properties:

- **Resumable** — skips ids already present in any output file
- **Concurrent-ready** — shard input JSONL; merge outputs (ids are unique keys)
- **Mock mode** — develop without API access

## The other three patterns (not implemented here)

This repo focuses on active-learning triage. Sibling repos / extensions:

1. **Data curation** — drop failed Noul gates (`transcript_valid`, `label_plausible`, duplicate-in-substance) before training
2. **Soft labels only** — skip routing; log distributions for every example
4. **Caption-then-judge** — VLM describes media → Jev judges description (validate captions first)

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
