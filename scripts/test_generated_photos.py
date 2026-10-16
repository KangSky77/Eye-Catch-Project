"""
Test AI-generated photos with Eye-Catch vision pipeline.
Evaluates gate decisions, cataract probability, and failure modes.
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.vision import predict_cataract, load_trained_weights
from app.services import eye_validator, eye_detector

def run_tests(image_dir: Path):
    load_trained_weights()
    eye_validator.warmup()
    if eye_detector.is_available():
        eye_detector.warmup()

    image_paths = sorted(list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpeg")))
    if not image_paths:
        print(f"No images found in {image_dir}")
        return

    print("=" * 80)
    print(f"Testing {len(image_paths)} images from: {image_dir}")
    print("=" * 80)

    results = []
    for p in image_paths:
        print(f"\n[Testing: {p.name}]")
        try:
            with Image.open(p) as raw_img:
                img = raw_img.convert("RGB")
                res = predict_cataract(img)
                
                checks_summary = {c['key']: c['ok'] for c in res.get('checks', [])}
                result_code = res.get('result_code')
                prob = res.get('probability', 0.0)
                msg = res.get('result', '')
                mode = res.get('mode', 'unknown')
                asym = res.get('asymmetric', False)
                eyes_det = res.get('eyes_detected', 0)
                
                print(f"  - Mode: {mode} (Eyes detected: {eyes_det})")
                print(f"  - Result Code: {result_code}")
                print(f"  - Probability: {prob:.1f}%")
                print(f"  - Message: {msg}")
                print(f"  - Asymmetric: {asym}")
                print(f"  - Checks:")
                for k, v in checks_summary.items():
                    status_str = "PASS" if v is True else ("FAIL" if v is False else "N/A")
                    print(f"      [{status_str}] {k}")

                eyes_info = res.get('eyes', [])
                eyes_str = " / ".join([f"{e['side']}:{e['probability']}%({e['code']})" for e in eyes_info])
                closeup = res.get('closeup_suggested', False)
                print(f"  - Eyes Detail: {eyes_str}")
                print(f"  - Closeup Suggested: {closeup}")

                results.append({
                    "file": p.name,
                    "mode": mode,
                    "result_code": result_code,
                    "prob": prob,
                    "eyes_str": eyes_str,
                    "asym": asym,
                    "closeup": closeup,
                    "message": msg,
                    "checks": checks_summary
                })
        except Exception as exc:
            print(f"  - ERROR: {exc}")
            results.append({"file": p.name, "error": str(exc)})

    print("\n" + "=" * 95)
    print("SUMMARY TABLE")
    print("=" * 95)
    print(f"{'Filename':<28} | {'Mode':<5} | {'Code':<11} | {'Total':<5} | {'Asym':<5} | {'Eyes (L/R)':<20} | {'Gate / Closeup'}")
    print("-" * 95)
    for r in results:
        if "error" in r:
            print(f"{r['file']:<28} | ERROR: {r['error']}")
        else:
            checks = r.get("checks", {})
            failed_checks = [k for k, v in checks.items() if v is False]
            gate_note = f"FAIL:{','.join(failed_checks)}" if failed_checks else ("CloseupRec" if r.get('closeup') else "All OK")
            asym_str = "YES" if r.get('asym') else "no"
            print(f"{r['file']:<28} | {r['mode']:<5} | {r['result_code']:<11} | {r['prob']:<4.1f}% | {asym_str:<5} | {r.get('eyes_str',''):<20} | {gate_note}")
    print("=" * 95)

if __name__ == "__main__":
    target = ROOT / "tests" / "generated_test_photos"
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    run_tests(target)
