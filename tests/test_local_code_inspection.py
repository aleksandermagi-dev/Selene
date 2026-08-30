from __future__ import annotations

from selene.local_code_inspection import (
    build_local_code_approval_receipt,
    inspect_local_code,
    local_code_inspection_status,
)


def test_status_keeps_local_code_inspection_read_only_and_explicit():
    result = local_code_inspection_status()

    assert result["status"] == "local_code_inspection_ready"
    assert result["directory_scan_allowed"] is False
    assert result["glob_allowed"] is False
    assert result["code_execution_allowed"] is False
    assert result["filesystem_write_allowed"] is False
    assert result["observation_interpretation_separated"] is True
    assert result["chat_exact_file_approval_required"] is True


def test_chat_file_approval_requires_both_authenticated_aleks_and_exact_current_paths():
    payload = {
        "speaker_envelope": {
            "claimed_speaker": "Aleks",
            "authentication_strength": "local_desktop_session",
        },
        "approved_workspace_files": [
            {"path": "src/selene/answer_engine.py", "approved": True}
        ],
        "local_code_approval": {
            "approved": True,
            "scope": "current_request",
            "exact_paths": ["src/selene/answer_engine.py"],
        },
    }

    allowed = build_local_code_approval_receipt(payload)
    transport_only = build_local_code_approval_receipt(
        {
            **payload,
            "speaker_envelope": {
                "claimed_speaker": "Aleks",
                "authentication_strength": "transport_claim_only",
            },
        }
    )
    mismatched = build_local_code_approval_receipt(
        {
            **payload,
            "local_code_approval": {
                "approved": True,
                "scope": "current_request",
                "exact_paths": ["src/selene/verified_math.py"],
            },
        }
    )

    assert allowed["eligible"] is True
    assert allowed["file_read_allowed"] is True
    assert allowed["approval_reusable_across_requests"] is False
    assert transport_only["eligible"] is False
    assert "authenticated_aleks_session_required_for_file_read" in transport_only["blockers"]
    assert mismatched["eligible"] is False
    assert "approved_paths_do_not_exactly_match_selected_paths" in mismatched["blockers"]


def test_attributed_paste_needs_no_filesystem_approval_and_grants_no_file_read():
    result = build_local_code_approval_receipt(
        {
            "code_packets": [
                {
                    "source_ref": "supplied:snippet.py",
                    "path": "snippet.py",
                    "content": "def safe():\n    return True\n",
                }
            ]
        }
    )

    assert result["eligible"] is True
    assert result["input_mode"] == "attributed_pasted_code"
    assert result["file_read_allowed"] is False
    assert result["filesystem_write_allowed"] is False


def test_inline_packet_reports_observation_interpretation_and_cited_location():
    result = inspect_local_code(
        {
            "prompt": "Where is target_function defined?",
            "inspection_terms": ["target_function"],
            "code_packets": [
                {
                    "source_ref": "supplied:sample.py",
                    "path": "sample.py",
                    "content": "def target_function(value):\n    return value + 1\n",
                }
            ],
        }
    )

    assert result["inspected"] is True
    assert result["citations"] == [
        {"source_ref": "supplied:sample.py", "path": "sample.py", "line_start": 1, "line_end": 1}
    ]
    assert any(item["kind"] == "text_match_observation" for item in result["observations"])
    assert result["interpretations"][0]["interpretation"].startswith("This location appears to define")
    assert result["source_refs"] == ["supplied:sample.py"]
    assert result["filesystem_write_allowed"] is False
    assert result["autonomous_filesystem_authority"] is False


def test_exact_approved_workspace_file_can_be_inspected_without_scanning():
    result = inspect_local_code(
        {
            "prompt": "Inspect run_verified_math_answer in the approved file.",
            "inspection_terms": ["run_verified_math_answer"],
            "approved_workspace_files": [
                {"path": "src/selene/answer_engine.py", "approved": True}
            ],
        }
    )

    assert result["inspected"] is True
    assert result["inspected_sources"][0]["path"] == "src/selene/answer_engine.py"
    assert result["inspected_sources"][0]["source_kind"] == "approved_workspace_file"
    assert result["citations"]
    assert all(item["path"] == "src/selene/answer_engine.py" for item in result["citations"])
    assert result["directory_scan_allowed"] is False


def test_outside_unapproved_and_unattributed_sources_fall_gracefully(tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("def outside():\n    pass\n", encoding="utf-8")

    result = inspect_local_code(
        {
            "prompt": "Inspect outside.",
            "code_packets": [{"path": "missing_ref.py", "content": "pass"}],
            "approved_workspace_files": [
                {"path": str(outside), "approved": True},
                {"path": "src/selene", "approved": True},
                {"path": "src/**/*.py", "approved": True},
                {"path": "src/selene/answer_engine.py", "approved": False},
            ],
        }
    )

    reasons = " ".join(item["reason"] for item in result["rejected_sources"])
    assert result["status"] == "local_code_inspection_unable"
    assert result["inspected"] is False
    assert "source_ref" in reasons
    assert "outside the approved project root" in reasons
    assert "directories" in reasons
    assert "wildcard" in reasons
    assert "approved=true" in reasons
    assert result["citations"] == []


def test_absent_term_is_bounded_to_inspected_files_not_global_absence():
    result = inspect_local_code(
        {
            "prompt": "Find missing_symbol.",
            "inspection_terms": ["missing_symbol"],
            "code_packets": [
                {
                    "source_ref": "supplied:small.py",
                    "path": "small.py",
                    "content": "def present_symbol():\n    return True\n",
                }
            ],
        }
    )

    assert result["inspected"] is True
    assert result["citations"] == []
    assert result["answer_confidence"] == "insufficient_matching_code_evidence"
    assert "bounded set" in result["result_summary"]
    assert result["interpretations"][0]["scope_limit"].startswith("This does not establish absence")


def test_duplicate_inline_source_references_do_not_create_ambiguous_citations():
    result = inspect_local_code(
        {
            "prompt": "Inspect target_symbol.",
            "inspection_terms": ["target_symbol"],
            "code_packets": [
                {"source_ref": "supplied:duplicate", "path": "first.py", "content": "def target_symbol():\n    pass\n"},
                {"source_ref": "supplied:duplicate", "path": "second.py", "content": "target_symbol = None\n"},
            ],
        }
    )

    assert result["inspected"] is True
    assert result["source_refs"] == ["supplied:duplicate"]
    assert result["rejected_sources"][0]["reason"] == "duplicate source_ref"
    assert all(item["path"] == "first.py" for item in result["citations"])
