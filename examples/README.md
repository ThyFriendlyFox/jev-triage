# Examples — jev-triage

Each example is a **mini playbook**: input corpus, rubric, command, and **what a good result looks like**.

Run any example from the repo root:

```bash
pip install -e ".[dev]"
export TYPESAFE_API_KEY="sk-..."   # use live Jev for real runs

jev-triage run \
  --rubric examples/<scenario>/rubric.yaml \
  --input examples/<scenario>/corpus.jsonl \
  --output .output/<scenario>
```

Use `--mock` only to verify the pipeline runs in CI or without an API key.

---

## Example index

| Folder | Scenario | You learn |
|--------|----------|-----------|
| [support-tickets](support-tickets/) | Support ticket routing + frustration/urgency | Multi-question fan-out; accept vs teacher vs human |
| [audio-transcripts](audio-transcripts/) | Post-Whisper transcript labeling (lexical only) | Text-only Jev on ASR output; gating hallucinations |
| [weak-labels](weak-labels/) | Noisy vendor labels; when to re-label | Triage when existing `label` may be wrong |

---

## Shared JSONL conventions

```json
{"id": "unique-string", "text": "…", "label": "optional-existing-label"}
```

- **`id`** — Required for resume; must be stable across re-runs.
- **`text`** — Default field sent to Jev (override with `state_field` in rubric).
- Extra fields are kept in output rows under `source`.

---

## Reading results

After `jev-triage run`:

```bash
jev-triage stats --output .output/<scenario>
```

| Output file | Meaning |
|-------------|---------|
| `accepted.jsonl` | Safe to use Jev’s distributions as **provisional** labels until you have something better |
| `teacher_queue.jsonl` | Send to GPT/Claude/VLM/audio-LM with your rubric |
| `human_queue.jsonl` | Annotator review — often ambiguous or low confidence |
| `soft_labels.jsonl` | Full probs for distillation experiments |

**Success for the scenario** is documented in each folder’s `SUCCESS.md`.
