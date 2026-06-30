from provenance_guard.classification import ALL_TRANSPARENCY_LABELS

TEXT_ONE = (
    "The system module processes system data and the system module validates system data. "
    "The system module checks system fields and the system module returns system responses. "
    "The system schema defines system requirements and the system endpoint handles system submissions."
)

TEXT_TWO = (
    "Wow honestly I was not expecting that at all today. "
    "She laughed paused then whispered try again with different words. "
    "Punctuation everywhere and rhythm changes constantly throughout the passage."
)


def test_log_returns_empty_entries(client):
    resp = client.get("/log")
    assert resp.status_code == 200
    assert resp.get_json() == {"entries": []}


def test_log_returns_structured_entries(client):
    client.post("/submit", json={"text": TEXT_ONE, "creator_id": "creator-1"})
    client.post("/submit", json={"text": TEXT_TWO, "creator_id": "creator-2"})

    resp = client.get("/log")
    assert resp.status_code == 200

    entries = resp.get_json()["entries"]
    assert len(entries) >= 2

    for entry in entries:
        assert entry["record_type"] == "decision"
        assert entry["content_id"]
        assert entry["creator_id"]
        assert entry["timestamp"].endswith("Z")
        assert entry["transparency_label"] in ALL_TRANSPARENCY_LABELS
        assert isinstance(entry["score_signal_a"], float)
        assert isinstance(entry["score_signal_b"], float)
        assert isinstance(entry["confidence"], float)
        assert isinstance(entry["llm_score"], float)
        assert entry["status"] == "classified"

    assert entries[0]["creator_id"] == "creator-1"
    assert entries[1]["creator_id"] == "creator-2"
