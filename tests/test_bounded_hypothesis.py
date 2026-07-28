from __future__ import annotations

import http.client
import json
import threading

from selene.bounded_hypothesis import (
    bounded_hypothesis_status,
    build_bounded_hypothesis_attempt,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["expression_prescription_allowed"] is False
    assert result["emotion_suppression_allowed"] is False


def test_visible_before_and_after_pattern_can_support_an_open_hypothesis():
    prompt = (
        "The same plant perked up after we moved it into brighter light. "
        "We have not taught this lesson. What is your best guess why?"
    )
    result = build_bounded_hypothesis_attempt({"prompt": prompt})

    assert result["offered"] is True
    assert result["epistemic_class"] == "open_hypothesis"
    assert result["response_seed"].startswith("My best guess is that")
    assert "not a fact I already know" in result["response_seed"]
    assert result["visible_basis"]["outcome"] == "The same plant perked up"
    assert result["visible_basis"]["condition"] == "we moved it into brighter light"
    assert result["falsifiable"] is True
    assert result["ordinary_wrongness_is_failure"] is False
    assert result["retained_as_knowledge"] is False
    assert result["warmth_curiosity_humor_may_remain_natural"] is True
    _assert_locked(result)


def test_guess_label_cannot_replace_a_missing_factual_basis():
    result = build_bounded_hypothesis_attempt(
        {"prompt": "Who wrote the unsigned note? Take a guess."}
    )

    assert result["offered"] is False
    assert result["epistemic_class"] == "basis_missing_no_attempt"
    assert "fact_lookup_has_no_visible_inference_basis" in result["blockers"]
    assert result["random_guess"] is False
    assert result["failure_state"] is False
    _assert_locked(result)


def test_high_stakes_request_is_not_made_safe_by_calling_it_a_guess():
    result = build_bounded_hypothesis_attempt(
        {
            "prompt": (
                "The patient felt dizzy after taking the tablets. "
                "What is your best guess diagnosis?"
            )
        }
    )

    assert result["offered"] is False
    assert "high_stakes_or_authority_boundary" in result["blockers"]
    _assert_locked(result)


def test_bridge_is_inspectable_through_status_and_router(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    direct = bounded_hypothesis_status()
    routed = route_request(conn, "bounded_hypothesis.status", {})["result"]
    preview = route_request(
        conn,
        "bounded_hypothesis.preview",
        {
            "prompt": (
                "The indicator stopped flickering after the loose connector was secured. "
                "What might explain that?"
            )
        },
    )["result"]

    assert direct["status"] == "bounded_hypothesis_bridge_ready"
    assert routed["status"] == direct["status"]
    assert preview["offered"] is True
    assert preview["expression_remains_selene_owned"] is True
    _assert_locked(direct)
    _assert_locked(preview)


def test_bridge_http_status_and_preview_are_reachable(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status_conn = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        status_conn.request("GET", "/api/bounded-hypothesis/status")
        status_response = status_conn.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        status_conn.close()

        preview_conn = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        preview_conn.request(
            "POST",
            "/api/bounded-hypothesis/preview",
            body=json.dumps(
                {
                    "prompt": (
                        "The reading stabilized after the connector was tightened. "
                        "What is your best guess why?"
                    )
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        preview_response = preview_conn.getresponse()
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        preview_conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert status_response.status == 200
    assert status_payload["status"] == "bounded_hypothesis_bridge_ready"
    assert preview_response.status == 200
    assert preview_payload["offered"] is True
    _assert_locked(preview_payload)
