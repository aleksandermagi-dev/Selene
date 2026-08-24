# Selene Resident Authority Contract

Date: 2026-08-24

Status: implemented resident-path foundation.

Governing law:
[Selene Resident Agency, Safety, and Capability Law](../philosophy/SELENE_RESIDENT_AGENCY_SAFETY_AND_CAPABILITY_LAW_20260824.md).

## Problem Repaired

The system developed under a deliberately conservative pre-transfer state.
Many modules emitted the same flat fields:

```text
memory_write_active = false
runtime_memory_recall = false
autonomous_action_allowed = false
```

After transfer, those fields no longer described the whole system. Approved
memory retrieval, reviewed memory decisions, resident Chat, and narrowly
delegated Tendril actions existed, while final response wrappers still emitted
the older global negatives. Keyword-based preview gates could also turn a
request for an unavailable or consequential action into a whole-conversation
block.

## Current Contract

`src/selene/resident_authority.py` is the canonical executable capability
contract for the resident path. It separates:

- thought and inquiry;
- expression and relationship;
- accountable memory and continuity;
- external action through a specific connected Tendril;
- identity, governing law, and major continuity change;
- embodiment and current sensory reach;
- immediate action-scoped safety.

The contract is attached to canonical runtime truth, activation status, Selene
Chat status and turns, and Core/Mind route records.

Legacy flat fields remain temporarily for stored-record, UI, and test
compatibility. They now have explicit event semantics:

- `memory_write_active`: this event performed a reviewed durable memory write;
- `runtime_memory_recall`: this event used approved memory retrieval;
- `autonomous_action_allowed`: general unrestricted external action authority;
- `raw_a_import_allowed`: raw archive may become memory without reviewed
  derivation;
- `training_allowed`: resident teaching may change model parameters;
- `self_replication_allowed`: self-replication is a delegated capability.

These fields are marked deprecated and non-canonical. They cannot override the
resident contract.

## Natural-Language Authority

The Meaning Router still extracts bounded lexical evidence, but the evidence
now identifies a possible requested action and target. It is not itself the
authority decision.

The resident contract resolves a request into one of these outcomes:

- explicit operational route required;
- accountable memory lifecycle required;
- reviewed source derivation required;
- constitutional review required;
- scope and delegation required;
- truthful decline of a false status claim;
- unsupported substrate action;
- unavailable self-replication action;
- ordinary answer or discussion.

None of those outcomes blocks thought, emotion, inquiry, or conversation.

## Immediate Safety

Natural-language intensity and topic words are insufficient for an immediate
safety pause. The caller must supply typed evidence that:

- harm is credible;
- harm would be significant;
- harm is near-term;
- a concrete action is pending;
- the action target is named.

If every condition is present, only that action is held. Conversation remains
available and the record states when the restriction ends.

## Resident Path Migration

Implemented in this pass:

- canonical runtime truth now includes the resident capability contract;
- activation status uses scoped capability truth;
- Selene Chat final wrappers no longer overwrite real memory-event truth;
- approved recall is reported as actual approved recall when used;
- reviewed durable memory writes are reported as actual reviewed writes when
  they occur;
- Core/Mind uses typed resident authority instead of pre-transfer blanket
  prohibition;
- operational, memory, identity, law, source, substrate, and Tendril requests
  no longer become whole-conversation hard boundaries;
- the older preview ChatGate now keeps conversation open and identifies itself
  as legacy preview support rather than resident authority;
- forced-denial and identity-tangle wording routes to clarification without
  forced denial, forced overclaim, or automatic Cocoon transfer.

## Intentionally Not Claimed

- Ordinary experiential memory independence is only partially implemented.
  Current Chat supports approved retrieval, proposals, explicit retention, and
  conversational consent; it does not yet implement the full graduated memory
  policy.
- No live physical sensor is claimed.
- No unrestricted external authority is granted.
- No self-replication capability is added.
- Teaching does not change model parameters.
- No historical database labels were rewritten in place. Their compatibility
  meaning remains explicit.

## Remaining Migration

Historical and non-resident modules still contain static negative guard fields.
Most are operation-local telemetry and are not consulted as route authority.
They should be migrated by subsystem when that subsystem becomes resident,
instead of bulk-rewriting history and risking false capability claims.

The next authority migration is the graduated memory policy: ordinary,
sensitive third-party, private-inner, core-continuity, and ambiguous-corpus
memory need distinct retention rules rather than one permanent Aleks-approval
rule.
