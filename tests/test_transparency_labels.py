import pytest

from provenance_guard.classification import (
    ALL_TRANSPARENCY_LABELS,
    LABEL_CLEARLY_AI,
    LABEL_CLEARLY_HUMAN,
    LABEL_LIKELY_AI,
    LABEL_LIKELY_HUMAN,
    LABEL_UNCERTAIN,
    derive_transparency_label,
)


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


def test_all_five_label_variants_are_defined():
    assert ALL_TRANSPARENCY_LABELS == {
        LABEL_CLEARLY_AI,
        LABEL_LIKELY_AI,
        LABEL_UNCERTAIN,
        LABEL_LIKELY_HUMAN,
        LABEL_CLEARLY_HUMAN,
    }


@pytest.mark.parametrize("confidence_score,expected_label", [
    (0.9, LABEL_CLEARLY_AI),
    (0.7, LABEL_LIKELY_AI),
    (0.5, LABEL_UNCERTAIN),
    (0.3, LABEL_LIKELY_HUMAN),
    (0.1, LABEL_CLEARLY_HUMAN),
])
def test_all_five_label_variants_are_reachable(confidence_score, expected_label):
    assert derive_transparency_label(confidence_score) == expected_label


def test_submit_response_uses_transparency_label_variant(client):
    text = (
        "The system module processes system data and the system module validates system data. "
        "The system module checks system fields and the system module returns system responses. "
        "The system schema defines system requirements and the system endpoint handles system submissions."
    )
    resp = client.post("/submit", json={"text": text, "creator_id": "creator-1"})
    assert resp.status_code == 200

    label = resp.get_json()["transparency_label"]
    assert label in ALL_TRANSPARENCY_LABELS
