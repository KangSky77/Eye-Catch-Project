"""웃는 얼굴의 '가늘게 뜬 눈'과 '웃으며 감은 눈' 수집 — Wikimedia Commons

왜 필요한가 (2026-09-13):
    뜸 여부 판정기(build_eye_open_gate.py)가 AI로 만든 '웃으며 눈 감은 얼굴'을 뜸 0.345/0.357로
    통과시켰다(임계 0.30). 기존 검수는 웃거나 찡그려 가늘어진 눈을 양쪽 모두에서 '애매'로 뺐기 때문에,
    판정기는 웃을 때 생기는 초승달 모양 눈꺼풀을 뜬 눈·감은 눈 어느 쪽으로도 배운 적이 없다.
    웃는 얼굴에서 홍채가 보이는 크롭(뜸)과 보이지 않는 크롭(감음)을 둘 다 모아 그 경계를 가르친다.

원칙은 다른 수집 스크립트와 같다: CC0/PD/CC BY/CC BY-SA만, ATTRIBUTION.csv 기록, 사진은 git 제외,
초상권이 있으므로 배포하지 않는다. 파일명은 제목 해시로 만들어 재수집해도 이름이 바뀌지 않는다.

실행:  python scripts/fetch_smile_eye_photos.py --per-category 120
"""
import argparse, csv, sys, time, urllib.request, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_non_eye_photos as base

OUT_DIR = ROOT / "dataset_smileeye"
ATTRIBUTION = OUT_DIR / "ATTRIBUTION.csv"
EXPAND = ["Category:Laughing", "Category:Smiling", "Category:Happiness"]


def subcategories(category):
    data = base._api({"action": "query", "list": "categorymembers", "cmtitle": category, "cmtype": "subcat", "cmlimit": 50})
    return [m["title"] for m in (data.get("query") or {}).get("categorymembers", [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=120)
    args = ap.parse_args()
    cats = list(EXPAND)
    for c in EXPAND:
        try:
            cats += [s for s in subcategories(c) if s not in cats]
        except Exception as exc:
            print(f"  ⚠️ 하위 범주 조회 실패 {c}: {type(exc).__name__}")
        time.sleep(0.3)
    OUT_DIR.mkdir(exist_ok=True)
    rows, seen = [], set()
    for cat in cats:
        try:
            items = base.collect(cat, args.per_category)
        except Exception as exc:
            print(f"  ⚠️ {cat}: 조회 실패 ({type(exc).__name__})"); continue
        new = [it for it in items if it["title"] not in seen]
        for it in new:
            seen.add(it["title"])
            it["file_url"] = it["file_url"].replace("/800px-", "/1280px-")
            it["filename"] = base.safe_name(cat, it["title"], zlib.crc32(it["title"].encode("utf-8")) % 1000)
            rows.append(it)
        print(f"  {cat:46s} {len(new):3d}장", flush=True)
    print(f"\n자유 라이선스 후보 {len(rows)}장", flush=True)
    ok = []
    for i, row in enumerate(rows, 1):
        dest = OUT_DIR / row["filename"]
        if not dest.exists():
            got = False
            for url in (row["file_url"], row["file_url"].replace("/1280px-", "/800px-")):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": base.UA})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        dest.write_bytes(resp.read())
                    got = True; break
                except Exception:
                    continue
            if not got:
                continue
            time.sleep(0.2)
        ok.append(row)
        if i % 50 == 0:
            print(f"  ... {i}/{len(rows)}", flush=True)
    with open(ATTRIBUTION, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["filename", "category", "title", "author", "license", "source_page", "file_url"])
        w.writeheader(); w.writerows(ok)
    print(f"\n💾 {OUT_DIR} 에 {len(ok)}장 — 출처 기록: {ATTRIBUTION}", flush=True)


if __name__ == "__main__":
    main()
