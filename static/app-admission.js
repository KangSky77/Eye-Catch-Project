// Shared by the lightweight entry page and the screening app; no screening data.
(() => {
    const copy = {
        ko: ['입장 준비 중', '지금 다른 분들이 체험하고 있어요', '대기 순번 {n}번', '차례가 오면 자동으로 입장해요.\n이 화면을 열어두고 기다려 주세요.', '새로고침해도 유효한 대기 순번은 유지됩니다. 연결이 오래 끊기면 다시 대기합니다.', '앱의 대기를 기다리며 필요한 진료를 미루지 마세요.', '대기 취소', '다시 대기하기', '대기를 취소했습니다', '연결을 다시 확인하고 있어요. 자동으로 재시도합니다.'],
        en: ['Preparing your visit', 'Others are trying the app', 'Queue position: {n}', 'You will enter automatically when a visit ends. Keep this screen open.', 'Refreshing keeps a valid place. A long disconnection may require rejoining.', 'Do not delay needed medical care while waiting for the app.', 'Leave queue', 'Join again', 'You left the queue', 'Checking the connection. Retrying automatically.'],
        es: ['Preparando su visita', 'Otras personas están probando la aplicación', 'Posición en la cola: {n}', 'Entrará automáticamente cuando termine una visita. Mantenga esta pantalla abierta.', 'Actualizar conserva un turno válido. Tras una desconexión prolongada tendrá que volver a la cola.', 'No retrase la atención médica necesaria mientras espera.', 'Salir de la cola', 'Volver a la cola', 'Ha salido de la cola', 'Comprobando la conexión. Se reintentará automáticamente.'],
        fr: ['Préparation de votre visite', 'D’autres personnes essaient l’application', 'Position dans la file : {n}', 'Vous entrerez automatiquement à la fin d’une visite. Gardez cet écran ouvert.', 'Actualiser conserve une place valide. Une longue déconnexion peut nécessiter de rejoindre la file.', 'Ne retardez pas les soins nécessaires en attendant l’application.', 'Quitter la file', 'Rejoindre la file', 'Vous avez quitté la file', 'Vérification de la connexion. Nouvelle tentative automatique.'],
        ja: ['入場を準備しています', 'ほかの方がアプリを体験中です', '待ち順：{n}番', '体験が終わると自動で入場します。この画面を開いたままお待ちください。', '有効な待ち順は再読み込みでも維持されます。長い接続切れの後は再び並びます。', 'アプリを待つために必要な受診を遅らせないでください。', '待機を取り消す', 'もう一度並ぶ', '待機を取り消しました', '接続を確認しています。自動で再試行します。'],
        zh: ['正在准备进入', '其他人正在体验应用', '排队位置：第{n}位', '前面的体验结束后会自动进入。请保持此页面打开。', '刷新会保留有效的排队位置。长时间断线后可能需要重新排队。', '请勿因等待应用而延误必要的就医。', '取消排队', '重新排队', '已取消排队', '正在检查连接，将自动重试。']
    };
    const entry = document.body.hasAttribute('data-waiting-entry');
    const details = {
        ko: ['자동 입장 대기', '나의 대기 순번', '번', '입장을 기다리고 있어요'],
        en: ['Automatic admission', 'Your queue position', '', "You're in the queue"],
        es: ['Entrada automática', 'Su posición en la cola', '', 'Ya está en la cola'],
        fr: ['Entrée automatique', 'Votre place dans la file', '', 'Vous êtes dans la file'],
        ja: ['順番に自動入場', 'あなたの待ち順', '番', '順番をお待ちください'],
        zh: ['按顺序自动进入', '您的排队位置', '位', '正在等候进入']
    };
    const illustration = '<div class="queue-visual" aria-hidden="true"><svg viewBox="0 0 96 96" fill="none"><rect x="18" y="20" width="57" height="56" rx="12" fill="#DBEAFE" transform="rotate(-12 46 48)"/><rect x="20" y="18" width="57" height="56" rx="12" fill="white" stroke="#BDD3FF" stroke-width="1.5"/><path d="M30 44s7-10 18-10 18 10 18 10-7 10-18 10-18-10-18-10Z" stroke="#2563EB" stroke-width="2.5"/><circle cx="48" cy="44" r="5" stroke="#2563EB" stroke-width="2.5"/><path d="M37 64h22" stroke="#D3E2FF" stroke-width="3" stroke-linecap="round"/><circle cx="73" cy="73" r="15" fill="#2563EB" stroke="white" stroke-width="4"/><path d="M73 65v8l5 3" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>';
    let language = 'ko';
    try { language = localStorage.getItem('ec_lang') || navigator.language.split('-')[0]; } catch (_) { /* defaults */ }
    if (!copy[language]) language = 'en';
    let seat = false, enabled = true, explanationRequiresSeat = false, lastActivity = Date.now(), lastStatus = 0;
    let pending = null, resolveWait = null, rejectWait = null, joining = false, paused = false;
    let latest = {state: 'joining', position: 0}, dialog = null, busy = false, revision = 0, leaving = null;
    let cookieBlocked = false;
    const cookieCopy = {
        ko: '입장 순번을 유지하려면 이 사이트의 필수 쿠키를 허용하고 다시 대기해 주세요.',
        en: 'Allow essential cookies for this site, then join again to keep your place.',
        es: 'Permita las cookies esenciales de este sitio y vuelva a la cola para conservar su turno.',
        fr: 'Autorisez les cookies essentiels de ce site, puis rejoignez la file pour garder votre place.',
        ja: '順番を保持するため、このサイトの必須Cookieを許可してからもう一度並んでください。',
        zh: '请允许此网站的必要 Cookie，然后重新排队以保留您的位置。'
    };
    const nativeFetch = window.fetch.bind(window);
    async function api(action) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 8000);
        try {
            const response = await nativeFetch('/api/admission/' + action, {method: action === 'status' ? 'GET' : 'POST',
                cache: 'no-store', credentials: 'same-origin', signal: controller.signal});
            if (!response.ok) { const error = new Error('admission ' + response.status); error.status = response.status; throw error; }
            return await response.json();
        } finally { clearTimeout(timer); }
    }
    function card() {
        if (entry) return document.getElementById('queue-card');
        if (!dialog) {
            dialog = document.createElement('dialog');
            dialog.className = 'admission-dialog';
            dialog.setAttribute('aria-labelledby', 'queue-title');
            dialog.innerHTML = '<div class="queue-card"><div class="queue-brand">Eye-Catch</div><div class="queue-status"><span class="queue-status-dot" aria-hidden="true"></span><span id="queue-badge"></span></div>' + illustration + '<h1 id="queue-title"></h1><p id="queue-description"></p><div id="queue-position" class="queue-ticket" role="status" aria-live="polite" aria-atomic="true" hidden></div><div class="queue-help"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 6.7M20 5v6h-6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg><p id="queue-note"></p></div><button id="queue-cancel" type="button"></button><p id="queue-care" class="queue-care"></p></div>';
            dialog.addEventListener('cancel', event => { event.preventDefault(); cancel(); });
            document.body.appendChild(dialog);
            dialog.querySelector('button').onclick = cancel;
        }
        return dialog.querySelector('.queue-card');
    }
    function render() {
        if (!entry && !pending) return;
        const c = card(), words = copy[language], extra = details[language];
        c.dataset.state = paused ? 'paused' : latest.state;
        c.querySelector('#queue-badge').textContent = extra[0];
        c.querySelector('#queue-title').textContent = paused && !cookieBlocked ? words[8] : latest.state === 'waiting' ? extra[3] : words[0];
        c.querySelector('#queue-description').textContent = cookieBlocked ? cookieCopy[language] : latest.state === 'error' ? words[9] : words[3];
        const ticket = c.querySelector('#queue-position');
        ticket.hidden = !(latest.position > 0 && !paused);
        const positionKey = ticket.hidden ? '' : language + ':' + latest.position;
        // Stable live-region nodes avoid announcing the same number every poll.
        if (ticket.dataset.position !== positionKey) {
            ticket.dataset.position = positionKey;
            ticket.replaceChildren();
            if (!ticket.hidden) {
                const label = document.createElement('span'); label.className = 'queue-ticket-label'; label.textContent = extra[1];
                const value = document.createElement('span'); value.className = 'queue-ticket-value';
                const number = document.createElement('span'); number.className = 'queue-ticket-number'; number.textContent = latest.position;
                const unit = document.createElement('span'); unit.className = 'queue-ticket-unit'; unit.textContent = extra[2];
                value.append(number, unit); ticket.append(label, value);
            }
        }
        c.querySelector('#queue-note').textContent = words[4];
        c.querySelector('#queue-care').textContent = words[5];
        c.querySelector('#queue-cancel').textContent = paused ? words[7] : words[6];
        if (!entry && !dialog.open) dialog.showModal();
    }
    function accept(data) {
        latest = data; enabled = data.enabled; lastStatus = Date.now();
        explanationRequiresSeat = data.explanation_requires_seat === true;
        seat = !enabled || data.state === 'active';
        if (seat && pending) {
            const done = resolveWait;
            pending = resolveWait = rejectWait = null;
            if (dialog?.open) dialog.close();
            done();
        }
        render();
    }
    async function tick() {
        if (busy || paused || (!pending && (!seat || Date.now() - lastActivity > 15000))) return;
        busy = true;
        const version = revision, wasJoining = joining;
        try {
            let didJoin = joining;
            let data = await api(joining ? 'join' : 'status');
            if (version !== revision) { if (wasJoining) await api('leave'); return; }
            if (data.enabled && data.state === 'idle' && pending) { didJoin = true; data = await api('join'); }
            if (version !== revision) { await api('leave'); return; }
            // Confirm the HttpOnly cookie before redirecting; blocked cookies must
            // not create an endless loop of new tickets and /app redirects.
            if (data.enabled && didJoin) {
                const verified = await api('status');
                if (version !== revision) { await api('leave'); return; }
                if (verified.state === 'idle') { cookieBlocked = paused = true; seat = false; render(); return; }
                data = verified;
            }
            joining = false;
            accept(data);
        } catch (_) { if (version === revision) { latest = {state: 'error', position: latest.position}; render(); } }
        finally { busy = false; }
    }
    function ensure() {
        if (leaving) return leaving.then(ensure);
        lastActivity = Date.now();
        if (!enabled || (seat && Date.now() - lastStatus < 15000)) return Promise.resolve();
        if (pending) return pending;
        paused = false;
        cookieBlocked = false;
        joining = !seat;
        pending = new Promise((resolve, reject) => { resolveWait = resolve; rejectWait = reject; });
        const waiting = pending;
        render(); tick();
        return waiting;
    }
    function complete() {
        if (leaving) return leaving;
        revision++;
        seat = false;
        if (pending) {
            const reject = rejectWait;
            pending = resolveWait = rejectWait = null;
            const error = new Error('queue cancelled'); error.name = 'AbortError'; reject(error);
        }
        if (dialog?.open) dialog.close();
        leaving = (async () => {
            try { await api('leave'); } catch (_) { /* disconnected leases expire on the server */ }
            finally { leaving = null; }
        })();
        return leaving;
    }
    function cancel() {
        if (paused && entry) { paused = cookieBlocked = false; ensure().then(() => location.replace('/app')).catch(() => {}); tick(); return; }
        paused = true;
        const reject = rejectWait;
        pending = resolveWait = rejectWait = null;
        const error = new Error('queue cancelled'); error.name = 'AbortError';
        if (reject) reject(error);
        complete();
        if (dialog?.open) dialog.close();
        latest = {state: 'idle', position: 0}; render();
    }
    window.eyeCatchAdmission = {ensure, complete,
        explanationRequiresSeat: () => enabled && explanationRequiresSeat,
        hasSeat: () => !enabled || (seat && Date.now() - lastStatus < 45000),
        language: value => { if (copy[value]) { language = value; render(); } }};
    ['pointerdown', 'keydown', 'change'].forEach(type => document.addEventListener(type, () => { lastActivity = Date.now(); }, {passive:true}));
    setInterval(tick, 5000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) tick(); });
    if (entry) {
        const selector = document.getElementById('queue-language');
        selector.value = language;
        selector.onchange = () => { language = selector.value; document.documentElement.lang = language;
            try { localStorage.setItem('ec_lang', language); } catch (_) { /* optional */ } render(); };
        document.getElementById('queue-cancel').onclick = cancel;
        document.documentElement.lang = language;
        ensure().then(() => location.replace('/app')).catch(() => {});
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            const version = revision;
            api('status').then(data => { if (version !== revision) return; accept(data); if (!seat) ensure().catch(() => {}); })
                .catch(error => { if (version !== revision) return;
                    // Static assets can update before an old server is restarted.
                    if (error.status === 404) accept({enabled: false, state: 'active', position: 0});
                    else ensure().catch(() => {}); });
        });
    }
})();
