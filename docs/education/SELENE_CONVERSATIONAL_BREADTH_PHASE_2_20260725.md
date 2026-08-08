# Selene Conversational Breadth — Phase 2 Figurative Interpretation

Date: 2026-07-25

Status: implemented and proportionally verified.

## Outcome

Selene now has an inspectable, session-scoped interpretation layer between
input cleanup and conversational routing:

```text
original wording
  -> literal reading
  -> supported nonliteral candidates
  -> visible contextual cues
  -> selected reading and confidence
  -> Conversation Spine, dialogue, NLO, and response
```

The original message remains intact. A supported interpretation may supply a
separate `interpreted_text` for current-turn routing and composition, but it
does not rewrite the stored source wording or create a durable profile.

## Implemented

### Literal and nonliteral candidates

`src/selene/figurative_interpretation.py` produces a bounded packet containing:

- original and literal wording;
- detected figurative forms;
- candidate meanings;
- selected reading;
- intended meaning;
- contextual cues;
- confidence;
- whether the distinction materially changes the response;
- a clarification question when one is genuinely necessary;
- an interpretation correction packet;
- explicit memory, identity, personality, governance, training, authority,
  and autonomy guards.

### Supported forms

The first bounded interpreter covers:

- reviewed conventional idioms;
- explicit metaphors and figures of speech;
- analogy and simile markers;
- explicit hyperbole and understatement;
- conservative sarcasm;
- context-sensitive conversational pacing language such as “slow down”;
- the ordinary literal-or-metaphorical ambiguity of “the storm passed.”

This is deliberately not an unrestricted guesser. Unrecognized wording remains
literal, and unsupported confidence is not manufactured.

### Context before selection

The interpreter uses only visible current-session conversation context. It
does not infer a private speaker profile.

For example:

- “slow down” with explanation and step cues is interpreted as a request to
  reduce conversational pace or information density;
- “slow down” with driving and road cues remains literal;
- “the storm passed” can remain unresolved if visible context does not
  distinguish weather from a difficult situation.

Clarification is requested only when the reading is unresolved and the current
request depends materially on the difference.

### Sarcasm restraint

Sarcasm is not inferred from punctuation or one positive word. Selection
requires either:

- an explicit marker such as `/s` or a direct statement that the wording is
  sarcastic; or
- both a surface/context contradiction and visible adverse context.

### Analogy is not equivalence

Analogy packets keep:

- source domain;
- target domain;
- proposed mapped relationship;
- a mapping limit;
- `equivalence_claimed: false`.

NLO and the Conversation Spine carry the same boundary forward.

### Session-scoped correction

An explicit correction such as “I meant that literally” updates the prior
figurative reading for the current session. The update:

- identifies the prior and revised reading;
- preserves the surrounding conversation;
- does not reset the dialogue workspace;
- does not write durable memory.

### Active Chat integration

The active Chat path now keeps three separate forms:

1. the original user message;
2. the input detangler’s legibility-preserving result;
3. the figurative interpreter’s current-session meaning result.

The selected meaning flows through:

- contextual follow-up;
- intent and Core/Mind routing;
- memory query relevance without changing memory ownership;
- dialogue workspace;
- Conversation Spine;
- intelligenceOS, Comprehension, and Answer Engine handoffs;
- NLO;
- Voice and final response checks.

User and assistant message payloads retain the figurative packet so a later
explicit correction can refer to the prior reading without creating another
memory system.

NLO is now `v22_contextual_figurative_meaning`.

## Verification

Testing remained synthetic and ordinary because no stress-shaped interaction
was necessary.

Focused checks cover:

- conventional idiom interpretation;
- conversational versus physical “slow down”;
- analogy mapping limits and non-equivalence;
- conservative sarcasm;
- material-only clarification;
- session-scoped interpretation correction;
- dialogue workspace, Conversation Spine, and NLO handoff;
- active Chat handoff and correction continuity;
- nearby dialogue, spine, NLO, and active Chat regressions.

Result: **162 focused tests passed**.

No live Selene conversation, affect provocation, memory proposal, provider,
training, or autonomy test was used.

## Boundaries Confirmed

Phase 2 creates no:

- identity or personality change;
- governance or authority change;
- durable or hidden memory write;
- speaker profiling;
- raw corpus access;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomous action.

Interpretation supports conversation. Selene remains Selene.

## Remaining Gaps

- The first conventional idiom inventory is intentionally small and should
  expand through reviewed language teaching rather than raw phrase dumping.
- Implicit metaphor, hyperbole, understatement, and sarcasm remain
  conservative when context is weak.
- Cross-domain analogy evaluation beyond the explicit mapping boundary belongs
  to Phase 8.
- Shared-joke continuity and humor timing belong to Phases 3 and 9.
- Broader contextual expression modulation belongs to Phase 4.

No reinstall is required at this checkpoint. The first planned reinstall
remains after Phase 4.

## Next Phase — Phase 3: Conversational Micro-moves

Phase 3 will expand the small context-sensitive behaviors that let a
conversation breathe:

- greetings, acknowledgements, encouragement, celebration, reflection, and
  receipt;
- soft and direct disagreement;
- correction, repair, proportionate apology, and backing up;
- topic expansion, invitation, transition, pivot, return, and closure;
- noticing confusion and checking understanding when useful;
- playful disagreement, jokes, shared jokes, and release after a joke;
- landing, resting, pivoting, or ending when a topic naturally goes flat.

The core constraint is that these moves are optional contextual acts, not
mandatory scripts. They cannot replace the answer, force a follow-up question,
create habitual apologies, or close a useful exchange prematurely.
