# Example: Weak existing labels

## Story

Your corpus already has a `label` field from a cheap classifier or vendor. You want Jev to decide **trust label as-is**, **re-label with teacher**, or **human audit** — not to blindly train on bad labels.

## Goal

Use Noul/Choice questions that compare **content vs assigned label**; route disagreements and low confidence to teacher/human.

## Run

```bash
jev-triage run \
  --rubric examples/weak-labels/rubric.yaml \
  --input examples/weak-labels/corpus.jsonl \
  --output .output/weak-labels
```

State sent to Jev includes `text` and `label` (see pipeline: extra fields are attached when `state_field` is text).

## Success

See [SUCCESS.md](SUCCESS.md).
