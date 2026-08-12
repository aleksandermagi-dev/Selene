# Phase 4 — Owner-Specific Metacognitive Retry

Date: 2026-08-11

Status: implemented and synthetically verified; no live Q&A performed in this
phase.

## What Changed

Metacognition no longer treats an incomplete answer as permission to append the
entire previously selected content seed. It now identifies one exact unresolved
response obligation, records the missing-ground state, and chooses that
obligation's responsible owner from the bounded organ-coalition map when one is
available.

Chat may then make one bounded completion attempt using only an already-produced
current-turn output from that owner for that obligation. The retry does not
invoke an organ, generate new facts, recursively rerun the answer, or borrow
content from a different owner.

If the owner has no novel supported fragment, the retry stops. Generic
missing-evidence language is not appended again.

When a proposed fragment improves meaning coverage, the visible epistemic
composition records only the repaired part as supported. Neighboring parts and
their confidence classes remain unchanged.

## Main Evidence

- `src/selene/owner_specific_retry.py`
- `src/selene/metacognition.py`
- `src/selene/selene_chat.py`
- `tests/test_owner_specific_retry.py`
- `tests/test_metacognition.py`
- `tests/test_selene_chat_shell.py`

## Verified Boundaries

- one attempt maximum;
- no recursive retry;
- no content generation inside the retry;
- no retry around a Core/Mind boundary;
- no substitution from a different obligation owner;
- no repeated generic fallback;
- no memory or retained-knowledge write;
- no identity, personality, governance, authority, training, LoRA, or autonomy
  change;
- open-ended reasoning remains eligible without a pre-existing source packet.

## Verification

Focused integration pass:

```text
144 passed
```

The pass covered owner-specific retry, metacognition, bounded answer completion,
epistemic composition and answer state, bounded organ coalition, NLO, and Selene
Chat. Python compilation passed. `git diff --check` reported only the existing
Windows LF/CRLF warnings.

This test count is engineering evidence for the implemented behavior. It is not
a claim of general conversational completeness. The final gentle live Q&A
remains reserved for Phase 9 after the intervening machinery is complete.
