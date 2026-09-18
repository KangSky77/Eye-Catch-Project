// AI 사진 인식 결과 — 서버 게이트(app/services/vision.py의 PHOTO_CHECKS)가 무엇을 보고
// 통과/거절했는지 기준별로 보여준다.
//
// 예전에는 업로드 전에 사람에게 '사진에서 눈동자가 보이나요?'를 묻고 스스로 통과시키게
// 했다. 판단 기준을 아는 사람이 드물고 자기 사진은 대체로 통과시키는 데다, 같은 검사를
// 서버가 이미 하고 있어 질문이 두 번이었다. 이제는 AI가 판단하고, 사람은 결과를 본다.
const photoCheckCopy = {
    ko: ['이 사진으로는 검사할 수 없어요', 'AI 사진 인식 기준 — 모두 통과', '확인하지 못함',
        '사진 크기가 충분해요', '한 사람만 찍혀 있어요', '초점이 맞고 흔들리지 않았어요', '밝기가 충분해요',
        '눈을 찾았어요', '눈을 뜨고 있어요', '빛 반사에 가리지 않았어요', '다른 사진 고르기'],
    en: ['This photo cannot be assessed', 'AI photo checks — all passed', 'Not checked',
        'Photo is large enough', 'Only one person in frame', 'In focus, not blurred', 'Bright enough',
        'An eye was found', 'The eye is open', 'Not covered by glare', 'Choose another photo'],
    es: ['Esta foto no se puede evaluar', 'Comprobaciones de la IA: todas superadas', 'Sin comprobar',
        'La foto es bastante grande', 'Solo una persona en la imagen', 'Enfocada, sin movimiento', 'Luz suficiente',
        'Se ha encontrado un ojo', 'El ojo está abierto', 'Sin reflejos que tapen el ojo', 'Elegir otra foto'],
    fr: ['Cette photo ne peut pas être analysée', 'Contrôles de l’IA : tous réussis', 'Non vérifié',
        'Photo assez grande', 'Une seule personne sur la photo', 'Nette, sans flou', 'Assez lumineuse',
        'Un œil a été trouvé', 'L’œil est ouvert', 'Pas masqué par un reflet', 'Choisir une autre photo'],
    ja: ['この写真では検査できません', 'AIの写真チェック — すべて通過', '未確認',
        '写真の大きさが十分です', '写っているのは一人だけです', 'ピントが合いブレていません', '明るさが十分です',
        '目を見つけました', '目が開いています', '光の反射で隠れていません', '別の写真を選ぶ'],
    zh: ['这张照片无法检测', 'AI 照片识别标准 — 全部通过', '未检查',
        '照片尺寸足够', '画面中只有一个人', '对焦清晰、未抖动', '亮度足够',
        '已找到眼睛', '眼睛是睁开的', '没有被反光遮挡', '选择其他照片']
};
// review_retake: index.html의 '다른 사진 고르기' 버튼이 data-i18n으로 참조하는데
// 정의가 어디에도 없어서 6개 언어 모두 한국어로 굳어 있었다(2026-09-17 실측).
const PHOTO_CHECK_KEYS = ['check_fail_title', 'check_pass_title', 'check_unknown',
    'chk_resolution', 'chk_single_face', 'chk_sharp', 'chk_bright',
    'chk_eye_visible', 'chk_eye_open', 'chk_no_glare', 'review_retake'];
for (const [lang, copy] of Object.entries(photoCheckCopy)) {
    PHOTO_CHECK_KEYS.forEach((key, i) => translations[lang][key] = copy[i]);
}

/** 기준 목록을 <ul>에 그린다. ok=true 체크 / false 엑스 / null(앞 기준이 막혀 확인 못 함) 대시.
 *
 *  왜 null을 X로 칠하지 않는가: 게이트는 앞 기준이 무너지면 뒤를 보지 않는다. 흔들린 사진의
 *  눈 크롭은 눈 게이트에서 0.1점이 나오므로, 측정했더라도 '눈이 없다'는 틀린 말이 된다. */
function renderPhotoChecks(list, checks) {
    if (!list) return;
    const t = translations[state.lang] || {};
    list.innerHTML = '';
    (checks || []).forEach(c => {
        const li = document.createElement('li');
        li.className = 'pc-item ' + (c.ok === true ? 'pc-ok' : c.ok === false ? 'pc-no' : 'pc-unknown');
        const mark = document.createElement('span');
        mark.className = 'pc-mark';
        mark.setAttribute('aria-hidden', 'true');
        mark.textContent = c.ok === true ? '✓' : c.ok === false ? '✕' : '–';
        const label = document.createElement('span');
        label.textContent = t['chk_' + c.key] || c.key;
        // 표시가 기호뿐이면 스크린리더에는 '체크 / 엑스'가 읽히지 않는다.
        if (c.ok !== true) li.setAttribute('aria-label',
            `${label.textContent} — ${c.ok === false ? (t.check_fail_title || '') : (t.check_unknown || '')}`);
        li.appendChild(mark);
        li.appendChild(label);
        list.appendChild(li);
    });
}

let _photoCheck = null;
function closePhotoCheck() { if (_photoCheck) _photoCheck(); }

/** 열려 있는 재촬영 안내창의 글자를 현재 언어로 (다시) 쓴다.
 *  창을 처음 열 때와 언어를 바꿀 때 같은 경로를 쓴다 — 두 벌로 나뉘면 한쪽만 번역된다. */
function renderPhotoCheckText() {
    if (!_photoCheckView) return;
    const t = translations[state.lang] || {};
    const body = document.getElementById('photo-check-body');
    if (body) body.textContent = t['ai_' + _photoCheckView.reasonCode] || '';
    renderPhotoChecks(document.getElementById('photo-check-list'), _photoCheckView.checks);
}

// 열려 있는 창을 언어 전환 때 다시 그리려면 '무엇을 보여주는 중인지'를 들고 있어야 한다.
// 문장이 아니라 언어 중립 코드로 들고 있다가 그릴 때 현재 언어로 만든다.
let _photoCheckView = null;

/** 재촬영 판정을 받은 사진을 이유·기준과 함께 보여주고, 다른 사진을 고르게 한다.
 *  file이 없으면(미리보기를 만들 수 없는 경로) 사진 없이 기준만 보여준다.
 *  reasonCode는 서버의 result_code(eyes_hidden·invalid·blurry…) — 문장이 아니다. */
function showPhotoCheckFailure(file, checks, reasonCode) {
    closePhotoCheck();
    const dialog = document.getElementById('photo-check');
    // <dialog> 미지원 브라우저(구형 iOS Safari·일부 인앱 WebView)에서는 업로드 카드의
    // 고정 배너가 이미 같은 이유를 말한다. 사람에게 물어보던 것이 아니므로 막지 않는다.
    if (!dialog || typeof dialog.showModal !== 'function') return;

    const preview = document.getElementById('photo-check-image');
    const body = document.getElementById('photo-check-body');
    const retake = document.getElementById('photo-check-retake');
    // 사진을 건너뛰는 버튼은 수술한 사람에게만 보인다(안대·보호대로 촬영이 불가능한 경우).
    // 일반 검사는 사진이 검사의 본체라, 건너뛰면 남는 것이 문진뿐이다.
    const symptoms = document.getElementById('photo-check-symptoms');
    const url = file ? URL.createObjectURL(file) : '';
    const finish = () => {
        if (_photoCheck !== finish) return;
        _photoCheck = null;
        _photoCheckView = null;
        if (preview) { preview.removeAttribute('src'); preview.hidden = true; }
        if (url) URL.revokeObjectURL(url);
        dialog.close();
    };
    _photoCheck = finish;

    _photoCheckView = { reasonCode, checks };
    renderPhotoCheckText();
    if (preview) {
        preview.hidden = !url;
        if (url) preview.src = url; else preview.removeAttribute('src');
    }
    // 버튼 핸들러는 이 창이 아직 살아 있을 때만 움직인다. finish()만 막으면 이미 닫힌
    // 창의 늦은 클릭(문진으로 빠진 뒤 재촬영 버튼)이 화면을 한 번 더 갈아탄다.
    const act = run => () => { if (_photoCheck !== finish) return; finish(); run(); };
    // 다른 사진 고르기 — 업로드 화면으로 돌려보내고 파일 선택창을 바로 연다.
    if (retake) retake.onclick = act(() => { if (typeof retakePhoto === 'function') retakePhoto(); });
    if (symptoms) symptoms.onclick = act(() => skipPhotoStep());
    dialog.oncancel = event => { event.preventDefault(); finish(); };
    dialog.showModal();
    if (retake) retake.focus();
}

/** 결과 화면의 '무엇을 확인했는지' 접이식 요약. */
function showPhotoCheckSummary(checks) {
    const box = document.getElementById('photo-check-summary');
    if (!box) return;
    const has = Array.isArray(checks) && checks.length;
    box.classList.toggle('hidden', !has);
    if (!has) return;
    renderPhotoChecks(document.getElementById('photo-check-summary-list'), checks);
}
