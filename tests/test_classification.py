import pytest

from provenance_guard.classification import (
    LABEL_CLEARLY_AI,
    LABEL_CLEARLY_HUMAN,
    LABEL_LIKELY_AI,
    LABEL_LIKELY_HUMAN,
    LABEL_UNCERTAIN,
    compute_confidence,
    derive_transparency_label,
)


def test_confidence_is_unweighted_average():
    assert compute_confidence(0.8, 0.6) == 0.7
    assert compute_confidence(0.2, 0.8) == 0.5


def test_confidence_near_half_when_signals_disagree():
    confidence = compute_confidence(0.9, 0.1)
    assert confidence == 0.5
    assert derive_transparency_label(confidence) == LABEL_UNCERTAIN


@pytest.mark.parametrize("confidence_score,expected_label", [
    (1.0, LABEL_CLEARLY_AI),
    (0.8, LABEL_CLEARLY_AI),
    (0.79, LABEL_LIKELY_AI),
    (0.65, LABEL_LIKELY_AI),
    (0.64, LABEL_UNCERTAIN),
    (0.46, LABEL_UNCERTAIN),
    (0.45, LABEL_LIKELY_HUMAN),
    (0.21, LABEL_LIKELY_HUMAN),
    (0.2, LABEL_CLEARLY_HUMAN),
    (0.0, LABEL_CLEARLY_HUMAN),
])
def test_transparency_label_thresholds(confidence_score, expected_label):
    assert derive_transparency_label(confidence_score) == expected_label
