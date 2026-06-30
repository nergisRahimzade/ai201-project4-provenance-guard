# Provenance Guard

CodePath AI 201 — Week 4 — Provenance Guard

Provenance Guard is a Flask API that classifies submitted text as likely AI-generated or likely human-written, assigns a transparency label, logs every decision for audit, and lets creators appeal a classification for human review. It is designed to **surface uncertainty honestly** rather than deliver a binary verdict.

---

## Architecture

A submission follows a fixed pipeline from raw text to a logged decision:

```
POST /submit → validate input → Signal A + Signal B (in parallel)
  → weighted confidence score → transparency label → audit log → response

POST /appeal → lookup by content_id → status = "under review" → append appeal to audit log
```

**Components**

| Component | Role |
|---|---|
| `validation.py` | Rejects empty, too-short, or oversized submissions |
| `signals/signal_a.py` | Structural score (type-token ratio + punctuation density) |
| `signals/signal_b.py` | Semantic score (LLM perplexity via Groq, heuristic fallback) |
| `classification.py` | Combines signals into confidence score and transparency label |
| `audit_log.py` | In-memory structured JSON log of decisions and appeals |
| `content_store.py` | Tracks current status per `content_id` |
| `extensions.py` | Flask-Limiter (10/min, 100/day on `/submit`) |

**Design intent:** Detection signals run independently so each can fail in different ways. The appeal workflow exists because no automated classifier should be the final authority — when the system is wrong, a human reviewer gets the full audit trail.

---

## Detection Signals

### Why these two signals?

AI-generated and human-written text differ in ways no single metric captures well. I chose two complementary signals:

**Signal A (structural)** measures *type-token ratio* (vocabulary diversity) and *punctuation density*. AI text tends toward safe, repeated vocabulary and clean, predictable punctuation. Human writing — especially informal or expressive prose — tends toward more varied word choice and expressive punctuation (question marks, dashes, ellipses).

**Signal B (semantic)** measures how predictable the text is to a language model (*perplexity*). AI text is optimized to produce high-probability token sequences, so it often scores as more "predictable" (more AI-like). Human writing can include surprising word choices that a model would not expect.

Using both signals together catches cases where one alone would fail. A human technical report has low structural variation and predictable phrasing — both signals may point AI even when a human wrote it. A human blog post with casual language and varied punctuation may score human on structure even if the semantics are somewhat predictable.

### What I would change for a real deployment

- **Calibrate on labeled data.** Both signals use hand-tuned thresholds, not a validated dataset. Production would require labeled examples across genres, lengths, and languages.
- **Persist the audit log.** The current in-memory store resets on server restart. Production needs durable storage (database or append-only log file).
- **Replace or supplement perplexity.** Groq API calls add latency and cost; a local model or ensemble of detectors would be more reliable at scale.
- **Genre-aware baselines.** Legal, medical, and academic human writing share AI-like structural properties; a production system should normalize by genre or let users declare context.

---

## Confidence Scoring

### Why this approach?

Both signals output a score from 0 (most human-like) to 1 (most AI-like), so they can be combined into one number. The original spec used a simple average:

```
(score_signal_A + score_signal_B) / 2
```

During testing I found Signal B separated clearly AI and clearly human examples more reliably than Signal A. Signal A alone was thrown off by domain-specific vocabulary (technical reports score AI-like because writers reuse terminology) and by short samples where type-token ratio is unstable.

I changed the formula to weight Signal B more heavily:

```
confidence_score = 0.3 × score_signal_A + 0.7 × score_signal_B
```

Because I noticed my program wasn't being accurate with confidence score, due to signal B being better at detecting human and AI than A, I changed the formula to weigh more towards signal B score.

**Important:** A confidence score of 0.6 does **not** mean "60% chance this is AI." It means the combined evidence leans mildly toward AI-generated writing. Mid-range scores are treated as genuinely uncertain, not weak guesses.

| Range | Label |
|---|---|
| ≥ 0.8 | Clearly AI-generated |
| 0.65 – 0.79 | Likely AI-generated |
| 0.45 – 0.65 | Uncertain |
| 0.20 – 0.45 | Likely human-written |
| ≤ 0.20 | Clearly human-written |

### Example submissions

These four texts were run through the live detection pipeline. Scores show meaningful variation — not a constant output.

#### 1. AI-style essay — high confidence AI case

**Text:**
> Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.

| score_signal_a | score_signal_b | confidence | label |
|---|---|---|---|
| 0.544 | 0.925 | **0.81** | Clearly AI-generated |

Signal B is very high — the phrasing is highly predictable to a language model ("It is important to note," "Furthermore," "stakeholders across various sectors"). Signal A is moderate. The weighted score lands firmly in the high-confidence AI band.

#### 2. Casual ramen review — lower confidence human case

**Text:**
> ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won't go back unless someone drags me there

| score_signal_a | score_signal_b | confidence | label |
|---|---|---|---|
| 0.211 | 0.231 | **0.23** | Likely human-written |

Both signals agree this reads human: informal vocabulary, expressive punctuation (question mark, casual phrasing), and less predictable word choices for a language model. This contrasts sharply with Example 1 (0.81 vs 0.23).

#### 3. Academic monetary policy excerpt

**Text:**
> The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations.

| score_signal_a | score_signal_b | confidence | label |
|---|---|---|---|
| 0.381 | 0.825 | **0.69** | Likely AI-generated |

Signal A is relatively low (formal but not repetitive), but Signal B is high because academic prose is statistically predictable. This illustrates how professional human writing in a formal register can score AI-like on the semantic signal alone.

#### 4. Remote work opinion — mixed signals at the boundary

**Text:**
> I've been thinking a lot about remote work lately. There are genuine tradeoffs — flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type.

| score_signal_a | score_signal_b | confidence | label |
|---|---|---|---|
| 0.251 | 0.825 | **0.65** | Likely AI-generated |

The signals **disagree**: Signal A suggests human-like structure (varied phrasing, an em-dash), while Signal B strongly suggests AI-like predictability. The weighted score sits exactly at the Likely AI threshold — a case where the label should be read cautiously, not as a definitive verdict.

---

## Transparency Label Variants

The API returns a short label name. The reader-facing text below is what would be displayed to an end user.

### High-confidence AI (Example 1 — confidence 0.81)

**Label:** Clearly AI-generated

**Displayed text:**
> Our system is clearly confident that this content was written by an AI.

### High-confidence human (Example 2 — confidence 0.23)

**Label:** Likely human-written

**Displayed text:**
> Our system is likely confident that this content was written by a human.

*(At confidence ≤ 0.20 the label becomes "Clearly human-written": "Our system is clearly confident that this content was written by a human.")*

### Uncertain (when 0.45 < confidence < 0.65)

**Label:** Uncertain

**Displayed text:**
> Our system is uncertain whether this content was written by an AI or a human.

None of the four example texts above landed in the Uncertain band, which is itself informative: borderline cases like Example 4 (0.65) sit at the edge of Likely AI rather than Uncertain. A production system would expect more submissions in the uncertain band as text mixes human and AI characteristics.

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/submit` | Submit text for classification |
| `POST` | `/appeal` | Appeal a decision by `content_id` |
| `GET` | `/log` | Retrieve structured audit log (JSON) |

**Submit body:** `{ "text": "...", "creator_id": "..." }`

**Appeal body:** `{ "content_id": "...", "creator_reasoning": "..." }`

---

## Rate Limiting

The `/submit` endpoint is limited to **10 requests per minute** and **100 requests per day**.

These limits balance usability and abuse prevention. A legitimate writer may submit multiple revisions while editing, but is unlikely to exceed ten submissions per minute or one hundred per day. The limits allow normal interactive use while reducing automated flooding.

Flask-Limiter uses in-memory storage for local development (`storage_uri="memory://"`).

### Rate limit test evidence

12 rapid requests — 10 succeed, then 429:

```
200
200
200
200
200
200
200
200
200
200
429
429
```

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test submission for rate limit testing purposes only.", "creator_id": "ratelimit-test"}'
done
```

Automated test: `python -m pytest tests/test_rate_limit.py -v`

---

## Audit Log

`GET /log` returns structured JSON — not console output. Each **decision** entry includes `timestamp`, `content_id`, `attribution_result`, `confidence`, `score_signal_a`, `score_signal_b`, and `appeal_filed`. Each **appeal** entry includes `appeal_id`, `creator_reasoning`, and a snapshot of the `original_decision`.

The log is in-memory and resets when the server restarts.

---

## Known Limitations

**Human-written technical and academic reports are likely to be misclassified as AI-generated.**

Example 3 above scores 0.69 (Likely AI-generated) even though a human economist or policy analyst could plausibly have written it. This is not a generic "needs more training data" problem — it follows directly from how the signals work:

- **Signal A** penalizes low type-token ratio. Technical writing reuses domain terms ("monetary policy," "asset price inflation," "central banks"), which lowers vocabulary diversity regardless of authorship.
- **Signal B** penalizes low perplexity. Formal academic prose is intentionally predictable — writers avoid surprising phrasing. A language model finds this text easy to predict, so it scores AI-like.

Neither signal distinguishes *why* the text is structurally uniform or semantically predictable. A human expert and an AI both produce clean, formulaic academic prose. The appeal workflow exists specifically for this failure mode: the creator can explain context ("I wrote this policy brief myself") and a human reviewer makes the final call.

Other known weaknesses: very short submissions (unstable TTR), AI text deliberately styled to mimic casual human writing, and human text heavily edited from an AI draft.

---

## Spec Reflection

**How the spec helped:** The architecture narrative in `planning.md` gave me a clear component map — validate → two independent signals → confidence → label → audit log → response — which I implemented almost directly as separate modules and routes. The false-positive scenario trace also shaped the appeal workflow: I built `POST /appeal` and the audit log specifically so a misclassified technical writer could dispute the result without triggering automated re-classification.

**Where I diverged:** The spec originally defined confidence as an unweighted average of both signals, arguing that weighting one signal more would be unjustified without labeled data. After Milestone 4 testing, Signal B consistently separated my test cases better than Signal A, so I changed to a 30/70 weighted formula and documented the reason in both `README.md` and `planning.md`. I also used `creator_reasoning` as the appeal field name (instead of `reasoning`) and added explicit `attribution_result` and `appeal_filed` fields to audit log entries for clearer structured logging.

---

## AI Usage

### Instance 1 — Building the appeal workflow and tests

**What I directed:** I gave the AI sections of `planning.md` (architecture narrative, transparency labels, appeal workflow diagram, API surface) and asked it to implement `POST /appeal`, verify transparency label thresholds, and write test files.

**What it produced:** A `content_store.py` module, `routes/appeal.py`, audit log extensions (`append_appeal`, `mark_appeal_filed`), and `test_appeal.py` / `test_transparency_labels.py`. It correctly wired the appeal to update status and log the original decision.

**What I revised:** I chose `creator_reasoning` as the request field name to match my API design. I verified the transparency label thresholds against `planning.md` rather than changing working code unnecessarily.

### Instance 2 — Confidence formula change and production features

**What I directed:** I asked the AI to change the confidence formula to weight Signal B more heavily, update `planning.md` to match, and later implement Flask-Limiter plus complete the audit log fields.

**What it produced:** Updated `compute_confidence()` with 0.3/0.7 weights, revised tests in `test_classification.py`, added Flask-Limiter via `extensions.py`, and extended audit log entries with `attribution_result` and `appeal_filed`.

**What I revised:** I provided the exact reason text for the formula change ("Because I noticed my program wasn't being accurate…"). I ran the four example submissions myself to validate that scores varied meaningfully before documenting them here. I kept rate-limit test evidence (10× 200, 2× 429) in the README as grader-facing proof.

### Instance 3 — Implementing signals

**What I directed:** I asked the AI to generate the code for the signals using planning.md as a guide.

**What it produced:** Generated the code for the signals.

**What I revised:** I tested both signals individually and together to make sure the scores were valid and varied meaningfully.

---

## Running the Project

```bash
pip install -r requirements.txt
python -m provenance_guard.app
```

Server runs at `http://127.0.0.1:5000`.

```bash
python -m pytest tests/ -v
```

Optional: set `GROQ_API_KEY` in a `.env` file for live Signal B perplexity scoring. Without it, Signal B falls back to a heuristic.

---

## Project Layout

```
provenance_guard/
  app.py              # Flask app factory, limiter init
  audit_log.py        # Structured in-memory audit log
  classification.py   # Confidence scoring + transparency labels
  content_store.py    # Content status tracking
  extensions.py       # Flask-Limiter configuration
  validation.py       # Input validation
  routes/
    submit.py         # POST /submit
    appeal.py         # POST /appeal
    log.py            # GET /log
  signals/
    signal_a.py       # Structural signal
    signal_b.py       # Semantic signal (Groq + fallback)
tests/
  test_appeal.py
  test_classification.py
  test_log.py
  test_rate_limit.py
  test_submit.py
  test_transparency_labels.py
```
