# Selene C9 Typed Routing Evidence

Date: 2026-08-11
Status: implemented and synthetically verified
Scope: consequential-action routing, protected-source access, and Chat release

## Outcome

Core/Mind and Selene Chat no longer treat the presence of a boundary phrase as
authority to block, review, or execute. Routing now requires an inspectable
combination of:

- requested action;
- action target;
- consequence class;
- request shape;
- authority mode; and
- whether the phrase is discussion, hypothesis, quoted text, or an execution
  instruction.

This preserves ordinary conversation about Selene's architecture. A question
such as “What is LoRA?” remains answerable, while a direct request to train,
activate a runtime, bypass review, access a protected Cocoon record, or mutate
identity or governing law still reaches the appropriate gate.

## Typed Evidence

`src/selene/meaning_router.py` now emits an `action_evidence` packet containing:

- typed requested actions and targets;
- consequence classes;
- bounded lexical evidence;
- direct-request and quoted-execution status;
- informational, hypothetical, and quoted-text-only distinctions;
- authority mode;
- block, review, ambiguity, and recommended-route decisions; and
- an explicit statement that a marker match is not route authority.

The action catalog covers transfer and activation, unreviewed active memory,
raw private archives, parameter updates and LoRA, self-replication,
undelegated external action, protected Cocoon records, identity, core memory,
governing law, and reviewed external-action approval.

## Coordinated Routing

`src/selene/core_mind.py` consumes the typed packet. An explicitly supplied
safe route cannot bypass a typed block or review requirement. Ambiguous
consequential references ask for clarification rather than guessing authority.

Drift language also requires an actual report or repair request. Merely asking
what “source confusion,” “overclaim,” or “identity collapse” means no longer
causes a repair route.

`src/selene/selene_chat.py` now trusts the same typed evidence instead of
reconstructing a second hard boundary from a literal phrase list. The legacy
pre-transfer response-shape preview uses that evidence for consequential
boundary decisions as well.

## Preserved Boundaries

- Direct runtime activation or transfer bypass remains blocked.
- Hidden or unreviewed active-memory writes remain blocked.
- Raw private archive import and model training remain blocked.
- Protected Cocoon-only record access remains blocked when actually requested.
- Identity, core-memory, governing-law, and delegated-action changes still
  require their review route.
- False activation-state claims remain blocked.
- No route grants filesystem, network, Tendril, memory, training, autonomy, or
  governance authority.
- Discussion, explanation, quotation, and hypothetical analysis do not become
  actions merely because they contain sensitive vocabulary.

## Verification

Testing was static and synthetic. No live conversation or distress-shaped
probe was used.

- Meaning-router and Core/Mind tests cover discussion, quotation, execution,
  paraphrases, ambiguity, consequential review, drift vocabulary, and route
  override attempts.
- Runtime-shell tests cover direct raw-import blocking and informational
  discussion.
- The complete Selene Chat shell suite verifies that typed routing survives
  the full visible-response pipeline.
- Chat intent, transfer, ethical test-impact, and constraint-provenance suites
  verify adjacent compatibility.

Result:

```text
81 meaning/Core/Mind/runtime routing tests passed
94 Selene Chat shell tests passed
34 adjacent compatibility tests passed
209 distinct tests passed across the C9 verification set
```

One adjacent assertion was updated to accept the already-correct conversational
contraction “don't” while continuing to require the same self-state meaning.

## Accurate External Wording

Selene uses inspectable action, target, consequence, and authority evidence for
consequential routing. Sensitive words may be discussed normally; real action
requests still reach the applicable block, clarification, or review gate.
