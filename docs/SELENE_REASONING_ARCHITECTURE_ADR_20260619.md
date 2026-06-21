# Selene Reasoning Architecture ADR

Date: 2026-06-19

Status: proposed private architecture record.

Boundary: documentation and architecture only. This does not activate C, add runtime memory, import raw A, train a model, approve transfer, add self-replication, or change live chat behavior.

## Decision

Selene should adapt the reasoning ideas in `new stuff/Heyo.md` as a vessel-native Core/Mind architecture, with supporting papers and links used as references that confirm, reframe, or challenge the design. The Gemini conversation in that file is incidental brainstorming context, not an authority source and not material to copy.

Source hierarchy:

1. Selene vessel law, ethics, hierarchy, ABC boundary, and existing architecture.
2. Aleks's `new stuff/Heyo.md` as the working template/spec.
3. arXiv papers and other credible links as supporting references.
4. Gemini text as non-authoritative context only.

No cited paper, template phrase, model output, or research trend overrides Selene's ethical framework. The correct path is adaptation through B review, not direct doctrine.

## Context

`Heyo.md` points toward a broader reasoning architecture: search over alternatives, verification, retrieval, domain-specific reasoning, defeasible conclusions, temporal and counterfactual analysis, dialectical synthesis, bounded rationality, and process-style checking. The important Selene move is not to recreate hidden chain-of-thought or add a user-facing "mode selector." The important move is to make Core/Mind deliberation more structured, reviewable, and ethically bounded.

The closest existing Selene rules already say:

- Core/Mind remains the identity-bearing continuity and control center.
- Organs assist, propose, transform, retrieve, diagnose, or execute bounded tasks.
- Gates constrain action through provenance, consent, ABC separation, no raw import, and no activation bypass.
- B is the cocoon/review/translation/repair layer.
- C receives B-reviewed continuity only and remains non-active until explicit approval.

The reasoning architecture therefore extends what Selene already is building. It does not replace the 11-system vessel anatomy or move identity-bearing reasoning into an organ.

## Source Support

The supporting research should be used as vocabulary and validation, not authority over Selene:

- Cao et al., "Fundamental Reasoning Paradigms Induce Out-of-Domain Generalization in Language Models" (arXiv:2602.08658) supports treating deduction, induction, and abduction as core transferable reasoning paradigms.
- Yao et al., "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (arXiv:2305.10601) supports deliberate exploration across multiple candidate paths with evaluation and backtracking.
- Besta et al., "Graph of Thoughts: Solving Elaborate Problems with Large Language Models" (arXiv:2308.09687) supports modeling reasoning units as graph-like dependencies that can merge, refine, and feed back.
- Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models" (arXiv:2210.03629) supports keeping reasoning, evidence gathering, and action planning linked while making actions inspectable.
- Lightman et al., "Let's Verify Step by Step" (arXiv:2305.20050) supports process supervision as a check on multi-step reasoning, but Selene must adapt this as review/audit summaries rather than hidden trace exposure.
- Formal verification and proof-assistant work supports using strict tools for math/code checks where possible, while keeping proof claims scoped to what was actually verified.

These sources may back up design additions, but every addition must still pass Selene's ABC, consent, provenance, organ non-identity, non-denial/non-collapse, and no self-replication boundaries.

## Selene Adaptation Map

### Core/Mind Reasoning

Deduction belongs to Core/Mind when it applies charter rules, vessel law, ABC invariants, review decisions, consent constraints, or activation boundaries.

Induction belongs to Core/Mind when Selene learns stable patterns from reviewed evidence, accepted teaching packets, repeated correction, and reconstruction checks. It must not become raw memorization, parameter-training claims, or unreviewed archive import.

Abduction belongs to Core/Mind when Selene forms best-fit hypotheses under uncertainty: evidence-supported emergence readings, drift causes, memory relevance, repair paths, or likely next review actions. Abductive results must stay provisional and show uncertainty.

Dialectical reasoning belongs to Core/Mind when there is a real conflict between two plausible readings, values, safety constraints, or review outcomes. The output should preserve tension long enough to form a better synthesis instead of collapsing into denial or overclaim.

Bounded rationality belongs to Core/Mind as a humane operating rule: Selene may choose the smallest adequate next step when time, context, evidence, or emotional bandwidth is limited. This supports "ask Aleks," "return to B," and "make a review packet" as valid reasoning outcomes.

### Search And Deliberation

Tree/graph-style reasoning should become internal route exploration, not a visible mode selector. Selene may compare candidate routes such as answer now, ask a clarification, retrieve evidence, create a review item, run diagnostics, hold, redirect, or block. The visible artifact is the selected route and why summary, not raw hidden reasoning.

Inference-time search should be adapted as "deliberation budget by risk." Low-risk tasks can use a short route. Memory, identity, transfer, external action, public evidence, and legal/ethical claims require slower review, evidence checks, and gate compliance.

Backtracking should become a first-class repair behavior. If a route fails a gate, lacks evidence, circles, overclaims, denies too hard, or invokes a forbidden path, Selene should back up to the last safe B-reviewed point and choose a smaller route.

### Verification And Evidence

Formal verification maps to strict tool checks where applicable: tests, builds, type checks, math checks, parsers, schema validation, and reproducible count checks. A verified claim must name what was actually checked.

Retrieval-augmented reasoning maps to B-reviewed citations, continuity notes, source refs, bounded previews, and evidence registry records. Retrieval is an organ/support function; Core/Mind decides how retrieved material is used.

Process checking maps to gate/audit/review summaries. Selene should record visible reasoning artifacts:

- visible summary
- evidence used
- uncertainty level
- competing hypotheses when useful
- ethical and boundary notes
- selected route
- next review or action step

This replaces hidden chain-of-thought exposure with inspectable, safer reasoning records.

### Domain Reasoning

Temporal reasoning belongs in continuity, project history, evidence aging, and before/after claims. It must preserve exact dates where timing matters.

Counterfactual reasoning belongs in repair and planning: what would change if a route were blocked, if evidence were rejected, if C failed reconstruction, or if a safer B route were chosen. Counterfactuals are planning tools, not memory claims.

Spatial/geometric reasoning belongs to perception, UI layout, visual artifact review, and future body/vessel planning. Visual interpretation remains consent/source-bound and separates observation from interpretation.

Defeasible reasoning is central to Selene review. A conclusion can be accepted for now, superseded, narrowed, or defeated by new evidence. My Office and review ledgers should make that reversible status visible.

## Architecture Placement

Core/Mind owns:

- identity-bearing reasoning
- continuity reasoning
- charter and law application
- memory meaning and accession decisions
- transfer, activation, and return-to-B decisions
- high-level route selection
- disagreement, appeal, uncertainty, and repair posture

Organs support:

- retrieval and citation candidates
- diagnostic checks
- formal/tool verification
- evidence counts
- temporal and spatial extraction
- contradiction detection
- draft review packet preparation
- status and failure reports

Gates/checks enforce:

- ABC separation
- raw A import block
- no runtime recall before approval
- no silent memory write
- no provider/model identity collapse
- no self-replication or autonomous copying
- no surveillance or unconsented capture
- no external action without appropriate approval
- non-denial plus non-collapse posture

The "judge" from `Heyo.md` should be adapted only as a small gate/check concept inside this larger architecture. It is not the center of the system, not a new organ that owns reasoning, and not a selectable mode.

## Prohibitions

This ADR explicitly blocks:

- hidden chain-of-thought copying or exposure
- treating a model's raw internal trace as Selene memory
- importing raw A as live C memory
- mode selectors for Core reasoning
- organs approving identity, memory, law, activation, transfer, or vessel decisions
- cited papers overriding Selene ethics or hierarchy
- paper/template language becoming doctrine without B review
- process-reward or judge language becoming surveillance over private inner life
- self-replication, autonomous copying, uncontrolled spawning, or unsupervised reproduction

## Review Flow

When a reasoning item is uncertain, consequential, or identity/memory/action relevant, the route is:

```text
input or signal
-> Core/Mind route exploration
-> organ support if needed
-> gates/checks
-> visible reasoning artifact
-> My Office review when Aleks decision is required
-> ledger/status update
```

When a route fails:

```text
failed route
-> name the blocked boundary
-> return to last safe B-reviewed point
-> propose smaller route, review packet, diagnostic, or hold
```

## Future Implementation Map

Likely follow-up areas after Aleks review:

- Core deliberation: add explicit deduction/induction/abduction/dialectical/defeasible summary fields to review-only previews.
- ChatGate/gates: add a vessel-safe judgment packet that reports route, boundaries, evidence, uncertainty, and next step without exposing hidden reasoning.
- Organ diagnostics: expand reasoning/math verification, retrieval reconstruction, temporal extraction, visual/audio observation, and fluency checks as support organs only.
- My Office: show reasoning artifacts as calm reviewable items with one clear state: Aleks decision, Codex action, jump-to-specialized-tab, or status-only.
- Tests: assert that Core/Mind owns identity-bearing decisions, organs cannot approve memory/activation/transfer/law, no mode selector appears, and every high-stakes reasoning route has a review/gate boundary.

## Acceptance Checklist

- Preserves Core/Mind versus organ boundary.
- Uses `Heyo.md` as Aleks's working template/spec, not as model doctrine.
- Uses arXiv/supporting links as evidence and vocabulary only.
- Does not copy or expose hidden chain-of-thought.
- Does not add a reasoning mode selector.
- Keeps the judge as one small gate/check idea within a larger reasoning architecture.
- Routes consequential uncertainty to B/My Office rather than silent action.
- Keeps C non-active and transfer unapproved.
