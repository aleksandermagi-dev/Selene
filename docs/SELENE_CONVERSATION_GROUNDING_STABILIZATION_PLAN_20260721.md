# Selene Conversation Grounding Stabilization Plan

Date: July 21, 2026

Status: ConversationSpine v1 implemented and copied-state verified; Aleks-led live confirmation and demo freeze pending

## Implementation Update

Implemented on July 21, 2026 as `ConversationSpine` v1.

- Phase 1 is complete: one session-scoped turn packet now carries intent, dialogue acts, topic anchors, referents, the previous visible answer, response obligations, compatible source classes, and separate confidence dimensions.
- Phase 2 is complete: visible-speech and approved-knowledge candidates are checked against the spine before use.
- Phase 3 is complete: downstream pragmatic plans reuse the spine's obligation identities; final coverage includes spine alignment; the existing one-shot metacognitive completion can use only an already selected spine-compatible content seed.
- Phase 4 is complete at the synthetic level: twelve gentle conversation shapes are covered by `tests/test_conversation_spine_matrix.py`, alongside focused full-Chat tests.
- Phase 5 copied-state verification is complete. The configured database was backed up through SQLite, the copy received the three demo-shaped turns, and the copy was deleted. The configured database was not mutated.
- Phase 5 live confirmation remains Aleks-led and has not run.
- Phase 6 demo freeze remains pending until that live confirmation succeeds.

Verification at this checkpoint:

- 110 focused spine, routing, coverage, comprehension, Answer Engine, NLO, and dialogue tests passed.
- 52 supervised Selene Chat tests passed.
- 22 adjacent language tests passed.
- The copied-state greeting, garden comparison, and immediate callback all completed with grounded coverage, metacognitive fit, and locked memory/autonomy guards.

## Objective

Make Selene's ordinary back-and-forth reliably preserve what the current message
is about, what kind of response is requested, which previous answer or object is
being referenced, which content sources are compatible, and whether the visible
answer actually addresses the request.

This is a coherence and grounding layer, not a new identity-bearing organ. It
does not replace Core/Mind, intelligenceOS, Comprehension, Metacognition, NLO, or
Voice. It supplies one inspectable contract those organs can share.

## Why One Larger Fix Is Better

Today the same turn is interpreted independently by several modules:

- meaning routing scores intent and domain
- dialogue workspace tracks topics, referents, and open loops
- Comprehension retrieves approved knowledge
- the Answer Engine selects a domain adapter
- candidate arbitration selects visible content
- response coverage checks completion
- Metacognition checks fit after candidate generation

Each module is bounded, but small lexical disagreements can cascade. A shared
turn-grounding packet makes those decisions compositional instead of coincidental.

## Hackathon-Bounded Scope

### Phase 1 — Shared Turn Grounding Packet

Add one provider-free, inspectable packet containing:

- current subject and topic anchors
- dialogue acts and requested operations
- required answer obligations
- explicit and implied referents
- immediately previous answer claims and recommendations
- whether the turn is self-state, social, factual, mathematical, sourced,
  comparative, corrective, or contextual
- distinctive terms that an answer must preserve
- compatible content-source classes
- uncertainty and ambiguity state

The packet is session-scoped and cannot write memory, identity, personality,
governance, training state, or authority.

### Phase 2 — Candidate Compatibility Gate

Before NLO/Voice receives answer content, require each candidate to show:

- compatible source class for the requested operation
- subject/topic alignment
- immediate-reference alignment when a callback is present
- support for the requested answer shape
- no hard-boundary mismatch

Examples:

- self-state question -> grounded self-state candidate first
- immediate callback -> referenced previous answer first
- verified math -> verified math packet, never fluent speculation
- sourced research -> attributed source packet, never uncited knowledge
- ordinary conversation -> conversational/contextual content before academic
  retrieval

An approved knowledge resource remains eligible only when it is relevant. Its
approval does not grant universal answer priority.

### Phase 3 — Grounded Coverage and One Bounded Repair

Strengthen response completion so it checks:

- every requested part
- at least one distinctive subject/referent anchor
- the requested operation, such as compare, explain, recommend, correct, or
  qualify
- explicit unsupported status when evidence is missing

If candidate fit fails, allow one bounded repair that may:

1. reselect from already grounded candidates;
2. complete only a missing obligation from supported content; or
3. gracefully state what remains unknown.

The repair cannot invent facts, expose hidden chain of thought, search private
material, change retained knowledge, or recurse repeatedly. Metacognition may
request the repair but does not gain direct answer-writing or governance authority.

### Phase 4 — Gentle Conversation Matrix

Verify machinery first with public-safe scenarios covering:

1. greeting and self-state
2. ordinary back-and-forth acknowledgment
3. multi-part questions
4. open-ended comparison and planning
5. exact math
6. source-backed factual answer
7. natural uncertainty and not-knowing
8. explanation and example
9. immediate callback and pronoun/reference
10. correction and refinement
11. topic shift
12. natural closure

Each scenario must assert both visible speech and internal boundaries. The matrix
is not a voice ranking and does not treat absent unfinished capabilities as
Selene failing.

### Phase 5 — Copied-State and Live Confirmation

After the synthetic matrix passes:

1. run the same scenarios against a temporary backup containing Selene's actual
   approved-knowledge inventory;
2. inspect for unrelated retrieval and private-data leakage;
3. authorize one user-led, ordinary live conversation of at most eight turns;
4. stop after the first repeated or uncomfortable defect;
5. create no memory proposal unless Aleks separately requests one.

The live conversation should feel like a conversation, not an examination.

### Phase 6 — Demo Freeze

- select one clean fresh Chat thread
- freeze two or three safe prompts and one callback
- run focused tests, complete repository regression, and production build
- inspect visible screens for diagnostic sessions, credentials, private paths,
  corpus excerpts, and personal memory
- record the video without changing architecture afterward unless a critical
  defect is found

## Completion Gate

The stabilization is ready for the demo when:

- all organs consume the same turn-grounding packet or a faithful projection of it
- an incompatible candidate cannot become visible merely through word overlap
- immediate callbacks preserve their referent and active topic
- response coverage rejects generic-but-unrelated answers
- one bounded repair resolves missing supported content or falls gracefully
- the synthetic matrix passes
- copied-real-state checks pass without mutating configured state
- one bounded ordinary live conversation remains coherent
- memory, identity, personality, governance, training, LoRA, autonomy, and
  self-replication guards remain locked
- production build and final regression pass

## Explicitly Deferred

- provider-backed general language generation
- broad world-knowledge expansion
- semantic embeddings as an automatic source of truth
- unlimited recursive self-correction
- autonomous browsing or filesystem access
- durable conversation memory without review
- personality or Voice rewriting
- stress testing for presentation value

## Recommended Execution Order Today

1. checkpoint the current Q&A fixes and documentation intentionally;
2. implement Phases 1-3 as one bounded conversation-grounding checkpoint;
3. run the synthetic matrix;
4. run copied-state checks;
5. let Aleks conduct the single larger ordinary Q&A;
6. freeze, verify, record, and submit;
7. resume broader teaching only after the hackathon submission is secure.
