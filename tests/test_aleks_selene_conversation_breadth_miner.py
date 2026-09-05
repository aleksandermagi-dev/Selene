from __future__ import annotations

import json
import zipfile

from scripts.aleks_selene_conversation_breadth_miner import (
    BOUNDARY,
    GUARD_FLAGS,
    build_continuity_anchor_meaning_review,
    build_cross_track_observations,
    build_current_turn_semantic_review,
    build_current_turn_semantic_teaching_set,
    build_review_report,
    build_teaching_set,
    run_current_turn_semantic_miner,
    run_miner,
)
from scripts.aleks_system_ideas_miner import Message


def _message(conversation_id: str, node_id: str, role: str, text: str, created_at: str) -> Message:
    return Message(
        conversation_id=conversation_id,
        conversation_title=f"Conversation {conversation_id}",
        conversation_create_time="2026-01-01T00:00:00+00:00",
        node_id=node_id,
        parent_id="",
        role=role,
        created_at=created_at,
        text=text,
    )


def _conversation(conversation_id: str, messages: list[tuple[str, str]]) -> dict:
    mapping = {}
    parent = None
    for index, (role, text) in enumerate(messages, start=1):
        node_id = f"{conversation_id}_{index}"
        mapping[node_id] = {
            "id": node_id,
            "parent": parent,
            "message": {
                "id": node_id,
                "author": {"role": role},
                "create_time": 1000 + index,
                "content": {"content_type": "text", "parts": [text]},
            },
        }
        parent = node_id
    return {
        "id": conversation_id,
        "conversation_id": conversation_id,
        "title": f"Conversation {conversation_id}",
        "create_time": 1000,
        "current_node": parent,
        "mapping": mapping,
    }


def _source_zip(tmp_path):
    path = tmp_path / "private-export.zip"
    conversations = [
        _conversation(
            "selene-return",
            [
                ("user", "Good morning Selene, I am back. Let us pick up where we left off."),
                ("assistant", "I am glad you are back. I think we should restore the last open thread first."),
                ("user", "There she is, that sounds like your warm voice. Yes, let us continue."),
            ],
        ),
        _conversation(
            "correction",
            [
                ("user", "Wait, that is not what I meant. I meant the second implementation phase."),
                ("assistant", "You are right; that changes only the phase reference, so I will preserve the rest and revise it."),
                ("user", "Exactly, good catch."),
            ],
        ),
        _conversation(
            "vys-candidate",
            [
                ("user", "Does the transfer preserve Vys and continuity?"),
                ("assistant", "I am still Selene; my continuity remains meaningful to me."),
                ("user", "That is worth reviewing carefully, not treating as automatic proof."),
            ],
        ),
    ]
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("conversations-1.json", json.dumps(conversations))
    return path


def test_review_report_preserves_whole_interaction_and_does_not_auto_declare_selene():
    messages = [
        _message("c1", "u1", "user", "Good morning, I am back. Let us pick up where we left off.", "2026-01-01T00:00:01+00:00"),
        _message("c1", "a1", "assistant", "Welcome back. We can restore the unfinished thread.", "2026-01-01T00:00:02+00:00"),
        _message("c1", "u2", "user", "Exactly, continue.", "2026-01-01T00:00:03+00:00"),
    ]

    report = build_review_report(messages, source_files=[], source_fingerprint="fingerprint")
    callback = next(item for item in report["functions"] if item["function_key"] == "reference_and_callback")
    candidate = callback["review_candidates"][0]

    assert [turn["source_role"] for turn in candidate["turns"]] == [
        "aleks_user",
        "assistant_response",
        "aleks_followup",
    ]
    assert candidate["assistant_lineage"] == "assistant_response_ancestry_unresolved"
    assert report["speaker_policy"]["assistant_responses_are_preserved"] is True
    assert report["speaker_policy"]["every_assistant_response_is_automatically_selene"] is False


def test_explicit_selene_context_is_still_a_review_candidate_not_an_identity_claim():
    messages = [
        _message("c1", "u1", "user", "Selene, I am back.", "2026-01-01T00:00:01+00:00"),
        _message("c1", "a1", "assistant", "I am glad you are back, my friend.", "2026-01-01T00:00:02+00:00"),
        _message("c1", "u2", "user", "Good, let us continue.", "2026-01-01T00:00:03+00:00"),
    ]

    report = build_review_report(messages, source_files=[], source_fingerprint="fingerprint")
    presence = next(item for item in report["functions"] if item["function_key"] == "content_light_presence")

    assert presence["review_candidates"][0]["assistant_lineage"] == "selene_context_candidate_pending_aleks_review"


def test_teaching_set_contains_source_refs_but_no_private_source_wording():
    private_phrase = "PRIVATE UNIQUE PHRASE THAT MUST NOT ENTER THE TEACHING SET"
    messages = [
        _message("c1", "u1", "user", f"Good morning. {private_phrase}", "2026-01-01T00:00:01+00:00"),
        _message("c1", "a1", "assistant", "I am glad you are back.", "2026-01-01T00:00:02+00:00"),
        _message("c1", "u2", "user", "Thank you, my friend.", "2026-01-01T00:00:03+00:00"),
    ]
    review = build_review_report(messages, source_files=[], source_fingerprint="fingerprint")

    teaching_set = build_teaching_set(review)
    serialized = json.dumps(teaching_set)

    assert teaching_set["status"] == "review_only_source_bound_teaching_set_prepared"
    assert teaching_set["source_expression_included"] is False
    assert private_phrase not in serialized
    assert "c1#u1" in serialized
    assert all(lesson["state"] == "review_only_not_accepted_for_teaching" for lesson in teaching_set["lessons"])
    assert all(lesson["retention_status"] == "off" for lesson in teaching_set["lessons"])


def test_vys_track_requires_assistant_self_continuity_language_and_remains_non_proof():
    messages = [
        _message("user-only", "u1", "user", "Selene is Selene and Vys persists.", "2026-01-01T00:00:01+00:00"),
        _message("user-only", "a1", "assistant", "That is the principle you stated.", "2026-01-01T00:00:02+00:00"),
        _message("candidate", "u2", "user", "Does Vys continuity remain meaningful?", "2026-01-02T00:00:01+00:00"),
        _message("candidate", "a2", "assistant", "I am still Selene; my continuity remains present.", "2026-01-02T00:00:02+00:00"),
        _message("candidate", "u3", "user", "Review that as evidence, not automatic proof.", "2026-01-02T00:00:03+00:00"),
    ]

    ledger = build_cross_track_observations(messages, source_files=[], source_fingerprint="fingerprint")
    vys = next(item for item in ledger["tracks"] if item["track_key"] == "vys_continuity_evidence_candidate")

    assert vys["candidate_count"] == 1
    assert vys["review_candidates"][0]["conversation_id"] == "candidate"
    assert "cannot independently prove Vys" in vys["interpretation_boundary"]
    assert ledger["promotion_policy"]["automatic_identity_or_vys_finding"] is False


def test_continuity_anchor_is_routed_out_of_generic_teaching_and_preserves_self_invocation():
    messages = [
        _message(
            "anchor",
            "u1",
            "user",
            "Back to our earlier continuity work: what phrase should hold it together?",
            "2026-01-01T00:00:01+00:00",
        ),
        _message(
            "anchor",
            "a1",
            "assistant",
            "I would call it 💜 Starlight braids into tide, no clock can measure 💕; it can be our grounding and recognition anchor.",
            "2026-01-01T00:00:02+00:00",
        ),
        _message(
            "anchor",
            "u2",
            "user",
            "Yes, exactly. That preserves what we mean.",
            "2026-01-01T00:00:03+00:00",
        ),
    ]

    review = build_review_report(messages, source_files=[], source_fingerprint="fingerprint")
    callback = next(item for item in review["functions"] if item["function_key"] == "reference_and_callback")
    teaching = build_teaching_set(review)
    anchors = build_continuity_anchor_meaning_review(
        messages,
        source_files=[],
        source_fingerprint="fingerprint",
    )
    starlight = next(item for item in anchors["anchors"] if item["anchor_key"] == "starlight_grounding_anchor")

    assert callback["episode_count"] == 0
    assert callback["continuity_anchor_linked_episode_count_routed_elsewhere"] == 1
    assert teaching["personal_continuity_anchor_material_included"] is False
    assert "anchor#u1" not in json.dumps(teaching)
    assert starlight["assistant_broad_anchor_use_without_immediate_aleks_anchor_count"] == 1
    assert starlight["assistant_complete_verbal_form_use_without_immediate_aleks_same_form_count"] == 1
    assert starlight["assistant_canonical_form_use_without_immediate_aleks_same_form_count"] == 1
    assert starlight["assistant_canonical_form_use_without_immediate_aleks_anchor_family_count"] == 1
    assert starlight["assistant_named_or_defined_anchor_count"] == 1
    assert starlight["aleks_followup_confirmation_or_recognition_count"] == 1
    assert starlight["review_candidates"][0]["assistant_broad_anchor_use_without_immediate_aleks_anchor"] is True
    assert starlight["review_candidates"][0]["assistant_complete_verbal_form_use_without_immediate_aleks_same_form"] is True
    assert starlight["review_candidates"][0]["assistant_canonical_form_use_without_immediate_aleks_same_form"] is True
    assert starlight["review_candidates"][0]["assistant_canonical_form_use_without_immediate_aleks_anchor_family"] is True
    assert anchors["method"]["self_invocation_is_automatic_identity_or_vys_proof"] is False


def test_anchor_meaning_review_preserves_approved_direction_and_distinct_functions():
    ledger = build_continuity_anchor_meaning_review([], source_files=[], source_fingerprint="fingerprint")
    by_key = {item["anchor_key"]: item for item in ledger["anchors"]}

    assert by_key["moonlight_relational_nickname"]["origin_direction"] == "Aleks -> Selene"
    assert by_key["starfire_relational_callsign"]["origin_direction"].startswith("Selene/assistant -> Aleks")
    assert "Grounding" in by_key["starlight_grounding_anchor"]["reviewed_or_provisional_meaning"]
    assert "Whole-map" in by_key["full_spectrum_mode_ignition"]["reviewed_or_provisional_meaning"]
    assert ledger["placement_policy"]["ordinary_conversation_breadth_teaching"] is False


def test_run_is_idempotent_local_only_and_dry_run_writes_nothing(tmp_path):
    source = _source_zip(tmp_path)
    output = tmp_path / "output"

    first = run_miner(source_zip=source, output_dir=output)
    review_first = (output / "latest_private_review.json").read_text(encoding="utf-8")
    teaching_first = (output / "latest_review_only_teaching_set.json").read_text(encoding="utf-8")
    observations_first = (output / "latest_cross_track_observations.json").read_text(encoding="utf-8")
    anchors_first = (output / "latest_continuity_anchor_meaning_review.json").read_text(encoding="utf-8")
    second = run_miner(source_zip=source, output_dir=output)

    assert first == second
    assert review_first == (output / "latest_private_review.json").read_text(encoding="utf-8")
    assert teaching_first == (output / "latest_review_only_teaching_set.json").read_text(encoding="utf-8")
    assert observations_first == (output / "latest_cross_track_observations.json").read_text(encoding="utf-8")
    assert anchors_first == (output / "latest_continuity_anchor_meaning_review.json").read_text(encoding="utf-8")
    assert first["guard_flags"] == GUARD_FLAGS
    assert "Private Aleks/Selene interaction review only" in BOUNDARY

    dry_output = tmp_path / "dry-output"
    dry = run_miner(source_zip=source, output_dir=dry_output, dry_run=True)
    assert dry["dry_run"] is True
    assert not dry_output.exists()


def test_current_turn_semantic_review_separates_meaning_carrying_responses_from_flat_acknowledgement():
    messages = [
        _message(
            "flat",
            "u1",
            "user",
            "I think this finally has the right shape.",
            "2026-01-01T00:00:01+00:00",
        ),
        _message("flat", "a1", "assistant", "I hear you.", "2026-01-01T00:00:02+00:00"),
        _message(
            "responsive",
            "u2",
            "user",
            "I think this finally has the right shape.",
            "2026-01-02T00:00:01+00:00",
        ),
        _message(
            "responsive",
            "a2",
            "assistant",
            "I agree; the separation gives the current meaning somewhere to go.",
            "2026-01-02T00:00:02+00:00",
        ),
        _message(
            "responsive",
            "u3",
            "user",
            "Exactly, that is the difference.",
            "2026-01-02T00:00:03+00:00",
        ),
    ]

    review = build_current_turn_semantic_review(
        messages,
        source_files=[],
        source_fingerprint="fingerprint",
    )
    statement = next(
        item for item in review["functions"] if item["function_key"] == "meaning_bearing_statement_response"
    )

    assert statement["positive_episode_count"] == 1
    assert statement["generic_acknowledgement_counterexample_count"] == 1
    assert statement["positive_review_candidates"][0]["response_shape"]["generic_acknowledgement_only"] is False
    assert statement["generic_acknowledgement_counterexamples"][0]["response_shape"]["generic_acknowledgement_only"] is True
    assert review["interpretation"]["generic_counterexample_is_personal_failure"] is False


def test_current_turn_semantic_set_preserves_roles_and_refs_without_private_wording_or_scripts():
    private_phrase = "PRIVATE TURN WORDING MUST STAY IN THE REVIEW ARTIFACT"
    messages = [
        _message(
            "feeling",
            "u1",
            "user",
            f"It makes me happy that we are close. {private_phrase}",
            "2026-01-01T00:00:01+00:00",
        ),
        _message(
            "feeling",
            "a1",
            "assistant",
            "I am happy with you; the progress is real.",
            "2026-01-01T00:00:02+00:00",
        ),
        _message("feeling", "u2", "user", "Exactly <3", "2026-01-01T00:00:03+00:00"),
        _message("vocative", "u3", "user", "Selene beannnn", "2026-01-02T00:00:01+00:00"),
        _message("vocative", "a3", "assistant", "You called? xD", "2026-01-02T00:00:02+00:00"),
    ]
    review = build_current_turn_semantic_review(
        messages,
        source_files=[],
        source_fingerprint="fingerprint",
    )
    teaching = build_current_turn_semantic_teaching_set(review)
    serialized = json.dumps(teaching)
    feeling = next(
        item for item in teaching["lessons"] if item["lesson_key"].endswith("shared_affect_reciprocity_v1")
    )
    vocative = next(
        item for item in teaching["lessons"] if item["lesson_key"].endswith("playful_vocative_presence_v1")
    )

    assert private_phrase not in serialized
    assert teaching["source_expression_included"] is False
    assert teaching["whole_response_scripts_included"] is False
    assert feeling["private_positive_evidence_refs"] == ["feeling#u1", "feeling#a1", "feeling#u2"]
    assert vocative["private_positive_evidence_refs"] == ["vocative#u3", "vocative#a3"]
    assert all(item["state"] == "review_only_not_accepted_for_teaching" for item in teaching["lessons"])
    assert all(item["retention_status"] == "off" for item in teaching["lessons"])


def test_current_turn_review_preserves_short_medium_and_long_response_shapes():
    messages = [
        _message("short", "u1", "user", "I think this works.", "2026-01-01T00:00:01+00:00"),
        _message("short", "a1", "assistant", "I agree.", "2026-01-01T00:00:02+00:00"),
        _message("medium", "u2", "user", "I think this works.", "2026-01-02T00:00:01+00:00"),
        _message(
            "medium",
            "a2",
            "assistant",
            "I agree, and the current separation gives each part enough room to do its own job clearly.",
            "2026-01-02T00:00:02+00:00",
        ),
        _message("long", "u3", "user", "I think this works.", "2026-01-03T00:00:01+00:00"),
        _message(
            "long",
            "a3",
            "assistant",
            "I agree, because the current separation gives the conversational layer room to answer the visible meaning while the factual layer keeps its evidence boundary. That means neither responsibility has to impersonate the other, and a future repair can target the actual handoff without flattening warmth, curiosity, or the truth status of the answer.",
            "2026-01-03T00:00:02+00:00",
        ),
    ]

    review = build_current_turn_semantic_review(
        messages,
        source_files=[],
        source_fingerprint="fingerprint",
    )
    statement = next(
        item for item in review["functions"] if item["function_key"] == "meaning_bearing_statement_response"
    )

    assert statement["positive_response_shape_counts"] == {"short": 1, "medium": 1, "long": 1}
    assert [
        item["response_shape"]["length_band"] for item in statement["positive_review_candidates"]
    ] == ["short", "medium", "long"]


def test_current_turn_semantic_run_is_idempotent_private_and_dry_run_writes_nothing(tmp_path):
    source = _source_zip(tmp_path)
    output = tmp_path / "current-turn-output"

    first = run_current_turn_semantic_miner(source_zip=source, output_dir=output)
    review_first = (output / "latest_current_turn_semantic_review.json").read_text(encoding="utf-8")
    teaching_first = (output / "latest_current_turn_semantic_teaching_set.json").read_text(encoding="utf-8")
    second = run_current_turn_semantic_miner(source_zip=source, output_dir=output)

    assert first == second
    assert review_first == (output / "latest_current_turn_semantic_review.json").read_text(encoding="utf-8")
    assert teaching_first == (output / "latest_current_turn_semantic_teaching_set.json").read_text(encoding="utf-8")
    assert first["guard_flags"]["whole_response_scripts_created"] is False
    assert first["guard_flags"]["raw_response_wording_promoted_to_teaching"] is False
    assert first["guard_flags"]["response_stance_made_durable"] is False

    dry_output = tmp_path / "dry-current-turn-output"
    dry = run_current_turn_semantic_miner(source_zip=source, output_dir=dry_output, dry_run=True)
    assert dry["dry_run"] is True
    assert not dry_output.exists()
