"""검사 요약 해석을 '쉬운 말'로 바꾼다 — 단, 바꾼 문장은 검증을 통과해야만 쓴다.

왜 이렇게까지 하는가:
    이 앱의 해석 문장(static/app-findings.js)은 검사 결과에 따라 코드가 고정 문장으로 만든다.
    LLM에게 해석을 맡겼더니 실제로 "암슬러가 정상이므로 녹내장 가능성이 낮다"는 문장이 나왔기 때문이다
    (app/services/safety.py 주석). 그래서 이 모듈은 LLM에게 '해석'을 시키지 않는다.
    이미 확정된 문장을 **말투만** 쉽게 바꾸게 하고, 아래 검사를 모두 통과한 줄만 화면에 내보낸다.

    1. 줄 수가 원문과 같아야 한다(한 줄이라도 빠지거나 합쳐지면 통째로 원문을 쓴다).
    2. 원문에 없던 숫자가 새로 나오면 안 된다(점수·나이·기간을 지어내는 것을 막는다).
    3. 원문에 없던 질환 이름이 나오면 안 되고, 원문에 있던 질환 이름은 사라지면 안 된다.
    4. safety.check_sentence를 통과해야 한다(확률·배제·진단·질환 교차 표현 금지).
    5. 원문보다 크게 길어지면 안 된다(설명을 덧붙였다는 뜻이다).

    검증에 실패한 줄은 조용히 원문으로 되돌린다. 실패는 로그에 남긴다.
"""
import logging
import re

from app.services import safety

logger = logging.getLogger(__name__)

# 원문 대비 허용 길이 — 말투를 풀어 쓰면 조금 길어질 수 있지만 '설명 추가'는 막는다.
MAX_LENGTH_RATIO = 1.6
MAX_LENGTH_SLACK = 20
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
# 줄 앞의 "1.", "2)", "- " 같은 머리표는 모델이 붙이는 형식이라 비교 전에 떼어낸다.
_BULLET = re.compile(r"^\s*(?:\d+\s*[.)、]|[-*•·])\s*")


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in _NUMBER.findall(text)}


def _diseases(text: str) -> set[str]:
    low = text.lower()
    return {key for key, terms in safety.DISEASE_TERMS.items()
            if any(term.lower() in low for term in terms)}


def check_rewrite(original: str, candidate: str) -> str | None:
    """바꾼 문장을 쓸 수 있는지 본다. 쓸 수 있으면 None, 아니면 사유 문자열."""
    text = candidate.strip()
    if not text:
        return "empty"
    if len(text) > len(original) * MAX_LENGTH_RATIO + MAX_LENGTH_SLACK:
        return "too_long"
    if not _numbers(text) <= _numbers(original):
        return "new_number"
    before, after = _diseases(original), _diseases(text)
    if after - before:
        return "new_disease"
    if before - after:
        return "dropped_disease"
    reason = safety.check_sentence(text)
    if reason:
        return reason
    return None


def _prompt(lines: list[str], lang_name: str) -> str:
    numbered = "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))
    return f"""Rewrite each numbered line below in plain, everyday {lang_name} for an older reader.

[Absolute rules]
- Output exactly {len(lines)} lines, numbered "1." to "{len(lines)}.", in the same order.
- Keep the meaning identical. Do NOT add, remove or soften any fact.
- Do NOT add numbers, percentages, disease names, causes, reassurance or advice that is not in the line.
- Do NOT say a condition is likely, unlikely, ruled out or confirmed.
- Keep every disease name that already appears in the line.
- Each rewritten line must be about the same length or shorter.
- Output only the numbered lines, nothing else.

[Lines]
{numbered}"""


def parse_numbered(text: str, expected: int) -> list[str] | None:
    """모델 출력에서 번호 줄만 뽑는다. 줄 수가 다르면 None(= 통째로 원문 사용)."""
    lines = [_BULLET.sub("", line).strip() for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    if len(lines) != expected:
        return None
    return lines


async def rewrite_findings(lines: list[str], lang: str) -> list[dict]:
    """[{text, rewritten}] 반환. 실패·검증 탈락은 원문 그대로(rewritten=False)."""
    from app.services.llm import _lang_name, generate_ollama   # 순환 import 방지

    fallback = [{"text": line, "rewritten": False} for line in lines]
    if not lines:
        return fallback
    try:
        raw = await generate_ollama(_prompt(lines, _lang_name(lang)))
    except Exception:
        logger.warning("쉬운 말 변환 실패 — 원문을 그대로 쓴다", exc_info=True)
        return fallback

    candidates = parse_numbered(raw, len(lines))
    if candidates is None:
        logger.info("쉬운 말 변환: 줄 수가 달라 원문을 유지한다 (기대 %d)", len(lines))
        return fallback

    out, dropped = [], []
    for original, candidate in zip(lines, candidates):
        reason = check_rewrite(original, candidate)
        if reason:
            dropped.append(reason)
            out.append({"text": original, "rewritten": False})
        else:
            out.append({"text": candidate.strip(), "rewritten": True})
    if dropped:
        logger.warning("⚠️  쉬운 말 변환 %d줄 폐기 (사유: %s)", len(dropped), ", ".join(sorted(set(dropped))))
    return out
