import re
import string

WORD_RE = re.compile(r"[a-zA-Z']+")
PUNCT_CHARS = set(string.punctuation)
SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")

AI_TRANSITION_RE = re.compile(
    r"\b("
    r"furthermore|moreover|additionally|in conclusion|in summary|ultimately|"
    r"consequently|therefore|thus|however|nevertheless|"
    r"it is important to note|it is worth noting|it is essential|"
    r"in today'?s|across various|stakeholders|landscape|paradigm|"
    r"comprehensive|multifaceted|crucial|robust|leverage|utilize|delve"
    r")\b",
    re.IGNORECASE,
)


def _type_token_ratio(text: str) -> float:
    words = [w.lower() for w in WORD_RE.findall(text)]
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _punctuation_density(text: str) -> float:
    if not text:
        return 0.0
    punct_count = sum(1 for ch in text if ch in PUNCT_CHARS)
    return punct_count / len(text)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _punctuation_ai_score(pd: float) -> float:
    """Low punctuation density → AI-like (clean, predictable punctuation)."""
    return _clamp01((0.04 - pd) / 0.04)


def _ttr_ai_score(ttr: float, pd: float) -> float:
    """
    AI-like TTR patterns:
    - very low TTR: repetitive phrasing (technical/formulaic AI or prose)
    - high TTR + low PD: polished AI essay with varied but safe vocabulary
    High TTR + high PD → human-like (expressive punctuation), scored low here.
    """
    if pd >= 0.05:
        return _clamp01(0.15 - (pd - 0.05) * 2)

    if ttr < 0.5:
        return _clamp01((0.5 - ttr) / 0.3)

    if ttr >= 0.65:
        return _clamp01(0.55 + (ttr - 0.65) / 0.35 * 0.45)

    return _clamp01(0.35 - (ttr - 0.5) / 0.15 * 0.2)


def _sentence_uniformity_score(text: str) -> float:
    """Uniform sentence lengths → AI-like; high variance → human-like."""
    lengths = [
        len(WORD_RE.findall(sentence))
        for sentence in SENTENCE_SPLIT_RE.split(text)
        if sentence.strip()
    ]
    if len(lengths) < 2:
        return 0.5

    mean_length = sum(lengths) / len(lengths)
    if mean_length == 0:
        return 0.5

    variance = sum((length - mean_length) ** 2 for length in lengths) / len(lengths)
    coefficient_of_variation = (variance ** 0.5) / mean_length
    return _clamp01(1.0 - coefficient_of_variation / 0.75)


def _transition_phrase_score(text: str) -> float:
    """Formal AI-typical transition phrases and diction."""
    words = WORD_RE.findall(text)
    if not words:
        return 0.0
    matches = len(AI_TRANSITION_RE.findall(text))
    density = matches / len(words)
    return _clamp01(density / 0.08)


def compute_signal_a(text: str) -> float:
    """
    1.0 = more AI-like, 0.0 = more human-like.
    Structural signal from TTR, punctuation density, sentence uniformity,
    and AI-typical transition phrasing.
    """
    ttr = _type_token_ratio(text)
    pd = _punctuation_density(text)

    pd_score = _punctuation_ai_score(pd)
    ttr_score = _ttr_ai_score(ttr, pd)
    uniformity_score = _sentence_uniformity_score(text)
    transition_score = _transition_phrase_score(text)

    raw_score = (
        pd_score * 0.30
        + ttr_score * 0.30
        + uniformity_score * 0.20
        + transition_score * 0.20
    )
    return round(_clamp01(raw_score), 4)
