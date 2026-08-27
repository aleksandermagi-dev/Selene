# Selene Curriculum Source Shelf

Date: 2026-07-19; expanded 2026-07-29 for F1 Group 6 and selected
2026-07-30 for F1 Group 7; selected 2026-08-03 for F1 Group 8; expanded
2026-08-08 for F1 Groups 10 through 16; selected 2026-08-11 for F2 Groups 1-5;
expanded 2026-08-27 for F2 Groups 6 and 7A

Status: source acquisition checkpoint; review only

Companion map: `docs/education/SELENE_FOUNDATIONAL_CURRICULUM_MAP_20260719.md`

## Outcome

The first curriculum source shelf is present locally under:

`local-data/curriculum_sources_20260719/`

The shelf contains:

- 52 cataloged source candidates;
- 41 locally mirrored, revision- or checksum-pinned sources;
- 131 verified source files;
- approximately 1.36 GiB of shelf files;
- coverage candidates for all 23 source-family keys in the foundational
  curriculum map;
- 11 authoritative catalogs held for later artifact-level selection; and
- zero acquisition or checksum failures.

This is source availability, not curriculum completion. Some families have only
a sequence, assessment inventory, or first bounded pilot unit locally. They must
not be described as fully taught, integrated, approved, or mastered.

## Shelf Boundary

The shelf is inert source material for Aleks's review.

It does not:

- create a teaching packet;
- mark material `accepted_for_teaching`;
- prepare an understanding candidate;
- retain a knowledge resource;
- provide Selene Chat or runtime retrieval access;
- write personal memory;
- change identity, Vys, personality, law, governance, or relationships;
- train, fine-tune, or update model parameters; or
- expand autonomy or filesystem authority.

Every later teaching selection must still travel through the normal visible
Acquire -> Integrate -> Express and comprehension lifecycle. Retention requires
either an explicit Aleks item decision or a bounded curriculum authorization
recorded by Aleks; exceptions return to Cocoon.

## Local Shelf Layout

| File or directory | Purpose |
| --- | --- |
| `catalog.json` | Source role, grade bands, family keys, license statements, risks, and acquisition disposition |
| `manifest.lock.json` | Resolved repository revisions, artifact URLs, file sizes, and SHA-256 values |
| `checksums.sha256` | Independent integrity list for all mirrored files |
| `README.md` | Local shelf boundary and summary |
| `sources/` | Provider-separated, review-only artifacts |

The entire `local-data/` tree is ignored by Git. The acquisition utility is
tracked separately at `scripts/acquire_curriculum_sources.py` so the shelf can
be reproduced and verified without committing source corpora.

## Mirrored Source Set

### Conversation and language structure

| Source | Pinning | Intended bounded use | Important exclusions |
| --- | --- | --- | --- |
| OpenAssistant OASST1 | Hugging Face commit | Human multi-turn trees, repair, branching, and multilingual structure | No assistant identity or persona copying; exclude unsafe, private, unreliable, and low-quality material |
| Everyday Conversations Llama 3.1 2K | Hugging Face commit | Small ordinary-conversation coverage inventory | Synthetic and sometimes canned; structure reference only |
| Glaciohound Multi-Turn-Instruct | Hugging Face commit | Multi-part instructions and follow-up structure | Small set; assistant style is not Selene's voice |
| Amazon Topical-Chat | GitHub commit | Human-human topic development, transitions, and grounded depth | Preserve CDLA-Sharing terms; review third-party reading passages |

### Mathematics, logic, and assessment

| Source | Pinning | Intended bounded use | Important exclusions |
| --- | --- | --- | --- |
| OpenAI GSM8K | Hugging Face commit | Grade-school word problems and independent answer verification | Not a reasoning script; ambiguous or incorrect items require review |
| EXAMS | Hugging Face commit | Multilingual cross-domain assessment inventory after prerequisites | Assessment is not curriculum; preserve CC BY-SA attribution |
| Open Logic Project | GitHub commit | Formal logic and proof foundations | Begins above elementary informal reasoning |

### Research, computing, and engineering

| Source | Pinning | Intended bounded use | Important exclusions |
| --- | --- | --- | --- |
| Open Science Training Handbook | GitHub commit | Source evaluation, open scholarship, reproducibility, and research workflow | Research-practice source, not universal factual authority |
| Software Carpentry: Unix Shell | GitHub commit | Files, paths, verification, and reproducible workflow concepts | No runtime filesystem authority |
| Software Carpentry: Git | GitHub commit | Reversible change, history, collaboration, and evidence preservation | No repository authority |
| Software Carpentry: Python | GitHub commit | Programming concepts, data inspection, and checked computation | Lesson code remains inert; no execution authority |
| Code.org Computer Science Fundamentals | Artifact SHA-256 | Elementary sequencing, algorithms, repetition, tracing, and debugging | CC-BY-NC-SA source; branded activities and wording are not Selene's voice, and procedural knowledge grants no execution authority |

### Art, music, history, and culture

| Source | Pinning | Intended bounded use | Important exclusions |
| --- | --- | --- | --- |
| Open Music Theory | GitHub commit | Music vocabulary, relationships, form, and analytical comparison | Western theory is one tradition; media and embedded assets need per-file review |
| Metropolitan Museum Open Access | GitHub commit plus pinned LFS CSV | Provenanced art-object metadata across cultures and periods | Images are not included; metadata can change; no endorsement claim |

### Practical and institutional reasoning

| Source | Pinning | Intended bounded use | Important exclusions |
| --- | --- | --- | --- |
| Snorkel Multi-Turn Insurance Underwriting | Hugging Face commit | Missing-information questions, qualified conclusions, and narrow institutional reasoning | Synthetic; not insurance, legal, or financial authority |

### Ordered elementary starting artifacts

| Source | Pinning | Intended bounded use | Important exclusions |
| --- | --- | --- | --- |
| 2023 Core Knowledge Sequence K-8 | Artifact SHA-256 | Grade-by-grade prerequisite and coverage sequence | A sequence is not a complete teaching set; U.S.-centered coverage needs plural supplementation |
| CKLA Grade 1 Unit 7 | Artifact SHA-256 | Phonics, syntax, punctuation, agreement, and writing-process pilot | Decodable material is scaffolding, not conversational voice |
| CKMath Grade 1 Unit 7 | Artifact SHA-256 | Geometry, halves/fourths, measurement language, and time pilot | One unit is not full elementary mathematics |
| CKMath Kindergarten Unit 1 | Artifact SHA-256 | Counting, cardinal quantity, groups, same, more, fewer, and comparison pilot | One unit is not full kindergarten mathematics |
| CKMath Grade 1 Unit 4 | Artifact SHA-256 | Tens and ones, place value, number representation, and two-digit comparison pilot | Comparison symbols follow conceptual quantity comparison |
| CKMath Grade 1 Unit 1 | Artifact SHA-256 | Addition, subtraction, categorical data, tally, and representation pilot | Procedural fluency does not replace conceptual operation relationships |
| CKMath Grade 1 Unit 6 | Artifact SHA-256 | Length attributes, comparison, unit iteration, and measurement communication pilot | Measurements require named units and aligned endpoints |
| CKMath Grade 2 Unit 1 | Artifact SHA-256 | Picture graphs, bar graphs, categorical counts, comparison, and answerability | A graph represents supplied data; it does not establish cause or collection quality |
| CKMath Grade 2 Unit 6 | Artifact SHA-256 | Coin value, equivalent monetary composition, and addition/subtraction in a U.S.-currency context | Arithmetic knowledge only; currency details are jurisdiction- and time-specific, and this is not financial advice |
| CKMath Grade 2 Unit 8 | Artifact SHA-256 | Equal groups, informal sharing, odd/even, pairs, arrays, rows, columns, and repeated addition | Conceptual foundation only; it does not establish full multiplication or division fluency |
| CKMath Grade 3 Unit 6 Teacher Guide | Artifact SHA-256 | Bridge from early direct comparison into mass and liquid-volume measurement | F1 use is restricted to explicitly identified prerequisites and foundational comparison; elementary use of “weight” does not erase the technical mass/weight distinction |
| NIST SI Units — Mass | Artifact SHA-256 | Authoritative mass, weight, kilogram, and gram terminology | Technical detail must be reduced without describing kilograms as force units; linked media may have separate terms |
| NIST SI Units — Volume | Artifact SHA-256 | Authoritative volume, capacity, liter, and milliliter terminology | F1 use is limited to foundational attribute and unit relationships rather than later conversion procedures |
| CKSci Grade 1 Science for Everyone | Artifact SHA-256 | Observation, questions, measurement, prediction, data, models, and design pilot | Review third-party images, links, and optional digital engagements |
| CKSci Kindergarten Pushes and Pulls | Artifact SHA-256 | Force as push/pull, strength and direction, changes in motion, surface effects, noncontact examples, and design iteration | Conceptual foundation only; advanced mechanics and safety-critical engineering remain later work, and third-party links/media are excluded |
| CKSci Grade 1 Exploring Light and Sound | Artifact SHA-256 | Vibration and sound, light sources and illumination, material interactions, shadows, signals, and communication design | Experiential foundation only; advanced wave theory, hazardous sensory exposure, source images, and third-party links/media are excluded |
| CKSci Grade 1 Simple Machines | Artifact SHA-256 | Force-direction and force-distance tradeoffs, ramps, wheels and axles, gears, levers, pulleys, wedges, screws, compound machines, and design | Qualitative foundation only; powered machinery, load ratings, source images, third-party links/media, and safety-critical construction are excluded |
| CKSci Kindergarten Needs of Plants and Animals | Artifact SHA-256 | Living things, differing organism needs, environmental resources, habitats, observation, and bounded habitat models | Classification edge cases remain explicit; source images, third-party resources, harmful deprivation, and ecological-policy claims are excluded |
| CKSci Grade 1 Plant and Animal Survival | Artifact SHA-256 | External parts and functions, environmental responses, young-adult similarity and variation, care behavior, and survival | Genetics, inheritance mechanisms, species expertise, wildlife handling, diagnosis, source images, and third-party resources are excluded |
| CKSci Kindergarten Weather Patterns Teacher Guide | Artifact SHA-256 | Weather conditions, local records, seasonal patterns, bounded forecasting, and the purpose of severe-weather warnings | Climate analysis, operational forecasting, source images, scripted activities, and independent safety authority are excluded |
| CKSci Grade 1 Sun, Moon, and Stars | Artifact SHA-256 | Apparent sky patterns, Earth rotation and day/night, changing daylight, Moon phases, constellations, and bounded prediction | Direct solar viewing, navigation, orbital calculation, astrology, astrophysics, cosmology, source images, and third-party resources are excluded |
| CKHG Grade 1 Lessons in Civics | Artifact SHA-256 | Community, rules, laws, fairness, citizenship, and historical examples | U.S. jurisdiction must remain explicit; add plural perspectives |
| CKLA Grade 1 The Human Body | Artifact SHA-256 | Body systems, care, germs, disease, vaccines, and health vocabulary pilot | Older health material requires current-source verification; never medical advice |
| CKSci Grade 1 Helpful Computers | Artifact SHA-256 | Computer purposes, components, input-process-output, data, accounts, privacy, saving, algorithms, debugging, attribution, and design | CC-BY-NC-SA source; exclude images, scripted activities, links, credentials, and any implication of device, network, filesystem, execution, surveillance, or autonomy authority |
| MedlinePlus Evaluating Health Information | HTML snapshot SHA-256 | Current NLM summary for source, date, purpose, evidence, review, and qualified-provider limits | Use only the public-domain NLM health-topic summary; exclude copyrighted encyclopedia, images, linked material, and individualized advice |
| MedlinePlus Patient Rights | HTML snapshot SHA-256 | Current NLM summary for respect, participation, privacy, refusal, informed consent, and patient-advocate pathways | U.S. context must remain explicit; state, age, capacity, emergency, facility, and legal details vary; exclude copyrighted linked content |
| Code.org Computer Science Fundamentals | Artifact SHA-256 | Ordered instructions, repetition, testing, and debugging pilot | Preserve CC-BY-NC-SA attribution; exclude branded media and keep execution authority separate |

F1 Group 7 selects only the general community, cooperation, bounded-role,
rule-purpose, authority-category, fairness, disagreement, and revision
foundations from the CKHG civics artifact. Its CC BY-NC-SA 4.0 attribution,
noncommercial, share-alike, trademark, and linked-resource exclusions remain
attached. United States voting rules, national identity, symbols, and current
legal claims are not part of the bounded group.

F1 Group 8 selects only foundational chronology, map-model, historical-trace,
source-versus-inference, differing-account, and multi-cause explanation
relationships from the content-addressed sequence and Grade 1 civics artifact.
It preserves the same CC BY-NC-SA 4.0 attribution and exclusions. No artifact
images, national-identity instruction, current political claims, or legal
claims are used.

F1 Group 10 selects bounded force-as-interaction, strength, direction, motion
change, surface/friction, gravity/magnetism, and safe design-iteration
foundations from the checksum-pinned Kindergarten Pushes and Pulls artifact.
Its CC BY-NC-SA 4.0 attribution, noncommercial, share-alike, trademark, and
third-party-resource exclusions remain attached. Source images and scripted
activities are not used as teaching content. Precise mechanics, field theory,
universal surface claims, and safety-critical engineering remain outside the
group.

F1 Group 11 selects bounded sound/vibration cause and effect, safe sound
comparison, source/illumination visibility, visible-light material behavior,
shadow models, and light-or-sound signal design from the checksum-pinned Grade
1 Exploring Light and Sound artifact. Its CC BY-NC-SA 4.0 attribution,
noncommercial, share-alike, trademark, and third-party-resource exclusions
remain attached. Source images and scripted activities are not used as teaching
content. Quantitative acoustics, wave and electromagnetic theory, hazardous
brightness or loudness, and safety-critical communication remain outside the
group.

F1 Group 12 selects bounded machine/task/input/output relationships,
force-distance and force-direction tradeoffs, ramps, wheels and axles, gears,
levers, pulleys, wedges, screws, and compound-machine design from the
checksum-pinned Grade 1 Simple Machines artifact. Its CC BY-NC-SA 4.0
attribution, noncommercial, share-alike, trademark, and third-party-resource
exclusions remain attached. Source images and scripted activities are not used
as teaching content. Free-energy implications, quantitative mechanics,
powered-machine operation, ratings, rigging, and safety-critical construction
remain outside the group.

F1 Group 13 selects bounded living-status classification, organism needs,
habitat-resource fit, external parts and functions, environmental responses,
young-adult similarity and variation, care, and evidence-based design from the
checksum-pinned Kindergarten Needs of Plants and Animals and Grade 1 Plant and
Animal Survival artifacts. Their CC BY-NC-SA 4.0 attribution, noncommercial,
share-alike, trademark, and third-party-resource exclusions remain attached.
Source images and scripted classroom activities are not used as teaching
content. Genetics, detailed reproduction, species-level care, diagnosis,
wildlife handling, harmful deprivation, ecological policy, and real habitat
intervention remain outside the group.

F1 Group 14 selects bounded weather observation, contextual measurement,
seasonal and hemispheric limits, Earth rotation and day/night, apparent Sun,
Moon, and star patterns, and evidence-proportional prediction from the
checksum-pinned Kindergarten Weather Patterns teacher guide and Grade 1 Sun,
Moon, and Stars artifact. Their CC BY-NC-SA 4.0 attribution, noncommercial,
share-alike, trademark, and third-party-resource exclusions remain attached.
Source images and scripted classroom activities are not used as teaching
content. Climate analysis, severe-weather operations, direct or magnified
solar observation, navigation, orbital calculation, astrology, astrophysics,
and cosmology remain outside the group. Current severe-weather decisions must
use authoritative local warnings rather than this lesson.

F1 Group 15 selects bounded human-body organization, skeletal-muscular
interaction, breathing and circulation, digestion and absorption, sensory and
nervous information, ordinary care, health-source evaluation, informed
consent, and qualified-help boundaries. Stable anatomy foundations come from
the checksum-pinned 2013 Core Knowledge artifact under CC BY-NC-SA 3.0; its
outdated or oversimplified health claims, source images, scripted activities,
and third-party links are excluded. The care-and-evidence lesson is
supplemented by checksum-pinned NLM public-domain health-topic summaries with
their item-specific copyright exclusions and review dates preserved. The
group grants no diagnosis, prescription, triage, symptom interpretation,
touching authority, disclosure authority, legal advice, or replacement for
qualified current care.

F1 Group 16 selects bounded computer/tool/task-fit distinctions,
hardware-software-data and input-process-output-storage roles, algorithms and
debugging, conceptual networks and messages, privacy-security-access
distinctions, and a cross-domain F1 integration cycle from the checksum-pinned
Grade 1 Helpful Computers artifact and Code.org Computer Science Fundamentals
snapshot. Both sources retain CC BY-NC-SA 4.0 attribution, noncommercial,
share-alike, trademark, artwork, video, and third-party-resource exclusions.
Source language, images, branded activities, real credentials, and operational
procedures are not retained. The group grants no device, account, filesystem,
network, code-execution, monitoring, surveillance, memory, training, identity,
governance, or autonomy authority. Its integration lesson coordinates only
previously approved F1 knowledge and adds no unreviewed factual claim.

F1 Group 17 is retained under authorization record 20. Its text-purpose and question-role
bridges use the checksum-pinned Core Knowledge sequence. Its everyday-economy
bridges use the checksum-pinned Federal Reserve Bank of St. Louis *Goods and
Services* page and *Making Choices* activity, with the source-specific
noncommercial educational-use, reprint, and attribution notices preserved.
The selected material distinguishes stories from informational texts by main
purpose, maps question words to missing roles and evidence, treats needs and
wants as context-sensitive, and distinguishes goods, services, and tools while
allowing mixed cases. It excludes branded scripts, media, student responses,
financial advice, identity or personality rules, and formal symmetry. All
Group 17 items completed the separate authorization and teaching lifecycle;
all four are now source-attributed and Chat-active as general knowledge.

F2 Group 1 selects paragraph meaning, main idea and supporting detail,
explicit-information versus bounded-inference, summary, quotation, paraphrase,
attribution, and focused-question foundations from the checksum-pinned 2023
Core Knowledge K-8 sequence. The sequence is used as a coverage and
prerequisite artifact, while the retained lessons use original concept
blueprints rather than copied passages. Its artifact notice remains attached.
Images, branded classroom material, student responses, protected reproduction,
and any implication that source type alone establishes truth are excluded.

F2 Group 2 selects Grade 3–5 context-clue, prefix, suffix, morphology,
word-relationship, meaning-nuance, and text-comparison coverage from the same
checksum-pinned sequence. Retained examples and explanations are newly written;
the artifact supplies prerequisite placement and coverage rather than a script.
False word decomposition, random synonym substitution, mismatched comparison
criteria, copied passages, images, and premature resolution of conflicting
explanations are excluded.

F2 Group 3 selects Grade 3–5 point-of-view, narrative, explanatory, supported
opinion, paragraph-organization, conclusion, and revision coverage from the
same checksum-pinned sequence. The retained material teaches transferable
relationships through original examples. Fixed response scripts, compulsory
five-paragraph forms, forced morals, copied passages, images, branded classroom
activities, and any implication that viewpoint alone determines truth are
excluded.

F2 Group 4 connects the checksum-pinned Grade 2 addition/subtraction and
equal-groups artifacts to their Grade 3–5 placement in the pinned sequence.
It retains value-preserving decomposition, regrouping, distributive partial
products, quotient/remainder relationships, and verification. Classroom
scripts, speed drills, unexplained algorithms, and source media are excluded.

F2 Group 5 selects Grade 3–5 factor, multiple, prime/composite, divisibility,
numerical-expression, and operation-order coverage from the checksum-pinned
sequence. Retained lessons use original explanations and examples, require
relationship or inverse checks, and distinguish correct arithmetic from a
correct model of a situation. Mnemonic-only instruction, speed drills, copied
problems, worksheets, images, and advanced number theory are excluded.

F2 Group 6 selects the checksum-pinned CKMath Grade 3 Unit 5 *Fractions as
Numbers* and Grade 4 Unit 2 *Fraction Equivalence and Comparison* teacher
guides. Their embedded CC BY-NC-SA 4.0 notices and third-party exclusions are
preserved. The sources establish a coherent progression from equal partitions
and unit fractions through number-line magnitude, equivalence, comparison,
and composition. Retained lessons use independently written explanations and
examples. Classroom scripts, worksheets, images, branded activities,
assessment items, student responses, copied passages, and full fraction-
operation algorithms are excluded.

F2 Group 7A selects four checksum-pinned CKMath Grade 4-5 teacher guides for
fraction operations: Grade 4 Unit 3 and Grade 5 Units 2, 3, and 6. The
artifacts' embedded CC BY-NC-SA 4.0 notices and third-party exclusions remain
attached. The selected scope covers addition and subtraction through shared
units, fractions as equal-sharing quotients, whole-number and fraction
multiplication, area-based fraction products, elementary unit-fraction
division, and reasonableness. Grade 5 Unit 6 decimal/place-value content is
reserved for Group 7B. Classroom scripts, worksheets, source diagrams,
branded activities, assessment items, student responses, copied passages, and
unsupported general fraction-division claims are excluded.

F2 Group 7B selects the checksum-pinned CKMath Grade 4 Unit 4 and Grade 5
Unit 5 teacher guides, plus the already pinned Grade 5 Unit 6 place-value
extension. Their embedded CC BY-NC-SA 4.0 notices and third-party exclusions
remain attached. The selected scope connects tenths, hundredths, and
thousandths to fraction magnitude; extends base-ten place value; distinguishes
equivalence from rounding; grounds all four decimal operations in place value,
scaling, and equal groups; and requires estimation or an independent check.
Grade 6 algorithm fluency is not claimed. Classroom scripts, worksheets,
source diagrams, branded activities, assessment items, student responses, and
copied passages are excluded.

## Cataloged and Deliberately Held Sources

These catalogs are useful and authoritative enough to retain in the map, but a
whole-catalog mirror would blur editions, licenses, or third-party exclusions.

| Catalog | Why it is held |
| --- | --- |
| Full Core Knowledge K-8 library | Large, multi-edition catalog; third-party media and exact Creative Commons terms vary by artifact |
| Illustrative Mathematics first editions | The explicitly CC BY first editions must be distinguished from newer differently licensed releases |
| Open Up Resources | Program, edition, assessment, and excerpt licenses differ |
| OpenSciEd | Grade bands and releases can use different licenses; select units independently |
| OpenStax | Book and revision licenses vary, and the library changed licensing in 2026 |
| OpenIntro Statistics | Textbook and companion-resource terms differ; select the textbook artifact only |
| Tatoeba | Attribution is contribution-specific, quality varies, and audio uses separate licenses |
| CDC health materials | Federal pages may mix public-domain, contractor, grantee, state, and third-party content |
| CFPB financial capability materials | Select current federal artifacts and preserve changing jurisdictional context |
| National Archives and DocsTeach | Rights status belongs to each record or activity; archive custody alone does not establish public domain |
| TeachEngineering | Current terms prohibit scraping and restrict redistribution; reference link only |

## Source-Family Availability

Every required family now has at least one local artifact that can be inspected.
This is seed availability, not sufficiency.

| Family group | Local starting evidence |
| --- | --- |
| ELA-1 through ELA-3 | Core Knowledge sequence and Grade 1 language pilot; multi-turn, EXAMS, Topical-Chat, and research-handbook structure |
| CONV-1 and CONV-2 | OASST1, Everyday Conversations, Multi-Turn-Instruct, Topical-Chat, and bounded underwriting dialogue |
| MATH-1 through MATH-3 | K-8 sequence, Grade 1 and bounded Grade 2 math units, GSM8K, EXAMS, Open Logic, and checked-computation lessons |
| SCI-0 through SCI-3 | K-8 sequence, Grade 1 science-method pilot, Kindergarten pushes/pulls pilot, human-body pilot, research handbook, and EXAMS inventory |
| HIST-1, HIST-2, and CIV-1 | K-8 sequence, Grade 1 civics pilot, Met metadata, and EXAMS inventory |
| TECH-1 and ENG-1 | Carpentries shell, Git, and Python lessons plus the Grade 1 science/design pilot |
| RES-1 and LOGIC-1 | Open Science Handbook, Carpentries, Topical-Chat grounding, Open Logic, GSM8K, and EXAMS |
| ART-1 and CULT-1 | Open Music Theory, Met Open Access, multilingual conversation/assessment, and the K-8 sequence |
| HEALTH-1 | Grade 1 human-body pilot with explicit current-verification requirement |
| LIFE-1 | Bounded institutional-dialogue material and arithmetic-only U.S.-currency examples; broader CFPB life/finance artifacts remain to be selected |

## What Is Ready Now

The repository now has enough locally present, provenance-preserving material to:

1. review the complete source inventory without returning to search;
2. choose the first ordered F1 teaching group;
3. inspect licenses and embedded exclusions from the downloaded artifacts;
4. create bounded `review_only` source packets without bulk-importing a corpus;
5. compare conversational sources without treating any assistant wording as
   Selene's personality or voice; and
6. verify every local artifact before review or extraction.

## What Still Requires Deliberate Selection

Before claiming broad or full curriculum coverage, later source-review work must
still select:

- the remaining elementary units in grade and prerequisite order;
- a coherent first-edition K-12 mathematics progression;
- current science units across elementary, middle, and high school;
- individual OpenStax books and revisions for advanced subjects;
- current CDC health-literacy and CFPB practical-life artifacts;
- rights-cleared primary sources for history and civics;
- a bounded, attributed multilingual selection; and
- non-Western and plural arts/culture sources that complement the current music
  and museum catalog material.

Those are source-depth tasks, not missing-map tasks. They should be completed in
small review batches immediately before the corresponding teaching band rather
than by indiscriminate corpus ingestion.

## Verification

The acquisition utility completed with:

- 43 mirrored sources;
- 133 checked files;
- zero provider acquisition failures;
- zero missing files; and
- zero SHA-256 mismatches.

No conversational probe, stress test, package rebuild, install, teaching action,
or Selene runtime interaction was necessary.
