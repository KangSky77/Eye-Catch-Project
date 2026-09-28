"""'내 검사 결과 쉽게 설명해 줘' 답변이 빠뜨리거나 뒤집은 것이 없는지 코드로 확인한다.

왜 필요한가: 9/02에 '해석은 코드, AI는 조언만'으로 정했고 9/16에는 소견의 LLM 쉬운 말 변환도
고정 문장표로 바꿨다(plain_language.py). 9/28에 되살린 결과 설명 버튼은 다시 LLM이 소견을 풀어 쓴다.
위험 사례 8번 실측(2026-09-29, e2b)에서 뒤집힘은 0번이었지만 격자 이상을 2번, 권장 시기를 1번 빠뜨렸다.
빠진 채로 나가면 사용자는 '설명에 없으니 괜찮은가 보다'로 읽는다.

그래서 AI 설명은 그대로 두되, 필수 항목(비정상 소견·권장 조치 시기)이 모두 있는지 확인하고
하나라도 빠지거나 백내장 소견이 '정상'으로 뒤집혔으면 고정 문장으로 대신 보여준다.
어휘 목록은 느슨하게 잡는다 — 잘못 통과하는 쪽보다 불필요하게 고정 문장으로 가는 쪽이 안전하다.
"""
import re

from app.services.plain_language import rewrite_findings

# 필수 항목 코드 — 프론트(app-report.js explainRequired)가 현재 결과에서 고른다
REQUIRED_CODES = ("cat_risk", "cat_borderline", "ams_left", "ams_right", "ams_both", "tri_now", "tri_weeks")

_TERMS = {
    "cataract": {
        "ko": ["백내장", "수정체", "혼탁"], "en": ["cataract", "lens", "cloud"],
        "es": ["catarata", "cristalino", "opacidad"], "fr": ["cataracte", "cristallin", "opacit"],
        "ja": ["白内障", "水晶体", "混濁", "濁り"], "zh": ["白内障", "晶状体", "晶体", "混浊", "浑浊"],
    },
    # 경계 소견은 '백내장'이라는 말 없이 '점수가 경계 구간'으로만 말하는 문장이 있다(es·fr 고정 문장)
    "borderline": {"ko": ["경계"], "en": ["borderline"], "es": ["límite", "limite"], "fr": ["limite"],
                   "ja": ["境界"], "zh": ["临界", "边界"]},
    "amsler": {
        "ko": ["암슬러", "격자", "황반"], "en": ["amsler", "grid", "macula"],
        "es": ["amsler", "rejilla", "cuadrícula", "mácula", "macula"], "fr": ["amsler", "grille", "macula"],
        "ja": ["アムスラー", "格子", "黄斑"], "zh": ["阿姆斯勒", "方格", "网格", "黄斑"],
    },
    "left": {"ko": ["왼쪽", "좌안"], "en": ["left"], "es": ["izquierd"], "fr": ["gauche"], "ja": ["左"], "zh": ["左"]},
    "right": {"ko": ["오른쪽", "우안"], "en": ["right"], "es": ["derech"], "fr": ["droit"], "ja": ["右"], "zh": ["右"]},
    "both": {
        "ko": ["양쪽", "두 눈", "양안"], "en": ["both"], "es": ["ambos"], "fr": ["deux yeux", "les deux"],
        "ja": ["両"], "zh": ["双眼", "两眼", "两只"],
    },
    "doctor": {
        "ko": ["안과"], "en": ["ophthalmolog", "eye doctor", "eye exam", "eye specialist", "eye care", "eye clinic"],
        # fr 수 주 권고 고정 문장은 'Planifiez un examen dans quelques semaines'라 '안과'에 해당하는 말이 없다
        "es": ["oftalm", "examen ocular", "revisión"], "fr": ["ophtalmo", "examen", "consult"], "ja": ["眼科"], "zh": ["眼科"],
    },
    "soon": {
        "ko": ["빠른", "가까운 시일", "가능한 한 빨리", "조만간", "서둘러", "빨리", "되도록 일찍"],
        "en": ["soon", "promptly", "without delay"], "es": ["pronto", "cuanto antes", "lo antes"],
        "fr": ["rapidement", "bientôt", "dès que possible", "sans tarder"],
        "ja": ["早め", "早く", "すぐ", "速やか"], "zh": ["尽快", "尽早", "及早", "早日"],
    },
    "weeks": {"ko": ["주 내", "주 안", "몇 주", "수 주"], "en": ["week"], "es": ["semana"], "fr": ["semaine"],
              "ja": ["週間"], "zh": ["周内", "几周", "数周", "星期"]},
    # 백내장 문장에 이 말이 같이 있으면 '감지했다'가 '정상·없음'으로 뒤집힌 것으로 본다
    "normal": {
        "ko": ["정상", "이상 없", "이상이 없", "문제 없", "문제가 없", "감지되지 않", "감지하지 않", "발견되지 않", "보이지 않"],
        "en": ["normal", "no sign", "not detect", "no clear", "no cataract", "not find", "not found", "healthy"],
        "es": ["normal", "no se detect", "no detect", "sin signos", "no hay"],
        "fr": ["normal", "pas détect", "aucun signe", "pas de cataracte", "n'a pas"],
        "ja": ["正常", "異常なし", "異常はありません", "検出されませんでした", "見られません"],
        "zh": ["正常", "没有发现", "未发现", "未检测", "没有检测", "无异常"],
    },
}


# 단순 포함 검사는 'abnormal'·'anormal' 안의 'normal', '비정상' 안의 '정상', '不正常' 안의 '正常'을
# 뒤집힘으로 잘못 읽었다(2026-09-29 영어 실측 5번 중 2번 오탐). 라틴 문자 언어는 단어 앞 경계를 요구하고
# 한·중·일은 부정 접두어가 붙은 경우를 뺀다. 뒤쪽은 열어 둔다 — 'ophthalmolog', 'izquierd'처럼 어간으로 적었다.
_NEGATING_PREFIX = {"ko": "비", "zh": "不", "ja": "非"}


def _pattern(word: str, lang: str) -> str:
    if lang in _NEGATING_PREFIX:
        return f"(?<!{_NEGATING_PREFIX[lang]})" + re.escape(word)
    return r"(?<![a-zà-ÿ])" + re.escape(word)


_COMPILED = {
    (key, lang): re.compile("|".join(_pattern(w, lang) for w in words), re.I)
    for key, table in _TERMS.items() for lang, words in table.items()
}


def _has(text: str, key: str, lang: str) -> bool:
    return bool((_COMPILED.get((key, lang)) or _COMPILED[(key, "en")]).search(text))


def _sentences(text: str) -> list[str]:
    from app.services.safety import SENT_SPLIT
    out, buf = [], text
    while True:
        m = SENT_SPLIT.search(buf)
        if not m:
            break
        out.append(buf[:m.end()])
        buf = buf[m.end():]
    if buf.strip():
        out.append(buf)
    return [s.strip() for s in out if s.strip()]


def missing_items(text: str, required: list[str], lang: str) -> list[str]:
    """빠졌거나 뒤집힌 필수 항목 코드 목록. 빈 목록이면 통과."""
    missing: list[str] = []
    sentences = _sentences(text)
    for code in required:
        if code in ("cat_risk", "cat_borderline"):
            about = [s for s in sentences if _has(s, "cataract", lang)
                     or (code == "cat_borderline" and _has(s, "borderline", lang))]
            if not about:
                missing.append(code)
            elif any(_has(s, "normal", lang) for s in about):
                missing.append(code + ":reversed")
        elif code.startswith("ams_"):
            about = [s for s in sentences if _has(s, "amsler", lang)]
            side = code[4:]
            joined = " ".join(about)
            eye_ok = (_has(joined, "both", lang) or (_has(joined, "left", lang) and _has(joined, "right", lang))) \
                if side == "both" else _has(joined, side, lang)
            # AI can preserve the correct eye but still invert the result
            # ("the left-eye grid was normal"). Treat that as missing too.
            if not about or not eye_ok:
                missing.append(code)
            elif any(_has(sentence, "normal", lang) for sentence in about):
                missing.append(code + ":reversed")
        elif code == "tri_now":
            if not any(_has(s, "doctor", lang) and _has(s, "soon", lang) for s in sentences):
                missing.append(code)
        elif code == "tri_weeks":
            if not any(_has(s, "doctor", lang) and _has(s, "weeks", lang) for s in sentences):
                missing.append(code)
    return missing


async def fallback_text(lines: list[str], lang: str) -> str:
    """고정 문장(쉬운 말 문장표가 있으면 그 문장)을 이어 붙인다. 문장표에 없는 줄은 원문 그대로."""
    rewritten = await rewrite_findings([line for line in lines if line.strip()], lang)
    parts = []
    for item in rewritten:
        s = item["text"].strip()
        if s and s[-1] not in ".!?。！？":
            s += "。" if lang in ("ja", "zh") else "."
        parts.append(s)
    return " ".join(parts)
