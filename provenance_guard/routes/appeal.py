import uuid

from flask import Blueprint, jsonify, request

from provenance_guard.audit_log import append_appeal, get_decision_by_content_id
from provenance_guard.classification import (
    CLASSIFIED_STATUS,
    UNDER_REVIEW_LABEL,
    UNDER_REVIEW_STATUS,
    current_timestamp,
)
from provenance_guard.content_store import get_content, update_status
from provenance_guard.validation import validate_appeal

appeal_bp = Blueprint("appeal", __name__)


@appeal_bp.post("/appeal")
def appeal():
    payload = request.get_json(silent=True) or {}
    try:
        content_id, creator_reasoning = validate_appeal(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    original_decision = get_decision_by_content_id(content_id)
    if original_decision is None:
        return jsonify({"error": "content_id not found"}), 404

    content = get_content(content_id)
    if content is None:
        return jsonify({"error": "content_id not found"}), 404
    if content["status"] != CLASSIFIED_STATUS:
        return jsonify({"error": "content is not eligible for appeal"}), 400

    appeal_id = str(uuid.uuid4())
    timestamp = current_timestamp()

    update_status(
        content_id,
        UNDER_REVIEW_STATUS,
        transparency_label=UNDER_REVIEW_LABEL,
    )
    append_appeal(
        appeal_id=appeal_id,
        content_id=content_id,
        timestamp=timestamp,
        status=UNDER_REVIEW_STATUS,
        transparency_label=UNDER_REVIEW_LABEL,
        creator_reasoning=creator_reasoning,
        original_decision=original_decision,
    )

    return jsonify({
        "appeal_id": appeal_id,
        "status_update": UNDER_REVIEW_STATUS,
    }), 200
