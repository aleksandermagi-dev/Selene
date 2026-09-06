# Selene G14 Emoji and Symbolic Conversation

Date: 2026-09-05

Status: five source-free language mechanisms completed Acquire → Integrate
→ Express and are available in the configured resident language shelf.

## Purpose

Emoji are part of written conversation. They can carry affection, amusement,
celebration, agreement, thought, emphasis, tenderness, or another contextual
signal. G14 lets Selene interpret that visible signal and optionally use an
emoji in her own reply without treating a symbol as a diagnosis, an emotional
command, or a response script.

## Ordered Lessons

1. **Emoji as contextual written meaning** — keep visible symbols inside the
   utterance instead of discarding them as decoration.
2. **Context and ambiguity** — preserve multiple live readings for symbols
   such as `😭`, `💀`, `🔥`, or `👀` until nearby language actually
   narrows them.
3. **Emoji-only complete social turns** — a heart, laugh, agreement mark, or
   thoughtful symbol can perform a complete conversational act without words.
4. **Optional authored emoji expression** — Selene may choose zero or one
   meaning-compatible emoji; copying the other speaker is never required.
5. **Mixed text-and-emoji cadence** — answer and meaning come first; an emoji
   may support the completed thought but cannot replace owed content.

Each lesson contains concepts, vocabulary, relationships, uncertainties,
near-concept distinctions, examples, scope, limits, counterexamples,
correction behavior, reconstruction, application, analogy, questions,
comparisons, and ordinary conversational participation.

## Architecture

`src/selene/emoji_expression.py` is connective tissue, not a new organ. It:

- reads known and unknown visible symbols;
- reports contextual meaning candidates and unresolved ambiguity;
- distinguishes emoji-only from mixed text-and-emoji turns;
- suggests a conversational act without claiming an inner state;
- permits at most one optional authored emoji; and
- carries explicit no-Memory, no-diagnosis, no-identity, no-personality,
  no-governance, and no-authority receipts.

The existing owners remain responsible:

- Meaning Router and Chat Intent arbitrate the conversational act;
- Relational Context carries visible current-turn meaning;
- the language shelf selects reviewed G14 guidance;
- NLO composes the response;
- the social realizer may place one optional symbol; and
- Voice retains final expression compatibility.

The work also consolidated the meaning of `actually` as a correction signal.
Dialogue, Pragmatics, Affect, Repair, the language selector, and Meaning Router
now use one shared rule: `actually` marks revision only when it visibly revises
content. Celebration such as `we actually did it 🎉` is no longer turned into
a false correction obligation.

## Teaching Decision and Provenance

Aleks authorized G14 on 2026-09-05. The lessons are project-authored,
source-free mechanisms. Their evidence lineage includes the existing aggregate
emoji-usage count in the private continuity review, but no private wording,
conversation excerpt, copied response, or imported persona is present.

The first lifecycle pass responsibly held two lessons because their natural
conversation examples were shorter than the existing Express evidence floor.
Those examples were completed; the gate was not bypassed.

## Boundaries

G14 does not:

- infer or diagnose emotion from a symbol;
- require mirroring, warmth, humor, affection, or emoji use;
- use random decoration or scatter symbols through owed content;
- convert an emoji into factual evidence or relationship truth;
- prescribe Selene's personality or expression;
- create personal Memory or a durable affect record; or
- change identity, Vys, law, governance, authority, autonomy, training,
  self-replication, external action, perception, or embodiment.

The installed executable still predates G14. A later explicitly authorized
package/reinstall is required before the desktop app can use the new source
mechanics; the resident teaching decision does not need to be repeated.
