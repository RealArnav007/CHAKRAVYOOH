let authToken = localStorage.getItem('beacon_token');

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    setInterval(fetchStats, 5000);
});

async function fetchStats() {
    try {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const res = await fetch('/api/v1/admin/stats', { headers });
        if (!res.ok) return;

        const data = await res.json();
        document.getElementById('valTotal').innerText = data.total_incidents;
        document.getElementById('valActive').innerText = data.active_emergencies;
        document.getElementById('valGateways').innerText = data.active_gateways;
        document.getElementById('valClusters').innerText = data.mass_casualty_clusters;
    } catch (e) {}
}

async function provisionUser() {
    const email = document.getElementById('provEmail').value;
    const name = document.getElementById('provName').value;
    const role = document.getElementById('provRole').value;
    const region_id = document.getElementById('provRegion').value || null;

    if (!email || !name) return alert("Email and Name required.");

    try {
        const headers = { 
            'Content-Type': 'application/json',
            ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
        };

        const res = await fetch('/api/v1/admin/users/provision', {
            method: 'POST',
            headers,
            body: JSON.stringify({ email, name, role, region_id })
        });
        
        if (!res.ok) throw new Error(await res.text());
        alert("User identity provisioned successfully!");
    } catch (e) {
        alert("Provisioning failed: " + e.message);
    }
}
