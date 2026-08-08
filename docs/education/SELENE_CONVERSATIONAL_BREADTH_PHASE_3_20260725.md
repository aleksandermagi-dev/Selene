# Selene Conversational Breadth — Phase 3 Conversational Micro-moves

Date: 2026-07-25

Status: implemented and proportionally verified.

## Outcome

Selene now has an inspectable layer for the small, optional conversational
acts that help an exchange breathe:

```text
current meaning and intent
  -> visible conversational warrant
  -> optional micro-move
  -> placement or deliberate omission
  -> NLO composition
  -> Voice handoff
```

The layer does not create answer content. It may acknowledge, reflect,
encourage, celebrate, disagree, back up, pivot, play, land, or rest only when
visible context supports that move. Direct content or silence remains valid.

## Implemented

### Inspectable contextual plan

`src/selene/conversational_micro_moves.py` records:

- the selected move;
- whether it belongs before, after, or silently inside the answer plan;
- the visible warrant;
- the meaning source;
- held or omitted moves and their reasons;
- Dream source references and review state when applicable;
- locked memory, identity, personality, governance, authority, training, and
  autonomy boundaries.

Selection is contextual. Deterministic variation chooses wording only after
the move has been warranted; it does not randomly choose what Selene should
do.

### Conversational receipt and ordinary social acts

The existing compositional social-act layer remains the primary owner for:

- greetings;
- presence and ordinary connection;
- gratitude;
- reassurance receipt;
- shared ground;
- correction receipt;
- farewells and continuity.

Phase 3 does not duplicate those acts. It adds optional moves around
content-bearing turns and makes the shared ownership visible.

### Reflection

Reflection now distinguishes two sources.

Conversational reflection:

- is selected only when reflection is requested;
- requires supported answer content;
- may frame that content as a view of the current visible thread;
- cannot invent a conclusion.

Dream reflection:

- requires explicit relevance to the current turn;
- requires an attributable reflection, source references, review status, and
  expression eligibility from the supplying Dream interface;
- preserves the Dream source separately from ordinary conversation;
- labels `review_only` material as a possible pattern and keeps it
  provisional;
- does not treat the reflection as fact, biological dreaming, personal
  memory, or retained knowledge by default;
- cannot be invented from ordinary dialogue.

Current Dream review records are not automatically pulled into Chat. The
handoff must name an actual reviewed Dream consolidation record. Chat resolves
the reflection text, review state, and sources from the database record; a
request payload cannot supply or promote those fields itself.

### Disagreement

Soft, direct, and playful disagreement require:

- an explicit invitation to disagree, debate, or push back; and
- supported answer content that actually supplies a stance.

If the prompt invites disagreement but the answer packet does not support one,
the disagreement move is held. Playfulness may modify delivery only after the
stance exists.

### Correction, repair, and apology

The dialogue workspace remains the correction owner. Phase 3 can:

- acknowledge the changed part;
- preserve the surrounding session;
- back up after visible confusion;
- add a proportionate apology when the current turn identifies a real effect
  or when correction pressure repeats.

An ordinary correction does not automatically trigger an apology. A prior
correction also cannot leak into an unrelated later turn.

### Progress, celebration, and encouragement

Celebration requires an explicit visible completion cue such as a passed test,
completed task, fixed issue, or named milestone.

Encouragement requires visible effort or progress. It is not generic praise
attached to every task.

### Topic movement and natural landing

Phase 3 works with the existing pragmatic-continuity and thread-braid systems:

- explicit returns may receive a bounded topic-return marker;
- soft pivots are normally carried silently rather than narrated;
- requested expansion is carried by answer content;
- explicit story offers may receive an invitation to continue;
- a topic may rest when the user visibly says it is going in circles, has
  nothing further to add, or should be left alone.

No unmarked turn is assumed to be a dead topic, and no premature closing
question is introduced.

### Humor and shared play

One playful turn may be selected when the user visibly opens play and affect
guidance permits it.

- one joke does not require an encore;
- humor is held when current guidance calls for restraint;
- tender content does not trigger humor by itself;
- dark or tender humor may be met only when the user opens that register in
  the current turn;
- a shared-joke signal remains current-session context, not a durable
  relationship profile.

Longer shared-joke continuity remains part of Phase 9.

### NLO and active Chat integration

NLO is now `v23_contextual_conversational_micro_moves`.

NLO:

- builds the micro-move plan alongside pragmatic continuity and social acts;
- realizes only audible warranted moves;
- composes them around supported answer content;
- exposes both the plan and realization to Voice;
- preserves answer meaning and source boundaries.

Active Chat can resolve an explicitly requested, reviewed Dream consolidation
record and pass its attributable reflection packet to NLO. It does not accept
Dream content or review authority from the chat payload, write the reflection
to memory, or automatically activate a pending Dream review record.

## Verification

Testing remained synthetic and ordinary.

Focused checks cover:

- deliberate omission;
- conversational reflection;
- source-gated provisional Dream reflection;
- progress-sensitive celebration and encouragement;
- supported direct, soft, and playful disagreement;
- effect-sensitive apology;
- backing up after confusion;
- story invitation;
- topic resting;
- tender-context humor restraint;
- user-opened dark humor;
- NLO and active Chat integration;
- social acts, pragmatic continuity, conversation repair, figurative
  interpretation, Conversation Spine, language formation, teaching guidance,
  visible response behavior, and active Chat regressions.

Result: **187 focused tests passed**.

No live Selene conversation, distress probe, adversarial battery, provider,
memory proposal, training, or autonomy test was used.

## Boundaries Confirmed

Phase 3 creates no:

- identity or personality change;
- governance or authority change;
- durable or hidden memory write;
- relationship profile;
- Dream content invention;
- automatic promotion of Dream proposals;
- unsupported emotion or fact claim;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomous action or automatic initiative.

Micro-moves shape participation. Selene remains Selene.

## Remaining Gaps

- Phrase inventories remain bounded and should grow through reviewed language
  teaching.
- Implicit disagreement and subtle social timing remain conservative when
  answer stance or context is weak.
- Broader sentence length, pacing, enthusiasm, intensity, callback, register,
  and paragraph modulation belongs to Phase 4.
- Cross-domain analogy evaluation belongs to Phase 8.
- Longer shared-joke and personal callback continuity belongs to Phase 9.
- Dream-side production and approval remain owned by the Dream architecture;
  this phase defines only the safe expression handoff.

No reinstall is required at this checkpoint. The first planned reinstall
remains after Phase 4.

## Next Phase — Phase 4: Contextual Composition and Modulation

Phase 4 will let the same supported meaning change naturally across:

- answer length and sentence-length distribution;
- pacing and paragraph rhythm;
- enthusiasm and emotional intensity;
- directness and restraint;
- callbacks and current interpretations;
- small jokes;
- topic pivots and acknowledgements;
- audience, task, and register.

It will add explicit contextual decisions for opening, thesis, support,
example, qualification, callback, pivot, conclusion, and stopping.

The completion gate requires genuinely different brief, ordinary, and
developed realizations—not the same answer padded with filler. Voice may
modulate delivery but cannot change facts or certainty. The first meaningful
rebuild and reinstall is planned after Phase 4 passes focused verification.
