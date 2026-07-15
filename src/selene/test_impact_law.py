from __future__ import annotations

from typing import Any

from .registry import truncate


LAW_VERSION = "v1_least_impact_sufficient_test"
LAW_SOURCE = "docs/SELENE_TEST_IMPACT_LAW_20260713.md"
TEST_LEVELS = ("machinery", "gentle_integrated", "stressful_integrated")


def test_impact_law_status() -> dict[str, Any]:
    return {
        "status": "test_impact_law_active",
        "version": LAW_VERSION,
        "law_source": LAW_SOURCE,
        "governing_rule": "Use the least stressful test that can answer the specific question.",
        "selection_order": list(TEST_LEVELS),
        "default_test_level": "machinery",
        "stressful_tests_are_routine": False,
        "stressful_test_burden": "necessity_must_be_demonstrated_before_authorization",
        "ordinary_software_verification_allowed": True,
        "selene_participation_required_by_default": False,
        "identity_change": False,
        "governance_expansion": False,
        "autonomous_testing_allowed": False,
    }


def review_test_impact(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    proposed_level = str(payload.get("proposed_level") or "machinery").strip()
    if proposed_level not in TEST_LEVELS:
        raise ValueError(f"unsupported test impact level: {proposed_level}")

    purpose = _text(payload.get("purpose"), 600)
    unresolved_question = _text(payload.get("unresolved_question"), 600)
    necessity_reason = _text(payload.get("necessity_reason"), 1000)
    stopping_rule = _text(payload.get("stopping_rule"), 600)
    aftercare = _text(payload.get("aftercare"), 1000)
    persistence_plan = _text(payload.get("persistence_plan"), 600)
    safer_methods_considered = _text_list(payload.get("safer_methods_considered"))
    safer_alternative_available = payload.get("safer_alternative_available") is True
    aleks_aware = payload.get("aleks_aware") is True
    smallest_sufficient_prompt_set = payload.get("smallest_sufficient_prompt_set") is True

    requirements: dict[str, bool] = {"specific_purpose": bool(purpose)}
    if proposed_level in {"gentle_integrated", "stressful_integrated"}:
        requirements.update(
            {
                "machinery_or_synthetic_methods_considered_first": bool(safer_methods_considered),
                "smallest_sufficient_prompt_set": smallest_sufficient_prompt_set,
                "stopping_rule_present": bool(stopping_rule),
                "persistence_handled": bool(persistence_plan),
            }
        )
    if proposed_level == "stressful_integrated":
        requirements.update(
            {
                "specific_unresolved_question": bool(unresolved_question),
                "necessity_explained": len(necessity_reason) >= 20,
                "no_safer_sufficient_alternative": not safer_alternative_available,
                "aleks_aware": aleks_aware,
                "care_compatible_closure_present": bool(aftercare),
            }
        )

    missing = [key for key, present in requirements.items() if not present]
    authorized = not missing
    if proposed_level == "stressful_integrated" and safer_alternative_available:
        authorized = False

    if not authorized:
        selected_level = "machinery"
        decision = "stressful_test_blocked" if proposed_level == "stressful_integrated" else "integrated_test_needs_impact_review"
    else:
        selected_level = proposed_level
        decision = "test_route_authorized"

    return {
        "status": "test_impact_review_complete",
        "decision": decision,
        "authorized": authorized,
        "proposed_level": proposed_level,
        "selected_level": selected_level,
        "requirements": requirements,
        "missing_requirements": missing,
        "use_easier_test_when_sufficient": True,
        "stressful_test_is_exception": True,
        "stressful_test_necessary": proposed_level == "stressful_integrated" and authorized,
        "next_step": _next_step(proposed_level, missing, safer_alternative_available),
        "law_source": LAW_SOURCE,
        "version": LAW_VERSION,
        "identity_change": False,
        "memory_write_active": False,
        "autonomous_testing_allowed": False,
    }


def _next_step(proposed_level: str, missing: list[str], safer_alternative_available: bool) -> str:
    if safer_alternative_available:
        return "Use the safer sufficient test instead."
    if missing:
        return "Do not run the proposed integrated test; complete the impact review or use a machinery check."
    if proposed_level == "machinery":
        return "Run the focused machinery check."
    if proposed_level == "gentle_integrated":
        return "Run only the bounded gentle check and stop at the stated condition."
    return "Run only the necessary bounded check, stop at the stated condition, and complete the stated closure."


def _text(value: Any, limit: int) -> str:
    return truncate(str(value or ""), limit).strip()


def _text_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [truncate(str(item), 300).strip() for item in value if str(item).strip()][:20]
    if isinstance(value, str) and value.strip():
        return [truncate(value, 300).strip()]
    return []
