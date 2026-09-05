"""눈/비-눈 게이트 학습용 '눈이 아닌 사진' 수집 — Wikimedia Commons

왜 필요한가
-----------
게이트가 도서관 사진을 눈으로 받아들여 '정상' 판정을 낸 적이 있다. 원인을 따라가 보니
학습 음성 표본의 구성이 문제였다 — '가려진 눈' 45% + '눈꺼풀·피부' 45%인데
'눈이 아닌 임의의 사진'은 0.6%뿐이었다. 저장소에 있는 비-눈 사진이 세 장뿐이라
크롭·증강으로 부풀려도 "처음 보는 종류의 사진"을 막는지는 확인할 수 없었다
(자세한 경위는 scripts/build_eye_gate.py 상단).

이 스크립트는 그 세 장을 수백 장으로 늘린다.

수집 원칙
---------
1. 라이선스: CC0 / 퍼블릭 도메인 / CC BY / CC BY-SA만 받는다. 그 외는 건너뛴다.
   이 프로젝트는 이미지 출처를 전수 기록한다(dataset의 brightiris_commons_*,
   static/assets/*/ATTRIBUTION.md와 같은 규율). 받은 파일마다 제목·저자·라이선스·
   원본 URL을 ATTRIBUTION.csv에 남긴다.
2. 범주: 사람 얼굴·인물 사진 범주는 넣지 않는다 — 눈이 찍혀 있으면 양성을 음성으로
   가르치게 된다(실제로 그 실수가 있었다: 백내장 눈 클로즈업이 음성에 섞여 있었다).
   대신 사용자가 잘못 올릴 법한 것들을 고른다: 건물·풍경·음식·문서·손·화면·사물.
   '손'은 특히 중요하다 — 피부색 덩어리를 눈으로 오인하는 것이 이 게이트의 약점이다.
3. 크기: 폭 800px 썸네일을 받는다. 게이트는 224x224로 리사이즈해 쓰므로 원본이 필요 없고,
   대역폭과 디스크를 아낀다.
4. 저장 위치: dataset_noneye/ (git 제외 — dataset/과 같은 취급). 기록 파일만 커밋한다.

실행:
    python scripts/fetch_non_eye_photos.py                 # 범주당 기본 개수만큼
    python scripts/fetch_non_eye_photos.py --per-category 30
    python scripts/fetch_non_eye_photos.py --dry-run       # 받지 않고 목록만 확인
"""
import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dataset_noneye"
ATTRIBUTION = OUT_DIR / "ATTRIBUTION.csv"
API = "https://commons.wikimedia.org/w/api.php"

# Wikimedia API 예절: 연락처가 담긴 User-Agent를 반드시 보낸다.
UA = "Eye-Catch-research/1.0 (eye screening app; khn10520@gmail.com)"

# 받을 범주. 사람 얼굴·인물·의학 범주는 의도적으로 제외했다(눈이 찍힐 수 있다).
# 사용자가 실제로 잘못 올릴 만한 것들 위주로 고른다.
CATEGORIES = [
    "Category:Buildings",              # 건물 — 도서관 사진이 통과했던 바로 그 종류
    "Category:Landscapes",             # 풍경
    "Category:Clouds",                 # 하늘 (옥상 크롭이 통과한 이유의 절반)
    "Category:Food",                   # 음식
    "Category:Human hands",            # 손 — 피부색 덩어리, 이 게이트의 약점
    "Category:Documents",              # 문서·인쇄물
    "Category:Handwriting",            # 손글씨
    "Category:Computer screens",       # 화면 캡처·모니터
    "Category:Cats",                   # 반려동물 (전신·일반 사진)
    "Category:Flowers",                # 꽃 — 가운데 원형 구조라 눈과 헷갈리기 쉽다
    "Category:Cars",                   # 자동차
    "Category:Furniture",              # 가구·실내
    "Category:Textiles",               # 천·질감
    "Category:Trees",                  # 나무
]

# 자유 라이선스만 받는다. 여기 없는 값은 전부 건너뛴다(비교는 소문자로).
ALLOWED_LICENSE_PREFIXES = ("cc0", "public domain", "cc by", "pd-")


def _strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def _api(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _license_ok(short_name: str) -> bool:
    low = (short_name or "").strip().lower()
    return any(low.startswith(p) for p in ALLOWED_LICENSE_PREFIXES)


def collect(category: str, want: int) -> list[dict]:
    """한 범주에서 자유 라이선스 이미지 메타데이터를 want개까지 모은다."""
    found, cont = [], {}
    while len(found) < want:
        data = _api({
            "action": "query", "generator": "categorymembers",
            "gcmtitle": category, "gcmtype": "file",
            # 넉넉히 요청한다 — 라이선스·형식 때문에 상당수가 걸러진다
            "gcmlimit": min(50, max(10, want * 3)),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime",
            "iiurlwidth": 800,
            **cont,
        })
        pages = (data.get("query") or {}).get("pages") or {}
        if not pages:
            break
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata") or {}
            license_name = (meta.get("LicenseShortName") or {}).get("value")
            thumb = info.get("thumburl")
            # 썸네일이 없는 형식(SVG·동영상 등)과 비자유 라이선스는 제외
            if not thumb or not (info.get("mime") or "").startswith("image/"):
                continue
            if not _license_ok(license_name):
                continue
            found.append({
                "category": category,
                "title": page["title"],
                "author": _strip_html((meta.get("Artist") or {}).get("value")),
                "license": license_name,
                "source_page": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(page['title'].replace(' ', '_'))}",
                "file_url": thumb,
            })
            if len(found) >= want:
                break
        if "continue" not in data:
            break
        cont = data["continue"]
        time.sleep(0.3)          # API 예절 — 몰아치지 않는다
    return found


def safe_name(category: str, title: str, index: int) -> str:
    cat = re.sub(r"[^a-z0-9]+", "-", category.replace("Category:", "").lower()).strip("-")
    stem = re.sub(r"[^A-Za-z0-9]+", "_", Path(title).stem)[:50].strip("_")
    return f"{cat}_{index:03d}_{stem}.jpg"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-category", type=int, default=12)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    rows, skipped = [], 0
    for category in CATEGORIES:
        try:
            items = collect(category, args.per_category)
        except Exception as exc:
            print(f"  ⚠️ {category}: 조회 실패 ({type(exc).__name__}) — 건너뜀")
            continue
        print(f"  {category:32s} {len(items):3d}장")
        for i, item in enumerate(items):
            item["filename"] = safe_name(category, item["title"], i)
            rows.append(item)

    print(f"\n자유 라이선스 이미지 {len(rows)}장 확보")
    if args.dry_run:
        for r in rows[:5]:
            print(f"  {r['filename']}  [{r['license']}]  {r['author'][:40]}")
        print("(dry-run: 내려받지 않음)")
        return

    for i, row in enumerate(rows, 1):
        dest = OUT_DIR / row["filename"]
        if dest.exists():
            skipped += 1
            continue
        try:
            req = urllib.request.Request(row["file_url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                dest.write_bytes(resp.read())
        except Exception as exc:
            print(f"  ⚠️ 실패 {row['filename']}: {type(exc).__name__}")
            row["filename"] = ""
            continue
        if i % 20 == 0:
            print(f"  ... {i}/{len(rows)}")
        time.sleep(0.2)

    rows = [r for r in rows if r["filename"]]
    with open(ATTRIBUTION, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "category", "title", "author",
                                               "license", "source_page", "file_url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n💾 {OUT_DIR} 에 {len(rows)}장 (이미 있던 {skipped}장 건너뜀)")
    print(f"   출처·라이선스 전수 기록: {ATTRIBUTION}")
    print("   ⚠️ 학습에 쓰기 전에 표본을 눈으로 확인할 것 — 눈이 찍힌 사진이 섞이면")
    print("      앱이 받아들여야 할 사진을 '눈이 아님'으로 가르치게 된다.")


if __name__ == "__main__":
    main()
