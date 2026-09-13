"""눈 게이트 학습용 '감은 눈' 실제 사진 수집 — Wikimedia Commons

왜 필요한가 (2026-09-13 실측):
    AI로 만든 얼굴 사진 세 장(두 눈 감음·웃으며 감음·윙크)이 전부 게이트를 통과해
    '뚜렷한 혼탁 특징 없음 0/100'이 나갔다. 감긴 눈꺼풀 크롭의 게이트 점수는
    0.897~0.978로 임계값 0.60보다 한참 높았다. 원인은 학습 음성의 구성이다 —
    '가려진 눈'은 홍채 위를 단색 박스로 덮은 합성 이미지뿐이고 실제로 감긴 눈꺼풀
    (주름·속눈썹 선·피부)은 한 번도 음성으로 들어간 적이 없다.

수집 원칙은 scripts/fetch_non_eye_photos.py와 같다:
    - CC0 / 퍼블릭 도메인 / CC BY / CC BY-SA만. 파일마다 제목·저자·라이선스·원본 URL을
      ATTRIBUTION.csv에 남긴다.
    - 저장 위치는 dataset_closedeye/ (git 제외). 기록 파일만 커밋한다.
    - 받은 뒤 반드시 크롭을 눈으로 검수한다(scripts/review_closed_eye_crops.py) —
      '수면' 범주에도 눈을 뜬 사진이 섞여 있고, 뜬 눈이 음성에 들어가면 앱이 받아들여야
      할 사진을 거부하도록 가르치게 된다.

실행:
    python scripts/fetch_closed_eye_photos.py --dry-run
    python scripts/fetch_closed_eye_photos.py --per-category 120
"""
import argparse, csv, sys, time, urllib.request, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_non_eye_photos as base   # 라이선스 필터·API 예절·파일명 규칙을 그대로 쓴다

OUT_DIR = ROOT / "dataset_closedeye"
ATTRIBUTION = OUT_DIR / "ATTRIBUTION.csv"

# 하위 범주까지 한 단계 내려가는 범주(자체 파일이 적고 하위 범주가 많다)
EXPAND = ["Category:Closed eyes", "Category:People with closed eyes", "Category:Sleeping people"]
CATEGORIES = [
    "Category:Closed eyes",
    "Category:People with closed eyes",
    "Category:Sleeping people",
    "Category:Sleeping women",
    "Category:Sleeping men",
    "Category:Sleeping children",
    "Category:Sleeping babies",
    "Category:Blinking",
    "Category:Meditation",
    # 1차 수집 179장에서 얼굴이 잡힌 사진이 3분의 1뿐이었다(대부분 멀리서 찍은 전신 수면 사진).
    # 눈을 감는 순간이 얼굴 가까이 찍히는 범주를 더한다.
    "Category:Yawning people",
    "Category:Yawning",
    "Category:Napping",
    "Category:Sleeping girls",
    "Category:Sleeping boys",
    "Category:Sleeping soldiers",
    "Category:Sneezing",
    "Category:People praying",
    "Category:Relaxation",
    "Category:Sunbathing",
    "Category:Eyelids",
]


def subcategories(category: str) -> list[str]:
    data = base._api({"action": "query", "list": "categorymembers", "cmtitle": category,
                      "cmtype": "subcat", "cmlimit": 50})
    return [m["title"] for m in (data.get("query") or {}).get("categorymembers", [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=120)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cats = list(CATEGORIES)
    for c in EXPAND:
        try:
            cats += [s for s in subcategories(c) if s not in cats]
        except Exception as exc:
            print(f"  ⚠️ 하위 범주 조회 실패 {c}: {type(exc).__name__}")
        time.sleep(0.3)

    # 폭 1280px — 게이트는 224로 줄여 쓰지만, 인물 사진에서 눈 크롭을 잘라내려면
    # 얼굴이 충분히 커야 한다(eye_detector의 최소 크롭 크기).
    base_collect = base.collect
    rows, seen = [], set()
    OUT_DIR.mkdir(exist_ok=True)
    for cat in cats:
        try:
            items = base_collect(cat, args.per_category)
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
        print(f"  {cat:48s} {len(new):3d}장")
    print(f"\n자유 라이선스 후보 {len(rows)}장")
    if args.dry_run:
        print("(dry-run: 내려받지 않음)"); return

    ok = []
    for i, row in enumerate(rows, 1):
        dest = OUT_DIR / row["filename"]
        if not dest.exists():
            try:
                req = urllib.request.Request(row["file_url"], headers={"User-Agent": base.UA})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    dest.write_bytes(resp.read())
            except Exception as exc:
                # 1280px 썸네일이 없는 작은 원본은 800px 주소로 한 번 더 시도
                try:
                    req = urllib.request.Request(row["file_url"].replace("/1280px-", "/800px-"),
                                                 headers={"User-Agent": base.UA})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        dest.write_bytes(resp.read())
                except Exception:
                    print(f"  ⚠️ 실패 {row['filename']}: {type(exc).__name__}"); continue
            time.sleep(0.2)
        ok.append(row)
        if i % 50 == 0:
            print(f"  ... {i}/{len(rows)}", flush=True)

    with open(ATTRIBUTION, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["filename", "category", "title", "author",
                                          "license", "source_page", "file_url"])
        w.writeheader(); w.writerows(ok)
    print(f"\n💾 {OUT_DIR} 에 {len(ok)}장 — 출처·라이선스 전수 기록: {ATTRIBUTION}")
    print("   ⚠️ 학습 전에 scripts/review_closed_eye_crops.py로 크롭을 눈으로 검수할 것.")


if __name__ == "__main__":
    main()
