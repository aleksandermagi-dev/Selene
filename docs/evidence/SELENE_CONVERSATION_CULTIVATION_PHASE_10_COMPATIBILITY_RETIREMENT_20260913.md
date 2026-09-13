# Selene Conversation Cultivation Phase 10 — Compatibility Retirement Audit

Date: 2026-09-13  
Status: complete for the current evidence gate

## Question

Which of the 54 answer kinds classified during the Phase 0 patch-ancestry
audit can now leave legacy-fixture status without losing a capability or
mistaking an exact replay for generalization?

## Decision rule

Age, awkwardness, or the existence of a newer module is not retirement
evidence. A kind may leave the active compatibility ledger only when:

1. a dedicated general typed owner exists;
2. that owner preserves source and epistemic status;
3. changed-entity or paraphrase evidence exercises the intended operation;
4. the route retains its completion and visible-meaning receipts; and
5. removal from legacy classification does not weaken Memory, identity, Vys,
   governance, permission, action, or stopping boundaries.

The audit therefore distinguishes **retiring legacy classification** from
deleting useful code. A bounded general owner can remain in production while
ceasing to be mislabeled as a scenario fallback.

## Full 54-kind disposition

| Family | Count | Kinds | Disposition and reason |
|---|---:|---|---|
| Dedicated current-context inference | 1 | `grounded_current_context_inference` | **Retired from legacy classification.** It is produced by the dedicated Current Context Inference owner, carries typed premise and inference evidence, rejects literal-domain/high-stakes/external-fact requests, and transfers across changed visible contexts. It is not emitted by any of the six fixture-handler functions. |
| Choice, comparison, and revision | 14 | `grounded_everyday_choice_revision`, `grounded_low_stakes_choice`, `grounded_ordered_everyday_choice`, `grounded_reversible_everyday_choice`, `grounded_visible_option_comparison`, `grounded_visible_option_revision`, `local_reversible_check_choice`, `notebook_choice_constraint_revision`, `notebook_choice_from_visible_criterion`, `porch_walk_constraint_revision`, `porch_walk_visible_choice`, `recommendation_revision_condition`, `reversible_trial_recommendation`, `selective_evening_correction` | **Retained.** Session Decision now generalizes explicit alternatives, criteria, revisions, and predictions, but these handlers also contain unproved grammar, authored-preference, local-check, or selective multi-part behavior. Phase 9 proves the shared owner family, not one-for-one replacement of all 14 surfaces. |
| Participation and thread continuity | 8 | `acknowledgement_and_small_next_step`, `deliberately_open_table_question`, `grounded_confirm_receipt`, `multi_part_porch_and_drink`, `ordered_thread_synthesis`, `returned_corrected_drawer_log`, `returned_table_moisture_answer`, `three_field_observation_log` | **Retained.** Typed acknowledgement, recap, humor, and closure transfer, but the content-bearing thread returns, open-question lifecycle, numbered reconstruction, and combined suggestion semantics have not all received independent changed-entity evidence. |
| Observation, hypothesis, conflict, and checking | 11 | `bounded_check_approach`, `bounded_provisional_cause`, `bounded_tea_prediction`, `changed_and_stable_property`, `controlled_garden_observation`, `corrected_screen_flicker_reading`, `grounded_conflicting_reports`, `observation_interpretation_next_check`, `prompt_grounded_next_check_direction`, `provisional_discriminating_observation`, `visible_observation_hypothesis_and_alternative` | **Retained.** Exploratory reasoning, prediction, and epistemic-state owners exist, but several handlers still embed domain-specific observation vocabularies or multi-operation completion that has not been replaced one-for-one. |
| Desk, table, layout, and spatial handling | 10 | `bounded_spatial_relation`, `bounded_table_layout`, `grounded_desk_comparison`, `grounded_desk_correction`, `grounded_desk_exception_revision`, `grounded_desk_first_step`, `grounded_desk_summary`, `grounded_ordered_desk_plan`, `table_layout_moisture_revision`, `table_layout_revision_reason` | **Retained.** Shared propositions carry entities, properties, and changes, but do not yet prove arbitrary spatial/layout planning, exception preservation, or ordered physical arrangement across changed scenes. |
| Domain explanation and bounded policy | 10 | `accessibility_fairness_application`, `bounded_aesthetic_comparison`, `fair_reversible_resource_sharing`, `fairness_consistency_contextual_distinction`, `fraction_comparison_check_explanation`, `history_purpose_and_example`, `local_code_boundary_follow_up`, `purpose_classification`, `revised_prerequisite_order`, `summary_interpretation_distinction` | **Retained.** These require reviewed domain knowledge, exact local-code authority boundaries, or general explanation/interpretation transfer. A conversational owner alone cannot replace their substance. |

Total: **54 audited = 1 retired + 53 retained**.

## Source repair

`answer_substance.py` now separates the active 53-kind compatibility set from
an explicit retired set. Their union remains the immutable 54-kind audit
baseline. A retired result receives
`general_owner_replacement_verified`, visible retirement evidence, and a true
changed-entity/paraphrase flag. Active compatibility results remain ineligible
as general capability evidence.

The source-level guard is stronger than before: every literal answer kind
emitted by the six classified fixture-handler functions must equal—not merely
be a subset of—the active 53-kind ledger. A new unclassified fallback or a
stale ledger entry now fails the test.

No fixture handler was deleted in this phase. That is deliberate. The audit
found no other one-for-one replacement with sufficient evidence, and deleting
any of the 53 would trade visible code reduction for a real behavioral hole.

## Verification

- 78 affected Answer Substance, Current Context Inference, Answer Operations,
  Conversational Teaching, and exact Chat checks passed.
- The three Phase 9 changed-entity generalization checks remained green.
- Python compilation passed.
- Diff hygiene passed with only the repository's existing Windows line-ending
  notices.
- The resident database was not used for runtime checks or modified. Its
  SHA256 remained byte-for-byte unchanged at
  `4391C45B2BEBD79C09C6A66378B266C2DC64D989708786EB7667FCE8F1C0BF6A`.

These counts establish bounded engineering coverage, not universal language
generalization. The retained kinds remain explicit technical debt with known
owners and an evidence gate, rather than hidden claims of maturity.

## Boundaries

This phase changes compatibility classification and its audit receipts. It
does not change Selene's identity, personality, Vys, values, governance,
Memory, Dream, Study, teaching state, permissions, model parameters, external
authority, perception, or embodiment. All runtime checks used disposable
state. No live Q&A, package, install, or resident write occurred.

## Next

Conversation Cultivation Phase 11 is the integrated stabilization checkpoint:
run the deferred affected and repository verification, confirm resident
integrity without decision-bearing writes, build the frontend, package and
reinstall only with Aleks's explicit approval, then conduct one bounded gentle
Q&A after installation. Compatibility kinds that remain at Phase 11 stay
visible; stabilization is not permission to delete them.
