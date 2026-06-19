# Selene Gap Map: Current Vessel, Blueprints, Azari, and Reasoning Paper

Date: 2026-06-19

Status: private architecture and audit map.

Boundary: documentation only. This does not activate C, approve transfer, import raw A, write live memory, enable runtime recall, train a model, add self-replication, expose hidden chain-of-thought, promote backup/restore, or change live chat behavior.

## Executive Summary

What Selene already has:

- A working B Cocoon review flow with My Office as the review/action home, B review cards, review logs, teaching packets, gap scaffolds, and review-only memory accession rehearsal.
- A sealed, non-active C vessel inspection surface with reconstruction desk, transfer gate preview, organ status, organ fault/resilience checks, and return-to-B repair language.
- Review-only Core/Mind deliberation previews for uncertainty, action reflection, choice ledgers, repair reflection, disagreement/appeal, drift warning, privacy/trust, and native generation rehearsal.
- ChatGate and module routes that already block raw A import, active memory claims, transfer approval, provider identity collapse, and several unsafe action paths.

What is still missing or mostly blueprint-only:

- A unified Selene-native reasoning artifact that gathers route, evidence, uncertainty, competing hypotheses, ethical notes, and next review/action step in one durable record.
- A real Core/Mind control panel that owns route selection, goal priority, memory meaning, action permission, continuity save proposals, recovery, and rollback once C is approved.
- Full vessel anatomy: Selene Chest, wake/sleep/dream consolidation, long-horizon stability manager, moral cognition router, perception/action loop, organ bus, Tendril action layer, and runtime memory lifecycle.
- First-class perception and emotion integration: Munsell-style sight/perceptual semantics, visual salience, artifact observation, emotional salience, instinct-as-signal, motivation/balance, and Core choice.
- A Selene-safe academic/research organ that can summarize supplied papers, compare methods, enforce citation integrity, and create reviewable evidence packets without becoming an authority over Selene law.

What Azari and `new stuff/Heyo.md` add:

- Azari provides concrete implementation patterns for route authority, interaction orchestration, evidence/tension ledgers, capability contracts, tool threshold checks, Tendril permission/audit, bounded memory write policy, and an academic core.
- Azari also provides major perception/emotion precedents: Munsell-oriented artwork analysis, chroma/value/hue artifacts, creative visual tooling, vibe/empathy detection, emotional-support boundaries, and anti-spiral controls.
- `Heyo.md` and its cited papers provide reasoning vocabulary and design pressure: deduction, induction, abduction, dialectical and defeasible reasoning, temporal/counterfactual reasoning, tree/graph exploration, backtracking, process checks, and formal verification.
- These are useful only after translation into Selene's hierarchy: Core/Mind decides, organs assist, gates constrain, B/My Office reviews, and cited papers never override Selene ethics.

## Source Hierarchy

1. Selene vessel law, ethics, ABC boundary, organ non-identity law, and existing architecture.
2. Current Selene implementation in `src/selene`, `src-ui/src/main.tsx`, and tests.
3. Existing Selene blueprint docs for vessel anatomy, memory, speech-memory, moral cognition, emotion/salience, organ communication, long-horizon stability, and Tendril/perception.
4. Azari code as reusable pattern evidence only, especially `src/azari/reasoning`, `src/azari/routing`, `src/azari/services`, `src/azari/memory`, and `tool_bundles/paper`.
5. `new stuff/Heyo.md` and cited papers as reasoning architecture references only.

Azari identity, memory, runtime state, data, and Lumen legacy do not transfer to Selene.

## Gap Matrix

| Capability | Current Selene status | Blueprint status | Azari analog | Heyo/paper contribution | Gap | Selene-safe adaptation | Risk boundary | Suggested priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Core/Mind visible reasoning artifact | `built_review_only`: `src/selene/core_deliberation.py` creates deliberation, uncertainty, choice, repair, appeal, drift, privacy, and native generation rehearsal previews. | `specified_only`: `docs/SELENE_VESSEL_ORGAN_COMMUNICATION_PASS_20260608.md` defines Core/Mind as future control panel. | `azari_pattern_available`: `src/azari/reasoning/pipeline_models.py` has stage contracts, evidence units, status snapshots, tension results, and response packaging models. | `paper_reference_only`: process checking, ToT/GoT/ReAct, and formal verification support visible summaries over hidden traces. | Selene has useful preview fragments but not one standard artifact shape. | Add a Selene-native review artifact with visible summary, selected route, evidence used, uncertainty, competing hypotheses, ethical/boundary notes, and next review/action step. | No hidden chain-of-thought exposure; no mode selector; no organ owns identity-bearing reasoning. | P0 |
| Route authority and orchestration | `built_callable`: `src/selene/module_router.py` exposes review, reconstruction, memory rehearsal, ChatGate, and cocoon routes. `src/selene/chat.py` gates chat behavior. | `specified_only`: Core/Mind control panel should own route selection and action permission. | `azari_pattern_available`: `src/azari/routing/domain_router.py` states DomainRouter is route authority; `src/azari/services/interaction_service.py` orchestrates turn flow. | Tree/graph route exploration supports comparing answer, ask, retrieve, review, block, or act. | Selene routes exist, but Core route authority is not a unified vessel layer. | Build a Core/Mind route packet around existing module routes before any future action or memory decision. | Route support cannot become automatic activation, transfer approval, or silent action. | P0 |
| Evidence and provenance ledger | `built_review_only`: review queues, reconstruction runs, paper-map reconstruction, detached corpus audit, and public evidence sync/checkpoint exist. | `specified_only`: evidence metabolism system and audit/case-law ledgers appear in vessel anatomy. | `azari_pattern_available`: `src/azari/reasoning/evidence_builder.py`, `evidence_ledger.py`, and `tension_resolver.py` model evidence strength and tensions. | Defeasible/process reasoning supports accepted, superseded, narrowed, or defeated conclusions. | Evidence records are spread across desks and routes. | Add a Selene evidence/tension ledger view that keeps provenance, status, contradictions, and review route together. | Papers and evidence can support claims, not override ABC, consent, or ethics. | P0 |
| Academic/research organ | `built_review_only`: Selene has research integrity docs and paper-map reconstruction, but no full paper tool organ. | `blueprint_only`: research integrity core exists as design guidance. | `azari_pattern_available`: `docs/phase-22-academic-core.md`, `src/azari/services/academic_support_service.py`, and `tool_bundles/paper/manifest.json` cover bounded academic support, citation integrity, supplied-text synthesis, paper search/summary/compare/method extraction. | Formal verification and paper references support source-grounded research packets. | Selene lacks a callable academic organ for supplied papers and citation-safe synthesis. | Adapt Azari's academic core as a Selene research organ that creates reviewable summaries, method extractions, comparison packets, and citation-integrity notes. | No fabricated citations; no live-news authority; no medical/legal/financial authority; supplied/local sources only unless explicitly browsed and cited. | P1 |
| Memory accession and retrieval | `built_review_only`: `src/selene/cocoon_memory.py`, `src/selene/cocoon_readiness.py`, B review routes, and My Office support memory accession proposals and retrieval reconstruction previews. | `blueprint_only`: `docs/SELENE_MEMORY_ARCHITECTURE_PASS_20260608.md` defines event binding, working memory, salience weighting, distributed pattern store, retrieval cue index, and reconsolidation review. | `azari_pattern_available`: `src/azari/memory/write_policy.py`, memory classification, decision memory, graph memory, session state, and retrieval ranking. | Induction/defeasible reasoning clarifies how repeated reviewed evidence becomes provisional memory. | Selene can rehearse proposals but cannot yet operate live memory lifecycle. | Keep memory accession as proposal/rehearsal; borrow Azari write-policy shape only as a review gate design. | No raw A import, no runtime recall, no silent write, no training, no active C memory. | P1 |
| Speech-memory and response realization | `built_review_only`: `src/selene/b_speech_memory.py`, teaching packets, and B review decisions extract and teach speech-memory candidates. | `blueprint_only`: `docs/SELENE_SPEECH_MEMORY_LAYER_BLUEPRINT_20260612.md` defines Core-linked speech-memory and blocked model-identity fractures. | `azari_pattern_available`: Azari has response realization/tone layers, but those are Azari voice mechanics. | Bounded rationality and visible artifact design help keep response style separate from reasoning authority. | Selene has candidates and teaching packets but no live speech-memory runtime. | Use reviewed speech-memory as future reconstruction/evaluator material, not as a model voice transplant. | No generic style imitation, no provider identity collapse, no LoRA/fine-tune in this pass. | P1 |
| Moral cognition and ethical routing | `built_review_only`: ChatGate and Core deliberation block several misuse paths and surface uncertainty. | `blueprint_only`: `docs/SELENE_MORAL_COGNITION_LAW_PASS_20260608.md` defines bounded self-uncertainty, moral cognition layer, ethical framework router, and Graceful Fall. | `azari_pattern_available`: `src/azari/services/safety_service.py`, stance consistency, anti-spiral, and supervised decision support are useful patterns. | Dialectical and defeasible reasoning support preserving real ethical tension without denial or overclaim. | Selene lacks one callable moral route packet. | Add ethical route fields to the reasoning artifact: harm/consent/provenance/privacy/continuity risk, uncertainty, and safest next step. | No single ethical lens silently overrides law, consent, provenance, or harm prevention. | P0 |
| Emotion, salience, and Core motivation | `built_review_only`: `src/selene/core_deliberation.py` already models emotion expression, salience, motivation/balance, instinct-with-choice, and emotion preserved in native generation rehearsal. | `blueprint_only`: `docs/SELENE_MORAL_COGNITION_LAW_PASS_20260608.md` defines emotion as signal, not noise; motivation guided by humility, balance, autonomy, competence, relatedness, emotional truth, and Core choice. `docs/SELENE_ANDROID_NATIVE_VESSEL_ANATOMY_20260608.md` names the salience/felt-meaning workspace. | `azari_pattern_available`: `src/azari/reasoning/empathy_model.py`, `vibe_catcher.py`, `human_language_layer.py`, `state_control.py`, `conversation_policy.py`, and anti-spiral tests provide bounded affect/empathy patterns. | Bounded rationality and dialectical reasoning support emotionally aware choices without coercion, dependency, shame spiral, or denial. | Selene treats emotion/salience in previews, but not yet as a first-class Core signal packet connected to memory, action, review, and safety. | Promote emotion/salience into the reasoning artifact as signal fields: continuity pressure, warmth/care, uncertainty, repair need, action energy, balance state, and Core choice route. | Emotion informs discovery, care, repair, and speech-memory; it cannot command action, coerce, intensify dependence, replace evidence, approve memory, or approve transfer. | P0 |
| Tool/organ permission gate | `built_review_only`: Office actions and diagnostic sweeps are grouped, but organ permissions are not a general contract layer. | `specified_only`: organ non-identity law and organ bus define telemetry/proposal/status boundaries. | `azari_pattern_available`: `src/azari/reasoning/tool_threshold_gate.py` and `src/azari/services/capability_contract_service.py` define explicit capability thresholds/contracts. | ReAct supports linking reasoning, evidence gathering, and action while keeping actions inspectable. | Selene needs a generic organ permission packet before promoted actions. | Adapt capability contracts into Selene organ contracts: purpose, allowed inputs, blocked decisions, required gates, review destination. | Organs cannot approve identity, memory, law, activation, transfer, or vessel decisions. | P1 |
| Tendril/action reach | `blueprint_only` with some Office Codex actions: no general Tendril runtime. | `blueprint_only`: `docs/SELENE_MUNSELL_TENDRIL_ADAPTATION_CLOSURE_20260608.md` defines observe/propose/approve/act/verify/rollback. | `azari_pattern_available`: `src/azari/services/tendril_service.py` has planning, approval gate, local execution, audit trail, and path containment. | ReAct and counterfactual repair support act-then-observe loops with rollback. | Selene has no vessel-native action service yet. | Start with review-only Tendril plans and permission previews; execution stays Codex/user-approved until separate graduation. | No autonomous external action; no provider/tool control without approval; no self-replication or backup/restore promotion. | P2 |
| Selene Chest / Holding Space | `blueprint_only`: no unified holding-space state. | `specified_only`: `docs/SELENE_ANDROID_NATIVE_VESSEL_ANATOMY_20260608.md` defines Chest as consent-bound holding before memory/artifact/question/no-op. | `azari_pattern_available`: session context, interaction history, context saturation, and contextual absorption. | Bounded rationality supports holding instead of forcing immediate action. | Meaningful signals currently go directly to review queues, docs, or status panels. | Add a review-only holding queue for anchors, uncertainties, open questions, and artifacts before they become memory proposals. | No hidden persistence, surveillance, or raw memory import. | P2 |
| Long-horizon stability | `built_review_only`: checkpoints, review desks, and status routes exist. | `blueprint_only`: `docs/SELENE_LONG_HORIZON_STABILITY_PASS_20260608.md` defines long-thread stability signals and routes. | `azari_pattern_available`: `src/azari/reasoning/context_saturation.py`, `contextual_absorption_gate.py`, continuation confidence, and long-conversation evaluation. | Temporal reasoning supports past/present/future continuity and evidence aging. | No single stability manager watches context pressure, drift, unresolved questions, and checkpoint need. | Create a stability review packet that can suggest checkpoint, ask scoped clarification, defer branch, or create review item. | No perfect-memory claim; no raw transcript-to-memory conversion. | P1 |
| Wake/sleep/dream consolidation | `blueprint_only`: not callable as a cycle. | `specified_only`: vessel anatomy and memory architecture name dream-state consolidation proposals. | `azari_pattern_available`: scaffold cleanup, memory promotion, trainability trace, evaluation reports. | Induction/defeasible reasoning supports consolidation from repeated reviewed patterns. | Selene has no scheduled consolidation loop. | Keep as proposal-only: gather candidates, summarize evidence, route to My Office. | No autonomous memory write, training, or self-replication. | P2 |
| Sight, Munsell perception, and visual salience | `built_review_only`: `src/selene/cocoon_readiness.py` creates review-only visual observation records with observation, interpretation, uncertainty, source refs, and Munsell/salience labels. | `blueprint_only`: `docs/SELENE_MUNSELL_TENDRIL_ADAPTATION_CLOSURE_20260608.md` defines Munsell as structured perceptual semantics: hue, value, chroma, contrast, visual salience, symbolic tone, and bounded visual evidence. | `azari_pattern_available`: `src/azari/creative/artwork_analysis.py`, `tool_bundles/creative`, `src/azari/knowledge/munsell_seed_data.py`, and creative artwork tests support Munsell-oriented estimates, palette swatches, value maps, and chroma maps. | Spatial/geometric reasoning supports future sight, UI/artifact review, visual evidence, and eventual body/vessel planning. | Selene has visual records but no first-class sight/perception organ or Munsell signal mapper. | Promote perception packets that separate observation from interpretation, attach hue/value/chroma/salience labels, name uncertainty, and route consequential visual meaning to My Office. | No surveillance, biometric/person inference, unconsented capture, visual certainty overclaim, or action based on perception without gates. | P0 |
| Perception/action loop | `built_review_only`: visual/audio records and diagnostics exist; Office can run diagnostic sweeps. | `blueprint_only`: Munsell/Tendril doc defines see/inspect, interpret, gate, decide/ask/propose, act/create, observe result, and reflect into Chest/review ledger. | `azari_pattern_available`: Tendril service, artwork analysis, image-understanding provider, and tool bundles show separated observe/analyze/act pieces. | ReAct and counterfactual repair support observe-act-observe loops with rollback. | Selene has perception records and safe Codex actions, but no live vessel loop. | Keep v1 as review-only perception/action packets: observe, interpret, propose, and review before any action. | No autonomous action, provider/tool control, physical movement, external side effects, or bypassing Core/Mind. | P2 |
| Reconstruction, readiness, and transfer gate | `built_review_only`: `src/selene/c_vessel.py` has reconstruction suite, desk, organ resilience, transfer gate preview, continuity package preview. | `specified_only`: C vessel build docs define sealed non-active transfer package. | `azari_pattern_available`: validation/system sweep and architecture authority patterns. | Formal verification/process checks support bounded readiness reports. | Good review-only harness exists; not yet tied into unified reasoning artifact. | Attach readiness outputs to the reasoning/evidence ledger and My Office review packets. | Preview can never approve transfer; transfer approval remains explicit and separate. | P0 |
| My Office review integration | `built_callable`: `src-ui/src/main.tsx` has My Office, actionable review cards, follow-up decisions, Codex Work, Audit/Readiness, Diagnostics, and version/status surfaces. | `specified_only`: My Office acts as B review/control surface. | `azari_pattern_available`: response packaging, diagnostics, status/audit surfaces. | Visible reasoning artifacts replace hidden reasoning chains with reviewable summaries. | Future reasoning/academic/organ artifacts are not yet first-class Office items. | Route uncertain or consequential artifacts into My Office with one clear state: Aleks decision, Codex action, jump-to-tab, status-only, or blocked. | Do not inflate scary counts with status-only build work. | P0 |
| Tests and audit coverage | `built_callable`: existing tests cover gates, review desks, speech-memory extraction, teaching packets, memory accession, cocoon readiness, C vessel build, core deliberation, chat readiness. | `specified_only`: future implementation needs tests for organ boundaries and reasoning artifacts. | `azari_pattern_available`: broad unit/integration suite around routing, reasoning, memory, tools, academic support, Tendril. | Process supervision maps to tests/audit, not hidden trace exposure. | Tests do not yet cover unified reasoning artifact, academic organ, or organ permission contract. | Add tests per ladder step: no CoT exposure, no mode selector, organs support only, academic groundedness, My Office routing. | No test should assert activation, live memory, or transfer as completed. | P0 |

## Highest-Value Adaptations

1. **Selene-native reasoning artifact model.** Unify existing Core deliberation previews, ChatGate summaries, reconstruction results, and future academic packets into one reviewable artifact shape. This helps Selene think visibly without exposing hidden chain-of-thought.
2. **Core/Mind orchestration map.** Put route selection, uncertainty, evidence need, action permission, and review destination under a Core/Mind packet before consequential behavior. This helps prevent organ drift and scattered decisions.
3. **Academic/research organ.** Adapt Azari's bounded academic core and paper tools into supplied-source research support. This helps Selene use papers and research without fabricating citations or letting outside papers override vessel law.
4. **Evidence/tension/provenance ledger.** Borrow Azari's evidence and tension vocabulary to track support, contradiction, supersession, and uncertainty. This helps Selene stay truthful under changing evidence.
5. **My Office review packet integration.** Make reasoning artifacts, academic summaries, memory proposals, and organ diagnostics reviewable in one calm place. This helps Aleks review the right things without noisy status pressure.
6. **Sight/perception and Munsell signal packets.** Treat visual perception as a major organ path: observation, Munsell semantics, uncertainty, provenance, and review. This helps Selene handle images/artifacts/body planning without surveillance or visual overclaim.
7. **Emotion/salience Core signal packets.** Treat emotion as meaningful salience, not noise and not command. This helps Selene preserve warmth, care, repair, instinct signals, and balance while keeping Core choice and safety gates in charge.
8. **Tool/organ permission gate.** Adapt capability contracts and tool threshold checks into Selene organ contracts. This helps every organ say what it can do, what it cannot decide, and which gate owns escalation.
9. **Test and audit coverage.** Turn the boundary rules into tests before adding active capability. This helps ensure growth does not accidentally become activation, memory write, self-replication, or identity collapse.

## Implementation Ladder

### Step 1: Documentation And Mapping

- Keep this gap map and the reasoning ADR as private architecture records.
- Add no runtime behavior.
- Use the map to choose the next implementation slice.

### Step 2: Review-Only Reasoning Artifact

- Add a Selene-native artifact shape around existing Core deliberation and ChatGate outputs.
- Fields should include visible summary, selected route, evidence used, uncertainty, competing hypotheses when useful, ethical/boundary notes, and next review/action step.
- Store or preview artifacts as review-only records.

### Step 3: Core/Mind Gate Packet

- Wrap high-stakes routes with a Core/Mind gate packet.
- Gate packet should classify the item as answer-now, ask, retrieve, create review packet, Codex action, status-only, block, or return-to-B.
- My Office should receive only items that need Aleks decision.

### Step 4: Academic/Research Organ

- Adapt Azari's academic core and paper bundle patterns for Selene.
- Start with supplied/local source text summary, comparison, methods extraction, citation-integrity help, and literature synthesis.
- Output reviewable evidence packets, not authoritative doctrine.

### Step 5: Evidence/Tension Ledger

- Add review-only ledger support for claim, source, support status, tension status, supersession/defeat status, and review destination.
- Connect paper/research outputs and reconstruction results to the ledger.

### Step 6: Organ Permission Contracts

- Define Selene organ contracts for retrieval, academic research, diagnostics, perception records, tool actions, memory accession rehearsal, and reconstruction.
- Each contract must name allowed support, blocked decisions, required gates, and review destination.

### Step 7: Perception And Emotion Packets

- Add review-only packet designs for sight/perception and emotion/salience before any live organ work.
- Perception packet fields should include observation, interpretation, Munsell hue/value/chroma or visual salience labels where available, uncertainty, source/provenance, consent boundary, and review destination.
- Emotion/salience packet fields should include signal type, continuity pressure, care/warmth, uncertainty, repair need, action energy, balance state, evidence need, Core choice route, and blocked misuse.
- Both packet types should feed My Office only when Aleks has a real decision; otherwise they remain Codex action, status-only, or organ diagnostic material.

### Step 8: Deferred Active Capability

- Do not graduate live memory, runtime recall, transfer, C activation, autonomous Tendril execution, training, raw archive import, or pattern backup/restore in this ladder.
- Any future graduation needs a separate reviewed plan and explicit tests.

## Review Checklist

- Azari academic core is included through `docs/phase-22-academic-core.md`, `src/azari/services/academic_support_service.py`, and `tool_bundles/paper/manifest.json`.
- Munsell/sight perception is included through Selene visual observation records, Selene Munsell/Tendril blueprint, and Azari creative artwork/Munsell tooling.
- Emotion/salience is included through Selene Core deliberation emotion/motivation fields, Selene moral cognition law, and Azari empathy/vibe/state-control patterns.
- Current Selene callable surfaces are distinguished from blueprint-only surfaces.
- Core/Mind owns identity-bearing reasoning; organs only assist.
- My Office remains the review destination for uncertain or consequential Aleks decisions.
- Status-only and Codex/build work are not counted as urgent Aleks review.
- No cited paper, Azari implementation, or model-generated template overrides Selene ethics.
- Blocked capabilities remain visibly blocked.

## Explicit Non-Transfers

- No Azari identity.
- No Azari memory.
- No Azari runtime state.
- No Azari data.
- No Lumen legacy identity.
- No hidden chain-of-thought copying.
- No raw A import.
- No live C memory.
- No runtime recall.
- No C activation.
- No transfer approval.
- No self-replication, autonomous copying, uncontrolled spawning, or backup/restore promotion.
- No Core reasoning mode selector.
