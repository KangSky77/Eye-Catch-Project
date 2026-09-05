"""Reproducible gate threshold audit; internal samples, not external validation.

Run: python scripts/evaluate_eye_gate.py --sample 300
No model files are modified. Both classes are sampled separately with seed 20260905.
"""
import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageOps
from app.services import eye_validator, eye_detector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=300)
    args = parser.parse_args()
    if args.sample < 1:
        parser.error('--sample must be positive')
    if not eye_validator.warmup() or not eye_validator.gate_available():
        raise SystemExit('Eye gate unavailable')
    rng = random.Random(20260905)
    scores = {}
    for category in ('0_normal', '1_cataract'):
        paths = sorted(p for p in (ROOT / 'dataset' / category).rglob('*')
                       if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp'})
        if not paths:
            raise SystemExit(f'Missing dataset: {category}')
        paths = rng.sample(paths, min(args.sample, len(paths)))
        values = []
        for path in paths:
            with Image.open(path) as source:
                img = ImageOps.exif_transpose(source).convert('RGB')
                values.append(eye_validator._gate_prob(img))
        scores[category] = values
    negatives = {}
    for name in ('vision-scene.jpg', 'diseases/diabetic-retinopathy-fundus.jpg',
                 'diseases/amd-fundus.jpg'):
        with Image.open(ROOT / 'static' / 'assets' / name) as img:
            negatives[name] = eye_validator._gate_prob(img)
    with Image.open(ROOT / 'static/assets/examples/face-good.jpg') as img:
        face = [eye_validator._gate_prob(c) for c in eye_detector.extract_eye_crops(img)]
    print(json.dumps({
        'seed': 20260905, 'note': 'Internal sample; may contain gate training images.',
        'thresholds': {str(t): {k: {'n': len(v), 'rejected': sum(s < t for s in v)}
                               for k, v in scores.items()} for t in (0.20682776, 0.4, 0.5, 0.6)},
        'negative_scores': negatives, 'face_eye_scores': face,
    }, indent=2))


if __name__ == '__main__':
    main()
