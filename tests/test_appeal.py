import pytest

from provenance_guard.audit_log import get_entries
from provenance_guard.classification import (
    CLASSIFIED_STATUS,
    UNDER_REVIEW_LABEL,
    UNDER_REVIEW_STATUS,
)
from provenance_guard.content_store import get_content


SAMPLE_TEXT = (
    "The system module processes system data and the system module validates system data. "
    "The system module checks system fields and the system module returns system responses. "
    "The system schema defines system requirements and the system endpoint handles system submissions."
)


def _submit(client, creator_id="creator-123"):
    return client.post("/submit", json={
        "text": SAMPLE_TEXT,
        "creator_id": creator_id,
    })


def test_appeal_updates_status_and_logs_entry(client):
    submit_resp = _submit(client)
    content_id = submit_resp.get_json()["content_id"]

    appeal_resp = client.post("/appeal", json={
        "content_id": content_id,
        "creator_reasoning": "I am a technical writer; this is my own work.",
    })
    assert appeal_resp.status_code == 200

    data = appeal_resp.get_json()
    assert data["appeal_id"]
    assert data["status_update"] == UNDER_REVIEW_STATUS

    content = get_content(content_id)
    assert content["status"] == UNDER_REVIEW_STATUS
    assert content["transparency_label"] == UNDER_REVIEW_LABEL

    entries = get_entries()
    assert len(entries) == 2
    assert entries[0]["record_type"] == "decision"
    assert entries[1]["record_type"] == "appeal"
    assert entries[1]["appeal_id"] == data["appeal_id"]
    assert entries[1]["content_id"] == content_id
    assert entries[1]["creator_reasoning"] == "I am a technical writer; this is my own work."
    assert entries[1]["status"] == UNDER_REVIEW_STATUS
    assert entries[1]["transparency_label"] == UNDER_REVIEW_LABEL
    assert entries[1]["timestamp"].endswith("Z")
    assert entries[1]["original_decision"]["content_id"] == content_id
    assert entries[1]["original_decision"]["status"] == CLASSIFIED_STATUS


def test_appeal_appears_in_get_log(client):
    submit_resp = _submit(client)
    content_id = submit_resp.get_json()["content_id"]

    client.post("/appeal", json={
        "content_id": content_id,
        "creator_reasoning": "Please review this classification.",
    })

    log_resp = client.get("/log")
    assert log_resp.status_code == 200

    entries = log_resp.get_json()["entries"]
    assert len(entries) == 2
    assert entries[1]["record_type"] == "appeal"


@pytest.mark.parametrize("payload", [
    {},
    {"content_id": "missing-id", "creator_reasoning": "Reason"},
    {"creator_reasoning": "Reason"},
    {"content_id": "some-id"},
    {"content_id": "", "creator_reasoning": "Reason"},
    {"content_id": "some-id", "creator_reasoning": ""},
])
def test_appeal_validation_errors(client, payload):
    resp = client.post("/appeal", json=payload)
    assert resp.status_code in {400, 404}
    assert "error" in resp.get_json()


def test_appeal_unknown_content_id_returns_404(client):
    resp = client.post("/appeal", json={
        "content_id": "00000000-0000-0000-0000-000000000000",
        "creator_reasoning": "This should not be found.",
    })
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "content_id not found"


def test_appeal_rejects_already_under_review(client):
    submit_resp = _submit(client)
    content_id = submit_resp.get_json()["content_id"]

    first = client.post("/appeal", json={
        "content_id": content_id,
        "creator_reasoning": "First appeal.",
    })
    assert first.status_code == 200

    second = client.post("/appeal", json={
        "content_id": content_id,
        "creator_reasoning": "Second appeal.",
    })
    assert second.status_code == 400
    assert second.get_json()["error"] == "content is not eligible for appeal"
