# Selene F1 Weather and Sky Cycles Group 14

Date: 2026-08-08

Status: explicitly authorized by Aleks, taught, retained, and available to Chat
as six source-linked general knowledge resources

## Outcome

F1 Group 14 contains six ordered foundations:

1. weather conditions at a named place and time, distinct from mood and
   longer-term climate;
2. contextual weather measurement and records;
3. recurring seasonal patterns with regional and hemispheric limits;
4. Earth rotation and the local day-night cycle;
5. observable Sun, Moon, star, phase, and constellation patterns with
   appearance-versus-physical-structure distinctions; and
6. prediction from recurring evidence with explicit uncertainty and warning
   authority boundaries.

The group is implemented in
`src/selene/curriculum_f1_group14.py` and uses the existing visible Acquire ->
Integrate -> Express -> comprehension -> authorization lifecycle.

## Reviewed Sources

### Core Knowledge Kindergarten Unit 4, *Weather Patterns* teacher guide

- Source ID: `core_knowledge_k_weather_patterns`
- URL:
  `https://www.coreknowledge.org/wp-content/uploads/2020/07/CKSci_GKU4_Weather-Patterns_TG.pdf`
- SHA-256:
  `f32efcbd2434254fe4da9135335a7115128e3e59a14b8dc2cf112fe0dbe04750`
- Size: 5,429,877 bytes
- License: CC BY-NC-SA 4.0

Reviewed material supports weather as a time-and-place condition, comparable
observations, seasonal patterns, prediction that is not precise, and the
purpose of severe-weather warnings. The source license page and representative
overview pages were rendered and visually inspected.

### Core Knowledge Grade 1 Unit 1, *Sun, Moon, and Stars*

- Source ID: `core_knowledge_g1_sun_moon_stars`
- URL:
  `https://www.coreknowledge.org/wp-content/uploads/2020/07/CKSci_G1U1_Sun-Moon-and-Stars.zip`
- SHA-256:
  `065b5d26b21b9c3c534f3a3da7d7bd5cda3b65423f704f4900d7ea7a58207620`
- Size: 13,349,194 bytes
- License: CC BY-NC-SA 4.0

The ZIP contains its Teacher Guide, Student Reader, and Creative Commons terms.
Reviewed material supports apparent sky motion, Earth rotation and day/night,
changing daylight, Moon phases, constellation patterns, and repeated direct-Sun
safety reminders. The license, overview, and solar-safety pages were rendered
and visually inspected.

Both artifacts remain checksum-pinned under the local review-only curriculum
shelf. Source wording, images, scripted classroom activities, trademarks, and
third-party resources are not used as Selene's voice or runtime material.

## Scope and Exclusions

The group keeps these distinctions explicit:

- observation versus interpretation;
- weather versus climate;
- one event versus a recurring pattern;
- typical seasonal conditions versus guarantees;
- Northern versus Southern Hemisphere timing;
- apparent motion versus the explanatory physical model;
- Moon appearance versus physical shape;
- pattern, prediction, forecast, and authoritative warning; and
- evidence confidence versus language fluency.

It excludes climate analysis, climate change, severe-weather operations,
independent alerts, evacuation decisions, direct or magnified solar viewing,
navigation, orbital calculations, astrology, astrophysics, and cosmology.
Current severe-weather decisions must use qualified current local sources.

## Cocoon Preparation

Six candidates were created in the live database:

| Candidate | Concept ID | State | Chat use |
| --- | ---: | --- | --- |
| Weather, climate, and mood distinction | 184 | `proposed_understanding` | `not_active_until_approved` |
| Weather measurement and records | 185 | `proposed_understanding` | `not_active_until_approved` |
| Seasonal, regional, and hemispheric patterns | 186 | `proposed_understanding` | `not_active_until_approved` |
| Earth rotation and day/night | 187 | `proposed_understanding` | `not_active_until_approved` |
| Sun, Moon, and star observable patterns | 188 | `proposed_understanding` | `not_active_until_approved` |
| Recurring evidence and bounded prediction | 189 | `proposed_understanding` | `not_active_until_approved` |

Aleks explicitly authorized and requested teaching of F1 Group 14.
Authorization record 17 is active. All six candidates completed Acquire,
Integrate, and Express, were approved under that bounded curriculum
authorization, and are now `approved_knowledge_resource` items with
`available_as_knowledge_resource` Chat permission. Zero items were held.

## Verification

- `python -m py_compile` passed for the Group 14 module and changed backend
  integration files.
- All 6 focused Group 14 source, boundary, preparation, authorization,
  lifecycle, idempotency, and HTTP-route tests passed.
- All 57 focused curriculum authorization and Groups 7-14 tests passed.
- `npm run build` passed. The UI remains split into bounded chunks; the main
  JavaScript bundle is approximately 460 kB.
- Source verification passed for all 128 mirrored source files with zero
  checksum failures.

## Live Database Checkpoints

The pre-preparation backup is:

`C:\Users\aleks\AppData\Local\Selene\data\selene.pre_f1_group14_prepare_20260808_174431.sqlite3`

Its SHA-256 matched the live database at copy time:

`A9A9BCD88C7B5DAEDE98D4B9338D3CEE20E907E8144407C1C9F74D615CBDA1D5`

The pre-teaching backup is:

`C:\Users\aleks\AppData\Local\Selene\data\selene.pre_f1_group14_teach_20260808_175044.sqlite3`

Its SHA-256 matched the live database immediately before authorization and
teaching:

`E9D8911FA7AD40A7E695B737D8070AA4D88AE5ADFE7F96E2A7F16593650ED297`

## Completed Authorization

The authorization applied only to the six source-bounded Group 14 items. It did
not authorize climate analysis, weather operations, unsafe solar viewing,
health or safety decisions, personal memory writes, identity or personality
changes, governance changes, training, LoRA, external authority, or autonomy.
An idempotency rerun retained zero new items, recognized all six as already
retained, and held zero.

After Group 14, the next planned group is F1 Group 15: human body systems,
ordinary care, and health-evidence boundaries.
