import logging

from provenance_guard.signals.groq_perplexity import groq_predictability_score
from provenance_guard.signals.signal_b_heuristic import heuristic_signal_b

logger = logging.getLogger(__name__)


def compute_signal_b(text: str) -> float:
    """
    1.0 = more AI-like (low perplexity / high LM predictability).
    0.0 = more human-like (high perplexity / surprising word choices).

    Uses Groq when GROQ_API_KEY is set; falls back to a local heuristic otherwise.
    """
    try:
        return groq_predictability_score(text)
    except RuntimeError:
        logger.info("GROQ_API_KEY not set; using heuristic Signal 2 fallback")
        return heuristic_signal_b(text)
    except Exception as exc:
        logger.warning("Groq Signal 2 failed (%s); using heuristic fallback", exc)
        return heuristic_signal_b(text)
