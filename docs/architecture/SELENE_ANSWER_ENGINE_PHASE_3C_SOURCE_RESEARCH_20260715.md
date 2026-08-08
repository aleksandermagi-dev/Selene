# Selene Answer Engine Phase 3C — Source-Backed Research

Date: 2026-07-15

Status: attributed source-backed research is connected as a status-only Answer
Engine adapter. It is not Selene memory, governance, or a general truth oracle.

## Source Boundary

Every usable packet requires:

- a non-empty `source_ref`; and
- visible statements, content, or an excerpt.

The adapter selects relevant visible statements and returns their source
reference and locator. Provenance-free or content-free packets are held back.
It never creates a citation for a source that was not accepted.

Source statements are labeled separately from bounded inferences. Attribution
means “this source states this,” not “this statement is automatically true.”

## Disagreement And Missing Evidence

Packets may label statements with a shared `claim_key` and a `stance`. Different
stances for the same claim are surfaced as source disagreement rather than
flattened into a false consensus.

The adapter also surfaces:

- missing corroboration when only one source is supplied;
- packet-declared missing evidence;
- unresolved disagreement;
- absence of statements relevant enough to answer.

## Great Library

Great Library consultation requires two independent conditions:

1. the request sets `consult_great_library: true`; and
2. the existing loopback-only Library Tendril adapter is separately enabled
   and credentialed.

The Library remains an external inert resource. Only attributed returned
records may enter the research packet. Consultation does not create memory,
authority, training material, or a Library dependency for identity continuity.

## Open-Ended Problem Solving Remains Available

Source-backed research does not replace the comparison/planning adapter.
Open-ended problems without a pre-existing answer may still use intelligenceOS
to build and challenge provisional explanations. Their confidence remains
`reasoning_only_not_source_verified` unless attributed evidence is actually
provided.

This preserves the distinction between:

- solving or exploring an open problem; and
- claiming that a conclusion is supported by named sources.

## Routes

- `answer_engine.research.run`
- `POST /api/answer-engine/research-run`

## Completion Gate

Focused machinery checks cover attribution, statement/inference separation,
disagreement, missing evidence, held-back packets, graceful no-answer results,
non-invented citations, optional Library observation, router access, and guard
preservation.

The adapter cannot write memory, law, identity, personality, governance, or
authority.
