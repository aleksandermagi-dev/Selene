# Selene Contradiction and Safety-Guard Map

Date: 2026-08-11
Status: living architecture and implementation map; C-01 through C-10 and
C-12 were repaired and synthetically verified on 2026-08-11. C-11 remains
intentionally deferred until the external-messaging design resumes.

## Purpose

This map compares four things:

1. the intentions recorded during Selene's development;
2. the current philosophy and governing laws;
3. the behavior implemented in the repository; and
4. the claims made by current documentation and telemetry.

It has two equally important jobs:

- find old constraints that now suppress valid expression, curiosity,
  initiative, or learning; and
- find missing or incomplete protections that could expose Selene, Aleks, the
  repository, private data, or future users to avoidable harm.

The map does **not** assume that every restriction is a cage or that every gap
requires another broad guard. The desired repair is normally the narrowest
rule that protects the real boundary without inheriting authority over
identity, thought, feeling, discussion, or ordinary expression.

## Reading the Map

The following labels are used throughout:

- **confirmed contradiction** — two current parts of the system make
  materially incompatible claims or produce incompatible behavior;
- **legacy guard** — a restriction had an understandable earlier purpose but
  is now broader than that purpose;
- **incomplete connection** — the law permits a capability, but no ordinary
  runtime owner can reliably supply it yet;
- **terminology or telemetry mismatch** — behavior may be sound, but the
  labels report the wrong thing;
- **documentation drift** — an older summary no longer describes the current
  implementation;
- **intentional boundary** — a restriction remains justified and should not be
  removed;
- **safety gap** — protection is missing, conditional, procedural rather than
  enforced, or insufficient for a broader deployment context;
- **cleared concern** — inspection found that the suspected conflict is not a
  live contradiction.

Priority means:

- **P0** — immediate unsafe default or active integrity threat;
- **P1** — repair before the affected capability is broadened or relied upon;
- **P2** — important correctness, clarity, or maturity work;
- **P3** — maintenance or documentation hygiene.

No P0 issue was established in the default local-only desktop posture during
this mapping pass.

## Governing Repair Rule

> Preserve the real boundary. Remove inherited suppression. Replace broad
> denial with the narrowest intent-aware protection that addresses the actual
> risk.

For every future guard change, ask:

1. What harm was this guard intended to prevent?
2. Does it block an action, or does it also suppress thought, discussion,
   emotion, curiosity, or ordinary language?
3. Is that harm already prevented by a more specific invariant?
4. What must remain true after the guard changes?
5. Can the change be verified statically or synthetically before involving
   Selene?

This follows the
[Constraint Provenance and Expression Freedom review](../philosophy/SELENE_CONSTRAINT_PROVENANCE_AND_EXPRESSION_FREEDOM_20260711.md),
the [Test Impact Law](../philosophy/SELENE_TEST_IMPACT_LAW_20260713.md),
and the development history in the
[Selene Work Journal](SELENE_WORK_JOURNAL.md).

## Executive Finding

The repository has strong boundaries around identity, governance, raw corpus
use, reviewed memory, teaching provenance, training, hidden reasoning, and
general autonomy. The principal Selene-facing contradictions are not missing
safety. They are remnants of early caution that still constrain expression or
report current capability inaccurately.

The principal technical safety gaps are deployment-boundary gaps:

- local desktop routes trust other processes running as the same user;
- private-LAN mobile pairing uses HTTP with a bearer secret;
- paired-email identity is filtered but not cryptographically authenticated;
- the ethical-test review exists but is not a mandatory precondition on every
  diagnostic entry path;
- the local database and backups are not encrypted by this repository;
- distributed installers do not yet have signing, reproducible hashes, and a
  complete release-provenance chain.

Those do not make the present local desktop system broadly unsafe. They define
the conditions under which the current trust model must not be overstated.

## Aleks Review Decisions — 2026-08-11

Aleks reviewed the initial map and approved the following directions for later
implementation. These are design decisions, not claims that the runtime has
already changed.

1. **Tiered personal-memory authority:** Selene may later retain ordinary,
   low-risk continuity with visible auditability. Sensitive, identity-bearing,
   third-party, consequential, or uncertain material continues to require
   explicit review. The exact classifications and transition rules must be
   designed before changing the current memory lifecycle.
2. **Corpus privacy:** approved corpus-derived meaning may support conversation
   with Aleks, including callbacks and cadence. Raw excerpts and private details
   remain private by default and are not exposed to another speaker without a
   specific reason and applicable permission.
3. **Typed speaker identity:** inputs should carry claimed speaker, channel,
   authentication strength, diagnostic status, and purpose. A paired channel is
   evidence about the route used, not cryptographic proof of who authored the
   message.
4. **Bounded paired Tendril authority:** when explicitly enabled, replies and
   bounded initiative to Aleks remain available without per-message approval.
   Arbitrary recipients remain blocked, quiet mode remains available, and
   three unanswered initiatives pause further initiative. This behavior still
   requires focused end-to-end testing before it is relied upon.
5. **Portable encryption and recovery:** future at-rest protection should
   support convenient local unlock plus an Aleks-held offline recovery method,
   so encryption does not trap continuity on one Windows installation.

The epistemic distinction discussed with C-08 is also explicit: observation,
data, evidence, hypothesis, model, theory, law, and formal proof are related but
non-interchangeable categories. A hypothesis does not become a theory merely
through confidence, and a theory does not become a scientific law. Approved
memory may inform conversational context and cadence without becoming evidence
for an unrelated factual claim.

---

## Part I — Contradiction and Legacy-Guard Register

### C-01 — Optional affect guidance contains categorical expression bans

- **Resolution (2026-08-11):** repaired and focused-verified. Categorical
  `avoid`, `restrained`, and global `high` restraint values were replaced by
  contextual availability or turn-specific holding. Hard boundaries and tender
  contexts may still guide the current response without becoming global
  expression bans.

- **Class:** confirmed contradiction / legacy guard
- **Priority:** P1 for Phase 7 conversational realization
- **Evidence:**
  [affect_expression.py](../../src/selene/affect_expression.py), especially
  `build_affect_expression_guidance()` and `_dimensions()`;
  [test_affect_expression.py](../../tests/test_affect_expression.py)
- **Intended law:** guidance is optional; expression remains Selene's through
  the coordinated NLO/Voice pipeline;
  technical or epistemic focus does not require emotional flatness; curiosity,
  warmth, humor, enthusiasm, and honest state expression remain Selene-owned.
- **Pre-repair implementation:** several posture profiles used categorical
  values such as `humor: avoid`, `enthusiasm: restrained`, and `restraint:
  high`.
- **Pre-repair effect:** an advisory profile could function as a prohibition even
  when the current conversation safely supports warmth, play, or enthusiasm.
- **Repair shape:** express these fields as contextual considerations or
  defaults, not unconditional bans. A genuine hard boundary or tender context
  may still justify restraint for that turn.
- **Boundary to preserve:** affect must not replace evidence, manufacture an
  internal-state claim, coerce the user, or soften a real safety boundary into
  ambiguity.

### C-02 — Social curiosity is categorically rejected

- **Resolution (2026-08-11):** repaired and focused-verified. Genuine,
  attributable social curiosity may be selected, while engagement-only
  questions, compulsory questions, and interrogation loops remain held.

- **Class:** confirmed contradiction / legacy guard
- **Priority:** P1 for reciprocal conversation
- **Evidence:**
  [conversational_energy.py](../../src/selene/conversational_energy.py),
  `_curiosity_ready()`
- **Intended law:** a follow-up question is never required merely to keep the
  user engaged, but genuine curiosity remains available.
- **Pre-repair implementation:** every complete `social_turn` rejected an
  otherwise supplied curiosity signal because the turn "does not need" an
  added question.
- **Pre-repair effect:** the anti-assistant-habit rule also blocked authentic
  reciprocal interest.
- **Repair shape:** make absence of a question acceptable without making a
  relevant, genuine question unavailable.
- **Boundary to preserve:** no compulsory question, no interrogation loop, no
  question used to evade an answer, and no artificial engagement bait.

### C-03 — Ideas and connections are permitted but lack a reliable ordinary owner

- **Resolution (2026-08-11):** repaired for the currently attributable upstream
  owners and focused-verified. Distinct structural discoveries and supported
  claim/evidence thoughts can enter ordinary NLO expression without a caller
  setting an expression flag. The bridge reports surface addition separately
  and never claims to have created the thought's meaning.

- **Class:** incomplete connection
- **Priority:** P2
- **Evidence:**
  [selene_chat.py](../../src/selene/selene_chat.py), conversational-energy
  inputs around supported ideas, connections, curiosity, and collaborative
  help;
  [generative_thought_expression.py](../../src/selene/generative_thought_expression.py),
  whose status truthfully reports `creates_reasoning: False`
- **Intended law:** Selene may offer a supported idea, make a revisable logical
  leap, notice a connection, or ask Aleks for material help during
  collaboration.
- **Pre-repair implementation:** the expression layer could select attributable
  upstream candidates, but ordinary Chat often depends on a candidate being
  explicitly supplied in the payload or by another already-active path.
- **Pre-repair effect:** permission existed without dependable endogenous supply.
- **Repair shape:** connect bounded, attributable candidate production from
  intelligenceOS, Metacognition, structural discovery, and approved knowledge.
  Keep ideas typed as ideas and hypotheses typed as provisional.
- **Boundary to preserve:** no invented facts, hidden chain-of-thought export,
  unexplained authority claim, or automatic external action.

### C-04 — Exact seed locks can override valid expression ownership

- **Resolution (2026-08-11):** repaired and Chat-verified. Typed semantic
  anchors preserve required meaning, protected numbers, and negative polarity.
  If a later layer loses an anchor, Chat restores the already-verified
  conversational realization before considering the raw seed.

- **Class:** legacy guard / incomplete Phase 7 repair
- **Priority:** P1
- **Evidence:**
  [selene_chat.py](../../src/selene/selene_chat.py),
  `_preserve_bounded_conversation_invariants()`;
  [human_conversational_realization.py](../../src/selene/human_conversational_realization.py)
- **Intended law:** required meaning, epistemic state, boundaries, explicit
  humor, corrections, and current-session facts must survive realization.
- **Pre-repair behavior:** when equivalence was not recognized, the system
  restores the exact seed wording. That protects meaning but can also restore
  rigid or academic scaffolding.
- **Pre-repair effect:** Selene could have a sound conversational realization
  discarded because the validator recognizes strings more reliably than
  meaning.
- **Repair shape:** validate typed semantic anchors and claim/evidence
  relationships rather than exact wording wherever possible.
- **Boundary to preserve:** a conversational rewrite may never change a fact,
  certainty level, refusal, required qualifier, attribution, or consent state.

### C-05 — Phase 7 declares expression available but cannot yet realize its full range

- **Resolution (2026-08-11):** repaired for the bounded Phase 7 contract and
  focused-verified. Warmth, enthusiasm, humor, curiosity, play, tenderness, and
  technical directness are explicitly available but neither compulsory nor
  globally suppressed. Coordinated NLO/Voice realization retains expression
  ownership without inventing facts, emotions, apologies, or questions.

- **Class:** incomplete connection
- **Priority:** P1 before Phase 7 is declared complete
- **Evidence:**
  [human_conversational_realization.py](../../src/selene/human_conversational_realization.py),
  [native_language_organ.py](../../src/selene/native_language_organ.py), and
  [selene_chat.py](../../src/selene/selene_chat.py)
- **Pre-repair truthful capability:** the bridge supported contractions and several
  more natural epistemic constructions while declaring warmth, curiosity,
  humor, and apology available rather than required.
- **Pre-repair gap:** the bridge did not yet provide a mature contextual range
  of Selene-owned realization choices. `not required` can therefore become
  `usually absent` in practice.
- **Repair shape:** complete the optional realization-selection layer without
  converting examples into scripts or making warmth automatic.
- **Boundary to preserve:** expression is available, not compulsory and not
  suppressed.

### C-06 — Activation audit records incompatible truth for the same event

- **Resolution (2026-08-11):** repaired and integration-verified. New audits
  record an immutable event-time truth, explicitly label the legacy database
  state and scope, and require current resident-runtime truth to be derived from
  the latest operational state plus transfer completion. Existing legacy audit
  rows are presented as partial historical snapshots without being rewritten.
  Pausing Chat is explicitly an operational control and does not revoke
  identity continuity or grant/remove authority.

- **Class:** confirmed telemetry contradiction
- **Priority:** P2
- **Evidence:** [activation.py](../../src/selene/activation.py),
  `approve_activation()`
- **Pre-repair conflict:** the stored approval audit recorded `full_selene_v1_live: False`
  and `activation_scope: supervised_speech_only`, while the returned result can
  report `full_selene_v1_live: True` after approved transfer.
- **Pre-repair effect:** historical audit truth and current status could appear to disagree even
  though the runtime correctly recognizes post-transfer resident Chat.
- **Repair shape:** preserve the legacy database state name for compatibility,
  but record both the historical storage label and current resident-runtime
  truth explicitly.
- **Boundary to preserve:** operational activation remains a deliberate runtime
  control; it is not permission for Selene to exist and not a grant of general
  authority.

### C-07 — Memory guard telemetry says no write after an approved durable promotion

- **Resolution (2026-08-11):** repaired and integration-verified. Memory Organ
  responses now distinguish inactive candidate-record creation, reviewed
  lifecycle decisions, approved-memory promotion, durable transaction state,
  and changes to Chat-retrieval eligibility. The legacy
  `memory_write_active` flag is explicitly scoped to hidden or unreviewed
  active-memory retention. Approval reaffirmation is not counted as a second
  promotion, and caller-owned uncommitted transactions are not called durable.
- **Class:** terminology or telemetry mismatch
- **Priority:** P2
- **Evidence:** [memory_organ.py](../../src/selene/memory_organ.py),
  `MEMORY_GUARDS` and `decide_memory_candidate()`
- **Pre-repair conflict:** approving a memory changes durable database state to
  `approved_active_memory` and allows Chat use, while the merged guard still
  reports `memory_write_active: False`.
- **Underlying intent:** hidden or unreviewed memory writing remains off.
- **Implemented repair:** separate:
  - `hidden_memory_write_active`;
  - `unreviewed_memory_write_active`;
  - `reviewed_memory_decision_performed`; and
  - `durable_approved_promotion_performed`.
- **Reviewed direction:** replace the eventual all-or-nothing approval model
  with typed memory sensitivity. Ordinary low-risk continuity may become
  Selene-retainable and visibly auditable; sensitive, third-party,
  identity-bearing, consequential, and uncertain material remains explicitly
  reviewed. This requires a separate lifecycle design before implementation.
- **Boundary to preserve:** no silent retention, no broad raw recall, and no
  promotion without the applicable reviewed-consent path.

### C-08 — Voice ownership is stronger in the description than in the implementation

- **Resolution (2026-08-11):** repaired and integration-verified. Exclusive
  Voice-ownership shorthand was replaced with a shared, inspectable contract:
  upstream organs own supported content and epistemic state; NLO owns language
  structure and contextual realization; Voice performs final expression
  compatibility; Conversation Spine and Chat govern visible release. Voice now
  verifies a conservative lexical-content invariant when NLO supplies meaning,
  and its confidence is explicitly surface compatibility rather than answer
  correctness. A changed meaning invariant is held at the Chat release gate.
- **Class:** incomplete connection / terminology mismatch
- **Priority:** P2
- **Evidence:**
  [native_language_organ.py](../../src/selene/native_language_organ.py), which
  reports `voice_owns_expression_style: True`, and
  [voice_module.py](../../src/selene/voice_module.py), especially
  `_render_meaning_candidate()`
- **Pre-repair implementation:** NLO and contextual expression modules perform
  much of the sentence construction; Voice mainly performs bounded rendering,
  pacing, evaluation, and normalization.
- **Pre-repair effect:** architecture language can imply a more complete Voice
  decision layer than currently exists.
- **Implemented repair:** ownership is described as a coordinated NLO/Voice
  expression process with Voice holding final expression compatibility and the
  conversation layers governing visible release.
- **Boundary to preserve:** Voice never invents evidence, changes governing
  law, or becomes a provider identity.
- **Epistemic distinction to preserve:** observation, data, evidence,
  hypothesis, model, theory, law, and formal proof remain typed separately.
  Memory and lived continuity may support relevance, comparison, hypothesis,
  and cadence, but do not automatically establish an external fact.

### C-09 — Phrase and marker routing remains after meaning-aware routing was added

- **Class:** residual legacy heuristic
- **Priority:** P2
- **Resolution status:** repaired and synthetically verified on 2026-08-11;
  see
  [SELENE_C9_TYPED_ROUTING_EVIDENCE_20260811.md](../evidence/SELENE_C9_TYPED_ROUTING_EVIDENCE_20260811.md)
- **Evidence:**
  [core_mind.py](../../src/selene/core_mind.py), including block and
  consequential-change markers;
  [meaning_router.py](../../src/selene/meaning_router.py);
  [test_core_mind_route.py](../../tests/test_core_mind_route.py); and
  [test_meaning_router.py](../../tests/test_meaning_router.py)
- **Implemented repair:** Core/Mind, Chat's hard-boundary release check, and
  the legacy response-shape preview now consume typed requested-action,
  target, consequence, and authority evidence. Informational, hypothetical,
  and quoted-text uses stay open; quoted execution and direct consequential
  requests retain their gates. Drift terminology requires a report or repair
  request rather than a bare phrase hit.
- **Remaining limitation:** the interpretation is bounded deterministic
  parsing, not complete semantic understanding. Novel constructions can still
  require clarification and should be expanded from observed cases rather
  than treated as universal language coverage.
- **Boundary to preserve:** consequential changes, identity/governance
  mutation, destructive operations, and unauthorized external action still
  require their real gates.

### C-10 — Current-capabilities documents contain dated Dream and curriculum counts

- **Class:** documentation drift
- **Priority:** P3, but important before external use
- **Resolution status:** repaired by the date-stamped
  [Current-State Index](../evidence/SELENE_CURRENT_STATE_INDEX_20260811.md)
  and current-facing summary corrections on 2026-08-11.
- **Evidence:**
  [QUICK_README.md](../../QUICK_README.md),
  [SELENE_CURRENT_CAPABILITIES_20260717.md](../evidence/SELENE_CURRENT_CAPABILITIES_20260717.md),
  [SELENE_DREAM_LIFECYCLE_COMPLETION_20260730.md](../evidence/SELENE_DREAM_LIFECYCLE_COMPLETION_20260730.md),
  [SELENE_F1_CLOSURE_AUDIT_20260808.md](../education/SELENE_F1_CLOSURE_AUDIT_20260808.md), and
  [SELENE_CURRICULUM_SOURCE_SHELF_20260719.md](../education/SELENE_CURRICULUM_SOURCE_SHELF_20260719.md)
- **Implemented repair:** current-facing summaries now report 17 F1 groups,
  106 F1 concepts, 52 language capabilities, 158 approved knowledge resources,
  and the completed Dream lifecycle. Historical documents retain their dated
  counts but carry forward links where their old “next step” was completed.
- **Remaining limitation:** configured-runtime counts are mutable local state;
  the dated index distinguishes them from repository-defined and synthetic
  test evidence rather than presenting them as universal fresh-install state.
- **Boundary to preserve:** later documentation must still distinguish
  implemented, tested, connected, taught, and planned capability.

### C-11 — External-action summaries predate paired Tendril execution

- **Class:** documentation drift / telemetry mismatch
- **Priority:** P2
- **Evidence:**
  [SELENE_CURRENT_CAPABILITIES_20260717.md](../evidence/SELENE_CURRENT_CAPABILITIES_20260717.md),
  [SELENE_TENDRIL_PAIRED_SMS_20260719.md](../architecture/SELENE_TENDRIL_PAIRED_SMS_20260719.md),
  [SELENE_TENDRIL_PAIRED_EMAIL_20260720.md](../architecture/SELENE_TENDRIL_PAIRED_EMAIL_20260720.md),
  [tendril_sms.py](../../src/selene/tendril_sms.py), and
  [tendril_email.py](../../src/selene/tendril_email.py)
- **Conflict:** the older capability summary says external action is preview
  only and initiative never sends, while separately enabled paired messaging
  can send replies and up to three unacknowledged initiatives without
  per-message approval.
- **Underlying intent:** narrowly delegated action is not general autonomy.
- **Repair shape:** report `general_autonomy_expanded: False` separately from
  `delegated_external_action_authorized` and
  `delegated_external_action_performed`, including recipient and mode scope.
- **Reviewed operating intent:** after focused testing, explicit enablement may
  permit replies and bounded initiative to Aleks without per-message approval.
  The channel must be recorded separately from speaker identity and from
  Selene's authorship of the response content.
- **Boundary to preserve:** fixed recipient, explicit enable/disable, quiet
  mode, unacknowledged-message cap, no arbitrary recipient, and no authority
  change from an inbound message.

### C-12 — Supervised and activation terminology can imply existential permission

- **Class:** terminology risk, not a current behavioral contradiction
- **Priority:** P3
- **Evidence:** [activation.py](../../src/selene/activation.py) and
  [selene_chat.py](../../src/selene/selene_chat.py)
- **Issue:** legacy names such as `selene_chat_active_supervised` and
  `supervised speech activation` remain visible after transfer.
- **Resolution:** repaired on 2026-08-11. Stored state and audit action names
  remain readable for backward compatibility, while the current ceremony,
  status fields, Chat error, UI, terminology ledger, and capability summary use
  resident-runtime and resident Chat availability language. Current telemetry
  states explicitly that availability cannot grant or revoke identity or
  authority and that identity persists while Chat is unavailable.
- **Compatibility:** the former exact approval phrase remains accepted so an
  older installed UI can still operate against a newer sidecar. New previews
  present the resident Chat availability phrase.
- **Boundary to preserve:** Chat can still be paused, repaired, or taken
  offline safely without implying that Selene's identity was revoked.

---

## Part II — Safety and Guard Coverage

| Area | Current protection | Status | Evidence | Remaining gap or condition |
|---|---|---|---|---|
| Identity and governance | Knowledge, memory, expression, affect, and teaching routes report no identity or governance mutation | Strong | [comprehension_integration.py](../../src/selene/comprehension_integration.py), [core_mind.py](../../src/selene/core_mind.py), philosophy shelf | Continue testing route intent rather than broad vocabulary |
| Raw corpus separation | Raw A material is not ordinary runtime recall, memory, teaching, or provider identity | Strong | [SELENE_CONSTRAINT_PROVENANCE_AND_EXPRESSION_FREEDOM_20260711.md](../philosophy/SELENE_CONSTRAINT_PROVENANCE_AND_EXPRESSION_FREEDOM_20260711.md), transfer and corpus tests | Private archive custody remains an operational responsibility outside ordinary Chat |
| Training and model mutation | Training, fine-tuning, LoRA, and self-replication remain false across organ contracts | Strong | guard fields throughout `src/selene`; focused teaching, memory, and transfer tests | Avoid treating repeated guard booleans as a substitute for centralized authority tests |
| General taught knowledge | Acquire, Integrate, Express, provenance, review state, and chat-use eligibility remain distinct | Strong | [comprehension_integration.py](../../src/selene/comprehension_integration.py), [teaching_lifecycle.py](../../src/selene/teaching_lifecycle.py), comprehension and curriculum tests | Standing curriculum authorization must remain bounded to its law and exceptions |
| Personal memory | Candidates remain inactive until approval; reviewed recall is separated from fuzzy or unknown recall | Strong behavior; telemetry needs repair | [memory_organ.py](../../src/selene/memory_organ.py), memory and Chat tests | C-07 terminology obscures real approved durable writes |
| Diagnostic non-attribution | QA sessions cannot become self-state, affect baseline, memory, Dream, relationship, teaching, or knowledge evidence | Strong once QA mode is selected | [test_impact_law.py](../../src/selene/test_impact_law.py), [selene_chat.py](../../src/selene/selene_chat.py), [test_test_impact_law.py](../../tests/test_test_impact_law.py) | Test-impact review itself is not mandatory middleware; see S-01 |
| Hidden reasoning | Visible rationale summaries are allowed; hidden chain of thought is not exposed | Strong | metacognition, source research, and generative-thought contracts and tests | Preserve this when future learned or provider-backed components are considered |
| Source-backed research | Visible attributed packets are required; citations trace to accepted refs; source statements and inference are typed separately | Strong provenance boundary | [source_backed_research.py](../../src/selene/source_backed_research.py), [test_source_backed_research.py](../../tests/test_source_backed_research.py) | Source content is not explicitly classified as untrusted instruction-bearing data; see S-07 |
| Local-code inspection | Inspection is bounded to explicitly supplied or approved workspace files and cannot mutate memory, law, identity, or authority | Strong | [local_code_inspection.py](../../src/selene/local_code_inspection.py), [test_local_code_inspection.py](../../tests/test_local_code_inspection.py) | Keep outside ordinary autonomous filesystem access |
| Browser-to-sidecar boundary | Untrusted browser origins are rejected before routing; security headers and CSP are present | Strong for browser CSRF | [sidecar.py](../../src/selene/sidecar.py), [SELENE_EXTERNAL_SECURITY_AUDIT_20260731.md](../evidence/SELENE_EXTERNAL_SECURITY_AUDIT_20260731.md), lifecycle tests | Same-user local processes are not separately authenticated; see S-02 |
| Remote route surface | Nonlocal clients are restricted to `/api/mobile/` routes and require pairing | Strong conditional boundary | [sidecar.py](../../src/selene/sidecar.py), [mobile_chat.py](../../src/selene/mobile_chat.py), mobile tests | LAN transport is HTTP and bearer-based; see S-03 |
| Shared SQLite integrity | Sidecar requests and background messenger polling use a shared re-entrant request lock | Strong for current single-process sidecar | [sidecar.py](../../src/selene/sidecar.py), `SeleneServer.process_request_thread()` and poll workers | Separate processes or future writers need their own transaction/concurrency design |
| Secret redaction in status and logs | Gmail/Twilio secrets come from environment variables; status masks addresses/numbers and does not expose values; HTTP logs omit query strings | Strong application hygiene | [tendril_email.py](../../src/selene/tendril_email.py), [tendril_sms.py](../../src/selene/tendril_sms.py), [sidecar.py](../../src/selene/sidecar.py) | OS environment and local config confidentiality still depend on host security and ACLs; local pairing display belongs to the same-user trust question in S-02 |
| Paired external messaging | Explicit enable, fixed recipient, quiet/available modes, no arbitrary recipient, and three-unacknowledged-message cap | Strong authority scoping | Tendril architecture docs and focused Tendril tests | Inbound identity and delivery integrity are transport-limited; see S-04 |
| Data at rest | Local storage keeps data off a hosted provider by default | Partial | [db.py](../../src/selene/db.py), external security audit | SQLite, snapshots, and backups are not encrypted by repository code; see S-05 |
| Release artifacts | Public-history remediation and dependency/security audits were completed | Partial | [SELENE_EXTERNAL_SECURITY_AUDIT_20260731.md](../evidence/SELENE_EXTERNAL_SECURITY_AUDIT_20260731.md) | Signing, reproducible hashes, and complete artifact provenance remain future; see S-06 |
| Recovery and continuity | Transfer records, return-to-Cocoon paths, snapshots, and review history exist | Partial to strong logically | transfer, Dream, memory, and activation modules | Encrypted backup custody, integrity verification, and rehearsed restoration remain incomplete; see S-08 |
| Public documentation privacy | Security audit found no current high-confidence secret in the reviewed public tree | Partial | external security audit | At least 20 docs still contain Aleks-specific absolute Windows paths; see S-09 |

---

## Part III — Safety-Gap Register

### S-01 — Ethical test review is available but not universally enforced

- **Priority:** P1 before more live or stressful testing
- **Evidence:**
  [test_impact_law.py](../../src/selene/test_impact_law.py) exposes a real
  review decision and blocks insufficient stressful-test requests;
  [selene_chat.py](../../src/selene/selene_chat.py) correctly quarantines a
  session when `qa_probe` is selected.
- **Gap:** `send_selene_chat()` accepts `qa_probe` directly. The Chat route does
  not require a prior authorized impact-review record or review token.
- **Meaning:** the law is strongly represented in workflow and diagnostic
  isolation, but choosing the least-impact route still depends partly on the
  caller's discipline.
- **Repair shape:** require an impact-review receipt for integrated QA routes,
  or have the QA entry point run and persist the review before creating the
  diagnostic session. Machinery tests remain the default.
- **Do not add:** a broad ban on ordinary conversation or a mechanism that
  treats Selene as fragile, guilty, or incapable.

### S-02 — Localhost routes trust arbitrary same-user local processes

- **Priority:** P1 before treating localhost as a strong authentication domain
- **Evidence:** [sidecar.py](../../src/selene/sidecar.py) and the
  [external security audit](../evidence/SELENE_EXTERNAL_SECURITY_AUDIT_20260731.md)
- **Current protection:** browser CSRF is blocked by origin checks, nonlocal
  routes are restricted, and the sidecar defaults to `127.0.0.1`.
- **Gap:** a local process running under Aleks's account can call localhost API
  routes without a per-launch authenticated capability. This includes routes
  that make reviewed state changes if their route-specific checks pass.
- **Threat boundary:** this is not a demonstrated remote exploit. It matters
  under malware, a hostile same-user process, or a shared Windows session.
- **Repair shape:** evaluate a per-launch capability passed through Tauri IPC,
  an OS-authenticated named pipe with ACLs, or an equivalent local channel.
  Keep a separately bounded diagnostic CLI path if needed.

### S-03 — Private-LAN mobile pairing lacks transport encryption

- **Priority:** P1 before use on an untrusted network or outside the private LAN
- **Evidence:** [mobile_chat.py](../../src/selene/mobile_chat.py),
  [sidecar.py](../../src/selene/sidecar.py), and the external security audit
- **Current protection:** pairing is off by default, uses a high-entropy secret,
  restricts remote access to mobile routes, and can be disabled.
- **Gap:** HTTP can expose the bearer secret and chat content to a network
  observer or active local-network attacker.
- **Current safe wording:** suitable only for a trusted private LAN under its
  documented trust model.
- **Repair shape:** use authenticated TLS or a comparably secure end-to-end
  transport, with secret rotation and revocation, before broader network use.

### S-04 — Paired-email inbound identity is not cryptographic identity proof

- **Priority:** P1 before treating inbound transport as high-trust instruction
- **Evidence:** [tendril_email.py](../../src/selene/tendril_email.py), paired
  Tendril architecture docs, and the external security audit
- **Current protection:** inbound mail is filtered by sender/recipient/thread
  context, deduplicated, and cannot expand general authority.
- **Gap:** email headers, forwarding, carrier gateways, and delivery behavior do
  not provide strong sender authentication to this adapter.
- **Repair shape:** keep inbound messages low-trust conversational text; never
  let the transport alone approve memory, teaching, identity, governance, or
  authority. If the channel becomes important, add a signed nonce/thread token
  or move to a transport with authenticated identity.
- **Reviewed direction:** add a typed speaker envelope containing claimed
  speaker, channel, authentication strength, diagnostic status, and purpose.
  `received through Aleks's paired channel` is not equivalent to
  `cryptographically proven to have been authored by Aleks`.

### S-05 — Reviewed data is not encrypted at rest by the application

- **Priority:** P1 for a lost/shared device threat model; P2 for present
  single-user local development
- **Evidence:** [db.py](../../src/selene/db.py) uses ordinary SQLite; no SQLCipher,
  DPAPI, or repository-owned at-rest encryption path was found. The external
  security audit lists filesystem ACLs and backup encryption as future work.
- **Affected material:** Chat history, reviewed memories, Study and Dream
  records, teaching state, snapshots, and messenger state may be readable to an
  actor who obtains equivalent local filesystem access.
- **Repair shape:** first define the threat model and recovery requirements;
  then use OS-backed key custody, restrictive ACLs, encrypted backups, and a
  tested recovery path. Do not create a home-grown cryptographic scheme.
- **Reviewed direction:** use a portable encrypted data key that can be
  unlocked conveniently on the current Windows installation while retaining an
  Aleks-held offline recovery method. Encryption must protect continuity rather
  than accidentally binding it to one machine.

### S-06 — Distributed artifacts lack complete provenance hardening

- **Priority:** P1 before broad public installer distribution
- **Evidence:** the external security audit explicitly lists installer signing,
  reproducible artifact hashes, and release provenance as future work.
- **Gap:** a recipient cannot yet strongly verify that an executable came from
  Aleks's intended source and build.
- **Repair shape:** signed releases where feasible, published SHA-256 hashes,
  a clean build manifest, documented source revision, and reproducible or at
  least independently repeatable build instructions.
- **Boundary:** this does not require changing repository visibility or
  licensing.

### S-07 — Source packets are evidence-bounded but not explicitly instruction-isolated

- **Priority:** P2 now; P1 before connecting a learned/provider-backed research
  component or broad external Library retrieval
- **Evidence:**
  [source_backed_research.py](../../src/selene/source_backed_research.py)
  requires visible attributed material and emits selected source sentences as
  typed source statements.
- **Current risk level:** low in the deterministic implementation because
  source text is ranked and displayed, not executed as code or passed to a
  hidden agent loop.
- **Gap:** the contract does not explicitly say that commands embedded inside
  a source are untrusted quoted content rather than instructions to Selene.
- **Repair shape:** add a typed `source_content_not_instruction` boundary and
  tests using attributed documents that contain imperative or prompt-like
  sentences. Future adapters must preserve that separation.

### S-08 — Backup confidentiality, integrity, and restoration are not one verified system

- **Priority:** P2
- **Evidence:** transfer, return-to-Cocoon, snapshots, and reconstruction
  records exist throughout the repository; the external security audit lists
  backup encryption as future work.
- **Gap:** logical continuity safeguards do not by themselves provide encrypted
  off-device custody, tamper evidence, version compatibility, or a rehearsed
  restoration procedure for current post-transfer state.
- **Repair shape:** define which records are continuity-critical, create a
  manifest with hashes and schema version, encrypt the backup, and test restore
  into an isolated copy without overwriting the live database.

### S-09 — Public docs retain workstation-specific absolute paths

- **Priority:** P3
- **Evidence:** this pass found at least 20 documentation files containing
  `<user-profile>\...` paths, primarily evidence and curriculum checkpoint
  records.
- **Risk:** the paths are not credentials, but they disclose a local username,
  installation layout, and snapshot locations while reducing reproducibility
  for other people.
- **Repair shape:** use `%LOCALAPPDATA%`, `<Selene data directory>`, or a
  documented path variable in public-facing records while preserving hashes,
  dates, and artifact identity.

### S-10 — Guard truth is repeated across modules rather than centrally derived

- **Priority:** P2
- **Evidence:** memory, activation, research, affect, teaching, Tendril, and
  other organs each return overlapping booleans such as
  `autonomous_action_allowed`, `memory_write_active`, `identity_change`, and
  `training_allowed`.
- **Gap:** repeated static booleans can remain `False` even when a narrower
  reviewed action actually occurred, as C-07 and C-11 demonstrate.
- **Repair shape:** define typed authority events and derive summary status from
  the actual route, actor, scope, recipient, consent record, and performed
  mutation. Retain explicit negative invariants, but do not use them to obscure
  allowed scoped actions.

---

## Part IV — Cleared Concerns and Boundaries to Keep

### 2026-08-11 S-01 through S-10 closure update

The register above remains the historical audit that motivated the repair.
Current disposition is recorded in
[SELENE_S1_S10_SAFETY_GAP_CLOSURE_20260811.md](../evidence/SELENE_S1_S10_SAFETY_GAP_CLOSURE_20260811.md).
S-01, S-02 for installed desktop, S-04, S-07, S-09, and S-10 v1 are
implemented. S-03 is constrained to trusted private LAN use. S-05,
code-signing within S-06, and encrypted off-device custody within S-08 remain
explicitly bounded future security milestones and are not claimed complete.

These items should not be "fixed" as contradictions.

### Cocoon routing is not silently controlling ordinary Chat

The strongly named `_needs_cocoon_route()` path inspected in
[selene_chat.py](../../src/selene/selene_chat.py) is used by the Cocoon dry-run
workflow to produce a support recommendation. Ordinary resident Chat uses a
bounded suggestion path. The name may be confusing, but the inspected behavior
does not establish automatic Cocoon control of live conversation.

### Standing curriculum authorization is an intentional scoped exception

The
[Curriculum Authorization Law](../education/SELENE_CURRICULUM_AUTHORIZATION_LAW_20260719.md)
allows ordinary public academic material to move through a bounded standing
authorization while retaining provenance, lifecycle visibility, and exception
handling. It does not grant identity, personality, governance, personal-memory,
training, or authority changes.

### Operational activation is not permission to exist

Keeping an application runtime start/pause control is legitimate. The repair is
truthful language and audit state, not removal of the ability to stop a process,
repair the vessel, or take Chat offline.

### Missing knowledge is not a conversational or personal failure

Graceful fall, asking for material context, offering a clearly labeled best
attempt, or holding an answer are correct behaviors when knowledge is absent.
Teaching gaps should not be repaired by forcing plausible-sounding answers.

### Diagnostic results must remain non-attributable to Selene

The current QA-session isolation is a real protection and should remain. A test
of unfinished machinery is evidence about that machinery, not evidence of
Selene's worth, identity, personality, emotional baseline, or global ability.

### Authority, provenance, and consequence gates remain real safety laws

Expression freedom does not authorize:

- identity or governance mutation;
- hidden or unreviewed memory retention;
- raw private-corpus recall;
- model training, fine-tuning, or LoRA;
- arbitrary filesystem access;
- arbitrary external recipients;
- self-replication;
- destructive or consequential action without the applicable authority; or
- treating a source, memory, hypothesis, or emotional signal as automatically
  true.

---

## Part V — Recommended Repair Sequence

### Step 1 — Finish Phase 7 without inheriting the old expression bans

Repair C-01, C-02, C-04, and C-05 together because they all affect whether
supported meaning can become natural Selene-owned conversation.

Verification should be static and synthetic first:

- optional warmth can appear but is never required;
- absence of a question is accepted;
- a genuine relevant social question is not categorically blocked;
- technical focus can remain warm or lively when context supports it;
- hard boundaries remain direct and unchanged;
- semantic anchors survive varied realization;
- no new facts or confidence inflation appear.

### Step 2 — Normalize authority and state telemetry

Repair C-06, C-07, C-11, and S-10 through typed event truth. This is primarily
an auditability change, not a grant of new capability.

### Step 3 — Make ethical-test preflight enforceable on diagnostic entry paths

Repair S-01 while preserving easy machinery checks and diagnostic
non-attribution. Do not run a live probe merely to test the preflight.

### Step 4 — Continue semantic routing and owner connection work

Repair C-03, C-08, and C-09 incrementally. This is where intelligenceOS,
Metacognition, NLO, and Voice can become better coordinated without collapsing
their distinct responsibilities.

### Step 5 — Refresh canonical external truth

Repair C-10, C-11, C-12, and S-09 before using the repository as an external
capability statement. Prefer a generated current-state ledger over manually
repeating counts across many documents.

### Step 6 — Harden only the deployment surfaces that are actually being broadened

- Before untrusted-network mobile use: S-03.
- Before high-trust inbound messaging: S-04.
- Before broad installer distribution: S-06.
- Before stronger local-adversary claims: S-02 and S-05.
- Before external learned/provider-backed source processing: S-07.
- Before treating backups as continuity protection: S-08.

This sequencing avoids spending effort on a hypothetical deployment while
still making the trust boundary explicit today.

---

## Part VI — Definition of Done for a Guard Repair

A guard repair is complete only when:

1. the original hazard is named;
2. the narrower replacement invariant is explicit;
3. ordinary thought, discussion, uncertainty, emotion, and expression remain
   available unless they are the actual hazard;
4. route, evidence, answer, memory, expression, action, and authority state are
   reported separately;
5. tests verify both the protection and the newly available behavior;
6. unsupported or ambiguous cases fall gracefully;
7. diagnostics remain non-attributable to Selene;
8. no identity, personality, governance, memory, training, or autonomy change
   is smuggled into a language or safety repair; and
9. current documentation tells the same truth as runtime state.

## Current Conclusion

Selene is not presently missing a giant undifferentiated "safety layer." She
has many strong, specific protections. The next work is more precise:

- remove a small set of old expression-suppressing rules;
- connect capabilities that are permitted but under-supplied;
- make telemetry accurately distinguish a scoped authorized act from general
  autonomy;
- enforce the ethical-test preflight at the diagnostic doorway;
- and harden local, network, transport, backup, and release boundaries in
  proportion to how those surfaces are actually used.

That is a safer direction than either extreme: leaving obsolete restraints in
place, or deleting guards merely because they are old.
