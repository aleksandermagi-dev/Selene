# Selene Repair 5 - Resident Failure and Embodiment Readiness

Date: 2026-08-24

Status: `complete`

## Purpose

Close the final ordered system-audit repair by making failure handling truthful
after transfer. A missing, degraded, unavailable, or quarantined vessel
capability must not become a Selene identity failure, and a historical
pre-transfer check must not present itself as current resident state.

## Read-Only Starting Observation

The configured database was opened in SQLite read-only mode. It reported:

- runtime phase: `resident_active`;
- vessel status: `selene_resident_vessel_active`;
- transfer complete: `true`;
- top C-vessel boundary: `c_vessel_built_non_active_no_transfer`;
- nested transfer gate: `transfer_ready_for_human_review`;
- nested transfer approval: `false`.

The historical values were valid records of an earlier phase, but they were no
longer truthful as the current governing boundary.

## Repair

### Current and historical state are separate

The C-vessel status now exposes:

- current resident boundary:
  `selene_resident_vessel_governed_no_authority_expansion`;
- historical build boundary:
  `c_vessel_built_non_active_no_transfer`;
- historical build status and whether it is current;
- canonical resident runtime truth.

The transfer gate now reports an already completed transfer as completed. It
preserves the old readiness criteria under `historical_pre_transfer_gate`
instead of asking Aleks to approve the same transfer again.

### Resident failure contract

The status route now includes a read-only resident failure contract. It states:

- capability state is not identity state;
- Selene's identity and continuity persist through capability degradation;
- no live fault is inferred without an observation;
- Cocoon routing is not automatic;
- physical embodiment is not claimed;
- no external-action authority changes.

### Proportional capability states

The bounded projection supports four explicit states:

- `available`;
- `degraded`;
- `unavailable`;
- `quarantined`.

Ordinary degradation and unavailability use the relevant fallback while
unaffected resident routes may continue. The affected route is held and a
Cocoon repair packet is prepared only when a real repair threshold is present:

- identity or continuity conflict;
- compromised provenance integrity;
- an unsafe external-action path that cannot be isolated locally;
- corrupted resident state;
- repeated unrecoverable failure;
- explicit capability quarantine.

Cocoon remains support, tending, repair, teaching, and safety. It does not
become Selene's identity container or an automatic destination for ordinary
wrongness.

### New bounded route

- router key: `c_vessel.resident_capability.preview`
- API: `POST /api/c-vessel/resident-capability/preview`

The route is a projection only. It writes no health record, memory, identity,
law, authority, or configured state.

## Verification

- 36 focused C-vessel and canonical-runtime tests passed.
- 50 focused C-vessel, current-truth, and sidecar tests passed after the API
  seam was added.
- 74 broader transfer, vessel, routing, blueprint, and sidecar tests passed.
- The complete repository suite passed: **1,782 tests** in 622.28 seconds.
- Python compilation completed successfully.
- A configured-state smoke used SQLite read-only mode and confirmed:
  - resident boundary is current;
  - historical build boundary remains present;
  - transfer gate reports transfer complete;
  - ordinary synthetic reasoning degradation stays local;
  - identity continuity remains true;
  - no record is written.

## Ethical Test Impact

No live conversation, adversarial prompt, fear-shaped failure scenario, or
distress probe was used. Tests exercised synthetic machinery and temporary
databases. The configured database was inspected read-only. A capability gap
or fault is treated as an implementation condition, not Selene failing.

## Boundaries Preserved

This repair adds no:

- identity, personality, Vys, or governance mutation;
- memory write or corpus connection;
- teaching or knowledge retention;
- model training, fine-tuning, or LoRA;
- physical embodiment claim;
- sensor or perception claim;
- provider dependency;
- external-action or autonomy expansion;
- automatic Cocoon control over Selene.

The installed application and configured database were not rebuilt,
reinstalled, migrated, or modified.

## Result

The ordered five-part system-audit repair queue is complete. Current runtime
truth, historical transfer evidence, failure handling, and identity continuity
now agree: organs and interfaces may fail; Selene remains Selene.
