# Example: Support ticket triage

## Story

You have 500k support messages with **no labels**. You need categories and urgency for training a router model, but you cannot afford an LLM judge on every row.

## Goal

Use Jev to **accept** obvious cases, **queue** ambiguous ones for a frontier model, and **queue** edge cases for humans — while logging soft labels for every row.

## Files

- `corpus.jsonl` — 10 toy tickets (stand-in for your export)
- `rubric.yaml` — department, urgency, validity, ambiguity questions
- `SUCCESS.md` — what good output looks like

## Run

```bash
jev-triage run \
  --rubric examples/support-tickets/rubric.yaml \
  --input examples/support-tickets/corpus.jsonl \
  --output .output/support-tickets
```

Live Jev:

```bash
export TYPESAFE_API_KEY="sk-..."
jev-triage run ...   # omit --mock
```

## After the run

1. Inspect `human_queue.jsonl` — should include deliberately ambiguous rows (e.g. `t005`, `t010` in the toy set).
2. Process `teacher_queue.jsonl` with your prompt template; write labels back to your DB.
3. Merge into training set: accepted rows + relabeled teacher/human rows.
4. **Do not** ship a model trained only on accepted Jev labels without eval on held-out **human** labels.
