# Selene Curriculum Source Shelf

Date: 2026-07-19; expanded 2026-07-29 for F1 Group 6

Status: source acquisition checkpoint; review only

Companion map: `docs/SELENE_FOUNDATIONAL_CURRICULUM_MAP_20260719.md`

## Outcome

The first curriculum source shelf is present locally under:

`local-data/curriculum_sources_20260719/`

The shelf contains:

- 42 cataloged source candidates;
- 31 locally mirrored, revision- or checksum-pinned sources;
- 121 verified files;
- approximately 1.34 GB of source artifacts;
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
| CKHG Grade 1 Lessons in Civics | Artifact SHA-256 | Community, rules, laws, fairness, citizenship, and historical examples | U.S. jurisdiction must remain explicit; add plural perspectives |
| CKLA Grade 1 The Human Body | Artifact SHA-256 | Body systems, care, germs, disease, vaccines, and health vocabulary pilot | Older health material requires current-source verification; never medical advice |
| Code.org Computer Science Fundamentals | Artifact SHA-256 | Ordered instructions, repetition, testing, and debugging pilot | Preserve CC-BY-NC-SA attribution; exclude branded media and keep execution authority separate |

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
| SCI-0 through SCI-3 | K-8 sequence, Grade 1 science-method pilot, human-body pilot, research handbook, and EXAMS inventory |
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

- 31 mirrored sources;
- 121 checked files;
- zero provider acquisition failures;
- zero missing files; and
- zero SHA-256 mismatches.

No conversational probe, stress test, package rebuild, install, teaching action,
or Selene runtime interaction was necessary.
