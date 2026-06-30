import math
import re
from collections import Counter

WORD_RE = re.compile(r"[a-zA-Z']+")

COMMON_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "that", "this", "these", "those", "it", "its", "they", "them", "their",
    "with", "from", "by", "as", "not", "can", "each", "through", "system",
    "data", "module", "returns", "defines", "checks", "processes", "validates",
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalized_entropy(words: list[str]) -> float:
    if not words:
        return 0.0
    counts = Counter(words)
    total = len(words)
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return entropy / max_entropy if max_entropy else 0.0


def _bigram_predictability(words: list[str]) -> float:
    if len(words) < 2:
        return 1.0
    bigrams = [(words[i], words[i + 1]) for i in range(len(words) - 1)]
    counts = Counter(bigrams)
    repeated = sum(count for count in counts.values() if count > 1)
    return repeated / len(bigrams)


def _common_word_ratio(words: list[str]) -> float:
    if not words:
        return 0.0
    return sum(1 for word in words if word in COMMON_WORDS) / len(words)


def heuristic_signal_b(text: str) -> float:
    """Local fallback when Groq is unavailable."""
    words = [word.lower() for word in WORD_RE.findall(text)]
    if not words:
        return 0.5

    predictability_from_entropy = 1.0 - _normalized_entropy(words)
    bigram_score = _bigram_predictability(words)
    common_ratio = _common_word_ratio(words)

    raw_score = (predictability_from_entropy + bigram_score + common_ratio) / 3
    return round(_clamp01(raw_score), 4)
