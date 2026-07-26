from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.structural_discovery import (
    RELATION_TYPES,
    build_structural_discovery_packet,
    structural_discovery_response_seed,
)


def _base(**updates):
    payload = {
        "source_domain": "biology",
        "target_domain": "engineering",
        "relation_type": "analogy",
        "source_relation": "A feedback loop senses deviation and changes the next response.",
        "target_relation": "A controller measures error and adjusts its output.",
        "transferred_relation": "Both systems compare a current state with a constraint and use the difference to alter the next step.",
        "mappings": [
            {
                "source_role": "sensory signal",
                "target_role": "measurement input",
                "relation_preserved": "reports the current state to the regulating process",
                "basis": "current supplied descriptions",
            },
            {
                "source_role": "biological response",
                "target_role": "controller output",
                "relation_preserved": "changes behavior in response to measured deviation",
                "basis": "current supplied descriptions",
            },
        ],
        "holds_where": ["Both systems use feedback to reduce a measured deviation."],
        "breaks_where": ["Biological adaptation can involve growth and evolution that the controller analogy does not represent."],
        "source_refs": ["teaching:feedback", "engineering:controller"],
    }
    payload.update(updates)
    return payload


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_corpus_access_allowed"] is False
    assert result["private_corpus_wording_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["automatic_cocoon_routing"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def test_status_and_build_routes_expose_a_nonpersistent_discovery_contract(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    status = route_request(conn, "structural_discovery.status")["result"]
    packet = route_request(conn, "structural_discovery.build", _base())["result"]

    assert set(status["relation_types"]) == RELATION_TYPES
    assert packet["status"] == "structural_discovery_packet_ready"
    assert packet["classification"]["label"] == "bounded_structural_analogy"
    assert packet["writes_records"] is False
    assert packet["direct_truth_authority"] is False
    _assert_bounded(status)
    _assert_bounded(packet)


def test_structural_mapping_names_roles_hold_boundary_and_break_boundary():
    packet = build_structural_discovery_packet(_base())

    assert packet["bridge_traceable"] is True
    assert len(packet["structural_bridge"]) == 2
    assert packet["surface_similarity_used_as_bridge"] is False
    assert packet["holds_where"]
    assert packet["breaks_where"]
    assert packet["analogy_is_evidence"] is False
    assert packet["analogy_is_proof"] is False
    assert packet["expression_handoff"]["voice_may_upgrade_relation"] is False


def test_shared_word_without_role_mapping_is_held_as_incomplete_not_discovery():
    packet = build_structural_discovery_packet(
        _base(
            source_relation="Both descriptions use the word network.",
            target_relation="Both descriptions use the word network.",
            transferred_relation="They may be related because both say network.",
            mappings=[],
        )
    )

    assert packet["status"] == "structural_discovery_held_for_missing_or_private_basis"
    assert packet["bridge_traceable"] is False
    assert packet["classification"]["asserted_as"] == "not_yet_structural"
    assert any("two role mappings" in item for item in packet["missing_evidence"])
    assert structural_discovery_response_seed(packet) == ""


def test_homology_cause_and_equivalence_require_more_than_analogy():
    homology = build_structural_discovery_packet(
        _base(
            relation_type="homology",
            hypothesis={
                "statement": "The two forms may share an origin.",
                "discriminating_observations": ["A traceable lineage should preserve intermediate forms."],
                "counterexamples": ["Independent emergence without shared lineage would reject homology."],
            },
        )
    )
    cause = build_structural_discovery_packet(
        _base(
            relation_type="causal_connection",
            hypothesis={
                "statement": "The biological feedback design caused the controller architecture.",
                "discriminating_observations": ["Dated design records should show the transfer before implementation."],
                "counterexamples": ["An earlier independent controller design would weaken the causal claim."],
            },
        )
    )
    equivalence = build_structural_discovery_packet(
        _base(
            relation_type="equivalence",
            hypothesis={
                "statement": "The two systems may be equivalent within this scope.",
                "discriminating_observations": ["Every mapped input should produce corresponding outputs in both directions."],
                "counterexamples": ["A biological state with no controller counterpart would break equivalence."],
            },
        )
    )

    assert homology["classification"]["label"] == "homology_hypothesis_not_established"
    assert homology["classification"]["asserted_as"] == "hypothesis"
    assert cause["classification"]["label"] == "causal_hypothesis_not_established"
    assert cause["pattern_is_causal_connection"] is False
    assert equivalence["classification"]["label"] == "analogy_not_equivalence"
    assert equivalence["classification"]["asserted_as"] == "analogy"


def test_pattern_supported_homology_and_scoped_equivalence_keep_distinct_labels():
    pattern = build_structural_discovery_packet(_base(relation_type="pattern"))
    homology = build_structural_discovery_packet(
        _base(
            relation_type="homology",
            shared_origin_evidence_refs=["paper:shared-lineage"],
            hypothesis={
                "statement": "The two forms may descend from a shared origin.",
                "discriminating_observations": ["Intermediate forms should preserve the mapped roles."],
                "counterexamples": ["Independent emergence would reject shared origin."],
            },
        )
    )
    equivalence = build_structural_discovery_packet(
        _base(
            relation_type="equivalence",
            breaks_where=[],
            bidirectional_mapping=True,
            shared_constraints_verified=True,
            evidence_refs=["test:bidirectional-correspondence"],
            hypothesis={
                "statement": "The two relations may be equivalent inside the tested scope.",
                "discriminating_observations": ["Each mapped input should preserve the corresponding output in both directions."],
                "counterexamples": ["Any in-scope state without a reverse mapping would reject equivalence."],
            },
        )
    )

    assert pattern["classification"]["label"] == "structural_pattern"
    assert pattern["classification"]["asserted_as"] == "pattern"
    assert homology["classification"]["label"] == "provisional_homology"
    assert homology["classification"]["asserted_as"] == "hypothesis"
    assert equivalence["classification"]["label"] == "provisional_scoped_equivalence"
    assert equivalence["classification"]["asserted_as"] == "provisional_equivalence"


def test_logical_leap_remains_a_testable_hypothesis_with_claim_evidence():
    packet = build_structural_discovery_packet(
        _base(
            relation_type="causal_connection",
            mechanism="Designers translated a documented biological feedback relation into controller logic.",
            evidence_refs=["paper:design-history"],
            hypothesis={
                "statement": "The biological model influenced the controller design.",
                "predictions": ["Design notes should use the same role mapping before the controller was built."],
                "discriminating_observations": [
                    "Compare dated design notes with independent controller work from the same period."
                ],
                "counterexamples": [
                    "A complete earlier controller design with no biological input would weaken the influence claim."
                ],
                "what_would_change": ["Earlier independent provenance for the same controller relation."],
                "logical_leap": True,
            },
        )
    )

    assert packet["status"] == "structural_discovery_packet_ready"
    assert packet["classification"]["label"] == "supported_causal_hypothesis"
    assert packet["hypothesis_testable"] is True
    assert packet["hypothesis"]["logical_leap"] is True
    assert packet["hypothesis"]["conclusion"] is False
    claims = packet["claim_evidence_packet"]
    assert claims["claims_by_type"]["observation"]
    assert claims["claims_by_type"]["inference"] == ["discovery-structural-inference"]
    assert claims["claims_by_type"]["hypothesis"] == ["discovery-open-hypothesis"]


def test_uncheckable_logical_leap_is_held_until_a_test_and_counterexample_exist():
    packet = build_structural_discovery_packet(
        _base(
            hypothesis={
                "statement": "The same hidden principle may govern both systems.",
                "logical_leap": True,
            }
        )
    )

    assert packet["status"] == "structural_discovery_held_for_missing_or_private_basis"
    assert packet["hypothesis_testable"] is False
    assert any("discriminating observation" in item for item in packet["missing_evidence"])
    assert any("counterexample" in item for item in packet["missing_evidence"])


def test_only_approved_provenance_bearing_knowledge_can_be_reused():
    packet = build_structural_discovery_packet(
        _base(
            approved_knowledge_links=[
                {
                    "concept_id": "feedback-1",
                    "domain": "biology",
                    "central_claim": "Negative feedback can reduce deviation from a regulated range.",
                    "source_refs": ["teaching:feedback"],
                    "approved": True,
                },
                {
                    "concept_id": "unreviewed",
                    "central_claim": "A draft idea.",
                    "source_refs": ["draft:one"],
                    "approved": False,
                },
                {
                    "concept_id": "memory-shaped",
                    "central_claim": "Private recollection.",
                    "source_refs": ["private_corpus:message-2"],
                    "approved": True,
                },
            ]
        )
    )

    assert [item["concept_id"] for item in packet["approved_knowledge_links"]] == ["feedback-1"]
    assert packet["earlier_approved_knowledge_reused"] is True
    assert packet["personal_memory_used_as_domain_knowledge"] is False
    assert len(packet["held_back_knowledge_links"]) == 2
    approved_claim_id = "discovery-approved-knowledge-feedback-1"
    assert approved_claim_id in packet["claim_evidence_packet"]["claims_by_type"]["conclusion"]
    inference = next(
        item
        for item in packet["claim_evidence_packet"]["claims"]
        if item["claim_id"] == "discovery-structural-inference"
    )
    assert approved_claim_id in inference["basis_claim_ids"]


def test_private_corpus_or_miner_provenance_is_held_out_of_visible_discovery():
    packet = build_structural_discovery_packet(
        _base(
            source_relation="PRIVATE EXACT SOURCE WORDING",
            source_refs=["private_corpus:message-42"],
            source_provenance_class="raw_private_corpus",
        )
    )

    assert packet["status"] == "structural_discovery_held_for_missing_or_private_basis"
    assert packet["response_seed"] == ""
    assert any("Private corpus" in item for item in packet["missing_evidence"])
    assert packet["claim_evidence_packet"]["accepted_source_refs"] == []
    assert packet["source_relation"] == ""
    assert packet["structural_bridge"] == []
    assert packet["hypothesis"] == {}
    assert packet["claim_evidence_packet"]["claim_count"] == 0


def test_response_seed_keeps_relation_holds_breaks_hypothesis_and_check_distinct():
    packet = build_structural_discovery_packet(
        _base(
            hypothesis={
                "statement": "The same feedback constraint may predict failure in both systems.",
                "discriminating_observations": ["Perturb each system beyond its response range and compare recovery."],
                "counterexamples": ["One system recovering without feedback would break the proposed transfer."],
            }
        )
    )
    response = packet["response_seed"]

    assert "structural relationship I am transferring" in response
    assert "analogy is not proof" in response
    assert "It holds where:" in response
    assert "It breaks where:" in response
    assert "Hypothesis:" in response
    assert "A discriminating check would be:" in response
    assert "A counterexample or failure condition is:" in response
