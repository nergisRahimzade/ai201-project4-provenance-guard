import pytest

from provenance_guard.signals.signal_a import compute_signal_a
from provenance_guard.signals.signal_b import compute_signal_b
from provenance_guard.signals.signal_b_heuristic import heuristic_signal_b


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


def test_heuristic_technical_report_scores_more_ai_like():
    technical_score = heuristic_signal_b(TECHNICAL_REPORT)
    human_score = heuristic_signal_b(EXPRESSIVE_HUMAN)
    assert technical_score > human_score
    assert technical_score > 0.5


def test_heuristic_score_is_bounded():
    assert 0.0 <= heuristic_signal_b("word " * 20) <= 1.0


def test_heuristic_varied_vocabulary_scores_more_human_like():
    evasion_score = heuristic_signal_b(AI_EVASION)
    technical_score = heuristic_signal_b(TECHNICAL_REPORT)
    assert evasion_score < technical_score


def test_compute_signal_b_uses_groq_when_available(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    def fake_groq_score(text: str) -> float:
        return 0.82 if "system module" in text.lower() else 0.15

    monkeypatch.setattr(
        "provenance_guard.signals.signal_b.groq_predictability_score",
        fake_groq_score,
    )

    assert compute_signal_b(TECHNICAL_REPORT) == 0.82
    assert compute_signal_b(EXPRESSIVE_HUMAN) == 0.15


def test_compute_signal_b_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    expected = heuristic_signal_b(TECHNICAL_REPORT)
    assert compute_signal_b(TECHNICAL_REPORT) == expected


def test_false_positive_both_signals_point_ai_with_groq_mock(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        "provenance_guard.signals.signal_b.groq_predictability_score",
        lambda text: 0.78,
    )

    signal_a = compute_signal_a(TECHNICAL_REPORT)
    signal_b = compute_signal_b(TECHNICAL_REPORT)
    assert signal_a > 0.5
    assert signal_b > 0.5
