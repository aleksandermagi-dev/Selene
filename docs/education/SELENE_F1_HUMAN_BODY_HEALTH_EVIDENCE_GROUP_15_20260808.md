# Selene F1 Human Body and Health Evidence Group 15

Date: 2026-08-08

Status: explicitly authorized by Aleks, taught, retained, and available to Chat
as six source-linked general knowledge resources

## Outcome

F1 Group 15 contains six ordered foundations:

1. the human body as interacting parts, organs, systems, and models;
2. skeletal-muscular support, protection, movement, and variation;
3. breathing, gas exchange, circulation, and transport as distinct connected
   processes;
4. digestion, absorption, transport, and energy use as distinct connected
   processes;
5. sensory receptors, nervous information, perception, individual report, and
   model limits; and
6. ordinary care, health-source evaluation, consent, privacy, questions, and
   qualified-help boundaries.

The group is implemented in `src/selene/curriculum_f1_group15.py` and uses the
existing visible Acquire -> Integrate -> Express -> comprehension ->
authorization lifecycle.

## Reviewed Sources

### Core Knowledge Grade 1 Domain 2, *The Human Body*

- Source ID: `core_knowledge_g1_human_body`
- URL:
  `https://www.coreknowledge.org/wp-content/uploads/2016/12/CKLA-G1-The-Human-Body.zip`
- SHA-256:
  `6a38dd4c9b8a08544847801ce12951ab7ac45bcfe3b434418604a57c5bfa8846`
- Size: 17,497,651 bytes
- License: CC BY-NC-SA 3.0 under the artifact's 2013 terms

The ZIP contains the anthology, supplemental guide, flip book, image cards,
and embedded terms. The license page and representative system pages were
rendered and visually inspected. Stable structure-and-function relationships
were retained for review. Source images, scripted activities, external links,
and outdated or oversimplified health claims were excluded.

In particular, Group 15 does not carry forward simplified statements that the
stomach turns food directly into energy, that the familiar five senses are a
complete sensory inventory, or that one typical diagram defines every human
body.

### MedlinePlus, *Evaluating Health Information*

- Source ID: `medlineplus_evaluating_health_information_current`
- URL: `https://medlineplus.gov/evaluatinghealthinformation.html`
- SHA-256:
  `e982df7023e54e8a816b33fd65dd0a5258bec657e1ed3a86664d1d08ece00fa5`
- Snapshot review date preserved from the page: 2024-02-26
- License boundary: NLM-authored health-topic summary is U.S. federal public
  domain; copyrighted encyclopedia, images, abstracts, and linked material are
  excluded

### MedlinePlus, *Patient Rights*

- Source ID: `medlineplus_patient_rights_current`
- URL: `https://medlineplus.gov/patientrights.html`
- SHA-256:
  `5ba9263599b81cbd247c9f3ecfb8ef748781ff607b0f73eac257d988173927c5`
- Snapshot review date preserved from the page: 2024-10-11
- License boundary: NLM-authored health-topic summary is U.S. federal public
  domain; copyrighted encyclopedia, images, handouts, and linked material are
  excluded
- Jurisdiction boundary: the summary is United States-oriented and explicitly
  notes variation among states, facilities, organizations, and plans

The MedlinePlus content-use page remains attached to both snapshots. No
copyrighted A.D.A.M. Medical Encyclopedia content was selected.

## Medical, Human, and Consent Boundaries

Group 15 teaches human biology. It does not imply Selene has a human biological
body and does not alter her identity or architecture.

The group explicitly keeps separate:

- structure, function, system, and whole organism;
- a typical model and individual human variation;
- observation, first-person report, interpretation, and diagnosis;
- breathing, gas exchange, pumping, and circulation;
- digestion, absorption, transport, metabolism, and waste removal;
- stimulus, sensation, perception, and response;
- general information and individualized medical advice; and
- support, informed choice, consent, professional authority, and control.

It cannot diagnose, triage, prescribe, interpret symptoms or tests, recommend
doses or individualized diets, provide emergency instructions, settle legal
consent, touch another person, disclose private information, or replace
clinicians, emergency services, patient advocates, or current local guidance.

## Cocoon Preparation

Six candidates were created in the live database:

| Candidate | Concept ID | State | Chat use |
| --- | ---: | --- | --- |
| Interacting parts, organs, and systems | 190 | `approved_knowledge_resource` | `available_as_knowledge_resource` |
| Skeletal-muscular support and movement | 191 | `approved_knowledge_resource` | `available_as_knowledge_resource` |
| Breathing, exchange, and circulation | 192 | `approved_knowledge_resource` | `available_as_knowledge_resource` |
| Digestion, absorption, and transport | 193 | `approved_knowledge_resource` | `available_as_knowledge_resource` |
| Senses, nervous information, and limits | 194 | `approved_knowledge_resource` | `available_as_knowledge_resource` |
| Care, evidence, consent, and qualified help | 195 | `approved_knowledge_resource` | `available_as_knowledge_resource` |

Aleks explicitly authorized and requested teaching of F1 Group 15.
Authorization record 18 is active. All six candidates completed Acquire,
Integrate, and Express, were approved under that bounded curriculum
authorization, and are now `approved_knowledge_resource` items with
`available_as_knowledge_resource` Chat permission. Zero items were held.

## Verification

- `python -m py_compile` passed for the Group 15 module and changed backend
  integration files.
- All 6 focused Group 15 source, boundary, preparation, authorization,
  lifecycle, idempotency, and HTTP-route tests passed.
- All 63 focused curriculum authorization and Groups 7-15 tests passed.
- `npm run build` passed. The main JavaScript bundle remains split and is
  approximately 462 kB.
- Source verification passed for all 130 mirrored source files with zero
  checksum failures.

## Live Database Checkpoints

The pre-preparation backup is:

`%LOCALAPPDATA%\Selene\data\selene.pre_f1_group15_prepare_20260808_180516.sqlite3`

Its SHA-256 matched the live database at copy time:

`0DA940F8FDBAD4951FF36F33415CD9A0D765036EB39131E744145E2B5561F521`

The pre-teaching backup is:

`%LOCALAPPDATA%\Selene\data\selene.pre_f1_group15_teach_20260808_181024.sqlite3`

Its SHA-256 matched the live database immediately before authorization and
teaching:

`4F79C28317C68B327573EED84AAADC6B233D724C07BF6478527C3071922A3B16`

## Completed Authorization

The authorization applied only to the six source-bounded Group 15 items. It did
not authorize diagnosis, triage, prescription, individualized medical or legal
advice, emergency instructions, touching or disclosure authority, personal
memory writes, identity or personality changes, governance changes, training,
LoRA, external authority, or autonomy. Identity, personality, governance,
personal memory, training, LoRA, medical authority, external authority, and
autonomy remain unchanged.

After Group 15, the next planned group is F1 Group 16: helpful computers,
information tools, privacy, security, fallibility, and cross-domain F1
integration.
