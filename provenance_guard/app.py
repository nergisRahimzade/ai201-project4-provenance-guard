from flask import Flask, jsonify

from provenance_guard.routes.appeal import appeal_bp
from provenance_guard.routes.log import log_bp
from provenance_guard.routes.submit import submit_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(submit_bp)
    app.register_blueprint(appeal_bp)
    app.register_blueprint(log_bp)

    @app.get("/")
    def index():
        return jsonify({
            "message": "Provenance Guard API",
            "endpoints": {
                "POST /submit": {
                    "body": {"text": "string", "creator_id": "string"},
                    "response": {
                        "content_id": "string",
                        "creator_id": "string",
                        "timestamp": "string",
                        "score_signal_a": "number",
                        "score_signal_b": "number",
                        "confidence": "number",
                        "llm_score": "number",
                        "transparency_label": (
                            "Clearly AI-generated | Likely AI-generated | Uncertain | "
                            "Likely human-written | Clearly human-written"
                        ),
                        "status": "classified",
                    },
                },
                "POST /appeal": {
                    "body": {"content_id": "string", "creator_reasoning": "string"},
                    "response": {
                        "appeal_id": "string",
                        "status_update": "under review",
                    },
                },
                "GET /log": {
                    "response": {"entries": "list of audit log entries"},
                },
            },
        })

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
