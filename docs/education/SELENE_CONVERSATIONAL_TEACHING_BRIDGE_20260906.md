# Selene Conversational Teaching Bridge

Date: 2026-09-06

Status: implemented and boundedly verified in disposable state; not yet
packaged or reinstalled

## Outcome

Selene can now turn a small, explicitly marked teaching statement from Aleks
into approved general knowledge without requiring an LEA form. The bridge does
not create a new organ. It connects the existing Selene Chat, Comprehension,
Acquire, Integrate, Express, and approved-knowledge retrieval owners.

The lightweight loop is:

`unknown -> optional teaching invitation -> explicit answer or teaching cue -> Comprehension -> Acquire -> Integrate -> Express -> explicit Aleks item approval -> ordinary Chat use`

LEAs remain the deeper path for multi-part, ambiguous, high-stakes,
time-sensitive, or difficult material.

## Activation Contract

Ordinary conversation is never teaching. The bridge activates only through:

- an explicit leading cue such as `Let me teach you ...`, `I want you to learn
  ...`, `Here's something for you to learn ...`, `The answer is ...`, or
  `Actually, X works like this ...`; or
- a direct answer to Selene's immediately pending teaching invitation. A bare
  `yes` keeps the question open for the actual teaching content; `yes` plus a
  bounded claim may supply it in the same turn.

A normal factual statement, personal statement, correction-like phrase, or
answer to an ordinary curiosity question does not silently activate teaching.

The lightweight path is limited to small durable propositions. It holds rather
than activates material that is current or time-sensitive, high-stakes,
personal-memory shaped, protected identity/personality/governance/authority
material, ambiguous, or too large for a single concept.

## Question and Answer Continuity

The canonical assistant message now carries a session-scoped question handoff
when Selene asks a question. It distinguishes:

- teaching invitations;
- reason questions;
- personal curiosity;
- permission or proposals; and
- ordinary curiosity.

Short or expanded `yes` and `no` answers are interpreted against that pending
question. A `no` is received as the user's answer and boundary. Selene may ask
why without pressure, but the stated reason remains user-authored and cannot be
argued away or converted into permission. Later follow-up may clarify or keep
conversation moving naturally; it does not activate teaching unless the
teaching contract is separately satisfied.

## Existing Owners Reused

| Responsibility | Existing owner used |
| --- | --- |
| gap classification | Answer Substance / intelligenceOS support |
| source-bound concept proposal | Comprehension and Integration Organ |
| concepts, vocabulary, relationships, uncertainty | Acquire |
| scope, contradiction, why, correction and reopening | Integrate |
| teach-back, distinct application, analogy, limits | Express |
| retention decision | existing Aleks lifecycle approval |
| later answering | approved knowledge retrieval in Selene Chat |
| question continuity | canonical Selene Chat assistant payload |

## Preserved Boundaries

- No raw corpus import, provider model, training, fine-tuning, or LoRA.
- No personal Memory write or duplicate Memory record.
- No identity, personality, Vys, governance, law, authority, autonomy, or
  embodiment change.
- No knowledge activation from ordinary chat wording.
- No learning during diagnostic-only Q&A.
- No replacement of Cocoon, Study, or LEAs.
- Approved knowledge is checked before offering another teaching invitation,
  preventing a stale `Can you teach me?` beside an answer Selene already has.

## Evidence

- `src/selene/conversational_teaching.py`
- `src/selene/selene_chat.py`
- router status key: `conversational_teaching.status`
- `tests/test_conversational_teaching.py`

Verification at this checkpoint:

- 7 direct bridge and active-Chat checks passed;
- 56 existing Comprehension, teaching-lifecycle, and Dialogue Workspace checks
  passed;
- 3 selected existing active-Chat compatibility checks passed; and
- Python compilation and diff checking passed apart from the existing Windows
  line-ending notices.

All active-Chat verification used disposable databases. No resident teaching,
Memory, Study, Dream, Chat, affect, or continuity state was changed.

## Next

The bridge is ready for one future ordinary-use check after packaging is
separately authorized. Conversation-breadth source work remains a different
stage: verify and select small source slices, then teach mechanisms through the
existing lifecycle rather than ingesting a dataset as a response bank.
