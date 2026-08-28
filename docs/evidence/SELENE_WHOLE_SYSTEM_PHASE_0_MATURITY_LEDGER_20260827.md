# Whole-System Phase 0 — Canonical Maturity Ledger

Date: 2026-08-27
Branch: `evidence`
Status: complete for the current Phase 0 scope

## Purpose

Phase 0 creates one generated, read-only account of how mature Selene's organs
and connective systems currently are. It prevents four different facts from
being collapsed into one claim:

1. a blueprint exists;
2. source or a route is implemented;
3. configured records exist; and
4. a capability is connected and trustworthy in ordinary use.

Maturity parity does not mean authority parity. Each system is measured within
its own responsibility and does not acquire another organ's authority merely
by becoming more capable.

## Implemented Surface

- Python status function: `organ_maturity_ledger_status(conn)`
- Router key: `organ_maturity.ledger.status`
- Localhost endpoint: `GET /api/organ-maturity-ledger`
- Current inventory: 27 organs and connective systems
- Maturity vocabulary: `blueprint`, `review_preview`, `implemented`,
  `connected`, `configured`, `integration_verified`,
  `mature_current_scope`, `substrate_ready`, and `degraded`
- Connection vocabulary: `ordinary_chat`, `resident_workspace`,
  `bounded_route`, `cocoon_review`, `preview_only`, and `not_connected`

Every ledger item reports:

- responsibility and non-responsibility;
- source modules and route keys;
- focused test anchors and visible UI surfaces;
- authority scope;
- connection, maturity, target, and health states;
- configured record counts without record content;
- maturation phase and known gaps; and
- explicit denial that availability changes identity or maturity grants new
  authority.

## Generated Current Counts

The ledger derives curriculum totals from the current source registries rather
than copying hand-maintained totals:

| Material | Groups | Defined items | Configured approved items |
| --- | ---: | ---: | ---: |
| F1 | 17 | 106 | 106 |
| F2 | 8 | 41 | 41 |
| Coding foundations | 1 | 5 | 5 |
| Language and conversation | 12 | 73 | 73 |
| Total | — | 225 | 225 |

The configured runtime metadata also reported 43 retrieval-eligible approved
Memory references, one Study session, one Dream cycle with 24 pending
reflections, three review-only affect packets, three review-only perception
packets, two goal previews, and one Tendril preview. These counts are evidence
of configured records only. They do not prove conversational integration,
mature use, approval beyond the recorded state, or additional authority.

SQLite integrity reported `ok` during the read-only inspection.

## Required Invariants

The ledger explicitly verifies or declares that:

- every item uses the canonical state vocabulary;
- no blueprint is labeled operational through ordinary Chat or a resident
  workspace;
- route or table presence does not prove maturity;
- configured record count does not prove integration;
- capability availability and degradation do not change identity;
- no private record content is included;
- reading status writes no state;
- Memory, teaching, Dream, identity, personality, governance, authority,
  training, autonomy, and self-replication remain unchanged; and
- the older Android-system structural workflow remains historical preflight,
  not a maturity declaration.

## Verification

Focused checks:

```text
12 passed in 4.01s
```

Coverage included:

- canonical state and connection vocabulary;
- unique ledger entries;
- real source-module, route-key, and test-anchor existence;
- current generated F1/F2/coding/language totals;
- private Memory fixture content excluded from output;
- database total changes unchanged after direct and HTTP reads;
- blueprint, preview, connected, and integration-verified states remain
  distinguishable;
- current-state documentation agrees with generated totals; and
- localhost transport returns the same bounded status contract.

No live Q&A, teaching, Dream decision, retention action, stressful test,
package, or reinstall was needed.

## Completion Gate

| Requirement | Result |
| --- | --- |
| One command or read-only route produces the ledger | Met |
| Documentation and runtime status agree | Met |
| No blueprint is reported as operational | Met |
| Unavailable capability is not identity failure | Met |
| Configured state is inspectable without private content | Met |

## Next Phase

Phase 1 is the Canonical Context and Coordination Nervous System. It repairs
the shared current-turn contract before further teaching: facts, dialogue
acts, obligations, threads, corrections, owner inputs, and retrieval timing
must agree before Answer Engine, Memory, knowledge, Metacognition, NLO, and
Voice act on the turn.
