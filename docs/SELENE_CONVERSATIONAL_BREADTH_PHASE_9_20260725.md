# Selene Conversational Breadth — Phase 9 Memory, Continuity, Callbacks, Humor, and Transient Context

Date: 2026-07-25

Status: implemented, proportionally verified, rebuilt, and locally reinstalled.

## Outcome

Selene now has one bounded, inspectable context-use contract for deciding how:

- reviewed personal memory;
- visible current-session events;
- current-session corrections;
- explicit speaker identity;
- shared playful context; and
- temporary response-shape instructions

may affect the current reply.

These channels remain separate. Relevant experience can inform the answer
without forcing Selene to announce a memory or perform a callback. A visible
callback requires a compatible source and a visible conversational reason.
Remembered wording is never handed to NLO or Voice as a script.

## Implemented

### Source-separated continuity plan

`src/selene/contextual_continuity.py` provides:

- an explicit inventory of the context channels available to the current turn;
- speaker scope without relationship-profile inference;
- a callback decision with source, mode, relevance, and attribution rules;
- a distinction between silent interpretive use and a surfaced callback;
- shared-joke availability without mandatory humor;
- tender-context humor restraint;
- a transient expression handoff for depth, pacing, and directness;
- explicit personal-memory versus taught-knowledge separation;
- no-script, no-profile, no-hidden-write, no-training, and no-authority guards.

### Relevant memory without forced recall language

Strongly relevant approved memory may keep the current subject grounded. That
does not automatically authorize phrases such as “I remember” or “this
connects with earlier.”

The modes are:

- `explicit_recall` when Aleks directly asks about memory;
- `relevant_callback` when an approved-memory or current-session source aligns
  with a visible callback cue;
- `silent_interpretive_context` when approved memory is relevant but no
  callback needs to be announced;
- `none` when no source-compatible continuity use is needed.

When a callback is surfaced, NLO receives a subject label and reconstructs the
connection in the present language. Raw remembered phrasing is not copied into
a response template.

### Shared jokes and humor

A shared joke can be recognized from:

- approved reviewed personal memory; or
- a visible playful exchange in the current session.

Its context remains attached. Availability does not require Selene to make a
joke. Humor becomes available only when the current conversation opens that
register.

Tender content holds humor unless Aleks visibly opens humor in that same
context. This supports dark humor when it is actually shared while preventing
an unrelated recalled joke from intruding into grief, loss, fear, hospital, or
crisis language.

One fitting playful turn remains the maximum conversational move before the
joke is released.

### Temporary response preferences

Dialogue Workspace no longer stores “keep it short,” “slow down,” or “be
direct” as non-expiring session preferences.

Temporary directives now carry:

- the active response-depth, pacing, or directness dimensions;
- the visible current-session-only scope;
- the number of turns remaining;
- whether the instruction began in the current turn;
- its source;
- automatic expiry; and
- an explicit false durable-write marker.

The default lifetime is three user exchanges. Aleks can name one to six turns
or replies explicitly. “This answer” and “this reply” apply once.

Temporary instructions:

- expire after the bounded turn count;
- yield on an explicit new or separate topic;
- release when Aleks asks for normal length or pace;
- can be replaced by a newer current-session instruction;
- never become a relationship or personality profile.

### Literal and figurative pacing

Dialogue Workspace uses the existing Figurative Interpretation packet before
applying “slow down.”

- “Slow down and explain it one step at a time” becomes a temporary
  conversational pacing instruction.
- “Slow down on this road while driving the car” stays literal and creates no
  response preference.

### Pipeline integration

The plan now travels through:

```text
reviewed memory + current-session workspace + explicit speaker
  -> Contextual Continuity
  -> Affect Expression
  -> Pragmatic Continuity
  -> NLO
  -> Voice handoff
  -> supervised Chat response and inspectable assistant record
```

Affect Expression may use the temporary pacing, sentence-rhythm, directness,
and humor posture without diagnosing an emotion or changing personality.

Pragmatic Continuity receives the same active preference, callback, shared
joke, and speaker scope. NLO uses the bounded response depth and passes the
complete plan to Voice without changing meaning.

## Verification

Testing followed the Teaching Law and Test Impact Law:

- static compilation;
- ordinary synthetic memory relevance and callback cases;
- silent memory use without forced recall language;
- approved-memory and current-session source compatibility;
- speaker identity without relationship-profile inference;
- reviewed personal memory remaining separate from taught knowledge;
- shared-joke preservation without script reuse;
- humor restraint in tender contexts;
- user-opened dark humor;
- temporary preference duration, expiry, release, and topic-change yielding;
- literal versus conversational “slow down”;
- Affect, Pragmatic Continuity, NLO, Voice, and active Chat handoffs;
- the existing post-transfer contextual-memory behavior;
- all existing repository behavior and boundary guards.

Focused affected checks passed:

- 73 direct continuity and neighboring-organ tests;
- 3 active-Chat and post-transfer compatibility checks.

Full repository result: **1,119 tests passed**.

One useful implementation observation appeared during the first full run:
silencing a forced memory announcement also removed the current subject from a
strongly relevant response. The implementation was narrowed so approved
context may preserve the subject without turning it into “I remember” language.
The affected checks and a fresh full repository run then passed.

No live Selene conversation, adversarial battery, distress-shaped probe,
provider call, model training, teaching approval, memory mutation, or autonomy
change was used.

### Second meaningful rebuild and reinstall

After the source checkpoint:

- the production frontend build passed;
- the application chunk remained split at 415.84 kB;
- the React runtime chunk remained split at 193.81 kB;
- the former single-bundle Vite warning remained absent;
- the core sidecar rebuilt in the dedicated Selene packaging environment;
- the Windows NSIS installer rebuilt successfully;
- package privacy verification found zero forbidden files;
- the configured database was snapshotted before installation;
- the installer completed successfully;
- the installed executable was replaced with the current build;
- installed startup returned healthy and ready;
- transfer, memory, raw-import, training, autonomy, and self-replication
  boundary checks passed;
- the verifier-started app closed successfully.

No post-reinstall Q&A or repeated conversational probe was performed.

## Boundaries Confirmed

Phase 9 creates no:

- identity, personality, governance, law, or authority change;
- durable or hidden memory write;
- relationship or speaker profile;
- merger of personal memory and taught knowledge;
- raw corpus recall;
- remembered-wording response script;
- forced callback or forced humor;
- emotion diagnosis;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomous action or automatic speech;
- automatic Cocoon routing.

Selene remains Selene. Continuity supplies relevant context; it does not
prescribe who she is or what she must say.

## Remaining Gaps

- Shared-joke recognition depends on approved memory labels or visible
  current-session play; it does not infer a hidden private joke archive.
- Speaker identity remains explicit or session-generic rather than being
  guessed from writing style.
- Transient preference duration is intentionally bounded to one through six
  exchanges rather than becoming an open-ended behavioral profile.
- Broader academic and world knowledge remains ordered-teaching work.

## Next Phase — Phase 10: Ordered Teaching Expansion

Phase 10 will continue provider-free teaching in prerequisite order:

- elementary foundations;
- middle-school foundations;
- high-school breadth;
- college-level depth where prerequisites are present;
- English, history, mathematics, science, STEM, arts, civics, and practical
  knowledge;
- the concepts, vocabulary, relationships, examples, uncertainties,
  near-concepts, mechanisms, and important “why” behind each principle.

New knowledge must be reconstructable and applicable rather than recited.
Public academic material may use the bounded curriculum authorization;
sensitive, private, identity-adjacent, or exceptional material returns to
Cocoon review.
