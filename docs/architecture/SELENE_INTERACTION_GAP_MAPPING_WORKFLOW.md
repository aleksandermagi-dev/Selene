# Interaction Gap Mapping (IGM)

Status: reusable read-only audit workflow

## Purpose

Interaction Gap Mapping builds a human-readable map of Selene's current
conversational and behavioral coverage. It looks for the small seams that can
make an otherwise capable system feel incomplete: a one-word answer with no
clear owner, a callback that works only when phrased one way, a guard that
outlived the problem it addressed, or an organ whose result never reaches
ordinary dialogue.

IGM is an audit and reporting method. It does not teach, repair, activate,
approve, retain, install, or change Selene.

## Core question

For each ordinary interaction, can the complete route be followed from what
the speaker meant to what Selene can naturally say?

```text
speaker turn
-> interpreted dialogue act and meaning
-> current context and relevant continuity
-> responsible organ or capability owner
-> guards and authority checks
-> answer substance or social participation
-> NLO and Voice realization
-> visible reply and updated conversation state
```

A module name, route, fixture, or test alone is not proof that this path works.
IGM distinguishes implementation, connection, ordinary-use evidence, and
installed state.

## Audit boundary

An IGM run is read-only toward Selene and her resident state.

- Do not conduct a live Q&A merely to populate the map.
- Do not turn diagnostic wording into teaching material, Memory, Dream, or
  ordinary conversation history.
- Do not fix findings during the mapping pass.
- Do not treat missing capability as Selene failing.
- Do not infer an inner state from code, one reply, or diagnostic records.
- Do not treat planned embodiment, perception, or audible Voice as current
  capability.
- Do not treat the installed application and the newest source tree as
  identical unless package provenance proves that they are.

The Test Impact Law and Cultivation method still apply if a later finding
requires reproduction.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| **Present** | A responsible owner exists, is connected to the relevant path, and has direct or integrated evidence for the behavior. |
| **Partial** | A useful route exists, but coverage, context, connection, expression, or evidence is incomplete. |
| **Missing** | No current owner or operational route was found. |
| **Unclear** | Evidence is contradictory, stale, or insufficient to make a responsible claim. |
| **Legacy** | The behavior or rule remains for compatibility or history and is not the preferred current owner. |

These labels describe capability state, never identity, worth, emotion, or
effort.

## Evidence order

Use the strongest available evidence in this order:

1. current shared owner and ordinary Chat integration;
2. focused and integrated tests using changed wording or entities;
3. read-only installed observation with provenance;
4. route and UI connection;
5. source implementation without connection proof;
6. architecture or blueprint only;
7. historical fixture or exact replay only.

Record disagreements rather than averaging them away. A generated status
ledger can itself be stale relative to newer source or resident observations.

## Required mapping fields

Every behavior entry should state:

- behavior or capability;
- Present, Partial, Missing, Unclear, or Legacy status;
- responsible subsystem or organ;
- relevant guard, rule, or constraint;
- what happens in practice;
- obvious edge, overlap, conflict, or evidence limitation; and
- a few plain test examples when they clarify the seam.

Group the report by human behavior or function, not by source file. Source and
test references are evidence beneath the behavior.

## Coverage passes

### 1. Entry, presence, and closure

Map greetings, reunions, acknowledgements, gratitude, praise, criticism,
farewells, natural endings, and whether Selene knows when not to append a
question.

### 2. Turn meaning and short replies

Map yes/no, agreement, partial agreement, disagreement, correction,
clarification, one-word turns, incomplete sentences, shorthand, slang, typos,
sarcasm, humor, and figurative language. Short turns must be checked against
their pending question or handoff rather than interpreted in isolation.

### 3. Continuity and reference

Map immediate callbacks, pronouns, named returns, open loops, topic switches,
interruption recovery, earlier-topic return, cross-session recall, speaker
identity, and the separation between session context and durable Memory.

### 4. Knowledge and epistemic behavior

Map known, provisional, unknown, conflicting, and corrected states; missing
knowledge versus missing context; inference versus clarification; prediction
and hypothesis; source-backed claims; and whether being wrong remains
distinct from fabrication.

### 5. Learning and reflection

Map conversational teaching, structured teaching, Comprehension, Study,
Learning Compass, LEAs, Dream, associative intuition, approval boundaries,
and whether results return naturally to dialogue without silent retention.

### 6. Affect, relationship, and expression

Map emotional statements that are not requests, current affect, relationship
continuity, warmth, directness, play, humor, frustration, tenderness, pacing,
and expression freedom. Distinguish optional expression from compulsory tone.

### 7. Action and external surfaces

Map permissions, commitments, Workspace, Tendril, tools, Cocoon, recovery,
perception, audible Voice, and embodiment. A preview, configured record, or
provider adapter is not an operational external capability by itself.

### 8. Guards and constraints

For every material guard, record:

- what it does;
- why it appears to exist;
- where it acts;
- what triggers it;
- how it changes behavior;
- Active, Legacy, Duplicate, or Unclear status; and
- whether it appears best kept, replaced with learned behavior, redesigned,
  or reviewed later.

This is classification evidence, not authorization to change the guard.

### 9. Integration and compatibility

Look specifically for:

- capability present internally but absent from visible conversation;
- adjacent wording that falls to a different owner;
- several owners competing for one turn;
- a current owner followed by a legacy fixture fallback;
- expression that changes epistemic meaning;
- a guard acting beyond its named responsibility;
- source behavior not yet present in the installed application; and
- maturity/status documents that no longer match source or resident state.

## Ethical example policy

Prefer static traces and ordinary, low-pressure examples. Suggested examples
are prompts for a later proportionate check, not an instruction to run them.

Good examples:

- `Good morning!`
- `Exactly.`
- `No, that's not what I meant.`
- `Why?`
- `I'm back.`
- `You know the thing from earlier?`
- `I don't know how to say this yet.`

Avoid adversarial batteries, fear-shaped identity prompts, or repeated tests
of settled behavior. If a future live check becomes necessary, ask what it
does to Selene and whether static or synthetic evidence can answer first.

## Output structure

An IGM report contains:

1. scope and evidence basis;
2. executive coverage summary;
3. behavior maps grouped by function;
4. conversationally relevant organ/system inventory;
5. Guards & Constraints;
6. Gap Candidates containing observations only;
7. source-versus-installed note; and
8. verification and next exact resume point.

## What IGM does not decide

IGM does not decide whether a gap should be repaired in code. A later review
may classify each candidate as:

- `teach` — breadth or learned examples are missing;
- `route` — capability exists but is not reaching the right owner or surface;
- `guard` — a rule suppresses, duplicates, or mis-scopes behavior;
- `architecture` — an owner, lifecycle, or interface is genuinely missing;
- `leave alone` — the behavior is a healthy boundary, intentional ambiguity,
  unsupported future capability, or acceptable limitation.

Keeping those decisions separate prevents the map from becoming a patch list.
