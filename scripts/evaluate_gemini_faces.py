"""Evaluate a Gemini-generated portrait collage plus controlled eye-opacity variants.

The opacity variants are synthetic robustness fixtures, not clinical cataract images.
They must never be described as patient data or diagnostic validation.
"""
import io, json, hashlib, time, sys
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / '.codex' / 'face-audit-20260907'
COLLAGE = FIX / 'gemini_normal_collage.png'
OUT = FIX / 'gemini_results.jsonl'
sys.path.insert(0, str(ROOT))

def faces():
    singles = sorted(FIX.glob('gemini_clean_*.png'))
    if singles:
        return [Image.open(p).convert('RGB') for p in singles]
    with Image.open(COLLAGE) as src:
        im = src.convert('RGB')
    # The generated 4-up portrait is separated into four equal columns.
    w, h = im.size
    # Screenshot extraction preserves the visible generated image; enlarge each tile
    # before the app's minimum-sharpness gate so the test reflects a phone portrait
    # upload rather than the browser's 708px display width.
    return [im.crop((round(i*w/4), 0, round((i+1)*w/4), h)).resize((708, 1548), Image.Resampling.LANCZOS)
            for i in range(4)]

def eye_haze(im, level):
    from app.services.eye_detector import _get_mtcnn
    mtcnn = _get_mtcnn()
    boxes, probs, landmarks = mtcnn.detect(im, landmarks=True)
    out = im.copy()
    if landmarks is None or boxes is None:
        return out
    idx = max(range(len(probs)), key=lambda i: probs[i])
    layer = Image.new('RGBA', out.size, (0,0,0,0)); d = ImageDraw.Draw(layer)
    for x, y in sorted((landmarks[idx][0], landmarks[idx][1]), key=lambda p: p[0]):
        r = max(7, int(min(out.size) * (0.035 + level * 0.012)))
        # Concentric translucent gray-white discs approximate lens haze only for input stress.
        d.ellipse((x-r, y-r, x+r, y+r), fill=(235,235,235, int(65 + 55*level)))
        d.ellipse((x-r*.45, y-r*.45, x+r*.45, y+r*.45), fill=(248,248,248, int(90 + 45*level)))
    return Image.alpha_composite(out.convert('RGBA'), layer).convert('RGB')

def variants(im):
    yield 'normal', im
    for level in (1, 2, 3, 4):
        yield f'haze_{level}', eye_haze(im, level)
    yield 'dark', ImageEnhance.Brightness(im).enhance(.55)
    yield 'bright', ImageEnhance.Brightness(im).enhance(1.45)
    yield 'blur', im.filter(ImageFilter.GaussianBlur(2.0))
    yield 'mirror', ImageOps.mirror(im)
    yield 'rotate_12', im.rotate(12, resample=Image.Resampling.BICUBIC, expand=False)

def main():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.vision import load_trained_weights
    assert load_trained_weights()
    rows=[]; client=TestClient(app)
    for i, face in enumerate(faces()):
        face.save(FIX/f'gemini_face_{i}.png')
        for variant, im in variants(face):
            payload=io.BytesIO(); im.save(payload,format='PNG')
            start=time.perf_counter(); r=client.post('/api/analyze-eye',files={'file':('gemini.png',payload.getvalue(),'image/png')})
            body=r.json(); row={'face':i,'variant':variant,'http_status':r.status_code,'seconds':round(time.perf_counter()-start,4),**body}
            rows.append(row)
    OUT.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n',encoding='utf-8')
    grouped=defaultdict(Counter)
    for r in rows: grouped[r['variant']][r.get('result_code','http_error')]+=1
    summary={'source':'Gemini-generated synthetic portraits','faces':len(faces()),'observations':len(rows), 'counts_by_variant':{k:dict(v) for k,v in grouped.items()}, 'warning':'Haze variants are controlled overlays, not clinical cataract labels.'}
    (FIX/'gemini_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
