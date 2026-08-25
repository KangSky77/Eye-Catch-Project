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
function uploadWithProgress(url, formData, onProgress, onUploaded) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        xhr.responseType = 'text';
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
        xhr.send(formData);
    });
}

async function runAIAnalysis(droppedFile) {
    const fileInput = document.getElementById('cataract-file');
    const file = droppedFile || fileInput.files[0];
    // 같은 파일을 다시 고를 때도 change 이벤트가 뜨도록 값을 비운다
    // (에러 후 같은 사진을 재시도하면 아무 반응이 없던 문제)
    fileInput.value = '';
    if (!file) return;

    const t = translations[state.lang];
    if (!file.type.startsWith('image/')) {
        showToast(t.err_file_type || "Please upload an image file.", 'error');
        return;
    }
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
        showToast((t.err_file_size || "File too large ({n} MB max).").replace('{n}', MAX_UPLOAD_MB), 'error');
        return;
    }

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
    try {
        const res = await uploadWithProgress(
            '/api/analyze-eye', fd,
            pct => progress.setProgress(pct),
            () => progress.toAnalyzing()
        );
        const d = res.data;
        if (!res.ok) {
            // detail이 문자열이 아닐 수 있음(422 검증 오류는 객체 배열) → 그대로 alert하면 [object Object]
            const msg = typeof d.detail === 'string' ? d.detail : (translations[state.lang].srv_err || "Error");
            showToast(msg, 'error');
            nextStep('step-photo');
            return;
        }

        // 눈 사진이 아니라고 판단되면 의료 결과 대신 재촬영 안내
        if (d.result_code === 'invalid') {
            showToast(translations[state.lang].ai_invalid || "눈 사진이 아닌 것 같아요. 눈을 가까이서 촬영한 사진을 올려주세요.", 'error', 6000);
            nextStep('step-photo');
            return;
        }

        // 백내장 결과를 선택 언어로 표시 (result_code 기반)
        const resultText = t['ai_' + d.result_code] || d.result;
        state.aiResultCode = d.result_code;   // 언어 중립 코드 저장 (RAG 검색용)
        state.eyeBreakdown = d.eyes || [];
        state.asymmetric = !!d.asymmetric;

        // 얼굴 모드(눈 2개)면 좌/우 분리 결과를, 아니면 단일 결과를 리포트/소견서 문자열에 반영
        const twoEyes = d.mode === 'face' && Array.isArray(d.eyes) && d.eyes.length === 2;
        if (twoEyes) {
            const bySide = {}; d.eyes.forEach(e => bySide[e.side] = e);
            const lp = bySide.left ? bySide.left.probability : '-';
            const rp = bySide.right ? bySide.right.probability : '-';
            // 좌/우 수치 자체가 비대칭을 드러내므로 문자열은 간결하게(스키마 길이 제한 대비)
            state.aiResult = `${resultText} (${t.eye_left} ${lp}%, ${t.eye_right} ${rp}%)`;
        } else {
            state.aiResult = `${resultText} (${d.probability}%)`;
        }

        const disp = document.getElementById('ai-result-display');
        disp.innerHTML = '';
        // 판정별 색상: 위험=장미색 / 경계=호박색 / 정상=파랑(기존 톤 유지)
        const probColor = { risk: 'text-rose-600', borderline: 'text-amber-600', normal: 'text-blue-700' };
        // 모델 출력은 보정되지 않은 softmax 값이라 '확률'로 읽히면 안 된다.
        // (Brier/ECE/temperature scaling 미적용) 표기와 각주로 명시한다.
        const pProb = document.createElement('p');
        pProb.className = `text-xs font-black mb-1 ${probColor[d.result_code] || probColor.normal}`;
        pProb.textContent = `${t.score_label || 'AI 위험 점수'} ${d.probability}`;
        const pRes = document.createElement('p');
        pRes.className = 'text-xl font-bold';
        pRes.textContent = resultText;
        disp.appendChild(pProb);
        disp.appendChild(pRes);
        const pNote = document.createElement('p');
        pNote.className = 'text-[10px] text-slate-400 mt-2 leading-relaxed';
        pNote.textContent = t.score_note || '';
        disp.appendChild(pNote);

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

        setTimeout(() => nextStep('step-ai-result'), 1000);
    } catch (e) {
        showToast(translations[state.lang].srv_err || "Server Connection Error", 'error');
        nextStep('step-photo');
    } finally {
        // 성공·실패·중간 return 어느 경로로 나가든 경과 시간 타이머는 반드시 멈춘다
        // (안 멈추면 결과 화면으로 넘어간 뒤에도 초가 계속 올라간다)
        progress.stop();
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
        val.textContent = `${e.probability}%`;
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

// ------------------------------------------------------------------
// 암슬러 격자 — 반드시 한쪽 눈씩 따로 본다.
// 양안으로 보면 한쪽 눈의 결손을 반대쪽 눈이 메워버려 이상을 놓친다.
// 실제 임상 프로토콜도 한눈 가리기 + 중심 응시가 기본이다.
// ------------------------------------------------------------------
function startAmslerStep() {
    state.amslerEye = 'left';
    state.amslerResult = {};
    updateAmslerPrompt();
    nextStep('step-amsler');
}

function updateAmslerPrompt() {
    const t = translations[state.lang];
    const el = document.getElementById('amsler-eye-instruction');
    if (el) el.textContent = t['ams_which_' + state.amslerEye] || '';
}

function recordAmsler(bad) {
    state.amslerResult[state.amslerEye] = bad;

    if (state.amslerEye === 'left') {
        state.amslerEye = 'right';
        updateAmslerPrompt();
        return;                       // 아직 반대쪽 눈이 남았다
    }

    const L = !!state.amslerResult.left, R = !!state.amslerResult.right;
    state.hasAmsler = L || R;         // 한쪽이라도 이상이면 이상 소견
    const t = translations[state.lang];
    state.amslerLabel = (L && R) ? (t.ams_result_bad || '양쪽 이상')
                      : L ? (t.ams_result_left || '왼쪽 눈 이상')
                      : R ? (t.ams_result_right || '오른쪽 눈 이상')
                          : (t.ams_result_both || '양쪽 정상');
    nextStep('step-chat');
    startChat();
}

// ------------------------------------------
// 사진 업로드 카드 드래그&드롭 — 데스크톱에서 파일 선택창을 거치지 않고 바로 분석
// ------------------------------------------
window.addEventListener('DOMContentLoaded', () => {
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
