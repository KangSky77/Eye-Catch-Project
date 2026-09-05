// ==========================================
// app-vision.js — AI 비전 분석 (Vision AI)
// app-core.js가 먼저 로드되어야 함 (state, nextStep 등 사용)
// ==========================================
// 백엔드(app/core/config.py의 max_upload_size_bytes) 기본값과 맞춘 클라이언트 사전 검사.
// 서버까지 올려서 거절당하기 전에 즉시 알려주면 모바일 데이터·대기시간을 아낄 수 있다.
const MAX_UPLOAD_MB = 10;

// ------------------------------------------
// 분석 로딩 진행 표시
// 서버 추론은 0.2초 수준이고, 폰에서 체감되는 대기는 거의 전부 '사진 업로드'다.
// 그래서 fetch 대신 XHR을 쓴다 — fetch는 업로드 진행률(upload.onprogress)을 주지 않는다.
// ------------------------------------------
const SLOW_HINT_AFTER_MS = 8000;   // 이 시간을 넘기면 "느릴 수 있다" 안내를 띄운다
const ANALYSIS_TIMEOUT_MS = 180000; // 끊긴 모바일망에서 로딩 화면이 영원히 남지 않게 3분 상한
let _analysisAbortController = null;
let _analysisRequestId = 0;

function startLoadingProgress() {
    const t = translations[state.lang];
    const titleEl = document.getElementById('loading-title');
    const elapsedEl = document.getElementById('loading-elapsed');
    const barEl = document.getElementById('upload-progress-bar');
    const wrapEl = document.getElementById('upload-progress');
    const hintEl = document.getElementById('loading-slow-hint');

    if (barEl) { barEl.style.width = '0%'; barEl.classList.remove('is-indeterminate'); }
    if (wrapEl) wrapEl.setAttribute('aria-valuenow', '0');
    if (hintEl) hintEl.classList.add('hidden');
    if (titleEl) titleEl.textContent = t.loading_uploading || '사진 업로드 중';

    const tmpl = t.loading_elapsed || '{s}초 경과';
    const t0 = performance.now();
    if (elapsedEl) elapsedEl.textContent = tmpl.replace('{s}', '0.0');

    const timer = setInterval(() => {
        const ms = performance.now() - t0;
        if (elapsedEl) elapsedEl.textContent = tmpl.replace('{s}', (ms / 1000).toFixed(1));
        if (hintEl && ms > SLOW_HINT_AFTER_MS) hintEl.classList.remove('hidden');
    }, 100);

    return {
        // 업로드 진행률(0~100)
        setProgress(pct) {
            // 99%에서 멈춘다. 업로드 바이트를 다 내보냈다고 끝난 게 아니라서,
            // 100%를 띄우면 '다 됐는데 왜 안 넘어가지?'가 된다.
            const v = Math.max(0, Math.min(99, Math.round(pct)));
            if (barEl) barEl.style.width = v + '%';
            if (wrapEl) wrapEl.setAttribute('aria-valuenow', String(v));
        },
        // 업로드가 끝나 서버가 분석하는 구간으로 전환.
        // 주의: xhr.upload 진행률은 '내보냈다'는 뜻이지 '서버가 다 받았다'는 뜻이 아니다.
        // ngrok/모바일망에서는 100%가 뜬 뒤에도 실제 도착·처리까지 한참 더 걸린다.
        // 그래서 여기서 막대를 100%로 채우지 않고, 끝을 모르는 진행(불확정)으로 바꾼다.
        toAnalyzing() {
            if (titleEl) titleEl.textContent = t.loading_analyzing || 'AI가 분석 중';
            if (barEl) { barEl.style.width = ''; barEl.classList.add('is-indeterminate'); }
            if (wrapEl) wrapEl.removeAttribute('aria-valuenow');   // 불확정 상태를 스크린리더에도 알림
        },
        stop() { clearInterval(timer); }
    };
}

/** XHR 업로드 — fetch와 달리 진행률을 받을 수 있다. fetch Response와 비슷한 형태로 돌려준다. */
function uploadWithProgress(url, formData, onProgress, onUploaded, signal) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        xhr.responseType = 'text';
        xhr.timeout = ANALYSIS_TIMEOUT_MS;
        if (xhr.upload) {
            xhr.upload.onprogress = e => {
                if (e.lengthComputable && onProgress) onProgress((e.loaded / e.total) * 100);
            };
            xhr.upload.onload = () => { if (onUploaded) onUploaded(); };
        }
        xhr.onload = () => {
            let data = {};
            try { data = JSON.parse(xhr.responseText); } catch (e) { /* 비-JSON 응답 */ }
            resolve({ ok: xhr.status >= 200 && xhr.status < 300, status: xhr.status, data });
        };
        xhr.onerror = () => reject(new Error('network'));
        xhr.ontimeout = () => reject(new Error('timeout'));
        xhr.onabort = () => {
            const err = new Error('aborted');
            err.name = 'AbortError';
            reject(err);
        };
        if (signal) {
            signal.addEventListener('abort', () => xhr.abort(), { once: true });
            if (signal.aborted) xhr.abort();
        }
        xhr.send(formData);
    });
}

// 업로드 카드 상단 고정 오류 배너 — 토스트는 카드 아래쪽에 잠깐 떠서 놓치기 쉬웠다(외부 리뷰).
// 다음 사진을 고를 때까지 남는다.
function showUploadError(msg) {
    const el = document.getElementById('upload-error');
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('hidden');
}
function clearUploadError() {
    const el = document.getElementById('upload-error');
    if (el) { el.textContent = ''; el.classList.add('hidden'); }
}

async function runAIAnalysis(droppedFile) {
    const fileInput = document.getElementById('cataract-file');
    const file = droppedFile || fileInput.files[0];
    // 같은 파일을 다시 고를 때도 change 이벤트가 뜨도록 값을 비운다
    // (에러 후 같은 사진을 재시도하면 아무 반응이 없던 문제)
    fileInput.value = '';
    if (!file) return;

    // 빠르게 사진을 다시 고르면 이전 응답이 나중에 도착해 최신 결과를 덮을 수 있다.
    // 이전 전송을 취소하고, 취소가 늦게 반영되더라도 requestId로 오래된 응답을 무시한다.
    const requestId = ++_analysisRequestId;
    if (_analysisAbortController) _analysisAbortController.abort();
    _analysisAbortController = null;

    const t = translations[state.lang];
    clearUploadError();
    if (!file.type.startsWith('image/')) {
        showToast(t.err_file_type || "Please upload an image file.", 'error');
        showUploadError(t.err_file_type || "Please upload an image file.");
        return;
    }
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
        const m = (t.err_file_size || "File too large ({n} MB max).").replace('{n}', MAX_UPLOAD_MB);
        showToast(m, 'error'); showUploadError(m);
        return;
    }

    if (typeof resetScreeningState === 'function') resetScreeningState();

    const r = new FileReader();
    r.onload = e => {
        const p = document.getElementById('preview-image');
        p.src = e.target.result;
        p.classList.remove('hidden');
    };
    r.readAsDataURL(file);
    nextStep('step-ai-loading');

    const fd = new FormData();
    fd.append('file', file);

    const progress = startLoadingProgress();
    const controller = new AbortController();
    _analysisAbortController = controller;
    try {
        const res = await uploadWithProgress(
            '/api/analyze-eye', fd,
            pct => progress.setProgress(pct),
            () => progress.toAnalyzing(),
            controller.signal
        );
        if (requestId !== _analysisRequestId) return;
        const d = res.data;
        if (!res.ok) {
            // detail이 문자열이 아닐 수 있음(422 검증 오류는 객체 배열) → 그대로 alert하면 [object Object]
            const msg = typeof d.detail === 'string' ? d.detail : (translations[state.lang].srv_err || "Error");
            showToast(msg, 'error'); showUploadError(msg);
            nextStep('step-photo');
            return;
        }

        // 판정 대신 재촬영을 요청하는 코드들 — 토스트 + 업로드 카드 상단 배너(다음 사진까지 유지)
        const retake = {
            blurry: translations[state.lang].ai_blurry || "사진이 흔들려 판독할 수 없어요. 또렷하게 다시 찍어주세요.",
            hold: translations[state.lang].ai_hold || "플래시 반사가 강해 판독할 수 없어요. 플래시를 끄고 다시 찍어주세요.",
            eyes_hidden: translations[state.lang].ai_eyes_hidden || "눈이 감겨 있거나 가려진 것 같아요. 눈을 크게 뜨고 안경·선글라스를 벗은 뒤 다시 찍어주세요.",
            invalid: translations[state.lang].ai_invalid || "눈 사진이 아닌 것 같아요. 눈을 가까이서 촬영한 사진을 올려주세요."
        };
        if (retake[d.result_code]) {
            showToast(retake[d.result_code], 'error', 7000);
            showUploadError(retake[d.result_code]);
            nextStep('step-photo');
            return;
        }

        // 백내장 결과를 선택 언어로 표시 (result_code 기반)
        const resultText = t['ai_' + d.result_code] || d.result;
        state.aiResultCode = d.result_code;   // 언어 중립 코드 저장 (RAG 검색용)
        state.eyeBreakdown = d.eyes || [];
        state.asymmetric = !!d.asymmetric;

        // 얼굴 모드(눈 2개)면 좌/우 분리 결과를, 아니면 단일 결과.
        // 표시 문자열이 아니라 원자료를 저장한다 — 언어를 바꾸면 formatCataractResult()가
        // 현재 언어로 다시 만든다(app-core.js 주석 참고).
        const twoEyes = d.mode === 'face' && Array.isArray(d.eyes) && d.eyes.length === 2;
        state.aiResultData = {
            code: d.result_code,
            probability: d.probability,
            twoEyes: twoEyes,
            eyes: d.eyes || [],
        };

        const disp = document.getElementById('ai-result-display');
        disp.innerHTML = '';
        // 판정별 색상: 위험=장미색 / 경계=호박색 / 정상=파랑(기존 톤 유지)
        const probColor = { risk: 'text-rose-600', borderline: 'text-amber-600', uncertain: 'text-amber-600', normal: 'text-blue-700' };
        // 모델 출력은 보정되지 않은 softmax 값이라 '확률'로 읽히면 안 된다.
        // (Brier/ECE/temperature scaling 미적용) 표기와 각주로 명시한다.
        const pProb = document.createElement('p');
        pProb.className = `text-xs font-black mb-1 ${probColor[d.result_code] || probColor.normal}`;
        pProb.textContent = `${t.score_label || 'AI 특징 점수'} ${d.probability}/100`;
        const pRes = document.createElement('p');
        pRes.className = 'text-xl font-bold';
        pRes.textContent = resultText;
        disp.appendChild(pProb);
        disp.appendChild(pRes);
        const pNote = document.createElement('p');
        pNote.className = 'text-[10px] text-slate-400 mt-2 leading-relaxed';
        pNote.textContent = t.score_note || '';
        disp.appendChild(pNote);

        // 애매한 신호(uncertain / 얼굴 모드의 borderline) → 눈 클로즈업 재촬영 권유.
        // 얼굴 사진은 편의 기능이고, 정확도는 눈을 한쪽씩 가까이 찍는 쪽이 훨씬 높다.
        if (d.closeup_suggested) {
            const hint = document.createElement('p');
            hint.className = 'closeup-hint';
            hint.textContent = t.closeup_hint || '얼굴 사진보다 눈을 한쪽씩 가까이(20~30cm) 찍으면 훨씬 정확해요.';
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'closeup-btn btn-pop';
            btn.textContent = t.closeup_btn || '눈 클로즈업으로 다시 찍기';
            btn.onclick = () => nextStep('step-photo');
            disp.appendChild(hint);
            disp.appendChild(btn);
        }

        // 눈별 분석 카드 (얼굴 모드 + 눈 2개일 때만)
        if (twoEyes) {
            renderEyeBreakdown(disp, d.eyes);
        } else if (d.mode === 'face' && d.eyes_detected > 0) {
            const pFace = document.createElement('p');
            pFace.className = 'text-[11px] text-slate-500 font-bold mt-2';
            const tmpl = t.face_mode_note || "얼굴 사진에서 눈 {n}곳을 찾아 분석했어요.";
            pFace.textContent = tmpl.replace('{n}', d.eyes_detected);
            disp.appendChild(pFace);
        }

        // 어떤 사진이 분석됐는지 결과 화면에서도 확인할 수 있어야 한다.
        // (로딩 화면에만 있어서, 사진을 잘못 고른 것을 결과에서 알아챌 방법이 없었다)
        showAnalyzedPhoto();

        setTimeout(() => {
            if (requestId === _analysisRequestId) nextStep('step-ai-result');
        }, 1000);
    } catch (e) {
        if (e && e.name === 'AbortError') return;
        showToast(translations[state.lang].srv_err || "Server Connection Error", 'error');
        showUploadError(translations[state.lang].srv_err || "Server Connection Error");
        nextStep('step-photo');
    } finally {
        // 성공·실패·중간 return 어느 경로로 나가든 경과 시간 타이머는 반드시 멈춘다
        // (안 멈추면 결과 화면으로 넘어간 뒤에도 초가 계속 올라간다)
        progress.stop();
        if (requestId === _analysisRequestId) _analysisAbortController = null;
    }
}

// 눈별(좌/우) 분석 결과 카드를 그린다 (얼굴 모드 + 눈 2개일 때).
function renderEyeBreakdown(container, eyes) {
    const t = translations[state.lang];
    const sideLabel = { left: t.eye_left, right: t.eye_right };

    const wrap = document.createElement('div');
    wrap.className = 'mt-4 pt-4 border-t border-slate-200 text-left';

    const title = document.createElement('p');
    title.className = 'text-[11px] font-black text-slate-400 mb-2';
    title.textContent = t.eye_breakdown_title || '눈별 분석';
    wrap.appendChild(title);

    // 판정 코드별 배지 색: 위험=장미색 / 경계=호박색 / 정상=에메랄드
    const codeStyle = {
        risk: 'bg-rose-100 text-rose-600',
        borderline: 'bg-amber-100 text-amber-600',
        uncertain: 'bg-amber-100 text-amber-600',
        normal: 'bg-emerald-100 text-emerald-600'
    };
    eyes.forEach(e => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between py-1.5';
        const label = document.createElement('span');
        label.className = 'text-sm font-bold text-slate-600';
        label.textContent = sideLabel[e.side] || e.side;
        const val = document.createElement('span');
        val.className = `text-sm font-black px-2.5 py-0.5 rounded-full ${codeStyle[e.code] || codeStyle.normal}`;
        // '%'를 붙이지 않는다(보정되지 않은 softmax) — 결과 카드·리포트와 같은 x/100 표기
        val.textContent = `${e.probability}/100`;
        row.appendChild(label);
        row.appendChild(val);
        wrap.appendChild(row);
    });

    if (state.asymmetric) {
        const badge = document.createElement('p');
        badge.className = 'mt-2 text-[11px] font-black text-rose-600 bg-rose-50 rounded-lg px-3 py-2';
        badge.textContent = t.eye_unilateral || '편측 의심';
        wrap.appendChild(badge);
    }

    const note = document.createElement('p');
    note.className = 'mt-2 text-[10px] text-slate-400 leading-relaxed';
    note.textContent = t.eye_ref_note || '';
    wrap.appendChild(note);

    container.appendChild(wrap);
}

/** Repaint the already displayed analysis when the language changes. */
function refreshAiResultDisplay() {
    const r = state.aiResultData, disp = document.getElementById('ai-result-display');
    if (!r || !disp) return;
    const t = translations[state.lang];
    const paragraphs = disp.querySelectorAll(':scope > p');
    if (paragraphs[0]) paragraphs[0].textContent = `${t.score_label || 'AI feature score'} ${r.probability}/100`;
    if (paragraphs[1]) paragraphs[1].textContent = t['ai_' + r.code] || r.code;
    if (paragraphs[2]) paragraphs[2].textContent = t.score_note || '';
    const labels = disp.querySelectorAll('.mt-4 .text-sm.font-bold');
    (r.eyes || []).forEach((e, i) => { if (labels[i]) labels[i].textContent = ({left:t.eye_left,right:t.eye_right}[e.side] || e.side); });
    const unilateral = disp.querySelector('.mt-4 .text-rose-600.bg-rose-50');
    if (unilateral) unilateral.textContent = t.eye_unilateral || 'Unilateral finding';
    const note = disp.querySelector('.mt-4 .text-slate-400');
    if (note) note.textContent = t.eye_ref_note || '';
}

// ------------------------------------------------------------------
// 암슬러 격자 — 반드시 한쪽 눈씩 따로 본다.
// 양안으로 보면 한쪽 눈의 결손을 반대쪽 눈이 메워버려 이상을 놓친다.
// 실제 임상 프로토콜도 한눈 가리기 + 중심 응시가 기본이다.
// ------------------------------------------------------------------
function startAmslerStep() {
    state.amslerEye = 'left';
    state.amslerResult = {};
    const box = document.getElementById('amsler-box');
    if (box) box.classList.remove('amsler-distorted');
    // 격자 크기는 부모의 실제 폭을 재서 정한다 — 화면에 붙이기 전에 계산하면
    // 폭이 0이라 잘못된 크기가 나온다. 그래서 nextStep() 다음에 그린다.
    nextStep('step-amsler');
    updateAmslerPrompt();
}

function updateAmslerPrompt() {
    const t = translations[state.lang];
    const el = document.getElementById('amsler-eye-instruction');
    if (el) el.textContent = t['ams_which_' + state.amslerEye] || '';
    renderAmslerGrid();
}

// ------------------------------------------------------------------
// 암슬러 격자를 '실물 크기'로 그린다.
//
// 왜 필요한가:
//   임상 암슬러는 10cm x 10cm를 5mm 칸 20x20으로 나눠 약 28~30cm에서 본다 —
//   중심 20°(편심 10°)를 덮고 칸 하나가 정확히 1°가 되도록 설계된 크기다.
//   기존 구현은 240 CSS px 고정 + 24px 칸(10x10)이었다. 같은 30cm에서 약 12°만
//   덮고 칸도 1°가 아니라서, 중심에서 6° 바깥의 암점은 구조적으로 볼 수 없었다.
//
// 어떻게:
//   시력검사에서 이미 받아둔 카드 캘리브레이션(px/mm)을 그대로 쓴다. 화면이 10cm를
//   담지 못하면 담을 수 있는 만큼 줄이고, '그 크기가 20°가 되는 거리'를 계산해
//   안내한다 — 물리 크기를 고정하는 것보다 시야각을 지키는 쪽이 임상적으로 맞다.
//   캘리브레이션이 없으면 CSS 기준 해상도(96dpi ≒ 3.78 px/mm)로 근사하고,
//   근사치임을 명시한 뒤 보정 화면으로 갈 수 있게 한다.
// ------------------------------------------------------------------
const AMSLER_SIDE_MM = 100;    // 표준 격자 한 변
const AMSLER_CELLS = 20;       // 표준 칸 수 (5mm 칸 = 1°)
const AMSLER_FIELD_DEG = 20;   // 격자가 덮는 시야각(편심 ±10°)
const CSS_PX_PER_MM = 96 / 25.4;   // CSS px의 기준 해상도(96dpi)

function renderAmslerGrid() {
    const box = document.getElementById('amsler-box');
    if (!box) return;
    // 아직 화면에 붙지 않았으면(폭 0) 재봤자 0이다 — 다음 프레임에 다시 시도한다.
    // 이걸 빼면 숨겨진 상태에서 잰 값으로 그려져 칸 수와 안내 거리가 어긋난다.
    if (!box.offsetParent && box.getBoundingClientRect().width === 0) {
        requestAnimationFrame(renderAmslerGrid);
        return;
    }
    const t = translations[state.lang];

    const cal = (typeof loadCalibration === 'function') ? loadCalibration() : null;
    const calibrated = !!cal && !(typeof calibrationStale === 'function' && calibrationStale(cal));
    const pxPerMm = calibrated ? cal.pxPerMm : CSS_PX_PER_MM;

    // 격자가 들어갈 수 있는 폭 = 부모의 '콘텐츠 폭'(패딩 제외).
    // clientWidth에는 패딩이 포함돼 있어서 그대로 쓰면 카드 밖으로 넘치고,
    // .amsler-grid의 max-width:100%에 잘려 칸 크기와 실제 폭이 어긋난다.
    let availPx = Math.max(160, window.innerWidth - 32);
    const parent = box.parentElement;
    if (parent) {
        const pcs = getComputedStyle(parent);
        const inner = parent.clientWidth
            - parseFloat(pcs.paddingLeft || 0) - parseFloat(pcs.paddingRight || 0);
        if (inner > 0) availPx = inner;
    }

    // availPx가 이미 부모의 콘텐츠 폭이므로 max-width:100%가 더 잘라낼 일이 없다.
    // (되읽기로 확인하려 들면 안 된다 — .amsler-grid에 transition이 걸려 있으면
    //  방금 설정한 값이 아니라 애니메이션 중간값이 돌아온다. 실제로 그렇게 해서
    //  칸 크기가 이전 폭 기준으로 계산돼 20칸이 아니라 23칸이 그려졌다.)
    const sidePx = Math.round(Math.min(AMSLER_SIDE_MM * pxPerMm, availPx));
    const sideMm = sidePx / pxPerMm;
    const cellPx = sidePx / AMSLER_CELLS;

    box.style.width = sidePx + 'px';
    box.style.height = sidePx + 'px';
    box.style.backgroundSize = `${cellPx}px ${cellPx}px`;

    // 이 크기가 AMSLER_FIELD_DEG를 덮는 거리:  d = side / (2 * tan(deg/2))
    const half = Math.tan((AMSLER_FIELD_DEG / 2) * Math.PI / 180);
    const distCm = Math.round(sideMm / (2 * half) / 10);

    const note = document.getElementById('amsler-dist-note');
    if (note) {
        note.textContent = (t.ams_dist_note || '')
            .replace('{d}', distCm).replace('{deg}', AMSLER_FIELD_DEG);
    }
    const uncal = document.getElementById('amsler-uncal');
    if (uncal) {
        uncal.classList.toggle('hidden', calibrated);
        const msg = uncal.querySelector('[data-role="msg"]');
        if (msg) msg.textContent = t.ams_uncal || '';
        const btn = uncal.querySelector('[data-role="go"]');
        if (btn) btn.textContent = t.ams_cal_go || '';
    }
}

// 회전·창 크기 변경으로 사용할 수 있는 폭이 바뀌면 격자도 다시 그린다.
window.addEventListener('resize', () => {
    const step = document.getElementById('step-amsler');
    if (step && step.classList.contains('active')) renderAmslerGrid();
});

/** 분석에 사용한 사진을 결과 화면에도 보여준다(로딩 화면의 미리보기를 복사). */
function showAnalyzedPhoto() {
    const src = document.getElementById('preview-image');
    const dst = document.getElementById('result-photo');
    if (!src || !dst || !src.src) return;
    dst.src = src.src;
    dst.alt = translations[state.lang].result_photo_label || '';
    const wrap = document.getElementById('result-photo-wrap');
    if (wrap) wrap.classList.remove('hidden');
    const cap = document.getElementById('result-photo-caption');
    if (cap) cap.textContent = translations[state.lang].result_photo_label || '';
}

function recordAmsler(bad) {
    state.amslerResult[state.amslerEye] = bad;

    if (state.amslerEye === 'left') {
        const grid = document.getElementById('amsler-box');
        if (grid) grid.classList.remove('amsler-distorted');
        state.amslerEye = 'right';
        updateAmslerPrompt();
        return;                       // 아직 반대쪽 눈이 남았다
    }

    const L = !!state.amslerResult.left, R = !!state.amslerResult.right;
    state.hasAmsler = L || R;         // 한쪽이라도 이상이면 이상 소견
    // 표시 문구는 formatAmslerResult()가 현재 언어로 만든다 — 여기서 문자열로 굳히지 않는다
    nextStep('step-chat');
    startChat();
}

// ------------------------------------------
// 사진 업로드 카드 드래그&드롭 — 데스크톱에서 파일 선택창을 거치지 않고 바로 분석
// ------------------------------------------
window.addEventListener('DOMContentLoaded', () => {
    // '카메라로 바로 찍기' 버튼 노출 — 터치 기기에서만.
    // CSS (hover: none) 조건은 S펜이 있는 갤럭시 Ultra에서 hover: hover 로 잡혀 버튼이 안 보였다(S25 Ultra 실기기, 2026-09-02).
    // maxTouchPoints 가 가장 믿을 만하고, 못 읽는 구형 브라우저는 UA 로 보조 판별한다.
    const isTouch = (navigator.maxTouchPoints || 0) > 0 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    if (isTouch) document.body.classList.add('touch-device');

    const zone = document.getElementById('dropzone');
    if (zone) {
        ['dragenter', 'dragover'].forEach(ev => zone.addEventListener(ev, e => {
            e.preventDefault();
            zone.classList.add('dragover');
        }));
        ['dragleave', 'drop'].forEach(ev => zone.addEventListener(ev, e => {
            e.preventDefault();
            zone.classList.remove('dragover');
        }));
        zone.addEventListener('drop', e => {
            const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
            if (file) runAIAnalysis(file);
        });
    }

    // 암슬러 "휘어보임" 버튼에 커서를 올리거나 포커스하면 격자가 왜곡되어 보인다 —
    // 사용자가 무엇을 고르는 건지 미리 볼 수 있게. 인라인 onmouseover였던 것을
    // 여기로 옮기면서 키보드 포커스(focus/blur)와 터치(pointer)에서도 동작하게 했다.
    const badBtn = document.getElementById('amsler-bad-btn');
    const box = document.getElementById('amsler-box');
    if (badBtn && box) {
        const on = () => box.classList.add('amsler-distorted');
        const off = () => box.classList.remove('amsler-distorted');
        ['pointerenter', 'focus'].forEach(ev => badBtn.addEventListener(ev, on));
        ['pointerleave', 'pointercancel', 'blur'].forEach(ev => badBtn.addEventListener(ev, off));
    }
});
