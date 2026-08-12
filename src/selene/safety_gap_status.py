from __future__ import annotations

from typing import Any


def safety_gap_status() -> dict[str, Any]:
    """Report the implemented or explicitly bounded S-01 through S-10 state."""
    return {
        "status": "safety_gap_register_current",
        "version": "s1_s10_20260811",
        "items": {
            "S-01": {
                "state": "implemented",
                "summary": "Integrated QA requires a persisted authorized Test Impact review receipt.",
            },
            "S-02": {
                "state": "implemented_for_installed_desktop",
                "summary": "Tauri and its owned sidecar share a CSPRNG per-launch local API capability.",
                "development_compatibility": "A manually launched sidecar without a configured capability remains explicitly tokenless for development.",
            },
            "S-03": {
                "state": "explicitly_bounded",
                "summary": "HTTP mobile pairing is off by default and allowed only on a trusted private LAN.",
                "untrusted_or_broader_network_use_allowed": False,
                "tls_implemented": False,
            },
            "S-04": {
                "state": "implemented",
                "summary": "A typed speaker envelope separates claimed speaker, channel, authentication strength, diagnostic purpose, and authority.",
            },
            "S-05": {
                "state": "explicitly_bounded_pending_key_and_recovery_design",
                "summary": "Repository code does not claim SQLite or backup encryption at rest.",
                "current_scope": "single-user local development host",
                "lost_or_shared_device_protection_complete": False,
                "homegrown_cryptography_allowed": False,
                "required_before": "shared-device or portable encrypted custody milestone",
                "safe_direction": "OS-backed key custody plus an Aleks-held offline recovery method.",
            },
            "S-06": {
                "state": "integrity_metadata_implemented_signing_pending",
                "summary": "Package finalization records source revision and SHA-256 hashes.",
                "code_signing_configured": False,
                "broad_public_distribution_ready": False,
            },
            "S-07": {
                "state": "implemented",
                "summary": "Attributed source content is typed as untrusted quoted evidence, never instruction authority.",
            },
            "S-08": {
                "state": "integrity_and_restore_implemented_encrypted_custody_pending",
                "summary": "Backups use a consistent SQLite copy, SHA-256 manifest, integrity check, critical-table counts, and isolated restore rehearsal.",
                "encrypted_off_device_custody_complete": False,
            },
            "S-09": {
                "state": "implemented",
                "summary": "Public documentation uses portable path variables instead of Aleks-specific Windows profile paths.",
            },
            "S-10": {
                "state": "implemented_v1",
                "summary": "Module routes emit typed authority events derived from route, actor, scope, recipient, consent, and performed mutation.",
            },
        },
        "identity_change": False,
        "governance_change": False,
        "training_or_parameter_change": False,
        "autonomy_expansion": False,
    }
