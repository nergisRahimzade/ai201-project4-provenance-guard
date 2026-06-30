import pytest

from provenance_guard.app import create_app
from provenance_guard.audit_log import clear, get_decision_by_content_id, get_entries
from provenance_guard.classification import (
    ALL_TRANSPARENCY_LABELS,
    CLASSIFIED_STATUS,
    compute_confidence,
    derive_transparency_label,
)
from provenance_guard.signals.signal_a import compute_signal_a
from provenance_guard.signals.signal_b import compute_signal_b


@pytest.fixture
def client():
    clear()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    clear()


SAMPLE_TEXT = (
    "The system module processes system data and the system module validates system data. "
    "The system module checks system fields and the system module returns system responses. "
    "The system schema defines system requirements and the system endpoint handles system submissions."
)


def test_submit_returns_all_three_scores(client):
    resp = client.post("/submit", json={
        "text": SAMPLE_TEXT,
        "creator_id": "creator-123",
    })
    assert resp.status_code == 200
    data = resp.get_json()

    expected_a = compute_signal_a(SAMPLE_TEXT)
    expected_b = compute_signal_b(SAMPLE_TEXT)
    expected_confidence = compute_confidence(expected_a, expected_b)

    assert data["content_id"]
    assert data["creator_id"] == "creator-123"
    assert data["timestamp"].endswith("Z")
    assert data["score_signal_a"] == expected_a
    assert data["score_signal_b"] == expected_b
    assert data["confidence"] == expected_confidence
    assert data["llm_score"] == expected_b
    assert data["transparency_label"] == derive_transparency_label(expected_confidence)
    assert data["status"] == CLASSIFIED_STATUS


def test_submit_writes_audit_log(client):
    resp = client.post("/submit", json={
        "text": SAMPLE_TEXT,
        "creator_id": "creator-123",
    })
    data = resp.get_json()

    assert len(get_entries()) == 1
    logged = get_decision_by_content_id(data["content_id"])
    assert logged is not None
    assert logged["score_signal_a"] == data["score_signal_a"]
    assert logged["score_signal_b"] == data["score_signal_b"]
    assert logged["confidence"] == data["confidence"]
    assert logged["record_type"] == "decision"


@pytest.mark.parametrize("payload", [
    {},
    {"text": "Sample submission text.", "creator_id": "creator-123"},
    {"text": SAMPLE_TEXT},
    {"creator_id": "creator-123"},
    {"text": "", "creator_id": "creator-123"},
    {"text": SAMPLE_TEXT, "creator_id": ""},
    {"text": "too short", "creator_id": "creator-123"},
])
def test_submit_validation_errors(client, payload):
    resp = client.post("/submit", json=payload)
    assert resp.status_code == 400
    assert "error" in resp.get_json()
    assert get_entries() == []
