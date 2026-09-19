# Success criteria — audio transcripts

## You succeeded when

1. Rows with **Whisper hallucination patterns** (music, repeated tokens, silence artifacts) skew toward **human** or **teacher**, not bulk **accepted** — on live Jev with `asr_plausible` gate in the rubric.
2. Clear refund / cancellation language lands in **accepted** or **teacher** with high `intent_refund` Noul in `soft_labels.jsonl`.
3. You **did not** claim the student model learns acoustics from these labels alone — your training doc states “lexical head only.”
4. You validated **5–10%** of transcripts against audio manually before trusting a full run (caption-then-judge caveat).

## Mock mode

Mock heuristics look for words like `garbled`, `hallucin`. Success = files written + resume works.

## Failure signals

- Using transcript triage to label “speaker angry (tone)” → wrong tool; label acoustically on a separate set.
- 100% accepted on a noisy ASR corpus → rubric or thresholds broken.
