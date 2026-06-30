from datetime import UTC, datetime

CLASSIFIED_STATUS = "classified"

LABEL_CLEARLY_AI = "Clearly AI-generated"
LABEL_LIKELY_AI = "Likely AI-generated"
LABEL_UNCERTAIN = "Uncertain"
LABEL_LIKELY_HUMAN = "Likely human-written"
LABEL_CLEARLY_HUMAN = "Clearly human-written"

ALL_TRANSPARENCY_LABELS = {
    LABEL_CLEARLY_AI,
    LABEL_LIKELY_AI,
    LABEL_UNCERTAIN,
    LABEL_LIKELY_HUMAN,
    LABEL_CLEARLY_HUMAN,
}


def current_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def compute_confidence(score_signal_a: float, score_signal_b: float) -> float:
    return round((score_signal_a + score_signal_b) / 2, 2)


def derive_transparency_label(confidence_score: float) -> str:
    if confidence_score >= 0.8:
        return LABEL_CLEARLY_AI
    if confidence_score >= 0.65:
        return LABEL_LIKELY_AI
    if confidence_score > 0.45:
        return LABEL_UNCERTAIN
    if confidence_score > 0.2:
        return LABEL_LIKELY_HUMAN
    return LABEL_CLEARLY_HUMAN
