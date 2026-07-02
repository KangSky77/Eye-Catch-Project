"""
주변 안과 검색 (카카오 로컬 REST API)
=====================================
- 카카오 '키워드 장소 검색' REST API를 서버에서 호출 → 좌표·이름·거리 반환
- REST API 키는 서버(Authorization 헤더)에서만 사용 → 사이트 도메인 등록 불필요
  (도메인 등록이 필요한 것은 카카오 '지도 JavaScript SDK'/로그인용)
- 지도 표시는 프론트의 Leaflet(OSM)이 담당하고, 여기서는 데이터만 제공
- 키가 없으면 빈 목록 + reason 반환 → 프론트가 외부 검색 링크로 폴백
"""
import httpx
from math import radians, sin, cos, asin, sqrt
from app.core.config import settings

KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Overpass는 User-Agent가 없으면 406을 반환 → 반드시 지정
_UA = {"User-Agent": "Eye-Catch/1.0 (eye clinic finder)"}


def _haversine(a_lat, a_lng, b_lat, b_lng):
    d_lat = radians(b_lat - a_lat); d_lng = radians(b_lng - a_lng)
    h = sin(d_lat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(d_lng / 2) ** 2
    return 2 * 6371000 * asin(sqrt(h))   # meters


async def _search_overpass(lat: float, lng: float, radius: int = 4000, size: int = 15) -> list:
    """해외 폴백: OSM Overpass로 안과/안경원/안과전문 검색 (전 세계)."""
    q = (
        f"[out:json][timeout:20];("
        f'nwr["healthcare:speciality"~"ophthalmology",i](around:{radius},{lat},{lng});'
        f'nwr["healthcare"="optometrist"](around:{radius},{lat},{lng});'
        f'nwr["shop"="optician"](around:{radius},{lat},{lng});'
        f'nwr["name"~"안과|ophthalm|eye clinic|optometr|augenarzt|oculist",i](around:{radius},{lat},{lng});'
        f");out center {size * 3};"
    )
    try:
        async with httpx.AsyncClient(timeout=20.0, headers=_UA) as client:
            r = await client.post(OVERPASS_URL, data={"data": q})
            r.raise_for_status()
            elements = r.json().get("elements", [])
    except Exception:
        return []

    seen, out = set(), []
    for el in elements:
        elat = el.get("lat") if el.get("lat") is not None else (el.get("center") or {}).get("lat")
        elng = el.get("lon") if el.get("lon") is not None else (el.get("center") or {}).get("lon")
        tags = el.get("tags") or {}
        name = tags.get("name")
        if elat is None or elng is None or not name:
            continue
        key = (name, round(elat, 4), round(elng, 4))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "name": name, "lat": float(elat), "lng": float(elng),
            "dist": _haversine(lat, lng, elat, elng),
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "address": tags.get("addr:full") or tags.get("addr:street") or "",
            "url": tags.get("website") or "",
        })
    out.sort(key=lambda c: c["dist"])
    return out[:size]


async def search_eye_clinics(lat: float, lng: float, radius: int = 5000, size: int = 15) -> dict:
    """현재 위치(lat,lng) 주변 안과를 거리순으로 검색.

    한국 → 카카오(빠르고 완전), 결과 없거나 키 없으면 → Overpass(OSM, 해외 커버리지 좋음).
    반환: {"source": "kakao"|"overpass"|"none", "clinics": [...], "reason"?}
    """
    if not settings.kakao_rest_key:
        # 키 없음 → 바로 Overpass(해외/한국 모두 시도)
        osm = await _search_overpass(lat, lng, radius=radius, size=size)
        if osm:
            return {"source": "overpass", "clinics": osm}
        return {"source": "none", "clinics": [], "reason": "no_key"}

    headers = {"Authorization": f"KakaoAK {settings.kakao_rest_key}"}
    params = {
        "query": "안과",
        "x": lng,            # 카카오는 x=경도, y=위도
        "y": lat,
        "radius": min(max(radius, 0), 20000),   # 최대 20km
        "sort": "distance",
        "size": min(max(size, 1), 15),           # 페이지당 최대 15
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(KAKAO_KEYWORD_URL, headers=headers, params=params)
            r.raise_for_status()
            docs = r.json().get("documents", [])
    except Exception:
        docs = []   # 카카오 실패 → 아래에서 Overpass로 폴백

    clinics = []
    for d in docs:
        try:
            clinics.append({
                "name": d.get("place_name", "안과"),
                "lat": float(d["y"]),
                "lng": float(d["x"]),
                "dist": float(d.get("distance") or 0),
                "phone": d.get("phone") or "",
                "address": d.get("road_address_name") or d.get("address_name") or "",
                "url": d.get("place_url") or "",
            })
        except (KeyError, ValueError, TypeError):
            continue
    if clinics:
        return {"source": "kakao", "clinics": clinics}

    # 카카오 결과 없음(해외 등) → Overpass(OSM) 폴백
    osm = await _search_overpass(lat, lng, radius=radius, size=size)
    if osm:
        return {"source": "overpass", "clinics": osm}
    return {"source": "none", "clinics": [], "reason": "no_results"}
