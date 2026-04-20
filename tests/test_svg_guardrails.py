import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ankigarden/assets/manifest.json"


def test_manifest_svg_refs_exist_and_are_versioned():
    data = json.loads(MANIFEST.read_text())
    missing = []
    unversioned = []
    for asset in data["assets"]:
        rel = asset["file"]
        p = ROOT / "ankigarden" / rel
        if not p.exists():
            missing.append(rel)
        if not rel.startswith("assets/v2_cozy_handpainted/"):
            unversioned.append(rel)
    assert not missing, f"Missing SVG files: {missing}"
    assert not unversioned, f"Unversioned file refs: {unversioned[:10]}"


def test_no_duplicate_manifest_file_refs():
    data = json.loads(MANIFEST.read_text())
    refs = [asset["file"] for asset in data["assets"]]
    duplicates = sorted({ref for ref in refs if refs.count(ref) > 1})
    assert not duplicates, f"Duplicate manifest refs found: {duplicates[:10]}"


def test_svgs_include_viewbox_and_trimmed_whitespace():
    offenders = []
    for svg in (ROOT / "ankigarden/assets/v2_cozy_handpainted").rglob("*.svg"):
        text = svg.read_text(encoding="utf-8")
        if "viewBox=" not in text.split("\n", 1)[0] and "viewBox=" not in text[:400]:
            offenders.append((svg.as_posix(), "missing viewBox"))
        if "<!--" in text:
            offenders.append((svg.as_posix(), "contains comment"))
    assert not offenders, f"SVG optimization guardrail failures: {offenders[:10]}"
