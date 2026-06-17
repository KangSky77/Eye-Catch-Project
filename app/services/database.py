from app.core.config import settings

# asyncpg는 선택적 의존성. 설치돼 있지 않아도 앱은 정상 기동하고
# DB 저장 기능만 비활성화됩니다. (pip install asyncpg 시 활성화)
try:
    import asyncpg
except ImportError:
    asyncpg = None

_pool = None


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
        # 테이블이 없으면 자동 생성
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
