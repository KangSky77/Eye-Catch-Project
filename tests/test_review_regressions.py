"""Regressions reproduced during the September 5 full review."""
import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException
from PIL import Image

from app.api import routes
from app.services import vision, eye_validator, llm


@pytest.mark.anyio
async def test_readiness_requires_eye_validator(monkeypatch):
    monkeypatch.setattr(vision, 'weights_loaded', True)
    monkeypatch.setattr(eye_validator, 'is_ready', lambda: False)
    result = await routes.readyz()
    assert getattr(result, 'status_code', 200) == 503


def test_each_eye_must_pass_sharpness(monkeypatch):
    img = Image.new('RGB', (32, 32))
    monkeypatch.setattr(vision, 'weights_loaded', True)
    monkeypatch.setattr(vision.eye_detector, 'extract_eye_crops', lambda _: [img, img])
    scores = iter([0.2, 0.001])
    monkeypatch.setattr(vision, '_sharpness', lambda _: next(scores))
    monkeypatch.setattr(eye_validator, 'check_eye', lambda _: (True, 0.99))
    def forbidden(_):
        pytest.fail('Blurry eye must not reach classification')
    monkeypatch.setattr(vision, '_predict_single', forbidden)
    assert vision.predict_cataract(img)['result_code'] == 'blurry'


@pytest.mark.anyio
async def test_decode_waits_for_inference_slot(monkeypatch):
    slots = asyncio.Semaphore(1)
    await slots.acquire()
    calls = []
    async def decode(_):
        calls.append(True)
        return Image.new('RGB', (8, 8))
    monkeypatch.setattr(routes, '_inference_slots', slots)
    monkeypatch.setattr(routes, 'validate_and_read_image', decode)
    task = asyncio.create_task(routes.analyze_eye(None))
    try:
        await asyncio.sleep(0.02)
        assert not calls
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    assert slots.locked()  # cancellation must not release somebody else's slot


@pytest.mark.anyio
async def test_llm_queue_emits_keepalive_and_cleans_cancelled_waiter(monkeypatch):
    slots = asyncio.Semaphore(1)
    await slots.acquire()
    monkeypatch.setattr(routes, '_llm_slots', slots)
    monkeypatch.setattr(routes, 'KEEPALIVE_INTERVAL', 0.01, raising=False)
    started = []
    async def source():
        started.append(True)
        yield 'text'
    stream = routes._limited_stream(source())
    try:
        assert await asyncio.wait_for(anext(stream), 0.3) == llm.KEEPALIVE
        assert not started
    finally:
        await stream.aclose()
    slots.release()
    await asyncio.wait_for(slots.acquire(), 0.1)
    assert slots.locked()


@pytest.mark.anyio
async def test_fully_filtered_opinion_is_an_error(monkeypatch):
    async def source(_):
        yield '정상입니다.\n'
    monkeypatch.setattr(llm, 'stream_with_keepalive', source)
    result = ''.join([part async for part in llm.sanitized_stream('test')])
    assert llm.ERROR_MARKER in result


def test_env_backups_are_ignored():
    import subprocess
    result = subprocess.run(['git', 'check-ignore', '.env.bak.20260904'],
                            capture_output=True, text=True)
    assert result.returncode == 0


@pytest.mark.anyio
@pytest.mark.parametrize('question', [
    'Does this affect one eye or both eyes?',
    'Is it one or both eyes?',
    '불편한 눈은 한쪽 눈인가요, 양쪽 눈인가요?',
])
async def test_alternative_questions_get_text_input(monkeypatch, question):
    async def generate(_):
        return question
    monkeypatch.setattr(llm, 'generate_ollama', generate)
    assert await llm.generate_next_question('en', '', '', []) == (question, 'text')


def test_gate_is_required_for_readiness():
    from app.services import eye_validator
    source = (Path(__file__).resolve().parent.parent / 'app' / 'services' / 'eye_validator.py').read_text(encoding='utf-8')
    assert 'and _gate_w is not None' in source
    assert 'return None, None' in source


def test_dynamic_question_answers_are_kept_as_pairs():
    chat = (Path(__file__).resolve().parent.parent / 'static' / 'app-chat.js').read_text(encoding='utf-8')
    report = (Path(__file__).resolve().parent.parent / 'static' / 'app-report.js').read_text(encoding='utf-8')
    assert 'state.dynamicAnswers.push({ q: current.q, a: answerText })' in chat
    assert 'state.dynamicAnswers || []' in report


@pytest.mark.anyio
async def test_llm_disconnect_after_waiter_acquires_returns_slot(monkeypatch):
    slots = asyncio.Semaphore(1)
    await slots.acquire()
    monkeypatch.setattr(routes, '_llm_slots', slots)
    monkeypatch.setattr(routes, 'KEEPALIVE_INTERVAL', 0.001)
    async def source():
        yield 'content'
    stream = routes._limited_stream(source())
    assert await anext(stream) == llm.KEEPALIVE
    slots.release()
    await asyncio.sleep(0.01)  # acquisition completes before generator resumes
    await stream.aclose()
    await asyncio.wait_for(slots.acquire(), 0.1)
    assert slots.locked()


@pytest.mark.anyio
@pytest.mark.parametrize('fails', [False, True])
async def test_llm_completion_and_failure_return_exactly_one_slot(monkeypatch, fails):
    slots = asyncio.Semaphore(1)
    monkeypatch.setattr(routes, '_llm_slots', slots)
    async def source():
        yield 'content'
        if fails:
            raise ValueError('upstream failure')
    stream = routes._limited_stream(source())
    assert await anext(stream) == 'content'
    with pytest.raises(ValueError if fails else StopAsyncIteration):
        await anext(stream)
    await asyncio.wait_for(slots.acquire(), 0.1)
    assert slots.locked()


# --- 2026-09-05 2차 리뷰: 1차 수정이 덜 닿은 곳 -------------------------------

def _asset(*parts):
    from pathlib import Path
    return Path(__file__).resolve().parent.parent / 'static' / 'assets' / Path(*parts)


@pytest.mark.skipif(not _asset('vision-scene.jpg').exists(), reason='번들 사진 없음')
def test_눈게이트가_사진_한장이_아니라_부류를_막는다():
    """임계값을 '문제된 사진 점수 바로 위'로 올리면 크롭만 바꿔도 다시 통과한다.

    실제로 0.40일 때 도서관 사진 원본(0.390)은 막혔지만 같은 사진의 3x3 상단 중앙
    조각(건물 옥상 + 하늘, 0.612)은 통과해 '정상' 판정을 받았다.
    임계값을 바꿀 때는 scripts/evaluate_eye_gate.py로 분포를 다시 재고 이 테스트를 볼 것.
    """
    from PIL import ImageOps
    if not eye_validator.warmup() or not eye_validator.gate_available():
        pytest.skip('눈 게이트 가중치 없음')

    with Image.open(_asset('vision-scene.jpg')) as src:
        scene = ImageOps.exif_transpose(src).convert('RGB')
    w, h = scene.size
    crops = {'원본': scene}
    for gy in range(3):
        for gx in range(3):
            crops[f'3x3-{gy}{gx}'] = scene.crop(
                (gx * w // 3, gy * h // 3, (gx + 1) * w // 3, (gy + 1) * h // 3))

    passed = {name: round(eye_validator._gate_prob(img), 4)
              for name, img in crops.items() if eye_validator.check_eye(img)[0]}
    assert not passed, f'비-눈 사진(및 그 크롭)이 눈으로 통과했다: {passed}'


@pytest.mark.skipif(not _asset('examples', 'face-good.jpg').exists(), reason='예시 사진 없음')
def test_게이트를_조여도_진짜_눈은_통과한다():
    """임계값을 올린 대가로 정상 경로가 막히면 안 된다 — 얼굴 사진의 눈 크롭은 통과해야 한다."""
    from PIL import ImageOps
    from app.services import eye_detector
    if not eye_validator.warmup() or not eye_validator.gate_available():
        pytest.skip('눈 게이트 가중치 없음')

    with Image.open(_asset('examples', 'face-good.jpg')) as src:
        face = ImageOps.exif_transpose(src).convert('RGB')
    eye_crops = eye_detector.extract_eye_crops(face)
    if not eye_crops:
        pytest.skip('MTCNN 미설치 — 얼굴에서 눈을 잘라낼 수 없음')
    rejected = [round(s, 4) for ok, s in map(eye_validator.check_eye, eye_crops) if not ok]
    assert not rejected, f'실제 눈 크롭이 거부됐다: {rejected}'


@pytest.mark.anyio
async def test_소견이_비면_필터_때문이든_아니든_오류로_알린다():
    """빈 소견을 성공으로 넘기면 프론트가 완료 처리하고 저장 동의까지 진행한다.

    세 경우 모두 사용자에게는 '소견서가 비어 있다'는 같은 결과이고 할 일도 같다(재생성).
    'dropped가 있을 때'로만 막으면 ②③이 새어 나간다.
    """
    async def feed(chunks):
        async def source(_):
            for c in chunks:
                yield c
        return source

    cases = {
        '① 금지 문장만 생성': ['정상입니다. 걱정하지 않으셔도 됩니다.'],
        '② 아무것도 생성 안 함': [''],
        '③ 공백만 생성': ['   \n  '],
    }
    for label, chunks in cases.items():
        original = llm.stream_with_keepalive
        llm.stream_with_keepalive = await feed(chunks)
        try:
            out = ''.join([part async for part in llm.sanitized_stream('t')])
        finally:
            llm.stream_with_keepalive = original
        assert llm.ERROR_MARKER in out, f'{label}: 빈 소견이 성공으로 나갔다'


def test_임상_눈_사진은_반드시_통과한다():
    """게이트 학습 음성에 이 사진들이 섞였던 적이 있다.

    EXTRA_NEG_DIRS = ["static/assets"]로 폴더를 통째로 음성에 넣는 바람에
    diseases/cataract-clinical.jpg(교과서적인 백내장 눈 클로즈업)가 '눈이 아님'으로
    학습됐다. 앱이 반드시 받아들여야 할 사진을 거부하도록 가르친 것이다.
    게이트를 다시 학습할 때마다 이 테스트로 확인한다."""
    from PIL import ImageOps
    if not eye_validator.warmup() or not eye_validator.gate_available():
        pytest.skip('눈 게이트 가중치 없음')

    rejected = {}
    for name in ('cataract-clinical.jpg', 'glaucoma-clinical.jpg'):
        path = _asset('diseases', name)
        if not path.exists():
            continue
        with Image.open(path) as src:
            img = ImageOps.exif_transpose(src).convert('RGB')
        ok, score = eye_validator.check_eye(img)
        if not ok:
            rejected[name] = round(score, 4)
    assert not rejected, (
        f"임상 눈 클로즈업이 '눈이 아님'으로 거부됐다: {rejected} — "
        "게이트 학습 음성에 눈 사진이 섞였는지 확인할 것"
    )


def test_게이트_학습이_눈_사진을_음성으로_쓰지_않는다():
    """음성 목록은 폴더 통째로가 아니라 파일별 명시여야 한다."""
    from pathlib import Path
    script = (Path(__file__).resolve().parent.parent / "scripts" / "build_eye_gate.py"
              ).read_text(encoding="utf-8")
    # 모듈 최상위 대입만 본다 — 경위를 적어둔 독스트링에는 옛 이름이 나온다
    assignments = [l for l in script.splitlines() if l.startswith("EXTRA_NEG_DIRS")]
    assert not assignments, (
        f"폴더를 통째로 음성에 넣고 있다 — 눈 사진이 섞일 수 있다: {assignments}"
    )
    assert "NON_EYE_ASSETS" in script
    # 임상 눈 사진이 음성 목록에 들어가면 안 된다
    non_eye_block = script[script.index("NON_EYE_ASSETS = ["):script.index("]", script.index("NON_EYE_ASSETS = ["))]
    for eye_photo in ("cataract-clinical", "glaucoma-clinical"):
        assert eye_photo not in non_eye_block, f"{eye_photo}가 음성 목록에 있다"
    # 학습/평가는 사진 단위로 갈라야 한다(크롭이 양쪽에 섞이면 암기를 재게 된다)
    assert "split.json" in script and 'split == "train"' in script
