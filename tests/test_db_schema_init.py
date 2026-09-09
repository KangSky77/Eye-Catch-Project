"""diagnoses 스키마 자동 대응 — 문자열 검사가 아니라 실제 분기 동작을 본다.

왜 별도 파일인가:
    test_static_assets.py의 검사는 database.py 안에 "RENAME TO"라는 글자가 있는지만 봤다.
    자동 rename이 도입되자 그 글자는 SQL 쪽에도 생겨서, 정작 '새 DB에서는 rename을
    시도하면 안 된다'는 조건이 깨졌는데도 통과했다. 실제로 새 DB 기동이 죽었다.
    → 여기서는 가짜 커넥션으로 분기를 직접 태운다.
"""
import pytest

from app.services import database


class FakeConn:
    """asyncpg 커넥션 흉내. 실행된 SQL을 남겨 어떤 분기를 탔는지 확인한다."""

    def __init__(self, existing_tables=()):
        self.existing = set(existing_tables)
        self.executed: list[str] = []

    async def fetchval(self, query, *args):
        # _rename_incompatible_schema의 '이 이름의 테이블이 이미 있나' 조회
        return args[0] in self.existing

    async def execute(self, query, *args):
        self.executed.append(query)
        if "RENAME TO" in query and "diagnoses" not in self.existing:
            raise RuntimeError('relation "diagnoses" does not exist')
        return "OK"


@pytest.mark.anyio
async def test_테이블이_없으면_rename을_시도하지_않는다():
    """새 DB에는 diagnoses가 아예 없다 — 컬럼 0개다.

    '필수 컬럼이 없다'만 보고 rename을 걸면 존재하지 않는 테이블에 ALTER를 날려
    기동이 실패하고, 첫 배포에서 저장 기능이 통째로 비활성화된다."""
    conn = FakeConn()
    assert await database._rename_incompatible_schema(conn, set()) is None
    assert conn.executed == [], "새 DB인데 SQL을 실행했다"


@pytest.mark.anyio
async def test_스키마가_맞으면_건드리지_않는다():
    conn = FakeConn(existing_tables={"diagnoses"})
    actual = set(database.REQUIRED_COLUMNS) | {"created_at"}
    assert await database._rename_incompatible_schema(conn, actual) is None
    assert conn.executed == []


@pytest.mark.anyio
async def test_구스키마는_이름만_바꿔_데이터를_보존한다():
    """예전 설계의 테이블(diag_id·cataract_score…)이 남아 있으면 비켜준다.
    DROP이 아니라 RENAME이어야 한다 — 기존 진단 기록을 지우면 안 된다."""
    conn = FakeConn(existing_tables={"diagnoses"})
    name = await database._rename_incompatible_schema(
        conn, {"diag_id", "cataract_score", "ai_result"}
    )
    assert name == "diagnoses_legacy"
    assert len(conn.executed) == 1
    assert "RENAME TO" in conn.executed[0]
    assert "DROP" not in conn.executed[0].upper()


@pytest.mark.anyio
async def test_백업이름이_이미_있으면_다음_번호를_쓴다():
    """같은 DB에서 두 번 겪으면 첫 백업을 덮어써서 데이터를 잃는다."""
    conn = FakeConn(existing_tables={"diagnoses", "diagnoses_legacy", "diagnoses_legacy_1"})
    name = await database._rename_incompatible_schema(conn, {"diag_id"})
    assert name == "diagnoses_legacy_2"
    assert 'RENAME TO "diagnoses_legacy_2"' in conn.executed[0]
