"""
실사진(폰 촬영) 검증 도구
================================================================
데이터셋 test 성능(민감도 98.2%)은 '데이터셋 안에서의' 수치다. 실제 폰으로 찍은
사진은 조명·화질·구도가 달라 성능이 떨어질 수 있으므로(도메인 갭), 시연 전에
팀원들의 실사진으로 배포 파이프라인을 그대로 통과시켜 미리 확인한다.

이 스크립트는 서버(vision.py)와 완전히 동일한 경로를 쓴다:
MTCNN 눈 크롭 → 눈 검증(OOD) 게이트 → EfficientNet+TTA → 3단계 판정(risk/borderline/normal)

사용법:
    python validate_real_photos.py <사진 폴더>

폴더 구조 (라벨별 하위 폴더가 있으면 정답률까지 계산):
    real_photos/
      cataract/   백내장으로 알려진 눈 사진
      normal/     정상 눈 사진
      non_eye/    눈이 아닌 사진 (거부되는지 확인용, 선택)
    하위 폴더가 없으면 라벨 없이 예측 결과만 출력한다.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")   # Windows cp949 콘솔에서도 안전하게

import argparse
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

from app.services import vision, eye_validator

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
LABEL_DIRS = ("cataract", "normal", "non_eye")


def load_image(path: Path) -> Image.Image:
    """서버의 validate_and_read_image와 동일한 전처리(EXIF 회전 + RGB)."""
    with Image.open(path) as img:
        return ImageOps.exif_transpose(img.convert("RGB"))


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


def main():
    parser = argparse.ArgumentParser(description="실사진으로 배포 파이프라인 검증")
    parser.add_argument("folder", help="사진 폴더 (하위에 cataract/normal/non_eye 폴더 권장)")
    args = parser.parse_args()
    folder = Path(args.folder)
    if not folder.is_dir():
        raise SystemExit(f"폴더가 없습니다: {folder}")

    if not vision.load_trained_weights():
        raise SystemExit("가중치 로드 실패 — .env의 MODEL_PATH/MODEL_BACKBONE 확인")
    if not eye_validator.warmup():
        raise SystemExit("눈 검증기 로드 실패 — 인터넷 연결(최초 1회 가중치 다운로드) 확인")

    results = []   # (label, path, result_code, probability, mode)
    for label, f in iter_images(folder):
        try:
            r = vision.predict_cataract(load_image(f))
            code, prob, mode = r["result_code"], r["probability"], r["mode"]
        except Exception as e:
            code, prob, mode = "error", 0.0, "-"
        results.append((label, f, code, prob, mode))
        mark = {"risk": "[위험]", "borderline": "[경계]", "normal": "[정상]",
                "invalid": "[거부]", "error": "[오류]"}[code]
        print(f"{mark} {prob:5.1f}%  mode={mode:4s}  {f}")

    if not results:
        raise SystemExit("이미지가 없습니다.")

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
        if lab == "cataract":
            # 스크리닝 관점: risk 또는 borderline이면 '검진 안내를 받은 것'으로 성공
            hit = cnt["risk"] + cnt["borderline"]
            print(f"    검진 안내율(risk+borderline): {hit}/{n} = {hit/n*100:.0f}%"
                  f"  (invalid {cnt['invalid']}장은 재촬영 대상)")
            missed = [(f, p) for l, f, c, p, _ in results if l == lab and c == "normal"]
            for f, p in missed:
                print(f"    !! 정상으로 놓침 ({p:.1f}%): {f}")
        elif lab == "normal":
            fp = cnt["risk"]
            print(f"    오탐율(risk 판정): {fp}/{n} = {fp/n*100:.0f}%"
                  f"  (borderline {cnt['borderline']}장은 허용 가능한 재검 안내)")
        elif lab == "non_eye":
            print(f"    거부율(invalid): {cnt['invalid']}/{n} = {cnt['invalid']/n*100:.0f}%"
                  f"  — 거부 안 된 사진은 OOD 게이트를 통과한 것 (eye_score 임계값 재검토 필요)")

    print("\n※ 이 결과는 서버와 100% 동일한 파이프라인(MTCNN→OOD게이트→TTA→3단계 판정)입니다.")
    print("※ 실사진 성능이 데이터셋 test보다 낮게 나오는 것이 정상입니다(도메인 갭). 발표 때 함께 언급하세요.")


if __name__ == "__main__":
    main()
