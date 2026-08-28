from __future__ import annotations

from typing import Any


REFLECTIVE_LINEAGE_VERSION = "v1_origin_parent_destination_stop"


def build_reflective_lineage_receipt(
    *,
    origin_record_type: str,
    origin_record_id: Any,
    parent_record_type: str = "",
    parent_record_id: Any = None,
    destination: str = "held",
    destination_record_type: str = "",
    destination_record_id: Any = None,
    candidate_state: str = "provisional",
    source_refs: list[str] | None = None,
    terminal_stop_reason: str | None = None,
    duplicate_lineage_detected: bool = False,
) -> dict[str, Any]:
    """Return the shared Phase 3 handoff vocabulary.

    The receipt is descriptive connective tissue. It does not route, approve,
    retain, decide truth, or create authority for any participating system.
    """

    origin_type = str(origin_record_type or "unknown")
    parent_type = str(parent_record_type or "")
    destination_type = str(destination_record_type or "")
    refs = list(dict.fromkeys(str(ref) for ref in source_refs or [] if str(ref).strip()))[:100]
    return {
        "lineage_version": REFLECTIVE_LINEAGE_VERSION,
        "origin_record_type": origin_type,
        "origin_record_id": origin_record_id,
        "origin_ref": f"{origin_type}:{origin_record_id}",
        "parent_record_type": parent_type or None,
        "parent_record_id": parent_record_id,
        "parent_ref": (
            f"{parent_type}:{parent_record_id}"
            if parent_type and parent_record_id is not None
            else None
        ),
        "destination": str(destination or "held"),
        "destination_record_type": destination_type or None,
        "destination_record_id": destination_record_id,
        "destination_ref": (
            f"{destination_type}:{destination_record_id}"
            if destination_type and destination_record_id is not None
            else None
        ),
        "candidate_state": str(candidate_state or "provisional"),
        "source_refs": refs,
        "terminal_stop_reason": terminal_stop_reason,
        "duplicate_lineage_detected": bool(duplicate_lineage_detected),
        "provisional_until_responsible_owner_closes_fit": True,
        "automatic_truth_decision": False,
        "automatic_knowledge_retention": False,
        "automatic_memory_write": False,
        "automatic_cross_destination_routing": False,
    }
