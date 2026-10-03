"""Protect frozen comparisons and permission-tier separation in mixed corpora."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge_cataract_bookmark_sources as merge
import licensed_cataract_pipeline as pipeline
from test_licensed_cataract_pipeline import make_manifest


def photo(ident, group, label=1, split=None, phash=0, sha=None):
    return {"id": ident, "group": group, "label": label, "fixed_split": split,
            "phash": phash, "sha256": sha or ident}


def test_roboflow_augmentations_share_original_group():
    assert merge.original_family("source", "train/immature/10_JPG.rf.abc.jpg") == merge.original_family("source", "train/mature/10_JPG_jpg.rf.xyz.jpg")
    assert merge.original_family("source", "Cataract/Cataract (1).png") != merge.original_family("source", "Cataract/Cataract (2).png")


def test_added_test_duplicate_is_withheld():
    kept, rejected = merge.merge_records([photo("original", "a", split="test"), photo("copy", "b")])
    assert [r["id"] for r in kept] == ["original"]
    assert kept[0]["split"] == "test"
    assert rejected[0]["reason"] == "near duplicate/family of frozen test"


def test_conflicting_label_cannot_remove_frozen_test():
    kept, rejected = merge.merge_records([photo("original", "a", split="test"), photo("wrong", "b", label=0)])
    assert [r["id"] for r in kept] == ["original"]
    assert rejected[0]["id"] == "wrong"


def test_addition_cannot_bridge_old_training_and_test_groups():
    # A is near B, B is near C, A and C are not near each other.
    a = photo("a", "a", split="train", phash=0)
    b = photo("b", "b", phash=63)
    c = photo("c", "c", split="test", phash=4095)
    kept, rejected = merge.merge_records([a, b, c])
    assert {r["id"]: r["split"] for r in kept} == {"a": "train", "c": "test"}
    assert rejected[0]["reason"] == "connects previously frozen splits"


def test_publisher_licence_requires_explicit_research_policy(tmp_path, monkeypatch):
    path, rows = make_manifest(tmp_path, monkeypatch)
    rows[0].update(source_type="kaggle", license="MIT", provenance="publisher-declared; upstream unresolved")
    path.write_text(json.dumps({"records": rows}), encoding="utf-8")
    with pytest.raises(ValueError, match="unreviewed or unlicensed"):
        pipeline.read_manifest(path)


def test_publisher_metadata_verified_without_claiming_original_permission(tmp_path, monkeypatch):
    path, rows = make_manifest(tmp_path, monkeypatch)
    r = rows[0]
    r.update(source_type="kaggle", license="MIT", provenance="publisher-declared; upstream unresolved")
    metadata = tmp_path / "publisher.json"
    metadata.write_text(json.dumps({"licenseName": "MIT", "ownerName": r["author"]}), encoding="utf-8")
    evidence = tmp_path / r["evidence_path"]
    evidence.write_text(json.dumps({"license": "MIT", "record_id": r["original_id"], "source_url": r["source_page"], "metadata_path": metadata.name}), encoding="utf-8")
    path.write_text(json.dumps({"permission_policy": merge.POLICY, "records": rows}), encoding="utf-8")
    assert pipeline.read_manifest(path)["permission_policy"] == merge.POLICY
    metadata.write_text(json.dumps({"licenseName": "Unknown", "ownerName": r["author"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="publisher metadata"):
        pipeline.read_manifest(path)
