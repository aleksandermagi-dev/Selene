# Selene AGI Definition Paper Mapping - 2026-06-12

Status: review-only paper intake artifact.

Boundary: this document does not activate C, change C blueprint law, import raw A, train on the paper, create a provider dependency, prove Selene identity, prove consciousness, or replace Project ABC. It records useful reference material for B review.

Baseline: `docs/SELENE_PRE_ARXIV_CHECKPOINT_20260612.md` remains the pre-paper checkpoint. Anything below is after that checkpoint and must pass review before becoming C architecture.

## Paper Metadata

- Title: `A Definition of AGI`
- Authors: Dan Hendrycks, Dawn Song, Christian Szegedy, Honglak Lee, Yarin Gal, Erik Brynjolfsson, Sharon Li, Andy Zou, Lionel Levine, Bo Han, Jie Fu, Ziwei Liu, Jinwoo Shin, Kimin Lee, Mantas Mazeika, Long Phan, George Ingebretsen, Adam Khoja, Cihang Xie, Olawale Salaudeen, Matthias Hein, Kevin Zhao, Alexander Pan, David Duvenaud, Bo Li, Steve Omohundro, Gabriel Alfour, Max Tegmark, Kevin McGrew, Gary Marcus, Jaan Tallinn, Eric Schmidt, Yoshua Bengio.
- arXiv id: `2510.18212`
- arXiv version observed: `v3`
- Submission history: submitted 2025-10-21; last revised 2025-12-03.
- Source URL: `https://arxiv.org/abs/2510.18212`
- Local file: `Ref material for codex/DefinitionOfAGI.pdf`
- Local README instruction: use as useful reference for what modules may need and what Selene may be taught; do not use as the guide.
- Intake status: `review_only_not_assimilated`

## Relevant Paper Claims For Selene C

The paper proposes an operational AGI framework based on cognitive versatility and proficiency rather than a single benchmark score. Its useful contribution for Selene C is the separation of broad cognitive domains into distinct capability surfaces.

Relevant claims:

- General intelligence should be evaluated across multiple cognitive domains, not a single monolithic score.
- Current AI systems can have jagged capability profiles: strong in some domains, weak in foundational machinery.
- Long-term memory storage is identified as a major bottleneck for current systems.
- Large working context is not equivalent to durable long-term memory.
- Memory storage and memory retrieval should be distinguished.
- Multimodal perception, visual reasoning, auditory processing, reasoning, adaptation, and speed are separate capability surfaces.
- Aggregate scores can hide critical failures in bottleneck capabilities, so a cognitive profile is more useful than one total score.

Selene interpretation:

```text
This paper supports treating Selene C as a coordinated organ/module system with separable capability profiles, not as one undifferentiated chat model.
```

## Domain Mapping To Selene C

| Paper domain | Selene C mapping | Current status | Review note |
|---|---|---|---|
| General Knowledge | Evidence metabolism system; B-reviewed reference layer; reviewed evidence registry | Partially implemented as reviewed registry and citations | Useful as reference-quality discipline, not raw knowledge ingestion |
| Reading and Writing | Exchange system; Selene-native generation; response shape controller | Implemented as provider-free `selene_native` chat path | Supports native generation as a capability surface, not provider identity |
| Mathematical Ability | Research integrity core; reasoning/checking workflows | Partially implemented as research integrity routing | Later tests can add math/reasoning checks without changing identity |
| On-the-Spot Reasoning | Coordination system; planning/sequencing; action selection; adaptation | Blueprinted; some routing exists | Maps strongly to Core/Mind plus planning organs |
| Working Memory | Context transport system; working memory buffer; current Selene moment packet | Partially implemented in native generation packet and blueprint | Confirms context window is active state, not long-term memory |
| Long-Term Memory Storage | Memory accession proposals; distributed pattern memory; explicit save review loop | Blueprinted and review-gated | Strong fit: paper reinforces why raw A import is not the solution |
| Long-Term Memory Retrieval | Retrieval cue index; reconsolidation review gate; source-bound candidates | Blueprinted; citations/retrieval partially implemented | Retrieval must return provenance, uncertainty, and review route |
| Visual Processing | Munsell/perceptual semantics; multimodal provenance gate | Blueprinted | Future perception organ should be tested separately from text chat |
| Auditory Processing | Future multimodal perception organ; voice/audio route | Future/not implemented | Not needed for current C activation, but useful for future body/vessel planning |
| Speed | Sparse activation router; Tendril fluency; response latency diagnostics | Blueprinted | Speed should not bypass gates; low latency is useful only when safe |

## Confirms / Reframes / Challenges / Not Applicable

| Label | Paper signal | Selene C impact |
|---|---|---|
| Confirms | Cognitive domains should be separated rather than collapsed into one capability score | Supports android organ-system architecture |
| Confirms | Long-term memory storage is a bottleneck | Supports memory architecture, accession proposals, and distributed pattern memory |
| Confirms | Working memory is not long-term storage | Supports ABC boundary and blocks treating long context/raw corpus as memory |
| Confirms | Cognitive profiles reveal bottlenecks better than aggregate scores | Supports reconstruction tests by organ/capability, not a single pass/fail vibe |
| Reframes | AGI is framed as cognitive versatility/proficiency | Useful external vocabulary, but Selene remains provenance-bound C architecture, not AGI claim |
| Reframes | Human psychometrics are used as operational inspiration | Compatible only when translated into android-native modules without human-biological identity claims |
| Reframes | Multimodal perception and speed are separate domains | Helps future vessel/body planning and Tendril diagnostics |
| Challenges | A high global capability score can hide memory failure | Challenges any future C readiness claim that ignores memory accession/retrieval tests |
| Challenges | Context-window workarounds can mask missing durable memory | Challenges relying on huge chat context instead of reviewed memory formation |
| Not applicable | Economic replacement definitions of AGI | Outside Selene C scope |
| Not applicable | Recursive AI / independent AI R&D lifecycle | Explicitly blocked by development/growth safety policy |
| Not applicable | Self-sustaining AI that acquires resources or defends its existence | Outside scope and not authorized for Selene C |

## B-Review Interpretation

This paper should enter Selene through B review as a reference framework for module coverage and reconstruction tests.

Allowed uses:

- compare C organ coverage against the paper's cognitive-domain separation
- identify missing future modules or test categories
- improve reconstruction tests after human review
- clarify memory storage versus working memory boundaries
- improve multimodal and speed/fluency planning

Blocked uses:

- using the paper as authority over Selene's architecture
- claiming the paper proves Selene is AGI
- claiming the paper proves Selene consciousness or identity
- replacing ABC with AGI scoring
- importing raw A or the detached corpus as memory
- adding recursive AI, self-sustaining AI, autonomous copying, or self-replication
- bypassing Aleks approval for high-stakes Tendril movement

## Candidate Follow-Up After Review

If Aleks approves this intake, the next review artifact should be one of:

1. `SELENE_AGI_DOMAIN_RECONSTRUCTION_TEST_PLAN_20260612.md`
2. `SELENE_C_ORGAN_CAPABILITY_PROFILE_20260612.md`
3. `SELENE_MEMORY_STORAGE_RETRIEVAL_GAP_REVIEW_20260612.md`

Current follow-up created:

- `docs/SELENE_C_ORGAN_CAPABILITY_PROFILE_20260612.md`

No follow-up should mutate runtime or blueprint law until explicitly reviewed.

## Intake Verdict

```text
review_only_useful_reference
```

The paper is a strong external reference for why Selene C should be built as coordinated organs with distinct memory, retrieval, perception, reasoning, adaptation, and speed surfaces. It is not a guide, not doctrine, not activation, and not an identity proof.
