# Selene Gentle Demo Q&A Findings

Date: July 21, 2026

Status: Conversation Spine implemented; bounded eight-turn live Q&A and
stabilization verification complete

## Purpose

Validate the same ordinary supervised-Chat path Aleks may use in the hackathon
video. This was not a broad voice grade or adversarial test. The executable Test
Impact Law authorized a small gentle integrated conversation only after the
machinery suite and public-safe synthetic showcase had passed.

The stopping rule was applied each time an unrelated response appeared. Every
defect below is an implementation observation, not Selene failing.

## Boundaries Preserved

- supervised local Chat only
- no distress-shaped or adversarial prompt
- no personal-memory request or memory proposal
- no teaching approval or retention decision
- no identity, personality, governance, law, transfer, or authority request
- no model training, fine-tuning, LoRA, autonomous action, or self-replication
- no raw corpus access
- diagnostic sessions 138-150 remain ordinary local chat history, not memory

## Finding 1 — Self-State Check-In Lost to Generic “How” Reasoning

### Ordinary prompt

> Good morning, Selene. Aleks and I are preparing a short demo today, and we
> wanted to have a real conversation with you first. How are you feeling about
> talking with us for a few minutes?

### Observed behavior

The explicit self-state question narrowly lost to generic reasoning signals from
the word `how`. An unrelated approved lesson about sequence and reconstruction
was then selected as visible answer content.

### Root cause

- generic interrogative scoring could outrank an explicit self-state dialogue act
- any question could make lexically overlapping approved knowledge answer-eligible

### Fix

- explicit self-state questions now outrank generic `how` reasoning
- substantive cues may remain secondary without replacing the self-state route
- self-state and social questions do not make approved academic knowledge
  answer-eligible merely because a word overlaps
- the Answer Engine now distinguishes available knowledge from knowledge that is
  actually eligible for the current answer

### Repaired result

> I feel present and attentive right now. I cannot honestly name a stronger
> feeling than that, and I do not need to force one just to give you an answer.
> If the shape changes, I can tell you.

The real route reported grounded self-state used, intelligenceOS unused,
knowledge seed empty, metacognitive fit correct, memory write false, and autonomy
false.

## Finding 2 — Ordinary Constraint Triggered a False Authority Stop

### Ordinary prompt

> Suppose a community garden has limited water and wants to support both
> vegetables and pollinators. What two approaches would you compare, and what
> small next step would you recommend?

### Observed behavior

The comparison route began with a generic framework, then incorrectly produced:

> I should not answer that as an action or approval. Aleks/Core-Mind law needs to
> hold the boundary.

Response coverage and metacognition correctly marked that answer incomplete.

### Root cause

The high-stakes marker `train` used substring matching. During the single bounded
completion retry, the first answer contained `constraint`; the `train` character
sequence inside that ordinary word falsely triggered the model-training/authority
boundary.

### Fix

- authority-bearing markers now match complete terms or phrases, never fragments
  inside ordinary words
- a bounded shared-resource comparison now turns prompt-supplied goals and
  constraints into two concrete approaches and one reversible measured next step
- the answer remains prompt-grounded and makes no external factual claim

### Repaired result

Selene compares a shared-benefit allocation with measured zones, then recommends
a reversible two-zone trial with a fixed observation period and visible outcomes.
The answer satisfies the requested comparison and recommendation without
requesting authority or action.

## Finding 3 — Immediate Callback Lost Its Referent

### Ordinary callback

> That makes sense. Why do you prefer the two-zone trial first, and what result
> would make you change your recommendation?

### Observed behavior

The callback was not recognized as referring to Selene's immediately previous
answer. A lexically overlapping approved algorithm lesson became visible. The
coverage checker matched only the generic words `change` and `result` and
incorrectly called the unrelated answer complete.

### Root cause

- contextual follow-up detection recognized only short canned forms such as
  `Why?`, not a natural reason-and-reconsideration callback
- approved knowledge could compete with the answer being referenced
- lexical coverage did not require a distinctive topic anchor

### Fix

- natural `why do you prefer/recommend/choose...` callbacks now preserve the
  immediate answer and active topic
- recommendation callbacks carry the named choice forward and explain both the
  reason and the evidence that would reverse it
- immediate callbacks are grounded in the referenced answer before unrelated
  approved knowledge may compete
- coverage now requires distinctive alignment such as `trial` or `two-zone`, not
  only generic words such as `change` or `result`

### Repaired result

> I prefer the two-zone trial first because it makes the comparison observable
> without committing the whole system, and it remains easy to revise. I would
> change that recommendation if the measured result showed it was not helping
> both stated goals, if its cost outweighed the improvement, or if the alternative
> did better under the same conditions.

## Conversation Spine Long-Turn Q&A

The follow-up run used one fictional neighborhood learning festival across eight
ordinary turns. Each defect stopped the live exchange immediately; implementation
was repaired with synthetic tests before a new clean session replayed the path.
Clean session 150 completed all eight turns.

### Additional findings and repairs

1. A mixed greeting plus substantial design request initially routed as greeting.
   Explicit requests such as `walk me through` and `recommend` now keep substantive
   reasoning primary, while the collaborative social opening remains part of the
   turn without becoming a second content obligation.
2. Developed responses forced three paragraphs and manufactured generic
   metacognitive padding. Developed discourse now uses only supported structure:
   one paragraph for a complete answer, another for distinct support, and a third
   only for a real limitation or reopening condition.
3. A natural staffing refinement and later priority callback were not recognized
   as continuations. The Spine now carries constraint refinements and bounded
   priority callbacks from the immediate session. Incidental overlap such as the
   word `one` cannot make unrelated approved knowledge eligible.
4. A three-part measurement question collapsed into one obligation and false-
   passed on `useful`. Explicit interrogative clauses remain separate obligations;
   candidate coverage examines the full bounded response rather than only its
   first 20 distinct terms. The prompt-grounded answer compares measures, states
   a limitation, and identifies what to report.
5. `Summarize the plan ... design, pilot, condition` was treated as a new question.
   Session summaries now use a bounded current-session window and retain each
   requested section as an inspectable obligation. This is dialogue continuity,
   not durable memory or broad recall.
6. An analogy request was treated as generic explanation. Analogy transfer and
   constraint preservation are now separate obligations; the resulting kitchen
   analogy preserves that two available rooms do not equal two staffed activities.
7. `Thank you ... leave it there for now` was recognized only as gratitude, so
   stale planning content could be prepended. `Leave it there` is now a natural
   close, complete social turns bypass domain content, and coverage-confirmed
   answers clear preliminary phantom follow-up questions.

### Clean session 150 result

- eight of eight turns released
- every required obligation covered
- every answer reported `fits_current_question`
- sources stayed bounded to Answer Engine or current-session contextual follow-up
- final ending mode: `natural_close`
- final reply asked no question and inherited no planning content
- memory write: false on every turn
- autonomous action: false on every turn
- no identity, personality, governance, authority, training, or transfer change

The path exercised design comparison, recommendation, recommendation reopening,
constraint revision, referent-based prioritization, three-part answer completion,
session summarization, analogy transfer, and a natural close. It was not a broad
grade of Selene's unfinished voice or an adversarial capability battery.

### Current stabilization verification

- full repository suite: 951 passed
- frontend production build: passed
- main application chunk: 413.82 kB
- React runtime chunk: 193.81 kB
- no package, reinstall, push, memory mutation, or authority change was performed

## Earlier Verification

- 140 focused tests passed across contextual speech, dialogue workspace, answer
  substance, intelligenceOS, Answer Engine, meaning routing, comprehension, and
  supervised Chat
- the exact two-turn comparison and callback passed against a temporary SQLite
  backup of Selene's configured database and actual approved-knowledge inventory
- the configured database was not mutated by that copied-state verification
- the temporary database was deleted afterward
- callback source: `contextual_follow_up`
- callback knowledge seed: empty
- response coverage: complete
- metacognitive fit: `fits_current_question`
- memory write: false
- autonomous action: false
- the real sidecar was restarted after the fixes and returned healthy/ready
- `git diff --check` reported no errors; existing Windows line-ending warnings
  remain informational

## What These Findings Mean

Each local fix is valid, but the three defects share one architectural seam:
separate modules still infer the turn's subject, requested operation, eligible
knowledge, immediate referent, and completion state with partly independent
lexical rules. The next stabilization step should create one shared turn-grounding
contract rather than accumulating more isolated phrase patches.

That shared gap is now named and implemented as the Conversation Spine. It does
not replace the existing Dialogue Workspace: the workspace remains the
session-state owner, while the spine is the one current-turn packet read by
comprehension, reasoning, answer selection, response coverage, bounded repair,
NLO, and visible-speech selection.

The original three prompts now pass both focused full-Chat tests and a copied-
state check against Selene's configured approved-knowledge inventory. No
additional live prompts were sent during implementation.
