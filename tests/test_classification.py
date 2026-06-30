import pytest

from provenance_guard.classification import (
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
