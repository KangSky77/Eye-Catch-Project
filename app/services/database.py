import logging

from app.core.config import settings

# asyncpg는 선택적 의존성. 설치돼 있지 않아도 앱은 정상 기동하고
# DB 저장 기능만 비활성화됩니다. (pip install asyncpg 시 활성화)
try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)

_pool = None

# save_diagnosis()의 INSERT가 실제로 쓰는 컬럼. 아래 CREATE TABLE과 반드시 일치해야 한다.
REQUIRED_COLUMNS = frozenset(
    {"id", "cataract_result", "amsler_result", "symptoms", "gemma_opinion"}
)


async def _verify_schema(conn) -> None:
    """기존 diagnoses 테이블이 이 코드가 기대하는 모양인지 확인한다.

    왜 필요한가 (실제로 겪은 사고):
        CREATE TABLE IF NOT EXISTS는 '이름이 같은 테이블'만 보고 넘어간다. 예전 설계의
        테이블(diag_id·cataract_score·ai_result …)이 남아 있는 DB에서는 아무 일도 하지
        않고 조용히 성공하고, 기동 로그에도 "DB 풀 초기화 완료"가 찍힌다.
        그러다 사용자가 저장에 동의한 '그 순간'에야 INSERT가 UndefinedColumnError로
        터지고, 라우트가 소프트 실패로 감싸서 화면에는 "저장하지 못했습니다"만 남는다.
        → 스키마가 안 맞는다는 사실을 기동 시점에, 고칠 방법과 함께 알려준다.
    """
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = 'diagnoses'"
    )
    actual = {r["column_name"] for r in rows}
    missing = REQUIRED_COLUMNS - actual
    if missing:
        raise RuntimeError(
            "diagnoses 테이블이 이 코드와 맞지 않습니다 — 저장 기능을 끕니다.\n"
            f"    없는 컬럼: {sorted(missing)}\n"
            f"    실제 컬럼: {sorted(actual)}\n"
            "    예전 설계의 테이블이 남아 있는 것입니다. 기존 데이터를 보존한 채 비키려면:\n"
            "        ALTER TABLE diagnoses RENAME TO diagnoses_legacy;\n"
            "    그다음 서버를 다시 시작하면 올바른 테이블이 자동으로 만들어집니다."
        )


async def init_db_pool() -> None:
    global _pool
    if asyncpg is None:
        raise RuntimeError("asyncpg 미설치 — 진단 저장 기능 비활성화 (pip install asyncpg)")
    _pool = await asyncpg.create_pool(
        host=settings.db_host,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        port=settings.db_port,
        min_size=1,
        max_size=5,
    )
    # 테이블 생성·검증은 커넥션을 반납한 뒤에 결과를 처리한다.
    # (pool.close()는 대여 중인 커넥션이 모두 돌아올 때까지 기다리므로,
    #  acquire() 블록 안에서 풀을 닫으면 그 자리에서 멈춘다.)
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS diagnoses (
                    id          SERIAL PRIMARY KEY,
                    cataract_result  TEXT NOT NULL,
                    amsler_result    TEXT NOT NULL,
                    symptoms         TEXT NOT NULL,
                    gemma_opinion    TEXT,
                    created_at       TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            # CREATE ... IF NOT EXISTS는 '이름'만 본다 — 실제 컬럼이 맞는지 여기서 확인한다.
            await _verify_schema(conn)
    except Exception:
        # 스키마가 안 맞거나 생성에 실패하면 저장은 어차피 전부 실패한다.
        # 풀을 열어둔 채 두면 유휴 커넥션만 붙잡으므로 정리하고 비활성 상태로 되돌린다.
        await _close_pool_quietly()
        raise
    logger.info("diagnoses 테이블 스키마 확인 완료")


async def _close_pool_quietly() -> None:
    """초기화 실패 경로에서 풀만 정리한다(원래 예외를 덮어쓰지 않도록 조용히)."""
    global _pool
    pool, _pool = _pool, None
    if pool is not None:
        try:
            await pool.close()
        except Exception:
            logger.debug("DB 풀 정리 실패(무시)", exc_info=True)


async def close_db_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def save_diagnosis(
    cataract_result: str,
    amsler_result: str,
    symptoms: list[str],
    gemma_opinion: str,
) -> int:
    """진단 결과를 DB에 저장하고 생성된 id를 반환합니다."""
    if _pool is None:
        raise RuntimeError("DB 풀이 초기화되지 않았습니다.")

    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO diagnoses (cataract_result, amsler_result, symptoms, gemma_opinion)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            cataract_result,
            amsler_result,
            ", ".join(symptoms),
            gemma_opinion,
        )
        return row["id"]
