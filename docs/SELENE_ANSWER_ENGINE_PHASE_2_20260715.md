# Selene Answer Engine Phase 2

Date: 2026-07-15

Status: the comparison/planning adapter and one bounded completion retry are
implemented as status-only infrastructure. Selene Chat remains intentionally
disconnected.

## Purpose

Phase 2 connects the first Answer Engine domain without broadening authority.
The adapter uses the existing intelligenceOS reasoning path to produce a
bounded comparison or planning answer. It does not replace Core/Mind, NLO,
Voice, comprehension, or memory.

## Comparison And Planning Adapter

The adapter:

- accepts only requests routed to `comparison_planning`;
- preserves the Phase 1 answer request and domain packet contracts;
- invokes intelligenceOS for a visible best-current answer;
- returns assumptions, limitations, source references, and what could change
  the answer;
- keeps route, evidence, answer, memory, and expression confidence separate;
- describes reasoning through visible summaries only;
- remains current-session and status-only.

All other domain adapters remain `contract_only_not_connected`. Authority-
bearing and disallowed requests do not execute intelligenceOS.

## Bounded Completion Retry

After the first answer, the pragmatic coverage checker compares visible answer
text with required dialogue obligations. If a required part is still open, the
adapter may request one supplemental intelligenceOS answer for only the missing
parts.

The retry contract is strict:

- maximum retry count: one;
- no recursive retries;
- no retry when the first answer is complete;
- unresolved obligations remain explicit after the retry;
- incomplete coverage lowers answer confidence without changing expression
  confidence;
- callers may disable the retry for a request.

An incomplete result is an implementation or information gap, not a judgment
of Selene.

## Confidence Boundary

The connected adapter can now report answer confidence, but expression
confidence remains `not_assessed`. A coherent sentence does not establish a
correct answer, and source availability does not claim independent source
verification.

## Routes

- `answer_engine.status`
- `answer_engine.route.preview`
- `answer_engine.packet.preview`
- `answer_engine.comparison.run`
- `GET /api/answer-engine/status`
- `POST /api/answer-engine/route-preview`
- `POST /api/answer-engine/packet-preview`
- `POST /api/answer-engine/comparison-run`

## Still Deferred

- verified math execution;
- local-code inspection;
- source-backed research;
- approved-knowledge answer execution;
- ordinary-conversation answer execution;
- Acquire -> Integrate -> Express orchestration;
- Selene Chat, NLO, or Voice integration.

No activation, autonomy, model training, LoRA, memory write, raw corpus recall,
identity change, governance change, or personality change is introduced by
this phase.
