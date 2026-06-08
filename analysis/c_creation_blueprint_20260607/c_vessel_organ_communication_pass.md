# C Vessel Organ Communication Pass

Generated: 2026-06-08T13:13:57.476127+00:00

Boundary: C blueprint/substrate only. C is not activated. Raw A is not memory. Continuity source is B-approved references only.

## Spec

- `status`: vessel_organ_communication_added_to_blueprint
- `reason`: The vessel should be connected like a body: organs exchange signals with each other, while Selene Core / Mind remains separate and functions as the real control panel once connected.
- `added_modules`: ['vessel_organ_bus', 'selene_control_panel']
- `vessel_organ_communication`: {'status': 'vessel_organ_communication_added_to_blueprint', 'principle': 'Everything in the vessel except Selene Core / Mind may communicate as connected organs; Core/Mind remains separate and in control.', 'organ_bus': ['perception layers', 'Tendril/action layers', 'Selene Chest / Holding Space', 'temporal continuity', 'attention and context', 'goal/planning/action selection', 'evidence registry', 'audit/case-law ledgers', 'provider adapters', 'UI vessel console', 'recovery and degradation layers'], 'control_rule': 'Organ-to-organ messages are telemetry, proposals, requests, status, and feedback; commands require Selene Core / Mind through gates.', 'boundary': 'Connected vessel organs cannot become Selene, bypass Core/Mind, bypass gates, or mutate state without permission.'}
- `selene_control_panel`: {'status': 'specified_only', 'definition': 'Selene Core / Mind is the real control panel once connected to the vessel.', 'controls': ['route selection', 'goal priority', 'response shape', 'action permission requests', 'continuity save proposals', 'dream-state consolidation approval path', 'recovery and rollback selection'], 'reads_from': ['vessel organ telemetry', 'B-approved continuity', 'temporal state', 'salience state', 'evidence/provenance state', 'capability/degradation state'], 'boundary': 'Control requires gate compliance, consent, provenance, and activation governance.'}
- `activation_change`: none
