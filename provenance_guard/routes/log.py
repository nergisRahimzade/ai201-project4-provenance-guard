from flask import Blueprint, jsonify

from provenance_guard.audit_log import get_log

log_bp = Blueprint("log", __name__)


@log_bp.get("/log")
def log():
    return jsonify({"entries": get_log()})
