import pytest
from provenance_guard.signals.signal_b import compute_signal_b
from provenance_guard.signals.signal_a import compute_signal_a
from provenance_guard.classification import compute_confidence, derive_transparency_label


TECHNICAL_REPORT = """
The system module processes system data and the system module validates system data.
The system module checks system fields and the system module returns system responses.
The system schema defines system requirements and the system endpoint handles system submissions.
The system module processes system data and the system module validates system data again.
The system module checks system fields and the system module returns system responses again.
"""

EXPRESSIVE_HUMAN = """
Wow—honestly? I wasn't expecting that at all!!!
She laughed, paused... then whispered: "Try again?"
Different words, different rhythm; punctuation everywhere!!!
"""

AI_EVASION = """
Furthermore, juxtaposed against conventional paradigms—quite unexpectedly—the narrative
employs elliptical fragments; parenthetical asides (remarkably dense); and volatile
punctuation!!! Nevertheless, terminology oscillates: mercurial, capricious, luminous,
iridescent, ephemeral, kaleidoscopic, and unpredictable throughout the passage.
"""

DIALOGUE_HEAVY = """
She said hello to him. He asked how she was. She said fine thanks.
He asked about the weather. She said it was nice. He asked if she wanted coffee.
She said yes please. He asked how she took it. She said with milk.
He asked if she needed sugar. She said no thank you very much.
"""

FORMULAIC_SPEECH = """
Thank you for coming today. Thank you for being here today. Thank you for sharing today.
I am honored to be here today. I am grateful to be here today. I am happy to be here today.
We celebrate love today. We celebrate joy today. We celebrate friendship today.
We thank our friends today. We thank our family today. We thank everyone here today.
"""

TYPICAL_AI_ESSAY = """
In today's rapidly evolving digital landscape, organizations must adapt to unprecedented changes in technology.
Furthermore, the integration of artificial intelligence presents both opportunities and challenges for businesses.
Moreover, stakeholders should consider ethical implications while embracing innovation across all departments.
Ultimately, success depends on balancing efficiency with responsible implementation throughout the organization.
"""


def test_technical_report_scores_more_ai_like():
    """False positive trace: plain technical writing scores AI-like on Signal 1."""
    ai_score = compute_signal_a(TECHNICAL_REPORT)
    human_score = compute_signal_a(EXPRESSIVE_HUMAN)
    assert ai_score > human_score
    assert ai_score > 0.5


def test_score_is_bounded():
    assert 0.0 <= compute_signal_a("word " * 20) <= 1.0


def test_varied_vocabulary_and_punctuation_scores_more_human_like():
    """Edge case 2: AI text instructed to vary vocabulary and punctuation."""
    evasion_score = compute_signal_a(AI_EVASION)
    technical_score = compute_signal_a(TECHNICAL_REPORT)
    assert evasion_score < technical_score


def test_dialogue_heavy_fiction_scores_ai_like():
    """Edge case 5: repeated phrases like 'She said' drive TTR down."""
    dialogue_score = compute_signal_a(DIALOGUE_HEAVY)
    expressive_score = compute_signal_a(EXPRESSIVE_HUMAN)
    assert dialogue_score > expressive_score


def test_formulaic_genre_scores_ai_like():
    """Edge case 7: formulaic human genres reuse predictable phrasing."""
    formulaic_score = compute_signal_a(FORMULAIC_SPEECH)
    expressive_score = compute_signal_a(EXPRESSIVE_HUMAN)
    assert formulaic_score > expressive_score

def test_typical_ai_essay_scores_higher_than_expressive_human():
    """Polished AI prose should not score as strongly human on Signal 1."""
    ai_score = compute_signal_a(TYPICAL_AI_ESSAY)
    human_score = compute_signal_a(EXPRESSIVE_HUMAN)
    assert ai_score > human_score
    assert ai_score > 0.45


def test_my_custom_text_block():
    text = """
    Artificial intelligence represents a transformative paradigm shift in modern society.
    It is important to note that while the benefits of AI are numerous, it is equally
    essential to consider the ethical implications. Furthermore, stakeholders across
    various sectors must collaborate to ensure responsible deployment.
    """
    score_a = compute_signal_a(text)
    score_b = compute_signal_b(text)
    confidence = compute_confidence(score_a, score_b)
    label = derive_transparency_label(confidence)

    print(score_a, score_b, confidence, label)
    assert score_a > 0.45
    assert 0.0 <= score_a <= 1.0
