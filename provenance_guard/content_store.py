_records: dict[str, dict] = {}


def register_content(record: dict) -> None:
    _records[record["content_id"]] = dict(record)


def get_content(content_id: str) -> dict | None:
    record = _records.get(content_id)
    return dict(record) if record else None


def update_status(
    content_id: str,
    status: str,
    *,
    transparency_label: str | None = None,
) -> dict | None:
    if content_id not in _records:
        return None
    _records[content_id]["status"] = status
    if transparency_label is not None:
        _records[content_id]["transparency_label"] = transparency_label
    return dict(_records[content_id])


def clear() -> None:
    _records.clear()
