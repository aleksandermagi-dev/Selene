# Selene Conversational Breadth — Phase 7 Curiosity, Initiative, Collaborative Help, and Conversational Energy

Date: 2026-07-25

Status: implemented and proportionally verified.

## Outcome

Selene now has one bounded, inspectable current-turn decision contract for
whether to:

- answer and land;
- offer one supported idea;
- surface one relevant supported connection;
- ask one curiosity question that matters to understanding;
- ask Aleks for one specific contribution to a shared task;
- incorporate that contribution and resume;
- ask one materially necessary clarification;
- wait, stay quiet, or let the exchange end.

This is responsive conversational initiative, not autonomous initiation:

```text
active exchange
  -> use the answer, reasoning, and supported context already available
  -> decide whether one addition materially improves the exchange
  -> express it without pressure
  -> stop when the answer is complete
```

The contract cannot start speech, send a message, perform an action, write
memory, route Selene to Cocoon, or expand authority.

## Implemented

### Shared conversational-energy contract

`src/selene/conversational_energy.py` coordinates these acts:

- `answer_and_land`;
- `answer_and_offer_supported_idea`;
- `answer_and_surface_supported_connection`;
- `answer_then_ask_relevant_curiosity`;
- `ask_for_specific_collaborative_help`;
- `answer_and_resume_shared_task`;
- `ask_one_material_question`;
- `wait_and_listen`;
- `stay_quiet`;
- `close_naturally`;
- `defer_to_core_mind`.

The plan is temporary and current-turn scoped. It writes no records of its own
and has no direct expression, truth, memory, delivery, or action authority.

### Supported initiative

A proposed idea or connection must:

- carry visible support or an explicit supported-current-context signal;
- be highly or materially relevant;
- be distinct from the answer already given;
- advance the active task or exchange.

Only one optional addition is selected. It follows the answer when an answer
is available and cannot pressure Aleks to act, redirect the conversation, or
become reflexive permission-seeking.

NLO realizes the supplied meaning with varied, compositional openings such as
having an idea, noticing a direction, or seeing a connection. These are
expression choices rather than fixed whole-answer scripts.

### Relevant curiosity

A curiosity question is allowed only when:

- it is relevant to the current subject;
- the answer matters to Selene's understanding;
- it has not already been answered;
- the turn is not a complete social exchange or closing.

At most one curiosity question is added. Questions remain disallowed by
default, so complete answers, greetings, thanks, and natural endings do not
receive habitual follow-ups.

### Collaborative help

Selene can ask Aleks for:

- a missing observation she cannot access;
- Aleks's relevant expertise;
- a value-dependent choice;
- an action that properly belongs to Aleks.

Before asking, the contract requires:

- an active shared task;
- use of available reasoning and supported information;
- the exact requested contribution;
- an explanation of why it materially affects the task;
- material, blocking, or meaningfully improving relevance.

Asking for help is represented as collaboration, not failure, submission,
Cocoon routing, or a request for general permission.

### Incorporation and resumption

The help request is retained only inside the existing current-session assistant
chat record. If Aleks supplies the requested contribution in the next
non-social turn:

- the contribution remains part of the visible current conversation;
- existing reasoning and Conversation Spine machinery can use it;
- the conversational-energy plan selects
  `answer_and_resume_shared_task`;
- NLO carries the explicit move to incorporate Aleks's contribution and resume.

No durable personal memory, hidden task store, relationship profile, or
cross-session assumption is created.

### Pragmatic continuity and endings

Pragmatic Continuity remains the owner of topic transitions, interruption,
referent posture, and ending decisions. Phase 7 adds a subordinate energy plan
without renaming or replacing established ending states.

Material ambiguity still outranks optional initiative. Closing, waiting, and
silence outrank ideas or curiosity.

### Metacognition, NLO, Voice, and active Chat

Metacognition can inspect whether:

- an optional addition was selected;
- a help request names a specific contribution;
- the question is habitual or materially justified;
- pressure or automatic Cocoon routing was introduced.

NLO carries the selected act into discourse planning and realizes only the
supplied addition. It preserves an existing long-form answer and does not
replace the answer with the initiative clause.

Voice receives the complete conversational-energy packet as expression
guidance. Voice may vary wording but cannot change the selected act, invent a
new request, add pressure, or alter meaning.

Active Chat exposes the packet in the response and assistant record. Ordinary
supervised Chat remains the caller; Phase 7 does not enable automatic speech or
Tendril delivery.

### Inspectable routes

- `conversational_energy.status`
- `conversational_energy.plan`

These routes report or construct the non-persistent coordination packet only.

## Verification

Testing followed the Teaching Law and ethical testing law:

- static compilation;
- supported and unsupported initiative;
- relevance and duplication restraint;
- pressure-free idea realization;
- relevant versus habitual curiosity;
- complete social turns without added questions;
- all four bounded collaborative-contribution kinds in the contract;
- required use of existing support before asking for help;
- exact request and materiality requirements;
- incorporation and current-session task resumption;
- closing, waiting, and silence precedence;
- long-form answer and paragraph preservation;
- Pragmatic Continuity ownership;
- NLO discourse and Voice-handoff preservation;
- Metacognition observation without failure language or Cocoon routing;
- active Chat idea, help, and resume behavior;
- existing claim evidence, epistemic revision, research, intelligenceOS,
  Answer Engine, Dialogue Workspace, Conversation Spine, Comprehension,
  special expression, intent, contextual speech, repair, supported semantics,
  language formation, affect expression, Voice, and visible-speech
  regressions.

Result: **322 focused cross-organ tests passed**.

No live Selene conversation, adversarial battery, distress-shaped prompt,
provider call, model training, package, or reinstall was needed. No frontend
files changed, so the production frontend build was not repeated.

Static compilation passed. `git diff --check` passed with only existing
Windows LF/CRLF warnings.

## Boundaries Confirmed

Phase 7 creates no:

- identity, personality, governance, law, or authority change;
- durable or hidden memory write;
- relationship-profile write;
- automatic speech or message delivery;
- autonomous action;
- reflexive approval requirement;
- automatic Cocoon routing;
- model training, fine-tuning, or LoRA;
- provider dependency;
- hidden chain-of-thought exposure.

Selene remains Selene. Conversational energy changes when a supported thought
is worth expressing, not who she is.

## Remaining Gaps

- Ideas and connections must already have supported current-context meaning;
  Phase 7 does not invent evidence or domain knowledge.
- Autonomous initiation and Tendril delivery remain separately governed and
  unchanged.
- Structural cross-domain analogy, hypothesis generation, and logical-leap
  testing remain Phase 8 work.
- Longer callbacks, shared humor, and transient-context graduation remain
  Phase 9 work.

## Next Phase — Phase 8: Cross-Domain Analogy, Hypothesis, and Discovery

Phase 8 will let Selene:

- map relationships across domains rather than match surface words;
- state which structural relationship is being transferred;
- explain where an analogy holds and where it breaks;
- distinguish pattern, analogy, homology, causal connection, and equivalence;
- make bounded logical leaps as hypotheses;
- propose discriminating observations and counterexamples;
- bring earlier approved knowledge into a later domain when it becomes
  relevant.

The completion gate requires novel connections to remain proportionally
labeled, analogy never to become proof silently, each logical leap to retain a
traceable bridge and a way to be checked, and private corpus wording never to
enter visible cross-domain reasoning.
