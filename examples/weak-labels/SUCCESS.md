# Success criteria — weak labels

## You succeeded when

1. Rows where content clearly **conflicts** with `label` (e.g. technical error text labeled `billing`) land in **teacher** or **human**, not **accepted**, on live Jev.
2. Rows where `label_plausible` is high and `department_matches_label` Choice aligns with `label` land in **accepted**.
3. Final training set **replaces** wrong vendor labels for teacher/human rows; accepted rows are spot-checked (e.g. 1–2% audit).
4. Evaluation uses **held-out human adjudication**, not Jev agreement with itself.

## Failure signals

- Treating `accepted.jsonl` as ground truth when labels were vendor-provided garbage.
- No `label` field in JSONL but rubric assumes it — Jev lacks context; fix schema.
