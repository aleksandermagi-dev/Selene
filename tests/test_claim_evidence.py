from __future__ import annotations

from selene.claim_evidence import CLAIM_TYPES, build_claim_evidence_packet
from selene.db import connect, init_db
from selene.epistemic_revision import build_epistemic_revision_plan
from selene.module_router import route_request


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["automatic_evidence_ledger_write"] is False
    assert result["citation_invention_allowed"] is False


def test_status_and_build_routes_expose_the_typed_nonpersistent_contract(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    status = route_request(conn, "claim_evidence.status")["result"]
    packet = route_request(
        conn,
        "claim_evidence.build",
        {
            "claims": [
                {
                    "claim_id": "observed",
                    "claim_type": "observation",
                    "text": "The instrument displayed 11.",
                }
            ]
        },
    )["result"]

    assert set(status["claim_types"]) == CLAIM_TYPES
    assert status["domain_category_policy"]["automatic_acceptance_by_category"] is False
    assert packet["claims"][0]["validity"] == "reported_observation"
    assert packet["writes_records"] is False
    _assert_bounded(status)
    _assert_bounded(packet)


def test_all_claim_types_remain_distinct_and_keep_reversal_conditions():
    claims = [
        {"claim_id": "obs", "claim_type": "observation", "text": "The sample changed color."},
        {
            "claim_id": "report",
            "claim_type": "source_statement",
            "text": "Source A reports a temperature increase.",
            "source_refs": ["source:a"],
        },
        {
            "claim_id": "infer",
            "claim_type": "inference",
            "text": "The change may track temperature.",
            "basis_claim_ids": ["obs", "report"],
        },
        {
            "claim_id": "hyp",
            "claim_type": "hypothesis",
            "text": "Temperature caused the color change.",
            "basis_claim_ids": ["obs"],
        },
        {
            "claim_id": "model",
            "claim_type": "model",
            "text": "A temperature-response model explains the sample.",
            "basis_claim_ids": ["obs", "report"],
        },
        {
            "claim_id": "conclusion",
            "claim_type": "conclusion",
            "text": "Temperature is the leading current explanation.",
            "basis_claim_ids": ["infer", "model"],
        },
        {
            "claim_id": "spec",
            "claim_type": "speculation",
            "text": "An unknown field might also affect it.",
        },
    ]
    packet = build_claim_evidence_packet({"claims": claims})

    assert {item["claim_type"] for item in packet["claims"]} == CLAIM_TYPES
    assert all(item["what_would_change"] for item in packet["claims"])
    assert packet["claims_by_type"]["observation"] == ["obs"]
    assert packet["claims_by_type"]["speculation"] == ["spec"]
    assert next(item for item in packet["claims"] if item["claim_id"] == "spec")["speculation_is_evidence"] is False
    assert packet["direct_answer_inference_and_uncertainty_separate"] is True


def test_source_statements_require_attribution_and_citations_cannot_be_invented():
    packet = build_claim_evidence_packet(
        {
            "claims": [
                {"claim_type": "source_statement", "text": "An unattributed statement."},
                {
                    "claim_id": "attributed",
                    "claim_type": "source_statement",
                    "text": "The paper reports a bounded effect.",
                    "source_refs": ["paper:one"],
                },
            ],
            "accepted_source_refs": ["paper:one"],
            "citations": [
                {"source_ref": "paper:one", "locator": "p. 4"},
                {"source_ref": "paper:invented", "locator": "p. 99"},
            ],
        }
    )

    assert packet["claim_count"] == 1
    assert packet["held_back_claims"][0]["reason"].startswith("source_statement requires")
    assert packet["citations"][0]["source_ref"] == "paper:one"
    assert packet["held_back_citations"][0]["citation"] == "paper:invented"
    assert packet["all_citations_trace_to_accepted_sources"] is False
    _assert_bounded(packet)


def test_claims_are_judged_individually_not_by_source_or_domain_category():
    packet = build_claim_evidence_packet(
        {
            "claims": [
                {
                    "claim_id": "science-limited",
                    "claim_type": "model",
                    "text": "This model works in the measured range.",
                    "basis_claim_ids": ["observation"],
                    "validity": "limited",
                    "source_category": "science",
                },
                {
                    "claim_id": "myth-open",
                    "claim_type": "hypothesis",
                    "text": "This story may encode a remembered event.",
                    "basis_claim_ids": ["observation"],
                    "validity": "open_hypothesis",
                    "source_category": "mythology",
                },
                {
                    "claim_id": "observation",
                    "claim_type": "observation",
                    "text": "The two records share a dated place reference.",
                    "source_category": "archaeology",
                },
            ]
        }
    )
    by_id = {item["claim_id"]: item for item in packet["claims"]}

    assert by_id["science-limited"]["validity"] == "limited"
    assert by_id["myth-open"]["validity"] == "open_hypothesis"
    assert all(item["source_category_determines_validity"] is False for item in packet["claims"])
    assert packet["claim_evaluation"]["whole_source_category_accepted_or_rejected"] is False
    assert packet["claim_evaluation"]["same_evidentiary_questions_across_domains"] is True


def test_claims_from_one_source_can_have_independent_useful_limited_revised_and_reopened_states():
    packet = build_claim_evidence_packet(
        {
            "claims": [
                {
                    "claim_id": "useful",
                    "claim_type": "source_statement",
                    "text": "The source accurately reports the measured date.",
                    "source_refs": ["source:mixed"],
                    "validity": "useful_within_scope",
                },
                {
                    "claim_id": "limited",
                    "claim_type": "source_statement",
                    "text": "The source generalizes from one site.",
                    "source_refs": ["source:mixed"],
                    "validity": "limited",
                },
                {
                    "claim_id": "revised",
                    "claim_type": "source_statement",
                    "text": "The source's original sequence was later corrected.",
                    "source_refs": ["source:mixed"],
                    "validity": "revised",
                },
                {
                    "claim_id": "reopened",
                    "claim_type": "source_statement",
                    "text": "A later find reopened the source's identification.",
                    "source_refs": ["source:mixed"],
                    "validity": "reopened",
                },
            ]
        }
    )

    assert [item["validity"] for item in packet["claims"]] == [
        "useful_within_scope",
        "limited",
        "revised",
        "reopened",
    ]
    assert {ref for item in packet["claims"] for ref in item["source_refs"]} == {"source:mixed"}


def test_claim_level_disagreement_does_not_reject_whole_sources():
    packet = build_claim_evidence_packet(
        {
            "claims": [
                {
                    "claim_id": "a",
                    "claim_type": "source_statement",
                    "text": "Study A reports an effect.",
                    "source_refs": ["study:a"],
                    "claim_key": "effect",
                    "stance": "support",
                },
                {
                    "claim_id": "b",
                    "claim_type": "source_statement",
                    "text": "Study B reports no effect.",
                    "source_refs": ["study:b"],
                    "claim_key": "effect",
                    "stance": "oppose",
                },
            ]
        }
    )

    assert packet["disagreements"][0]["status"] == "claim_level_disagreement_unresolved"
    assert packet["disagreements"][0]["whole_sources_rejected"] is False
    assert all(item["validity"] == "contested" for item in packet["claims"])
    assert packet["expression_handoff"]["disagreement_count"] == 1
    assert packet["expression_handoff"]["uncertainty_claim_ids"] == ["a", "b"]


def test_phase_five_model_ancestry_flows_into_claim_evidence_without_erasure():
    revision = build_epistemic_revision_plan(
        {
            "requested_kind": "scope_restriction",
            "target": "Newtonian mechanics",
            "prior_claim": "Newtonian mechanics explains motion.",
            "revised_claim": "Newtonian mechanics applies at low speeds and weak gravity.",
            "scope": "low speeds and weak gravity",
        }
    )
    packet = build_claim_evidence_packet(
        {
            "claims": [
                {
                    "claim_id": "newton",
                    "claim_type": "model",
                    "text": revision["revised_claim"],
                    "basis_claim_ids": ["observation"],
                    "scope": revision["scope"],
                },
                {"claim_id": "observation", "claim_type": "observation", "text": "The bounded case remains predictive."},
            ],
            "epistemic_revision": revision,
        }
    )

    ancestry = packet["model_ancestry"][0]
    assert ancestry["prior_model"] == "Newtonian mechanics explains motion."
    assert ancestry["current_model"] == "Newtonian mechanics applies at low speeds and weak gravity."
    assert ancestry["valid_scope"] == "low speeds and weak gravity"
    assert ancestry["prior_model_erased"] is False
