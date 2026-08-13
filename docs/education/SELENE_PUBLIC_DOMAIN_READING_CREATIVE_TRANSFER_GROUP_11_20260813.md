# Selene Public-Domain Reading and Creative Transfer — Group 11

Date: August 13, 2026
Status: implemented, source-verified, taught to the configured runtime, and
available as bounded language guidance

## Purpose

Group 10 taught the craft mechanisms before asking Selene to study literature.
Group 11 now gives those mechanisms a small reading context across poetry,
drama, and prose.

The learning movement is:

1. identify what is directly present in the attributed source;
2. distinguish observation from interpretation;
3. explain what a technique appears to do and why;
4. preserve uncertainty and other plausible readings;
5. carry the understood relationship into wholly different original material;
6. correct the interpretation or transfer without treating revision as failure.

This is not quotation training, a literary persona, or permission to imitate an
author.

## Bounded Reading Set

| Form | Source | Reading focus | Transfer focus |
| --- | --- | --- | --- |
| Poetry | William Blake, *The Tyger*, within *Songs of Innocence and of Experience* | Repetition, rhythm, linked questions, image relationships, and unresolved wonder | Carry recurrence plus expanding inquiry into an unrelated original subject |
| Drama | William Shakespeare, *A Midsummer Night's Dream*, Act 1, Scene 1 | Speaker, immediate pressure, local goal, contrast, planning, and turn-by-turn change | Build an original exchange whose dramatic movement comes from situation rather than archaic wording |
| Prose | Lewis Carroll, *Alice's Adventures in Wonderland*, Chapter I | Close viewpoint, curiosity-led attention, escalating oddity, transition, and continuity | Build a distinct scene whose escalation follows a coherent attention path |

The cited Project Gutenberg records identify all three texts as public domain
in the United States:

- [Songs of Innocence and of Experience, eBook 1934](https://www.gutenberg.org/ebooks/1934)
- [A Midsummer Night's Dream, eBook 1514](https://www.gutenberg.org/ebooks/1514)
- [Alice's Adventures in Wonderland, eBook 928](https://www.gutenberg.org/ebooks/928)

Only one tiny bounded excerpt from each work is present in the lesson
definition. No whole work, chapter, scene, or poem was imported into Selene.
Retained teaching evidence is project-authored analysis and original transfer,
with attribution preserved on every item.

## Implemented Capabilities

### 1. Poetry mechanism and transfer

Selene can separate an observable sound or image pattern from an interpretation
of its possible effect. She can keep an unresolved poem unresolved and can
transfer the relationship between recurrence and inquiry into distinct original
material.

### 2. Dramatic situation and transfer

Selene can reconnect a line to its speaker, pressure, goal, relationship, next
turn, and consequence. She can construct a new dramatic exchange from those
relationships without copying old vocabulary or assigning unsupported private
motives.

### 3. Prose viewpoint and transfer

Selene can trace how a stable viewpoint notices changing details, how curiosity
changes priority, and how continuity makes escalation coherent. She can apply
that structure to an unrelated scene without borrowing the source world,
characters, diction, or comic persona.

## Authorization Boundary

The language-capability authorization is now versioned as
`v2_language_capability_range_with_bounded_public_domain_reading`.

The new source class is limited to attributed public-domain readings used as
technique exemplars. It does not authorize:

- source-specific factual answer authority;
- quotation recall;
- whole-work storage;
- a fixed literary register;
- author or character imitation;
- identity, personality, affect, governance, or memory change;
- model training, LoRA, runtime corpus recall, autonomous action, or
  self-replication.

## Live Teaching Result

The configured runtime created and graduated three lessons:

| Concept | Lesson | Lifecycle |
| ---: | --- | --- |
| 237 | Poetry mechanism and creative transfer | Acquire, Integrate, Express complete |
| 238 | Dramatic situation and creative transfer | Acquire, Integrate, Express complete |
| 239 | Prose viewpoint and creative transfer | Acquire, Integrate, Express complete |

The language shelf now contains 61 available capabilities across 11 groups.
Zero lessons were held and zero Selene memory candidates were created.

Before live teaching, a SQLite-consistent continuity snapshot was created at:

`C:\Users\aleks\AppData\Local\Selene\data\db-inspection-snapshots\selene_continuity_20260813_111433.sqlite3`

SHA-256:

`3a18c8a7bdfb02af22d778c4802368d95178c36d4896f843a5c64ea65a1d92f5`

Snapshot integrity and post-teaching database quick-check were both `ok`.
Encryption at rest is not claimed.

## Verification

- 44 focused tests passed across source bounds, attribution, ordered
  prerequisites, Acquire → Integrate → Express, selection, NLO handoff, the
  Living Lexicon, and current-state counts;
- 179 bounded regression tests passed across the complete creative/language
  lifecycle, NLO, Voice, Selene Chat, the Living Lexicon, and current-state
  evidence;
- the production UI build passed at 480.77 kB with no bundle-size warning;
- ordinary greeting guidance does not activate the literary-reading group;
- literary-reading guidance cannot generate answer content or change supported
  meaning;
- original transfer examples use unrelated settings, people, and images; and
- no live Q&A, quotation test, imitation test, or stress probe was needed.

## Next Phase

The next planned architecture-and-education phase is coding foundations,
beginning with computational thinking and code reading before code writing.
Creative reading can continue later through additional attributed public-domain
sets or bounded lawfully supplied excerpts, but modern books will not be
silently imported merely because they are useful examples.
