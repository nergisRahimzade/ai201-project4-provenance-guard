import os

import pytest

from provenance_guard.classification import compute_confidence, derive_transparency_label
from provenance_guard.signals.signal_a import compute_signal_a
from provenance_guard.signals.signal_b import compute_signal_b


AI_ESSAY = """
In today's rapidly evolving digital landscape, organizations must adapt to unprecedented changes in technology.
Furthermore, the integration of artificial intelligence presents both opportunities and challenges for businesses.
Moreover, stakeholders should consider ethical implications while embracing innovation across departments.
Ultimately, success depends on balancing efficiency with responsible implementation throughout the organization.
"""


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
def test_groq_scores_typical_ai_essay_higher_than_expressive_human():
    ai_score = compute_signal_b(AI_ESSAY)
    human_text = """
    Wow honestly I was not expecting that at all today here now.
    She laughed paused then whispered try again with totally different words.
    Punctuation everywhere and rhythm changes constantly throughout this passage here.
    """
    human_score = compute_signal_b(human_text)

    assert ai_score > human_score
    confidence = compute_confidence(compute_signal_a(AI_ESSAY), ai_score)
    assert confidence > 0.45
