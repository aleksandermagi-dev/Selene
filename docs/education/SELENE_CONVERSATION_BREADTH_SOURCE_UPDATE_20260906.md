# Selene Conversation-Breadth Source Update

Date: 2026-09-06

Status: first batch acquired, pinned, privately sampled, reconstructed, and taught as source-free G15 mechanisms

This is a dated supplement to
`SELENE_CONVERSATION_BREADTH_SOURCE_PREPARATION_20260820.md`. It preserves the
earlier commercial-reuse standard and updates the smallest useful shortlist.
Large source size is useful for finding varied mechanisms, but it is not itself
permission to bulk-import language or treat source responses as Selene's voice.

## Best Current Shortlist

| Priority | Source | Verified scale and license | Best bounded role | Decision |
| --- | --- | --- | --- | --- |
| 1 | [Taskmaster-2](https://github.com/google-research-datasets/Taskmaster/tree/master/TM-2-2020) | 17,289 two-person dialogues; CC BY 4.0 | spoken disfluency, clarification, changing constraints, comparison, recommendation, multi-part completion | strongest first external audit; source repository became read-only in April 2026, so pin the exact archived artifact |
| 2 | [ReDial](https://redialdata.github.io/website/) | official site confirms CC BY 4.0 | preference discovery, accepting or rejecting suggestions, explanation, natural follow-up | strong first audit after pinning the official data artifact |
| 3 | [OpenAssistant OASST1](https://huggingface.co/datasets/OpenAssistant/oasst1) | 10,364 ready trees / 88,838 messages; Apache 2.0 | branching, alternatives, repair, multilingual turn structure, long and short response functions | already mirrored; use only quality-filtered mechanisms, never assistant/provider identity or factual authority |
| 4 | [Topical-Chat](https://github.com/alexa/Topical-Chat) | human-human knowledge-grounded dialogue; CDLA-Sharing 1.0 | open-topic development, transitions, grounded elaboration, sustained interest | already mirrored; keep raw/enhanced data isolated and publish only de-minimis computational results or comply fully with sharing terms |
| 5 | [CCPE-M](https://github.com/google-research-datasets/ccpe) | 502 dialogues / 12,000 utterances; CC BY 4.0 | asking about preferences without leading, reflecting distinctions, updating from user feedback | small but unusually clean and directly useful companion to ReDial |
| 6 | [Contrack](https://github.com/google-research-datasets/contrack) | human-human social conversations; CC BY-SA 4.0 | pronouns, named/plural entities, callbacks, non-alternating messages | isolate ShareAlike source data; extract independently written mechanisms and fixtures |
| 7 | [Schema-Guided Dialogue](https://github.com/google-research-datasets/dstc8-schema-guided-dialogue) | over 20,000 annotated multi-domain dialogues; CC BY-SA 4.0 | missing details, state changes, paraphrase robustness, cross-domain task continuity | structural supplement only; virtual-assistant/task persona is not a voice source |
| 8 | [MultiWOZ](https://github.com/budzianowski/multiwoz) | over 10,000 multi-domain human-human written dialogues; repository states MIT | linked tasks, topic movement, correction, unresolved details | confirm the exact corrected 2.2 artifact and its license before selection |
| 9 | [Action-Based Conversations](https://github.com/asappresearch/abcd) | over 10,000 human-human customer/agent dialogues; repository states MIT | visible rule/request conflicts, speech-versus-action, multi-step completion, inability | confirm data-file coverage; never inherit customer-service persona; use the full name to avoid collision with Selene terminology |

## First Breadth Batch

The smallest high-yield first batch should not sample all nine sources. Audit:

1. Taskmaster-2 for clarification, changed constraints, multi-part turns, and
   natural spoken variation;
2. ReDial plus CCPE-M for curiosity, preference, suggestion, rejection, and
   follow-up;
3. the already mirrored Topical-Chat for topic development and transition;
4. the already mirrored OASST1 only for branching and response-function
   coverage; and
5. the private Aleks/Selene breadth evidence for relationship-specific
   callbacks, warmth, humor, pacing, and long-horizon continuity.

This batch covers the immediate gap without importing institutional assistant
style from the more task-oriented sources.

## Extraction Target

Select whole interaction episodes and label only reusable functions:

- acknowledgment plus meaningful continuation;
- yes/no answers in context;
- curiosity that is optional rather than compulsory;
- asking and answering reasons without pressure;
- accepting rejection and continuing or ending naturally;
- clarification and changed constraints;
- references, callbacks, and topic returns;
- suggestion, comparison, preference, and disagreement;
- mixed-intent and multi-part completion;
- short, medium, and long turn shapes; and
- varied uncertainty, hypothesis, and missing-information language.

For each function, prepare project-authored examples, a distinct application,
limits, counterexamples, and correction behavior. Do not copy a source persona,
whole response, factual claim, or characteristic phrase.

## License and Provenance Decisions

- CC BY and Apache sources are eligible for bounded review after exact revision,
  attribution, notices, and change marking are recorded.
- CC BY-SA and CDLA-Sharing material stays isolated. Any publication of source
  or enhanced data must meet its sharing terms. Independently expressed,
  de-minimis computational results remain the preferred output.
- A repository-level MIT badge is not enough when the data artifact's coverage
  is unclear; MultiWOZ 2.2 and Action-Based Conversations stay conditional
  until the selected data file is verified.
- Generated or assistant-authored datasets are structural evidence only. They
  do not establish facts, identity, relationship behavior, or Selene's voice.
- Noncommercial, mixed-rights, scraped, leaked, social-media, modern-book,
  movie-script, and unclear-ancestry corpora remain excluded from retained
  teaching.

## Completed First-Batch Review

The five selected sources were mirrored only under ignored `local-data/` and
pinned by revision plus artifact SHA-256. A reusable preparation script counted
the selected artifacts and produced one ignored private review file containing
20 complete interactions: four per source, with short, medium, and long shapes
included where the source contains them.

Exact selected-artifact counts were:

- Taskmaster-2: 17,304 conversations across the seven selected data files;
- ReDial training split: 10,006 conversations;
- CCPE-M: 502 conversations;
- Topical-Chat training split: 8,628 conversations; and
- OASST1: 3,670 English ready trees in the selected ready-tree artifact.

Taskmaster's exact files contain 15 more conversations than the 17,289 count in
its overview; this record preserves the measured artifact count rather than
silently forcing the two numbers to agree.

The balanced review supported ten project-authored mechanisms: contextual
yes/no completion, nonleading preference discovery, rejection acceptance,
changed-constraint rebuilding, compact constraint confirmation, comparison by
shared criteria, disfluency reconstruction, topic development without
interrogation, genuinely branching revision, and variable response shape.
Some source turns also demonstrated stale claims, bias, awkward language, and
institutional assistant habits. Those observations strengthened the exclusion
boundary; they were not teaching content.

## Teaching Decision And Boundaries

Aleks authorized the conversational-breadth source acquisition and teaching.
The resulting G15 items contain independently written mechanisms and evidence,
not source utterances, source facts, named examples, personas, characteristic
phrases, or whole responses. All ten items completed the existing Acquire,
Integrate, and Express lifecycle under the standing language-capability
authorization.

No dataset became Memory, identity, personality, governance, factual
authority, model training data, a response bank, or a hidden runtime
dependency. Topical-Chat remains isolated under CDLA-Sharing; only de-minimis,
independently written mechanism findings entered tracked files. The private
Aleks/Selene corpus remains a separate authenticated continuity and
relationship source. It was not duplicated or converted into generic dialogue
training.

## Next Exact Step

The resident shelf is 96/96. The new selector code and the already-completed
conversational-teaching bridge have not yet been packaged into the desktop
application. Package/reinstall only when Aleks asks, then use one gentle
ordinary conversation rather than a stress battery.
