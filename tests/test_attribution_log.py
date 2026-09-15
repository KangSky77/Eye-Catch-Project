"""수집 스크립트의 출처 기록 — 도중에 멈춰도 이미 받은 사진의 출처가 남아야 한다.

2026-09-13 웃는 얼굴 수집이 도중에 끝나 사진 373장만 남고 ATTRIBUTION.csv는 한 줄도 없었다.
스크립트가 모든 다운로드가 끝난 뒤에 CSV를 한 번에 썼기 때문이다. 그 사진으로 뜸 여부 판정기를
학습했으므로 CC BY·CC BY-SA 저작자 표시의 근거가 통째로 사라진 셈이었다."""
import csv
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fetch_non_eye_photos as base  # noqa: E402


def _row(name):
    return {"filename": name, "category": "c", "title": "File:" + name, "author": "a",
            "license": "CC0", "source_page": "p", "file_url": "u"}


def _names(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [r["filename"] for r in csv.DictReader(f)]


def test_출처는_사진마다_즉시_디스크에_남는다(tmp_path):
    path = tmp_path / "ATTRIBUTION.csv"
    log = base.AttributionLog(path)
    log.add(_row("a.jpg"))
    # close()를 부르기 전(=스크립트가 도중에 죽은 상태)에도 이미 파일에 있어야 한다
    assert _names(path) == ["a.jpg"]
    log.close()


def test_재실행은_중복없이_빠진_출처만_채운다(tmp_path):
    path = tmp_path / "ATTRIBUTION.csv"
    with base.AttributionLog(path) as log:
        log.add(_row("a.jpg"))
        log.add(_row("b.jpg"))
    with base.AttributionLog(path) as log:
        assert log.add(_row("a.jpg")) is False
        assert log.add(_row("c.jpg")) is True
    lines = path.read_text(encoding="utf-8").splitlines()
    assert sum(line.startswith("filename,") for line in lines) == 1, "헤더가 두 번 쓰였다"
    assert _names(path) == ["a.jpg", "b.jpg", "c.jpg"]


def test_수집_스크립트는_끝에서_한번에_쓰지_않는다():
    for name in ["fetch_non_eye_photos.py", "fetch_closed_eye_photos.py",
                 "fetch_open_eye_portraits.py", "fetch_smile_eye_photos.py"]:
        src = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "AttributionLog" in src, name
        assert "writerows(" not in src, f"{name}이 아직 끝에서 CSV를 한 번에 쓴다"
