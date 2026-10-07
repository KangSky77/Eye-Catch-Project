// Readiness is separate from screening results; checking never uploads user input.
let _serviceStatus = null;
let _statusChecking = false;
const SERVICE_STATUS_TIMEOUT_MS = 8000;

function refreshServiceStatus() {
    const t = translations[state.lang];
    const box = document.getElementById('service-status');
    if (!box) return;
    // 준비가 끝났으면 첫 화면에 아무것도 띄우지 않는다. 문제가 확인됐을 때만 보여 주고,
    // 다시 확인하는 동안에는 보이던 상태를 그대로 둔다(첫 확인 때 깜빡이지 않게).
    if (!_statusChecking) {
        const s = _serviceStatus?.services;
        box.hidden = !!s && s.photo === 'ready' && s.ollama === 'ready';
    }
    for (const [service, key] of [['photo', 'status_photo'], ['ollama', 'status_ai']]) {
        const el = document.getElementById('service-' + service);
        const value = _statusChecking ? 'checking' : _serviceStatus?.services?.[service] === 'ready' ? 'ready' : 'unavailable';
        el.textContent = `${t[key]} · ${t['status_' + value]}`;
        el.dataset.status = value;
    }
    const note = document.getElementById('service-note');
    note.textContent = _statusChecking ? t.status_checking_note
        : !_serviceStatus ? t.status_server_unavailable
        : _serviceStatus.services.photo !== 'ready' ? t.status_photo_unavailable
        : _serviceStatus.services.ollama !== 'ready' ? t.status_ai_unavailable : t.status_ready_note;
    const button = document.getElementById('service-recheck');
    button.disabled = _statusChecking;
    button.setAttribute('aria-busy', String(_statusChecking));
}

async function checkServiceStatus() {
    if (_statusChecking) return;
    _statusChecking = true;
    refreshServiceStatus();
    const controller = new AbortController();
    let deadline;
    try {
        const request = (async () => {
            const response = await fetch('/api/service-status', {signal: controller.signal, cache: 'no-store'});
            if (response.status !== 200 && response.status !== 503) throw new Error('status unavailable');
            const data = await response.json();
            if (!['ready', 'unavailable'].includes(data.services?.photo)
                || !['ready', 'unavailable'].includes(data.services?.ollama)) throw new Error('invalid status');
            return data;
        })();
        _serviceStatus = await Promise.race([request, new Promise((_, reject) => {
            deadline = setTimeout(() => { controller.abort(); reject(new Error('status timeout')); }, SERVICE_STATUS_TIMEOUT_MS);
        })]);
    } catch (error) {
        _serviceStatus = null;
    } finally {
        clearTimeout(deadline);
        _statusChecking = false;
        refreshServiceStatus();
    }
}

window.addEventListener('DOMContentLoaded', checkServiceStatus);
window.addEventListener('online', checkServiceStatus);
