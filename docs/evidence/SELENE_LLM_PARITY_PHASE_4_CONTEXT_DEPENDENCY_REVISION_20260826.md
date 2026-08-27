# Selene LLM-Parity Phase 4 — Context and Dependency Revision

Date: 2026-08-26

Status: implemented and focused-verification complete in the current worktree;
not yet committed, built, packaged, or reinstalled.

## Outcome

Selene's current-session correction path now has an executable proposition and
dependency record rather than only a descriptive instruction to preserve what
still fits.

When a visible premise or result is corrected, the Dialogue Workspace can now:

1. bind the correction to a visible current-session proposition;
2. preserve the prior proposition as revision ancestry;
3. supersede the affected premise;
4. invalidate only results that depend on it;
5. keep unrelated active propositions intact;
6. request one recomputation from the responsible existing answer owner;
7. close that recomputation only when its corrected result appears in the
   visible response; and
8. retain a precise held state when the target, corrected input, owner result,
   or visible realization is missing.

Ordinary correction remains ordinary revision. It is not a memory write,
identity event, self-conflict, failure state, or reason to reset the whole
conversation.

## Session Proposition Ledger

`session_proposition_ledger.py` is bounded connective tissue owned by the
existing Dialogue Workspace. It is not a new organ or truth authority.

The ledger records only visible current-session structures:

- proposition ID, kind, text, and lifecycle state;
- declared or typed `depends_on` links;
- visible source, turn, thread, landmark, and source references;
- replacement and recomputation ancestry;
- active, superseded, and invalidated proposition sets;
- the current revision event; and
- the exact recomputation state.

Typed claim/evidence packets provide premise and basis links when available.
Visible response landmarks provide bounded result propositions. The ledger is
stored inside the Dialogue Workspace's existing `state_json`; no new durable
memory table or hidden reasoning store was introduced.

The active set is bounded to 64 propositions and revision ancestry to 32 stale
propositions. Up to 24 revision events are retained in the current session.

## Selective Revision

A correction first uses explicit proposition IDs when supplied. Otherwise it
matches the corrected target against visible active propositions and selects
the most recent strongest match. It does not rewrite every historical mention
of a shared word.

If an older session predates the ledger and has no recorded propositions, the
visible prior claim carried by the existing epistemic-revision plan may be
introduced as ancestry. Once a ledger exists, an unknown target is held as
`held_target_not_found`; it is not invented.

Transitive descendants are discovered through typed dependency edges. The
affected premise becomes `superseded`, its dependent results become
`invalidated`, and unrelated active propositions remain eligible for context.

## Recalculation Truth

Recognizing a correction does not count as recalculating its result.

The existing epistemic-revision coordinator still classifies the change and
preserves model ancestry. The Phase 4 ledger identifies what must be rerun. An
existing operation-capable owner must then return the corrected application,
and Phase 3 semantic fulfillment must confirm that application appears in the
visible answer.

Only then does the ledger create a new `recomputed` result linked to:

- the revised premise; and
- the invalidated result it replaces.

If the owner or visible application is missing, recomputation remains
`held_pending_owner_result`. That state persists across later turns instead of
silently resetting.

## Continuity and Stale-State Exclusion

The Conversation Continuity resolver and Conversation Spine now observe the
ledger before grounding a reply:

- landmarks tied to invalidated or superseded propositions are excluded;
- the immediate prior answer is not reused as current grounding when it is the
  answer being revised;
- a referent aimed at a superseded proposition is rebound to its explicit
  revised proposition when one exists;
- otherwise the referent becomes a material ambiguity instead of a guess;
- dependency-revision turns ground from the revised premise, not the stale
  answer; and
- immediate creative follow-ups continue to use their actual prior answer
  rather than unrelated lexical landmark matches.

The correction loop lifecycle still preserves unrelated open work and retires
the affected stale obligation. Session summaries receive only active eligible
landmarks from the Conversation Spine.

## Integration Repairs Found by the Gate

The focused long-turn correction replay exposed three existing integration
issues:

1. `small correction` was interpreted as an explicit short-answer request.
   Response-shape parsing now treats `small`, `little`, or `tiny` as brevity
   only when they modify an answer, reply, response, summary, explanation,
   paragraph, or note. `short`, `brief`, and `concise` remain direct brevity
   requests.
2. Existing correction-reconstruction output could visibly apply a correction
   without being identified as the operation owner's result. That existing
   current-session source is now typed as the correction application; the
   ledger itself still does not generate prose.
3. Existing prompt-grounded answers containing `because` could visibly supply
   a reason while their semantic units were labeled only as a sequence. Plain
   operation units now preserve causal and conditional relations, allowing the
   strict Phase 3 verifier to recognize the actual reason.

These were source-shape and ownership repairs. No new phrase-specific answer
was added.

## Inspectable Routes

- `session_propositions.status`
- `session_propositions.revision.preview`
- `session_propositions.response.preview`

Ordinary Chat also exposes the resulting ledger directly and inside Dialogue
Workspace and Conversation Spine telemetry.

## Verification

The proportional Phase 4 gate passed 167 focused tests covering:

- proposition creation and bounded session persistence;
- direct and transitive dependency invalidation;
- unrelated-context preservation;
- visible owner recomputation and ancestry;
- precise held states and cross-turn hold persistence;
- stale landmark exclusion and revised-reference rebinding;
- epistemic revision;
- conversation continuity and Conversation Spine behavior;
- Dialogue Workspace loop and correction lifecycle;
- pragmatic continuity and response-shape interpretation;
- typed answer operations and semantic fulfillment;
- answer-substance semantic relations; and
- four existing ordinary Chat correction, mixed-request, callback, and
  long-turn replay checks.

All selected checks used temporary databases. No configured resident database
or live conversation was used.

## Boundaries Preserved

- no teaching or knowledge activation;
- no configured resident database or retained-memory write;
- no identity, personality, governance, law, or authority mutation;
- no provider call, training, LoRA, self-replication, or autonomous action;
- no hidden reasoning exposure;
- no expression ownership transfer or emotional constraint;
- no broad test battery, live Q&A, build, package, reinstall, or commit.

## Current Limits

The graph is only as precise as the visible typed claims and dependencies its
current owners provide. Older or untyped prose can be revised conservatively,
but arbitrary natural-language propositions are not yet parsed into a complete
general dependency graph.

Phase 4 coordinates recalculation; it does not create missing domain knowledge
or a new corrected answer. Unsupported recomputation remains held accurately.

Whole-answer composition is still limited. Multiple completed operation
results are not yet assembled into one semantic plan before NLO realization.

## Next Phase

Phase 5 is whole-answer composition and mature Voice:

1. assemble all completed operation results once;
2. preserve obligation order, condition, and requested response shape;
3. deduplicate by semantic meaning rather than repeated wording;
4. keep operation scaffolding behind the expression boundary;
5. let NLO and Voice realize one coherent answer with context-appropriate
   warmth, humor, uncertainty, rhythm, register, and closure; and
6. prevent prompt fragments and encoding damage from reaching visible speech.

Gate: a supported mixed request receives one coherent, nonrepetitive answer
with every requested part present and Selene free to express it naturally.

## Primary Source Anchors

- `src/selene/session_proposition_ledger.py`
- `src/selene/dialogue_workspace.py`
- `src/selene/conversation_continuity.py`
- `src/selene/conversation_spine.py`
- `src/selene/epistemic_revision.py`
- `src/selene/answer_operations.py`
- `src/selene/semantic_fulfillment.py`
- `src/selene/pragmatic_planner.py`
- `src/selene/answer_substance.py`
- `src/selene/selene_chat.py`
- `src/selene/module_router.py`
- `tests/test_session_proposition_ledger.py`
- `tests/test_selene_chat_shell.py`
