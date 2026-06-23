// ==========================================
// app-map.js — 병원 찾기 (위치 기반 임베디드 지도)
// Leaflet 지도 + Overpass(OSM) 실제 안과 검색
// app-core.js가 먼저 로드되어야 함 (state, escapeHTML 사용)
// ==========================================
const DEFAULT_CENTER = [37.5012, 127.0396];   // 위치 거부 시 기본(강남)
let _map = null, _userMarker = null, _clinicLayer = null;

function ensureMap() {
    if (_map) { _map.invalidateSize(); return _map; }
    _map = L.map('leaflet-map', { zoomControl: true }).setView(DEFAULT_CENTER, 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '© OpenStreetMap'
    }).addTo(_map);
    _clinicLayer = L.layerGroup().addTo(_map);
    setTimeout(() => _map.invalidateSize(), 200);   // 숨겨진 탭 init 보정
    return _map;
}

function haversine(aLat, aLng, bLat, bLng) {
    const R = 6371000, rad = x => x * Math.PI / 180;
    const dLat = rad(bLat - aLat), dLng = rad(bLng - aLng);
    const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(aLat)) * Math.cos(rad(bLat)) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(s));   // meters
}
const fmtDist = m => m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(1)}km`;

function findNearbyClinics() {
    const status = document.getElementById('map-status');
    const map = ensureMap();
    if (!navigator.geolocation) {
        status.innerText = translations[state.lang].map_status_unsupported || "이 브라우저는 위치 기능을 지원하지 않아요.";
        return;
    }
    status.innerText = translations[state.lang].map_status_loading || "위치를 확인하는 중...";
    navigator.geolocation.getCurrentPosition(
        pos => {
            const lat = pos.coords.latitude, lng = pos.coords.longitude;
            map.setView([lat, lng], 15);
            if (_userMarker) _userMarker.remove();
            _userMarker = L.marker([lat, lng]).addTo(map)
                .bindPopup(translations[state.lang].map_you || "📍 내 위치");
            fetchClinics(lat, lng);
        },
        () => { status.innerText = translations[state.lang].map_status_denied || "위치 권한이 거부되었어요. 전체 지도에서 검색해 주세요."; }
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
        row.innerHTML =
            `<span class="ci-ico">🏥</span>`
            + `<div style="flex:1;min-width:0">`
            + `<p class="ci-name" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHTML(c.name)}</p>`
            + `<p class="ci-desc" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHTML(c.address || (ko ? '안과 · 탭하면 지도에서 보기' : 'Eye clinic · tap to view on map'))}</p></div>`
            + `<span class="ci-dist">${fmtDist(c.dist)}</span>`
            + `<a href="${dir}" target="_blank" rel="noopener">${t.map_directions || (ko ? '길찾기' : 'Directions')}</a>`;
        row.querySelector('a').onclick = e => e.stopPropagation();   // 링크는 새 탭만
        row.onclick = () => { map.setView([c.lat, c.lng], 17); map.closePopup(); };
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
        `<div class="clinic-item"><span class="ci-ico">🏥</span>`
        + `<div style="flex:1;min-width:0"><p class="ci-name">${ko ? '카카오맵 안과 검색' : 'Kakao Map – Eye Clinics'}</p>`
        + `<p class="ci-desc">${ko ? '주변 안과를 지도에서 확인' : 'Nearby eye clinics on the map'}</p></div>`
        + `<a href="${kakao}" target="_blank" rel="noopener">${label}</a></div>`
        + `<div class="clinic-item"><span class="ci-ico">🌎</span>`
        + `<div style="flex:1;min-width:0"><p class="ci-name">${ko ? '구글맵 안과 검색' : 'Google Maps – Eye Clinics'}</p>`
        + `<p class="ci-desc">${ko ? '내 좌표 기준 안과 탐색' : 'Search clinics around you'}</p></div>`
        + `<a href="${google}" target="_blank" rel="noopener">${label}</a></div>`;
}
