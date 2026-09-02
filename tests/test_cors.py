"""CORS 화이트리스트 — 필요한 origin만 열리는지.

예전에는 `allow_origins=["*"]`로 모든 출처에 열려 있었다. 프론트가 같은 서버(/static)
에서 서빙되므로 평소에는 same-origin이라 CORS 헤더 자체가 필요 없고(ngrok 공유도
페이지와 API가 같은 도메인이라 동일), 별도 도메인에서 이 API를 부를 때만
.env의 ALLOWED_ORIGINS로 연다.
"""
import pytest

from app.core.config import Settings, settings


def test_기본값은_빈목록():
    assert Settings(allowed_origins="").allowed_origins_list == []


def test_쉼표구분_파싱():
    s = Settings(allowed_origins="http://localhost:8000,https://a.example.com")
    assert s.allowed_origins_list == ["http://localhost:8000", "https://a.example.com"]


def test_공백과_빈항목_제거():
    # .env를 손으로 고치다 흔히 생기는 형태 — 항목 사이 공백, 끝에 남은 쉼표
    s = Settings(allowed_origins=" http://a.com , , https://b.com ,")
    assert s.allowed_origins_list == ["http://a.com", "https://b.com"]


@pytest.mark.skipif(
    bool(settings.allowed_origins_list),
    reason=".env에서 ALLOWED_ORIGINS를 설정한 환경에서는 열려 있는 것이 정상",
)
def test_설정이_없으면_교차출처에_허용헤더를_주지_않는다(client):
    # 미들웨어를 아예 달지 않으므로 Access-Control-Allow-Origin이 응답에 없어야 한다.
    r = client.get("/", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}
