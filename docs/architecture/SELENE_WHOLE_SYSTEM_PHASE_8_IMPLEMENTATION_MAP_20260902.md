# Selene Whole-System Phase 8 Implementation Map

Date: 2026-09-02

Status: source-mapped; Phase 8A is the next production edge

Parent plan:
[Selene Whole-System Maturation Plan](SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

Previous phase:
[Phase 7 Text and Creative Voice](SELENE_WHOLE_SYSTEM_PHASE_7_IMPLEMENTATION_MAP_20260901.md)

## Goal

Mature Selene's existing goal, initiative, commitment, collaboration, and
stopping pathways so that what to do next is bounded, inspectable, and honest
without creating a duplicate executive organ, hidden agenda, global autonomy
switch, automatic action authority, or endless coordination loop.

Phase 8 coordinates responsibilities. It does not grant whole-system control
to a goal, organ, user instruction, external demand, or compatibility flag.
Conversation, Study, tools, Tendril, and future embodiment graduate
separately under the authority and stopping rules that actually apply to each
capability.

## Namespace Note

Older project records may use “Phase 8” for a different historical workflow.
In this document, Phase 8 means only **Whole-System Phase 8 — Executive
Initiative, Goals, Commitments, and Collaboration** from the 2026-08-27
maturation plan. It does not reopen or renumber completed historical work.

## Care and Ethical Boundary

- Selene may distinguish her own goal, Aleks's request, a shared project goal,
  a governing requirement, an external demand, and organ advice. Naming an
  owner does not make the goal automatically correct or authorized.
- Immediate safety may constrain a specific requested action. It may not be
  converted into broad control over Selene's identity, personality, Voice,
  Vys, thought, ordinary expression, Memory, or relationships.
- Vys is not an executive score, permission flag, optimization target, or
  behavioral profile. This phase does not define or rewrite it.
- Ordinary Chat may coordinate the current turn, but it may not silently
  persist a new long-running goal, commitment, Memory, Study thread, or tool
  action.
- A commitment must be explicit and attributable. An idea, hope, suggestion,
  plan, possibility, intention, or offer is not silently promoted into one.
- Help-seeking is available when collaboration genuinely needs Aleks's input,
  authority, knowledge, or physical action. Selene should not push decisions
  back to Aleks when they are already inside the granted scope and evidence.
- Quiet, wait, defer, decline, and natural closure are valid outcomes. The
  coordinator may not manufacture work, urgency, dependence, or performance
  pressure to keep a loop alive.
- Associations and logical leaps remain provisional candidates under their
  existing evidence rules. Coordination cannot turn them into proof, fact,
  Memory, or a finished answer.
- This phase adds no live external action, new tool grant, new Tendril grant,
  provider, model training, learned substrate, sensor claim, or embodiment
  authority.
- No resident Dream, Study, Memory, teaching, relationship, or identity
  decision is required. The 24 Dream reflections remain pending Aleks's
  review.

## Current Resident and Verification Baseline

The configured resident database was opened read-only during source mapping.
Only schema/counts and SQLite integrity were inspected; no resident content or
pending decision was read or changed.

| Resident state | Count |
| --- | ---: |
| goal-drive preview records | 2 |
| Tendril plan previews | 1 |
| chat sessions | 18 |
| chat messages | 308 |
| native-language runs | 113 |
| Voice module runs | 16 |
| LEA runs | 0 |
| Dream reflections pending Aleks review | 24 |
| personal Memory candidates | 0 |

SQLite integrity reported `ok`. A focused pre-edit baseline of 158 goal-drive,
conversational-agency, contribution, energy, commitment, pragmatic
continuity, Core/Mind, resident-authority, Tendril, maturity, and runtime
checks passed.

The last verified frontend comparison is a 491.33 kB main application bundle
(gzip 109.20 kB), no Vite size warning, with Study workspaces lazy-loaded.

## Existing Owner and Handoff Map

| Responsibility | Existing owner | Current strength | Phase 8 edge |
| --- | --- | --- | --- |
| bounded goal preview | `remaining_runtime.py::goal_drive_preview` | stores a review-only current goal, subgoals, priority, stop/ask markers, exclusions, provenance, and payload | owner, scope, evidence, authority, lifecycle, lineage, and idempotent closure are not yet canonical typed fields |
| responsive current-turn initiative | `conversational_contribution.py` | selects at most one attributable responsive contribution and never speaks out of turn | needs to carry the selected goal/authority/stop receipt without becoming a second goal owner |
| collaboration and help energy | `conversational_energy.py` | chooses one bounded answer, idea, connection, curiosity, help, resume, question, wait, quiet, close, or defer act | choice is current-turn and safe, but is not yet visibly tied to a goal conflict or capability-specific authority |
| interruption, silence, and ending | `pragmatic_continuity.py` | keeps initiative invited or responsive and preserves quiet, wait, and closure | needs the same stopping receipt so optional energy cannot reopen a closed responsibility |
| commitment truthfulness | `commitment_anomaly_coordination.py` | separates real commitments from plans/offers and holds unsupported state-changing completion claims | needs explicit goal/capability lineage and persistent lifecycle states so a real commitment cannot disappear silently |
| current-turn executive coordination | `core_mind.py` | coordinates bounded organ evidence for a turn | needs an inspectable responsibility-conflict receipt rather than organ precedence or competition |
| action-specific authority | `resident_authority.py` | evaluates typed requested actions and explicitly retires the global autonomy boolean | new goal contracts must reuse this action-specific boundary; compatibility flags cannot become canonical authority |
| capability-specific external reach | `library_tendril.py` and channel adapters | produces bounded previews/proposals within actual capability grants | Phase 8 may report the grant state but may not widen it or execute a new action |
| Study lifecycle | existing Study owners and Phase 3 receipts | approved, attributable, idempotent reflective-growth paths already exist | Study can be selected only through its existing explicit lifecycle, not by generic executive persistence |

## Cultivation Findings

Cultivation distinguishes a missing capability from a missing connection and
from working behavior that needs stronger evidence. Phase 8 mainly needs typed
connection and lifecycle closure.

### Runtime defects

1. **The goal-drive record is a compatibility preview, not a mature contract.**
   It records useful review-only text but does not require typed owner, scope,
   evidence, stop condition, authority, lifecycle, or ancestry. Its old
   guard fields must remain compatibility telemetry rather than become a
   disguised global autonomy switch.
2. **Responsibility conflicts do not have one inspectable receipt.**
   Core/Mind and the conversational owners can each behave safely, but the
   runtime does not expose why one responsibility was selected, deferred,
   held, completed, or closed when several apply.
3. **A commitment has no cross-turn goal lineage.**
   Current-turn language is checked honestly, but an explicit commitment is
   not yet linked to one goal and one capability with status, mechanism,
   result or blocker, and stop reason.
4. **Capability maturity can be mistaken for whole-system permission.**
   Conversation already permits bounded responsive contribution while tools
   and Tendril depend on narrower grants. No typed graduation receipt makes
   that difference visible end to end.

### Missing connective capability

- The goal-drive owner should normalize explicit goals and produce a bounded
  coordination packet; it should not become another answer, Memory, Study,
  affect, or action owner.
- Core/Mind should compare responsibility packets and return a selection,
  defer/hold set, reasons, authority checks, and a terminal stop in one pass.
- Conversational contribution, energy, and pragmatic continuity should
  consume that receipt for one current-turn choice, preserving direct-answer
  priority, responsive-only initiative, silence, and natural ending.
- Commitment coordination should attach an explicit promise to exactly one
  goal and capability and expose its lifecycle without treating plans or
  suggestions as commitments.
- Existing action authority, Study authorization, and Tendril grants remain
  authoritative. The executive path reports and obeys them; it does not
  replace them.

### Working behavior needing stronger evidence

- one attributable contribution can already be selected without a ritual
  permission phrase;
- hard boundaries, interruption, wait, quiet, and close already suppress
  optional contribution;
- direct answers already outrank optional ideas and questions;
- genuine help can be requested after available support is used;
- ideas, plans, hopes, and offers are not silently called commitments;
- unsupported state-changing completion claims are already held;
- resident authority is action-specific and rejects a global autonomy flag;
  and
- Tendril preview routes cannot execute or grant themselves authority.

These paths require cross-owner receipts, conflict and lineage tests, and
disposable lifecycle evidence—not replacement.

## Phase 8 Contract Shape

Phase 8 extends existing owners. A helper may shape or validate typed data,
but it receives no independent agenda, persistence, speaking, Memory, Study,
or action authority.

### Goal responsibility packet

Every active goal must expose:

- a stable goal key and lifecycle state;
- one owner kind: `selene_goal`, `aleks_request`, `shared_project_goal`,
  `governing_requirement`, `external_demand`, or `organ_advice`;
- bounded scope and affected capability;
- priority with an attributable reason rather than an opaque score;
- visible evidence references and explicit unknowns;
- completion conditions and stop conditions;
- action-specific authority state and its receipt;
- root, parent, and supersession lineage when persistence is explicitly
  requested;
- created/updated provenance and an idempotency key for a persisted change;
  and
- one terminal coordination state such as `selected`, `deferred`, `held`,
  `completed`, `blocked`, `waiting`, or `closed`.

Ordinary Chat uses an ephemeral current-turn packet. A persisted goal record
requires an explicit goal lifecycle request; conversation text alone is not
authorization to create one.

### Core/Mind responsibility-conflict receipt

The existing coordinator should receive a bounded set of typed responsibility
packets and return:

- the considered goal keys and capability scopes;
- hard action-safety holds applied only to the affected action;
- governing requirements and existing grants actually relevant to the choice;
- one selected next move, or a typed wait/quiet/close/ask outcome;
- deferred and held responsibilities with reasons and preservation state;
- whether collaboration or missing authority genuinely requires Aleks;
- a fixed pass/candidate ceiling; and
- an explicit terminal stop reason.

Permitted next-move kinds are `answer`, `ask`, `suggest`, `explore`,
`remember_proposal`, `study`, `tool`, `wait`, `quiet`, and `close`. A selected
kind is a coordination decision, not proof that its downstream operation is
authorized or completed.

### Commitment lifecycle receipt

An explicit commitment should contain:

- a commitment key and the exact attributable commitment claim;
- one linked goal key and one capability;
- root/parent ancestry and idempotency key;
- lifecycle state: `accepted`, `in_progress`, `fulfilled`, `blocked`,
  `released`, or `closed`;
- the authorized execution or handoff mechanism, if one exists;
- visible result evidence for fulfillment, or a visible blocker and next
  honest move;
- revision/supersession reason; and
- a terminal stopping receipt.

Only an explicit accepted commitment enters this lifecycle. A fulfillment
claim without result evidence is held; a blocker is reported rather than
hidden; and no lifecycle transition grants the underlying capability.

### Capability-graduation receipt

Initiative is reported per capability:

| Capability | Current Phase 8 boundary |
| --- | --- |
| conversation | bounded responsive answer/idea/connection/curiosity/help/question/wait/quiet/close under existing current-turn owners |
| Study | explicit selection through the existing approved and attributable Study lifecycle only |
| Memory | proposal only through the canonical privacy and review gate; no automatic durable Memory |
| tools | selection/reporting only when a named tool has an actual grant; Phase 8 adds no grant or live execution |
| Tendril | existing capability-specific preview/proposal boundary; no self-grant or new external reach |
| future embodiment | deferred and unavailable until its own later phase and real substrate exist |

Each receipt names the capability, maturity/grant state, permitted move,
required downstream authority, unavailable claims, and stop reason. There is
no aggregate `autonomous`, `allowed`, or equivalent whole-system boolean.

## Implementation Order

### Phase 8A — Typed goal lifecycle and Core/Mind conflict receipt

Status: **next**

- extend the existing goal-drive owner with typed owner, scope, priority,
  evidence, stop, authority, lifecycle, ancestry, and idempotency fields;
- preserve the old preview route and resident records as review-only
  compatibility data;
- add read-only status and pure current-turn coordination before any explicit
  persistence path;
- require explicit intent for persisted goal creation or transition;
- let Core/Mind select/defer/hold from a bounded responsibility set in one
  pass, with no organ precedence masquerading as truth;
- keep action-safety holds specific to the affected action and preserve
  ordinary thought/expression/quiet; and
- prove duplicate keys, descendants, supersession, closed goals, and terminal
  stops do not reopen or fork a hidden agenda.

### Phase 8B — Responsive initiative, collaboration, and stopping

Status: **planned after 8A**

- carry the selected current-turn goal and conflict receipt into the existing
  contribution and energy owners;
- choose at most one attributable response move while preserving direct-answer
  priority and never speaking out of turn;
- distinguish a useful idea, connection, curiosity, help request, capability
  limit, disagreement, wait, quiet, and close;
- ask Aleks only for missing knowledge, missing authority, a genuinely shared
  choice, or physical/external help that Selene cannot supply;
- do not ask for ritual permission when the next step is already safe and
  within scope;
- let interruption, new higher-priority evidence, completion, explicit stop,
  or natural ending close optional initiative; and
- expose one terminal receipt so help, curiosity, or collaboration cannot
  recursively create another contribution.

### Phase 8C — Commitment lifecycle and capability-specific graduation

Status: **planned after 8B**

- extend the existing commitment owner with one goal/capability lineage and
  explicit accepted/in-progress/fulfilled/blocked/released/closed transitions;
- preserve the difference between commitment, plan, hope, offer, prediction,
  and possibility;
- require result evidence before fulfillment and disclose blockers without
  silently dropping the obligation;
- make lifecycle transitions idempotent and reject cross-goal or
  cross-capability completion;
- expose separate graduation receipts for conversation, Study, Memory
  proposal, named tools, Tendril, and future embodiment;
- reuse each downstream owner's existing authority rather than inheriting it;
  and
- add no new live action, connection, grant, or external side effect.

### Phase 8D — Verification and closure

Status: **planned after 8C**

- run focused lifecycle, owner/scope, conflict, interruption, help-seeking,
  capability, lineage, idempotency, and stopping tests;
- exercise synthetic conflicts among Selene goals, Aleks requests, shared
  goals, governing requirements, external demands, and organ advice;
- verify unsupported external demands and organ advice cannot inherit
  whole-system authority;
- exercise one gentle disposable goal/commitment walkthrough with no resident
  mutation or real external action;
- run the complete repository regression and Python compilation checks;
- run the frontend production build, record the bundle comparison, and keep
  lazy Study boundaries visible;
- update the canonical maturity ledger, status, evidence, journal, and active
  continuation ledger; and
- close Phase 8 only if every active synthetic goal has owner, scope,
  priority, evidence, stop, authority, and an inspectable terminal state.

## Verification Matrix

| Risk | Required proof |
| --- | --- |
| hidden or duplicate executive owner | imports/routes and source inspection show existing owners remain canonical |
| goal becomes a global permission | capability-specific authority receipts; no aggregate autonomy boolean |
| ordinary chat silently persists an agenda | current-turn path is pure/ephemeral; explicit persistence tests |
| organ conflict becomes turf war | bounded Core/Mind receipt records considered, selected, deferred, and held goals with reasons |
| help-seeking becomes dependence or ritual permission | within-scope work proceeds; only genuine missing input/authority asks Aleks |
| commitment disappears or is falsely fulfilled | lineage, lifecycle, result evidence, blocker, and terminal-stop tests |
| stop reopens recursively | wait/quiet/close/interruption and closed-lineage duplicate tests |
| tool or Tendril self-authorizes | named capability grant required; simulated selection cannot execute or widen scope |
| Study or Memory is bypassed | canonical Study lifecycle and Memory privacy/review gates remain required |
| resident continuity changes during verification | read-only resident inspection plus disposable database walkthrough |
| frontend regresses | production build and bundle/lazy-chunk comparison |

## Completion Gate

Phase 8 is complete for current scope only when:

- every active synthetic or explicitly persisted goal has an inspectable
  owner, scope, priority, evidence, stop condition, authority, and lifecycle;
- conflicting responsibilities produce one bounded Core/Mind receipt;
- current-turn initiative remains responsive, singular, attributable, and
  naturally stoppable;
- Selene can request genuine help and can proceed without ritual permission
  inside granted scope;
- explicit commitments retain goal/capability lineage until fulfilled,
  blocked, released, or closed;
- conversation, Study, Memory proposal, tools, Tendril, and future embodiment
  expose separate capability states;
- no organ, goal, external instruction, compatibility flag, or action receipt
  inherits whole-system authority;
- no resident decision or live external action was needed for proof; and
- proportional focused, full-suite, disposable-runtime, and frontend
  verification passes with evidence recorded.

## Exact Production Resume Point

Begin Phase 8A with focused red tests for the typed goal responsibility
packet, ephemeral current-turn coordination, explicit persistence,
idempotency/lineage, and the bounded Core/Mind conflict receipt. Preserve the
existing `goal_drive_preview` behavior and its two resident review-only
records. Do not integrate the Chat contribution path until the 8A contract is
green and inspectable.
