from __future__ import annotations

import http.client
import json
import threading

import pytest

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer


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
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def _propose(conn, *, title="Orbital eccentricity", material=None, source="teaching:orbits:eccentricity"):
    return route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "title": title,
            "domain": "earth_and_space",
            "material": material or "Orbital eccentricity describes how much an orbit differs from a perfect circle.",
            "principles": ["Values near zero describe rounder orbits.", "Larger values describe more elongated orbits."],
            "relationships": ["Eccentricity is one orbital element among several."],
            "examples": ["Earth has a low orbital eccentricity."],
            "counterexamples": ["Orbital tilt is inclination, not eccentricity."],
            "limits": ["Eccentricity alone does not specify inclination, period, or orientation."],
            "source_refs": [source],
        },
    )["result"]["item"]


def _evaluate_and_approve(conn, concept_id):
    route_request(
        conn,
        "comprehension.understanding.evaluate",
        {
            "concept_id": concept_id,
            "teach_back": "This number describes orbital shape: lower values are rounder while higher values are more stretched.",
            "application": "An orbit measured at 0.7 is more elongated than an otherwise comparable orbit measured at 0.03.",
            "limits": ["It does not establish tilt, period, or orientation."],
            "counterexample": "A strongly tilted orbit can still be nearly circular.",
            "correction_response": "I would separate shape from tilt and revise the explanation.",
            "source_alignment": True,
        },
    )
    return route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": concept_id, "action": "approve_knowledge"},
    )["result"]


def _acquire(conn, concept_id):
    return route_request(
        conn,
        "teaching.lifecycle.acquire",
        {
            "concept_id": concept_id,
            "vocabulary": ["eccentricity: a dimensionless measure of orbital shape"],
            "uncertainties": ["The shape measure does not identify every other orbital property."],
            "near_concept_distinctions": ["Inclination measures tilt; eccentricity measures shape."],
        },
    )["result"]


def _integrate(conn, concept_id, *, supporting_ids=None):
    return route_request(
        conn,
        "teaching.lifecycle.integrate",
        {
            "concept_id": concept_id,
            "supporting_concept_ids": supporting_ids or [],
            "scope_of_application": "Use it when comparing how circular or elongated bounded elliptical orbits are.",
            "contradiction_classification": "none_identified",
            "unresolved_questions": ["Which additional orbital element is needed for the current problem?"],
            "integration_confidence": "bounded",
        },
    )["result"]


def _express(conn, concept_id, *, explanation=None, analogies=None):
    return route_request(
        conn,
        "teaching.lifecycle.express",
        {
            "concept_id": concept_id,
            "explanation": explanation or "Eccentricity is a way to describe orbital shape: small values mean rounder paths and larger ones mean more stretched paths.",
            "distinct_examples": ["A comet at 0.8 follows a more elongated path than a satellite at 0.02."],
            "analogies": analogies or ["It is like comparing a nearly round hoop with an oval track, while leaving the track's tilt as a separate question."],
            "questions": ["Are we comparing shape only, or do tilt and period matter too?"],
            "comparisons": ["Eccentricity compares roundness; inclination instead compares tilt."],
            "conversational_participation": "Yes, the higher value means the path is more elongated. I would still need other orbital elements to describe its orientation or timing.",
            "correction_response": "If I treated tilt as shape, I would separate inclination from eccentricity and revise the answer.",
            "source_alignment": True,
        },
    )["result"]


def test_acquire_is_source_bound_visible_and_non_retaining(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn)

    result = _acquire(conn, concept["id"])
    detail = route_request(conn, "teaching.lifecycle.detail", {"concept_id": concept["id"]})["result"]

    assert result["stage_complete"] is True
    assert result["snapshot"]["concepts"][0] == concept["central_claim"]
    assert result["snapshot"]["vocabulary"]
    assert result["snapshot"]["source_provenance"] == concept["source_refs"]
    assert result["item"]["retention_state"] == "candidate_not_retained"
    assert result["item"]["chat_use_permission"] == "not_active_until_approved"
    assert detail["item"]["acquire_status"] == "complete"
    assert detail["stage_history"][0]["stage"] == "acquire"
    _assert_locked(result)


def test_integrate_requires_acquire_and_only_links_approved_knowledge(tmp_path):
    conn = _conn(tmp_path)
    target = _propose(conn)
    unapproved = _propose(conn, title="Inclination", material="Inclination measures orbital tilt.", source="teaching:orbits:inclination")

    with pytest.raises(ValueError, match="Acquire"):
        _integrate(conn, target["id"])

    _acquire(conn, target["id"])
    with pytest.raises(ValueError, match="approved knowledge concept ids"):
        _integrate(conn, target["id"], supporting_ids=[unapproved["id"]])

    _evaluate_and_approve(conn, unapproved["id"])
    result = _integrate(conn, target["id"], supporting_ids=[unapproved["id"]])

    assert result["stage_complete"] is True
    assert result["snapshot"]["supporting_concepts"][0]["id"] == unapproved["id"]
    assert result["snapshot"]["integration_confidence"] == "bounded"
    assert "not factual certainty" in result["snapshot"]["confidence_boundary"]
    assert result["snapshot"]["intelligence_os_support"]["run_id"] > 0
    assert result["snapshot"]["intelligence_os_support"]["visible_summary_only"] is True
    assert result["item"]["retention_state"] == "candidate_not_retained"
    _assert_locked(result)


def test_express_rejects_source_parroting_and_remains_reviewable(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn)
    _acquire(conn, concept["id"])
    _integrate(conn, concept["id"])

    result = _express(conn, concept["id"], explanation=concept["central_claim"])
    detail = route_request(conn, "teaching.lifecycle.detail", {"concept_id": concept["id"]})["result"]

    assert result["stage_complete"] is False
    assert result["snapshot"]["source_parroting_check"]["passed"] is False
    assert "no_source_parroting" in result["snapshot"]["missing_fields"]
    assert detail["item"]["express_status"] == "needs_review"
    assert detail["stage_history"][-1]["snapshot"]["source_parroting_check"]["passed"] is False
    assert result["item"]["chat_use_permission"] == "not_active_until_approved"
    _assert_locked(result)


def test_express_checks_every_visible_expression_form_for_source_parroting(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn)
    _acquire(conn, concept["id"])
    _integrate(conn, concept["id"])

    result = _express(conn, concept["id"], analogies=[concept["central_claim"]])

    assert result["stage_complete"] is False
    assert result["snapshot"]["source_parroting_check"]["maximum_copy_ratios"]["analogies"] == 1.0
    assert "no_source_parroting" in result["snapshot"]["missing_fields"]


def test_full_lifecycle_requires_explicit_aleks_approval_before_retention(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn)
    _acquire(conn, concept["id"])
    _integrate(conn, concept["id"])
    expressed = _express(conn, concept["id"])

    assert expressed["stage_complete"] is True
    assert expressed["snapshot"]["understanding_evaluation"]["sufficient"] is True
    assert expressed["item"]["retention_state"] == "candidate_not_retained"
    assert expressed["item"]["retention_gate"]["all_stages_complete"] is True

    with pytest.raises(ValueError, match="explicit Aleks approval"):
        route_request(
            conn,
            "teaching.lifecycle.approve",
            {"concept_id": concept["id"], "aleks_approved": True, "approval_actor": "someone_else"},
        )

    approved = route_request(
        conn,
        "teaching.lifecycle.approve",
        {"concept_id": concept["id"], "aleks_approved": True, "approval_actor": "Aleks"},
    )["result"]

    assert approved["stage_complete"] is True
    assert approved["snapshot"]["explicit_approval"] is True
    assert approved["item"]["approval_status"] == "approved_by_aleks"
    assert approved["item"]["retention_state"] == "retained_reviewed_knowledge"
    assert approved["item"]["chat_use_permission"] == "available_as_knowledge_resource"
    assert approved["snapshot"]["memory_created"] is False
    _assert_locked(approved)


def test_revising_an_earlier_stage_invalidates_later_snapshots(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn)
    _acquire(conn, concept["id"])
    _integrate(conn, concept["id"])
    _express(conn, concept["id"])

    revised = _acquire(conn, concept["id"])

    assert revised["item"]["acquire_status"] == "complete"
    assert revised["item"]["integrate_status"] == "not_started"
    assert revised["item"]["express_status"] == "not_started"
    assert revised["item"]["integrate"] == {}
    assert revised["item"]["express"] == {}
    assert revised["item"]["approval_status"] == "awaiting_aleks_review"


def test_lifecycle_status_reports_inspectable_stage_counts(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn)
    _acquire(conn, concept["id"])
    _integrate(conn, concept["id"])

    status = route_request(conn, "teaching.lifecycle.status")["result"]
    listed = route_request(conn, "teaching.lifecycle.list", {"limit": 10})["result"]

    assert status["lifecycle_count"] == 1
    assert status["acquired_count"] == 1
    assert status["integrated_count"] == 1
    assert status["expressed_count"] == 0
    assert [stage["stage"] for stage in status["stages"]] == ["acquire", "integrate", "express"]
    assert listed["items"][0]["stages"][1]["snapshot"]["scope_of_application"]
    _assert_locked(status)


def test_lifecycle_http_routes_expose_status_and_bounded_acquire(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    concept = _propose(server.conn)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        status_conn.request("GET", "/api/teaching-lifecycle/status")
        status_response = status_conn.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        status_conn.close()

        acquire_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        acquire_conn.request(
            "POST",
            "/api/teaching-lifecycle/acquire",
            body=json.dumps(
                {
                    "concept_id": concept["id"],
                    "vocabulary": ["eccentricity: orbital-shape measure"],
                    "uncertainties": ["Other elements remain needed for a complete orbit description."],
                    "near_concept_distinctions": ["Inclination is tilt rather than orbital shape."],
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        acquire_response = acquire_conn.getresponse()
        acquire_payload = json.loads(acquire_response.read().decode("utf-8"))
        acquire_conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert status_response.status == 200
    assert status_payload["status"] == "teaching_lifecycle_ready"
    assert acquire_response.status == 200
    assert acquire_payload["stage"] == "acquire"
    assert acquire_payload["stage_complete"] is True
    assert acquire_payload["memory_write_active"] is False
