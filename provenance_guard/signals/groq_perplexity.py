import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TEXT_CHARS = 8000

SYSTEM_PROMPT = """You estimate Signal 2 (perplexity / language-model predictability) for Provenance Guard.

Return JSON with one field: score_signal_b (float from 0 to 1, four decimal places).

score_signal_b measures AI-likeness via how predictable the text is to a language model — NOT raw perplexity units:
- 1.0 = lowest perplexity, most AI-typical. Polished, conventional, highly predictable prose.
- 0.5 = mixed or ambiguous predictability.
- 0.0 = highest perplexity, most human-typical. Surprising word choices and irregular rhythm.

Calibrate approximately as:
- Typical polished AI essay → 0.75–0.95
- Expressive, idiosyncratic human writing → 0.05–0.35
- Repetitive technical documentation → 0.70–0.90

Judge statistical predictability to an LLM, not who you believe authored the text."""


def _get_client() -> Groq | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def groq_predictability_score(text: str) -> float:
    client = _get_client()
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not set")

    truncated = text.strip()[:MAX_TEXT_CHARS]
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Estimate score_signal_b for the text below.\n\n"
                    f"TEXT:\n{truncated}"
                ),
            },
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty response")

    payload = json.loads(content)
    score = float(payload["score_signal_b"])
    return round(max(0.0, min(1.0, score)), 4)
