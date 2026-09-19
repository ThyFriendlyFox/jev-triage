# Example: Audio transcripts (lexical path)

## Story

You ran Whisper on call-center clips. Each row is a **transcript**, not raw audio. Jev can judge **lexical** intent (refund asked, sentiment from wording) but **not** prosody, overlap, or background noise.

## Goal

Triage transcripts for labeling: drop ASR poison, accept clear intent, escalate garbled or ambiguous lines.

## Important constraint

Jev only sees `text`. Acoustic labels require a separate small set labeled by humans or an audio LM — see [GOALS.md](../../GOALS.md).

## Run

```bash
jev-triage run \
  --rubric examples/audio-transcripts/rubric.yaml \
  --input examples/audio-transcripts/corpus.jsonl \
  --output .output/audio-transcripts
```

## Success

See [SUCCESS.md](SUCCESS.md).
