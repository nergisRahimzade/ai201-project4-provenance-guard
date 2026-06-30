import pytest

from provenance_guard.app import create_app
from provenance_guard.audit_log import clear as clear_audit_log
from provenance_guard.content_store import clear as clear_content_store


@pytest.fixture
def client():
    clear_audit_log()
    clear_content_store()
    app = create_app()
    app.config["TESTING"] = True
    app.config["RATELIMIT_ENABLED"] = False
    with app.test_client() as client:
        yield client
    clear_audit_log()
    clear_content_store()
