"""감은 눈 수집 사진 → 얼굴별 눈 크롭 + 검수용 번호 시트

왜 사람이 검수하는가:
    '수면'·'명상' 범주에도 눈을 뜬 사진, 선글라스, 얼굴이 아닌 조각이 섞인다.
    뜬 눈이 음성으로 들어가면 앱이 반드시 받아들여야 할 사진을 거부하도록 가르친다
    (build_eye_gate.py 상단의 cataract-clinical.jpg 사고와 같은 실수).
    그래서 크롭마다 번호를 붙인 시트를 만들고, 사람이 보고 dataset_closedeye/review.json에
    '감은 눈이 아닌 것'의 번호를 적는다. 기본값은 제외(=검수 전에는 학습에 쓰지 않는다).

크롭 기하는 app/services/eye_detector.py와 똑같이 맞춘다(눈 사이 거리 × 0.45 반경).
앱이 실제로 게이트에 넣는 모양과 같아야 학습이 의미가 있다.

실행:  python scripts/review_closed_eye_crops.py          # 크롭 + 시트 생성
출력:  dataset_closedeye/crops/*.png, crops_index.json, _review/sheet_XX.png
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services import eye_detector, eye_validator

# 기본은 감은 눈 폴더. 뜬 눈 인물 사진(dataset_openeye)도 같은 기하로 크롭해야 두 판정기 입력이
# 일치하므로 --dir로 같은 스크립트를 쓴다.
DIR = ROOT / "dataset_closedeye"
CROPS = DIR / "crops"; SHEETS = DIR / "_review"
# 기준은 '앱이 실제로 게이트에 넣는 입력의 범위'에 맞춘다. eye_detector는 크롭 한 변이
# MIN_CROP_PX(32px) 이상이면 받는다 → 크롭 한 변 = 눈 사이 거리 × 0.9 이므로 눈 사이 36px.
# 처음엔 64px로 잡았다가 수면 사진 179장에서 크롭이 21개뿐이었다(눈 사이 거리 중앙값 18px —
# 대부분 멀리서 찍은 전신 사진). 앱이 받는 작은 크롭도 게이트가 막아야 하므로 학습에도 넣는다.
MIN_EYE_DIST = 36
MIN_CROP_SIDE = 32
# 수집용 얼굴 확신도. 앱은 0.95로 '한 사람'을 가려내지만, 여기서는 눈꺼풀의 모양을 모으는
# 것이라 0.90이면 충분하다(0.95→0.90에서 얼굴 86→107개). 잘못 잡힌 크롭은 검수에서 뺀다.
FACE_PROB = 0.90


def main():
    global DIR, CROPS, SHEETS
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="dataset_closedeye")
    args = ap.parse_args()
    DIR = ROOT / args.dir; CROPS = DIR / "crops"; SHEETS = DIR / "_review"
    CROPS.mkdir(parents=True, exist_ok=True); SHEETS.mkdir(parents=True, exist_ok=True)
    mtcnn = eye_detector._get_mtcnn()
    if mtcnn is None:
        raise SystemExit("MTCNN 사용 불가")
    eye_validator.warmup()
    photos = sorted(p for p in DIR.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    index = []
    for p in photos:
        try:
            with Image.open(p) as s:
                im = ImageOps.exif_transpose(s).convert("RGB")
        except Exception:
            continue
        boxes, probs, lms = mtcnn.detect(im, landmarks=True)
        if boxes is None or lms is None:
            continue
        W, H = im.size
        for k, (prob, lm) in enumerate(zip(probs, lms)):
            if prob is None or prob < FACE_PROB:
                continue
            left, right = sorted((lm[0], lm[1]), key=lambda q: float(q[0]))
            dist = float(np.linalg.norm(np.array(right) - np.array(left)))
            if dist < MIN_EYE_DIST:
                continue
            half = dist * eye_detector.EYE_CROP_RATIO
            for side, (cx, cy) in (("L", left), ("R", right)):
                box = (int(max(cx - half, 0)), int(max(cy - half, 0)),
                       int(min(cx + half, W)), int(min(cy + half, H)))
                if box[2] - box[0] < MIN_CROP_SIDE or box[3] - box[1] < MIN_CROP_SIDE:
                    continue
                crop = im.crop(box)
                name = f"{p.stem}__f{k}_{side}.png"
                crop.save(CROPS / name)
                score = eye_validator._gate_prob(crop) if eye_validator.gate_available() else None
                index.append({"id": len(index), "crop": name, "photo": p.name,
                              "gate_before": None if score is None else round(score, 4)})
    (DIR / "crops_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

    # 이미 판정한 크롭(review.json의 closed·excluded)은 시트에서 뺀다 — 수집을 늘릴 때 새 크롭만 보면 된다.
    # 판정은 크롭 '파일명'으로 기록하므로(사진 이름 + 얼굴 순번 + 좌우) 번호가 바뀌어도 유지된다.
    review_path = DIR / "review.json"
    done = set()
    if review_path.exists():
        r = json.loads(review_path.read_text(encoding="utf-8"))
        # 폴더마다 채택 키가 다르다(감은 눈 "closed", 뜬 눈 "open"). 한쪽만 세면 채택한 크롭이
        # 다시 미검수로 올라온다 — 뜬 눈 폴더에서 채택 153개가 그렇게 시트에 되돌아왔다.
        done = set(r.get("closed", [])) | set(r.get("open", [])) | set(r.get("excluded", []))
    pending = [it for it in index if it["crop"] not in done]
    for old_sheet in SHEETS.glob("sheet_*.png"):
        old_sheet.unlink()
    T, COLS, PER = 150, 8, 48
    for s in range(0, len(pending), PER):
        chunk = pending[s:s + PER]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * T, rows * (T + 16)), "white")
        d = ImageDraw.Draw(sheet)
        for j, it in enumerate(chunk):
            x, y = (j % COLS) * T, (j // COLS) * (T + 16)
            sheet.paste(Image.open(CROPS / it["crop"]).resize((T, T)), (x, y))
            d.rectangle((x, y, x + 34, y + 14), fill="black")
            d.text((x + 2, y + 1), str(it["id"]), fill="yellow")
            d.text((x + 3, y + T + 2), f"{it['gate_before']}", fill="red" if (it["gate_before"] or 0) >= 0.6 else "green")
        sheet.save(SHEETS / f"sheet_{s // PER:02d}.png")
    print(f"사진 {len(photos)}장 → 눈 크롭 {len(index)}개 (미검수 {len(pending)}개, 시트 {(len(pending) + PER - 1) // PER}장)")
    passed = sum(1 for it in index if (it["gate_before"] or 0) >= 0.6)
    print(f"현재 게이트(0.60)에서 '눈'으로 통과하는 크롭: {passed}/{len(index)}  ← 검수 전 수치(뜬 눈 섞임)")


if __name__ == "__main__":
    main()
