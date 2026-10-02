"""
실사진(폰 촬영) 검증 도구
================================================================
데이터셋 test 성능은 '데이터셋 안에서의' 수치다. 실제 폰으로 찍은
사진은 조명·화질·구도가 달라 성능이 떨어질 수 있으므로(도메인 갭), 시연 전에
팀원들의 실사진으로 배포 파이프라인을 그대로 통과시켜 미리 확인한다.

이 스크립트는 서버(vision.py)의 판독 함수를 직접 호출한다:
MTCNN 눈 크롭 → 눈 검증·화질 게이트 → EfficientNet(설정에 따른 TTA) → 4단계 판정(risk/borderline/uncertain/normal)

사용법:
    python scripts/validate_real_photos.py <사진 폴더>

폴더 구조 (라벨별 하위 폴더가 있으면 정답률까지 계산):
    real_photos/
      cataract/   백내장으로 알려진 눈 사진
      normal/     정상 눈 사진
      non_eye/    눈이 아닌 사진 (거부되는지 확인용, 선택)
    하위 폴더가 없으면 라벨 없이 예측 결과만 출력한다.
"""
import os
import sys
from pathlib import Path

# scripts/ 안에서 실행돼도 저장소 루트를 기준으로 동작하게 한다.
# (python scripts/x.py 로 실행하면 sys.path[0]이 scripts/라 app 패키지를 못 찾고,
#  dataset/ 같은 상대경로도 실행 위치에 따라 달라진다)
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # Windows cp949 콘솔에서도 안전하게

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

from app.services import vision, eye_validator, eye_detector

VERDICT_CODES = {"risk", "borderline", "uncertain", "normal"}
RETAKE_CODES = {"invalid", "dark", "low_resolution", "blurry", "hold", "eyes_hidden", "multiple_faces", "incomplete_eyes", "compressed", "unstable"}

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
LABEL_DIRS = ("cataract", "normal", "non_eye")


def load_image(path: Path) -> Image.Image:
    """서버의 validate_and_read_image와 동일한 전처리(EXIF 회전 + RGB)."""
    with Image.open(path) as img:
        return ImageOps.exif_transpose(img).convert("RGB")


def iter_images(folder: Path):
    """(라벨 또는 None, 파일경로) 나열. 라벨 하위 폴더가 있으면 그 안만 순회."""
    labeled = [d for d in LABEL_DIRS if (folder / d).is_dir()]
    if labeled:
        for d in labeled:
            for f in sorted((folder / d).rglob("*")):
                if f.is_file() and f.suffix.lower() in IMG_EXTS:
                    yield d, f
    else:
        for f in sorted(folder.rglob("*")):
            if f.is_file() and f.suffix.lower() in IMG_EXTS:
                yield None, f


def write_report(results, destination: Path):
    """Export counts and per-file outcomes; never copy photos or claim clinical accuracy."""
    destination.mkdir(parents=True, exist_ok=True)
    rows = [{"label": label or "unlabeled", "file": str(path), "result_code": code,
             "score": score if code != "error" else None, "mode": mode,
             "category": "verdict" if code in VERDICT_CODES else "retake" if code in RETAKE_CODES else "error"}
            for label, path, code, score, mode in results]
    summary = {"total": len(rows), "result_counts": dict(Counter(r["result_code"] for r in rows)),
               "labels": {}, "note": "Server pipeline only; browser resizing and real-device export need separate checks. This is not clinical validation."}
    for label in {r["label"] for r in rows}:
        selected = [r for r in rows if r["label"] == label]
        summary["labels"][label] = {"total": len(selected), "categories": dict(Counter(r["category"] for r in selected)),
                                     "codes": dict(Counter(r["result_code"] for r in selected))}
    with (destination / "photo-results.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["label", "file", "result_code", "score", "mode", "category"])
        writer.writeheader()
        writer.writerows(rows)
    (destination / "photo-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description="실사진으로 배포 파이프라인 검증")
    parser.add_argument("folder", help="사진 폴더 (하위에 cataract/normal/non_eye 폴더 권장)")
    parser.add_argument("--report-dir", type=Path, help="로컬 CSV·JSON 검증 결과를 내보낼 폴더 (사진은 복사하지 않음)")
    args = parser.parse_args()
    folder = Path(args.folder)
    if not folder.is_dir():
        raise SystemExit(f"폴더가 없습니다: {folder}")

    if not vision.load_trained_weights():
        raise SystemExit("가중치 로드 실패 — .env의 MODEL_PATH/MODEL_BACKBONE 확인")
    if not eye_validator.warmup():
        raise SystemExit("눈 검증기 로드 실패 — 인터넷 연결(최초 1회 가중치 다운로드) 확인")

    if not eye_detector.warmup():
        raise SystemExit("얼굴 검출기 준비 실패")

    results = []   # (label, path, result_code, probability, mode)
    for label, f in iter_images(folder):
        try:
            r = vision.predict_cataract(load_image(f))
            code, prob, mode = r["result_code"], r["probability"], r["mode"]
        except Exception as exc:
            print(f"분석 오류: {f.name}: {type(exc).__name__}")
            code, prob, mode = "error", 0.0, "-"
        results.append((label, f, code, prob, mode))
        # .get 폴백: 판정 코드가 새로 늘어나도(vision.py의 _classify 변경 등)
        # 검증 도구가 KeyError로 죽지 않고 끝까지 돌게 한다.
        mark = {"risk": "[위험]", "borderline": "[경계]", "normal": "[뚜렷한 혼탁 특징 없음]", "uncertain": "[판단 어려움]",
                "invalid": "[거부]", "error": "[오류]"}.get(code, f"[{code}]")
        print(f"{mark} {prob:5.1f}점  mode={mode:4s}  {f}")

    if not results:
        raise SystemExit("이미지가 없습니다.")

    if args.report_dir:
        write_report(results, args.report_dir)
        print(f"CSV·JSON 검증 결과: {args.report_dir}")

    print("\n" + "=" * 62)
    labels = {lab for lab, *_ in results if lab}
    if not labels:
        print("라벨 폴더(cataract/normal/non_eye)가 없어 예측 요약만 표시합니다.")
        print(dict(Counter(code for _, _, code, _, _ in results)))
        return

    for lab in LABEL_DIRS:
        rows = [(c, p) for l, _, c, p, _ in results if l == lab]
        if not rows:
            continue
        n = len(rows)
        cnt = Counter(c for c, _ in rows)
        print(f"\n[{lab}] {n}장 → " + ", ".join(f"{k} {v}" for k, v in cnt.most_common()))
        verdicts = sum(cnt[c] for c in VERDICT_CODES)
        retakes = sum(cnt[c] for c in RETAKE_CODES)
        print(f"    판정 가능: {verdicts}/{n}, 재촬영 요청: {retakes}/{n}, 오류: {cnt['error']}/{n}")
        if lab == "cataract":
            # 스크리닝 관점: risk 또는 borderline이면 '검진 안내를 받은 것'으로 성공
            hit = cnt["risk"] + cnt["borderline"]
            print(f"    검진 안내율(risk+borderline): {hit}/{n} = {hit/n*100:.0f}%"
                  f"  (판단 어려움 {cnt['uncertain']}장과 재촬영 {retakes}장은 진단 성공으로 세지 않음)")
            missed = [(f, p) for l, f, c, p, _ in results if l == lab and c == "normal"]
            for f, p in missed:
                print(f"    !! 알려진 백내장 사진에서 혼탁 특징 없음 ({p:.1f}점): {f}")
        elif lab == "normal":
            fp = cnt["risk"]
            print(f"    오탐율(risk 판정): {fp}/{n} = {fp/n*100:.0f}%"
                  f"  (borderline {cnt['borderline']}장은 허용 가능한 재검 안내)")
        elif lab == "non_eye":
            print(f"    거부·재촬영율: {retakes}/{n} = {retakes/n*100:.0f}%")
            print(f"    판정으로 통과한 비눈 사진: {verdicts}/{n} (별도 검토 필요)")

    print("\n※ 이 결과는 서버 판독 함수를 직접 사용합니다. 브라우저 사진 축소·전송 과정은 별도 검증이 필요합니다.")
    print("※ 실사진 결과는 내부 데이터셋 성능과 별도로 보고하세요. 이 표본으로 임상 성능을 주장할 수 없습니다.")


if __name__ == "__main__":
    main()
