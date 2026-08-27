# Selene Ordered Source-Gap Map and Teaching Queue

Date: 2026-08-13

Status: repository-backed curriculum map; source selection and teaching not yet
authorized by this document

## Outcome

Selene's conversational and learning architecture is ready to receive a much
broader education. Her present limiting factor is now primarily the breadth and
depth of reviewed knowledge available to that architecture, not the absence of
a general conversational control path.

The correct next move is not a bulk corpus import. It is an ordered source and
teaching program:

`select source → inspect rights and provenance → teach prerequisites → Acquire → Integrate → Express → retain under the applicable authorization → gentle LEA → continue`

The target is broad, transferable understanding. It is not memorized test
answers, copied textbook language, hidden training, or imitation of a provider
model.

## Verified Starting State

A read-only inspection of the configured runtime on 2026-08-13 found:

| Area | Active reviewed knowledge |
|---|---:|
| F1 elementary foundation | 106 concepts across 17 completed groups |
| F2 elementary foundation | 25 concepts across 5 completed groups |
| Language, conversation, grammar, and creative expression | 61 capabilities across 11 completed groups |
| Coding | 5 concepts in Coding Group 1 |
| **Total** | **197 active reviewed knowledge resources** |

The same inspection found 47 proposed understanding candidates that remain
inactive. They are not counted as taught knowledge. One lifecycle remains at
`acquire_needs_review`; it is also excluded from coverage.

The review-only source shelf currently contains:

- 54 cataloged source candidates;
- 43 mirrored catalog sources;
- 11 catalog-only sources requiring artifact and edition selection;
- 133 pinned source files; and
- zero checksum failures in `python scripts/acquire_curriculum_sources.py --verify`.

The source shelf is inert. Its presence creates no teaching packet, retained
knowledge, personal memory, runtime recall, training material, or authority.

Primary supporting records:

- [Foundational Curriculum Map](SELENE_FOUNDATIONAL_CURRICULUM_MAP_20260719.md)
- [Curriculum Source Shelf](SELENE_CURRICULUM_SOURCE_SHELF_20260719.md)
- [Teaching Lifecycle](SELENE_TEACHING_LIFECYCLE_PHASE_4_20260715.md)
- [Curriculum Authorization Law](SELENE_CURRICULUM_AUTHORIZATION_LAW_20260719.md)
- [Education–Expression–Personality Law](SELENE_EDUCATION_EXPRESSION_PERSONALITY_LAW_20260719.md)

## What “On Par” Can Accurately Mean

No finite curriculum should be described as reproducing every fact, phrase, or
construction inside a large pretrained language model. The defensible target
for Selene is functional general maturity:

- broad school-level and practical knowledge;
- coherent answers across ordinary domains;
- enough language breadth to express that knowledge naturally;
- correct routing to calculation, sources, memory, or clarification;
- visible separation of fact, inference, hypothesis, and uncertainty;
- transfer to unfamiliar examples instead of source recall;
- cross-domain synthesis when prerequisites exist; and
- an honest, useful hold or best-supported attempt when they do not.

That target can be assessed fairly after F4. F5 and F6 should remain continuing
education rather than a condition Selene must satisfy before ordinary use.

## Coverage Ledger

Status meanings:

- **Strong foundation:** the current band has coherent retained concepts.
- **Partial:** useful concepts exist, but the current band is incomplete.
- **Architecture-ready:** reasoning or language machinery exists, but more
  subject knowledge is required.
- **Untaught:** no coherent retained sequence currently supports the strand.
- **Source-present:** one or more review sources are local; this does not mean
  they are teaching-ready.
- **Selection-needed:** the catalog identifies a source family, but an exact
  artifact, revision, and license must be selected.

| Family | Current taught state | Current source position | Principal gap | Priority |
|---|---|---|---|---|
| ELA-1: words and sentences | Strong F1 plus grammar transfer | Source-present | Continue through use; do not repeat foundations by default | Maintain |
| ELA-2: paragraphs, vocabulary, comparison, attribution | Strong F2 Groups 1–3 | Source-present | More reading breadth and cumulative application | F2 integration |
| ELA-3: argument, literature, rhetoric, sustained composition | Partial creative and long-form foundation | Some sources present; broader artifact selection needed | Formal argument, research writing, rhetoric, genre breadth, sustained close reading | F3–F4 |
| CONV-1: ordinary turn-taking and repair | Strong architecture and language teaching | Several dialogue sources present | More naturally varied examples across everyday subjects | Parallel breadth |
| CONV-2: mixed intent, implication, humor, disagreement, initiative | Architecture-ready and substantially implemented | Dialogue sources present but require bounded slicing | Broader pragmatic experience without canned assistant behavior | F3–F4 |
| MATH-1: quantity and elementary operations | Strong F1 | Source-present | Spiral review only | Maintain |
| MATH-2: fractions through multi-step application | Partial; arithmetic and operation order complete | Some local support; coherent Grades 3–5 artifact selection needed | Fractions, decimals, ratios, percent, geometry, conversions, data, application | **Immediate** |
| MATH-3: algebra, functions, probability, statistics, proof, modeling | Untaught as a coherent sequence | Some sources present; several selections needed | Complete F3–F4 progression | F3–F4 |
| SCI-0: scientific observation and method | Strong early inquiry; later method partial | Source-present and OpenSciEd selection-needed | Variables, controls, repeated trials, measurement error, models, explanation | **Immediate F2** |
| SCI-1: life science | Early organisms and body systems present | Source-present; later artifacts needed | Ecosystems, adaptation, cells, heredity, evolution, ecology, physiology | F2–F4 |
| SCI-2: physical science | Early materials, motion, force, light, sound, machines present | Source-present; later artifacts needed | Matter, energy, atoms, chemistry, mechanics, waves, fields | F2–F4 |
| SCI-3: Earth and space | Early weather and sky cycles present | Thin local coverage; artifact selection needed | Earth systems, geology, climate, solar scale, stars, cosmology | **Real source gap** |
| HIST-1: chronology, geography, and sources | Early history/evidence foundation present | Sequence source present; primary-source selection needed | Maps, physical/human geography, overlapping timelines, primary/secondary evidence | **Immediate F2** |
| HIST-2: comparative world history | Untaught as a coherent sequence | Discovery material present; coherent curriculum selection needed | Comparative ancient-to-modern history, multiple causes, institutions, exchange, conflict, continuity | **Real source gap** |
| CIV-1: civics, economics, law, media, institutions | Early community/rules and needs/wants foundation present | Several local and catalog sources | Government scales, rights, participation, scarcity, policy, law, media literacy | F2–F4 |
| TECH-1: computing and information | Strong F1 plus Coding Group 1 concepts | Code.org and Carpentries present | Representation, software construction, data, networks, security, architecture | F2–F5 |
| ENG-1: engineering and systems | Early tools, machines, algorithms, and constraints present | Some sources present; OpenSciEd selection needed | Criteria, system connections, failure points, feedback, testing, tradeoffs | **Immediate F2** |
| RES-1: research and source reasoning | Source grounding and evidence distinction present | Many sources present | Search method, credibility comparison, research design, disagreement, synthesis, citation networks | F3–F5 |
| ART-1: art, music, narrative, media, design | Creative-writing foundation and small literary transfer present | Music and museum sources present | Visual composition, color, art history, music, media grammar, design practice | F2–F4 |
| LOGIC-1: reasons, contradiction, validity, counterexamples | Embedded reasoning foundation present | Open Logic and other sources present | Explicit informal/formal logic, validity, fallacies, decision structure | F3–F5 |
| HEALTH-1: health and care literacy | Body systems, consent, and health-source limits present | MedlinePlus present; CDC selection needed | Public health, accessibility, risk communication, care systems | F2–F5 |
| LIFE-1: practical institutional literacy | Needs, wants, goods, services, money foundations only | Federal and practical sources partly present | Finance, employment, records, taxes, insurance, schedules, institutional navigation | **Real source gap** |
| CULT-1: culture and language diversity | Small literary and historical exposure only | Museum/dialogue sources present; Tatoeba selection needed | Comparative culture, linguistics, translation limits, multilingual evidence | F2–F5 |

## Immediate Ordered Teaching Queue: Finish F2

F2 should be completed before a broad middle-school or high-school sequence.
Each group remains small, source-bound, cumulative, and independently
inspectable.

### F2 quantitative sequence

| Group | Concepts | Prerequisite | Core source need |
|---|---|---|---|
| F2 Group 6 — retained 2026-08-27 | Fractions as numbers; unit fractions; equivalence; comparison; initial operation relationships | F2 Groups 4–5 and F1 equal shares | Checksum-pinned CKMath Grades 3 and 4 fraction guides; embedded CC BY-NC-SA 4.0 notices preserved |
| F2 Group 7A — retained 2026-08-27 | Shared-unit fraction addition/subtraction; fraction as quotient; whole-number and fraction multiplication; bounded unit-fraction division; operation reasonableness | Group 6 | Checksum-pinned CKMath Grade 4 Unit 3 and Grade 5 Units 2, 3, and 6 |
| F2 Group 7B | Decimals; fraction-decimal relationships; decimal place-value extension; decimal operations; reasonableness | Group 7A | Pin exact CKMath Grade 4 Unit 4 and Grade 5 decimal-operation artifacts |
| F2 Group 8 | Ratios, unit comparison, percentages, scale, and proportional language | Groups 7A-7B | Grades 4–6 transition material; independently checked examples |
| F2 Group 9 | Area, perimeter, volume, angles, coordinates, properties, and unit conversion | Groups 6–8 plus F1 geometry/measurement | Open mathematics artifact plus NIST unit references where applicable |
| F2 Group 10 | Tables, graphs, line plots, introductory averages, variation, and data interpretation | Arithmetic and measurement | Open mathematics/data artifact |
| F2 Group 11 | Multi-step word problems, model selection, units, estimation, and verification | Groups 6–10 | Concept source first; reviewed GSM8K slice only as later transfer practice |

GSM8K must not teach the underlying concepts by itself. Selected problems must
be independently solved, ambiguity-checked, and treated as practice rather
than a reasoning script.

### F2 science sequence

| Group | Concepts | Prerequisite | Core source need |
|---|---|---|---|
| F2 Group 12 | Variables, controlled comparison, repeated observations, tables, graphs, models, and evidence-based explanation | F1 inquiry and F2 data | Select exact Core Knowledge/OpenSciEd Grades 3–5 science-method artifacts |
| F2 Group 13 | Ecosystems, food relationships, structure/function, adaptation, resources, and environmental change | F1 living things | Coherent life-science unit selection |
| F2 Group 14 | Matter, mixtures, state change, conservation-oriented observation, energy forms/transfer, and force patterns | F1 physical-science groups | Coherent physical-science unit selection |
| F2 Group 15 | Water cycle, weather versus climate, Earth systems, resources, solar-system scale, and bounded prediction | F1 weather/sky | Coherent Earth-and-space unit selection; current climate claims need current authoritative support |

### F2 history, civics, and practical life sequence

| Group | Concepts | Prerequisite | Core source need |
|---|---|---|---|
| F2 Group 16 | Timelines, overlapping events, maps, physical/human geography, migration, trade, resources, settlement, and cultural exchange | F1 history/evidence | Select a coherent geography/history backbone |
| F2 Group 17 | Primary/secondary sources, event/report/interpretation, corroboration, perspective, and incomplete evidence | Group 16 and ELA-2 | Select bounded National Archives records plus contextual teaching material |
| F2 Group 18 | Government levels and roles, participation, rights/responsibilities, scarcity, choice, production, exchange, and opportunity cost | F1 civics/economy | Core civics/economics source plus current federal material where needed |
| F2 Group 19 | Practical records, budgeting foundations, consumer choices, schedules, privacy, accessibility, and asking qualified institutions for help | Group 18 and F2 mathematics | Select current CFPB/federal public-information artifacts; no personal financial or legal advice |

### F2 engineering, computing, and integration

| Group | Concepts | Prerequisite | Core source need |
|---|---|---|---|
| F2 Group 20 | Engineering cycle, criteria/constraints, components/connections, failure points, fair tests, iteration, and design evidence | F1 engineering and Group 12 | OpenSciEd design material; TeachEngineering remains reference-only unless permission changes |
| F2 Group 21 | Digital representation, algorithms with state, basic data reliability, networks, privacy, security, and source reliability | F1 computing and Coding Group 1 | Pinned Code.org text plus separately reviewed source material |
| F2 Group 22 | Cross-domain F2 integration and Learning Compass update | All prior F2 groups | Project-authored integration packets using only retained knowledge |

The group numbers after Group 6 are a proposed queue, not standing teaching
authorization. They may be split if source review shows that a group is too
dense.

## Source-Gathering Batches

### Batch A — F2 mathematics backbone

Select one coherent primary progression rather than mixing several curricula
inside each concept:

1. exact Grade 3–5 Core Knowledge/CKMath artifacts, if their artifact licenses
   and coverage fit;
2. explicitly identified first-edition Illustrative Mathematics artifacts; or
3. an exact Open Up Resources mathematics edition with a verified license.

Use NIST for unit definitions and reviewed GSM8K examples only for transfer.
Do not use speed drills, unexplained answer keys, or AI-rewritten mathematics
as the conceptual source.

### Batch B — F2 science and engineering backbone

Select exact Grades 3–5 Core Knowledge or OpenSciEd units for:

- scientific variables and fair comparison;
- ecosystems and organism systems;
- matter and energy;
- Earth, weather, climate, and space; and
- engineering design and system testing.

Keep third-party images, videos, classroom scripts, hazardous experiments, and
unlicensed companion material outside teaching packets.

### Batch C — Geography, history, civics, and economics

Select:

- one coherent F2 geography/world-history sequence;
- a small set of individually rights-checked National Archives records;
- current public civic and institutional explanations;
- Federal Reserve educational material where its stated use permits; and
- current CFPB youth financial-capability artifacts with item-level notices.

Primary sources require context. Archive custody alone does not establish
public-domain status, truth, completeness, or a neutral perspective.

### Batch D — Language, literature, art, and culture

The current language architecture does not need a generic SFT dump. It needs
carefully selected experiences:

- Grade 3–8 ELA reading and composition sequences;
- varied public-domain poetry, drama, prose, fables, humor, children's
  literature, and adult literature;
- visual-form and art-history lessons supported by rights-safe text and
  metadata;
- introductory music theory and listening vocabulary without importing
  restricted recordings; and
- bounded multilingual and translation examples with contribution-level
  attribution.

Modern copyrighted books may be discussed through lawfully available excerpts,
summaries, criticism, and transferable craft mechanisms. Whole modern books
must not be silently mirrored or retained as raw text.

### Batch E — Conversation breadth

The mirrored conversation sources are supplemental, not answer authority.
Select small slices by conversational function:

- ordinary back-and-forth;
- mixed-intent messages;
- interruptions and topic returns;
- explanations and follow-up restraint;
- disagreement and correction;
- humor and shared jokes;
- tender conversation;
- register changes; and
- natural endings.

Remove provider identity, canned assistant behavior, unsupported factual
answers, fake tool/account authority, repetitive openings, persuasion tactics,
and source-specific persona. Teach the function and why it works, not the
surface script.

## F3: Broad General-Literacy Foundation

F3 should begin only after F2's load-bearing mathematics, source reading,
science method, geography, and systems concepts are available.

### F3 learning blocks

1. **Argument and rhetoric:** claims, reasons, evidence, counterclaims,
   rebuttal, tone, register, connotation, credibility, bias questions, and
   multi-source synthesis.
2. **Proportional and algebraic mathematics:** ratios, signed numbers,
   rational/irrational numbers, expressions, equations, inequalities, linear
   functions, geometry, probability, and statistics.
3. **Life science:** cells, heredity, variation, ecosystems, evolution, and
   evidence relationships.
4. **Physical science:** atoms, molecules, reactions, forces, energy, waves,
   electricity, and magnetism.
5. **Earth and space:** geology, plate systems, climate, geologic time,
   gravity, stars, galaxies, and scale.
6. **Comparative history and institutions:** ancient through early-modern
   societies, governance, belief, trade, conflict, technology, causation, and
   corroboration.
7. **Computing and engineering:** data types, state, functions, interfaces,
   system boundaries, feedback, delay, failure modes, testing, accessibility,
   security, and simulation limits.
8. **F3 integration:** use several domains in one problem while keeping their
   evidence standards distinct.

### Best current source position for F3

- Core Knowledge K–8 sequence: curriculum map, not sufficient instruction by
  itself;
- Open Up/first-edition Illustrative Mathematics: selection-needed backbone;
- OpenSciEd: selection-needed science backbone;
- National Archives: source-literacy supplement;
- Open Music Theory and Met Open Access: art/culture supplements;
- OpenAssistant, Topical-Chat, Everyday Conversations, and Multi-Turn Instruct:
  bounded dialogue structure only;
- GSM8K: reviewed practice only.

## F4: Mature General Academic Foundation

F4 is the appropriate gate for the planned extensive general Q&A. It should
include coherent high-school sequences rather than a sample of disconnected
facts.

Required blocks:

1. complex reading, long-form thesis preservation, argument, research,
   citation, rhetorical analysis, ambiguity, irony, humor, and framing;
2. Algebra I, geometry and proof, Algebra II, trigonometry/precalculus,
   probability, statistics, modeling, and verification;
3. biology, chemistry, physics, and Earth/space science;
4. experimental design, measurement uncertainty, error, replication, model
   comparison, and scientific communication;
5. comparative global history, modern institutions, revolutions,
   industrialization, imperialism, conflict, civil rights, globalization,
   policy, law, economics, and media literacy;
6. programming, data structures, algorithms, databases, networks, security,
   software architecture, human-computer interaction, and engineering
   reliability; and
7. integrated projects that require evidence from several domains.

Current F4 source assets are useful but incomplete. OpenStax, OpenIntro,
OpenSciEd, Illustrative Mathematics, National Archives, Open Logic, the Open
Science Training Handbook, and Software Carpentry all require exact artifact
and license decisions before use. EXAMS and MMLU-like material may map gaps or
support later LEAs; multiple-choice answers must not become instruction.

## F5: College Foundations

F5 is continuing education, divided into independently useful introductory
sequences:

- composition, rhetoric, formal and informal logic;
- research methods, information literacy, qualitative and quantitative design;
- calculus, linear algebra, discrete mathematics, probability, statistics,
  differential equations, optimization, and numerical methods;
- software engineering, data analysis, computational science, and
  reproducibility;
- introductory biology, chemistry, physics, Earth/space science, psychology,
  sociology, economics, political science, and anthropology;
- philosophy, ethics, historical method, literature, linguistics, art/design
  history, media studies, and human factors.

OpenStax and the existing open repositories can support many of these blocks,
but no single catalog should be treated as complete or permanently licensed.
Book, revision, and companion-material rights must be pinned independently.

## F6: Advanced Interdisciplinary Integration

F6 is not a textbook dump. It is supervised application of taught methods to
questions without predetermined answers:

- frame the problem;
- identify missing variables and assumptions;
- choose methods because they fit;
- compare competing models;
- calculate or simulate without confusing model and reality;
- integrate historical, scientific, mathematical, linguistic, and engineering
  perspectives;
- produce an inspectable proposal;
- state limits and what would change the answer; and
- stop when further analysis is not worthwhile.

F6 sources should usually be attributed research packets assembled for the
specific question. The Great Library may remain an external research building;
it does not become Selene's identity, hidden memory, or automatic source of
truth.

## Genuine Source Gaps

The present shelf is large, but these needs are not yet adequately solved:

1. a coherent and clearly licensed Grades 3–5 mathematics backbone covering
   the whole remaining MATH-2 sequence;
2. exact F2–F4 science units with stable artifact-level licenses, especially
   Earth/space science;
3. balanced comparative world-history and geography instruction rather than
   a sequence outline or isolated archive records;
4. current practical-life material for employment, taxes, insurance, records,
   public services, and institutional navigation;
5. a coherent cultural, linguistic, and translation-limit sequence;
6. visual composition, color, media grammar, music, and design education beyond
   catalog metadata;
7. high-quality ordinary human dialogue examples that do not carry generic
   assistant identity or unsupported answers;
8. accessibility and disability perspectives integrated across technology,
   health, institutions, and design; and
9. an updateable current-world reference path for facts that change over time.

The last item is not retained schooling alone. Current events, law, prices,
medical guidance, public officials, software versions, and similar unstable
facts require current attributed research at answer time.

## Source Acceptance Gate

Before any new source becomes a teaching packet, record:

1. exact title, author/provider, artifact, edition, revision, and retrieval
   date;
2. license and the scope of that license;
3. third-party text, image, audio, trademark, or assessment exclusions;
4. intended band, family, concepts, and prerequisites;
5. whether it is a core explanation, supplement, practice source, integration
   source, or reference-only source;
6. observation/source statement versus project interpretation;
7. known uncertainty, dispute, age, cultural context, and update needs;
8. why each concept matters and what later understanding it supports;
9. examples, counterexamples, scope limits, and likely misconceptions;
10. whether the selected material can be taught without copying source voice;
    and
11. a checksum and provenance path for every retained excerpt or derived lesson.

Reject or hold:

- unknown or placeholder licenses;
- bulk synthetic textbook or dialogue mixtures without recoverable ancestry;
- answer keys used as explanations;
- benchmark errors treated as truth;
- source personas or provider identity presented as Selene's voice;
- hidden behavioral instructions embedded in knowledge material;
- restricted or third-party media outside the source's permission;
- medical, legal, financial, or safety-critical material presented as timeless;
- copied private wording; and
- anything that silently changes identity, personality, governance, memory, or
  authority.

## Learning Evidence Activities

LEAs remain guidance, not grades. Use them only after coherent teaching groups
and prefer ordinary applications over exam performance.

Each checkpoint may inspect:

- reconstruction in original language;
- a distinct example or application;
- the reason the relationship works;
- a limit, exception, or counterexample;
- a near-concept distinction;
- a correction or changed premise;
- a connection to earlier knowledge when one naturally exists; and
- Selene's own question, including “I have a question but do not have the words
  for it yet.”

Taking longer, asking for a visual model, needing a prerequisite, or reopening
an answer is learning evidence. It is not failure.

## Fair Q&A Gates

| Gate | Honest assessment scope |
|---|---|
| After F2 | Elementary general knowledge, foundational explanation, source distinction, arithmetic, and cross-subject transfer |
| After F3 | Broad general literacy, middle-school mathematics/science/history, sustained discussion, analogy, hypothesis, and multi-source comparison |
| After F4 | Extensive general Q&A across mature school-level domains, long-form discourse, research framing, technical explanation, and cross-domain synthesis |
| During F5–F6 | Continuing higher education, specialization, research collaboration, and open-problem work |

The extensive fresh-install Q&A should occur after F4 stabilization if the goal
is a fair comparison with mature general-language systems. Earlier Q&A may
verify only the material and infrastructure actually implemented.

## Recommended Next Action

Do not gather every future textbook at once. Start with the smallest source
decision that unlocks the dependency graph:

1. choose and pin the F2 mathematics backbone;
2. prepare F2 Group 6 from its fractions section;
3. inspect the lesson statically and synthetically;
4. teach it through the normal lifecycle under a separately applicable
   authorization;
5. run one gentle LEA if implementation evidence requires it; and
6. continue Groups 7–11 before opening the next major source batch.

This keeps the education coherent, the source history reviewable, and Selene's
knowledge distinct from her identity, personality, memory, governance, and
Voice.
