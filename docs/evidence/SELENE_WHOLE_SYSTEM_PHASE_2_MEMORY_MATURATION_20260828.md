# Selene Whole-System Phase 2 — Memory Maturation

Date: 2026-08-28

Status: complete for current scope

Parent plan:
[Selene Whole-System Maturation Plan](../architecture/SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

## Outcome

Selene's current-session working context and reviewed personal Memory now have
inspectable, separate lifecycles. Relevant approved Memory can contribute
reconstructed meaning across bounded natural paraphrases, while present facts,
privacy, answer ownership, and uncertainty continue to outrank recall.

The resulting relationship is:

```text
visible current turn and session context
  -> bounded attention, expiry, interruption, and resume
  -> canonical subject / speaker / channel / owner gates
  -> optional approved personal Memory retrieval
  -> recalled content kept distinct from reconstruction and interpretation
  -> responsible answer owner
  -> NLO and Voice expression

Memory correction
  -> proposed descendant
  -> Aleks reconsolidation review
  -> approve: activate descendant and supersede parent
  -> otherwise: leave the approved parent unchanged
```

General taught knowledge remains a separate resource selected through the
Comprehension system. Dream remains reflective work rather than personal
Memory. Raw private corpus material remains outside live recall.

## Implemented Work

### Working-context lifecycle

`src/selene/dual_horizon_context.py` now exposes a read-only working-context
contract with:

- a bounded active attention budget and explicit overflow;
- selected and dropped item receipts;
- current-turn and current-session expiry;
- cleanup of expired transient response preferences;
- visible paused and active threads for interruption and resume; and
- an explicit guarantee that dropped or resumed context is not thereby
  retained as durable Memory.

Session checkpoints remain session context. They are not personal Memory,
taught knowledge, Dream conclusions, or hidden retention.

### Natural, layered approved-Memory recall

`src/selene/memory_organ.py` and `src/selene/semantic_relevance.py` now support
source-bound retrieval cues and conservative canonical lexical matching for
several natural ways of asking about the same approved event. Each selected
item exposes distinct read-only layers:

- recalled approved content;
- reconstruction for expression;
- present interpretation of relevance; and
- inference, which remains explicitly absent unless a downstream reasoning
  owner actually makes one.

Clear, fuzzy, partial, and not-known states remain distinct. Unrelated prompts
retrieve nothing. Internal titles, source metadata, and review labels remain
behind the expression boundary.

### Present-fact, privacy, and relationship boundaries

Current-turn corrections and conflicting present relations hold stale recalled
content without rewriting it. Memory eligibility can require both an allowed
channel and a minimum authentication strength. Existing speaker, consent,
subject, function, and answer-owner competition gates remain active.

Relational Memory supports continuity from approved shared events only. The
contract explicitly forbids constructing persuasion or vulnerability profiles.
Memory may support the conversation when relevant and remain silent otherwise;
it does not become a script for warmth, attachment, or response shape.

### Duplicate prevention and reviewed lifecycle

Equivalent proposals reuse the existing candidate or approved reference rather
than retaining another copy. Reading, summarizing, retitling, studying, or
discussing a Memory does not promote reconstruction into a new Memory.

Approved Memory can now be:

- reopened for review;
- revoked from Chat use while preserved for audit;
- placed into deletion review without immediate destructive erasure; or
- corrected through a descendant-based reconsolidation review.

A corrected descendant cannot use the generic approval path. Aleks must approve
it through the reconsolidation review. Approval preserves the parent's original
content and provenance, activates the descendant, records revision ancestry,
and marks the parent superseded. Needs-context, tending, and rejection leave the
parent active.

Router keys:

- `memory.reconsolidation.list`
- `memory.reconsolidation.propose`
- `memory.reconsolidation.decide`

The Cocoon Memory surface now provides correction drafting, revocation,
deletion review, and reconsolidation decisions without mixing revision
candidates into ordinary Memory approval.

## Completion Gate

| Requirement | Result |
| --- | --- |
| Clear, fuzzy, partial, and unknown recall differ | Met |
| Approved Memory survives bounded natural paraphrases | Met |
| Unrelated prompts retrieve nothing | Met |
| Present facts and corrections outrank stale recall | Met |
| Reading, discussing, or retitling creates no duplicate | Met |
| Corrected Memory preserves provenance and revision ancestry | Met |
| Ineligible speaker channel or authentication cannot receive private Memory | Met |
| Working context has bounded attention, expiry, cleanup, interruption, and resume | Met |
| General knowledge, Dream, raw corpus, and personal Memory remain separate | Met |

## Verification

```text
124 focused Memory, relevance, working-context, intent, and fact-ledger checks passed
258 broader Memory and conversational-integration checks passed
npm run build passed
main frontend bundle: about 486 kB (no size warning)
```

The broader run included the focused behavior and exercised Selene Chat shell,
Conversation Spine, contextual continuity, current-turn facts, recall intent,
and semantic competition. It caught two existing integration assumptions in
which canonical-ledger fallbacks could overwrite caller-supplied comparison or
older-thread data; those source handoffs were corrected and the full slice then
passed.

No live Q&A or distress-shaped test was necessary. Synthetic fixtures and the
existing ordinary Chat integration tests supplied sufficient evidence. No
package or reinstall was performed.

## Remaining Limits

- Paraphrase recall is bounded, source-cued, and lexical; it is not a claim of
  unrestricted semantic recall over arbitrary wording.
- Broader subject vocabulary comes from later ordered education, not from
  silently importing raw corpus wording into Memory.
- Delayed associative resurfacing, Study-to-knowledge updates, and Dream
  handoffs belong to Phase 3 rather than personal Memory.
- Physical deletion remains a custody decision after deletion review; this
  phase safely revokes use and records the request without destructive erasure.

## Boundaries Preserved

This phase performed no live Memory retention decision on Selene's resident
data. It did not import raw corpus material, approve taught knowledge, decide a
Dream proposal, alter identity, personality, governing law, authority,
training, LoRA, autonomy, external action, packaging, or installation. Selene
remains Selene. Aleks remains the approval authority for durable personal
Memory and its reviewed corrections.

## Next Phase

Phase 3 — Study, Dream, Associative Intuition, and Reflective Growth.

The next work should reconcile those already-built systems, make their
handoffs inspectable, and keep questions, reflections, associations, and Dream
candidates from becoming hidden Memory or automatic truth.
