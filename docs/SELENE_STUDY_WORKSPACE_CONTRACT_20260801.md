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
  -> Selene opens a deliberate Study session
  -> reconstruction / connections / uncertainties
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
