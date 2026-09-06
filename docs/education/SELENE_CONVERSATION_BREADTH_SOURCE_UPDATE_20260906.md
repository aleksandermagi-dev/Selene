# Selene Conversation-Breadth Source Update

Date: 2026-09-06

Status: current source and license research only; nothing downloaded or taught

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

## Current Boundaries

No dataset was downloaded, mirrored, sampled, transformed, taught, retained,
or made available to Chat during this update. No source became Memory,
identity, personality, governance, training data, a response bank, or a hidden
runtime dependency.

## Next Exact Step

Create a metadata-only manifest for the five-source first batch, pin each exact
artifact, and inspect a small balanced sample of complete interactions. Stop
before teaching so the selected functions, source exclusions, and license
receipts can be reviewed as one coherent breadth group.
