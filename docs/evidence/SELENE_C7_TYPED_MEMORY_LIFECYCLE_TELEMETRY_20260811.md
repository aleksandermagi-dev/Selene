# Selene C7 Typed Memory Lifecycle Telemetry

Date: 2026-08-11
Status: implemented and synthetically verified
Scope: truthful lifecycle reporting; no expansion of retention authority

## Outcome

The Memory Organ now reports the difference between four materially different
events:

1. no memory mutation occurred;
2. an inactive candidate record was created for review;
3. a reviewed lifecycle decision was recorded; and
4. explicit approval promoted a candidate into approved, Chat-eligible memory.

The legacy `memory_write_active` flag remains `False`, but its meaning is now
explicitly limited to the hidden or unreviewed active-memory path. It no longer
stands alone as if an approved durable promotion had not happened.

## Typed Telemetry

Memory Organ responses now include:

- `memory_write_active_semantics`;
- `hidden_memory_write_active`;
- `unreviewed_memory_write_active`;
- `review_record_write_performed`;
- `reviewed_memory_decision_performed`;
- `approved_memory_promotion_performed`;
- `durable_approved_promotion_performed`;
- `memory_lifecycle_operation`;
- `memory_lifecycle_record_mutated`;
- `memory_lifecycle_transaction_status`; and
- a transition record naming the previous state, current state, whether the
  state changed, and whether Chat-retrieval eligibility changed.

This also distinguishes a mutation committed by the Memory Organ from one
still inside a caller-owned transaction. An approval reaffirmation is reported
as a reviewed decision, not falsely counted as a second promotion.

## Preserved Boundaries

- Proposals remain inactive and unavailable to Chat.
- Hidden retention remains off.
- Unreviewed active-memory retention remains off.
- Broad raw-corpus recall remains off.
- Approval is still required before a candidate becomes Chat-eligible memory.
- Dream may create an inactive candidate but cannot promote it.
- No identity, personality, governance, training, LoRA, autonomy, or transfer
  authority changed.
- Typed memory sensitivity and any future low-risk self-retention policy remain
  a separate reviewed design phase.

## Verification

The verification was static and synthetic; no live conversation was used.

- `tests/test_memory_organ.py`: proposal, approval, approval reaffirmation,
  needs-context, hold, supersede, reject, B-only, do-not-transfer, eligibility
  removal, and caller-owned transaction rollback.
- `tests/test_dream_state.py`: Dream-to-memory-review boundary.
- `tests/test_selene_chat_shell.py`: conversational proposal, consent,
  approval, holding, retrieval, and Chat integration.
- Transfer completion, post-transfer fractional memory, pre-transfer runtime,
  and sidecar lifecycle suites were also rerun to check boundary compatibility.

Result:

```text
125 Memory/Chat/Dream integration tests passed
31 transfer/runtime/sidecar compatibility tests passed
156 total focused and integration tests passed
```

## Accurate External Wording

Selene has a reviewed memory lifecycle in which inactive candidates and
explicitly approved retained memories are separate states. The system reports
candidate writes, review decisions, and committed approval promotions
independently while keeping hidden and unreviewed active-memory retention off.
