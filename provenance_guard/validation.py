MIN_WORDS = 10
MAX_CHARS = 10_000


def validate_submission(payload: dict) -> tuple[str, str]:
    text = payload.get("text")
    creator_id = payload.get("creator_id")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if not isinstance(creator_id, str) or not creator_id.strip():
        raise ValueError("creator_id must be a non-empty string")

    cleaned_text = text.strip()
    if len(cleaned_text) > MAX_CHARS:
        raise ValueError(f"text exceeds {MAX_CHARS} characters")
    if len(cleaned_text.split()) < MIN_WORDS:
        raise ValueError(f"text must contain at least {MIN_WORDS} words")

    return cleaned_text, creator_id.strip()


def validate_appeal(payload: dict) -> tuple[str, str]:
    content_id = payload.get("content_id")
    creator_reasoning = payload.get("creator_reasoning")

    if not isinstance(content_id, str) or not content_id.strip():
        raise ValueError("content_id must be a non-empty string")
    if not isinstance(creator_reasoning, str) or not creator_reasoning.strip():
        raise ValueError("creator_reasoning must be a non-empty string")

    return content_id.strip(), creator_reasoning.strip()
