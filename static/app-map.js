// ==========================================
// app-map.js — 병원 찾기 (위치 기반 임베디드 지도)
// Leaflet 지도 + Overpass(OSM) 실제 안과 검색
// app-core.js가 먼저 로드되어야 함 (state, escapeHTML 사용)
// ==========================================
const DEFAULT_CENTER = [37.5012, 127.0396];   // 위치 거부 시 기본(강남)
// 목록 아이콘 — 기기마다 모양이 달라지는 이모지 대신 앱 전체와 같은 선형 SVG
const CLINIC_ICON = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 21V8.6l8-5 8 5V21"/><path d="M9.5 21v-5h5v5"/><path d="M12 7.4v3.4M10.3 9.1h3.4"/></svg>';
const GLOBE_ICON = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/><path d="M12 3.5c2.2 2.4 3.4 5.4 3.4 8.5S14.2 18.1 12 20.5c-2.2-2.4-3.4-5.4-3.4-8.5S9.8 5.9 12 3.5Z"/></svg>';
let _map = null, _userMarker = null, _clinicLayer = null;

function ensureMap() {
    if (_map) { _map.invalidateSize(); return _map; }

    // 마커 아이콘 경로를 명시 — Leaflet은 기본적으로 스크립트 URL에서 images/ 위치를
    // 추론하는데, 로컬 번들 경로에서는 추론이 빗나가 마커가 안 보일 수 있다.
    if (L.Icon && L.Icon.Default) L.Icon.Default.imagePath = '/static/vendor/leaflet/images/';

    _map = L.map('leaflet-map', { zoomControl: true }).setView(DEFAULT_CENTER, 14);
    const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '© OpenStreetMap'
    });
    // 지도 '타일'은 성격상 로컬 번들에 넣을 수 없다(전 세계 이미지).
    // 오프라인이면 빈 회색 화면이 남는데, 그걸 방치하면 앱이 고장난 것처럼 보인다.
    // → 타일 로드 실패를 감지해 안내로 대체한다. 나머지 기능(검사·문진·리포트·PDF)은 영향 없음.
    let tileFailed = false;
    tiles.on('tileerror', () => {
        if (tileFailed) return;
        tileFailed = true;
        showMapOffline();
    });
    tiles.addTo(_map);
    _clinicLayer = L.layerGroup().addTo(_map);
    setTimeout(() => _map.invalidateSize(), 200);   // 숨겨진 탭 init 보정
    return _map;
}

const MAP_OFFLINE_ICON = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m3 6.5 6-2.5 6 2.5 6-2.5v13l-6 2.5-6-2.5-6 2.5v-13Z"/><path d="M9 4v13M15 6.5v13"/></svg>';

/** 타일을 못 받아오는 환경(오프라인·발표장 네트워크)에서 지도를 안내로 대체. */
function showMapOffline() {
    const box = document.getElementById('leaflet-map');
    const t = translations[state.lang];
    if (!box) return;
    box.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'map-offline';
    const icon = document.createElement('div');
    icon.className = 'map-offline-ico';
    icon.setAttribute('aria-hidden', 'true');
    icon.innerHTML = MAP_OFFLINE_ICON;   // 고정 상수 (앱 전체 아이콘 규칙과 동일한 선형 SVG)
    const msg = document.createElement('p');
    msg.textContent = t.map_offline || '지도를 불러올 수 없습니다. 인터넷 연결을 확인해주세요. 나머지 검사 기능은 정상 동작합니다.';
    wrap.appendChild(icon); wrap.appendChild(msg);
    box.appendChild(wrap);
    const status = document.getElementById('map-status');
    if (status) status.innerText = t.map_offline_short || '지도 오프라인';
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
    if (!navigator.geolocation) {
        status.innerText = t.map_status_unsupported || "이 브라우저는 위치 기능을 지원하지 않아요.";
        return;
    }
    status.innerText = t.map_status_loading || "위치를 확인하는 중...";

    _locating = true;
    const restoreBtn = setButtonBusy(document.getElementById('map-locate-btn'), t.map_status_loading || "");
    const done = () => { _locating = false; restoreBtn(); };

    navigator.geolocation.getCurrentPosition(
        pos => {
            done();
            const lat = pos.coords.latitude, lng = pos.coords.longitude;
            map.setView([lat, lng], 15);
            if (_userMarker) _userMarker.remove();
            _userMarker = L.marker([lat, lng]).addTo(map)
                .bindPopup(t.map_you || "내 위치");
            fetchClinics(lat, lng);
        },
        error => {
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
        { timeout: 10000, maximumAge: 60000 }
    );
}

async function fetchClinics(lat, lng) {
    const status = document.getElementById('map-status');
    const t = translations[state.lang];
    status.innerText = t.map_searching || "주변 안과를 찾는 중...";
    try {
        // 우리 백엔드가 카카오 로컬 API로 검색 (키 없으면 빈 목록 → 폴백)
        const res = await fetch(`/api/nearby-clinics?lat=${lat}&lng=${lng}`);
        const data = await res.json();
        let items = (data.clinics || []).map(c => ({
            name: c.name, lat: c.lat, lng: c.lng,
            dist: c.dist || haversine(lat, lng, c.lat, c.lng),
            address: c.address || '', phone: c.phone || ''
        }));
        items.sort((a, b) => a.dist - b.dist);
        renderClinics(items, lat, lng);
        status.innerText = items.length
            ? (t.map_found || "주변 안과 {n}곳을 찾았어요.").replace('{n}', items.length)
            : (t.map_none || "주변에서 안과를 찾지 못했어요. 전체 지도에서 검색해 주세요.");
    } catch (e) {
        status.innerText = t.map_search_err || "안과 검색에 실패했어요. 전체 지도에서 검색해 주세요.";
        renderFallbackLinks(lat, lng);
    }
}

function renderClinics(items, lat, lng) {
    const map = ensureMap();
    const t = translations[state.lang], ko = state.lang === 'ko';
    _clinicLayer.clearLayers();
    const box = document.getElementById('clinic-list');
    box.innerHTML = '';
    if (!items.length) { renderFallbackLinks(lat, lng); return; }

    items.forEach(c => {
        L.marker([c.lat, c.lng]).addTo(_clinicLayer)
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
        desc.textContent = c.address || (ko ? '안과 · 눌러서 지도에서 보기' : 'Eye clinic · tap to view on map');
        info.appendChild(name);
        info.appendChild(desc);
        info.onclick = () => { map.setView([c.lat, c.lng], 17); map.closePopup(); };

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
    const layers = _clinicLayer.getLayers().slice();
    if (_userMarker) layers.push(_userMarker);
    try { map.fitBounds(L.featureGroup(layers).getBounds().pad(0.2)); } catch (e) {}
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
