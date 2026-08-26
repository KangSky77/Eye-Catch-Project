"""
안과 참고지식 베이스 (RAG: Retrieval-Augmented Generation)
============================================================
환자의 검사 결과(언어 중립 코드)에 맞는 '검증된 안과 참고지식'을 검색해
LLM 프롬프트에 주입한다. → 모델이 자기 기억(환각 위험)이 아니라
확립된 의학 정보에 근거해 더 정확하고 전문적으로 답하도록 한다.

각 항목은 일반적으로 확립된 안과 상식을 간결히 정리한 교육용 요약이며,
확정 진단이 아니라 '가능성/경향' 수준의 설명을 의도한다.

의학 내용은 코드가 아니라 **data/medical_knowledge.json**에 있다.
의학 전공자·조원이 파이썬을 건드리지 않고 문장만 검수·수정할 수 있게 분리했다.
(이 구조는 Antigravity 버전의 medical_guidelines.json 방식을 가져온 것)

로드 실패는 감추지 않고 즉시 예외로 띄운다 — 참고지식 없이 LLM을 돌리면
바로 환각 위험으로 이어지므로, 조용히 빈 지식으로 굴러가면 안 된다.
"""
import json
from pathlib import Path

# app/services/knowledge.py → 저장소 루트 → data/
KB_PATH = Path(__file__).resolve().parents[2] / "data" / "medical_knowledge.json"

# 코드·프론트가 실제로 참조하는 키. 프론트가 보내는 disease 코드(static/data.js의
# `disease:` 값)와 짝이 맞아야 하고, "general"은 아무 이상이 없을 때의 폴백이라 필수다.
REQUIRED_KEYS = ("cataract", "macular", "glaucoma", "retinopathy", "general")


def _load_kb(path: Path = KB_PATH) -> dict:
    """참고지식 JSON을 읽고 구조를 검증한다.

    손으로 고치다 생기는 실수(키 오타, 항목 누락, 빈 문장)를 서버 기동 시점에
    잡는다 — 런타임에 소견서가 조용히 부실해지는 것보다 낫다.
    """
    try:
        with open(path, encoding="utf-8") as f:
            kb = json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"참고지식 파일이 없습니다: {path}") from None
    except json.JSONDecodeError as e:
        raise RuntimeError(f"참고지식 JSON 문법 오류: {path} — {e}") from None

    if not isinstance(kb, dict):
        raise RuntimeError(f"참고지식 JSON의 최상위는 객체여야 합니다: {path}")

    missing = [k for k in REQUIRED_KEYS if k not in kb]
    if missing:
        raise RuntimeError(f"참고지식에 필수 항목이 없습니다: {missing} ({path})")

    for key, entry in kb.items():
        if not isinstance(entry, dict):
            raise RuntimeError(f"참고지식 '{key}'는 객체여야 합니다 ({path})")
        for field in ("title", "text"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeError(f"참고지식 '{key}'의 '{field}'가 비어 있습니다 ({path})")
        keywords = entry.get("keywords")
        if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            raise RuntimeError(f"참고지식 '{key}'의 'keywords'는 문자열 목록이어야 합니다 ({path})")

    return kb


# 질환 코드 → 참고지식. code는 프론트(설문/판독)에서 넘어오는 언어 중립 키.
KB = _load_kb()


def retrieve_for_opinion(cataract_code: str = "", amsler_abnormal: bool = False,
                         symptom_codes=None) -> list:
    """검사 결과(언어 중립 코드)에 해당하는 참고지식만 골라 반환."""
    symptom_codes = symptom_codes or []
    keys = []
    # 경계(borderline) 판정도 백내장 참고지식을 제공 — 소견서가 '왜 재검이 필요한지' 설명 가능
    if cataract_code in ("risk", "borderline"):
        keys.append("cataract")
    if amsler_abnormal:
        keys.append("macular")
    for c in symptom_codes:
        if c in KB and c not in keys:
            keys.append(c)
    if not keys:                      # 아무 이상 없으면 일반 관리 정보
        keys.append("general")
    return [KB[k] for k in keys]


def retrieve_for_chat(text: str, max_n: int = 2) -> list:
    """자유 질문(챗봇)에서 키워드로 가장 관련 깊은 참고지식 검색."""
    t = (text or "").lower()
    scored = []
    for k, e in KB.items():
        if k == "general":
            continue
        score = sum(1 for kw in e["keywords"] if kw.lower() in t)
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    snippets = [e for _, e in scored[:max_n]]
    return snippets or [KB["general"]]


def format_reference(snippets: list) -> str:
    """검색된 참고지식을 프롬프트용 블록 문자열로 변환."""
    if not snippets:
        return ""
    lines = [f"· {s['title']}: {s['text']}" for s in snippets]
    return "[참고 의학 정보 — 아래 내용에 근거해 작성하고, 여기에 없는 사실은 지어내지 마세요]\n" + "\n".join(lines)
