import uuid

from flask import Blueprint, jsonify, request

from provenance_guard.audit_log import append_decision
from provenance_guard.classification import (
    CLASSIFIED_STATUS,
    compute_confidence,
    current_timestamp,
    derive_transparency_label,
)
from provenance_guard.signals.signal_a import compute_signal_a
from provenance_guard.signals.signal_b import compute_signal_b
from provenance_guard.validation import validate_submission

submit_bp = Blueprint("submit", __name__)


def build_submission_response(
    *,
    content_id: str,
    creator_id: str,
    score_signal_a: float,
    score_signal_b: float,
    timestamp: str,
) -> dict:
    confidence = compute_confidence(score_signal_a, score_signal_b)
    return {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": timestamp,
        "score_signal_a": score_signal_a,
        "score_signal_b": score_signal_b,
        "confidence": confidence,
        "llm_score": score_signal_b,
        "transparency_label": derive_transparency_label(confidence),
        "status": CLASSIFIED_STATUS,
    }


@submit_bp.post("/submit")
def submit():
    payload = request.get_json(silent=True) or {}
    try:
        text, creator_id = validate_submission(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    content_id = str(uuid.uuid4())
    score_signal_a = compute_signal_a(text)
    score_signal_b = compute_signal_b(text)
    timestamp = current_timestamp()

    response = build_submission_response(
        content_id=content_id,
        creator_id=creator_id,
        score_signal_a=score_signal_a,
        score_signal_b=score_signal_b,
        timestamp=timestamp,
    )
    append_decision(response)

    return jsonify(response), 200
