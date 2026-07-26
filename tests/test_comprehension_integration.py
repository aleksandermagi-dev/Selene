from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["identity_change"] is False
    assert result["governance_change"] is False
    assert result["personality_change"] is False
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def _propose(conn):
    return route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "title": "Orbital eccentricity",
            "domain": "earth_and_space",
            "material": "Orbital eccentricity describes how much an orbit differs from a perfect circle.",
            "principles": ["A value near zero is close to circular.", "Larger values describe more elongated ellipses."],
            "examples": ["Earth has a low orbital eccentricity."],
            "counterexamples": ["Eccentricity is not the same thing as orbital tilt."],
            "limits": ["The value alone does not specify the orientation or period of an orbit."],
            "relationships": ["It is one orbital element among several."],
            "source_refs": ["teaching:earth_and_space:orbital_elements"],
        },
    )["result"]


def _evaluate(conn, concept_id):
    return route_request(
        conn,
        "comprehension.understanding.evaluate",
        {
            "concept_id": concept_id,
            "teach_back": "It is a measure of the shape of an orbit: low values are rounder and higher values are more stretched.",
            "application": "Given two otherwise comparable orbits, the one with eccentricity 0.6 is more elongated than one at 0.05.",
            "limits": ["It does not tell me the orbit's tilt, period, or orientation by itself."],
            "counterexample": "A tilted orbit can still have low eccentricity.",
            "correction_response": "If I confused eccentricity with inclination, I would separate shape from tilt and revise the answer.",
            "source_alignment": True,
        },
    )["result"]


def _teaching_packet(conn, *, review_status="accepted_for_teaching", status="teaching_material_reviewed_non_active"):
    material = conn.execute(
        """
        INSERT INTO b_reviewed_teaching_materials
        (source_candidate_table, source_candidate_id, core_memory_layer, speech_function,
         lesson_type, positive_example, correction_example, when_not_to_use,
         source_refs, provenance_boundary, review_status, status)
        VALUES ('test_teaching_source', 41, 'interaction_memory', 'uncertainty',
                'guided_expression', ?, ?, ?, ?, 'test_review_boundary', ?, ?)
        """,
        (
            "Name what is known, what remains uncertain, and ask naturally when the missing part matters.",
            "Do not invent certainty to avoid appearing incomplete.",
            "Do not use uncertainty language when the evidence is already clear.",
            json.dumps(["teaching:test:uncertainty"]),
            review_status,
            status,
        ),
    )
    packet = conn.execute(
        """
        INSERT INTO b_teaching_packets
        (speech_function, title, material_ids, lesson_json, source_refs,
         provenance_boundary, review_status, status)
        VALUES ('uncertainty', 'Honest uncertainty', ?, ?, ?, 'test_review_boundary',
                'review_only', 'teaching_packet_review_only')
        """,
        (
            json.dumps([int(material.lastrowid)]),
            json.dumps(
                {
                    "positive_examples": ["Name what is known and ask when the missing part matters."],
                    "correction_examples": ["Do not invent certainty to avoid appearing incomplete."],
                    "when_not_to_use": ["Do not hedge when the evidence is already clear."],
                }
            ),
            json.dumps(["teaching:test:uncertainty"]),
        ),
    )
    conn.commit()
    return int(packet.lastrowid)


def test_comprehension_status_is_separate_from_memory_identity_and_governance(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "comprehension.status")["result"]

    assert result["status"] == "comprehension_integration_ready"
    assert result["concept_count"] == 0
    assert result["comprehension_before_fluency"] is True
    assert result["speed_is_success_measure"] is False
    assert result["teaching_material_is_governance"] is False
    _assert_locked(result)


def test_concept_proposal_is_idempotent_and_not_available_to_chat(tmp_path):
    conn = _conn(tmp_path)

    first = _propose(conn)
    second = _propose(conn)

    assert first["created"] is True
    assert first["item"]["state"] == "proposed_understanding"
    assert first["item"]["retention_state"] == "candidate_not_retained"
    assert first["item"]["chat_use_permission"] == "not_active_until_approved"
    assert second["created"] is False
    assert second["item"]["id"] == first["item"]["id"]
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 1
    _assert_locked(first)


def test_accepted_teaching_packet_prepares_one_source_bound_candidate(tmp_path):
    conn = _conn(tmp_path)
    packet_id = _teaching_packet(conn)

    first = route_request(conn, "comprehension.teaching.prepare", {})["result"]
    second = route_request(conn, "comprehension.teaching.prepare", {})["result"]
    item = route_request(conn, "comprehension.concepts.list", {})["result"]["items"][0]

    assert first["created_count"] == 1
    assert first["existing_count"] == 0
    assert second["created_count"] == 0
    assert second["existing_count"] == 1
    assert item["concept_key"] == f"teaching_packet_{packet_id}"
    assert item["state"] == "proposed_understanding"
    assert item["retention_state"] == "candidate_not_retained"
    assert item["chat_use_permission"] == "not_active_until_approved"
    assert "teaching:test:uncertainty" in item["source_refs"]
    assert item["payload"]["source_metadata"]["teaching_packet_id"] == packet_id
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 1
    _assert_locked(first)


def test_teaching_packet_with_superseded_source_is_held_back(tmp_path):
    conn = _conn(tmp_path)
    packet_id = _teaching_packet(
        conn,
        review_status="superseded",
        status="teaching_material_superseded_non_active",
    )

    result = route_request(conn, "comprehension.teaching.prepare", {"packet_ids": [packet_id]})["result"]

    assert result["created_count"] == 0
    assert result["skipped_count"] == 1
    assert result["skipped"][0]["reason"] == "source_material_missing_or_no_longer_accepted"
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0
    _assert_locked(result)


def test_teaching_packet_without_source_provenance_is_held_back(tmp_path):
    conn = _conn(tmp_path)
    packet_id = _teaching_packet(conn)
    conn.execute("UPDATE b_reviewed_teaching_materials SET source_refs = '[]'")
    conn.execute("UPDATE b_teaching_packets SET source_refs = '[]' WHERE id = ?", (packet_id,))
    conn.commit()

    result = route_request(conn, "comprehension.teaching.prepare", {"packet_ids": [packet_id]})["result"]

    assert result["created_count"] == 0
    assert result["skipped_count"] == 1
    assert result["skipped"][0]["reason"] == "packet_has_no_source_refs"
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0
    _assert_locked(result)


def test_surface_copy_does_not_count_as_understanding(tmp_path):
    conn = _conn(tmp_path)
    proposed = _propose(conn)

    result = route_request(
        conn,
        "comprehension.understanding.evaluate",
        {
            "concept_id": proposed["item"]["id"],
            "teach_back": proposed["item"]["central_claim"],
            "application": "A high value would describe a more elongated orbit.",
            "limits": ["It does not specify inclination."],
            "source_alignment": True,
        },
    )["result"]

    assert result["understanding_evidence_sufficient"] is False
    assert result["dimensions"]["reconstruction"]["not_surface_copy"] is False
    assert result["speed_assessed"] is False
    _assert_locked(result)


def test_knowledge_cannot_be_approved_before_understanding_evidence(tmp_path):
    conn = _conn(tmp_path)
    proposed = _propose(conn)

    try:
        route_request(
            conn,
            "comprehension.concepts.decide",
            {"concept_id": proposed["item"]["id"], "action": "approve_knowledge"},
        )
    except ValueError as exc:
        assert "understanding evidence" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("knowledge approval should require understanding evidence")


def test_guided_understanding_can_be_reviewed_and_retained_as_knowledge(tmp_path):
    conn = _conn(tmp_path)
    proposed = _propose(conn)
    evaluated = _evaluate(conn, proposed["item"]["id"])

    approved = route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": proposed["item"]["id"], "action": "approve_knowledge"},
    )["result"]
    packet = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "What does orbital eccentricity tell us about an orbit?",
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
            "dialogue_workspace": {"active_topic": "orbital eccentricity", "pragmatics": {"ambiguity": {"level": "low"}}},
        },
    )["result"]

    assert evaluated["understanding_evidence_sufficient"] is True
    assert evaluated["dimensions"]["application"]["present"] is True
    assert approved["item"]["state"] == "approved_knowledge_resource"
    assert approved["item"]["retention_state"] == "retained_reviewed_knowledge"
    assert approved["item"]["chat_use_permission"] == "available_as_knowledge_resource"
    assert approved["knowledge_resource_active"] is True
    assert packet["understanding_state"] == "approved_concept_available"
    assert packet["knowledge_context"]["available"] is True
    assert packet["knowledge_context"]["memory_source"] is False
    assert packet["knowledge_context"]["governance_source"] is False
    assert "differs from a perfect circle" in packet["knowledge_response_seed"]
    discovery_handoff = packet["structural_discovery_knowledge_handoff"]
    assert discovery_handoff["status"] == "approved_knowledge_links_available"
    assert discovery_handoff["items"][0]["concept_id"] == str(approved["item"]["id"])
    assert discovery_handoff["items"][0]["approved"] is True
    assert discovery_handoff["items"][0]["personal_memory"] is False
    assert discovery_handoff["personal_memory_used"] is False
    assert discovery_handoff["automatic_discovery_claim"] is False
    _assert_locked(approved)
    _assert_locked(packet)


def test_approved_knowledge_why_question_includes_an_explanatory_principle(tmp_path):
    conn = _conn(tmp_path)
    proposed = _propose(conn)
    _evaluate(conn, proposed["item"]["id"])
    route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": proposed["item"]["id"], "action": "approve_knowledge"},
    )

    packet = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "Why does orbital eccentricity help distinguish rounder and more elongated orbits?",
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True, "dialogue_acts": ["question"]},
            "dialogue_workspace": {"active_topic": "orbital eccentricity", "pragmatics": {"ambiguity": {"level": "low"}}},
        },
    )["result"]

    assert packet["knowledge_response_basis"]["answer_kind"] == "why_supported"
    assert packet["knowledge_response_basis"]["why_relationship_included"] is True
    assert "differs from a perfect circle" in packet["knowledge_response_seed"]
    assert "value near zero is close to circular" in packet["knowledge_response_seed"]
    _assert_locked(packet)


def test_self_state_question_does_not_turn_overlapping_approved_knowledge_into_answer_content(tmp_path):
    conn = _conn(tmp_path)
    proposed = _propose(conn)
    _evaluate(conn, proposed["item"]["id"])
    route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": proposed["item"]["id"], "action": "approve_knowledge"},
    )

    packet = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "How are you feeling about talking through orbital eccentricity with us?",
            "intent_decision": {
                "intent": "self_state",
                "self_state_requested": True,
                "reasoning_requested": False,
                "dialogue_acts": ["self_state_question", "question"],
            },
            "dialogue_workspace": {
                "active_topic": "ordinary check-in",
                "pragmatics": {"ambiguity": {"level": "low"}},
            },
        },
    )["result"]

    assert packet["knowledge_context"]["available"] is True
    assert packet["knowledge_context"]["answer_eligible"] is False
    assert packet["knowledge_response_seed"] == ""
    assert packet["understanding_state"] == "not_yet_grounded"
    _assert_locked(packet)


def test_connective_words_do_not_retrieve_unrelated_approved_knowledge(tmp_path):
    conn = _conn(tmp_path)
    proposed = _propose(conn)
    _evaluate(conn, proposed["item"]["id"])
    route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": proposed["item"]["id"], "action": "approve_knowledge"},
    )

    packet = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "whats up means how are you",
            "intent_decision": {
                "intent": "correction",
                "reasoning_requested": False,
                "dialogue_acts": ["correction"],
            },
            "dialogue_workspace": {
                "active_topic": "ordinary check-in",
                "pragmatics": {"ambiguity": {"level": "low"}},
            },
        },
    )["result"]

    assert packet["knowledge_context"]["available"] is False
    assert packet["knowledge_response_seed"] == ""
    _assert_locked(packet)


def test_comprehension_handshake_asks_only_for_material_unresolved_meaning(tmp_path):
    conn = _conn(tmp_path)

    material = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "What about the other one?",
            "intent_decision": {"intent": "direct_answer"},
            "dialogue_workspace": {
                "active_topic": "",
                "pragmatics": {
                    "ambiguity": {"level": "material", "reason": "no bounded session referent"},
                    "resolved_reference": None,
                },
            },
        },
    )["result"]
    ordinary = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "Explain orbital shape in plain language.",
            "intent_decision": {"intent": "direct_answer"},
            "dialogue_workspace": {"active_topic": "orbital shape", "pragmatics": {"ambiguity": {"level": "low"}}},
            "content_seed": "Orbital shape describes the path an object follows around another body.",
        },
    )["result"]

    assert material["comprehension_handshake"]["required"] is True
    assert material["comprehension_handshake"]["does_not_interrogate_every_turn"] is True
    assert ordinary["comprehension_handshake"]["required"] is False
    _assert_locked(material)
    _assert_locked(ordinary)


def test_contradiction_reopens_metacognition_without_silently_mutating_knowledge(tmp_path):
    conn = _conn(tmp_path)
    proposed = _propose(conn)
    _evaluate(conn, proposed["item"]["id"])
    route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": proposed["item"]["id"], "action": "approve_knowledge"},
    )

    packet = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "Wait, that orbital eccentricity result doesn't look right. Recheck it.",
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
            "dialogue_workspace": {"active_topic": "orbital eccentricity", "pragmatics": {"ambiguity": {"level": "low"}}},
        },
    )["result"]
    stored = route_request(conn, "comprehension.concepts.list")["result"]["items"][0]

    assert packet["understanding_state"] == "reopened_for_recheck"
    assert packet["metacognitive_check"]["reopen_suggested"] is True
    assert stored["state"] == "approved_knowledge_resource"
    assert packet["retention"]["knowledge_write_active"] is False
    _assert_locked(packet)


def test_approved_knowledge_can_support_separate_parts_from_separate_concepts(tmp_path):
    conn = _conn(tmp_path)
    concepts = [
        {
            "title": "Garden water cycle",
            "domain": "earth_science",
            "material": "A garden water cycle moves water through soil, roots, plants, and air.",
            "principles": ["Evaporation and transpiration return garden water to the air."],
            "examples": ["Water can enter soil, move through a plant, and leave through its leaves."],
            "counterexamples": ["A sealed container does not model the full outdoor garden cycle."],
            "limits": ["The cycle description alone does not specify the rate of water movement."],
            "relationships": ["Plant transpiration connects living systems to the water cycle."],
            "source_refs": ["teaching:earth_science:garden-water-cycle"],
            "teach_back": "Water does not stay in one garden location: it moves through ground and plants before some of it returns to the air.",
        },
        {
            "title": "Soil water absorption",
            "domain": "earth_science",
            "material": "Soil absorption depends on pore space, composition, and existing saturation.",
            "principles": ["Less saturated soil can accept water until its available pore space fills."],
            "examples": ["A dry porous soil can initially absorb rainfall faster than saturated soil."],
            "counterexamples": ["Already saturated soil cannot keep absorbing water at the same rate."],
            "limits": ["Absorption capacity varies with soil composition and compaction."],
            "relationships": ["Saturation limits how much additional garden water can enter the soil."],
            "source_refs": ["teaching:earth_science:soil-absorption"],
            "teach_back": "Soil has a changing capacity for incoming water because its structure and how full it already is both affect absorption.",
        },
    ]
    approved_ids = []
    for concept in concepts:
        proposed = route_request(conn, "comprehension.concepts.propose", concept)["result"]
        concept_id = proposed["item"]["id"]
        route_request(
            conn,
            "comprehension.understanding.evaluate",
            {
                "concept_id": concept_id,
                    "teach_back": concept["teach_back"],
                "application": concept["examples"][0],
                "limits": concept["limits"],
                "counterexample": concept["counterexamples"][0],
                "correction_response": "I would revise the relationship while preserving the supported parts.",
                "source_alignment": True,
            },
        )
        route_request(
            conn,
            "comprehension.concepts.decide",
            {"concept_id": concept_id, "action": "approve_knowledge"},
        )
        approved_ids.append(concept_id)

    prompt = "Why does garden water return to the air, and what limitation does saturated soil place on absorption?"
    obligations = [
        {
            "id": "water-reason",
            "kind": "reason",
            "source_text": "Why does garden water return to the air?",
            "required": True,
        },
        {
            "id": "soil-limit",
            "kind": "limitation",
            "source_text": "What limitation does saturated soil place on absorption?",
            "required": True,
        },
    ]
    packet = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": prompt,
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True, "dialogue_acts": ["question"]},
            "dialogue_workspace": {
                "active_topic": "garden water and soil absorption",
                "pragmatics": {"ambiguity": {"level": "low"}, "response_obligations": obligations},
            },
            "knowledge_limit": 3,
        },
    )["result"]

    basis = packet["knowledge_response_basis"]
    assert basis["answer_kind"] == "multi_obligation_knowledge_synthesis"
    assert basis["concept_ids"] == approved_ids
    assert [item["obligation_id"] for item in basis["obligation_support"]] == ["water-reason", "soil-limit"]
    assert "Evaporation and transpiration" in packet["knowledge_response_seed"]
    assert "saturated soil cannot keep absorbing" in packet["knowledge_response_seed"]
    assert set(basis["source_refs"]) == {
        "teaching:earth_science:garden-water-cycle",
        "teaching:earth_science:soil-absorption",
    }
    _assert_locked(packet)
