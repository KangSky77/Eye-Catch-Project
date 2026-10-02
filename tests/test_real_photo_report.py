import sys
from PIL import Image
from scripts import validate_real_photos as report


def test_export_keeps_uncertain_retakes_and_errors_distinct(tmp_path):
    import json
    import csv
    results = [('cataract', tmp_path/'a.jpg', 'uncertain', 3, 'eye'),
               ('non_eye', tmp_path/'b.jpg', 'invalid', 0, 'none'),
               (None, tmp_path/'c.jpg', 'error', 0, '-')]
    summary = report.write_report(results, tmp_path/'export')
    assert summary['labels']['cataract']['codes'] == {'uncertain': 1}
    assert summary['labels']['non_eye']['categories'] == {'retake': 1}
    assert json.loads((tmp_path/'export/photo-summary.json').read_text())['total'] == 3
    with (tmp_path/'export/photo-results.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert rows[2]['score'] == ''
    assert not list((tmp_path/'export').glob('*.jpg'))


def test_photo_report_separates_uncertain_retakes_and_non_eye_verdicts(tmp_path,monkeypatch,capsys):
    # A retake is not an eye diagnosis; uncertain is neither a positive diagnosis nor normal.
    for label in ('cataract','non_eye'):
        folder=tmp_path/label
        folder.mkdir()
        for i in range(2):
            Image.new('RGB',(100,100)).save(folder/f'{i}.png')
    monkeypatch.setattr(sys,'argv',['validate_real_photos.py',str(tmp_path)])
    monkeypatch.setattr(report.vision,'load_trained_weights',lambda:True)
    monkeypatch.setattr(report.eye_validator,'warmup',lambda:True)
    monkeypatch.setattr(report.eye_detector,'warmup',lambda:True)
    codes=iter(['uncertain','risk','eyes_hidden','normal'])
    monkeypatch.setattr(report.vision,'predict_cataract',lambda image:{'result_code':next(codes),'probability':3,'mode':'eye'})
    report.main()
    output=capsys.readouterr().out
    assert '검진 안내율(risk+borderline): 1/2' in output
    assert '판단 어려움 1장' in output
    assert '거부·재촬영율: 1/2' in output
    assert '판정으로 통과한 비눈 사진: 1/2' in output
    assert '3단계' not in output
    assert '100% 동일' not in output
