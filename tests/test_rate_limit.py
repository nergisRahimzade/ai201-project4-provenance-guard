from provenance_guard.app import create_app

RATE_LIMIT_TEXT = (
    "This is a test submission for rate limit testing purposes only."
)


def test_submit_rate_limit_returns_429_after_ten_requests():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    status_codes = []
    for _ in range(12):
        resp = client.post("/submit", json={
            "text": RATE_LIMIT_TEXT,
            "creator_id": "ratelimit-test",
        })
        status_codes.append(resp.status_code)

    assert status_codes[:10] == [200] * 10
    assert status_codes[10:] == [429] * 2
