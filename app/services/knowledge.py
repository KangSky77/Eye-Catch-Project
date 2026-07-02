"""
안과 참고지식 베이스 (RAG: Retrieval-Augmented Generation)
============================================================
환자의 검사 결과(언어 중립 코드)에 맞는 '검증된 안과 참고지식'을 검색해
LLM 프롬프트에 주입한다. → 모델이 자기 기억(환각 위험)이 아니라
아래의 확립된 의학 정보에 근거해 더 정확하고 전문적으로 답하도록 한다.

각 항목은 일반적으로 확립된 안과 상식을 간결히 정리한 교육용 요약이며,
확정 진단이 아니라 '가능성/경향' 수준의 설명을 의도한다.
의학 내용 수정·검수는 이 파일만 고치면 전체 프롬프트에 반영된다.
"""

# 질환 코드 → 참고지식. code는 프론트(설문/판독)에서 넘어오는 언어 중립 키.
KB = {
    "cataract": {
        "title": "백내장 (Cataract)",
        "keywords": ["백내장", "수정체", "뿌옇", "눈부심", "번짐", "혼탁",
                     "cataract", "lens", "blurry", "glare", "cloudy"],
        "text": (
            "백내장은 수정체가 혼탁해져 시야가 뿌옇고 빛 번짐·눈부심이 생기는 질환으로, "
            "노화·자외선·당뇨·흡연이 위험을 높입니다. 세극등 현미경 검사로 혼탁 정도를 "
            "확인하며, 초기엔 경과 관찰, 일상에 지장이 크면 인공수정체 수술을 고려합니다."
        ),
    },
    "macular": {  # 암슬러 격자 이상 → 황반(AMD) 신호
        "title": "황반변성 (Macular Degeneration)",
        "keywords": ["황반", "암슬러", "휘어", "일그러", "중심 시력", "변형시",
                     "macular", "amsler", "distort", "central vision"],
        "text": (
            "암슬러 격자에서 선이 휘거나 가운데가 어둡게 보이면 망막 중심부인 황반의 이상을 "
            "시사합니다. 황반변성은 중심 시력이 손상돼 사물이 일그러져 보이며 노화·흡연·고혈압이 "
            "위험요인입니다. 안저 검사와 빛간섭단층촬영(OCT)으로 확인하고, 일부 유형은 항VEGF "
            "주사로 진행을 늦출 수 있어 조기 발견이 중요합니다."
        ),
    },
    "glaucoma": {
        "title": "녹내장 (Glaucoma)",
        "keywords": ["녹내장", "시야가 좁", "주변 시야", "안압",
                     "glaucoma", "peripheral", "tunnel", "pressure"],
        "text": (
            "주변 시야가 좁아지는 느낌은 녹내장 신호일 수 있습니다. 안압 상승 등으로 시신경이 "
            "서서히 손상돼 초기 증상이 거의 없고, 손상된 시신경은 회복되지 않아 조기 발견이 "
            "핵심입니다. 안압 측정·안저·시야 검사로 진단하며, 안약으로 안압을 조절해 진행을 "
            "늦춥니다."
        ),
    },
    "retinopathy": {
        "title": "당뇨망막병증 (Diabetic Retinopathy)",
        "keywords": ["당뇨", "비문증", "실오라기", "떠다니", "망막", "혈당",
                     "diabetic", "retinopathy", "floaters", "blood sugar"],
        "text": (
            "눈앞에 점·실오라기가 떠다니는 비문증이나 시야 흐림은 당뇨망막병증과 연관될 수 "
            "있습니다. 높은 혈당이 망막 미세혈관을 손상시키는 합병증으로, 산동(동공 확대) "
            "안저 검사와 OCT로 확인하고 혈당·혈압 관리가 기본입니다. 당뇨가 있으면 증상이 "
            "없어도 정기 안저 검진이 권장됩니다."
        ),
    },
    "general": {
        "title": "일반 눈 건강 관리",
        "keywords": ["관리", "예방", "정기 검진", "care", "prevent", "checkup"],
        "text": (
            "주요 안질환(백내장·황반변성·녹내장·당뇨망막병증)은 초기에 증상이 없는 경우가 "
            "많습니다. 40세 이후 1~2년마다 안과 정기 검진(안압·안저 포함)을 받고, 자외선 "
            "차단·금연·혈당 관리·눈 휴식이 기본 관리 수칙입니다."
        ),
    },
}


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
