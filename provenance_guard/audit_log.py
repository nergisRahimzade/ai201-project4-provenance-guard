from datetime import UTC, datetime

_log: list[dict] = []


def append_decision(record: dict) -> None:
    _log.append({
        **record,
        "record_type": "decision",
        "attribution_result": record["transparency_label"],
        "appeal_filed": False,
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
        "attribution_result": transparency_label,
        "creator_reasoning": creator_reasoning,
        "appeal_filed": True,
        "original_decision": dict(original_decision),
    })


def mark_appeal_filed(content_id: str) -> None:
    for entry in _log:
        if entry.get("record_type") == "decision" and entry.get("content_id") == content_id:
            entry["appeal_filed"] = True
            return


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
