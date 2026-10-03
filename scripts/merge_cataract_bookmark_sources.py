"""Build an isolated publisher-declared research corpus; not a rights clearance.

Keep the previous Commons test/validation groups frozen. Kaggle mirror photos
are grouped by export IDs and visual near-duplicates, not counted twice.
"""
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageOps
import requests

from licensed_cataract_pipeline import ROOT, digest, read_manifest, phash_one
from dedup_dataset import UnionFind

POLICY = "publisher-declared-research; upstream permissions unresolved"
OUT = ROOT / "dataset_raw/bookmark_merge_20261003"
MANIFEST = ROOT / "data/cataract-bookmark-merge-manifest-2026-10-03.json"


def original_family(source, member):
    name = Path(member).name
    if ".rf." in name:
        name = name.split(".rf.")[0].lower()
        name = re.sub(r"(?:_jpg|_jpeg|_png)+$", "", name)
        return source + "/export/" + name
    stem = Path(name).stem
    # Numbered generic filenames are independent photos, not augmentation IDs.
    if not re.fullmatch(r"(?:cataract|normal|image|img)(?: \(\d+\))?", stem, re.I):
        stem = re.sub(r" \(\d+\)$", "", stem)
    return source + "/file/" + stem.lower()


def merge_records(rows):
    uf = UnionFind([r["id"] for r in rows])
    for i, a in enumerate(rows):
        for b in rows[i+1:]:
            if a["group"] == b["group"] or a["sha256"] == b["sha256"] or (a["phash"] ^ b["phash"]).bit_count() <= 6:
                uf.union(a["id"], b["id"])
    groups = defaultdict(list)
    for r in rows:
        groups[uf.find(r["id"])].append(r)
    merged, excluded = [], []
    for key, photos in groups.items():
        if len({r["label"] for r in photos}) > 1:
            if any(r.get("fixed_split") == "test" for r in photos):
                # Retain the original test row, exclude every conflicting addition.
                for r in photos:
                    if r.get("fixed_split") == "test": merged.append({**r, "group": key, "split": "test"})
                    else: excluded.append({"id": r["id"], "reason": "label conflict with frozen test"})
            else:
                excluded.extend({"id": r["id"], "reason": "conflicting group labels"} for r in photos)
            continue
        fixed = {r.get("fixed_split") for r in photos} - {None}
        # Do not let an addition connect old train/val/test groups across splits.
        if len(fixed) > 1:
            for r in photos:
                if r.get("fixed_split"):
                    merged.append({**r, "group": r["group"], "split": r["fixed_split"]})
                else:
                    excluded.append({"id": r["id"], "reason": "connects previously frozen splits"})
            continue
        split = next(iter(fixed)) if fixed else "train"
        for r in photos:
            # The original 26-photo comparison test is unchanged. Additions
            # matching it are withheld entirely, not new favorable test cases.
            if split == "test" and not r.get("fixed_split"):
                excluded.append({"id": r["id"], "reason": "near duplicate/family of frozen test"})
            else:
                merged.append({**r, "group": key, "split": split})
    # Remove byte-identical additions while preserving all old Commons rows.
    keep, seen = [], set()
    for r in sorted(merged, key=lambda r: (not bool(r.get("fixed_split")), r["id"])):
        if r["sha256"] in seen and not r.get("fixed_split"):
            excluded.append({"id": r["id"], "reason": "identical processed photo"})
        else:
            keep.append(r); seen.add(r["sha256"])
    return keep, excluded


def main():
    if MANIFEST.exists() or (OUT / "acquired.json").exists():
        raise ValueError("merged snapshot already exists; do not overwrite it")
    old_path = ROOT / "data/licensed-cataract-manifest-2026-10-02.json"
    old = read_manifest(old_path)
    rows = [{**r, "fixed_split": r["split"]} for r in old["records"]]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "images").mkdir(exist_ok=True)
    (OUT / "evidence").mkdir(exist_ok=True)
    archive_dir = ROOT / "dataset_raw/licensing_20261002"
    sources = [("kershrita/cataract", "kershrita__cataract.zip", "MIT"), ("sheemazain/cataract-classification-dataset-in-ds", "sheemazain__cataract-classification-dataset-in-ds.zip", "Apache 2.0")]
    inventory = []
    failures = []
    for source, zipname, required in sources:
        response = requests.get("https://www.kaggle.com/api/v1/datasets/view/"+source, timeout=45)
        response.raise_for_status(); metadata = response.json()
        if metadata.get("licenseName") != required:
            raise ValueError("publisher licence changed; review again")
        archive = archive_dir / zipname
        archive_hash = digest(archive)
        metadata_path = OUT / "evidence" / (source.split('/')[0] + "_metadata.json")
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        inventory.append({"source": source, "publisher_license": required, "metadata_snapshot": metadata_path.relative_to(ROOT).as_posix(), "zip_sha256": archive_hash, "upstream_permissions": "unresolved"})
        with zipfile.ZipFile(archive) as z:
            for member in z.namelist():
                if Path(member).suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
                    continue
                ident = source.split('/')[0] + "_" + hashlib.sha256(member.encode()).hexdigest()[:18]
                target = OUT / "images" / (ident + ".jpg")
                label = int(member.startswith("Cataract/") or member.startswith("train/"))
                try:
                    contents = z.read(member)
                    with Image.open(io.BytesIO(contents)) as im:
                        im = ImageOps.exif_transpose(im).convert("RGB")
                        im.thumbnail((800, 800)); im.save(target, quality=95)
                except (OSError, ValueError):
                    failures.append({"member": member, "source": source, "reason": "decode failure"}); continue
                evidence = {"record_id": member, "source_url": "https://www.kaggle.com/datasets/"+source, "license": required, "author": metadata.get("ownerName"), "author_role": "dataset uploader, not confirmed original photographer", "source_type": "kaggle", "checked_date": "2026-10-03", "zip_sha256": archive_hash, "member_sha256": hashlib.sha256(contents).hexdigest(), "upstream_permissions": "unresolved", "metadata_path": metadata_path.relative_to(ROOT).as_posix()}
                ep = OUT / "evidence" / (ident + ".json")
                ep.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
                rows.append({"id": ident, "path": target.relative_to(ROOT).as_posix(), "sha256": digest(target), "label": label, "label_basis": "uploader label; immature and mature are both cataract; clinical review pending", "source_type": "kaggle", "source_page": evidence["source_url"], "original_id": member, "evidence_path": ep.relative_to(ROOT).as_posix(), "author": evidence["author"], "license": required, "provenance": "publisher-declared; upstream unresolved", "review": "accepted", "review_note": "dataset-label research inclusion; not clinically reviewed", "group": original_family(source, member), "phash": phash_one(str(target))[1], "baseline_eligible": False, "modifications": "EXIF transpose; RGB; maximum 800px; JPEG quality 95"})
    acquired_count = len(rows)
    merged, excluded = merge_records(rows)
    # Added unanchored groups: validation only, never add to the old test.
    # Seed and assignment fixed before training; old 177 splits remain intact.
    import random
    rng = random.Random(20261003)
    for label in (0, 1):
        groups = sorted({r["group"] for r in merged if r["label"] == label and not r.get("fixed_split") and not any(q.get("fixed_split") for q in merged if q["group"] == r["group"])})
        rng.shuffle(groups)
        val = set(groups[:max(1, round(len(groups)*.15))]) if groups else set()
        for r in merged:
            if r["group"] in val: r["split"] = "val"
    fixed_test = {r["id"] for r in old["records"] if r["split"] == "test"}
    if {r["id"] for r in merged if r["split"] == "test"} != fixed_test:
        raise ValueError("original comparison test changed")
    out = {"version": "bookmark-publisher-declared-merge-20261003", "permission_policy": POLICY, "scope": "research feasibility only; not rights-cleared for presentation/public distribution", "baseline_weights_sha256": old["baseline_weights_sha256"], "base_manifest_sha256": digest(old_path), "sources": inventory, "records": merged, "excluded": excluded+failures, "before_dedup": acquired_count, "mirror_exclusion": "akshayramakrishnan28 archive has identical 410 image bytes; not counted twice"}
    MANIFEST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    read_manifest(MANIFEST)
    (OUT / "acquired.json").write_text(json.dumps({"image_count": acquired_count, "manifest": MANIFEST.relative_to(ROOT).as_posix()}), encoding="utf-8")
    print(json.dumps({"counts": dict(Counter(f"{r['split']}/{r['label']}" for r in merged)), "sources": dict(Counter(r.get('source_type','Commons') for r in merged)), "groups": len({r['group'] for r in merged}), "excluded": len(excluded), "policy": POLICY},ensure_ascii=False), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    main()
