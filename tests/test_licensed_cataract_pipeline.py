"""Prevent permission, split leakage, and active-model overwrite regressions."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import licensed_cataract_pipeline as pipeline
from collect_licensed_eye_photos import allowed_license


@pytest.mark.parametrize("licence", ["Unknown", "CC BY-NC 4.0", "CC BY-NC-ND 4.0", "CC BY-ND 4.0", "Copyrighted free use", "CC BY-SA 4.0 extra permission", "CC BY 4.9", "CC BY-SA 3.0 xx", ""])
def test_unresolved_and_restricted_conditions_are_not_allowlisted(licence):
    assert not allowed_license(licence)


@pytest.mark.parametrize("licence", ["Public domain", "CC0", "CC BY 4.0", "CC BY-SA 3.0", "CC BY-SA 3.0 at"])
def test_allowlisted_conditions(licence):
    assert allowed_license(licence)


def make_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    records = []
    for split in ("train", "val", "test"):
        for label in (0, 1):
            key = f"{split}{label}"
            image = tmp_path / f"{key}.jpg"
            image.write_bytes(key.encode())
            evidence = tmp_path / f"{key}.json"
            evidence.write_text(json.dumps({"license": "CC BY 4.0", "pageid": key, "author": "Example author"}), encoding="utf-8")
            records.append({"id": key, "path": image.name, "sha256": hashlib.sha256(key.encode()).hexdigest(), "review": "accepted", "license": "CC BY 4.0", "author": "Example author", "source_page": "https://commons.wikimedia.org/wiki/File:example.jpg", "original_id": key, "evidence_path": evidence.name, "label": label, "split": split, "group": key})
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"records": records}), encoding="utf-8")
    return manifest, records


def test_manifest_integrity_and_evidence_are_enforced(tmp_path, monkeypatch):
    manifest, rows = make_manifest(tmp_path, monkeypatch)
    assert len(pipeline.read_manifest(manifest)["records"]) == 6
    (tmp_path / rows[0]["path"]).write_bytes(b"replaced image")
    with pytest.raises(ValueError, match="integrity"):
        pipeline.read_manifest(manifest)


def test_evidence_cannot_be_substituted(tmp_path, monkeypatch):
    manifest, rows = make_manifest(tmp_path, monkeypatch)
    (tmp_path / rows[0]["evidence_path"]).write_text(json.dumps({"license": "Unknown", "pageid": rows[0]["id"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence does not match"):
        pipeline.read_manifest(manifest)


def test_duplicate_group_cannot_cross_splits(tmp_path, monkeypatch):
    manifest, rows = make_manifest(tmp_path, monkeypatch)
    rows[2]["group"] = rows[0]["group"]
    manifest.write_text(json.dumps({"records": rows}), encoding="utf-8")
    with pytest.raises(ValueError, match="crosses splits"):
        pipeline.read_manifest(manifest)


def test_attribution_author_cannot_be_removed(tmp_path, monkeypatch):
    manifest, rows = make_manifest(tmp_path, monkeypatch)
    rows[0]["author"] = ""
    manifest.write_text(json.dumps({"records": rows}), encoding="utf-8")
    with pytest.raises(ValueError, match="attribution author"):
        pipeline.read_manifest(manifest)


def test_same_original_cannot_have_conflicting_labels(tmp_path, monkeypatch):
    manifest, rows = make_manifest(tmp_path, monkeypatch)
    rows[1]["group"] = rows[0]["group"]
    manifest.write_text(json.dumps({"records": rows}), encoding="utf-8")
    with pytest.raises(ValueError, match="conflicting labels"):
        pipeline.read_manifest(manifest)


def test_phash_cache_refreshes_replaced_image(tmp_path, monkeypatch):
    from PIL import Image
    class InlinePool:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def map(self, func, items, **kwargs):
            return map(func, items)
    monkeypatch.setattr(pipeline, "ProcessPoolExecutor", InlinePool)
    photo, cache = tmp_path / "photo.png", tmp_path / "cache.json"
    im = Image.new("RGB", (64, 64), "white")
    im.paste("black", (0, 0, 32, 64))
    im.save(photo)
    first = pipeline.hash_files([str(photo)], cache)[str(photo)]
    im = Image.new("RGB", (96, 96), "white")
    im.paste("black", (0, 0, 96, 48))
    im.save(photo)
    second = pipeline.hash_files([str(photo)], cache)[str(photo)]
    assert first != second


def test_test_selection_only_uses_baseline_unseen_groups():
    rows = [{"id": f"{label}-{i}", "label": label, "group": f"{label}-{i}", "baseline_eligible": i < 3} for label in (0, 1) for i in range(10)]
    assigned = pipeline.assign_splits(rows)
    assert all(r["baseline_eligible"] for r in assigned if r["split"] == "test")
    assert assigned == pipeline.assign_splits(rows)


def test_no_independent_test_groups_does_not_silently_split_seen_photos():
    rows = [{"id": f"{label}-{i}", "label": label, "group": f"{label}-{i}", "baseline_eligible": False} for label in (0, 1) for i in range(10)]
    with pytest.raises(ValueError, match="insufficient independent"):
        pipeline.assign_splits(rows)


def test_training_output_cannot_target_active_model_or_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="under model_archive"):
        pipeline.output_directory(tmp_path / "candidate")
    approved = tmp_path / "model_archive/licensed_pilot/seed42"
    approved.mkdir(parents=True)
    with pytest.raises(ValueError, match="already exists"):
        pipeline.output_directory(approved)
