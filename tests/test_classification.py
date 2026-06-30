from provenance_guard.classification import (
    LABEL_LIKELY_AI,
    LABEL_LIKELY_HUMAN,
    LABEL_UNCERTAIN,
    compute_confidence,
    derive_transparency_label,
)


def test_confidence_weights_signal_b_more_heavily():
    assert compute_confidence(0.8, 0.6) == 0.66
    assert compute_confidence(0.2, 0.8) == 0.62


def test_confidence_follows_signal_b_when_signals_disagree():
    confidence = compute_confidence(0.9, 0.1)
    assert confidence == 0.34
    assert derive_transparency_label(confidence) == LABEL_LIKELY_HUMAN

    confidence_ai = compute_confidence(0.1, 0.9)
    assert confidence_ai == 0.66
    assert derive_transparency_label(confidence_ai) == LABEL_LIKELY_AI
