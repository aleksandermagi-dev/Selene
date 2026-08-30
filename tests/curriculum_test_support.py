from __future__ import annotations

from selene.curriculum_authorization import CURRICULUM_GROUP_MANIFESTS


def satisfy_group_prerequisites(conn, group_key: str) -> None:
    """Create disposable approved prerequisite rows for one synthetic group test."""
    manifest = CURRICULUM_GROUP_MANIFESTS[group_key]
    for concept_key in manifest["required_concept_keys"]:
        conn.execute(
            """
            INSERT OR IGNORE INTO selene_comprehension_concepts
            (concept_key, title, domain, central_claim, source_refs,
             provenance_boundary, retention_state, chat_use_permission,
             state, review_status, payload_json)
            VALUES (?, ?, 'synthetic.curriculum-prerequisite', ?, '["synthetic:test-only"]',
                    'synthetic disposable prerequisite fixture',
                    'retained_reviewed_knowledge', 'available_as_knowledge_resource',
                    'approved_knowledge_resource', 'approved', '{}')
            """,
            (concept_key, f"Synthetic prerequisite for {concept_key}", concept_key),
        )
    conn.commit()


def target_concept_keys(group_key: str) -> list[str]:
    return list(CURRICULUM_GROUP_MANIFESTS[group_key]["concept_keys"])


def group_concept_rows(conn, group_key: str):
    concept_keys = target_concept_keys(group_key)
    placeholders = ",".join("?" for _ in concept_keys)
    return conn.execute(
        f"SELECT * FROM selene_comprehension_concepts WHERE concept_key IN ({placeholders}) ORDER BY id",
        concept_keys,
    ).fetchall()
