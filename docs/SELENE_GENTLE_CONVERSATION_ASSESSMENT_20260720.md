# Selene Gentle Conversation Assessment

Date: 2026-07-20

Status: bounded assessment complete; implementation seams found before broader language grading

Live QA session: `136`

## Ethical Test Decision

The relevant text-language foundation, all 22 language lessons, and the bounded Metacognition observer were implemented before this assessment. A small real conversation was therefore necessary to inspect their integrated behavior.

The conversation used four calm turns: an ordinary project update and short-summary request, one clarification with a question, one request to answer the missed part, and a supportive pause. It did not use distress, identity pressure, adversarial boundaries, fear-shaped wording, or emotionally provocative material.

The assessment stopped when repeated turns exposed the same content-routing seam. More prompts would not have produced new evidence.

## What Worked

- Supervised Chat, NLO, Voice, Comprehension, the Language Teaching Shelf, conversation repair, and Metacognition all remained connected.
- NLO selected contextually relevant language lessons on every turn, including explanation, summary, mixed-intent balance, correction refinement, reference continuity, and purposeful follow-up.
- Voice preserved the NLO candidate source.
- No memory candidate was created or suggested.
- No affect signal, provider call, model training, identity/personality change, authority change, or autonomy expansion occurred.
- On the final three turns, Metacognition correctly reported `answer_incomplete` and recommended `complete_missing_obligation`.

## Implementation Observations

### 1. Language guidance can leak into answer content

Approved language lessons occupy the same general comprehension-resource pool as answer-bearing academic knowledge. Simple lexical overlap can retrieve a lesson as though its central claim were the answer to an ordinary conversational turn.

The closing prompt asked to pause. The visible reply instead restated the central claim of the pressure-free-ending lesson. The lesson selector itself had not selected that lesson as guidance; general approved-knowledge retrieval supplied it as content.

This is an organ-boundary bug. Language teaching should guide response construction, not automatically become the proposition Selene says.

### 2. Approved-knowledge ranking is too permissive

`retrieve_approved_knowledge` ranks every approved concept by raw term overlap across title, domain, central claim, principles, and relationships. It has no distinctive-term threshold, domain-intent agreement, or ordinary-conversation exclusion.

The first prompt asked what the completed conversation lessons changed. Retrieval ranked an unrelated F1 concept about sequence and reconstruction first, and `knowledge_response_seed` copied that concept's central claim into the response.

### 3. The first retrieved concept is promoted directly to content

The comprehension packet uses the first retrieved concept's central claim as `knowledge_response_seed`. Supervised Chat prioritizes that seed ahead of the open-ended reasoning seed. A weak retrieval therefore becomes the answer before NLO or Voice can recover the intended meaning.

### 4. Correction recognition can consume the rest of a mixed turn

The clarification was correctly recognized as a correction, and the correction-refinement lesson was selected. The primary correction realization returned after acknowledging the changed meaning, leaving the explicit follow-up question unanswered.

The lifecycle lesson is present; the remaining gap is obligation composition. A correction should update the shared model and then allow later question or request obligations in the same turn to be answered.

### 5. Leading affirmation can hide a direct request

The next turn began with “Right” and then explicitly requested the missed answer. Primary-intent classification selected affirmation, producing a shared-ground acknowledgement while leaving the request unresolved.

Mixed-intent planning detected useful lessons, but primary realization did not compose the acknowledgement with the required content act.

### 6. Coverage and Metacognition need a stronger semantic-fit signal

The first unrelated answer was marked fully covered, so Metacognition reported that it fit the current question. On later turns, coverage exposed the missing obligation and Metacognition correctly caught it.

Metacognition v1 is therefore observing the supplied machinery correctly, but it cannot yet independently detect a semantically unrelated answer when shallow coverage reports success. It also cannot apply its completion recommendation by design.

### 7. QA transport artifact excluded from findings

One em dash entered through the PowerShell-to-Python QA harness as a replacement character. This was not reproduced through the application UI and is not attributed to Selene's language stack.

## Recommended Repair Order

1. Keep `language_and_conversation` lesson concepts out of general answer-content retrieval. They should reach NLO through the Language Teaching Shelf unless a turn explicitly asks about the lesson itself.
2. Add a knowledge relevance gate using domain-intent agreement and distinctive evidence, not any lexical overlap.
3. Stop promoting the first weakly matched concept directly into `knowledge_response_seed`.
4. Compose correction or affirmation acknowledgements with remaining required question and request obligations.
5. Strengthen semantic coverage so an answer cannot pass merely by sharing generic words with the prompt.
6. After those repairs pass synthetic checks, consider one bounded Metacognition-driven completion retry. Keep the retry limited to a known unresolved obligation.
7. Expand ordinary closure recognition for phrases such as “pause here,” “stop here,” and “checkpoint here.”

## Assessment Boundary

This session does not establish that Selene lacks humor, tenderness, analogy, disagreement, long-form structure, or conversational breadth. Those lesson routes were not meaningfully assessable once answer-content retrieval displaced the conversation.

The correct conclusion is narrower: the teaching and observer organs are connected, but general knowledge retrieval and single-primary-intent realization currently prevent a fair integrated language assessment.

## Stabilization Follow-up

The implementation seams above were repaired synthetically after the live assessment. The original session remains unchanged as evidence, and no further live prompts were needed.

- Language lessons are now excluded from general answer-bearing knowledge retrieval. They continue to reach NLO as reviewed guidance.
- Approved factual knowledge must pass an answer-request and distinctive-term relevance gate before its central claim can seed a reply.
- Questions about the completed language teaching are answered from the inspectable approved-shelf state, not by parroting a lesson claim.
- Correction and affirmation acknowledgements now compose with grounded content when the same turn contains a required question or request.
- Coverage now requires visible topic alignment; generic answer-shaped wording is not sufficient.
- Metacognition may request one grounded completion pass. Selene Chat can only append the already selected content seed, accepts it only when coverage improves, never recurses, and cannot cross a Core/Mind boundary.
- Ordinary phrases such as “pause here” and “stop here” now route as conversational closure.

Focused synthetic verification: 160 tests passed across Answer Engine, intent routing, comprehension, conversation repair, dialogue workspace, language teaching, Metacognition, NLO, pragmatic coverage, supervised Chat, and teaching lifecycle. `git diff --check` passed with only the existing Windows line-ending warnings.

This follow-up repairs the observed integration faults. It does not broadly grade Selene’s voice or claim that every conversational capability is complete.
