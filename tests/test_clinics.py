"""주변 안과 검색 — 거리 계산과 폴백 체인(카카오→Overpass→none). 네트워크는 모킹."""
import pytest

from app.core.config import settings
from app.services import clinics


def test_haversine_동일지점은_0():
    assert clinics._haversine(37.5665, 126.9780, 37.5665, 126.9780) == 0


def test_haversine_서울_부산_거리():
    # 서울시청 ~ 부산시청 직선거리 약 325km (±15km 허용)
    d = clinics._haversine(37.5665, 126.9780, 35.1796, 129.0756)
    assert 310_000 < d < 340_000


@pytest.mark.anyio
async def test_키없고_OSM도_비면_no_key(monkeypatch):
    monkeypatch.setattr(settings, "kakao_rest_key", "")
    async def empty(*a, **kw):
        return []
    monkeypatch.setattr(clinics, "_search_overpass", empty)
    out = await clinics.search_eye_clinics(37.5, 127.0)
    assert out == {"source": "none", "clinics": [], "reason": "no_key"}


@pytest.mark.anyio
async def test_키없어도_OSM결과로_폴백(monkeypatch):
    monkeypatch.setattr(settings, "kakao_rest_key", "")
    osm_result = [{"name": "OO안과", "lat": 37.5, "lng": 127.0, "dist": 120.0,
                   "phone": "", "address": "", "url": ""}]
    async def fake(*a, **kw):
        return osm_result
    monkeypatch.setattr(clinics, "_search_overpass", fake)
    out = await clinics.search_eye_clinics(37.5, 127.0)
    assert out["source"] == "overpass"
    assert out["clinics"] == osm_result
