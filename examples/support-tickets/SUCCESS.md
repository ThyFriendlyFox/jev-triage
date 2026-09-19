# Success criteria — support ticket triage

## You succeeded when

1. **Clear tickets** (duplicate charge + ASAP, deploy 500s) tend toward **`accepted`** or **`teacher_queue`**, not human — on **live Jev**, after you tune thresholds in `rubric.yaml`.
2. **Ambiguous tickets** (`billing or maybe technical`, `ambiguous case`) appear in **`human_queue.jsonl`** or **`teacher_queue.jsonl`**, not silently in accepted.
3. **`soft_labels.jsonl`** has one line per input `id` with `labels.*.soft_target` populated for Choice/Noul/Score questions.
4. You completed the **downstream step**: teacher/human queues are labeled with **authoritative** tags; training manifest lists source (accepted vs relabeled).
5. On a **held-out** set of human-labeled tickets, your trained router beats “always use Jev argmax” on the metric you care about (accuracy, calibration, cost).

## Mock mode expectations

With `--mock`, routing is **deterministic but not semantically faithful**. Success in mock means:

- Pipeline finishes with 0 errors
- All four output files exist
- Re-run skips all ids (`Skipped (resume)`)

Do **not** treat mock queue membership as validation of your rubric wording.

## Failure signals

- >30% of corpus in `human_queue` without domain justification → thresholds too aggressive or rubric questions overlap.
- Everything in `accepted` → thresholds too loose; spot-check 50 rows manually.
- Empty `soft_labels.jsonl` → pipeline bug or no rows processed.
- You trained on accepted only and never measured against human labels → process failure, not a tooling success.
