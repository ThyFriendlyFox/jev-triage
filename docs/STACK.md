# Jev training stack (two repos)

Use both repos in order when building a dataset for a **locally hosted** model.

```
                    ┌─────────────────────────────────────┐
                    │  Raw corpus (JSONL, transcripts, …) │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │  jev-curate  —  keep / drop          │
                    │  Output: curated.jsonl               │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │  jev-triage  —  accept / teacher / human │
                    │  Output: queues + soft_labels.jsonl  │
                    └──────────────────┬──────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
        accepted (cheap)         teacher (LLM/VLM)         human (annotators)
              │                        │                        │
              └────────────────────────┼────────────────────────┘
                                       ▼
                    ┌─────────────────────────────────────┐
                    │  Train — targets = REAL outcomes       │
                    │  (not “Jev was confident”)             │
                    └─────────────────────────────────────┘
```

| Repo | Question it answers | Success in one line |
|------|---------------------|---------------------|
| [jev-curate](https://github.com/ThyFriendlyFox/jev-curate) | “Should this row exist in our dataset at all?” | Curated split audited; bad rows in `rejected.jsonl` |
| [jev-triage](https://github.com/ThyFriendlyFox/jev-triage) | “How much labeling money do we spend on this row?” | Queues processed; model eval on human/outcome labels |

Shared rule: **filter and route with Jev; learn from real outcomes.**
