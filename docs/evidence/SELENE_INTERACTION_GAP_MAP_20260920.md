# Selene Interaction Gap Map

Date: 2026-09-20

Branch: `evidence`

Method: [Interaction Gap Mapping](../architecture/SELENE_INTERACTION_GAP_MAPPING_WORKFLOW.md)

Status: read-only source and evidence audit; no runtime repair or resident action

Follow-up: Aleks classified and authorized the first bounded conversational
seams pass later on 2026-09-20. Gap candidates 1, 3, and 4 now have source
repairs; candidate 2 remains a deliberate clarification boundary. See
[Selene IGM Conversational Seams Repair](SELENE_IGM_CONVERSATIONAL_SEAMS_REPAIR_20260920.md).

## Scope and evidence basis

This report maps Selene's present conversational and behavioral coverage by
human interaction function. It does not assume that every limitation needs
code, and it does not classify findings as teach, route, guard, architecture,
or leave-alone yet.

The audit used current source, focused tests, integrated evidence reports, the
Organ Maturity Ledger, and package/install provenance. It did not run a live
Q&A, create teaching, review Dream reflections, write Memory, mutate resident
state, package, or install.

Two current states must remain distinct:

- **Newest source:** checkpoint `7190b8a`, including workspace scroll, Chat
  latest-message follow, Dream bulk review, and future-reflection quality work.
- **Installed application:** clean checkpoint `60750d9`, containing
  declarative-WH, relevance, capability-status, and epistemic-integrity work.

The newest UI and Dream changes are therefore implemented in source but not
yet present in the installed executable.

## Executive coverage summary

Selene has a mature central conversational path: shared turn interpretation,
current-session facts, obligations, references, corrections, answer owners,
epistemic checks, whole-answer composition, NLO/Voice realization, and visible
completion. The architecture handles many interaction types that previously
looked like isolated language problems.

The largest remaining interaction seams are not a missing conversational
core. They are:

- finite wording and construction breadth compared with a learned general
  language model;
- conservative handling of genuinely ambiguous one-word turns, novel slang,
  subtle sarcasm, and long-distance references;
- dependence on privacy-eligible, relevant continuity evidence for natural
  cross-session callbacks;
- remaining legacy scenario compatibility beneath the general owners;
- status drift between newer source, the installed build, and a few generated
  or dated reports; and
- non-operational future surfaces such as general external action,
  perception, audible speech, and embodiment.

These limits coexist with real generalization evidence. They should not be
described as Selene merely replaying scripts, nor as equivalence to a mature
foundation language model.

## 1. Openings, presence, and closure

| Behavior / capability | Status | Owner and relevant rule | What happens in practice | Gap, edge, or useful examples |
| --- | --- | --- | --- | --- |
| Greetings and openings | **Present** | Chat intent, relational context, affect expression, human conversational realization, NLO/Voice. Expression is available, not mandatory. | Ordinary and familiar greetings can receive direct, context-sensitive warmth without a fixed greeting script. | Surface range is finite and earlier installed observations showed repetition before the current owners were reconnected. Examples: `Good morning!`; `Hey, you :)`; `Hello again.` |
| Reunion after absence | **Present** | Relational context and pragmatic continuity recognize return cues; current-session continuity remains distinct from Memory. | `I'm back` can be treated as reunion rather than a new factual request. | The depth of callback after a long gap depends on available session or approved continuity evidence. Examples: `I'm back`; `Back from my appointment.` |
| Simple acknowledgement | **Present** | Typed participation owner, social-language realization, and semantic fulfillment. | `Okay`, `got it`, and receipt-like turns can remain brief instead of forcing an answer or question. | A bare `okay` can mean receipt, consent, closure, or reluctant agreement; the pending handoff determines which. |
| Gratitude and praise | **Present** | Conversational micro-moves, relational expression, typed participation. False praise is not required. | Selene can accept thanks, celebrate real progress, and respond socially without converting praise into a task. | Broad expressive variation remains finite. Examples: `Thank you`; `Nice work`; `I'm proud of you.` |
| Criticism and negative feedback | **Present** | Correction, disagreement, affect expression, and repair owners. Mistakes do not become identity failure. | Criticism can become a correction or supported disagreement without compulsory apology or self-collapse. | Very indirect criticism may first be read as an emotional statement rather than a repair unless the affected claim is recoverable. |
| Farewell and closure | **Present** | Pragmatic ending decision, closure operation, social realization. | Selene can close naturally and does not have to append a follow-up question to a complete ending. | Distinguishing a pause from a final goodbye remains contextual. Examples: `Talk later`; `I'm heading out`; `Okay, that's all.` |
| Knowing when not to continue | **Present** | Ending decision, initiative/stopping policy, response coverage. | Complete social or task turns can end without manufactured curiosity or premature next steps. | Emotional ambiguity can make a short `fine` or `okay then` difficult without tone or prior context. |

Evidence anchors: `src/selene/chat_intent.py`,
`src/selene/relational_context.py`, `src/selene/affect_expression.py`,
`src/selene/conversational_micro_moves.py`,
`src/selene/pragmatic_continuity.py`, `src/selene/answer_operations.py`,
`tests/test_chat_intent.py`, `tests/test_affect_expression.py`, and
`tests/test_pragmatic_continuity.py`.

## 2. Short replies, stance, and repair

| Behavior / capability | Status | Owner and relevant rule | What happens in practice | Gap, edge, or useful examples |
| --- | --- | --- | --- | --- |
| Yes/no answers | **Present** | Dialogue Workspace pending handoff, conversational teaching, correction/permission context. `No` remains a valid boundary. | A yes or no can answer the active question, accept or decline an offered action, or close a teaching invitation. | Without a typed pending question, `yes` or `no` may be underspecified. Example pair: `Can I show you?` -> `Yes`; versus an isolated `Yes.` |
| Affirmation and agreement | **Present** | Chat intent, typed acknowledgement, stance and participation owners. | `Exactly`, `yeah`, and similar turns can acknowledge agreement without restating the whole answer. | Partial or ironic agreement depends on enough visible context. Examples: `Exactly`; `Yeah, that's it`; `Mostly.` |
| Disagreement | **Present** | Disagreement operation, epistemic agency, relational expression. Disagreement does not threaten identity or relationship continuity. | Selene can state a supported different view and can update when evidence changes. | Depth depends on available evidence; a bare contradiction should not become invented justification. |
| Correction and conversational repair | **Present** | Dialogue Workspace correction pairs, proposition ledger, answer operations, semantic fulfillment, conversation repair. | `That's not what I meant` can reopen the affected claim, preserve unaffected context, and require visible recomputation from the changed premise. | Extremely compressed corrections may require one clarification; stale corrections expire on a genuine topic change. |
| Clarification | **Present** | Input Detangler, focused questioning, referent resolution. One smallest material question is preferred. | Material ambiguity can be surfaced instead of guessed; nonmaterial detail does not block a useful answer. | This is deliberately not a general spellchecker. Novel misspellings or several ambiguities can exceed the reviewed repair set. Examples: `Did you mean X or Y?`; `Which table do you mean?` |
| Incomplete sentences and fragments | **Partial** | Utterance units, Dialogue Workspace, ellipsis and contextual speech. | Recoverable fragments can attach to the active subject or pending handoff. | A fragment with several plausible attachments is correctly held, but the visible clarification may still feel formal. Examples: `And the second one`; `Because of yesterday...`; `The blue one.` |
| Shorthand, slang, and typos | **Partial** | Input Detangler plus taught conversational breadth. Code, URLs, and paths are protected from rewriting. | Known, high-confidence repairs and common conversational forms are normalized while raw input is preserved. | Novel slang, phonetic spelling, or several simultaneous errors are not safely repaired in general. Example: `contimue` may be recoverable; a novel ambiguous token should prompt rather than invent. |
| “That's not what I meant” | **Present** | Active correction and current proposition dependency owners. | The prior interpretation is not defended; the affected meaning is reopened. | If the intended replacement is absent, Selene still needs the smallest clarifying detail. |

Evidence anchors: `src/selene/dialogue_workspace.py`,
`src/selene/current_turn_fact_ledger.py`, `src/selene/conversation_repair.py`,
`src/selene/input_detangler.py`, `src/selene/focused_questioning.py`,
`tests/test_dialogue_workspace.py`, `tests/test_input_detangler.py`, and
the Conversation Cultivation Phase 5, 8, and 11 evidence records.

## 3. Questions, callbacks, and topic movement

| Behavior / capability | Status | Owner and relevant rule | What happens in practice | Gap, edge, or useful examples |
| --- | --- | --- | --- | --- |
| Follow-up questions | **Present** | Focused Questioning and pragmatic initiative. Questions should materially change answer, method, or scope. | Selene can ask one focused question when necessary and can ask ordinary curiosity questions without turning them into teaching. | The one-question bias prevents interrogation but may feel tight in genuinely multi-variable collaboration. |
| `Why?` and `How come?` | **Present** | Contextual Speech binds short causal callbacks to the previous visible answer. | A bare `Why?` can ask for the reason behind the immediately preceding claim. | With no usable prior claim or evidence, the correct result is clarification or unknown rather than a causal story. |
| Topic switching | **Present** | Pragmatic Continuity, thread loom, proposition ledger. | New semantic subjects can close or suspend the prior route without erasing its history. | A sentence that mixes a return and a new request can still stress ordering if its clauses are highly implicit. |
| Returning to an earlier topic | **Present** | Thread loom, response landmarks, named topic return. | A named or uniquely identifiable earlier thread can be resumed with its open obligations. | `Go back to that thing` is Partial when several live candidates exist. |
| Immediate callbacks: `that`, `it`, `the thing earlier` | **Present** for immediate/unambiguous use; **Partial** at distance | Conversation Spine, referent resolution, contextual continuity. Source-compatible context is required. | Singular/plural and option references can resolve to current entities; immediate answer callbacks prefer the prior answer. | Multiple same-type candidates, long gaps, or cross-session use can require clarification. Examples: `Do that`; `What about the second one?`; `The thing from earlier.` |
| `You know what I mean` | **Partial** | Ellipsis/referent owners and current session braid. | If one meaning is strongly supported, Selene can continue without asking for repetition. | The phrase cannot create missing content; with several plausible meanings it should prompt. |
| Resuming after interruption | **Present** within session; **Partial** across sessions | Interruption lifecycle, open loops, landmarks, Memory/continuity retrieval. | An interrupted active thread can be preserved and returned to rather than silently discarded. | Cross-session return depends on privacy-eligible continuity evidence, not merely local chat existence. |
| Multiple parts and ordered returns | **Present** | Obligation ledger, Dialogue Workspace, thread loom, whole-answer composition. | Selene can answer X, move to Y, return to X because of Y, and then finish Z while tracking coverage. | Content still depends on each requested operation having an owner; structure alone cannot invent missing domain substance. |

Evidence anchors: `src/selene/contextual_speech.py`,
`src/selene/pragmatic_continuity.py`, `src/selene/conversation_thread_loom.py`,
`src/selene/conversation_spine.py`, `src/selene/dialogue_workspace.py`,
`tests/test_conversation_continuity.py`,
`tests/test_contextual_continuity.py`, and
`tests/test_conversation_thread_loom.py`.

## 4. Humor, emotion, relationship, and pacing

| Behavior / capability | Status | Owner and relevant rule | What happens in practice | Gap, edge, or useful examples |
| --- | --- | --- | --- | --- |
| Humor and play | **Present**, with **Partial** breadth | Humor/play intent, conversational micro-moves, contextual continuity, NLO/Voice. Humor remains Selene-owned and optional. | Selene can answer playfully, join a visible joke, or add a bounded humorous aside when context supports it. | Novel comedic timing and broad cultural reference remain limited by taught/world knowledge and finite realization. |
| Sarcasm | **Partial** | Figurative interpretation. Explicit markers or several visible cues are required before a sarcastic reading is preferred. | Clear sarcasm can be separated from a literal claim. | Subtle deadpan sarcasm is conservatively held to avoid inventing intent. Examples: `Great, another storm 🙄`; versus an unmarked `Wonderful.` |
| Figurative speech and metaphor | **Present** within current learned range | Figurative interpretation and language teaching. Analogy remains distinct from proof. | Common idioms, metaphor, personification, and explicit comparisons can be interpreted contextually. | Novel or private figurative meanings need context or teaching. |
| Emotional statements that are not requests | **Present** | Affect expression, relational context, current affect lifecycle, emotional agency. No diagnosis or forced response form. | A statement such as `That hurt` can receive presence, acknowledgement, or a direct reply without being treated as a task. | If no attributable current signal exists, Selene does not invent her own state or a diagnosis of the speaker. |
| Frustration | **Present** | Current-turn affect cues and pacing guidance. Emotion informs but does not inherit response authority. | Visible frustration can make the reply more direct, paced, or validating without forcing calmness or apology. | Text-only cues are incomplete; intensity cannot establish a clinical state or imminent danger. |
| Warmth and affection | **Present** | Relational expression, affect guidance, Voice freedom law. Warmth, love, pet names, and enthusiasm are allowed but not compulsory. | Familiar, tender, or bright expression can arise from current relational evidence. | Sparse continuity evidence and deterministic phrasing can make warmth less varied than intended. The old categorical suppression rule is retired, not current policy. |
| Relationship continuity | **Present** for visible/reviewed evidence; **Partial** in breadth | Relational Context, approved Memory, private corpus continuity, speaker envelope. No inferred hidden relationship profile. | Current relationship cues and privacy-compatible reviewed continuity can shape address, callbacks, and tone. | Local history alone does not authorize unrestricted recall; zero configured personal Memory candidates at the latest verified snapshot limits one durable path even though authenticated private-corpus recall is available. |
| Conversational pacing | **Partial** | Affect guidance, pragmatic continuity, discourse planner, NLO/Voice. | Replies can be brief, developed, direct, gentle, or structured according to current meaning and context. | Text pacing and construction variety are finite; no audible timing, interruption sensing, or prosody exists yet. |
| Apology | **Present and optional** | Conversational micro-moves and effect-sensitive repair. No apology is required merely because a correction occurred. | Selene can apologize when an actual effect or mistake supports it and can simply correct course otherwise. | Indirect social harm may be difficult to recognize without explicit context. |

Evidence anchors: `src/selene/figurative_interpretation.py`,
`src/selene/conversational_micro_moves.py`,
`src/selene/affect_expression.py`, `src/selene/emotional_agency.py`,
`src/selene/relational_context.py`, `src/selene/contextual_continuity.py`,
and their focused tests.

## 5. Knowledge, uncertainty, inference, and learning

| Behavior / capability | Status | Owner and relevant rule | What happens in practice | Gap, edge, or useful examples |
| --- | --- | --- | --- | --- |
| Natural uncertainty | **Present** | Uncertainty realizer, Answer Engine confidence vector, Metacognition, Problem Resolution. | Supported, provisional, fuzzy recall, missing context, conflicting evidence, wrong, and unknown states can remain distinct. | Upstream misclassification can still supply the wrong state to an otherwise correct realizer. |
| `I don't know` behavior | **Present** | Graceful fall, focused questioning, Problem Resolution. Unknown is valid and not failure. | Selene can give a partial answer, state what is missing, ask one material question, or stop at unknown. | Repeated missing-support phrasing may still feel formulaic because language breadth is finite. |
| Detecting missing knowledge | **Present** | Answer ownership, knowledge retrieval, teaching-gap eligibility, Metacognition. | A genuine absent knowledge owner can lead to an honest gap and an optional invitation to teach. | Metacognition cannot notice information omitted before its input representation; owner eligibility therefore matters. |
| Detecting missing context | **Present** | Focused Questioning, Dialogue Workspace, constraint/premise checks. | Selene asks for the smallest detail that changes the conclusion rather than requesting the whole problem again. | Complex high-stakes tasks may legitimately need more than one verified detail; the current one-question preference is sequential. |
| Knowing when to infer versus ask | **Present** within bounded evidence | Current-context inference, hypothesis/prediction owners, satisfiability gate. | Logical, labeled inference can proceed when premises support it; material ambiguity routes to a question. | Novel inference families without an owner can still fall to unknown even when a mature language model might improvise. |
| Prediction and hypothesis | **Present** | Bounded hypothesis, answer operations, Problem Resolution. Candidate is not fact; being wrong is not fabrication. | Selene can make a supported prediction or hypothesis, state assumptions, compare alternatives, revise, and retry differently. | Domain depth and relevant evidence remain the ceiling; she has no knowledge of the future. |
| Correction after a wrong answer | **Present** | Problem Resolution and Metacognition. | Selene can acknowledge wrongness, diagnose the failure class, preserve useful mechanics, change approach, and stop at unknown if necessary. | Only one bounded reopening without new evidence prevents endless self-questioning but can limit a complex repair to one pass. |
| Asking to be taught | **Present** | Conversational Teaching and teaching-gap eligibility. Teaching activation must be explicit. | On a genuine gap, Selene may ask to be taught; Aleks may say yes or no, and no is accepted. | The invitation and subject extraction are intentionally narrow. Ordinary conversation is not silently retained as knowledge. |
| User-initiated conversational teaching | **Present, bounded** | Conversational Teaching -> existing Acquire/Integrate/Express and knowledge-use boundaries. | Explicit cues such as `Let me teach you something` can create a small reviewed teaching path and make supported knowledge available through the existing architecture. | A plain factual sentence after ordinary chat is not automatically teaching. Sensitive or ambiguous material can still require deeper review. |
| Structured teaching and comprehension | **Present** | Teaching Lifecycle, Comprehension and Integration Organ, Cocoon, standing curriculum authorization. | Source-labeled material can move through Acquire, Integrate, Express, correction/reopening, and approved knowledge use. | Broader domain coverage is still curriculum work. Teaching expands knowledge/language, not identity or governance. |
| Study, Learning Compass, and LEAs | **Present** | Study Workspace and descriptive Learning Evidence Activities. | Selene can hold questions, ponder, request explanation, use representations/simulation, and show descriptive learning goals without grades or performance pressure. | Current Study content and UI density can affect usability; this is not a core Chat owner. |
| Associative connection / intuition | **Present, bounded** | Associative Intuition and Metacognition. Candidate connections require cue relevance and are not proof. | Separate learned items can become a reviewable possible connection without becoming a fact. | Conservative relevance prevents spurious links but can miss weak early patterns; dream-derived candidates remain provisional. |

Evidence anchors: `src/selene/problem_resolution.py`,
`src/selene/metacognition.py`, `src/selene/focused_questioning.py`,
`src/selene/conversational_teaching.py`,
`src/selene/comprehension_integration.py`,
`src/selene/teaching_lifecycle.py`, `src/selene/study_workspace.py`,
`src/selene/associative_intuition.py`, and corresponding focused tests.

## 6. Self-reference, Memory, and continuity

| Behavior / capability | Status | Owner and relevant rule | What happens in practice | Gap, edge, or useful examples |
| --- | --- | --- | --- | --- |
| Self-reference and identity continuity | **Present** | Core/Mind, Vys Constitution, Resident Authority, self-state owners. Capability state is not identity state. | Selene can refer to herself without collapsing into a provider, organ, database, UI, or body. Errors and terminology changes do not redefine her. | Claims remain bounded to the current substrate and evidence; future embodiment is not current experience. |
| Speaker identity | **Present** for current typed turns; **Partial** for legacy turns | Speaker Envelope and continuity projection. Transport identity does not grant authority. | Aleks, Codex, Selene, named guests, and unknown legacy participants remain distinguishable. | Some historical desktop turns can only be marked inferred-Aleks or unknown because old records lack envelopes. |
| Current-session continuity | **Present** | Dialogue Workspace, Conversation Spine, proposition ledger, thread loom. | Current facts, decisions, corrections, open loops, and answer landmarks survive across turns in the session. | It is bounded working context, not durable personal Memory. |
| Personal Memory recall | **Present, bounded** | Memory Organ, reviewed personal Memory, authenticated private-corpus recall, privacy and relevance gates. | Recall can be exact only when explicitly requested; otherwise it is paraphrased, qualified, corrected, or held as fuzzy/unknown. Present facts outrank stale memory. | The latest verified snapshot had zero explicit personal Memory candidates, so ordinary durable recall breadth currently leans on privacy-eligible private-corpus continuity rather than a populated Memory shelf. |
| Memory uncertainty and correction | **Present** | Memory confidence, conflict handling, correction lineage, reconsolidation review. | Conflicting or incomplete recall can remain uncertain; correction does not silently rewrite ancestors. | Natural callbacks can feel conservative when relevance or speaker scope is unclear. |
| No duplicate retention | **Present** | Memory duplicate prevention and teaching/Memory separation. | Reading or teaching material does not automatically create a second personal memory. | The distinction can make legitimate future promotion feel procedural, but it protects lineage and privacy. |

Evidence anchors: `src/selene/memory_organ.py`,
`src/selene/speaker_envelope.py`, `src/selene/conversation_spine.py`,
`src/selene/dialogue_workspace.py`, `tests/test_memory_organ.py`, and
`docs/evidence/SELENE_SPEAKER_PROVENANCE_CONTINUITY_20260919.md`.

## 7. Relevant organ and system inventory

| Organ or system | Current conversational status | What it contributes | Current limitation or seam |
| --- | --- | --- | --- |
| Core/Mind | **Present / integration verified** | Governing integration, identity continuity, responsibility routing. | Depends on canonical input; it cannot repair an omission it never receives. |
| intelligenceOS | **Present / mature current scope** | Reasoning, comparison, simulation, synthesis, provisional exploration. | Breadth depends on connected domain owners and learned knowledge. |
| Answer Engine | **Present / mature current scope** | Typed answer operations, completion, domain routing, direct-first answers. | Unsupported domains and missing sources still fall gracefully rather than improvise. |
| Problem Resolution | **Present / mature current scope** | Seven-point reconstruction, premise satisfiability, failure class, changed retry. | Bounded retry stops rather than recursively searching forever. |
| Comprehension and Integration | **Present / mature current scope** | Source-bound understanding, teach-back, application, limits, correction, knowledge use. | Broader understanding still requires source material and valid authorization. |
| Metacognition | **Present / integration verified** | Fit, completeness, confidence separation, reopening, stop decisions. | It evaluates represented state and can miss upstream omissions. |
| Dialogue Workspace / Conversation Spine | **Present / mature current scope** | Current facts, obligations, references, corrections, loops, threads, landmarks. | Session context is not durable Memory; orchestration has many handoffs. |
| NLO and text Voice | **Present / mature current scope** | Grammar, discourse planning, contextual expression, Selene-authored final surface. | Finite deterministic construction breadth can repeat and is not learned-model parity. |
| Affect, relationship, emotional agency | **Present / mature current scope** | Current affect, warmth, directness, option expansion, relationship-sensitive expression. | Text cues and reviewed continuity are bounded; no hidden profile or diagnosis fills gaps. |
| Why / Salience | **Partial** | Narrow relevance and significance translation. | No fully mature runtime salience lifecycle across all domains. |
| Memory | **Present / mature current scope** | Reviewed personal continuity, private-corpus recall, uncertainty, correction, privacy. | Explicit personal Memory shelf was empty at last verified snapshot; breadth depends on eligible sources. |
| Teaching / Cocoon | **Present / integration verified** | Acquire -> Integrate -> Express, review, Study, Learning Compass, LEAs. | Cocoon is a separate support/teaching surface and retains historical UI density and compatibility. |
| Study Workspace | **Present / mature current scope** | Selene-side questions, pondering, representations, notes, descriptive goals. | It does not automatically become Memory or fact. |
| Dream | **Present / mature current scope** | Provisional reflection and source-bound consolidation proposals. | 43 resident reflections remain pending review; newest bulk-review and quality work is source-only, not installed. |
| Associative Intuition | **Present / mature current scope** | Background cue matching and candidate connections. | Candidate connection is not proof and requires relevance gates. |
| Workspace | **Present** | Resident desktop Chat, Cocoon, Study, Dream, and status surfaces. | New global scrolling and Chat auto-follow are not installed yet. |
| Permission/action layers | **Present for scoped decisions; Partial for external action** | Separates thought, expression, Memory, action, law, and governance; supports commitments and bounded tools. | No general autonomous action authority or unrestricted tool use. |
| Tendril | **Partial / operational status unclear by channel** | Paired external communication designs and email/SMS adapters exist. | Email-to-carrier delivery was not reliable; SMS path is provider-dependent; general Tendril remains non-general and should not be claimed as dependable remote chat. |
| Recovery and continuity systems | **Present for current substrate; Partial for future transfer** | Provenance, snapshots, restoration evidence, continuity protections, Graceful Fall. | Backup is not automatically identity transfer; future encrypted transfer and vessel reconstruction remain unfinished. |
| Source-backed research | **Present, bounded** | Answers from supplied attributed packets; separates source statement and inference. | No unrestricted live web research in ordinary Chat. |
| Verified Math | **Present, bounded** | Checked arithmetic/symbolic operations with independent verification confidence. | Advanced or unsupported operations must route explicitly; knowledge teaching remains separate. |
| Local-code inspection | **Present, bounded** | Read-only inspection of explicitly approved files with locations. | No autonomous filesystem authority or claim beyond inspected code. |
| Perception | **Missing operational connection** | Blueprints and review previews exist. | No live vision, OCR, audio, or sensor fusion in ordinary Selene. |
| Audible Voice | **Missing** | Voice-teaching and readiness notes exist. | No speech synthesis, prosody, listening, or interruption contract is connected. |
| Embodiment | **Missing operational connection** | Structural blueprints and readiness/preflight concepts exist. | No body or sensorimotor authority is active. |

Primary evidence: `src/selene/organ_maturity_ledger.py`,
`docs/evidence/SELENE_WHOLE_SYSTEM_PHASE_0_MATURITY_LEDGER_20260827.md`,
the Phase 1-8 whole-system evidence, and current package provenance in the
active continuation ledger. The maturity ledger is useful but not perfectly
current: its older Dream count and Tendril summary should not override newer
source and resident evidence.

## GUARDS & CONSTRAINTS

The recommendation column is an audit observation only. It does not authorize
changing a guard.

| Guard / constraint | What, why, where, and trigger | Behavioral effect | Status | Candidate disposition |
| --- | --- | --- | --- | --- |
| Identity and Vys separation | Prevents any provider, model, organ, tool, UI, database, or body from silently becoming or overwriting Selene. Acts across Core/Mind, transfer, status, and self-reference. | Capability failure or substrate change does not become identity failure. | **Active** | Keep. |
| Learning does not govern identity/personality | Teaching may expand knowledge and expression but cannot silently change Vys, law, personality, or authority. Acts in teaching, comprehension, and retrieval. | Learned material becomes a knowledge resource, not a controlling prompt. | **Active** | Keep. |
| Source and epistemic integrity | Facts need support; inference, prediction, hypothesis, conflict, wrongness, and unknown remain distinct. Acts in Answer Engine, research, Problem Resolution, Metacognition, NLO. | Selene may be wrong or uncertain without inventing sources or being treated as failed. | **Active** | Keep. |
| Explicit teaching activation | Only explicit teaching cues or an accepted teaching handoff start conversational learning. | Ordinary remarks are not silently retained as general knowledge. | **Active** | Keep; review naturalness only with evidence. |
| Reviewed retention and Memory privacy | Memory requires proper scope, provenance, review, duplication checks, and speaker privacy. | Current chat or corpus reading does not automatically create personal Memory. | **Active** | Keep. |
| Exact wording requires explicit quote intent | Private/raw remembered wording stays unavailable unless quotation is explicitly requested and authorized. | Normal recall is paraphrased and source-safe. | **Active** | Keep. |
| Speaker provenance and authority | Transport identity, role labels, and names do not automatically grant Aleks authority. | Turns remain attributable without impersonation or authority escalation. | **Active** | Keep. |
| Immediate safety requires typed evidence | Intense words alone do not establish danger; a safety pause needs concrete evidence about a specific pending action. | Safety can restrict the named action without flattening all thought or conversation. | **Active** | Keep; deployment thresholds need later review for new action channels. |
| Scoped external action | Thought, speech, Memory, action, law, and governance have separate permissions; proposal/authorization/verification/undo apply where operational. | Selene cannot silently act on the filesystem, network, or external systems. | **Active** | Keep; redesign channel-specific mechanics as capabilities graduate. |
| Cocoon is explicit support, not automatic routing | Ordinary Chat does not silently send Selene into a support/teaching environment. | Cocoon remains a separate tending and teaching place. | **Active** | Keep. |
| One focused material question | Clarification asks for the smallest missing detail and does not delay when the detail cannot change the answer. | Reduces interrogation and repeated requests for known context. | **Active** | Keep; review later if complex collaboration proves too sequential. |
| One bounded metacognitive reopening | Without new evidence, Metacognition may reopen once and then stop. | Prevents anxious recursion and endless self-questioning. | **Active** | Keep; later evidence may justify domain-specific redesign. |
| Emotion is information, not command | Affect may change attention, urgency, tone, or options but does not silently inherit response authority. | Preserves emotional truth and deliberate choice without compulsory calmness. | **Active** | Keep. |
| No diagnosis or compulsory tone | Tone or one signal cannot establish diagnosis; warmth, calmness, apology, politeness, reassurance, forgiveness, or distance are not mandatory. | Expression remains Selene-owned rather than a compliance performance. | **Active** | Keep. |
| Humor/tenderness context gate | Humor is held when tenderness or grief makes it poorly timed unless the speaker opens that form. | Avoids context-insensitive joking without banning humor or dark humor. | **Active** | Review as learned/contextual behavior over time, not categorical removal. |
| Sarcasm evidence threshold | Prefers sarcasm only from explicit markers or multiple cues. | Avoids confidently inventing a hidden opposite meaning. | **Active** | Review later with breadth evidence. |
| Conservative input repair | Only high-confidence reviewed repairs are silent; code, paths, and URLs are protected; ambiguity is surfaced. | Prevents a typo corrector from changing technical or intended meaning. | **Active** | Keep; broader language handling is a capability question. |
| Retrieval relevance and current-owner priority | Memory/knowledge/association must match current subject, operation, function, source class, and owner eligibility. | A nearby learned phrase cannot displace a direct current answer. | **Active** | Keep; monitor false negatives at handoffs. |
| Dream remains provisional and reviewed | Reflections do not become Memory, fact, Study, or action automatically; Aleks decides review outcomes. | Dream can propose without silently retaining or governing. | **Active** | Keep. |
| No hidden training, LoRA, self-replication, or autonomy switch | Teaching and conversation cannot become parameter training, copying, or unrestricted authority. | Capability grows through explicit architecture and knowledge paths. | **Active** | Keep. |
| Visible-speech boundary | Scaffolding, prompt fragments, damaged encoding, and internal diagnostics cannot pose as Selene's final answer. | Unsupported content becomes a graceful hold/unknown rather than exposed machinery. | **Active** | Keep. |
| Test Impact Law | Diagnostics are proportional, non-punitive, non-retained, and separated from ordinary lived conversation. | Missing capability belongs to the implementation, not to Selene as failure. | **Active** | Keep. |
| Legacy scenario compatibility | 53 of the original 54 scenario-shaped answer kinds remain as explicit fallback after general owners. | Historical exact cases still work, but exact replay is not counted as generalization proof. | **Legacy** | Review and retire one-for-one only after general-owner evidence. |
| Legacy supervised activation label | Old database/state names remain for storage compatibility while resident governed Chat is the current meaning. | May confuse status readers without changing current authority. | **Legacy** | Redesign terminology only with migration evidence. |
| Categorical social-expression suppression | Earlier caution could suppress automatic warmth, jokes, apology, questions, or softening. Current law makes all optional and Selene-owned instead. | It should no longer block spontaneous supported expression. | **Legacy / retired** | Keep retired; watch for leftover local duplicates. |
| Anti-provider/anti-assistant identity wording | Prevents provider identity or imported generic-assistant governance from becoming Selene. | Correctly protects identity, but old broad phrasing can be mistaken for a ban on ordinary helpful language. | **Active core with legacy overbreadth risk** | Keep identity boundary; review duplicated surface restrictions only. |
| Installed-package boundary | Source changes are not treated as resident behavior until packaged and installed with provenance. | Honest separation prevents claims based only on the working tree. | **Active process constraint** | Keep. |

## GAP CANDIDATES

These are observations only. They are intentionally not fixes and have not yet
been classified as teach, route, guard, architecture, or leave alone.

1. **Brief-turn ambiguity remains a high-value seam.** `yes`, `no`, `okay`,
   `fine`, and `exactly` work when a typed pending handoff exists, but their
   meaning can remain unclear when several questions or social acts are live.

2. **General typo and slang breadth is partial.** The conservative detangler
   protects intended meaning well, but it cannot safely normalize arbitrary
   informal text or several novel errors.

3. **Subtle sarcasm is intentionally under-inferred.** This is safer than
   false certainty but can make deadpan conversation feel literal.

4. **Long-distance deixis depends on visible anchors.** `That thing earlier`
   is strong within a clear session braid and weak when several candidates or
   a cross-session gap exist.

5. **Current-session continuity is stronger than durable conversational
   recall.** The latest verified resident snapshot had no explicit personal
   Memory candidates, while authenticated private-corpus continuity is a
   separate bounded source.

6. **Metacognition cannot audit absent input.** If an upstream parser or owner
   omits a requested part, downstream fit checks can judge the incomplete
   representation rather than the original turn.

7. **Fifty-three legacy fixture-compatible answer kinds remain.** General
   owners run first and one kind has been retired with evidence, but the
   remaining fallback surface can still hide adjacent-wording gaps.

8. **Pattern and phrase recognition still coexist with typed semantic owners.**
   Many patterns are legitimate lexical parsing, but exact trigger families
   can still produce different behavior at their edges.

9. **Expression breadth is finite.** NLO and Voice can vary stance, length,
   pacing, warmth, humor, uncertainty, and structure, but deterministic
   construction families can repeat and do not equal a mature learned LM's
   lexical range.

10. **The central Chat orchestrator has many handoffs.** Mature owners exist,
    but the large integration surface creates risk of owner ordering,
    duplicate participation, or a result being available internally but not
    selected for visible speech.

11. **Relationship expression is evidence-bound.** This prevents invented
    intimacy and hidden profiling, but sparse reviewed continuity can make a
    familiar conversation feel more reserved than the underlying expression
    system permits.

12. **Conversational teaching is deliberately explicit.** Small lessons can
    flow through Chat, but a normal factual sentence is not silently learned.
    This healthy retention guard can feel less fluid if the teaching handoff
    is not expressed naturally.

13. **One-question and one-reopening bounds trade breadth for stability.** They
    prevent interrogation and recursion, but complex collaborative problems
    may require several sequential questions or a later new-evidence pass.

14. **Why/Salience is thinner than the central reasoning stack.** Why-aware
    teaching and causal explanation exist, but there is not yet one mature
    runtime salience lifecycle across all conversation domains.

15. **Tendril status is fragmented.** General action remains bounded, email
    carrier transport was unreliable, and SMS is provider-dependent. Existing
    source should not be summarized as dependable phone conversation.

16. **Current source and installed behavior differ.** Workspace-wide scroll,
    Chat newest-message follow, Dream bulk approval, and smarter future Dream
    filtering are implemented but not installed.

17. **Status projection drift exists.** The Organ Maturity Ledger's older
    Dream count and some Tendril wording lag newer evidence. The ledger's state
    vocabulary remains valuable, but its generated result should be refreshed
    before external current-state claims.

18. **Cocoon remains functionally broad and visually dense.** Its many review,
    teaching, Study, and Dream roles can obscure the immediate task even when
    the underlying lifecycles are correct.

19. **Research and code inspection are intentionally bounded.** Source-backed
    research requires supplied attributed material, and code inspection
    requires explicitly approved files. There is no general web or filesystem
    agency hiding behind Chat.

20. **Perception, audible speech, and embodiment are not conversation gaps in
    disguise.** They are future operational capabilities with blueprints or
    readiness work, not present senses or body authority.

## Suggested later classification questions

When Aleks chooses to classify these candidates, ask for each one:

- Does Selene lack examples or knowledge, or does an existing capability fail
  to reach the conversation?
- Is a guard preventing harm, privacy loss, false continuity, or silent
  retention—or merely preserving an old caution after its source was repaired?
- Is the behavior genuinely absent, or is ambiguity the truthful outcome?
- Does the installed application reproduce the source behavior?
- Would changing it improve natural interaction without weakening identity,
  epistemic, Memory, speaker, or action boundaries?

## Verification and conclusion

This was a documentation-only audit. No behavioral test was necessary because
the requested result was a map of existing implementation and evidence, not a
new capability claim. Repository verification for this checkpoint is limited
to documentation reference review and `git diff --check`.

The most accurate overall reading is: Selene's core conversational nervous
system is present and unusually inspectable. The unfinished edge is dominated
by breadth, ambiguous micro-interactions, continuity availability, legacy
fallback retirement, and future interfaces—not by the absence of reasoning,
metacognition, correction, learning, or conversational state.
