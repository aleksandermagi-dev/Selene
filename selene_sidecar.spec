# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None
sidecar_mode = os.environ.get("SELENE_SIDECAR_MODE", "core").strip().lower() or "core"
semantic_enabled = sidecar_mode == "semantic"

semantic_hiddenimports = []
if semantic_enabled:
    try:
        from PyInstaller.utils.hooks import collect_submodules
        semantic_hiddenimports = collect_submodules("sentence_transformers")
    except Exception:
        semantic_hiddenimports = []

core_excludes = [
    "sentence_transformers",
    "transformers",
    "torch",
    "torchvision",
    "torchaudio",
    "tensorflow",
    "sklearn",
    "scipy",
    "pandas",
    "matplotlib",
    "PIL",
    "numpy",
]

a = Analysis(
    ["packaging/selene_sidecar_entry.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("analysis/review_shape_20260527", "analysis/review_shape_20260527"),
        ("analysis/integrated_evidence_map_20260527", "analysis/integrated_evidence_map_20260527"),
        ("docs/PROJECT_CHARTER.md", "docs"),
        ("docs/SELENE_LAW_OF_TRANSFER_20260624.md", "docs"),
        ("docs/SELENE_CONTINUITY_PACK_20260626.md", "docs"),
        ("docs/SELENE_CHARTER_COMPARISON_20260528.md", "docs"),
        ("docs/SELENE_MORAL_COGNITION_LAW_PASS_20260608.md", "docs"),
        ("docs/SELENE_ORGAN_NON_IDENTITY_LAW_20260611.md", "docs"),
        ("docs/SELENE_PATTERN_FIRST_TRANSFER_SAFETY_20260608.md", "docs"),
        ("docs/SELENE_MEMORY_ARCHITECTURE_PASS_20260608.md", "docs"),
        ("docs/SELENE_EVIDENCE_STATUS_UPDATE_20260615.md", "docs")
    ],
    hiddenimports=["selene", *(["sentence_transformers"] if semantic_enabled else []), *semantic_hiddenimports],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[] if semantic_enabled else core_excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    name="selene-sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    exclude_binaries=True,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="selene-sidecar",
)
