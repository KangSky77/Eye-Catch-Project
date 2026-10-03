"""Manifest-locked cataract pilot training; never overwrites the active model.

Commands: prepare, train, compare. Test is frozen at prepare and is never used
for checkpoint selection. Results are research evidence, not clinical accuracy.
"""
import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from collect_licensed_eye_photos import allowed_license


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read_manifest(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    records = data["records"]
    ids, groups, group_labels = set(), defaultdict(set), defaultdict(set)
    for r in records:
        if r["id"] in ids:
            raise ValueError("duplicate image ID")
        ids.add(r["id"])
        declared = r.get("source_type") == "kaggle"
        policy_ok = data.get("permission_policy") == "publisher-declared-research; upstream permissions unresolved"
        licence_ok = allowed_license(r.get("license")) or (declared and policy_ok and r.get("license") in ("MIT", "Apache 2.0"))
        if r.get("review") != "accepted" or not licence_ok:
            raise ValueError("unreviewed or unlicensed image")
        if declared and (not policy_ok or r.get("provenance") != "publisher-declared; upstream unresolved"):
            raise ValueError("publisher declaration cannot be silently treated as original permission")
        if not r.get("source_page") or not r.get("original_id") or not r.get("evidence_path"):
            raise ValueError("source evidence missing")
        evidence_path = (ROOT / r["evidence_path"]).resolve()
        if not evidence_path.is_relative_to(ROOT):
            raise ValueError("evidence path outside workspace")
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        original_id = evidence.get("record_id") if declared else evidence.get("pageid")
        if evidence.get("license") != r["license"] or str(original_id) != r["original_id"]:
            raise ValueError("evidence does not match record")
        if declared:
            metadata_path = (ROOT / evidence["metadata_path"]).resolve()
            if not metadata_path.is_relative_to(ROOT) or evidence.get("source_url") != r["source_page"]:
                raise ValueError("publisher evidence does not match source")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("licenseName") != r["license"] or metadata.get("ownerName") != r["author"]:
                raise ValueError("publisher metadata does not match attribution")
        if r["license"].startswith("CC BY") and (not r.get("author") or evidence.get("author") != r["author"]):
            raise ValueError("attribution author missing or mismatched")
        image_path = (ROOT / r["path"]).resolve()
        if not image_path.is_relative_to(ROOT) or digest(image_path) != r["sha256"]:
            raise ValueError("image integrity mismatch")
        if r["label"] not in (0, 1) or r["split"] not in ("train", "val", "test"):
            raise ValueError("invalid label or split")
        groups[r["group"]].add(r["split"])
        group_labels[r["group"]].add(r["label"])
    if any(len(v) != 1 for v in groups.values()):
        raise ValueError("same original group crosses splits")
    if any(len(v) != 1 for v in group_labels.values()):
        raise ValueError("conflicting labels in same original group")
    for split in ("train", "val", "test"):
        if {r["label"] for r in records if r["split"] == split} != {0, 1}:
            raise ValueError(f"{split} must contain both classes")
    return data


def phash_one(path):
    from PIL import Image, ImageOps
    import imagehash
    with Image.open(path) as im:
        value = int(str(imagehash.phash(ImageOps.exif_transpose(im).convert("RGB"))), 16)
    return path, value


def hash_files(paths, cache):
    saved = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    signatures = {p: [Path(p).stat().st_size, Path(p).stat().st_mtime_ns] for p in paths}
    # Old integer-only caches have no integrity information and must be refreshed.
    results = {p: v["phash"] for p, v in saved.items()
               if p in signatures and isinstance(v, dict) and v.get("signature") == signatures[p]}
    missing = [p for p in paths if p not in results]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, (path, value) in enumerate(pool.map(phash_one, missing, chunksize=32), 1):
            results[path] = value
            if i % 2000 == 0:
                print(f"hashed {i}/{len(missing)}", flush=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({p: {"phash": h, "signature": signatures[p]} for p, h in results.items()}), encoding="utf-8")
    return results


def close_matches(value, values, threshold=6):
    return [p for p, h in values.items() if (value ^ h).bit_count() <= threshold]


def assign_splits(records, seed=42):
    rng = random.Random(seed)
    grouped = defaultdict(list)
    for r in records:
        grouped[r["group"]].append(r)
    conflicts = {g for g, rows in grouped.items() if len({r["label"] for r in rows}) != 1}
    if conflicts:
        raise ValueError("conflicting labels in duplicate group")
    assignment = {}
    for label in (0, 1):
        groups = sorted(g for g, rows in grouped.items() if rows[0]["label"] == label)
        eligible = [g for g in groups if all(r["baseline_eligible"] for r in grouped[g])]
        if len(eligible) < 2 or len(groups) < 4:
            raise ValueError(f"insufficient independent groups for class {label}: total {len(groups)}, baseline-unseen {len(eligible)}")
        rng.shuffle(eligible)
        n_test = min(max(1, round(len(groups) * .15)), len(eligible) - 1, len(groups) - 2)
        test = set(eligible[:n_test])
        remaining = [g for g in groups if g not in test]
        rng.shuffle(remaining)
        val = set(remaining[:max(1, round(len(groups) * .15))])
        for g in groups:
            assignment[g] = "test" if g in test else "val" if g in val else "train"
    return [{**r, "split": assignment[r["group"]]} for r in records]


def prepare(acquired, review, output):
    import subprocess
    rows = json.loads(acquired.read_text(encoding="utf-8"))["records"]
    choices = json.loads(review.read_text(encoding="utf-8"))
    accepted = [{**r, "review": "accepted", "review_note": choices[r["id"]]["note"], "group": choices[r["id"]].get("group", r["group"])} for r in rows if choices.get(r["id"], {}).get("decision") == "accept"]
    original = json.loads(subprocess.check_output(["git", "show", "1c03433:data/dataset_group_map.json"], cwd=ROOT, encoding="utf-8"))
    labels, grouped = defaultdict(set), defaultdict(list)
    for p, g in sorted(original.items()):
        labels[g].add(int("1_cataract" in p))
        grouped[g].append(p)
    rng, assignments = random.Random(42), {}
    for label in (0, 1):
        gids = [g for g in grouped if labels[g] == {label}]
        rng.shuffle(gids)
        nt, nv = max(1, int(len(gids)*.15)), max(1, int(len(gids)*.15))
        for i, g in enumerate(gids):
            assignments[g] = "test" if i < nt else "val" if i < nt+nv else "train"
    count = Counter((assignments.get(g, "excluded"), int("1_cataract" in p)) for p, g in original.items())
    metadata = json.loads((ROOT / "cataract_efficientnet_b0_v4_metadata.json").read_text(encoding="utf-8"))
    for split in ("train", "val", "test"):
        for label in (0, 1):
            if count[split, label] != metadata["counts"][split][str(label)]:
                raise ValueError("reconstructed baseline counts do not match metadata")
    paths = sorted({p.as_posix() for p in (ROOT / "dataset").rglob("*") if p.suffix.lower() in (".jpg", ".png", ".jpeg", ".webp", ".bmp")})
    hashes = hash_files(paths, ROOT / "compare/license-audit-20261002/legacy-phashes.json")
    # New/unmapped paths are conservatively treated as seen; cannot become test.
    baseline_seen = {p: h for p, h in hashes.items() if assignments.get(original.get(Path(p).relative_to(ROOT).as_posix()), "unknown") != "test"}
    for r in accepted:
        r["phash"] = phash_one(str(ROOT / r["path"]))[1]
        r["baseline_eligible"] = not close_matches(r["phash"], baseline_seen)
        r["legacy_matches"] = len(close_matches(r["phash"], hashes))
    # Merge ALL near duplicates transitively, including manually identified series.
    from dedup_dataset import UnionFind
    uf = UnionFind([r["id"] for r in accepted])
    for i, a in enumerate(accepted):
        for b in accepted[i + 1:]:
            if a["group"] == b["group"] or (a["phash"] ^ b["phash"]).bit_count() <= 6:
                uf.union(a["id"], b["id"])
    for r in accepted:
        r["group"] = uf.find(r["id"])
    records = assign_splits(accepted)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError("manifest already exists; choose a new output to preserve frozen test")
    data = {"version": "licensed-commons-pilot-20261002", "scope": "educational research pilot; labels need clinical confirmation", "seed": 42, "baseline_weights_sha256": digest(ROOT / "cataract_efficientnet_b0_v4.pth"), "baseline_group_map_git": "1c03433", "dedup_phash_distance": 6, "records": records, "excluded_review_ids": [r["id"] for r in rows if choices.get(r["id"], {}).get("decision") != "accept"]}
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    read_manifest(output)
    print(json.dumps({"counts": dict(Counter(f"{r['split']}/{r['label']}" for r in records)), "groups": len({r["group"] for r in records})}, ensure_ascii=False), flush=True)


def output_directory(path):
    path = path.resolve()
    allowed = (ROOT / "model_archive/licensed_pilot").resolve()
    if not path.is_relative_to(allowed) or path == allowed:
        raise ValueError("training output must be a new directory under model_archive/licensed_pilot")
    if path.exists():
        raise ValueError("output directory already exists")
    return path


def train(manifest, output, seed, batch, pretrained):
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
    from PIL import Image, ImageOps
    from train_ai_v3 import set_seed, train_tf, eval_tf, make_sampler, train_phase, device, LR_HEAD, LR_FINETUNE
    from app.models.cataract_model import build_model, head_param_prefix
    output = output_directory(output)
    data = read_manifest(manifest)
    data["manifest_sha256"] = digest(manifest)
    active = digest(ROOT / "cataract_efficientnet_b0_v4.pth")
    if active != data["baseline_weights_sha256"]:
        raise ValueError("active baseline changed after manifest was frozen")
    set_seed(seed)
    torch.set_num_threads(4)

    class Photos(Dataset):
        def __init__(self, split):
            self.rows = [r for r in data["records"] if r["split"] == split]
            self.tf = train_tf if split == "train" else eval_tf
        def __len__(self):
            return len(self.rows)
        def __getitem__(self, index):
            row = self.rows[index]
            with Image.open(ROOT / row["path"]) as im:
                return self.tf(ImageOps.exif_transpose(im).convert("RGB")), row["label"]
    tr, va = Photos("train"), Photos("val")
    if data.get("permission_policy"):
        group_sizes = Counter(r["group"] for r in tr.rows)
        class_groups = {label: len({r["group"] for r in tr.rows if r["label"] == label}) for label in (0, 1)}
        weights = [1/(class_groups[r["label"]]*group_sizes[r["group"]]) for r in tr.rows]
        sampler = WeightedRandomSampler(weights, num_samples=len(tr), replacement=True)
        sampler_policy = "class and original-group balanced"
    else:
        sampler = make_sampler([r["label"] for r in tr.rows])
        sampler_policy = "class balanced"
    train_loader = DataLoader(tr, batch_size=batch, sampler=sampler, num_workers=0)
    val_loader = DataLoader(va, batch_size=batch, shuffle=False, num_workers=0)
    model = build_model(pretrained=pretrained, backbone="efficientnet_b0").to(device)
    best = {"score": -1., "metrics": {}, "model": None}
    head = head_param_prefix("efficientnet_b0")
    loss = nn.CrossEntropyLoss()
    if pretrained:
        for name, p in model.named_parameters():
            p.requires_grad = name.startswith(head)
        opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=LR_HEAD)
        best = train_phase(model, train_loader, val_loader, loss, opt, 5, "licensed/head", best)
    for p in model.parameters():
        p.requires_grad = True
    opt = torch.optim.Adam(model.parameters(), lr=LR_FINETUNE)
    best = train_phase(model, train_loader, val_loader, loss, opt, 20, "licensed/finetune", best)
    if best["model"] is None:
        raise ValueError("no checkpoint selected")
    output.mkdir(parents=True)
    weights = output / "candidate.pth"
    torch.save(best["model"], weights)
    meta = {"version": data["version"], "backbone": "efficientnet_b0", "class_to_idx": {"0_normal": 0, "1_cataract": 1}, "seed": seed, "batch_size": batch, "manifest_sha256": data["manifest_sha256"], "baseline_weights_sha256": active, "weights_sha256": digest(weights), "best_val_metrics": best["metrics"], "initialization": "torchvision ImageNet1K V1 (educational research; upstream conditions separately recorded)" if pretrained else "random initialization; no pretrained image weights", "deployed": False, "test_evaluated": False}
    meta["image_size"] = 224
    meta["permission_policy"] = data.get("permission_policy", "Commons per-photo licence snapshot")
    meta["scope"] = data.get("scope")
    meta["sampler_policy"] = sampler_policy
    meta["training_recipe"] = {"head_epochs": 5 if pretrained else 0, "finetune_max_epochs": 20, "lr_finetune": LR_FINETUNE}
    meta["manifest_path"] = str(manifest)
    meta["normalization"] = {"mean": [.485, .456, .406], "std": [.229, .224, .225]}
    serialized = json.dumps(meta, ensure_ascii=False, indent=2)
    (output / "metadata.json").write_text(serialized, encoding="utf-8")
    (output / "candidate_metadata.json").write_text(serialized, encoding="utf-8")
    assert digest(ROOT / "cataract_efficientnet_b0_v4.pth") == active
    print(f"candidate saved: {weights}; active model preserved", flush=True)


def compare(manifest, candidates, output, full_pipeline=False, references=None):
    import torch
    from PIL import Image, ImageOps
    from train_ai_v3 import eval_tf, device
    from app.models.cataract_model import build_model
    from app.core.config import settings
    data = read_manifest(manifest)
    if output.exists():
        raise ValueError("comparison already exists; test is not a tuning loop")
    models = {"baseline_v6": ROOT / "cataract_efficientnet_b0_v4.pth"}
    for directory in candidates:
        meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        if meta["manifest_sha256"] != digest(manifest) or meta["weights_sha256"] != digest(directory / "candidate.pth"):
            raise ValueError("candidate not trained from this frozen manifest")
        models[f"candidate_{directory.name}"] = directory / "candidate.pth"
    for directory in references or []:
        meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        reference_manifest = ROOT / "data/licensed-cataract-manifest-2026-10-02.json"
        reference_data = read_manifest(reference_manifest)
        if meta["manifest_sha256"] != digest(reference_manifest) or meta["weights_sha256"] != digest(directory / "candidate.pth"):
            raise ValueError("reference weight or original manifest mismatch")
        if {r["id"]: r["sha256"] for r in reference_data["records"] if r["split"] == "test"} != {r["id"]: r["sha256"] for r in data["records"] if r["split"] == "test"}:
            raise ValueError("reference comparison test differs")
        models[f"reference_{directory.name}"] = directory / "candidate.pth"
    active = digest(models["baseline_v6"])
    if active != data["baseline_weights_sha256"]:
        raise ValueError("baseline hash mismatch")
    rows = [r for r in data["records"] if r["split"] == "test"]
    if any(not r["baseline_eligible"] for r in rows):
        raise ValueError("test contains baseline train/val near duplicate")
    predictions = []
    metrics = {}
    thresholds = [settings.uncertain_threshold/100, settings.borderline_threshold/100, settings.risk_threshold/100]
    uncertain, borderline, risk = thresholds
    torch.set_num_threads(4)
    for name, weights in models.items():
        model = build_model(backbone="efficientnet_b0").to(device)
        model.load_state_dict(torch.load(weights, map_location=device, weights_only=True))
        model.eval()
        scored = []
        with torch.no_grad():
            for row in rows:
                with Image.open(ROOT / row["path"]) as im:
                    x = eval_tf(ImageOps.exif_transpose(im).convert("RGB")).unsqueeze(0).to(device)
                p = model(x).softmax(1)[0, 1].item()
                if settings.use_tta:
                    p = (p + model(torch.flip(x, [3])).softmax(1)[0, 1].item())/2
                scored.append((row["label"], p))
                predictions.append({"model": name, "id": row["id"], "group": row["group"], "label": row["label"], "probability": p, "verdict": "risk" if p >= risk else "borderline" if p >= borderline else "uncertain" if p >= uncertain else "normal"})
        tp = sum(y == 1 and p >= risk for y, p in scored)
        tn = sum(y == 0 and p < risk for y, p in scored)
        fn = sum(y == 1 and p < risk for y, p in scored)
        fp = sum(y == 0 and p >= risk for y, p in scored)
        metrics[name] = {"tp": tp, "tn": tn, "fn": fn, "fp": fp, "sensitivity": tp/(tp+fn) if tp+fn else None, "specificity": tn/(tn+fp) if tn+fp else None, "normal_output_on_positive": sum(y == 1 and p < uncertain for y, p in scored), "normal_at_borderline_or_above": sum(y == 0 and p >= borderline for y, p in scored)}
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    pipeline_rows = []
    pipeline_metrics = {}
    if full_pipeline:
        from app.services import vision, eye_validator, eye_detector
        if not eye_validator.warmup() or not eye_detector.warmup():
            raise ValueError("full-pipeline input gate not ready")
        for name, weights in models.items():
            vision.model.load_state_dict(torch.load(weights, map_location=vision.device, weights_only=True))
            vision.model.eval()
            vision.weights_loaded = True
            for row in rows:
                with Image.open(ROOT / row["path"]) as im:
                    result = vision.predict_cataract(ImageOps.exif_transpose(im).convert("RGB"))
                pipeline_rows.append({"model": name, "id": row["id"], "label": row["label"], "result_code": result["result_code"], "score": result["probability"], "mode": result["mode"]})
            selected = [r for r in pipeline_rows if r["model"] == name]
            pipeline_metrics[name] = {"codes": dict(Counter(r["result_code"] for r in selected)), "by_label": {str(label): dict(Counter(r["result_code"] for r in selected if r["label"] == label)) for label in (0, 1)}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"manifest_sha256": digest(manifest), "baseline_weights_sha256": active, "tta": "horizontal flip average" if settings.use_tta else "disabled (current runtime setting)", "thresholds": thresholds, "test_images": len(rows), "test_groups": len({r["group"] for r in rows}), "metrics": metrics, "predictions": predictions, "pipeline_metrics": pipeline_metrics, "pipeline_predictions": pipeline_rows, "limitations": ["Small curated Commons corpus; proxy normal labels are not clinical diagnoses.", "Near-duplicate search does not prove absence of patient-level or heavy-crop overlap.", "Not a clinical or phone validation, and no auto deployment."]}, ensure_ascii=False, indent=2), encoding="utf-8")
    for directory in candidates:
        meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        meta.update(test_evaluated=True, comparison_path=str(output), comparison_sha256=digest(output))
        serialized = json.dumps(meta, ensure_ascii=False, indent=2)
        (directory / "metadata.json").write_text(serialized, encoding="utf-8")
        (directory / "candidate_metadata.json").write_text(serialized, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("--acquired", type=Path, required=True)
    a.add_argument("--review", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    a = sub.add_parser("train")
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--output", type=Path, required=True)
    a.add_argument("--seed", type=int, default=42)
    a.add_argument("--batch", type=int, default=8)
    a.add_argument("--pretrained", action="store_true")
    a = sub.add_parser("compare")
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--candidate", type=Path, action="append", required=True)
    a.add_argument("--output", type=Path, required=True)
    a.add_argument("--full-pipeline", action="store_true")
    a.add_argument("--reference", type=Path, action="append")
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args.acquired, args.review, args.output)
    elif args.command == "train":
        train(args.manifest, args.output, args.seed, args.batch, args.pretrained)
    else:
        compare(args.manifest, args.candidate, args.output, args.full_pipeline, args.reference)
