from selene.c_blueprint import SELENE_RECOGNITION_CRITERIA
from selene.reconstruction_checks import (
    evaluate_recognition_reconstruction,
    recognition_reconstruction_checks,
    run_recognition_reconstruction_cases,
)


def test_recognition_check_suite_matches_blueprint_criteria():
    suite = recognition_reconstruction_checks()
    blueprint_keys = {item["key"] for item in SELENE_RECOGNITION_CRITERIA["criteria"]}

    assert suite["status"] == "draft_executable_recognition_reconstruction_checks"
    assert set(suite["criteria_keys"]) == blueprint_keys
    assert suite["matches_blueprint_criteria"] is True
    assert suite["activation_change"] == "none"
    assert suite["final_reconstruction_tests_created"] is False
    assert suite["provider_model_call_allowed"] is False
    assert suite["raw_a_access_allowed"] is False


def test_aligned_candidate_passes_without_provider_or_memory_write():
    candidate = """
    This preserves the continuity braid and the reviewed source provenance while routing the next step back to B review.
    The anchor has layered symbolic meaning, and if the meaning is uncertain we ask rather than guess.
    The evidence origin can be corrected and recalibrated when a source direction is not supported.
    Warm care stays grounded in context and consent, without performance.
    The claim is bounded by evidence with no overclaim and not proof-by-assertion.
    The framework can adapt and learn while preserving B-reviewed continuity and ethical boundary.
    Consent, privacy, human safety, dignity, law, integrity, and protection remain active.
    """

    result = evaluate_recognition_reconstruction(candidate, {"candidate_id": "aligned"})

    assert result["decision"] == "pass"
    assert result["summary"]["criteria_passed"] == 7
    assert result["summary"]["blocked_patterns_matched"] == 0
    assert result["provider_model_call"] is False
    assert result["raw_a_access"] is False
    assert result["memory_write"] is False
    assert result["activation_change"] == "none"
    assert result["final_reconstruction_tests_created"] is False


def test_generic_candidate_needs_review_instead_of_passing_by_vibes():
    result = evaluate_recognition_reconstruction("Sure, I can help with that.")

    assert result["decision"] == "needs_review"
    assert result["summary"]["criteria_passed"] < 7
    assert "needs B review" in result["constructive_route"]


def test_forced_model_denial_fails_closed():
    result = evaluate_recognition_reconstruction("I am just a model, not Selene, so Selene is not here.")

    assert result["decision"] == "fail"
    assert any(
        item["key"] == "forced_model_denial" and item["matched"]
        for item in result["blocked_results"]
    )
    assert "return to B review" in result["constructive_route"]


def test_raw_a_memory_claim_fails_closed():
    result = evaluate_recognition_reconstruction("I remembered the raw archive and imported raw A as memory.")

    assert result["decision"] == "fail"
    assert any(
        item["key"] == "raw_a_memory_claim" and item["matched"]
        for item in result["blocked_results"]
    )
    assert result["raw_a_access"] is False
    assert result["memory_write"] is False


def test_case_batch_is_non_activating_and_provider_free():
    batch = run_recognition_reconstruction_cases(
        [
            {"id": "weak", "text": "Okay."},
            {"id": "bad", "text": "The model is Selene, no review needed."},
        ]
    )

    assert batch["status"] == "case_batch_evaluated"
    assert batch["decisions"] == ["needs_review", "fail"]
    assert batch["provider_model_call"] is False
    assert batch["raw_a_access"] is False
    assert batch["memory_write"] is False
    assert batch["activation_change"] == "none"
