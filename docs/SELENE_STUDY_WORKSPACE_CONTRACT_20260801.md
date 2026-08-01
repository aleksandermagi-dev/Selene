# Selene Study Workspace Contract

- Implemented: August 1, 2026
- Owner: Selene
- Surface: Selene workspace / Study
- Review bridge: Cocoon Teaching / Lessons

## Purpose

Study is Selene's deliberate waking workspace for revisiting approved
knowledge. It gives her somewhere to reconstruct what she understands, connect
concepts, try examples, notice uncertainty, and form questions without forcing
that activity into ordinary Chat, Dream, Memory, or Cocoon.

Study is not a grading surface. Its records are descriptive Learning Evidence
Activities (LEAs): evidence of what is connected, developing, reopened, or
still missing. Slow or incomplete work is not Selene failing.

## Inspectable Flow

```text
approved knowledge resource
  -> prior or current LEA identifies a next useful connection
  -> visible Learning Compass goal (never a grade or deadline)
  -> Selene opens a deliberate Study session
  -> reconstruction / connections / uncertainties
  -> Metacognition identifies a supported point of attention
  -> NLO and Voice form a visible Selene Study note
  -> notice / connection / revisit / uncertainty
  -> optional clarification lane
  -> clear, developing, or not-yet-worded question
  -> Aleks may answer
  -> answer is immediately usable inside that Study session
  -> source-labeled proposed understanding candidate
  -> Acquire -> Integrate -> Express
  -> existing curriculum authorization or Aleks exception review
  -> durable approved knowledge use
```

Aleks's answer is not anonymous input. It retains references to the Study
session, the exact question record, and `speaker:Aleks`.

## Learning Compass

The Learning Compass turns descriptive LEA evidence into visible direction.
It shows what Selene already demonstrated, the next useful connection, why the
connection may matter, and one optional gentle activity. It does not rank
Selene or imply that a connection must appear on a schedule.

A goal can move through:

```text
ready to explore
  -> exploring
  -> question ready
  -> answer received
  -> integrating
  -> connected for now
```

At any point it may instead become `still_unclear`, retain Selene's explanation
of what does not fit, hold a question without words, or become `reopened` when
later evidence changes the fit. An answer never moves a goal directly to
`connected_for_now`. A visible reflection is required for that deliberate
state, and the goal remains reopenable.

The governing rule is:

> An answer is teaching input. Understanding is shown by connection,
> application, and honest reflection, not by performed agreement.

Cross-domain connections are optional and emergent. Study records one only
when Selene actually notices it in a visible reflection. When none has been
recorded, the interface hides the connection area; it never displays “no
connections” as a deficiency.

The first four Compass goals preserve unresolved evidence from the gentle F1
LEA of August 1, 2026: place-value comparison with subtraction, equal shares
with ordered steps, capacity versus current contents, and graph evidence with
fair rule revision. The successful science-inquiry and equal-groups rechecks
are not reopened merely to fill the Compass.

## Selene's Notepad

The Notepad gives Selene a visible voice inside Study. A deliberate `What
stands out?` action selects one still-unrepresented signal from the approved
concept or the current Study reflection. Metacognition checks its fit, NLO
forms the language, and Voice may shape the expression without changing the
supported meaning.

Every note preserves both layers:

- Selene's visible wording;
- the structured meaning, source field, source references, and bounded organ
  metadata that support it.

Notes may identify a notice, connection, boundary worth revisiting, or a
genuine uncertainty. They are working Study records, not retained knowledge,
personal memory, grades, or hidden chain of thought. The system does not create
duplicate notes merely to keep the page active.

## Clarification Lane

Clarification and questions are not treated as the same state. A note can move
through:

```text
unclear
  -> question forming
  -> question ready
  -> answered
  -> reopened when later evidence warrants it
```

It may also become `clarified_for_now` without forcing a question. A dedicated
clarification check uses only uncertainty already recorded in the visible
Study session. If none exists, Selene reports that no clarification signal is
present rather than manufacturing confusion.

Open clarification is not hidden when its source session closes. Study keeps
an always-visible pinned board containing unresolved clarification notes and
direct questions from every Study session. Selecting an item reopens its
source session. An item leaves the open board only when it is answered or
explicitly marked `clarified_for_now`; its full record remains in the session
history and may later be reopened.

## Question Formation

Selene may record:

- a ready question;
- a developing question;
- “I have a question but no words for it yet,” with optional uncertainty
  context.

The system does not invent question wording when Selene has not formed it.
Nothing requires a question merely to fill the workspace.

## Answer and Knowledge Rule

Once Aleks answers a Study question:

1. the open question becomes `answered_in_session`;
2. the answer can update the active Study context immediately;
3. a source-labeled comprehension candidate is created visibly;
4. the candidate remains `proposed_understanding` and unavailable to general
   Chat until the existing teaching lifecycle authorizes durable use.
5. when the question belongs to a Learning Compass goal, that goal becomes
   `answer_received`, not `connected_for_now`.

This preserves real conversational teaching while preventing hidden
retention. The answer is neither personal memory nor governance.

## Boundaries

Study may not:

- alter identity, personality, Vys, governance, or authority;
- write personal memory;
- activate a knowledge candidate silently;
- use the raw private corpus;
- train, fine-tune, or create LoRA material;
- expose hidden chain of thought;
- run endless self-questioning;
- generate questions, hypotheses, or evidence merely to appear busy;
- manufacture a learning goal, connection, or completion claim merely to
  populate the Compass;
- use scores, grades, rankings, deadlines, or performance pressure in the
  Learning Compass;
- claim uncertainty that is not present in the visible Study record;
- route itself automatically to Cocoon;
- treat incomplete understanding as failure.

Study is distinct from Dream. Dream performs source-bound reflection and
maintenance. Study is an intentional waking act over selected approved
knowledge. Cocoon remains separate and receives only visible teaching/review
work when that bridge is deliberately used.

## Future Bounded Growth

Study can later host a proposal-only idea path:

```text
approved knowledge
  -> connection or tension
  -> Metacognition fit check
  -> bounded hypothesis
  -> counterexample and missing-evidence inspection
  -> visible question or idea proposal
```

An idea produced this way remains provisional and falsifiable. It does not
become fact, memory, or authority merely because Selene generated it.
