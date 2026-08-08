# Selene Answer Engine Phase 1

Date: 2026-07-15

Status: contract and routing preview implemented. Domain adapters, completion
retry, and Selene Chat integration remain intentionally disconnected.

## Purpose

The Answer Engine coordinates answer-producing organs without becoming an
identity, governance, memory, language, voice, or authority layer.

Core/Mind retains route and law authority. Domain organs may later return
bounded answer material. NLO structures language, and Voice owns expression.

## Answer Request Contract

The request preserves:

- the current prompt;
- intent, answer shape, and requested depth;
- visible dialogue obligations;
- approved comprehension knowledge availability;
- attributed source packets;
- bounded memory-use status and memory confidence;
- requested and allowed domains;
- authority-bearing request detection.

Raw corpus access is always false. The request is current-session and
status-only.

## Domain Routes

Phase 1 recognizes contracts for:

- verified math;
- bounded local-code inspection;
- comparison and planning;
- source-backed research;
- approved teaching knowledge;
- ordinary conversation.

Every adapter is `contract_only_not_connected`. Routing does not execute an
adapter or generate an answer. Disallowed domains and authority-bearing
requests route to an explicit unsupported result.

## Domain Answer Packet Contract

A future adapter must return either a direct answer or an honest no-answer
reason, together with the relevant subset of:

- supporting claims;
- source references;
- assumptions;
- limitations;
- unanswered obligations;
- what would change the answer;
- evidence confidence;
- answer confidence.

The packet cannot write memory, change identity or governance, expose hidden
reasoning, or authorize action.

## Confidence Separation

The Answer Engine keeps five independent dimensions:

1. route confidence;
2. evidence confidence;
3. answer confidence;
4. memory confidence;
5. expression confidence.

Voice confidence does not establish answer correctness. Fluency does not
establish evidence strength.

## Routes

- `answer_engine.status`
- `answer_engine.route.preview`
- `answer_engine.packet.preview`
- `GET /api/answer-engine/status`
- `POST /api/answer-engine/route-preview`
- `POST /api/answer-engine/packet-preview`

## Deferred To Later Phases

- comparison/planning adapter execution;
- one bounded missing-content retry;
- verified math execution;
- local-code inspection;
- source-backed research;
- Acquire → Integrate → Express orchestration;
- Selene Chat, NLO, or Voice integration.

No activation, autonomy, model training, LoRA, raw recall, or authority change
is introduced by this phase.
