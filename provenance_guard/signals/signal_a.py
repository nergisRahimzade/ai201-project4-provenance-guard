import math
import re
import string

WORD_RE = re.compile(r"[a-zA-Z']+")
SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")
PUNCT_CHARS = set(string.punctuation)

AI_TRANSITION_PHRASES = (
    "furthermore",
    "moreover",
    "additionally",
    "in conclusion",
    "it is important to note",
    "it is essential",
    "in today's",
    "paradigm",
    "landscape",
    "stakeholders",
    "ultimately",
    "consequently",
    "nevertheless",
    "on the other hand",
    "as a result",
    "in summary",
    "plays a crucial role",
    "rapidly evolving",
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


def _sentence_length_uniformity(text: str) -> float:
    """Low variance in sentence length → more AI-like (uniform structure)."""
    lengths = [
        len(WORD_RE.findall(sentence))
        for sentence in SENTENCE_SPLIT_RE.split(text)
        if sentence.strip()
    ]
    if len(lengths) < 2:
        return 0.5

    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.5

    variance = sum((length - mean) ** 2 for length in lengths) / len(lengths)
    coefficient_of_variation = math.sqrt(variance) / mean
    return max(0.0, 1.0 - coefficient_of_variation / 0.75)


def _transition_phrase_score(text: str) -> float:
    """Formal AI-style transition phrases → more AI-like."""
    lowered = text.lower()
    words = WORD_RE.findall(text)
    if not words:
        return 0.0

    hits = sum(1 for phrase in AI_TRANSITION_PHRASES if phrase in lowered)
    density = hits / (len(words) / 20)
    return min(1.0, density)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _repetition_score(ttr: float) -> float:
    """Low vocabulary diversity (repetitive phrasing) → more AI-like."""
    return _clamp01((0.55 - ttr) / 0.25)


def _punctuation_score(pd: float) -> float:
    """Clean, minimal punctuation → more AI-like. Wider band than before."""
    return _clamp01((0.05 - pd) / 0.05)


def compute_signal_a(text: str) -> float:
    """
    1.0 = more AI-like, 0.0 = more human-like.

    Combines type-token ratio, punctuation density, sentence-length uniformity,
    and formal transition-phrase density. Modern AI prose often has high TTR,
    so repetition alone is insufficient — uniformity and formality help capture it.
    """
    ttr = _type_token_ratio(text)
    pd = _punctuation_density(text)

    repetition = _repetition_score(ttr)
    punctuation = _punctuation_score(pd)
    uniformity = _sentence_length_uniformity(text)
    transitions = _transition_phrase_score(text)

    raw_score = (
        repetition * 0.25
        + punctuation * 0.25
        + uniformity * 0.25
        + transitions * 0.25
    )
    return round(_clamp01(raw_score), 4)
