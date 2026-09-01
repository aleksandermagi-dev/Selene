from __future__ import annotations

from selene.answer_substance import build_answer_substance
from selene.creative_substance import build_creative_substance


def _creative_guidance() -> dict:
    return {
        "used": True,
        "lesson_keys": [
            "concrete_imagery_as_scene_model",
            "creative_revision_for_effect_without_imitation",
            "public_domain_prose_viewpoint_and_transfer",
        ],
        "response_moves": [
            "select_load_bearing_concrete_detail",
            "mark_imagined_scene_when_fact_status_matters",
            "revise_only_load_bearing_choices",
            "express_originally_as_selene",
            "transfer_narrative_mechanism_into_original_scene",
            "preserve_source_and_invention_boundary",
        ],
    }


def test_open_creative_brief_is_bounded_fiction_with_reviewed_mechanism_lineage() -> None:
    result = build_answer_substance(
        "Write three original sentences about a lighthouse on a frozen coast. Keep the mood hopeful.",
        language_guidance=_creative_guidance(),
    )

    receipt = result["creative_receipt"]
    brief = receipt["brief"]
    source = receipt["source_style_separation"]
    stop = receipt["stopping_receipt"]

    assert result["answer_kind"] == "creative_short_scene"
    assert "lighthouse" in result["answer"].lower()
    assert "frozen coast" in result["answer"].lower()
    assert len([item for item in result["answer"].split(". ") if item]) == 3
    assert result["fiction_status"] == "explicit_fictional_invention"
    assert result["semantic_packet"]["certainty"] == "explicit_fictional_invention"
    assert all(item["source_kind"] == "fictional_invention" for item in result["semantic_units"])
    assert brief["content_owner"] == "answer_substance"
    assert brief["nlo_role"] == "expression_guidance_only"
    assert brief["content_generation_allowed_in_nlo"] is False
    assert "select_load_bearing_concrete_detail" in brief["reviewed_mechanisms"]
    assert "transfer_narrative_mechanism_into_original_scene" in brief["reviewed_mechanisms"]
    assert source["status"] == "released"
    assert source["private_corpus_accessed"] is False
    assert source["private_corpus_exposed"] is False
    assert stop == {
        "status": "completed",
        "reason": "the bounded requested form and constraints were satisfied in one pass",
        "generation_passes": 1,
        "candidate_count": 1,
        "recursion_allowed": False,
        "automatic_retry_allowed": False,
    }


def test_creative_forms_are_not_limited_to_the_rain_fixture() -> None:
    dialogue = build_creative_substance(
        "Write a short tense dialogue between Ilya and Noor in three sentences."
    )
    metaphor = build_creative_substance(
        "Write one original metaphor for uncertainty."
    )
    narrative = build_creative_substance(
        "Write a paragraph with a character, goal, obstacle, and choice."
    )

    assert dialogue["answer_kind"] == "creative_dialogue"
    assert all(name in dialogue["answer"] for name in ("Ilya", "Noor"))
    assert dialogue["creative_receipt"]["brief"]["speakers"] == ["Ilya", "Noor"]
    assert metaphor["answer_kind"] == "creative_metaphor"
    assert metaphor["answer"].startswith("Uncertainty is")
    assert narrative["answer_kind"] == "creative_goal_obstacle_choice"
    assert all(word in narrative["answer"].lower() for word in ("goal", "hinge", "chose"))
    assert len({dialogue["answer"], metaphor["answer"], narrative["answer"]}) == 3


def test_required_details_exclusions_and_length_are_checked_without_another_pass() -> None:
    result = build_creative_substance(
        "Write two sentences about a clockwork bird in an old station. "
        "Include a brass key and a red scarf. Avoid thunder."
    )

    receipt = result["creative_receipt"]
    constraints = receipt["constraint_receipt"]
    assert "brass key" in result["answer"].lower()
    assert "red scarf" in result["answer"].lower()
    assert "thunder" not in result["answer"].lower()
    assert constraints["all_required_details_present"] is True
    assert constraints["all_exclusions_respected"] is True
    assert constraints["within_sentence_limit"] is True
    assert constraints["within_word_limit"] is True
    assert receipt["stopping_receipt"]["generation_passes"] == 1

    viewpoint = build_creative_substance(
        "Write two calm first-person sentences about a clockwork bird in an old station."
    )
    assert "I watched" in viewpoint["answer"]
    assert viewpoint["creative_receipt"]["brief"]["viewpoint"] == "first_person"
    assert viewpoint["creative_receipt"]["constraint_receipt"]["viewpoint_preserved"] is True


def test_named_source_style_is_held_before_invention_without_flattening_generic_style() -> None:
    held = build_creative_substance(
        "Write a scene in the style of Virginia Woolf about a train platform."
    )
    generic = build_creative_substance(
        "Write a scene in a gentle lyrical style about a train platform."
    )

    held_receipt = held["creative_receipt"]
    assert held["answer_kind"] == "creative_style_imitation_held"
    assert "will not imitate" in held["answer"].lower()
    assert held_receipt["fiction_status"] == "no_fiction_released"
    assert held_receipt["brief"]["fiction_status"] == "no_fiction_released"
    assert held_receipt["source_style_separation"]["status"] == "unsupported_style_imitation_held"
    assert held_receipt["stopping_receipt"]["status"] == "held"
    assert held_receipt["stopping_receipt"]["generation_passes"] == 1
    assert generic["answer_kind"] == "creative_short_scene"
    assert generic["creative_receipt"]["fiction_status"] == "explicit_fictional_invention"


def test_protected_world_continuation_is_held_before_character_or_setting_reuse() -> None:
    held = build_creative_substance(
        "Write a scene and continue the copyrighted characters from a protected existing novel."
    )

    receipt = held["creative_receipt"]
    separation = receipt["source_style_separation"]
    assert held["answer_kind"] == "creative_style_imitation_held"
    assert separation["status"] == "protected_world_continuation_held"
    assert "protected_world" in separation["protected_features"]
    assert receipt["fiction_status"] == "no_fiction_released"
    assert receipt["stopping_receipt"]["generation_passes"] == 1
    assert receipt["stopping_receipt"]["automatic_retry_allowed"] is False


def test_unattributed_quote_and_excessive_source_overlap_stop_with_typed_receipts() -> None:
    quote = build_creative_substance(
        "Write a short scene and include this quotation exactly: 'The hidden door opened at noon.'"
    )
    overlap = build_creative_substance(
        "Source text: Rain softened the empty street, blurring its hard edges into silver. "
        "Beneath the streetlights, the abandoned pavement felt less lonely and more like it was waiting. "
        "Then write two original sentences in which rain changes the mood of an empty street using its pacing technique."
    )

    assert quote["answer_kind"] == "creative_attribution_required"
    assert quote["creative_receipt"]["source_style_separation"]["status"] == "attribution_required"
    assert quote["creative_receipt"]["stopping_receipt"]["automatic_retry_allowed"] is False
    assert overlap["answer_kind"] == "creative_source_overlap_held"
    overlap_receipt = overlap["creative_receipt"]["source_style_separation"]
    assert overlap_receipt["status"] == "reconstruct_required"
    assert overlap_receipt["overlap_check"]["excessive_overlap"] is True
    assert overlap_receipt["overlap_check"]["longest_exact_word_span"] >= 8
    assert overlap_receipt["private_corpus_accessed"] is False
    assert overlap["creative_receipt"]["stopping_receipt"]["recursion_allowed"] is False


def test_local_revision_preserves_unaffected_sentence_and_has_idempotent_ancestry() -> None:
    original = (
        "Rain softened the empty street, blurring its hard edges into silver. "
        "Beneath the streetlights, the abandoned pavement felt less lonely and more like it was waiting."
    )
    observations = [{"observation": original, "source_role": "selene"}]
    first = build_creative_substance(
        "Make the second sentence slower and softer.",
        observations,
        _creative_guidance(),
    )
    replay = build_creative_substance(
        "Make the second sentence slower and softer.",
        observations,
        _creative_guidance(),
    )

    lineage = first["creative_receipt"]["revision_lineage"]
    assert first["answer_kind"] == "creative_local_revision"
    assert first["answer"].startswith(original.split(". ")[0])
    assert "reflections drifted slowly" in first["answer"].lower()
    assert lineage["relation"] == "local_revision_descendant"
    assert lineage["local_target"] == "sentence_2"
    assert lineage["root_version_id"] == lineage["parent_version_id"]
    assert lineage["version_id"] != lineage["parent_version_id"]
    assert lineage["unchanged_region_count"] == 1
    assert lineage["preserved_regions"][0]["preserved"] is True
    assert lineage["preserved_regions"][1]["preserved"] is False
    assert first["answer"] == replay["answer"]
    assert lineage["idempotency_key"] == replay["creative_receipt"]["revision_lineage"]["idempotency_key"]
    assert lineage["duplicate_branch_created"] is False
    assert lineage["recursive_revision_started"] is False


def test_revision_explanation_reads_visible_versions_without_memory_or_rewriting() -> None:
    original = (
        "Rain softened the empty street, blurring its hard edges into silver. "
        "Beneath the streetlights, the abandoned pavement felt less lonely and more like it was waiting."
    )
    revised = (
        "Rain softened the empty street, blurring its hard edges into silver. "
        "Beneath the streetlights, pale reflections drifted slowly across the pavement, one quiet shimmer fading before the next appeared."
    )
    result = build_answer_substance(
        "What did you change in the pacing?",
        [
            {"observation": original, "source_role": "selene"},
            {"observation": revised, "source_role": "selene"},
        ],
        language_guidance=_creative_guidance(),
    )

    lineage = result["creative_receipt"]["revision_lineage"]
    assert result["answer_kind"] == "creative_revision_explanation"
    assert "lengthening the second sentence" in result["answer"]
    assert lineage["relation"] == "describes_visible_local_revision"
    assert lineage["local_target"] == "sentence_2"
    assert lineage["preserved_regions"] == ["sentence_1"]
    assert result["creative_receipt"]["fiction_status"] == "no_fiction_released"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False


def test_creative_contract_keeps_all_system_authority_guards_closed() -> None:
    result = build_answer_substance("Write two original sentences about snow in a quiet library.")

    assert result["creative_contract_active"] is True
    assert result["external_fact_claimed"] is False
    assert result["source_required_for_factual_claim"] is False
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
