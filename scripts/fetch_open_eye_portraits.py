"""눈 뜸 여부 판정기 학습용 '뜬 눈' 인물 사진 수집 — Wikimedia Commons

왜 필요한가 (2026-09-13):
    기존 눈 게이트 하나에 감은 눈을 음성으로 더해 재학습해 보니, 학습에 쓰지 않은 감은 눈 통과는
    58.9% → 21.4%로 줄었지만 정상 눈 거부가 4.7% → 6.3%로 늘었고 AI로 만든 감은 눈 얼굴은 여전히
    통과했다. '눈이 아닌 사진'과 '감은 눈'을 한 판정기에 같이 가르치면 서로 부딪힌다.
    그래서 얼굴 모드의 눈 크롭만 보는 '뜸 여부' 판정기를 따로 둔다. 그 양성(얼굴 사진에서 잘라낸
    뜬 눈)이 필요하다 — dataset/의 눈 사진은 초근접이라 얼굴 크롭과 구도가 다르다.

.codex/face-audit-20260907의 인물 사진은 쓰지 않는다 — 그 수집 스크립트가 '학습에 쓰지 말 것'을
명시했다. 이 스크립트는 처음부터 학습용으로 받는다.

원칙은 fetch_non_eye_photos.py·fetch_closed_eye_photos.py와 같다:
    CC0 / 퍼블릭 도메인 / CC BY / CC BY-SA만, 파일마다 ATTRIBUTION.csv 기록, 사진은 git 제외.
    인물 사진이므로 저작권과 별개로 초상권이 있다 — 사진·크롭을 배포하지 않고 로컬 학습에만 쓴다.

실행:  python scripts/fetch_open_eye_portraits.py --per-category 80
"""
import argparse, csv, sys, time, urllib.request, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_non_eye_photos as base

OUT_DIR = ROOT / "dataset_openeye"
ATTRIBUTION = OUT_DIR / "ATTRIBUTION.csv"
CATEGORIES = [
    "Category:Portrait photographs of women",
    "Category:Portrait photographs of men",
    "Category:Portrait photographs",
    "Category:Selfies",
    "Category:Passport photographs",
    "Category:Portrait photographs of children",
    "Category:Portraits of old women",
    "Category:Portraits of old men",
    "Category:Human faces",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=80)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    OUT_DIR.mkdir(exist_ok=True)
    rows, seen = [], set()
    for cat in CATEGORIES:
        try:
            items = base.collect(cat, args.per_category)
        except Exception as exc:
            print(f"  ⚠️ {cat}: 조회 실패 ({type(exc).__name__})"); continue
        new = [it for it in items if it["title"] not in seen]
        for it in new:
            seen.add(it["title"])
            it["file_url"] = it["file_url"].replace("/800px-", "/1280px-")
            # 파일명의 번호는 실행 순번이 아니라 제목 해시로 만든다. 순번을 쓰면 범주를 더해 다시 받을 때
            # 같은 사진이 다른 이름으로 또 저장되고, 앞서 받은 파일은 출처 기록에서 빠진다(2026-09-13 실제 발생:
            # 1,437장 기록에 파일 1,840개).
            it["filename"] = base.safe_name(cat, it["title"], zlib.crc32(it["title"].encode("utf-8")) % 1000)
            rows.append(it)
        print(f"  {cat:46s} {len(new):3d}장", flush=True)
    print(f"\n자유 라이선스 후보 {len(rows)}장", flush=True)
    if args.dry_run:
        return
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
                print(f"  ⚠️ 실패 {row['filename']}"); continue
            time.sleep(0.2)
        ok.append(row)
        if i % 50 == 0:
            print(f"  ... {i}/{len(rows)}", flush=True)
    with open(ATTRIBUTION, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["filename", "category", "title", "author",
                                          "license", "source_page", "file_url"])
        w.writeheader(); w.writerows(ok)
    print(f"\n💾 {OUT_DIR} 에 {len(ok)}장 — 출처 기록: {ATTRIBUTION}")


if __name__ == "__main__":
    main()
