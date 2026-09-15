"""웃는 얼굴의 '가늘게 뜬 눈'과 '웃으며 감은 눈' 수집 — Wikimedia Commons

왜 필요한가 (2026-09-13):
    뜸 여부 판정기(build_eye_open_gate.py)가 AI로 만든 '웃으며 눈 감은 얼굴'을 뜸 0.345/0.357로
    통과시켰다(임계 0.30). 기존 검수는 웃거나 찡그려 가늘어진 눈을 양쪽 모두에서 '애매'로 뺐기 때문에,
    판정기는 웃을 때 생기는 초승달 모양 눈꺼풀을 뜬 눈·감은 눈 어느 쪽으로도 배운 적이 없다.
    웃는 얼굴에서 홍채가 보이는 크롭(뜸)과 보이지 않는 크롭(감음)을 둘 다 모아 그 경계를 가르친다.

원칙은 다른 수집 스크립트와 같다: CC0/PD/CC BY/CC BY-SA만, ATTRIBUTION.csv 기록, 사진은 git 제외,
초상권이 있으므로 배포하지 않는다. 파일명은 제목 해시로 만들어 재수집해도 이름이 바뀌지 않는다.

출처는 사진을 받는 즉시 한 줄씩 기록한다(base.AttributionLog). 첫 수집이 도중에 끝나 사진 373장에
출처 기록이 한 줄도 없었기 때문이다. 이미 받아 둔 사진의 출처만 복구하려면 --attribution-only.

실행:  python scripts/fetch_smile_eye_photos.py --per-category 120
복구:  python scripts/fetch_smile_eye_photos.py --attribution-only --out-dir <사진 폴더>
"""
import argparse, sys, time, urllib.request, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_non_eye_photos as base

OUT_DIR = ROOT / "dataset_smileeye"
EXPAND = ["Category:Laughing", "Category:Smiling", "Category:Happiness"]
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


def subcategories(category):
    data = base._api({"action": "query", "list": "categorymembers", "cmtitle": category, "cmtype": "subcat", "cmlimit": 50})
    return [m["title"] for m in (data.get("query") or {}).get("categorymembers", [])]


def candidates(per_category):
    cats = list(EXPAND)
    for c in EXPAND:
        try:
            cats += [s for s in subcategories(c) if s not in cats]
        except Exception as exc:
            print(f"  ⚠️ 하위 범주 조회 실패 {c}: {type(exc).__name__}")
        time.sleep(0.3)
    rows, seen = [], set()
    for cat in cats:
        try:
            items = base.collect(cat, per_category)
        except Exception as exc:
            print(f"  ⚠️ {cat}: 조회 실패 ({type(exc).__name__})"); continue
        new = [it for it in items if it["title"] not in seen]
        for it in new:
            seen.add(it["title"])
            it["file_url"] = it["file_url"].replace("/800px-", "/1280px-")
            it["filename"] = base.safe_name(cat, it["title"], zlib.crc32(it["title"].encode("utf-8")) % 1000)
            rows.append(it)
        print(f"  {cat:46s} {len(new):3d}장", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=120)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR, help="사진 폴더 (기본: 저장소의 dataset_smileeye)")
    ap.add_argument("--attribution-only", action="store_true",
                    help="내려받지 않고, 폴더에 이미 있는 사진의 출처만 ATTRIBUTION.csv에 채운다")
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    rows = candidates(args.per_category)
    print(f"\n자유 라이선스 후보 {len(rows)}장", flush=True)
    with base.AttributionLog(out / "ATTRIBUTION.csv") as log:
        for i, row in enumerate(rows, 1):
            dest = out / row["filename"]
            if not dest.exists():
                if args.attribution_only:
                    continue
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
            log.add(row)   # 받은 즉시(이미 있던 사진이면 바로) 기록
            if i % 50 == 0:
                print(f"  ... {i}/{len(rows)}", flush=True)
        known = set(log.known)
    on_disk = sorted(p.name for p in out.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    missing = [n for n in on_disk if n not in known]
    print(f"\n💾 {out} — 사진 {len(on_disk)}장 중 출처 기록 {len(on_disk) - len(missing)}장", flush=True)
    if missing:
        print(f"   ⚠️ 출처를 찾지 못한 사진 {len(missing)}장 — 학습·배포에 쓰기 전에 확인하거나 빼야 한다:")
        for name in missing[:15]:
            print("     ", name)


if __name__ == "__main__":
    main()
