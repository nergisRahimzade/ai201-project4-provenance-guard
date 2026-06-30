# Provenance Guard — Planning

### Architecture narrative

This is the path a single piece of text takes from submission to the label a reader sees, naming every component it touches.

A creator sends a `POST /submit` request containing their text. The endpoint first runs **input validation** — checking the text is non-empty and within accepted length limits. Once validated, the raw text is passed into the **detection pipeline**, where it is run through two signals independently:

- **Signal 1** computes a structural score from the raw text (type-token ratio and punctuation density).
- **Signal 2** computes a semantic/statistical score from the raw text (perplexity / language model confidence).

Both signal scores are passed into **confidence scoring**, which combines them into a single confidence value between 0 and 1. This combined score is passed to the **transparency label** component, which selects one of five label variants and builds the plain-language text a reader will see.

The full decision record — including both signal scores, the combined confidence score, and the label text — is written to the **audit log**. Finally, the **response** is returned to the creator, containing the decision record, the confidence score, and the transparency label, along with a `content_id` they can use later if they want to appeal.

If a creator disputes the result, they call `POST /appeal` with their `content_id` and their reasoning. The system looks up the original decision **by content_id**, updates the **content record**'s status to `"under review"`, appends the appeal (along with the original decision) to the **audit log**, and returns a response confirming the new status. No automated re-classification happens at this stage — the audit log is what a human reviewer will use to make the final call.

---

### Detection Signals

#### Signal 1 (structural): Type-token ratio & punctuation density

**What it measures**
- Type-token ratio (TTR): the diversity of vocabulary, i.e. unique words divided by total words.
- Punctuation density (PD): the frequency of punctuation usage relative to text length.

**Why it differs between human and AI writing**
- AI-generated text: low TTR, low PD. Models favor common, "safe" vocabulary and produce clean, predictable punctuation patterns.
- Human-written text: high TTR, high PD. Humans reach for varied vocabulary and use punctuation more expressively (em-dashes, ellipses, parentheticals, exclamation points).

**Blind spots**
- AI instructed to use varied vocabulary and em-dashes will evade this signal.
- A human writing a technical report will naturally produce low TTR and low PD, scoring as if AI-written.

**Output**
- `score_signal_A`: number between 0 and 1; 1 = more AI-like, 0 = more human-like

#### Signal 2 (semantic): Perplexity & language model confidence

**What it measures**
- How predictable the text is to a language model — i.e., how confidently a model could have predicted each next word given the preceding context.

**Why it differs between human and AI writing**
- AI-generated text tends to have lower perplexity — it is more predictable, since models are optimized to produce high-probability token sequences.
- Human writing often contains more surprising word choices, producing higher perplexity.

**Blind spots**
- AI text that has been edited by a human can take on human-like perplexity.
- A professional human writer (technical writer, journalist) may also produce fairly predictable prose, scoring as if AI-written.

**Output**
- `score_signal_B`: number between 0 and 1; 1 = more AI-like, 0 = more human-like


#### Confidence Score

**Output**
- `confidence_score`: `0.3 × score_signal_A + 0.7 × score_signal_B`

- For both signals, a score of 1.0 represents the most AI-typical value observed, and 0.0 represents the most human-typical value observed, so the two scores are directly comparable and combinable into a single weighted score.

---

## Uncertainty Representation

A confidence score is not a measure of certainty that AI wrote the text — it's a measure of how strongly the combined signal evidence leans toward AI-generated or human-written writing. A score of 0.6 doesn't mean "60% chance this is AI." It means the combined evidence leans mildly toward AI-generated, but not strongly enough to be conclusive, and a reader should treat the result as an open question rather than a verdict.

**Why signal B is weighted more heavily**

`confidence_score = 0.3 × score_signal_A + 0.7 × score_signal_B` was chosen because Signal B (perplexity / language model confidence) proved more reliable than Signal A (structural features) at distinguishing human-written and AI-generated text in practice. Because I noticed my program wasn't being accurate with confidence score, due to signal B being better at detecting human and AI than A, I changed the formula to weigh more towards signal B score. When the two signals disagree, the weighted score follows Signal B more closely — so mixed evidence resolves toward whichever direction the semantic signal points, rather than always collapsing to the midpoint.

**What a mid-range score means**

| Range | Label | What it represents |
|---|---|---|
| `confidence_score ≥ 0.8` | Clearly AI-generated | Both signals strongly point toward AI-typical patterns |
| `0.65 ≤ confidence_score < 0.8` | Likely AI-generated | Evidence leans toward AI-generated, but not conclusively |
| `0.45 < confidence_score < 0.65` | Uncertain | Signals disagree, or evidence is mixed |
| `0.2 < confidence_score ≤ 0.45` | Likely human-written | Evidence leans toward human-written, but not conclusively |
| `confidence_score ≤ 0.2` | Clearly human-written | Both signals strongly point toward human-typical patterns |

The uncertain band spans the middle of the score range. Narrower bands at the extremes would force borderline cases into a false "clearly" label, which is exactly the failure mode the false positive scenario trace describes.

---

### False Positive Scenario Trace

Consider a human technical writer who submits a clearly-written, plainly-worded report.

- Signal 1 returns low TTR and low PD — they reuse domain terminology and use minimal punctuation variety.
- Signal 2 returns low perplexity — their wording is highly predictable, technical writing by nature avoids surprising phrasing.

Both signals agree and point toward AI, but for the wrong reason — neither captures that this is simply a professional human writing style. The confidence score lands high (toward the AI end), and the resulting label would read as Clearly AI-generated or Likely AI-generated, even though the content is human-written.

This is why the **appeal workflow** matters: the creator submits their reasoning (e.g., "I am a technical writer; this is my own work, plainly written"), the content status flips to `"under review"`, and the full audit trail — both signal scores and the appeal reasoning — is preserved for a human reviewer to make the final call. The system does not auto-correct; it surfaces the case for review.

---

### Anticipated Edge Cases

- **Edge case 1**: A human writer writes a clearly-written, plainly-worded report.
- **Edge case 2**: An AI writer writes a report that uses varied vocabulary and punctuation upon being instructed to do so.
- **Edge case 3**: A human writer writes a technical (academic, scientific, legal etc.) report that has predictable words and phrases.
- **Edge case 4**: An AI writer writing being edited by a human.
- **Edge case 5**: A human writer writing a heavily quoted or dialogue-heavy fiction that uses repeated phrases like "She said..." or "He asked...".
- **Edge case 6**: Short submissions because TTR is statistically unstable on small samples.
- **Edge case 7**: Formulaic genres written by humans, like wedding speeches or cover letters etc.
- **Edge case 8**: A human writer who is writing in a language that is not their mother tongue.

---

### API Surface

**`POST /submit`**
- Accepts: `{ text: string }`
- Returns: `{ content_id: string, score_signal_A: number, score_signal_B: number, confidence_score: number, transparency_label: string }`

**`POST /appeal`**
- Accepts: `{ content_id: string, reasoning: string }`
- Returns: `{ appeal_id: string, status_update: string }`

**`GET /log`**
- Returns: structured JSON list of audit log entries (decision records and appeals)
- Each decision entry includes: `timestamp`, `content_id`, `attribution_result`, `confidence`, `score_signal_a`, `score_signal_b`, and `appeal_filed`
- Each appeal entry includes: `timestamp`, `content_id`, `appeal_id`, `creator_reasoning`, and a snapshot of the `original_decision`

**Rate limiting**
- `POST /submit` is limited to 10 requests per minute and 100 requests per day (Flask-Limiter, in-memory storage)

---

### Transparency Label Variants

| Range (`confidence_score = cs`) | Label |
|---|---|
| `cs ≥ 0.8` | Clearly AI-generated |
| `0.65 ≤ cs < 0.8` | Likely AI-generated |
| `0.45 < cs < 0.65` | Uncertain |
| `0.2 < cs ≤ 0.45` | Likely human-written |
| `cs ≤ 0.2` | Clearly human-written |

**Label text shown to readers**

- **Clearly AI-generated**: "Our system is clearly confident that this content was written by an AI."
- **Likely AI-generated**: "Our system is likely confident that this content was written by an AI."
- **Uncertain**: "Our system is uncertain whether this content was written by an AI or a human."
- **Likely human-written**: "Our system is likely confident that this content was written by a human."
- **Clearly human-written**: "Our system is clearly confident that this content was written by a human."

---

### Diagrams

#### Submission Workflow

```
POST /submit
     │  raw text
     ▼
Validate input
     │  valid text
     ├──────────────┐
     ▼              ▼
 Signal 1        Signal 2
 (score A)       (score B)
     │              │
     └──────┬───────┘
            ▼
   Confidence scoring
   (combined score, 0–1)
            │  combined score
            ▼
   Transparency label
   (label text)
            │  decision record
            ▼
       Audit log
            │  full record
            ▼
        Response
```

#### Appeal Workflow

```
POST /appeal
     │  content_id + reasoning
     ▼
Validate content_id
(lookup by content_id)
     │  content record
     ├──────────────┐
     ▼              ▼
Status update    Audit log
(set to          (append appeal +
"under review")   original decision)
     │              │
     └──────┬───────┘
            ▼
        Response
        (full record)
```

- Only the creator can appeal the decision. 
- They have to provide a valid `content_id` and a valid `reasoning` for the appeal.
- The system will validate the `content_id` and the `reasoning` and return a response with the new status of the content and `appeal_id`.
- The status of transperancy label will be set to `Under Review` once an appeal is commited.
- The appeal will be added to the audit log with the `content_id`, date and time of appeal, status of transparency label, original decision, `appeal_id` and the new reasoning.
- After the appeal is logged to the audit log, the last will be a human reviewer making the final decision to decide whether to change the transparency label or keep the original decision.
- A human reviewer is needed because the model already has a high confidence that this content was written by an AI or a human. Once an appeal is made, this means that the AI might have a chance of being wrong. A human reviewer will be able to judge the content and the appeal to decide whether the content was written by an AI or a human.

---

### AI Tool Plan

- **M3 (submissions endpoint + signal 1)**: 
  - I will give the AI the following parts of the planning document:
    - Architecture Narrative
    - Detection Signals
    - False Positive Scenario Trace
    - Anticipated Edge Cases
    - API Surface
    - Diagrams
  - I will ask the AI to generate the code for the submissions workflow and endpoint and signal 1.
  - I will verify the output by testing with a few inputs directly before wiring into the endpoint.

- **M4 (signal 2 + confidence scoring)**: 
  - I will give the AI the following parts of the planning document:
    - Architecture Narrative
    - Detection signals
    - Anticipated Edge Cases
    - False positive scenario trace
    - Transparency label variants
    - Diagrams
  - I will ask the AI to generate the code for the signal 2 and confidence scoring.
  - I will verify the output by checking if the scores vary meaningfully between clearly AI and clearly human text.

- **M5 (production layer)**: 
  - I will give the AI the following parts of the planning document:
    - Architecture Narrative
    - Transparency label variants
    - Diagrams
  - I will ask the AI to generate the code for the appeal workflow and endpoint.
  - I will verify the output by testing all five label variants are reachable and that an appeal updates status correctly.

---
