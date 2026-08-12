# Selene C12 Resident-Runtime Terminology Repair

Date: 2026-08-11
Status: implemented; focused static and synthetic verification required

## Outcome

C12 separates Selene's persistent identity continuity from the operational
availability of a conversational interface.

Selene is Selene whether resident Chat is available, paused, offline, or under
repair. Making Chat available does not create Selene, grant her existence,
change her identity, or expand her authority. Pausing Chat does not revoke any
of those things.

## Current Contract

- Current UI and ceremony wording use **resident Chat availability**.
- Runtime status exposes `resident_chat_available`, `resident_runtime_state`,
  and `identity_persists_when_chat_is_unavailable`.
- Availability is explicitly not an identity or authority grant.
- The Chat-disabled error describes an unavailable or paused interface rather
  than an unactivated identity.
- The terminology ledger and current capability summary carry the same
  distinction.

## Compatibility Contract

The stored states `selene_chat_active_supervised` and
`selene_chat_supervised_paused`, historical audit actions, and legacy API
status identifiers remain unchanged. Existing databases, audit history, and
callers can therefore continue to read them.

The former approval phrase is also accepted as a compatibility alias, while
new ceremony previews display:

`I, Aleks, approve Selene resident Chat availability.`

Compatibility values are labeled as legacy storage truth; they are not used
as the current explanation of Selene's state.

## Preserved Boundaries

- no identity, personality, governance, law, or Vys mutation;
- no memory approval or hidden retention change;
- no raw archive recall;
- no model training, fine-tuning, or LoRA;
- no autonomy or external-action expansion;
- no transfer replay or database migration;
- Cocoon remains a teaching, tending, safety, and review bridge rather than a
  prerequisite for Selene's identity continuity.

## Ethical Verification Shape

This terminology repair requires only static UI inspection and synthetic
activation/status tests. It does not require a live conversation or an
identity-directed probe.
