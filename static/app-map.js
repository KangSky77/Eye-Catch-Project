// ==========================================
// app-map.js — 병원 찾기 (위치 기반 임베디드 지도)
// Leaflet 지도 + Overpass(OSM) 실제 안과 검색
// app-core.js가 먼저 로드되어야 함 (state, escapeHTML 사용)
// ==========================================
const DEFAULT_CENTER = [37.5012, 127.0396];   // 위치 거부 시 기본(강남)
// 목록 아이콘 — 기기마다 모양이 달라지는 이모지 대신 앱 전체와 같은 선형 SVG
const CLINIC_ICON = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 21V8.6l8-5 8 5V21"/><path d="M9.5 21v-5h5v5"/><path d="M12 7.4v3.4M10.3 9.1h3.4"/></svg>';
const GLOBE_ICON = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/><path d="M12 3.5c2.2 2.4 3.4 5.4 3.4 8.5S14.2 18.1 12 20.5c-2.2-2.4-3.4-5.4-3.4-8.5S9.8 5.9 12 3.5Z"/></svg>';
let _map = null, _userMarker = null, _clinicLayer = null, _mapTiles = null;
let _lastClinicSearch = null;

function ensureMap() {
    if (_map) { _map.invalidateSize(); return _map; }
    if (typeof L === 'undefined') return null;   // Leaflet 번들 로드 실패 → 호출자가 안내

    // 마커 아이콘 경로를 명시 — Leaflet은 기본적으로 스크립트 URL에서 images/ 위치를
    // 추론하는데, 로컬 번들 경로에서는 추론이 빗나가 마커가 안 보일 수 있다.
    if (L.Icon && L.Icon.Default) L.Icon.Default.imagePath = '/static/vendor/leaflet/images/';

    _map = L.map('leaflet-map', { zoomControl: true }).setView(DEFAULT_CENTER, 14);
    const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '© OpenStreetMap'
    });
    // 지도 '타일'은 성격상 로컬 번들에 넣을 수 없다(전 세계 이미지).
    // 오프라인이면 빈 회색 화면이 남는데, 그걸 방치하면 앱이 고장난 것처럼 보인다.
    // → 모든 타일이 실패하면 재시도 안내를 겹쳐 표시하고 기존 지도는 보존한다. 나머지 기능(검사·문진·리포트·PDF)은 영향 없음.
    let loaded = 0, failed = 0;
    _mapTiles = tiles;
    tiles.on('loading', () => { loaded = 0; failed = 0; });
    tiles.on('tileload', () => { loaded++; clearMapOffline(); });
    tiles.on('tileerror', () => { failed++; });
    tiles.on('load', () => { if (!loaded && failed) showMapOffline(); });
    tiles.addTo(_map);
    _clinicLayer = L.layerGroup().addTo(_map);

    // 위치 확인 전의 기본 지도(강남)는 '내 주변'처럼 오해된다(외부 리뷰). 예시 위치임을 지도 위에 명시하고
    // 흐리게 보여주다가, 실제 위치를 받으면 없앤다.
    const embed = document.querySelector('.map-embed');
    if (embed && !document.getElementById('map-example-badge')) {
        const badge = document.createElement('div');
        badge.id = 'map-example-badge';
        badge.className = 'map-example-badge';
        badge.setAttribute('data-i18n', 'map_example_badge');
        badge.textContent = translations[state.lang].map_example_badge || '예시 위치(서울 강남) — 아직 내 위치를 확인하지 않았어요';
        embed.appendChild(badge);
        embed.classList.add('is-example');
    }
    setTimeout(() => _map.invalidateSize(), 200);   // 숨겨진 탭 init 보정
    return _map;
}

/** 지도·마커를 보존한 채 연결 실패 안내를 겹쳐 표시한다. */
function showMapOffline() {
    const box = document.querySelector('.map-embed');
    const t = translations[state.lang];
    if (!box || document.getElementById('map-recovery')) return;
    const wrap = document.createElement('div');
    wrap.id = 'map-recovery';
    wrap.className = 'map-recovery';
    wrap.setAttribute('role', 'status');
    const msg = document.createElement('p');
    msg.setAttribute('data-i18n', 'map_offline');
    msg.textContent = t.map_offline;
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.setAttribute('data-i18n', 'map_retry');
    retry.textContent = t.map_retry;
    retry.onclick = retryMapTiles;
    wrap.append(msg, retry);
    box.appendChild(wrap);
}

function clearMapOffline() {
    const panel = document.getElementById('map-recovery');
    if (panel) panel.remove();
}

function retryMapTiles() {
    const map = ensureMap();
    if (!map || !_mapTiles) return;
    map.invalidateSize();
    _mapTiles.redraw();
}

function clearMapExample() {
    const badge = document.getElementById('map-example-badge');
    if (badge) badge.remove();
    const embed = document.querySelector('.map-embed');
    if (embed) embed.classList.remove('is-example');
}

function haversine(aLat, aLng, bLat, bLng) {
    const R = 6371000, rad = x => x * Math.PI / 180;
    const dLat = rad(bLat - aLat), dLng = rad(bLng - aLng);
    const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(aLat)) * Math.cos(rad(bLat)) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(s));   // meters
}
const fmtDist = m => m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(1)}km`;

let _locating = false;

function findNearbyClinics() {
    if (_locating) return;                  // 연타 시 요청이 겹치는 것 방지
    const status = document.getElementById('map-status');
    const t = translations[state.lang];
    const map = ensureMap();
    if (!map) {
        status.innerText = t.map_offline_short || "지도 오프라인";
        return;
    }
    if (typeof window !== 'undefined' && window.isSecureContext === false) {
        status.innerText = t.map_status_insecure || "현재 접속 주소에서는 위치를 사용할 수 없어요. 보안 연결(HTTPS)로 접속하거나 전체 지도에서 검색해 주세요.";
        return;
    }
    if (!navigator.geolocation) {
        status.innerText = t.map_status_unsupported || "이 브라우저는 위치 기능을 지원하지 않아요.";
        return;
    }
    status.innerText = t.map_status_loading || "위치를 확인하는 중...";

    _locating = true;
    const restoreBtn = setButtonBusy(document.getElementById('map-locate-btn'), t.map_status_loading || "");
    const done = () => { _locating = false; restoreBtn(); };

    // 첫 위치 측정(콜드 스타트)은 10초를 넘기기도 한다 — 갤럭시 S25 Ultra 실내에서 권한 허용 직후
    // 첫 요청이 시간 초과, 바로 다음 요청은 3ms(2026-09-27). 처음 쓰는 사람은 항상 첫 요청이라
    // 시간 초과 안내부터 보게 됐다. 시간 초과면 한 번만 더 길게 기다린다.
    let retried = false;
    const request = (timeout) => navigator.geolocation.getCurrentPosition(
        pos => {
            done();
            const lat = pos.coords.latitude, lng = pos.coords.longitude;
            clearMapExample();
            map.setView([lat, lng], 15);
            if (_userMarker) _userMarker.remove();
            _userMarker = L.marker([lat, lng]).addTo(map)
                .bindPopup(translations[state.lang].map_you || "내 위치");
            fetchClinics(lat, lng);
        },
        error => {
            // 재시도는 done()보다 먼저 — 버튼은 계속 '조회 중'으로, 잠금(_locating)도 유지한다
            if (error.code === 3 && !retried) {
                retried = true;
                request(20000);
                return;
            }
            done();
            const currentT = translations[state.lang];
            if (error.code === 1) {
                status.innerText = currentT.map_status_denied || "위치 권한이 거부되었어요. 전체 지도에서 검색해 주세요.";
            } else if (error.code === 3) {
                status.innerText = currentT.map_status_timeout || "위치 확인 시간이 초과됐어요. 다시 시도해 주세요.";
            } else {
                status.innerText = currentT.map_status_unavailable || "현재 위치를 확인할 수 없어요. 잠시 후 다시 시도해 주세요.";
            }
        },
        // timeout이 없으면 권한 대화상자를 무시했을 때 버튼이 영영 '조회 중'으로 남는다
        { timeout, maximumAge: 60000 }
    );
    request(10000);
}

let _clinicRequestId = 0, _clinicController = null;
const CLINIC_SEARCH_TIMEOUT_MS = 45000;

async function fetchClinics(lat, lng) {
    const requestId = ++_clinicRequestId;
    if (_clinicController) _clinicController.abort();
    const controller = new AbortController();
    _clinicController = controller;
    let deadline;
    const status = document.getElementById('map-status');
    const t = translations[state.lang];
    status.innerText = t.map_searching || "주변 안과를 찾는 중...";
    _lastClinicSearch = null;
    // Once a new location is requested, old pins/list entries are no longer current.
    if (_clinicLayer) _clinicLayer.clearLayers();
    const list = document.getElementById('clinic-list');
    if (list) list.innerHTML = '';
    try {
        // 우리 백엔드가 카카오 로컬 API로 검색 (키 없으면 빈 목록 → 폴백)
        const request = (async () => {
            const res = await fetch(`/api/nearby-clinics?lat=${lat}&lng=${lng}`, {signal: controller.signal});
            // Failed HTTP responses must not look like an empty clinic search.
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        })();
        // Bound body reading as well as connection establishment.
        const data = await Promise.race([request, new Promise((_, reject) => {
            deadline = setTimeout(() => {
                controller.abort();
                reject(new Error('clinic search timeout'));
            }, CLINIC_SEARCH_TIMEOUT_MS);
        })]);
        if (requestId !== _clinicRequestId) return;
        let items = (data.clinics || []).map(c => ({
            name: c.name, type: c.type || 'eye_clinic', lat: c.lat, lng: c.lng,
            dist: c.dist || haversine(lat, lng, c.lat, c.lng),
            address: c.address || '', phone: c.phone || ''
        }));
        items.sort((a, b) => Number(b.type === 'eye_clinic') - Number(a.type === 'eye_clinic') || a.dist - b.dist);
        _lastClinicSearch = {items, lat, lng};
        refreshMapResults();
    } catch (e) {
        if (requestId !== _clinicRequestId) return;
        status.innerText = translations[state.lang].map_search_err || "안과 검색에 실패했어요. 전체 지도에서 검색해 주세요.";
        renderFallbackLinks(lat, lng);
    } finally {
        clearTimeout(deadline);
        if (requestId === _clinicRequestId) _clinicController = null;
    }
}

function refreshMapResults() {
    if (!_lastClinicSearch) return;
    const {items, lat, lng} = _lastClinicSearch;
    const include = !!document.getElementById('clinic-include-services')?.checked;
    const visible = include ? items : items.filter(c => c.type === 'eye_clinic');
    renderClinics(visible, lat, lng);
    const t = translations[state.lang];
    document.getElementById('map-status').innerText = visible.length
        ? (include ? t.map_found_services : t.map_found).replace('{n}', visible.length) : t.map_none;
}

function renderClinics(items, lat, lng) {
    const map = ensureMap();
    const t = translations[state.lang], ko = state.lang === 'ko';
    if (_clinicLayer) _clinicLayer.clearLayers();
    const box = document.getElementById('clinic-list');
    box.innerHTML = '';
    if (!items.length) { renderFallbackLinks(lat, lng); return; }

    items.forEach(c => {
        if (map && _clinicLayer) L.marker([c.lat, c.lng]).addTo(_clinicLayer)
            .bindPopup(`<b>${escapeHTML(c.name)}</b><br>${fmtDist(c.dist)}`);
        const dir = ko
            ? `https://map.kakao.com/link/to/${encodeURIComponent(c.name)},${c.lat},${c.lng}`
            : `https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lng}`;

        const row = document.createElement('div');
        row.className = 'clinic-item';

        const ico = document.createElement('span');
        ico.className = 'ci-ico';
        ico.setAttribute('aria-hidden', 'true');
        ico.innerHTML = CLINIC_ICON;   // 고정 상수 (앱 전체 아이콘 규칙과 동일한 선형 SVG)

        // 병원 이름 자체를 버튼으로 — 예전엔 행 전체가 onclick이라 키보드로는 지도를
        // 이동시킬 수 없었고, 행을 버튼으로 감싸면 안의 '길찾기' 링크와 중첩돼버린다.
        const info = document.createElement('button');
        info.type = 'button';
        info.className = 'ci-info';
        const name = document.createElement('span');
        name.className = 'ci-name';
        name.textContent = c.name;
        const desc = document.createElement('span');
        desc.className = 'ci-desc';
        const typeLabel = c.type === 'optician' ? t.clinic_optician
            : c.type === 'optometrist' ? t.clinic_optometrist : t.clinic_eye;
        desc.textContent = `${typeLabel}${c.address ? ' · ' + c.address : ''}`;
        info.appendChild(name);
        info.appendChild(desc);
        info.onclick = () => { if (map) { map.setView([c.lat, c.lng], 17); map.closePopup(); } };

        const dist = document.createElement('span');
        dist.className = 'ci-dist';
        dist.textContent = fmtDist(c.dist);

        const link = document.createElement('a');
        link.href = dir;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = t.map_directions || (ko ? '길찾기' : 'Directions');

        row.append(ico, info, dist, link);
        box.appendChild(row);
    });

    // 내 위치 + 모든 안과가 한 화면에 보이도록 줌 맞춤
    const layers = _clinicLayer ? _clinicLayer.getLayers().slice() : [];
    if (_userMarker) layers.push(_userMarker);
    try { if (map && layers.length) map.fitBounds(L.featureGroup(layers).getBounds().pad(0.2)); } catch (e) {}
}

// Overpass 실패/무결과 시 외부 검색 링크로 폴백
function renderFallbackLinks(lat, lng) {
    const box = document.getElementById('clinic-list');
    const ko = state.lang === 'ko';
    const kakao = `https://map.kakao.com/?q=${encodeURIComponent('안과')}`;
    const google = `https://www.google.com/maps/search/eye+clinic/@${lat},${lng},15z`;
    const label = ko ? '바로가기' : 'Open';
    box.innerHTML =
        `<div class="clinic-item"><span class="ci-ico" aria-hidden="true">${CLINIC_ICON}</span>`
        + `<div style="flex:1;min-width:0"><p class="ci-name">${ko ? '카카오맵 안과 검색' : 'Kakao Map – Eye Clinics'}</p>`
        + `<p class="ci-desc">${ko ? '주변 안과를 지도에서 확인' : 'Nearby eye clinics on the map'}</p></div>`
        + `<a href="${kakao}" target="_blank" rel="noopener">${label}</a></div>`
        + `<div class="clinic-item"><span class="ci-ico" aria-hidden="true">${GLOBE_ICON}</span>`
        + `<div style="flex:1;min-width:0"><p class="ci-name">${ko ? '구글맵 안과 검색' : 'Google Maps – Eye Clinics'}</p>`
        + `<p class="ci-desc">${ko ? '내 좌표 기준 안과 탐색' : 'Search clinics around you'}</p></div>`
        + `<a href="${google}" target="_blank" rel="noopener">${label}</a></div>`;
}

if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('offline', () => { if (_map) showMapOffline(); });
    window.addEventListener('online', () => { if (_map && document.getElementById('map-recovery')) retryMapTiles(); });
}
