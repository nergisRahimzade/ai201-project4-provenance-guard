# ai201-project4-provenance-guard
CodePath AI 201 — Week 4 — Provenance Guard

## Confidence score

The combined confidence score is a weighted blend of the two detection signals:

```
confidence_score = 0.3 × score_signal_A + 0.7 × score_signal_B
```

Signal A measures structural patterns (type-token ratio and punctuation density). Signal B measures semantic/statistical patterns (perplexity / language model confidence). Both scores use the same scale: `1.0` = most AI-like, `0.0` = most human-like.

Because I noticed my program wasn't being accurate with confidence score, due to signal B being better at detecting human and AI than A, I changed the formula to weigh more towards signal B score.

## Project layout

```
provenance_guard/
  __init__.py
  app.py
  audit_log.py
  classification.py
  content_store.py
  validation.py
  routes/
    appeal.py
    log.py
    submit.py
  signals/
    signal_a.py
    signal_b.py
tests/
  test_appeal.py
  test_classification.py
  test_log.py
  test_submit.py
  test_transparency_labels.py
```
