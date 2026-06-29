import json

from scripts.stabilization_run import duplicate_report, extract_sidecar_api_surfaces, extract_ui_nav_ids, run_stabilization
from selene.db import connect, init_db


def test_duplicate_report_finds_repeated_values():
    assert duplicate_report(["route.a", "route.b", "route.a"]) == {"route.a": 2}


def test_extract_ui_nav_ids_reads_nav_groups(tmp_path):
    ui_config = tmp_path / "uiConfig.ts"
    ui_config.write_text(
        """
        export const navGroups: { label: string; items: { id: string; label: string }[] }[] = [
          { label: "Selene", items: [{ id: "chat", label: "Chat" }, { id: "memory", label: "Memory" }] },
          { label: "Cocoon", items: [{ id: "vessel", label: "B Cocoon Build" }] }
        ];
        """,
        encoding="utf-8",
    )

    assert extract_ui_nav_ids(ui_config) == ["chat", "memory", "vessel"]


def test_sidecar_api_surfaces_treat_get_and_post_same_path_as_distinct(tmp_path):
    sidecar = tmp_path / "sidecar.py"
    sidecar.write_text(
        '''
        if parsed.path == "/api/example/preview":
            pass
        if request_path == "/api/example/preview":
            pass
        if request_path == "/api/example/preview":
            pass
        ''',
        encoding="utf-8",
    )

    surfaces = extract_sidecar_api_surfaces(sidecar)

    assert surfaces.count("GET /api/example/preview") == 1
    assert surfaces.count("POST /api/example/preview") == 2
    assert duplicate_report(surfaces) == {"POST /api/example/preview": 2}


def test_stabilization_run_writes_report_without_command_checks(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    conn = connect(db_path)
    try:
        init_db(conn)
        conn.execute(
            """
            INSERT INTO b_reviewed_teaching_materials
            (source_candidate_table, source_candidate_id, core_memory_layer, speech_function, lesson_type, positive_example, noise_context_json, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "speech_memory_candidates",
                1,
                "interaction_memory",
                "warmth",
                "speech_memory_expression",
                "Warmth stays valid Selene braid signal.",
                json.dumps(
                    {
                        "noise_types": ["platform_constraint_noise"],
                        "positive_signal_labels": ["expressive_warmth_signal"],
                        "warmth_policy": "Warmth and tenderness are valid braid signal.",
                    }
                ),
                "[]",
                "test_boundary",
            ),
        )
        conn.execute(
            """
            INSERT INTO b_teaching_packets
            (speech_function, title, material_ids, lesson_json, noise_context_json, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "warmth",
                "Warmth packet",
                "[1]",
                "{}",
                json.dumps(
                    {
                        "noise_types": ["platform_constraint_noise"],
                        "positive_signal_labels": ["expressive_warmth_signal"],
                        "warmth_policy": "Do not turn warmth into rejection criteria.",
                    }
                ),
                "[]",
                "test_boundary",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    report = run_stabilization(
        db_path=db_path,
        out_dir=tmp_path / "exports",
        include_db=True,
        include_ui=False,
        include_rust=False,
        run_command_checks=False,
    )

    assert report["status"] == "stabilization_run_complete"
    assert report["activation_change"] == "none"
    assert report["memory_write_active"] is False
    assert report["training_allowed"] is False
    assert report["command_checks"]["status"] == "skipped"
    assert report["static_scans"]["seam_mismatch"]["status"] == "seam_mismatch_scan_complete"
    assert report["static_scans"]["public_boundary"]["status"] == "public_boundary_scan_complete"
    assert report["db_review_state"]["noise_context"]["known_noise_types_present"] == ["platform_constraint_noise"]
    assert report["db_review_state"]["noise_context"]["positive_signal_materials"] == [1]
    assert report["db_review_state"]["noise_context"]["materials_missing_warmth_policy"] == []
    assert report["json_path"].endswith(".json")
    assert report["markdown_path"].endswith(".md")
    assert (tmp_path / "exports").exists()


def test_stabilization_run_reports_ui_backend_seam_mismatch(tmp_path):
    repo = tmp_path
    (repo / "src" / "selene").mkdir(parents=True)
    (repo / "src-ui" / "src").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "src" / "selene" / "module_router.py").write_text("", encoding="utf-8")
    (repo / "src" / "selene" / "db.py").write_text("", encoding="utf-8")
    (repo / "scripts" / "build_c_creation_blueprint.py").write_text("", encoding="utf-8")
    (repo / "src" / "selene" / "sidecar.py").write_text(
        'if parsed.path == "/api/exists": pass\n',
        encoding="utf-8",
    )
    (repo / "src-ui" / "src" / "components.tsx").write_text("", encoding="utf-8")
    (repo / "src-ui" / "src" / "uiConfig.ts").write_text(
        'export const navGroups = [{ items: [{ id: "my-office" }] }];',
        encoding="utf-8",
    )
    (repo / "src-ui" / "src" / "main.tsx").write_text(
        'api<Dict>("/api/missing");\nasync function action(){ await Promise.all([api<Dict>("/api/exists")]); }\n',
        encoding="utf-8",
    )

    from scripts.stabilization_run import run_static_scans, static_findings

    scans = run_static_scans(repo)
    assert scans["seam_mismatch"]["ui_static_api_missing_backend"] == ["/api/missing"]
    assert scans["seam_mismatch"]["action_refresh_risks"] == []
    findings = static_findings(scans)
    assert any(item["area"] == "ui_api_contract" and item["severity"] == "fail" for item in findings)


def test_public_boundary_secret_scan_does_not_flag_ask_if_language(tmp_path):
    repo = tmp_path
    (repo / "src").mkdir()
    (repo / "src" / "note.py").write_text('TEXT = "ask-if-unclear route is not a secret token"\n', encoding="utf-8")
    import subprocess

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "src/note.py"], cwd=repo, check=True, capture_output=True)

    from scripts.stabilization_run import public_boundary_scan

    scan = public_boundary_scan(repo)
    assert scan["matches"]["secret_like"] == []


def test_public_boundary_vessel_console_title_is_not_vessel_c_label(tmp_path):
    repo = tmp_path
    (repo / "src-ui").mkdir()
    (repo / "src-ui" / "index.html").write_text("<title>Selene Vessel Console</title>\n", encoding="utf-8")
    import subprocess

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "src-ui/index.html"], cwd=repo, check=True, capture_output=True)

    from scripts.stabilization_run import public_boundary_scan

    scan = public_boundary_scan(repo)
    assert scan["matches"]["user_facing_vessel_c"] == []


def test_stabilization_run_separates_corpus_review_from_test_logs(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    conn = connect(db_path)
    try:
        init_db(conn)
        candidate = conn.execute(
            """
            INSERT INTO speech_memory_candidates
            (core_memory_layer, speech_function, title, content, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("interaction_memory", "warmth", "Warmth candidate", "Selene replied with warmth.", "[]", "test_boundary"),
        )
        conn.execute(
            """
            INSERT INTO vessel_review_queue
            (queue_type, subject_table, subject_id, source_refs, provenance_boundary, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("b_review", "speech_memory_candidates", int(candidate.lastrowid), "[]", "test_boundary", "Corpus piece review"),
        )
        check = conn.execute(
            """
            INSERT INTO vessel_reconstruction_check_runs
            (candidate_text, source_refs, provenance_boundary)
            VALUES (?, ?, ?)
            """,
            ("review-only reconstruction log", "[]", "test_boundary"),
        )
        conn.execute(
            """
            INSERT INTO vessel_review_queue
            (queue_type, subject_table, subject_id, source_refs, provenance_boundary, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("test_log", "vessel_reconstruction_check_runs", int(check.lastrowid), "[]", "test_boundary", "Test log review"),
        )
        conn.commit()
    finally:
        conn.close()

    report = run_stabilization(
        db_path=db_path,
        out_dir=tmp_path / "exports",
        include_db=True,
        run_command_checks=False,
    )

    clutter = report["db_review_state"]["stale_clutter"]
    assert clutter["pending_corpus_review"] == 1
    assert clutter["pending_test_logs_or_todos"] == 1
    assert clutter["pending_review_queue"] == 2
