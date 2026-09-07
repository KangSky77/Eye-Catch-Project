"""Reproducible external portrait input audit, NOT a clinical accuracy study.

Images and person-level outputs stay in an ignored local directory. Wikimedia
copyright metadata is recorded per image; it does not waive personality rights.
Do not publish subject-level model scores or use these photos for training.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / '.codex' / 'face-audit-20260907'
CATEGORIES = ['Portrait photographs', 'Portrait photographs of women',
              'Portrait photographs of men', 'People wearing glasses',
              'Front view portrait photographs', 'Human faces']
UA = 'EyeCatch-input-audit/1.0 (local research; Wikimedia Commons API)'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def api(params):
    return json.loads(get('https://commons.wikimedia.org/w/api.php?' +
                         urllib.parse.urlencode(dict(params, format='json'))))


def collect(limit):
    OUT.mkdir(parents=True, exist_ok=True)
    rows, seen, hashes, failures = [], set(), set(), []
    for category in CATEGORIES:
        cont = {}
        count = 0
        for _ in range(6):
            data = api(dict(action='query', generator='categorymembers',
                            gcmtitle='Category:' + category, gcmtype='file', gcmlimit=50,
                            prop='imageinfo', iiprop='url|extmetadata|size|mime',
                            iiurlwidth=960, **cont))
            for page in data.get('query', {}).get('pages', {}).values():
                if page['pageid'] in seen:
                    continue
                info = page.get('imageinfo', [{}])[0]
                meta = info.get('extmetadata', {})
                val = lambda k: meta.get(k, {}).get('value', '')
                license_name = val('LicenseShortName')
                if not re.fullmatch(r'(?:CC BY(?:-SA)? [1-4]\.0|CC0(?: 1\.0)?|Public domain)', license_name):
                    continue
                if info.get('mime') not in ('image/jpeg', 'image/png'):
                    continue
                try:
                    raw = get(info.get('thumburl') or info['url'])
                    digest = hashlib.sha256(raw).hexdigest()
                    if digest in hashes:
                        continue
                    with Image.open(io.BytesIO(raw)) as src:
                        im = ImageOps.exif_transpose(src).convert('RGB')
                    if min(im.size) < 200:
                        continue
                    im.thumbnail((960, 960))
                    name = f"commons_{page['pageid']}.jpg"
                    im.save(OUT / name, quality=95)
                    row = dict(id=page['pageid'], filename=name, category=category,
                               title=page['title'], author=re.sub('<[^>]+>', '', val('Artist')),
                               license=license_name, license_url=val('LicenseUrl'),
                               source_page=info.get('descriptionurl', ''),
                               download_url=info.get('thumburl') or info['url'],
                               source_sha256=digest,
                               local_sha256=hashlib.sha256((OUT/name).read_bytes()).hexdigest(),
                               change='EXIF oriented, RGB, resized max 960px, JPEG quality 95',
                               collected='2026-09-07', metadata=meta)
                    rows.append(row); seen.add(page['pageid']); hashes.add(digest); count += 1
                    (OUT/'manifest.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
                    if count % 10 == 0:
                        print(category, count, 'total', len(rows), flush=True)
                except Exception as exc:
                    failures.append(dict(title=page['title'], error=str(exc)))
                if count >= limit:
                    break
                time.sleep(.15)
            if count >= limit or 'continue' not in data:
                break
            cont = data['continue']
        print('category complete', category, count, flush=True)
    (OUT/'download_failures.json').write_text(json.dumps(failures, indent=2), encoding='utf-8')
    sheets(rows)
    print('downloaded', len(rows), flush=True)


def sheets(rows):
    for start in range(0, len(rows), 30):
        sheet = Image.new('RGB', (1200, 1100), 'white')
        draw = ImageDraw.Draw(sheet)
        for j, row in enumerate(rows[start:start+30]):
            with Image.open(OUT/row['filename']) as src:
                im = src.copy(); im.thumbnail((195, 185))
            x, y = j%6*200, j//6*220
            sheet.paste(im, (x,y))
            draw.text((x,y+188), f"{start+j}: {row['id']}", fill='black')
        sheet.save(OUT/f'contact_{start//30}.jpg')


def variants(im):
    yield 'original', im
    yield 'mirror', ImageOps.mirror(im)
    yield 'rotate_15', im.rotate(15, resample=Image.Resampling.BICUBIC)
    yield 'dark_055', ImageEnhance.Brightness(im).enhance(.55)
    yield 'bright_150', ImageEnhance.Brightness(im).enhance(1.5)
    yield 'small_320', ImageOps.contain(im, (320,320))
    yield 'small_160', ImageOps.contain(im, (160,160))
    yield 'blur_1pct', im.filter(ImageFilter.GaussianBlur(min(im.size)*.01))
    b = io.BytesIO(); im.save(b, format='JPEG', quality=25)
    yield 'jpeg_25', Image.open(io.BytesIO(b.getvalue())).convert('RGB')
    pair = Image.new('RGB', (im.width*2, im.height)); pair.paste(im); pair.paste(im,(im.width,0))
    pair.thumbnail((1200,1200))
    yield 'two_faces', pair


def evaluate():
    import numpy as np
    import logging
    from fastapi.testclient import TestClient
    from app.main import app
    logging.getLogger().setLevel(logging.WARNING)
    from app.services import vision, eye_detector, eye_validator
    from app.core.config import settings
    assert vision.load_trained_weights(), 'Model weights unavailable'
    assert eye_validator.warmup() and eye_detector.warmup(), 'Validator/detector unavailable'
    manifest = json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    review = json.loads((OUT/'review.json').read_text(encoding='utf-8'))
    accepted = {r['index'] for r in review if r['include']}
    result_path = OUT/'results.jsonl'
    rows = [json.loads(line) for line in result_path.read_text(encoding='utf-8').splitlines()] if result_path.exists() else []
    done = {(r['index'], r['variant']) for r in rows}
    client = TestClient(app)  # ASGI upload/decoder/route, real models; no DB or LLM startup.
    with result_path.open('a', encoding='utf-8') as log:
        for index, source in enumerate(manifest):
            if index not in accepted:
                continue
            with Image.open(OUT/source['filename']) as src:
                original=src.convert('RGB')
            for variant, im in variants(original):
                if (index, variant) in done:
                    continue
                start=time.perf_counter()
                try:
                    payload = io.BytesIO(); im.save(payload, format='PNG')
                    response = client.post('/api/analyze-eye', files={'file': ('audit.png', payload.getvalue(), 'image/png')})
                    result = response.json()
                    if response.status_code != 200:
                        result = dict(result_code='http_error', detail=result)
                    row=dict(index=index, variant=variant, width=im.width, height=im.height,
                             http_status=response.status_code, seconds=round(time.perf_counter()-start,4), **result)
                except Exception as exc:
                    row=dict(index=index,variant=variant,result_code='exception',error=str(exc))
                log.write(json.dumps(row,ensure_ascii=False)+'\n'); log.flush(); rows.append(row)
            print('evaluated',index,len(rows),flush=True)
    summary={}
    codes={'normal','uncertain','borderline','risk'}
    for v in sorted({r['variant'] for r in rows}):
        selected=[r for r in rows if r['variant']==v]
        summary[v]=dict(n=len(selected),counts=dict(Counter(r['result_code'] for r in selected)),
                        face_two=sum(r.get('mode')=='face' and r.get('eyes_detected')==2 for r in selected),
                        returned_result=sum(r['result_code'] in codes for r in selected),
                        median_seconds=float(np.median([r.get('seconds',0) for r in selected])))
    provenance=dict(model_sha256=hashlib.sha256(settings.model_file.read_bytes()).hexdigest(),
                    gate_sha256=hashlib.sha256(eye_validator._GATE_PATH.read_bytes()).hexdigest(),
                    eye_gate_threshold=settings.eye_gate_threshold, use_tta=settings.use_tta,
                    source_photos=len(accepted), observations=len(rows), summary=summary,
                    warning='Convenience portrait sample, not independent users; variants correlated; no disease ground truth')
    (OUT/'summary.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(provenance,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['collect','evaluate'])
    parser.add_argument('--per-category',type=int,default=25)
    args=parser.parse_args()
    if args.action=='collect': collect(args.per_category)
    else: evaluate()
