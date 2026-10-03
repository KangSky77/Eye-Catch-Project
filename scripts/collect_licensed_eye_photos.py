"""Acquire attributed Commons photos into a separate, non-deployed pilot corpus.

Every accepted file has a publisher licence snapshot and original identifier.
Category membership is NOT a clinical label; the review step is mandatory.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
API = "https://commons.wikimedia.org/w/api.php"
UA = "Eye-Catch-research/1.0 (https://github.com/KangSky77/Eye-Catch-Project)"


def allowed_license(value):
    return bool(re.fullmatch(r"(?:Public domain|CC0(?: 1\.0)?|CC BY(?:-SA)? (?:1\.0|2\.0|2\.5|3\.0|4\.0)(?: (?:at|fr|au))?)", value or ""))


def strip(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def api(params):
    response = requests.get(API, params={**params, "format": "json"}, headers={"User-Agent": UA}, timeout=45)
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise ValueError(result["error"].get("code", "Commons API error"))
    return result


def category_titles(category):
    titles, continuation = [], {}
    while True:
        data = api({"action": "query", "list": "categorymembers", "cmtitle": category, "cmtype": "file", "cmlimit": 500, **continuation})
        titles.extend(r["title"] for r in data.get("query", {}).get("categorymembers", []))
        if "continue" not in data:
            return titles
        continuation = data["continue"]


def collect(output):
    if not output.is_relative_to(ROOT):
        raise ValueError("acquisition output must stay within the workspace")
    if (output / "acquired.json").exists():
        raise ValueError("acquisition snapshot already exists; use a new output directory")
    output.mkdir(parents=True, exist_ok=True)
    snapshot_dir = output / "evidence"
    snapshot_dir.mkdir(exist_ok=True)
    with (ROOT / "data/brightiris_attributions.csv").open(encoding="utf-8-sig", newline="") as f:
        normals = list(csv.DictReader(f))
    labels = {r["original_title"]: (0, "legacy clear-eye proxy; not clinically confirmed") for r in normals if r["original_title"]}
    for title in category_titles("Category:Human cataracts"):
        labels.setdefault(title, (1, "Commons cataract category; photo review required"))
    pages = []
    titles = sorted(labels)
    for start in range(0, len(titles), 50):
        response = api({"action": "query", "titles": "|".join(titles[start:start + 50]), "redirects": 1, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime|timestamp|sha1", "iiurlwidth": 800})
        alias = {r["to"]: r["from"] for key in ("normalized", "redirects") for r in response.get("query", {}).get(key, [])}
        for page in response.get("query", {}).get("pages", {}).values():
            title = page.get("title", "")
            original = title
            for _ in range(3):
                original = alias.get(original, original)
            if original in labels:
                page["pilot_label"], page["label_basis"] = labels[original]
                pages.append(page)
        time.sleep(0.15)
    excluded = []

    def download(page):
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        get = lambda k: meta.get(k, {}).get("value", "")
        licence = get("LicenseShortName")
        author = strip(get("Artist"))
        title = page.get("title", "")
        reason = None
        if not allowed_license(licence):
            reason = "licence outside allowlist or no metadata"
        elif licence.startswith("CC BY") and not author:
            reason = "attribution author missing"
        elif info.get("mime") not in ("image/jpeg", "image/png", "image/tiff"):
            reason = "unsupported media (no SVG, PDF, animation)"
        if reason:
            return None, {"title": title, "reason": reason, "license": licence}
        stem = f"commons_{page['pageid']}"
        target = output / "images" / (stem + ".jpg")
        target.parent.mkdir(exist_ok=True)
        original_sha = None
        if not target.exists():
            url = info.get("thumburl") or info["url"]
            response = requests.get(url, headers={"User-Agent": UA}, timeout=60)
            response.raise_for_status()
            if len(response.content) > 30 * 1024 * 1024:
                raise ValueError("image exceeds acquisition limit")
            original_sha = hashlib.sha256(response.content).hexdigest()
            with Image.open(io.BytesIO(response.content)) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((800, 800))
                im.save(target, quality=95)
        evidence = {"title": title, "pageid": page["pageid"], "license": licence, "license_url": get("LicenseUrl"), "author": author, "original_url": info.get("url"), "download_url": info.get("thumburl") or info.get("url"), "original_timestamp": info.get("timestamp"), "original_sha1": info.get("sha1"), "source": strip(get("Credit")), "permission": strip(get("Permission")), "checked_date": datetime.now(timezone.utc).date().isoformat(), "download_sha256": original_sha}
        evidence_path = snapshot_dir / (stem + ".json")
        if not evidence_path.exists():
            evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        record = {"id": stem, "path": target.relative_to(ROOT).as_posix(), "label": page["pilot_label"], "label_basis": page["label_basis"], "source_id": "Wikimedia Commons", "source_page": "https://commons.wikimedia.org/wiki/" + quote(title.replace(" ", "_")), "original_id": str(page["pageid"]), "author": author, "license": licence, "license_url": get("LicenseUrl"), "evidence_path": evidence_path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "modifications": "Commons thumbnail; EXIF transpose; RGB; maximum 800px; JPEG quality 95", "review": "pending", "group": stem, "title": title}
        return record, None

    def safely(page):
        for attempt in range(3):
            try:
                return download(page)
            except (requests.RequestException, ValueError, OSError) as exc:
                if attempt == 2:
                    return None, {"title": page.get("title"), "reason": f"acquisition failed: {type(exc).__name__}"}
                time.sleep(1 + attempt)

    records = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        for record, failure in executor.map(safely, pages):
            if record:
                records.append(record)
            if failure:
                excluded.append(failure)
    (output / "acquired.json").write_text(json.dumps({"records": records, "excluded": excluded}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"acquired": len(records), "class0": sum(r["label"] == 0 for r in records), "class1": sum(r["label"] == 1 for r in records), "excluded": len(excluded)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dataset_raw/licensed_pilot_20261002")
    args = parser.parse_args()
    collect(args.output.resolve())
