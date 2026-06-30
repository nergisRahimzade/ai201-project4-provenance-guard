from datetime import UTC, datetime

_log: list[dict] = []


def append_decision(record: dict) -> None:
    _log.append({
        **record,
        "record_type": "decision",
    })


def append_appeal(
    *,
    appeal_id: str,
    content_id: str,
    timestamp: str,
    status: str,
    transparency_label: str,
    creator_reasoning: str,
    original_decision: dict,
) -> None:
    _log.append({
        "record_type": "appeal",
        "appeal_id": appeal_id,
        "content_id": content_id,
        "timestamp": timestamp,
        "status": status,
        "transparency_label": transparency_label,
        "creator_reasoning": creator_reasoning,
        "original_decision": dict(original_decision),
    })


def get_log() -> list[dict]:
    return list(_log)


def get_entries() -> list[dict]:
    return get_log()


def get_decision_by_content_id(content_id: str) -> dict | None:
    for entry in reversed(_log):
        if entry.get("record_type") == "decision" and entry.get("content_id") == content_id:
            return entry
    return None


def clear() -> None:
    _log.clear()
