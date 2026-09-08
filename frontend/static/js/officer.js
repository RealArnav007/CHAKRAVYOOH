let map;
let markers = {};
let lastPollTime = 0;
let authToken = localStorage.getItem('beacon_token');

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    startPolling();
});

function initMap() {
    map = L.map('map').setView([28.6139, 77.2090], 12);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors © CARTO'
    }).addTo(map);
}

function requestLogin() {
    if (typeof window.openAuthModal === 'function') {
        window.openAuthModal();
    }
}

function startPolling() {
    pollIncidents();
    setInterval(pollIncidents, 3000);
}

async function pollIncidents() {
    try {
        const token = localStorage.getItem('beacon_token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        const res = await fetch(`/api/v1/officer/incidents?since_ms=0`, { headers });
        if (!res.ok) return;

        const data = await res.json();
        renderQueue(data.incidents || []);
    } catch (e) {}
}

function renderQueue(incidents) {
    const list = document.getElementById('incidentList');
    document.getElementById('queueCount').innerText = `${incidents.length} Active`;
    list.innerHTML = '';

    incidents.forEach(inc => {
        const card = document.createElement('div');
        card.className = `incident-card priority-${inc.priority}`;
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span class="severity-badge severity-${inc.severity}" style="padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; background: rgba(255,59,48,0.15); color: var(--color-red);">${inc.severity} (P${inc.priority})</span>
                <span style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">${new Date(inc.received_at).toLocaleTimeString()}</span>
            </div>
            <div style="font-weight: 600; font-size: 0.9rem; color: var(--text-primary); margin-bottom: 0.25rem;">${inc.ai_summary || inc.payload}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">Status: <strong style="color: var(--color-cyan);">${inc.status}</strong></div>
            <div style="display: flex; gap: 0.5rem;">
                <button class="btn-primary" style="padding: 4px 10px; font-size: 0.78rem;" onclick="updateStatus('${inc.sos_id}', 'RESPONDING')">Respond</button>
                <button class="btn-primary" style="background: var(--color-green); color: var(--bg-gradient-bottom); padding: 4px 10px; font-size: 0.78rem;" onclick="updateStatus('${inc.sos_id}', 'RESOLVED')">Resolve</button>
            </div>
        `;
        list.appendChild(card);

        // Update Map Marker
        if (!markers[inc.sos_id]) {
            const marker = L.circleMarker([inc.lat, inc.lon], {
                color: inc.severity === 'CRITICAL' ? '#ff3b30' : '#f59e0b',
                radius: 10,
                fillOpacity: 0.8
            }).addTo(map);
            marker.bindPopup(`<b>${inc.severity}</b><br>${inc.ai_summary || inc.payload}`);
            markers[inc.sos_id] = marker;

            document.getElementById('alertSound').play().catch(e => {});
        }
    });
}

async function updateStatus(sos_id, new_status) {
    try {
        const token = localStorage.getItem('beacon_token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        await fetch(`/api/v1/officer/incidents/${sos_id}/status?new_status=${new_status}`, {
            method: 'POST',
            headers
        });
        pollIncidents();
    } catch (e) {
        alert("Action failed: " + e.message);
    }
}
