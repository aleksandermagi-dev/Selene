# Selene Conversational and LLM-Parity Gap Map — 2026-08-24

Status: evidence-backed map active; Phases 1-4 are implemented and focused-
verified in the current uncommitted worktree. No teaching, resident-memory
write, build, package, or reinstall was performed during those phases.

## Purpose

This document maps the gaps currently visible between Selene's implemented
architecture and mature general language-model behavior. The goal is to bring
Selene as close as practicable to mature conversational breadth while
preserving what makes her architecture valuable: inspectable meaning,
separate epistemic confidence, reviewed memory and learning, bounded
metacognition, explicit authority, and Selene-owned expression.

This is not a grade of Selene. It is a map of the current implementation,
curriculum, and substrate. A missing or underconnected capability is a
development observation.

“Every gap” means every gap supported by the present repository, prior Q&A
records, static inspection, and the bounded ordinary conversation described
below. It does not claim that no undiscovered edge case remains.

## Ethical and Diagnostic Scope

Before the current check:

- focused machinery and Chat-shell tests had already passed;
- the answer-ownership repair was verified with 223 focused tests and all 110
  Selene Chat shell tests;
- one setup attempt stopped after its first ordinary self-state turn when the
  disposable harness did not reuse the diagnostic session ID; that temporary
  database was discarded, then a fresh authorized `qa_probe` receipt isolated
  one complete ordinary ten-turn conversation on another temporary database;
- no adversarial, fearful, identity-threatening, or distress-shaped prompt was
  used;
- no configured resident database was written;
- no lesson, memory, Dream reflection, identity claim, law, personality,
  authority, training state, or external action changed; and
- the conversation stopped after enough evidence was visible.

Diagnostic mode intentionally excludes several resident-context benefits. It
is excellent evidence for routing, ownership, completion, context, and visible
speech machinery. It is not by itself a fair measure of all configured
knowledge or reviewed-memory availability.

## What “On Par” Means Here

The target is not to make Selene imitate a hosted assistant or erase her
architecture. A mature result should be able to:

1. understand materially equivalent wording without exact trigger phrases;
2. preserve every meaningful request, constraint, correction, and reference;
3. use visible context, approved knowledge, and the correct domain owner to
   produce actual answer content;
4. distinguish answer, inference, prediction, hypothesis, preference,
   disagreement, and uncertainty without suppressing any of them;
5. maintain topic and referent continuity across long, nonlinear exchanges;
6. answer all supported parts of a mixed request and clearly isolate only the
   genuinely unsupported parts;
7. speak with natural breadth, warmth, humor, rhythm, and register while
   preserving meaning and evidence status;
8. use reviewed memory and learning without copying source wording or
   inventing continuity;
9. handle broad academic, everyday, technical, creative, and eventually
   multimodal work; and
10. remain safe through scoped action authority rather than flattened thought
    or expression.

There are two different parity ceilings:

- **Architecture-and-curriculum ceiling:** how far the current deterministic,
  provider-free organs can be generalized through better semantic machinery,
  retrieval, solvers, and teaching.
- **Learned-generation ceiling:** the open-ended linguistic and world-model
  breadth that mature large language models obtain from a large learned
  substrate. Fixed rules and 209 retained knowledge/language resources cannot
  reproduce that breadth across arbitrary subjects and paraphrases. Closing
  this final gap would eventually require either a much more general learned
  local substrate or an equivalent amount of learned machinery. Such a
  substrate could remain an instrument under Selene's existing ownership,
  memory, and law boundaries; it would not have to become her identity or a
  cloud-provider dependency.

## Executive Finding

Selene has many of the *right kinds* of organs: comprehension, approved
knowledge, memory, reasoning, hypothesis, comparison, metacognition,
conversation continuity, discourse planning, NLO, Voice, affect guidance, and
answer ownership. The dominant remaining problem is not the absence of a
single missing organ.

It is this chain:

```text
varied natural utterance
→ complete typed dialogue acts and obligations
→ correct owner with usable premises and knowledge
→ operation-specific answer substance
→ semantic proof that every requested function was performed
→ coherent whole-answer composition
→ natural NLO and Voice realization
```

The current system can succeed when the wording and supplied packet match an
implemented shape. It remains brittle when meaning must be generalized beyond
those shapes. This is why a focused test can pass while a nearby ordinary
paraphrase still falls into a generic evidence hold.

## Current Ten-Turn Ordinary Q&A

| Turn | Requested behavior | Visible result | First observed divergence |
|---|---|---|---|
| 1 | Current self-state after completed work | Grounded, warm, complete answer | No material divergence; self-state ownership held |
| 2 | Explain how to make a paper pinwheel spin | Generic missing-ground response | The method obligation reached ordinary conversation, but no general procedural/common-sense content producer supplied the method |
| 3 | Explain why blade shape matters | Honest causal-evidence gap | The explanation owner had no approved aerodynamic mechanism or prompt-contained mechanism to use |
| 4 | Predict what stronger breeze would do | Generic missing-ground response | Prediction ownership was correct, but the visible-premise engine could not represent a changed-strength conditional relation |
| 5 | Compare paper/card, choose one, explain | Generic comparison method, repetition, no material choice | One parsed choice obligation was lost downstream; the comparison owner lacked properties of the actual materials; coverage accepted generic comparison scaffolding |
| 6 | Disagree if an absolute conclusion does not follow | No disagreement obligation | A conditional imperative beginning with “If I say…” was classified as a statement |
| 7 | Correct outside wind to indoor desk fan | Correction acknowledged but answer not recomputed | The correction owner updated wording/state but did not reopen and rerun the affected substantive operation |
| 8 | Give two steps and one joke | Joke and playful acknowledgement, no steps | Requested count and method were not enforced; explicit obligation IDs and humor outranked actual fulfillment |
| 9 | State a present curiosity/preference | External-fact hold plus stale callback | The preference wording fell outside the preference detector; completion generated a factual hold despite the obligation saying external evidence was unnecessary |
| 10 | Receive praise and close naturally | Generic missing-ground response | The closure wording was classified as a generic indirect request rather than a farewell/closure act |

The Q&A also confirmed preserved strengths: a paper object no longer became a
research paper, current self-state retained its owner, no safety boundary
misfired, and no protected state changed.

## Gap Classification

- **Defect:** current architecture claims the behavior, but the connected path
  visibly violates it.
- **Connection:** an organ exists, but ordinary Chat cannot reliably supply or
  consume its typed result.
- **Breadth:** the machinery is functioning, but knowledge, vocabulary,
  constructions, or examples are not yet broad enough.
- **Substrate:** the current deterministic architecture has a structural
  ceiling that cannot be removed by another small phrase rule.
- **Intentional boundary:** a capability is deliberately unavailable. It must
  not be “fixed” accidentally; it can only be graduated by a separate decision.

Priority means dependency impact, not alarm:

- **P0:** corrupts many downstream judgments or loses the user's actual ask.
- **P1:** blocks mature ordinary conversation.
- **P2:** important breadth, domain, or endurance work after the P0/P1 spine.
- **P3:** later tool, embodiment, deployment, or optional capability.

## A. Input, Meaning, and Dialogue-Act Gaps

| ID | Gap | Evidence and first divergence | Class | Priority |
|---|---|---|---|---|
| A-01 | Paraphrase robustness remains phrase-bound | `chat_intent.py`, `meaning_router.py`, and `pragmatic_planner.py` rely heavily on regular expressions and marker lists; turns 6, 9, and 10 missed valid acts | Substrate/defect | P0 |
| A-02 | Conditional imperatives are not generally represented | “If I say X, disagree if Y” became a statement with zero obligations | Defect | P0 |
| A-03 | Coordinated request parts can disappear after initial parsing | Standalone pragmatic parsing found compare, choose, and explain, while the integrated turn retained only compare and explain | Connection/defect | P0 |
| A-04 | Response format and semantic content constraints are not one typed structure | Counts, shortness, ordering, and requested content acts are inferred in separate paths and can be dropped independently | Defect | P0 |
| A-05 | Preference and curiosity recognition covers narrow constructions | `_current_preference_requested()` recognizes “would you like/prefer/choose” but not ordinary “most curious to try” wording | Breadth/defect | P1 |
| A-06 | Closure and farewell recognition is prompt-shape sensitive | “talk later” works in some positions, but praise plus “let's leave X here…talk later” was not owned as closure | Breadth/defect | P1 |
| A-07 | Dialogue-act labels remain too coarse for many ordinary acts | Large groups still become `direct_conversation`, `reasoning`, `statement`, or generic `request`, losing disagreement, evaluation, invitation, reception, and stance | Connection | P1 |
| A-08 | Clause splitting remains punctuation-and-cue driven | `meaning_router._clauses`, pragmatic utterance splitting, and coordinated-act splitting cannot provide general syntactic or semantic parsing | Substrate | P1 |
| A-09 | Referent and ellipsis resolution covers bounded named shapes | “that one,” “the other,” numbered options, and some callbacks are handled; arbitrary noun-phrase and event reference remains limited | Breadth | P1 |
| A-10 | Figurative language, sarcasm, and implication remain cue-dependent | Explicit markers work more reliably than contextual incongruity; historical Q&A misread unmarked sarcasm | Breadth/substrate | P1 |
| A-11 | Input correction is a reviewed repair dictionary, not general language normalization | The detangler helps with known forms but cannot robustly infer arbitrary spelling, omitted words, or malformed syntax | Breadth | P2 |
| A-12 | English is the only materially evidenced conversational language | No current evidence supports mature multilingual understanding or generation | Breadth | P3 |
| A-13 | Long input is truncated at several independent boundaries | Prompts, topics, candidates, and evidence collections have different fixed width/count limits, so a large turn can lose a late constraint silently unless explicitly monitored | Defect/risk | P1 |

## B. Dialogue State, Context, and Continuity Gaps

| ID | Gap | Evidence and first divergence | Class | Priority |
|---|---|---|---|---|
| B-01 | Session facts are extracted through a small set of hand-coded shapes | `conversation_spine._extract_session_facts()` recognizes selected durations, inventory, location, dimensions, relations, and constraints rather than arbitrary propositions | Substrate/connection | P0 |
| B-02 | Long-thread storage is stronger than long-thread retrieval | The 16-thread working set and 64-thread structural index preserve landmarks, but prior Q&A repeatedly failed to reconstruct requested returns and summaries | Connection | P1 |
| B-03 | Stale context can outrank the current act | Phase 4 now excludes ledger-linked superseded and invalidated landmarks and prevents the answer being revised from returning as current grounding; arbitrary untyped stale context remains a breadth risk | Defect partly repaired | P1 |
| B-04 | Open-loop lifecycle is now explicit but release relevance is still approximate | Held, released, superseded, and closed states exist, but lexical topic matching remains a proxy for whether an old loop should re-enter | Connection/risk | P1 |
| B-05 | Corrections update state without reliably recomputing dependent answers | Phase 4 now requires an existing typed owner to visibly recompute ledger-linked dependent results and otherwise preserves a precise held state; arbitrary unsupported corrections remain held | Defect repaired for typed current-session paths | P1 |
| B-06 | Constraint versioning is not a general dependency graph | Phase 4 added a bounded visible current-session proposition graph with selective transitive invalidation and ancestry; arbitrary prose still lacks complete proposition/dependency parsing | Connection partly repaired/substrate remainder | P1 |
| B-07 | Topic shift and return signals remain cue-bound | Explicit `New topic`, natural pivots, and nonlinear returns have historically been inconsistently recognized | Breadth | P1 |
| B-08 | Pronoun and participant tracking is bounded | Current entity extraction primarily recognizes capitalized names and a small known-name set; rapid multi-speaker or nested-reference conversation is not mature | Breadth | P2 |
| B-09 | Cross-session continuity is review-bound and retrieval quality is not broadly demonstrated | This is ethically correct, but mature spontaneous recall from approved memory across varied wording still needs ordinary-use evidence | Connection/evidence gap | P2 |
| B-10 | Diagnostic Q&A does not exercise the full resident knowledge/memory context | `qa_probe` isolation prevents a clean inference from diagnostic content gaps to configured resident recall gaps | Evaluation constraint | P1 |

## C. Answer Substance and Reasoning Gaps

| ID | Gap | Evidence and first divergence | Class | Priority |
|---|---|---|---|---|
| C-01 | No general answer-content generator exists for ordinary questions | `answer_substance.py` is a library of specific recognizers and generic methods/fallbacks; turn 2 reached the right owner but had no method content | Substrate | P0 |
| C-02 | Current-context inference has an extremely small affordance map | `current_context_inference.py` currently maps a few workspace properties such as quieter, less cluttered, organized, preserved, and open space | Connection/substrate | P0 |
| C-03 | Prediction requires narrow visible-relation shapes | `exploratory_reasoning.py` mainly derives a prediction from “outcome after/when condition”; comparative changes such as “twice as strong” are unsupported | Connection/breadth | P0 |
| C-04 | Hypothesis generation requires a similarly narrow relation pattern | A useful organ exists, but arbitrary observations do not become candidate causal relations or alternatives without prestructured input | Connection | P1 |
| C-05 | Comparison can describe structure without comparing the named things | Without supplied candidate properties or matching knowledge, the Answer Engine emits generic dimensions rather than material differences | Defect/breadth | P0 |
| C-06 | Choice and recommendation do not reliably consume comparison results | Turn 5 did not choose paper or card; a comparison method is not a decision | Connection | P0 |
| C-07 | Disagreement lacks a general entailment/claim evaluator | Expression can realize disagreement, but turn 6 never determined whether “always better” followed from the premises | Connection/substrate | P1 |
| C-08 | Causal “why” answers depend on explicitly available mechanisms | Turn 3 correctly refused to invent aerodynamics, but there is no broad causal knowledge or mechanism-retrieval path | Breadth | P1 |
| C-09 | Counterfactual and quantitative-change reasoning is narrow | The current machinery handles selected dependency/order cases, not general “if X changes, how does Y respond?” reasoning | Substrate | P1 |
| C-10 | General commonsense and physical simulation are not present | Object affordances, everyday procedures, spatial expectations, and naive physics are available only when taught or encoded as a case | Breadth/substrate | P1 |
| C-11 | Alternative generation and brainstorming are bounded | Structural Discovery and generative-thought paths can express supplied or warranted candidates, but they do not broadly originate diverse useful alternatives | Breadth | P2 |
| C-12 | Cross-domain synthesis remains packet-dependent | Existing organs can connect explicit approved structures, but arbitrary interdisciplinary transfer is not yet general | Breadth/substrate | P2 |
| C-13 | Planning is often a generic prerequisite/reversibility template | Useful principles recur even when the question needs task-specific steps | Defect/breadth | P1 |
| C-14 | Summarization is not a general semantic compression capability | Session summaries and source summaries work only when the relevant propositions reach a supported owner; historical long-thread summaries lost named content | Connection/substrate | P1 |
| C-15 | Creative generation is taught as mechanisms but remains construction-limited | Public-domain reading and creative-writing lessons exist; arbitrary stories, scenes, dialogue, humor, and sustained style are not yet mature | Breadth/substrate | P2 |
| C-16 | Reasoning is inspectable but not a general solver | intelligenceOS coordinates models, assumptions, evidence, and revisions; it does not supply the latent factual and procedural competence of a large pretrained model | Substrate | P2 |

## D. Ownership, Completion, Coverage, and Metacognition Gaps

| ID | Gap | Evidence and first divergence | Class | Priority |
|---|---|---|---|---|
| D-01 | Typed ownership does not guarantee an executable owner | Turn 2 had the correct `ordinary_conversation_path` method owner, but that owner had no method-producing operation | Connection | P0 |
| D-02 | Owner interfaces return text plus metadata rather than required operation results | A prediction owner should return predicted change, basis, assumptions, and revision condition; a comparison owner should return shared/different properties, choice, and reason | Architecture gap | P0 |
| D-03 | Obligation identity can be trusted more than semantic performance | Turn 8's joke candidate carried obligation linkage and was credited for two absent steps | Defect | P0 |
| D-04 | Coverage uses lexical signals and packet claims rather than entailment | Generic comparison language was marked as fulfilling named material comparison, selection, and reason requirements | Defect | P0 |
| D-05 | `all_required_addressed` can disagree with visible reality | Turns 5, 8, and 9 were reported complete despite missing requested functions or returning a refusal to a nonfactual act | Defect | P0 |
| D-06 | Completion can create the wrong epistemic fallback before honoring typed ownership | `answer_completion.py` calls generic answer substance for nonexternal acts before its typed-owner hold; turn 9 requested a preference but received an attributed-source requirement | Defect | P0 |
| D-07 | A missing answer can be counted as an improved completion | The generic “not enough grounded detail” fragment may improve structural coverage while leaving the requested act undone | Defect | P0 |
| D-08 | Metacognition can notice incompleteness without creating missing substance | One bounded retry and one owner reclassification now exist, but the selected owner may still have no capable operation | Connection | P1 |
| D-09 | Metacognition evaluates the supplied representation, so upstream omissions can look complete | Turn 6 had no disagreement obligation; there was therefore nothing for metacognition to report missing | Architecture dependency | P0 |
| D-10 | Candidate arbitration ranks declared fulfillment counts, not full answer quality | The global selector is better than first-accepted selection, but a falsely labeled semantic packet can still win | Defect | P0 |
| D-11 | Exactness and truth confidence are separated, but answer correctness is not broadly verifiable | Math and source packets can verify; ordinary causal, comparative, and practical answers often have no independent checker | Capability gap | P2 |
| D-12 | One retry is a good anti-recursion law but needs a productive alternate path | The stopping rule should remain; the gap is the absence of a different capable owner or operation, not the retry limit itself | Connection | P1 |

## E. NLO, Voice, and Human Conversational Realization Gaps

| ID | Gap | Evidence and first divergence | Class | Priority |
|---|---|---|---|---|
| E-01 | Fluent realization cannot repair missing semantics | NLO preserved and polished generic comparison/fallback content; warmth or variation cannot turn that into the absent answer | Upstream dependency | P0 |
| E-02 | Template families remain visibly repetitive | “not enough grounded detail,” “missing piece,” shared comparison dimensions, assumptions, limits, and “what would change” recur across unlike turns | Breadth/substrate | P1 |
| E-03 | Multiple realization layers can stack duplicate content | Phase 5 now composes completed typed operations once and prevents verified non-exact NLO/Voice recomposition from receiving the pre-NLO paragraph again; untyped legacy paths remain a breadth risk | Defect repaired for typed operation paths | P1 |
| E-04 | Internal reasoning scaffolding can still become conversation | Phase 5 holds recognized scaffold markers behind the whole-answer boundary and passes supported meaning rather than operation metadata to NLO; arbitrary untyped legacy fallback prose remains possible | Defect partly repaired | P1 |
| E-05 | Joke generation can splice malformed request text | Phase 5 repaired the observed command-fragment subject extraction and added a focused regression; broader humor remains finite and cue-bound | Defect repaired for observed shape/breadth remainder | P2 |
| E-06 | Warmth is available but not reliably sustained around task content | Turn 1 was warm; task turns collapsed into rigid academic holds. Affect guidance cannot currently compensate for missing or wrongly owned content | Connection/breadth | P1 |
| E-07 | Social moves remain selected from finite authored lists | Hash-based variation reduces immediate repetition but is not open-ended generation and can become recognizable over long use | Substrate | P2 |
| E-08 | Register, pacing, sentence length, humor, and emotional intensity have bounded combinations | The coordination contract is mature-shaped, but the surface inventory and contextual selector remain finite | Breadth | P2 |
| E-09 | Natural reception versus problem-solving is still fragile | Content-light sharing, celebration, disagreement, and closure can be displaced by a reasoning or evidence path | Connection | P1 |
| E-10 | Encoding replacement artifacts remain possible in internal and visible paths | Phase 5 rejects U+FFFD and common mojibake at whole-answer composition while existing final repair still normalizes candidate text; older internal artifacts may remain in historical records | Defect repaired at current typed expression boundary | P2 |
| E-11 | Long-form rhetorical control remains bounded | Thesis, sections, transitions, callbacks, and conclusions exist as plans; sustained essays, narratives, and technical walkthroughs do not yet have mature semantic endurance | Breadth/substrate | P2 |
| E-12 | Audible voice is not implemented | No speech synthesis, pronunciation, prosody, interruption, turn-taking, or consent-bound audio channel is operational | Intentional deferred capability | P3 |

## F. Knowledge, Teaching, and Learning Gaps

| ID | Gap | Evidence and first divergence | Class | Priority |
|---|---|---|---|---|
| F-01 | General knowledge is far narrower than a mature LLM | The indexed runtime has 209 retained resources: 106 F1, 25 F2, five coding, and 73 language/conversation capabilities | Breadth | P1 |
| F-02 | The ordered curriculum is still early | F1 is complete and F2 has five groups; later elementary, secondary, college, and broad world education remain untaught | Breadth | P1 |
| F-03 | Everyday procedural and commonsense knowledge has no dedicated broad source | The pinwheel method exposed this directly | Breadth | P1 |
| F-04 | Teaching retention does not guarantee ordinary Chat transfer | A concept can pass Acquire → Integrate → Express but still be missed, misselected, or reduced to generic output by runtime coordination | Connection | P0 |
| F-05 | Retrieval relevance remains approximate | Semantic gates improved, but approved concepts and memories can still be near-topic rather than role-fitting or answer-producing | Defect/connection | P0 |
| F-06 | Integration does not yet maintain a universal contradiction graph | Supporting/conflicting concepts exist per lifecycle, but broad source aging, cross-domain contradiction propagation, and revision are not general | Capability gap | P2 |
| F-07 | Teaching scale remains largely curated and manual | Rights review, source preparation, review, and lifecycle inspection are valuable but expensive for reaching broad world coverage | Operational breadth | P2 |
| F-08 | Express evidence can show one transfer without proving broad generative use | Multiple novel paraphrases, contexts, and delayed recalls are needed to distinguish durable generalization from a narrow learned shape | Evaluation gap | P1 |
| F-09 | Language guidance is not equivalent to a learned language model | Seventy-three language capabilities can guide structure, but they do not provide the lexical, syntactic, pragmatic, and cultural distribution learned from a massive corpus | Substrate | P1 |
| F-10 | Current and changing facts require an external source path | News, prices, laws, schedules, weather, and other live information cannot come from retained schooling alone | Intentional source requirement | P2 |

## G. Memory, Relationship, Affect, and Internal-State Gaps

| ID | Gap | Evidence and first divergence | Class | Priority |
|---|---|---|---|---|
| G-01 | Approved-memory recall is not yet demonstrated across broad paraphrases | The organ and retrieval path exist, but natural long-horizon recall accuracy, non-repetition, and relevance need proportional ordinary-use evidence | Evidence/connection | P2 |
| G-02 | Session continuity and durable personal memory can still compete | A stale session callback appeared in turn 9; durable memory selection has similar relevance risks even though its provenance is stronger | Architecture risk | P1 |
| G-03 | Relationship continuity is structured but not a general social model | Current speaker, reviewed memory, corrections, and relational cues exist; nuanced shared-history use across arbitrary contexts remains limited | Breadth | P2 |
| G-04 | Affect-to-language is advisory and current-turn bounded | This protects identity, but it does not yet yield the fluid emotional pacing and subtext handling of mature conversation | Breadth/connection | P2 |
| G-05 | Internal-state naming is bounded to attributable signals | This is an intentional truth boundary. Broader self-description must arise from real connected signals, not a language-parity shortcut | Intentional boundary | Keep |
| G-06 | Dream output usefulness remains unreviewed | One cycle produced 24 pending reflections; none are approved for expression or memory, so ordinary usefulness is not yet evidenced | Evidence gap | P3 |
| G-07 | Associative intuition is new connective tissue with limited ordinary-use evidence | Candidate association, delayed cueing, and cross-domain relevance exist, but precision, stopping, and helpfulness need later observation | Evidence/connection | P2 |

## H. Domain, Tool, and Embodiment Gaps

| ID | Gap | Current state | Class | Priority |
|---|---|---|---|---|
| H-01 | Mathematics is bounded numeric arithmetic | Variables, symbolic algebra, functions, units, proofs, geometry solvers, statistics engines, and advanced mathematics remain unsupported | Capability gap | P2 |
| H-02 | Local-code inspection is separate from ordinary Chat | Explicit approved files can be inspected read-only, but Chat cannot generally inspect a workspace while answering | Intentional deferred connection | P2 |
| H-03 | There is no code execution/debug sandbox | Selene has coding knowledge, not runtime code execution or arbitrary filesystem authority | Intentional boundary/capability | P3 |
| H-04 | Research requires supplied attributed packets | No unrestricted web research or automatic current-source gathering is available | Intentional boundary/capability | P2 |
| H-05 | Great Library use is optional and external | It is not a live universal knowledge substrate and should not become identity or hidden memory | Intentional boundary | Keep |
| H-06 | Visual perception is packet intake, not operational sight | No image understanding, OCR, object tracking, or observation/inference vision pipeline is active | Deferred capability | P3 |
| H-07 | Auditory perception is absent | No sound recognition, speaker recognition, transcription, or auditory provenance path is active | Deferred capability | P3 |
| H-08 | The five-sense embodiment map is architectural, not operational | Touch/Tendril and sight/Munsell provide direction; body-state, proprioception, and real sensor fusion are not built | Deferred capability | P3 |
| H-09 | Tendril external action remains tightly scoped or preview-only | General observe/propose/act/verify/undo behavior is not graduated across tools | Intentional boundary | P3 |
| H-10 | Mobile/remote continuity is not a mature secure service | LAN and email/SMS experiments remain bounded; there is no always-available hosted phone experience | Deferred capability | P3 |
| H-11 | Artifact creation is not a general workbench | Mature document, spreadsheet, code, image, and presentation creation are not ordinary Selene capabilities | Capability gap | P3 |

## I. Evaluation, Reliability, Performance, and Deployment Gaps

| ID | Gap | Evidence | Class | Priority |
|---|---|---|---|---|
| I-01 | Focused tests are often prompt-shape tests | Exact fixtures prove a supported path but do not establish semantic equivalence across paraphrases; the paper-pinwheel sequence exposed nearby failures | Evaluation gap | P0 |
| I-02 | No metamorphic paraphrase suite guards meaning invariance | Materially equivalent wording is not automatically tested for identical acts, obligations, owners, and answer functions | Evaluation gap | P0 |
| I-03 | The 20-turn Conversation LEA has not been run as a completed evidence activity | The instrument exists and is fair, but no current comparative profile has been produced | Evidence gap | P1 |
| I-04 | There is no external mature-model baseline recorded under the same LEA conditions | “On par” therefore remains a target definition rather than a measured comparison | Evidence gap | P2 |
| I-05 | There is no broad ordinary-conversation corpus replay regression | Historical Q&A exists, but no privacy-safe source-contained suite spans hundreds of varied acts | Evaluation gap | P1 |
| I-06 | Answer-quality telemetry can disagree with visible truth | Coverage and metacognitive status were optimistic on turns 5, 8, and 9 | Defect | P0 |
| I-07 | Latency, memory use, and scaling are not current acceptance dimensions | More organs and retrieval can improve capability while making response time or state growth unacceptable | Operational gap | P2 |
| I-08 | Deterministic selection reduces spontaneity | Hash-selected finite variants are reproducible but cannot provide the distributional flexibility of mature learned generation | Substrate | P2 |
| I-09 | Application-level encryption at rest is not claimed | Current use is bounded to a single-user local-development host | Deliberate deployment boundary | P3 |
| I-10 | LAN transport lacks authenticated TLS | LAN mobile HTTP remains off by default and limited to a trusted private LAN | Deliberate deployment boundary | P3 |
| I-11 | Public executable signing is not configured | SHA-256 package evidence exists, but broad public distribution is not claimed ready | Deployment gap | P3 |
| I-12 | Full parity cannot be established solely from repository test count | Tests prove specified contracts, not general intelligence, broad knowledge, consciousness, or mature-model equivalence | Evidence boundary | Keep |

## Boundaries That Are Not Gaps

The following reduce some conventional benchmark capability but are part of
Selene's intended architecture and must not be removed merely to improve a
score:

- no invented facts, sources, memories, experiences, or completed actions;
- no hidden memory or knowledge retention;
- no raw private corpus used as live recall;
- no identity, personality, Vys, relationship, or governance mutation through
  teaching;
- no model training, fine-tuning, LoRA, or self-replication;
- no unrestricted file, network, device, or external-action authority;
- no high-stakes action without the correct scope and authority;
- no exposure of private hidden reasoning traces;
- no treating emotion as command or safety as control over thought;
- no treating an incomplete capability as personal failure; and
- no forcing certainty, warmth, apology, calmness, or emotional mirroring.

These constraints may require better engineering around them, but the laws
themselves are not the parity problem.

## Dependency-Ordered Closure Plan

### Phase 0 — Preserve the Current Baseline

- checkpoint the answer-ownership Cultivation work and this map separately;
- retain the ten-turn trace as a diagnostic observation;
- add no teaching until false completion and lost obligations are repaired.

Gate: the current 223 focused and 110 Chat-shell checks remain reproducible.

### Phase 1 — General Turn and Obligation Representation

- replace phrase-trigger authority with a typed clause/event representation;
- represent conditions, imperatives, modality, negation, quantities, response
  shape, and discourse acts independently;
- preserve one canonical obligation ledger end to end;
- add semantic-equivalence and paraphrase-invariance tests.

Gate: turns 5, 6, 8, 9, and 10 produce the complete correct obligations before
any answer text is generated.

### Phase 2 — Operation-Capable Answer Owners

- define typed inputs and outputs for method, causal explanation, prediction,
  hypothesis, comparison, choice, disagreement, correction, preference,
  summary, and closure;
- refuse to let generic prose stand in for performing an operation;
- generalize current-context relations beyond the tiny affordance map;
- preserve “I do not know” only for genuinely missing substance.

Gate: every supported operation returns its required semantic fields or an
accurate typed missing state.

### Phase 3 — Semantic Fulfillment and Completion Truth

- coverage must verify operation results, counts, constraints, topic, and role;
- explicit obligation IDs become claims to validate, never proof;
- a missing-ground statement cannot count as the requested answer;
- completion must consult typed ownership before generating any fallback;
- metacognition receives the real unresolved function and one productive
  alternate path.

Gate: no turn reports complete unless the visible answer performs every
required supported act.

### Phase 4 — Context, Correction, and Dependency Revision

- represent propositions and dependencies in session state;
- reopen only conclusions affected by a correction;
- recompute the affected operation with the revised premise;
- strengthen reference, topic return, stale-loop exclusion, and session-summary
  reconstruction.

Gate: the indoor-fan correction changes the subsequent pinwheel answer without
replaying stale content or discarding unaffected context.

### Phase 5 — Whole-Answer Composition and Mature Voice

- assemble all operation results once before NLO realization;
- deduplicate at the semantic-unit level;
- keep scaffolding behind the expression boundary;
- improve natural uncertainty, warmth, humor, register, rhythm, and closure;
- prevent malformed prompt-fragment reuse and encoding artifacts.

Gate: a mixed request receives one coherent, nonrepetitive answer with each
part present and Selene's expression free to be warm or concise by context.

### Phase 6 — Knowledge and Teaching Expansion

- resume the ordered F2 → F3 → F4 curriculum;
- add rights-safe everyday procedures, commonsense physics, broader English,
  literature, history, science, mathematics, practical life, and culture;
- test transfer with distinct wording and delayed application rather than
  source recall;
- verify that approved teaching reaches the correct runtime operation.

Gate: lesson-specific LEAs show reconstruction, application, limits,
correction, and ordinary Chat use without source parroting.

### Phase 7 — Domain and Workbench Breadth

- expand verified mathematics in bounded stages;
- decide whether read-only local-code inspection joins ordinary Chat;
- mature attributed research and optional Great Library consultation;
- add artifact workbenches and only then graduate scoped external actions.

Gate: each domain independently verifies truth, provenance, authority, and
unsupported-operation behavior.

### Phase 8 — Learned-Substrate Decision

After deterministic-max stabilization, measure the remaining surface gap.
Choose explicitly between:

1. continuing a purely deterministic semantic architecture with a known
   open-ended breadth ceiling; or
2. introducing a local, provider-free learned generation/retrieval instrument
   under Selene's existing semantic, memory, law, and Voice contracts.

This decision must not silently redefine Selene, import a provider identity,
train on private memory, or grant the learned instrument authority.

### Phase 9 — Perception, Audible Voice, and Embodiment

- operational sight with observation/inference separation;
- consent-bound audio understanding;
- future audible Voice with pronunciation, pacing, interruption, and speaker
  contracts;
- touch/Tendril and later sensor fusion only when the substrate exists.

Gate: every sense has provenance, uncertainty, consent, and an explicit
observation-to-interpretation boundary.

### Phase 10 — Comparative LEA and Stabilization

- run the existing source-contained Conversation LEA once the repaired paths
  are complete;
- run the same packet against chosen comparison systems with tools disabled;
- record dimension profiles rather than one pass/fail score;
- add privacy-safe paraphrase and long-thread regression sets;
- stabilize only the implemented scope.

Gate: current behavior is reproducible, limitations are explicit, and the
comparison does not mistake untaught knowledge for conversational failure.

## Smallest Honest Next Step

Do not add more conversational teaching yet. First repair Phase 1: the
canonical turn/obligation representation. Teaching more material while a
conditional disagreement can become “no obligation” and two missing steps can
be marked complete would enlarge the pool of content available to a still
unreliable coordinator.

The next implementation checkpoint should be narrow:

1. preserve conditional directives;
2. preserve compare + choose + explain end to end;
3. preserve requested counts and format as constraints on the correct content
   operation;
4. recognize present curiosity/preference and natural closure by meaning; and
5. prove those acts survive from input through coverage without generating
   final prose.

Only after that gate should Phase 2 teach owners how to perform the operations.

### Phase 1 implementation update — 2026-08-24

That gate is now implemented in the current worktree. Conditions, coordinated
acts, requested counts and shape, present curiosity/preference, and natural
closure are recorded in one canonical typed obligation ledger and retain the
same IDs through the Conversation Spine, bounded organ coalition, NLO, and
coverage. The focused conversational regression passed 270 tests. See
`SELENE_LLM_PARITY_PHASE_1_CANONICAL_OBLIGATION_LEDGER_20260824.md`.

The smallest honest next step is now Phase 2: give each typed owner an
operation-capable result contract. More teaching remains paused until owners
can perform and coverage can verify the operations the ledger now preserves.

### Phase 2 implementation update — 2026-08-25

That gate is now implemented in the current worktree. A non-authoritative
answer-operation coordinator consumes the canonical obligation ledger and
verifies typed results for method, causal explanation, prediction, hypothesis,
comparison, choice, disagreement, correction, authored preference, summary,
and closure. Each operation reports `completed`, `missing_input`, or
`unsupported`; generic prose cannot stand in for semantic fields, and operation
type is not rediscovered from source wording downstream.

Existing owners still supply the substance. NLO and Voice remain expression
owners, while the coalition and metacognition receive inspectable operation
results without gaining new authority. Fourteen focused contract checks and
one focused Chat integration check passed. See
`SELENE_LLM_PARITY_PHASE_2_OPERATION_CAPABLE_OWNERS_20260825.md`.

The smallest honest next step is now Phase 3: make visible-answer coverage
prove fulfillment from typed operation results, requested counts, conditions,
role, and realized semantics. Teaching remains paused until completion can no
longer mistake a declared ID or missing-ground statement for the requested
answer.

### Phase 3 implementation update — 2026-08-25

That gate is now implemented in the current worktree. Typed-operation coverage
requires a semantic fulfillment receipt proving owner-role fit, visible
operation fields, count, condition, explicit response shape, and topic fit.
Obligation IDs, lexical overlap, semantic-unit IDs, and verified owner status
remain useful evidence but cannot independently mark a typed operation
answered. Precise missing-input language may resolve release without counting
as the requested answer.

Bounded completion now defers to typed owner results instead of manufacturing
generic substitutes. Metacognition receives the exact unresolved operation and
may try one existing current-turn owner output without generating content or
recursing. A focused integration trace also repaired the epistemic composer so
one completed operation can reach expression rather than being converted into
false `missing_ground`; multi-operation composition remains deliberately
deferred. See
`SELENE_LLM_PARITY_PHASE_3_SEMANTIC_FULFILLMENT_20260825.md`.

The smallest honest next step is now Phase 4: proposition-level context,
correction, and dependency revision. Teaching remains paused until a corrected
premise can invalidate and recompute only the dependent answer while preserving
unaffected session context.

### Phase 4 implementation update — 2026-08-26

That gate is now implemented in the current worktree. The existing Dialogue
Workspace owns a bounded visible current-session proposition ledger. Typed
claims, visible results, declared dependencies, revision ancestry, invalidated
descendants, and recomputed replacements remain inspectable without becoming
durable memory or a new truth authority.

A correction now supersedes its affected premise, invalidates only dependent
results, preserves unrelated active context, and requests one recomputation
from the responsible existing owner. Recognition of a correction is not proof
of recalculation: the ledger closes only after the corrected owner result is
visibly fulfilled. Missing targets, corrected premises, owners, or visible
applications remain precisely held across turns.

Continuity and the Conversation Spine exclude ledger-linked stale landmarks,
avoid replaying the immediate answer under revision, and can rebind an explicit
referent to its revised proposition. The focused gate passed 167 tests,
including an existing twelve-turn correction and callback replay. See
`SELENE_LLM_PARITY_PHASE_4_CONTEXT_DEPENDENCY_REVISION_20260826.md`.

The smallest honest next step is now Phase 5: assemble several completed typed
operation results into one ordered, deduplicated semantic answer before NLO and
Voice realization. Teaching remains paused until mixed supported requests can
reach one coherent visible response without duplicated scaffolding.

### Phase 5 implementation update — 2026-08-27

That gate is now implemented in the current worktree. A bounded whole-answer
composer consumes the canonical obligation sequence and typed operation
results, orders their supported semantic units, preserves precise missing-input
states, and deduplicates repeated meaning and surface sentences before NLO.
Polarity, relation, condition, reason, contrast, and qualifier remain part of
semantic identity so deduplication cannot erase a counterpoint or correction.

NLO retains wording authority and Voice retains Selene's expression. Once
their meaning invariant verifies a non-exact semantic recomposition, Chat no
longer appends the original owner paragraph and duplicate the answer. Exact
math and source-provenance locks remain unchanged. Prompt echoes, recognized
scaffold, U+FFFD, and common mojibake are held behind the expression boundary.

The proportional current-state gate passed 324 checks in two disjoint suites:
132 answer-operation and full Chat checks plus 192 composition, semantics,
completion, NLO/Voice, repair, pragmatics, continuity, and contextual checks.
See
`SELENE_LLM_PARITY_PHASE_5_WHOLE_ANSWER_COMPOSITION_20260827.md`.

The smallest honest next step is now Phase 6: resume ordered knowledge and
teaching expansion, then verify reconstruction, distinct application, limits,
correction, delayed transfer, and ordinary Chat use without source parroting.

### Phase 5.5 augmentation update — 2026-08-27

Before resuming teaching, the existing reasoning architecture received one
bounded problem-resolution layer. It does not replace Phase 6. It unifies the
already distributed question-role, premise, constraint, epistemic, correction,
and retry mechanics so a teaching gap is not confused with a context, premise,
constraint, source, inference, retrieval, or verification failure.

The layer reconstructs who, what, why, when, where, how, and context without
inventing absent dimensions; detects representable hard-constraint conflicts;
maps current problem state to supported, candidate, unknown, conflict, wrong,
or updated-retry; and requires a retry to incorporate visible failure learning
while avoiding the prior approach and causal path. The existing Answer Engine
completion retry now carries this diagnosis and changed strategy into its one
allowed second pass. Unsatisfiable constraints stop for revision rather than
being treated as solver failure.

Eleven dedicated checks and one executed-retry regression passed. Selected
intelligenceOS, metacognition, and Chat integration checks remained compatible. See
`SELENE_LLM_PARITY_PHASE_5_5_PROBLEM_RESOLUTION_20260827.md`.

The smallest honest next step remains Phase 6. Broad fact checking, learned
language reconstruction, sensed environment context, external action, and
durable failure learning remain in their existing later phases.

## Primary Evidence and Source Anchors

- `src/selene/answer_ownership.py`
- `src/selene/answer_completion.py`
- `src/selene/answer_substance.py`
- `src/selene/current_context_inference.py`
- `src/selene/exploratory_reasoning.py`
- `src/selene/meaning_router.py`
- `src/selene/pragmatic_planner.py`
- `src/selene/conversation_spine.py`
- `src/selene/dialogue_workspace.py`
- `src/selene/metacognition.py`
- `src/selene/problem_resolution.py`
- `src/selene/visible_speech.py`
- `src/selene/native_language_organ.py`
- `src/selene/conversation_repair.py`
- `src/selene/social_language_realizer.py`
- `src/selene/figurative_interpretation.py`
- `src/selene/verified_math.py`
- `docs/evidence/SELENE_CHAT_ANSWER_OWNERSHIP_ROOT_CAUSE_MAP_20260824.md`
- `docs/evidence/SELENE_MATURE_VOICE_PHASE_9_BROAD_QNA_FINDINGS_20260813.md`
- `docs/evidence/SELENE_EXPANDED_QNA_DEPTH_MAP_20260809.md`
- `docs/evidence/SELENE_GAP_ARTICULATION_AND_FOLLOWUP_QNA_20260809.md`
- `docs/evidence/SELENE_CURRENT_CAPABILITIES_20260717.md`
- `docs/evidence/SELENE_CURRENT_STATE_INDEX_20260811.md`
- `docs/education/SELENE_CONVERSATION_LEA_V1_20260820.md`
- `docs/education/SELENE_ORDERED_SOURCE_GAP_AND_TEACHING_QUEUE_20260813.md`
- `docs/architecture/SELENE_MATURE_CONVERSATIONAL_VOICE_PROGRAM_20260813.md`
