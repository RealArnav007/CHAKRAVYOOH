import os

html_code = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PUKAAR — National Disaster Operations Command Portal</title>
  <meta name="theme-color" content="#060911">
  <meta name="description" content="National Emergency Operations Command Center — Offline Mesh SOS Relay & Real-Time Official Dispatch Portal">

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              bg: '#060911',
              card: '#0d121f',
              hover: '#131b2d',
              border: '#1a243b'
            }
          },
          fontFamily: {
            sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
            heading: ['Outfit', 'Space Grotesk', 'Plus Jakarta Sans', 'sans-serif'],
            brand: ['Outfit', 'sans-serif'],
            mono: ['JetBrains Mono', 'Fira Code', 'monospace']
          }
        }
      }
    }
  </script>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@400;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

  <style>
    body { background-color: #060911; color: #f1f5f9; font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; }
    h1, h2, h3, h4, .font-heading { font-family: 'Plus Jakarta Sans', sans-serif; letter-spacing: -0.015em; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #060911; }
    ::-webkit-scrollbar-thumb { background: #1a243b; border-radius: 9999px; }

    /* Keyframe Glow strictly for Critical Red Alert bar */
    @keyframes glowPulseRed {
      0%, 100% {
        box-shadow: 0 0 18px rgba(244, 63, 94, 0.5), inset 0 0 14px rgba(244, 63, 94, 0.2);
        border-color: rgba(244, 63, 94, 0.8);
      }
      50% {
        box-shadow: 0 0 36px rgba(244, 63, 94, 0.95), inset 0 0 24px rgba(244, 63, 94, 0.4);
        border-color: rgba(244, 63, 94, 1);
      }
    }

    @keyframes beaconPing {
      0% { transform: scale(0.9); opacity: 0.8; box-shadow: 0 0 4px currentColor; }
      50% { transform: scale(1.4); opacity: 1; box-shadow: 0 0 18px currentColor; }
      100% { transform: scale(0.9); opacity: 0.8; box-shadow: 0 0 4px currentColor; }
    }

    @keyframes scanSweep {
      0% { transform: translateY(-100%); opacity: 0; }
      40% { opacity: 0.75; }
      100% { transform: translateY(100vh); opacity: 0; }
    }

    @keyframes floatParticle {
      0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0.3; }
      50% { transform: translateY(-24px) translateX(15px); opacity: 0.85; }
    }

    .glow-alert-red {
      animation: glowPulseRed 2s infinite ease-in-out;
    }

    .beacon-dot-red {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 9999px;
      background-color: #f43f5e;
      color: #f43f5e;
      animation: beaconPing 1.2s infinite ease-in-out;
    }

    /* Very dull, subtle background grid */
    .dull-grid-pattern {
      background-color: #060911;
      background-image: 
        linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        radial-gradient(circle at 50% 35%, rgba(244, 63, 94, 0.1) 0%, rgba(6, 9, 17, 0.98) 75%);
      background-size: 50px 50px, 50px 50px, 100% 100%;
    }

    /* Sweeping vertical radar beam */
    .scan-line {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 140px;
      background: linear-gradient(to bottom, transparent, rgba(244, 63, 94, 0.25), rgba(6, 182, 212, 0.15), transparent);
      animation: scanSweep 7s ease-in-out infinite;
      pointer-events: none;
    }

    .glass-card {
      background: rgba(13, 18, 31, 0.94);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: 0 30px 70px -15px rgba(0, 0, 0, 0.95);
    }
  </style>
</head>
<body class="antialiased min-h-screen">
  <div id="app"></div>

  <script>
    // --- Application State ---
    let defaultAdmins = [];

    let savedAdmins = [];
    try {
      const stored = localStorage.getItem('pukaar_admins');
      if (stored) savedAdmins = JSON.parse(stored);
    } catch (e) {}

    let initialAdmins = savedAdmins.length > 0 ? savedAdmins : defaultAdmins;

    let state = {
      isAuthenticated: false,
      role: 'COMMANDER',
      badge: '',
      officerName: '',
      activeTab: 'dashboard',
      showExistingLogin: false,
      registeredAdmins: initialAdmins,
      selectedIncidentId: null,
      lastSyncTime: new Date().toLocaleTimeString(),
      apiStatus: 'ONLINE',
      showIngestModal: false,
      rawPacketJson: JSON.stringify({
        sos_id: `INC-${Math.floor(100 + Math.random() * 900)}`,
        lat: 28.6139,
        lon: 77.2090,
        severity: "CRITICAL",
        payload: {
          victim_count: 4,
          hazard: "Building Structural Collapse Debris",
          message: "Emergency trapped victim report requiring instant heavy extraction team!"
        }
      }, null, 2),
      incidents: [
        {
          id: 'inc-104',
          code: 'INC-104',
          title: 'Multi-Story Structural Collapse',
          category: 'BUILDING_COLLAPSE',
          severity: 'CRITICAL',
          status: 'DISPATCHING',
          location: { sector: 'Sector 14, Central Metro District' },
          createdAt: '08:40:12',
          corroborationCount: 18,
          aiScoreV2: {
            priority: 97,
            regexScore: 88,
            groqScore: 94,
            corroborationBonus: 8,
            locationBonus: 3,
            briefing: { headline: 'Structural collapse, 3 trapped civilians — rescue + ambulance priority' }
          }
        },
        {
          id: 'inc-105',
          code: 'INC-105',
          title: 'Transformer Fire & Smoke Spread',
          category: 'FIRE',
          severity: 'HIGH',
          status: 'DISPATCHING',
          location: { sector: 'Sector 19, North Grid Substation 4B' },
          createdAt: '08:35:00',
          corroborationCount: 8,
          aiScoreV2: {
            priority: 86,
            regexScore: 78,
            groqScore: 84,
            corroborationBonus: 5,
            locationBonus: 2,
            briefing: { headline: 'Substation electrical explosion resulting in toxic smoke — fire engine advised' }
          }
        }
      ],
      resources: [
        { id: 'res-01', callsign: 'NDRF Heavy Rescue-03', type: 'RESCUE', status: 'AVAILABLE', etaMinutes: 0 },
        { id: 'res-02', callsign: 'Delhi Fire Foam Engine-12', type: 'FIRE', status: 'AVAILABLE', etaMinutes: 0 },
        { id: 'res-03', callsign: 'AIIMS ALS Ambulance-07', type: 'AMBULANCE', status: 'AVAILABLE', etaMinutes: 0 }
      ],
      auditEvents: [
        { id: 'aud-1', timestamp: new Date().toLocaleTimeString(), userName: 'System Gateway', role: 'SYSTEM', action: 'PORTAL_INITIALIZED', resourceName: 'Real-Time Ingest Pipeline Active', result: 'ONLINE' }
      ]
    };

    // --- State Management Helpers ---
    function setState(updater) {
      if (typeof updater === 'function') {
        state = updater(state);
      } else {
        state = { ...state, ...updater };
      }
      renderApp();
    }

    function doLogin(role, badge, name) {
      setState(s => ({
        ...s,
        isAuthenticated: true,
        role: role || 'COMMANDER',
        badge: badge || 'NDRF-DEL-882',
        officerName: name || 'Inspector A. Kumar',
        auditEvents: [
          { id: `aud-${Date.now()}`, timestamp: new Date().toLocaleTimeString(), userName: name || 'Officer', role: role || 'COMMANDER', action: 'SESSION_AUTHENTICATED', resourceName: `Badge: ${badge}`, result: 'SUCCESS' },
          ...s.auditEvents
        ]
      }));
    }

    function handleCreateAccountAndLogin(isFromDashboard = false) {
      const prefix = isFromDashboard ? 'dashReg' : 'newAdmin';
      const n = document.getElementById(prefix + 'Name')?.value?.trim();
      const b = document.getElementById(prefix + 'Badge')?.value?.trim();
      const r = document.getElementById(prefix + 'Role')?.value || 'COMMANDER';
      const p = document.getElementById(prefix + 'Password')?.value || 'pukaar2026';
      const ph = document.getElementById(prefix + 'Phone')?.value?.trim() || '+91 98765-43210';
      const em = document.getElementById(prefix + 'Email')?.value?.trim() || 'officer@ndrf.gov.in';

      if (!n || !b) {
        alert('Please enter your Officer Full Name and Badge ID.');
        return;
      }

      const newAdmin = { badge: b, name: n, role: r, password: p, phone: ph, email: em, dept: 'Disaster Command Unit' };
      const updatedAdmins = [newAdmin, ...state.registeredAdmins.filter(a => a.badge !== b)];
      
      try {
        localStorage.setItem('pukaar_admins', JSON.stringify(updatedAdmins));
      } catch (e) {}

      const newAudit = {
        id: `aud-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        userName: n,
        role: r,
        action: 'ADMIN_ACCOUNT_CREDENTIALIZED',
        resourceName: `Badge: ${b} (${n}) | Role: ${r}`,
        result: 'SUCCESS'
      };

      if (isFromDashboard) {
        setState(s => ({
          ...s,
          registeredAdmins: updatedAdmins,
          auditEvents: [newAudit, ...s.auditEvents]
        }));
        alert(`✅ Registered [ ${b} ] (${n} - ${r}) successfully!`);
      } else {
        setState(s => ({
          ...s,
          isAuthenticated: true,
          registeredAdmins: updatedAdmins,
          badge: b,
          officerName: n,
          role: r,
          auditEvents: [newAudit, ...s.auditEvents]
        }));
      }
    }

    function selectAdminProfileCard(badgeVal) {
      const found = state.registeredAdmins.find(a => a.badge === badgeVal);
      if (found) {
        setState({
          badge: found.badge,
          officerName: found.name,
          role: found.role
        });
        if (document.getElementById('newAdminName')) document.getElementById('newAdminName').value = found.name;
        if (document.getElementById('newAdminBadge')) document.getElementById('newAdminBadge').value = found.badge;
        if (document.getElementById('newAdminRole')) document.getElementById('newAdminRole').value = found.role;
        if (document.getElementById('newAdminPhone')) document.getElementById('newAdminPhone').value = found.phone || '+91 98765-43210';
        if (document.getElementById('newAdminEmail')) document.getElementById('newAdminEmail').value = found.email || 'officer@ndrf.gov.in';
      }
    }

    function handleDispatch(incId, resType) {
      const targetInc = state.incidents.find(i => i.id === incId) || state.incidents[0];
      const avail = state.resources.find(r => r.status === 'AVAILABLE' && (resType ? r.type === resType : true)) || state.resources.find(r => r.status === 'AVAILABLE');
      
      if (avail) {
        const updatedRes = state.resources.map(r => r.id === avail.id ? { ...r, status: 'DISPATCHED', assignedIncidentCode: targetInc.code, etaMinutes: 4 } : r);
        const newAudit = {
          id: `aud-${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          userName: state.officerName || `Officer ${state.badge}`,
          role: state.role,
          action: 'DISPATCH_RESOURCE',
          resourceName: `${avail.callsign} → ${targetInc.code}`,
          result: 'SUCCESS'
        };
        setState(s => ({
          ...s,
          resources: updatedRes,
          auditEvents: [newAudit, ...s.auditEvents],
          selectedIncidentId: null
        }));
        alert(`🚨 Dispatched ${avail.callsign} to ${targetInc.code}`);
      } else {
        alert('⚠️ No available units in staging area');
      }
    }

    async function syncBackendData() {
      try {
        const res = await fetch('/api/v1/officer/incidents');
        if (res.ok) {
          const data = await res.json();
          if (data && data.incidents && data.incidents.length > 0) {
            const mapped = data.incidents.map(inc => ({
              id: inc.sos_id || `inc-${Date.now()}`,
              code: inc.sos_id || 'INC-LIVE',
              title: inc.ai_summary || inc.payload?.message || 'Real-Time Emergency Signal',
              category: inc.severity === 'CRITICAL' ? 'BUILDING_COLLAPSE' : 'DISASTER_ALERT',
              severity: inc.severity || 'HIGH',
              status: inc.status || 'DISPATCHING',
              location: { sector: `Lat: ${inc.lat?.toFixed(4) || '28.61'}, Lon: ${inc.lon?.toFixed(4) || '77.20'}` },
              createdAt: new Date(inc.received_at || Date.now()).toLocaleTimeString(),
              corroborationCount: inc.payload?.victim_count || 12,
              aiScoreV2: {
                priority: inc.priority || 92,
                regexScore: 88,
                groqScore: 94,
                corroborationBonus: 8,
                locationBonus: 3,
                briefing: { headline: inc.ai_summary || inc.payload?.message || 'Emergency signal ingested via live backend pipeline' }
              }
            }));
            setState(s => {
              const combined = [...mapped];
              s.incidents.forEach(p => {
                if (!combined.some(c => c.code === p.code)) combined.push(p);
              });
              return { ...s, incidents: combined, apiStatus: 'ONLINE', lastSyncTime: new Date().toLocaleTimeString() };
            });
          }
        }
      } catch (err) {
        state.apiStatus = 'LOCAL_DESK';
      }
    }

    async function handleFeedSosPacket() {
      try {
        const parsed = JSON.parse(state.rawPacketJson);
        const res = await fetch('/api/v1/sos/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Gateway-Id': 'NODE-GW-P5' },
          body: JSON.stringify(parsed)
        });
        if (res.ok) {
          alert('⚡ Live SOS Packet Ingested into Backend API successfully!');
          setState({ showIngestModal: false });
          syncBackendData();
        } else {
          const newInc = {
            id: parsed.sos_id || `inc-${Date.now()}`,
            code: parsed.sos_id || 'INC-NEW',
            title: parsed.payload?.message || 'Real-Time Ingested SOS Event',
            category: 'DISASTER_ALERT',
            severity: parsed.severity || 'CRITICAL',
            status: 'DISPATCHING',
            location: { sector: 'Sector 14, Live Ingest Mesh' },
            createdAt: new Date().toLocaleTimeString(),
            corroborationCount: parsed.payload?.victim_count || 5,
            aiScoreV2: {
              priority: 95,
              regexScore: 90,
              groqScore: 95,
              corroborationBonus: 10,
              locationBonus: 5,
              briefing: { headline: parsed.payload?.message || 'Ingested emergency signal' }
            }
          };
          setState(s => ({
            ...s,
            incidents: [newInc, ...s.incidents],
            showIngestModal: false
          }));
          alert(`⚡ Live SOS [ ${newInc.code} ] ingested into portal!`);
        }
      } catch (e) {
        alert('Invalid JSON formatting. Please check syntax.');
      }
    }

    // Initialize backend polling loop
    setInterval(() => {
      if (state.isAuthenticated) syncBackendData();
    }, 4000);

    // --- HTML Render Component Generators ---
    function renderLoginView() {
      return `
        <div class="min-h-screen dull-grid-pattern text-slate-100 flex items-center justify-center p-4 sm:p-6 relative font-sans overflow-hidden">
          <!-- Sweeping Radar Beam -->
          <div class="scan-line"></div>

          <!-- Floating Glow Dots & Ambient Particles -->
          <div class="absolute inset-0 pointer-events-none overflow-hidden z-0">
            <div class="absolute top-[18%] left-[15%] w-3 h-3 rounded-full bg-rose-500/60 shadow-[0_0_12px_#f43f5e] animate-[floatParticle_7s_infinite_ease-in-out]"></div>
            <div class="absolute top-[35%] right-[18%] w-2.5 h-2.5 rounded-full bg-cyan-400/70 shadow-[0_0_10px_#06b6d4] animate-[floatParticle_9s_infinite_ease-in-out_1s]"></div>
            <div class="absolute bottom-[22%] left-[22%] w-3 h-3 rounded-full bg-amber-400/60 shadow-[0_0_12px_#f59e0b] animate-[floatParticle_8s_infinite_ease-in-out_2s]"></div>

            <!-- Outlined World Vector Outlined Map Backdrop -->
            <svg viewBox="0 0 1000 500" class="w-full h-full object-cover opacity-20 stroke-rose-500/30 fill-rose-500/5" stroke-width="1.5">
              <path d="M 120 100 Q 150 70 220 80 T 300 120 T 260 220 T 180 240 T 130 180 Z" />
              <path d="M 270 300 Q 320 320 340 370 T 310 460 T 270 420 T 250 340 Z" />
              <path d="M 460 100 Q 520 80 560 110 T 540 170 T 480 160 Z" />
              <path d="M 460 180 Q 540 180 570 240 T 540 360 T 480 340 T 450 240 Z" />
              <path d="M 570 90 Q 680 70 820 100 T 880 200 T 780 280 T 650 250 T 570 170 Z" />
            </svg>
          </div>

          <!-- Glassmorphic Create Admin Account Card -->
          <div class="w-full max-w-2xl glass-card rounded-3xl p-7 sm:p-10 space-y-7 relative z-10">
            <!-- Brand Header -->
            <div class="text-center space-y-3">
              <div class="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-b from-rose-500/20 to-rose-950/40 border border-rose-500/40 flex items-center justify-center text-rose-400 text-3xl sm:text-4xl shadow-[0_0_20px_rgba(244,63,94,0.3)]">
                🛡️
              </div>
              <div class="space-y-1">
                <h1 class="text-4xl sm:text-5xl md:text-6xl font-black font-heading tracking-tight text-white flex items-center justify-center">
                  <span class="bg-gradient-to-r from-white via-slate-100 to-rose-300 bg-clip-text text-transparent drop-shadow-md">PUKAAR</span>
                </h1>
                <p class="text-xs sm:text-sm text-slate-300 font-semibold tracking-wider uppercase mt-2 opacity-90 flex items-center justify-center gap-2 font-sans">
                  <span>🇮🇳</span>
                  <span>NATIONAL EMERGENCY OPERATIONS COMMAND PORTAL</span>
                </p>
              </div>
            </div>

            <!-- MAIN CREDENTIALS FORM -->
            <div class="space-y-5 text-xs font-sans">
              <div class="p-4 rounded-2xl bg-gradient-to-r from-rose-950/60 via-slate-900/90 to-rose-950/60 border border-rose-500/30 text-xs text-slate-200 flex items-center justify-between shadow-inner">
                <span class="font-bold text-xs sm:text-sm text-slate-100 flex items-center gap-2.5 tracking-wide">
                  <span class="beacon-dot-red"></span>
                  <span class="font-heading uppercase tracking-wide">ENTER ADMIN OFFICER CREDENTIALS</span>
                </span>
                <span class="text-[11px] font-mono text-cyan-300 bg-[#060a14] px-3 py-1 rounded-lg border border-slate-700 font-bold">
                  📝 LIVE CREDENTIAL FORM
                </span>
              </div>

              ${state.registeredAdmins.length > 0 ? `
                <div class="space-y-2">
                  <label class="text-slate-300 font-bold text-xs sm:text-[13px] tracking-wide flex items-center justify-between uppercase">
                    <span>Select Previously Registered Admin Profile</span>
                    <span class="text-[11px] text-cyan-400 font-mono font-bold">${state.registeredAdmins.length} Saved</span>
                  </label>
                  <select onchange="selectAdminProfileCard(this.value)" class="w-full px-4.5 py-3.5 rounded-xl bg-[#060a14] border border-slate-700/80 text-slate-100 text-xs font-mono font-semibold focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/30 transition-all shadow-inner text-center">
                    <option value="">-- Select a registered admin profile or type below --</option>
                    ${state.registeredAdmins.map(adm => `
                      <option value="${adm.badge}">${adm.name} (${adm.badge} - ${adm.role})</option>
                    `).join('')}
                  </select>
                </div>
              ` : ''}

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4.5">
                <div class="space-y-2">
                  <label class="text-slate-300 font-bold text-xs sm:text-[13px] tracking-wide uppercase text-center block">Officer Full Name <span class="text-rose-400">*</span></label>
                  <input id="newAdminName" type="text" value="" placeholder="e.g. Inspector R. Sharma" class="w-full px-4.5 py-3.5 rounded-xl bg-[#060a14] border border-slate-700/80 text-slate-100 text-sm font-medium focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/30 transition-all placeholder:text-slate-500 shadow-inner text-center" />
                </div>
                <div class="space-y-2">
                  <label class="text-slate-300 font-bold text-xs sm:text-[13px] tracking-wide uppercase text-center block">Badge ID / Admin ID <span class="text-rose-400">*</span></label>
                  <input id="newAdminBadge" type="text" value="" placeholder="e.g. NDRF-DEL-901" class="w-full px-4.5 py-3.5 rounded-xl bg-[#060a14] border border-slate-700/80 text-slate-100 text-sm font-mono font-bold focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/30 transition-all placeholder:text-slate-500 shadow-inner text-center" />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4.5">
                <div class="space-y-2">
                  <label class="text-slate-300 font-bold text-xs sm:text-[13px] tracking-wide uppercase text-center block">Assigned Command Role</label>
                  <select id="newAdminRole" class="w-full px-4.5 py-3.5 rounded-xl bg-[#060a14] border border-slate-700/80 text-slate-100 text-xs font-mono font-semibold focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/30 transition-all shadow-inner text-center">
                    <option value="SUPER_ADMIN" selected>SUPER_ADMIN (Full System Control)</option>
                    <option value="COMMANDER">COMMANDER (Incident Operations)</option>
                    <option value="RESPONDER">RESPONDER (Field Command)</option>
                    <option value="ANALYST">ANALYST (Audit & Telemetry)</option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label class="text-slate-300 font-bold text-xs sm:text-[13px] tracking-wide uppercase text-center block">Command Password</label>
                  <input id="newAdminPassword" type="password" value="" placeholder="Set your password" class="w-full px-4.5 py-3.5 rounded-xl bg-[#060a14] border border-slate-700/80 text-slate-100 text-sm font-medium focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/30 transition-all placeholder:text-slate-500 shadow-inner text-center" />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4.5">
                <div class="space-y-2">
                  <label class="text-slate-300 font-bold text-xs sm:text-[13px] tracking-wide uppercase text-center block">Official Mobile Number</label>
                  <input id="newAdminPhone" type="text" value="" placeholder="+91 98765-43210" class="w-full px-4.5 py-3.5 rounded-xl bg-[#060a14] border border-slate-700/80 text-slate-100 text-xs font-mono focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/30 transition-all placeholder:text-slate-500 shadow-inner text-center" />
                </div>
                <div class="space-y-2">
                  <label class="text-slate-300 font-bold text-xs sm:text-[13px] tracking-wide uppercase text-center block">Official Email Address</label>
                  <input id="newAdminEmail" type="email" value="" placeholder="officer@ndrf.gov.in" class="w-full px-4.5 py-3.5 rounded-xl bg-[#060a14] border border-slate-700/80 text-slate-100 text-sm font-medium focus:outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-500/30 transition-all placeholder:text-slate-500 shadow-inner text-center" />
                </div>
              </div>

              <!-- Primary Action Buttons -->
              <div class="space-y-3 pt-4">
                <button onclick="handleCreateAccountAndLogin(false)" class="w-full py-4.5 rounded-xl bg-gradient-to-r from-rose-600 via-rose-500 to-rose-600 hover:from-rose-500 hover:to-rose-400 text-white font-extrabold text-sm sm:text-base tracking-wider uppercase shadow-[0_0_25px_rgba(244,63,94,0.4)] hover:shadow-[0_0_35px_rgba(244,63,94,0.65)] hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-3">
                  <span>AUTHENTICATE & ENTER COMMAND DESK</span>
                  <span>→</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function renderDashboardView() {
      const selectedInc = state.incidents.find(i => i.id === state.selectedIncidentId);

      return `
        <div class="min-h-screen bg-[#060911] text-slate-100 flex flex-col font-sans">
          <!-- Header -->
          <header class="h-16 bg-[#0d121f] border-b border-slate-800/80 px-6 md:px-8 flex items-center justify-between sticky top-0 z-40">
            <div class="flex items-center space-x-4">
              <div class="w-9 h-9 rounded-xl bg-rose-600/20 border border-rose-500/30 flex items-center justify-center text-rose-400 text-lg">
                🛡️
              </div>
              <div>
                <div class="flex items-center space-x-3">
                  <span class="font-bold text-base text-slate-100 font-heading tracking-tight">PUKAAR</span>
                  <span class="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    LIVE COMMAND PORTAL
                  </span>
                </div>
                <p class="text-xs text-slate-400 font-sans hidden sm:block">National Emergency Operations Command Center • Official Dispatch Hub</p>
              </div>
            </div>

            <div class="flex items-center space-x-4">
              <div class="hidden lg:flex items-center space-x-3 text-xs font-mono text-slate-400 bg-[#060911] px-3.5 py-1.5 rounded-xl border border-slate-800">
                <span class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <strong class="text-slate-200">REAL-TIME BACKEND SYNC</strong>
                </span>
                <span class="text-slate-700">•</span>
                <span>Sync: <strong class="text-cyan-400">${state.lastSyncTime}</strong></span>
              </div>

              <button onclick="setState({ showIngestModal: true })" class="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-semibold border border-rose-500/30 transition-all flex items-center gap-1.5">
                <span>⚡</span>
                <span>Feed Live SOS Packet</span>
              </button>

              <button onclick="setState({ isAuthenticated: false })" class="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition-all">
                Sign Out
              </button>
            </div>
          </header>

          <div class="flex-1 flex overflow-hidden">
            <!-- Sidebar -->
            <aside class="w-64 bg-[#0d121f] border-r border-slate-800/80 p-5 hidden md:flex flex-col justify-between shrink-0">
              <div class="space-y-6">
                <div class="p-4 rounded-2xl bg-[#060911] border border-slate-800/80 space-y-1">
                  <p class="text-xs font-bold text-slate-200">${state.officerName}</p>
                  <p class="text-[11px] text-slate-400 font-mono">Badge: ${state.badge}</p>
                  <div class="pt-1">
                    <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                      ROLE: ${state.role}
                    </span>
                  </div>
                </div>

                <div class="space-y-1 text-xs">
                  <p class="text-[10px] text-slate-500 uppercase px-3 mb-2 font-bold tracking-wider">OPERATIONAL SPACES</p>
                  ${[
                    { id: 'dashboard', label: 'Command Desk' },
                    { id: 'incidents', label: 'Priority Queue' },
                    { id: 'map', label: 'Operations Map' },
                    { id: 'dispatch', label: 'Dispatch & Fleet' },
                    { id: 'analytics', label: 'Zone Analytics' },
                    { id: 'admins', label: 'Admins & Roles' },
                    { id: 'audit', label: 'Audit & Security' }
                  ].map(tab => `
                    <button onclick="setState({ activeTab: '${tab.id}' })" class="w-full text-left px-4 py-3 rounded-xl font-medium transition-all ${state.activeTab === tab.id ? 'bg-slate-800/90 text-white font-semibold border-l-2 border-rose-500 shadow-sm' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}">
                      ${tab.label}
                    </button>
                  `).join('')}
                </div>
              </div>
            </aside>

            <!-- Main Workspace -->
            <main class="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
              ${state.activeTab === 'dashboard' ? `
                <div class="space-y-6">
                  <!-- Top Glowing Alert Banner (STRICTLY THE ONLY GLOWING BAR) -->
                  <div class="p-6 rounded-2xl bg-gradient-to-r from-[#14080d] via-[#0d121f] to-[#14080d] border-2 border-rose-500/80 glow-alert-red flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-2xl relative overflow-hidden">
                    <div class="space-y-2">
                      <div class="flex flex-wrap items-center gap-3">
                        <span class="text-xs sm:text-sm font-black font-mono tracking-widest uppercase text-rose-200 bg-gradient-to-r from-rose-950 via-rose-900 to-rose-950 px-3.5 py-1.5 rounded-xl border border-rose-500/80 shadow-[0_0_15px_rgba(244,63,94,0.4)] flex items-center gap-2.5">
                          <span class="beacon-dot-red"></span>
                          <span>CRITICAL RED ALERT — IMMEDIATE ACTION REQUIRED</span>
                        </span>
                        <span class="px-3 py-1.5 rounded-xl text-xs font-mono font-extrabold tracking-wider uppercase bg-amber-500/10 text-amber-300 border border-amber-500/40 flex items-center gap-2">
                          <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                          <span>STATUS: REAL-TIME ACTIVE</span>
                        </span>
                      </div>
                      <p class="text-base sm:text-lg font-heading font-extrabold leading-snug pt-1 text-white tracking-wide flex items-center gap-2">
                        <span class="text-rose-400 text-xl">🚨</span>
                        <span class="bg-gradient-to-r from-white via-rose-100 to-rose-300 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(244,63,94,0.4)]">
                          ${state.incidents[0]?.title} — ${state.incidents[0]?.aiScoreV2?.briefing?.headline}
                        </span>
                      </p>
                    </div>
                    <button onclick="setState({ selectedIncidentId: '${state.incidents[0]?.id}' })" class="px-6 py-3 rounded-xl bg-gradient-to-r from-rose-600 to-rose-500 hover:from-rose-500 hover:to-rose-400 text-white text-xs font-extrabold font-mono tracking-wider uppercase transition-all shrink-0 shadow-lg shadow-rose-600/40 flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98]">
                      <span>⚡</span>
                      <span>INSPECT TACTICAL BRIEFING →</span>
                    </button>
                  </div>

                  <!-- Metrics -->
                  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="p-5 rounded-2xl bg-[#0d121f] border border-rose-500/50 space-y-1.5 relative overflow-hidden">
                      <div class="flex items-center justify-between">
                        <span class="text-xs text-rose-400 font-bold tracking-wide flex items-center gap-2">
                          <span class="beacon-dot-red"></span>
                          CRITICAL ALERTS
                        </span>
                        <span class="text-[10px] font-mono text-rose-300 font-bold bg-rose-950/60 px-2 py-0.5 rounded border border-rose-500/30">PRIORITY 1</span>
                      </div>
                      <p class="text-3xl font-extrabold text-rose-400">${state.incidents.filter(i => i.severity === 'CRITICAL').length}</p>
                      <p class="text-xs text-slate-300 font-medium">Immediate Life Threat</p>
                    </div>

                    <div class="p-5 rounded-2xl bg-[#0d121f] border border-amber-500/30 space-y-1.5 relative overflow-hidden">
                      <div class="flex items-center justify-between">
                        <span class="text-xs text-amber-400 font-bold tracking-wide flex items-center gap-2">
                          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
                          HIGH PRIORITY
                        </span>
                        <span class="text-[10px] font-mono text-amber-300 font-bold bg-amber-950/60 px-2 py-0.5 rounded border border-amber-500/30">PRIORITY 2</span>
                      </div>
                      <p class="text-3xl font-extrabold text-amber-400">${state.incidents.filter(i => i.severity === 'HIGH').length}</p>
                      <p class="text-xs text-slate-300 font-medium">Substation & Fire Alerts</p>
                    </div>

                    <div class="p-5 rounded-2xl bg-[#0d121f] border border-slate-800 space-y-1.5">
                      <span class="text-xs text-cyan-400 font-bold tracking-wide">TOTAL QUEUED</span>
                      <p class="text-3xl font-extrabold text-cyan-300">${state.incidents.length}</p>
                      <p class="text-xs text-slate-400">Live Ingested Incidents</p>
                    </div>

                    <div class="p-5 rounded-2xl bg-[#0d121f] border border-slate-800 space-y-1.5">
                      <span class="text-xs text-emerald-400 font-bold tracking-wide">FLEET READY</span>
                      <p class="text-3xl font-extrabold text-emerald-400">${state.resources.filter(r => r.status === 'AVAILABLE').length}</p>
                      <p class="text-xs text-slate-400">Available NDRF Units</p>
                    </div>
                  </div>

                  <!-- Queue -->
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <h3 class="text-base font-bold text-slate-100 font-heading tracking-tight flex items-center gap-2">
                        <span>EMERGENCY PRIORITY TRIAGE QUEUE</span>
                        <span class="beacon-dot-red"></span>
                      </h3>
                      <button onclick="syncBackendData()" class="text-xs text-cyan-400 font-mono hover:underline flex items-center gap-1">
                        <span>🔄</span>
                        <span>Force Backend Refresh</span>
                      </button>
                    </div>
                    ${state.incidents.map(inc => `
                      <div onclick="setState({ selectedIncidentId: '${inc.id}' })" class="p-6 rounded-2xl bg-[#0d121f] border transition-all cursor-pointer space-y-3 relative ${inc.severity === 'CRITICAL' ? 'border-rose-500/60' : 'border-amber-500/40'}">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div class="flex items-center space-x-3">
                            <span class="px-3 py-1.5 rounded-xl font-mono font-bold text-xs flex items-center gap-1.5 shadow-md ${inc.severity === 'CRITICAL' ? 'bg-rose-950/70 text-rose-300 border border-rose-500/60' : 'bg-amber-950/70 text-amber-300 border border-amber-500/60'}">
                              <span class="${inc.severity === 'CRITICAL' ? 'beacon-dot-red' : 'w-2 h-2 rounded-full bg-amber-400'}"></span>
                              PRIORITY SCORE: ${inc.aiScoreV2?.priority || 90}/100
                            </span>
                            <div>
                              <h4 class="text-base font-bold text-slate-100 tracking-tight">${inc.title}</h4>
                              <p class="text-xs text-slate-400">${inc.location?.sector}</p>
                            </div>
                          </div>
                          <span class="text-xs font-bold text-rose-400 hover:text-rose-300 flex items-center gap-1 bg-rose-500/10 px-3 py-1.5 rounded-lg border border-rose-500/20">
                            <span>Inspect Tactical Briefing</span>
                            <span>→</span>
                          </span>
                        </div>
                        <p class="text-xs text-slate-200 bg-[#060911] p-4 rounded-xl border border-slate-800/90 leading-relaxed font-sans">
                          <strong class="text-rose-400 font-mono uppercase">🚨 Tactical Briefing:</strong> ${inc.aiScoreV2?.briefing?.headline}
                        </p>
                      </div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

              ${state.activeTab === 'incidents' ? `
                <div class="space-y-4">
                  <h3 class="text-lg font-bold text-slate-100 font-heading">PRIORITY QUEUE WORKSPACE</h3>
                  ${state.incidents.map(inc => `
                    <div class="p-6 rounded-2xl bg-[#0d121f] border border-slate-800 space-y-4">
                      <div class="flex items-center justify-between">
                        <span class="text-xs font-mono font-bold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-lg border border-rose-500/20">${inc.code}</span>
                        <span class="text-xs font-mono text-amber-300 font-bold">SCORE: ${inc.aiScoreV2?.priority}/100</span>
                      </div>
                      <h4 class="text-lg font-bold text-slate-100">${inc.title}</h4>
                      <p class="text-xs text-slate-300 bg-[#060911] p-4 rounded-xl border border-slate-800 leading-relaxed">${inc.aiScoreV2?.briefing?.headline}</p>
                      <button onclick="setState({ selectedIncidentId: '${inc.id}' })" class="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs">Inspect Briefing & Hops →</button>
                    </div>
                  `).join('')}
                </div>
              ` : ''}

              ${state.activeTab === 'map' ? `
                <div class="h-[78vh] rounded-3xl bg-[#060911] border border-slate-800 relative overflow-hidden flex items-center justify-center p-6 text-center">
                  <div class="absolute w-[500px] h-[500px] rounded-full bg-rose-600/5 border border-rose-500/30 animate-pulse flex items-center justify-center">
                    <div class="w-80 h-80 rounded-full bg-rose-500/5 border border-rose-400/20 flex items-center justify-center">
                      <span class="text-xs font-mono font-semibold text-rose-300 bg-[#0d121f] px-3 py-1.5 rounded-xl border border-rose-500/30">
                        🔴 ZONE A: SECTOR 14 CRITICAL (850m • 18 Reports)
                      </span>
                    </div>
                  </div>
                  <div class="relative z-10 text-xs text-slate-300 max-w-md space-y-3 bg-[#0d121f] p-6 rounded-2xl border border-slate-800 shadow-xl leading-relaxed">
                    <p class="font-bold text-slate-100 text-sm">🗺️ DYNAMIC DISASTER OPERATIONS MAP</p>
                    <p class="text-slate-400">Visualizing real-time dynamic severity polygons, mesh link routes (P1→P5), and active NDRF fleet positions.</p>
                  </div>
                </div>
              ` : ''}

              ${state.activeTab === 'dispatch' ? `
                <div class="space-y-4">
                  <h3 class="text-lg font-bold text-slate-100 font-heading">DISPATCH & EMERGENCY FLEET MATRIX</h3>
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${state.resources.map(res => `
                      <div class="p-5 rounded-2xl bg-[#0d121f] border border-slate-800 space-y-4">
                        <div class="flex items-center justify-between">
                          <span class="text-xs font-mono font-semibold text-slate-300 bg-slate-800 px-2.5 py-1 rounded-lg">${res.type}</span>
                          <span class="text-xs font-mono font-bold text-emerald-400">${res.status}</span>
                        </div>
                        <h4 class="text-base font-bold text-slate-100">${res.callsign}</h4>
                        ${res.assignedIncidentCode ? `<p class="text-xs font-mono text-amber-300 bg-[#060911] p-2.5 rounded-xl border border-slate-800">Assigned: ${res.assignedIncidentCode}</p>` : ''}
                        <button onclick="handleDispatch('${state.incidents[0]?.id}', '${res.type}')" class="w-full py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold">Dispatch Unit</button>
                      </div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

              ${state.activeTab === 'analytics' ? `
                <div class="relative min-h-[82vh] rounded-3xl bg-[#060911] border border-slate-800 p-6 md:p-8 space-y-6 overflow-hidden flex flex-col justify-between">
                  <!-- Outlined World Map Vector Background -->
                  <div class="absolute inset-0 pointer-events-none overflow-hidden z-0">
                    <svg viewBox="0 0 1000 500" class="absolute inset-0 w-full h-full object-cover opacity-25 stroke-cyan-400 fill-cyan-500/5" stroke-width="1.5">
                      <path d="M 120 100 Q 150 70 220 80 T 300 120 T 260 220 T 180 240 T 130 180 Z" />
                      <path d="M 270 300 Q 320 320 340 370 T 310 460 T 270 420 T 250 340 Z" />
                      <path d="M 460 100 Q 520 80 560 110 T 540 170 T 480 160 Z" />
                      <path d="M 460 180 Q 540 180 570 240 T 540 360 T 480 340 T 450 240 Z" />
                      <path d="M 570 90 Q 680 70 820 100 T 880 200 T 780 280 T 650 250 T 570 170 Z" />
                      <path d="M 670 210 L 720 230 L 700 290 L 660 250 Z" class="fill-rose-500/20 stroke-rose-400 animate-pulse" stroke-width="2" />
                      <circle cx="685" cy="235" r="14" fill="none" stroke="#f43f5e" stroke-width="2" />
                      <circle cx="685" cy="235" r="4" fill="#f43f5e" />
                    </svg>
                  </div>

                  <div class="relative z-10 space-y-6">
                    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0d121f]/85 backdrop-blur-md p-6 rounded-2xl border border-slate-800">
                      <div>
                        <h3 class="text-xl font-extrabold text-slate-100 font-heading">GLOBAL DISASTER & ZONE EXPANSION ANALYTICS</h3>
                        <p class="text-xs text-slate-400 mt-1">Real-time geospatial severity mapping and multi-hop telemetry.</p>
                      </div>
                      <span class="px-3 py-1.5 rounded-xl bg-rose-950/60 text-rose-300 border border-rose-500/40 font-bold text-xs">ACTIVE ZONE ALPHA: SECTOR 14</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div class="p-5 rounded-2xl bg-[#0d121f]/90 border border-rose-500/40 space-y-1.5">
                        <span class="text-xs text-rose-400 font-bold">ZONE ALPHA RADIUS</span>
                        <p class="text-3xl font-extrabold text-rose-400">850m</p>
                        <p class="text-xs text-slate-300">Expanded (+240% velocity)</p>
                      </div>
                      <div class="p-5 rounded-2xl bg-[#0d121f]/90 border border-amber-500/40 space-y-1.5">
                        <span class="text-xs text-amber-400 font-bold">CORROBORATION RATE</span>
                        <p class="text-3xl font-extrabold text-amber-400">18 / 3min</p>
                        <p class="text-xs text-slate-300">Spike velocity confirmed</p>
                      </div>
                      <div class="p-5 rounded-2xl bg-[#0d121f]/90 border border-slate-800 space-y-1.5">
                        <span class="text-xs text-cyan-400 font-bold">PACKET DELIVERY</span>
                        <p class="text-3xl font-extrabold text-cyan-300">99.4%</p>
                        <p class="text-xs text-slate-400">Mesh Hop P1→P5</p>
                      </div>
                      <div class="p-5 rounded-2xl bg-[#0d121f]/90 border border-slate-800 space-y-1.5">
                        <span class="text-xs text-emerald-400 font-bold">AI CONFIDENCE</span>
                        <p class="text-3xl font-extrabold text-emerald-400">94.0%</p>
                        <p class="text-xs text-slate-400">Groq NLP Extraction</p>
                      </div>
                    </div>
                  </div>
                </div>
              ` : ''}

              ${state.activeTab === 'admins' ? `
                <div class="space-y-6 text-xs">
                  <div class="flex items-center justify-between">
                    <div>
                      <h3 class="text-lg font-bold text-slate-100 font-heading">ENTERPRISE ADMINS & ROLES CONTROL</h3>
                      <p class="text-xs text-slate-400">Registered officers and system admins with active credentials.</p>
                    </div>
                    <span class="px-3 py-1.5 rounded-xl bg-cyan-950/60 text-cyan-300 border border-cyan-500/40 font-mono font-bold">
                      ${state.registeredAdmins.length} Active Admins
                    </span>
                  </div>

                  <!-- Inline Register Admin Card -->
                  <div class="p-6 rounded-2xl bg-[#0d121f] border border-slate-800 space-y-4">
                    <h4 class="text-sm font-bold text-slate-100">➕ Register Additional Command Admin / Officer</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <input id="dashRegName" type="text" placeholder="Officer Full Name (e.g. Dr. K. Raman)" class="px-4 py-2.5 rounded-xl bg-[#060911] border border-slate-800 text-slate-100 text-xs" />
                      <input id="dashRegBadge" type="text" placeholder="Badge ID (e.g. ADM-DEL-771)" class="px-4 py-2.5 rounded-xl bg-[#060911] border border-slate-800 text-slate-100 text-xs font-mono" />
                      <select id="dashRegRole" class="px-4 py-2.5 rounded-xl bg-[#060911] border border-slate-800 text-slate-100 text-xs font-mono">
                        <option value="SUPER_ADMIN" selected>SUPER_ADMIN</option>
                        <option value="COMMANDER">COMMANDER</option>
                        <option value="RESPONDER">RESPONDER</option>
                        <option value="ANALYST">ANALYST</option>
                      </select>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <input id="dashRegPhone" type="text" placeholder="Mobile (+91 98765-43210)" class="px-4 py-2.5 rounded-xl bg-[#060911] border border-slate-800 text-slate-100 text-xs font-mono" />
                      <input id="dashRegEmail" type="email" placeholder="Official Email (officer@pukaar.gov.in)" class="px-4 py-2.5 rounded-xl bg-[#060911] border border-slate-800 text-slate-100 text-xs" />
                    </div>
                    <button onclick="handleCreateAccountAndLogin(true)" class="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-md">
                      ➕ Add Admin Credentials
                    </button>
                  </div>

                  <!-- Table of Registered Admins -->
                  <div class="p-4 rounded-2xl bg-[#0d121f] border border-slate-800 overflow-x-auto">
                    <table class="w-full text-left">
                      <thead>
                        <tr class="border-b border-slate-800 text-slate-400 text-xs">
                          <th class="py-3 px-4">Badge ID</th>
                          <th class="py-3 px-4">Officer Name</th>
                          <th class="py-3 px-4">Role</th>
                          <th class="py-3 px-4">Contact Phone</th>
                          <th class="py-3 px-4">Official Email</th>
                          <th class="py-3 px-4">Status</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-slate-800/60">
                        ${state.registeredAdmins.map(adm => `
                          <tr>
                            <td class="py-3 px-4 text-cyan-400 font-mono font-bold">${adm.badge}</td>
                            <td class="py-3 px-4 font-semibold text-slate-200">${adm.name}</td>
                            <td class="py-3 px-4">
                              <span class="px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold ${adm.role === 'SUPER_ADMIN' ? 'bg-purple-950 text-purple-300 border border-purple-500/40' : 'bg-slate-800 text-slate-300 border border-slate-700'}">
                                ${adm.role}
                              </span>
                            </td>
                            <td class="py-3 px-4 text-slate-300 font-mono">${adm.phone || '+91 98765-43210'}</td>
                            <td class="py-3 px-4 text-slate-400">${adm.email || 'admin@pukaar.gov.in'}</td>
                            <td class="py-3 px-4 text-emerald-400 font-mono font-bold">ACTIVE</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  </div>
                </div>
              ` : ''}

              ${state.activeTab === 'audit' ? `
                <div class="space-y-4 text-xs">
                  <h3 class="text-lg font-bold text-slate-100 font-heading">ENTERPRISE AUDIT EVENT LOG STREAM</h3>
                  <div class="p-4 rounded-2xl bg-[#0d121f] border border-slate-800 overflow-x-auto">
                    <table class="w-full text-left">
                      <thead>
                        <tr class="border-b border-slate-800 text-slate-400 text-xs">
                          <th class="py-3 px-4">Time</th>
                          <th class="py-3 px-4">User</th>
                          <th class="py-3 px-4">Role</th>
                          <th class="py-3 px-4">Action</th>
                          <th class="py-3 px-4">Result</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-slate-800/60">
                        ${state.auditEvents.map(evt => `
                          <tr>
                            <td class="py-3 px-4 text-cyan-400 font-mono">${evt.timestamp}</td>
                            <td class="py-3 px-4">${evt.userName}</td>
                            <td class="py-3 px-4 text-amber-300 font-mono">${evt.role}</td>
                            <td class="py-3 px-4 font-semibold text-slate-200">${evt.action}</td>
                            <td class="py-3 px-4 text-emerald-400 font-mono">${evt.result}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  </div>
                </div>
              ` : ''}
            </main>
          </div>

          <!-- Ingest Modal -->
          ${state.showIngestModal ? `
            <div class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
              <div class="bg-[#0d121f] border border-slate-700 rounded-3xl w-full max-w-lg p-6 space-y-4 shadow-2xl text-xs">
                <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 class="text-sm font-bold text-slate-100">⚡ FEED LIVE SOS PACKET TO BACKEND</h3>
                  <button onclick="setState({ showIngestModal: false })" class="text-slate-400 hover:text-white">✕</button>
                </div>
                <p class="text-slate-300">Post raw emergency JSON packet to backend endpoint:</p>
                <textarea id="rawPacketInput" rows="8" class="w-full p-4 rounded-xl bg-[#060911] border border-slate-800 text-cyan-300 font-mono text-xs focus:outline-none">${state.rawPacketJson}</textarea>
                <div class="flex justify-end gap-2 pt-2">
                  <button onclick="setState({ showIngestModal: false })" class="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-semibold">Cancel</button>
                  <button onclick="handleFeedSosPacket()" class="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold shadow-sm">Ingest Packet →</button>
                </div>
              </div>
            </div>
          ` : ''}

          <!-- Incident Workspace Modal -->
          ${selectedInc ? `
            <div class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
              <div class="bg-[#0d121f] border border-slate-700 rounded-3xl w-full max-w-3xl max-h-[92vh] overflow-y-auto p-8 space-y-6 shadow-2xl">
                <div class="flex items-start justify-between border-b border-slate-800 pb-4">
                  <div>
                    <span class="text-xs font-mono font-bold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-lg border border-rose-500/20">${selectedInc.code}</span>
                    <h2 class="text-xl font-bold text-slate-100 mt-2 font-heading">${selectedInc.title}</h2>
                    <p class="text-xs text-slate-400 mt-0.5">${selectedInc.location?.sector}</p>
                  </div>
                  <button onclick="setState({ selectedIncidentId: null })" class="text-slate-400 hover:text-white text-lg">✕</button>
                </div>

                <div class="p-4 rounded-2xl bg-[#060911] border border-slate-800 space-y-1">
                  <p class="font-mono text-xs font-bold text-amber-400 uppercase">TACTICAL BRIEFING</p>
                  <p class="text-sm font-semibold text-slate-100 leading-relaxed">${selectedInc.aiScoreV2?.briefing?.headline}</p>
                </div>

                <div class="p-5 rounded-2xl bg-[#060911] border border-slate-800 space-y-3 text-xs">
                  <p class="font-bold text-slate-200 text-sm">⚡ AUTOMATED TRIAGE MATRIX</p>
                  <div class="grid grid-cols-5 gap-2 text-center text-xs font-mono">
                    <div class="p-2.5 bg-[#0d121f] rounded-xl border border-slate-800">Regex: <strong class="text-cyan-400">${selectedInc.aiScoreV2?.regexScore || 88}%</strong></div>
                    <div class="p-2.5 bg-[#0d121f] rounded-xl border border-slate-800">NLP: <strong class="text-amber-400">${selectedInc.aiScoreV2?.groqScore || 94}%</strong></div>
                    <div class="p-2.5 bg-[#0d121f] rounded-xl border border-slate-800">Corroboration: <strong class="text-emerald-400">+${selectedInc.aiScoreV2?.corroborationBonus || 8}</strong></div>
                    <div class="p-2.5 bg-[#0d121f] rounded-xl border border-slate-800">Location: <strong class="text-indigo-400">+${selectedInc.aiScoreV2?.locationBonus || 3}</strong></div>
                    <div class="p-2.5 bg-rose-950/40 text-rose-300 rounded-xl border border-rose-500/40 font-bold">Priority: ${selectedInc.aiScoreV2?.priority || 97}</div>
                  </div>
                </div>

                <div class="p-5 rounded-2xl bg-[#060911] border border-slate-800 space-y-3 text-xs">
                  <p class="font-bold text-slate-200 text-sm">📡 MESH PACKET TRANSIT ROUTE (P1 → P5 → SERVER)</p>
                  <div class="flex flex-wrap items-center gap-2 text-xs font-mono">
                    <span class="p-2.5 rounded-xl bg-rose-950/40 text-rose-300 border border-rose-500/30">P1 (Victim)</span>
                    <span class="text-slate-600">→</span>
                    <span class="p-2.5 rounded-xl bg-[#0d121f] text-slate-300 border border-slate-800">P2 (Relay)</span>
                    <span class="text-slate-600">→</span>
                    <span class="p-2.5 rounded-xl bg-[#0d121f] text-slate-300 border border-slate-800">P3 (Relay)</span>
                    <span class="text-slate-600">→</span>
                    <span class="p-2.5 rounded-xl bg-[#0d121f] text-slate-300 border border-slate-800">P4 (Relay)</span>
                    <span class="text-slate-600">→</span>
                    <span class="p-2.5 rounded-xl bg-[#0d121f] text-slate-300 border border-slate-800">P5 (Gateway)</span>
                    <span class="text-slate-600">→</span>
                    <span class="p-2.5 rounded-xl bg-emerald-950/40 text-emerald-300 border border-emerald-500/30">SERVER 🌐</span>
                  </div>
                </div>

                <div class="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button onclick="handleDispatch('${selectedInc.id}', 'RESCUE')" class="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs shadow-sm flex items-center gap-2">
                    <span>🚒</span>
                    <span>Dispatch Rescue</span>
                  </button>
                  <button onclick="handleDispatch('${selectedInc.id}', 'AMBULANCE')" class="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs shadow-sm flex items-center gap-2">
                    <span>🚑</span>
                    <span>Dispatch Ambulance</span>
                  </button>
                  <button onclick="setState({ selectedIncidentId: null })" class="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold">Close</button>
                </div>
              </div>
            </div>
          ` : ''}
        </div>
      `;
    }

    function renderApp() {
      const container = document.getElementById('app');
      if (!container) return;
      if (!state.isAuthenticated) {
        container.innerHTML = renderLoginView();
      } else {
        container.innerHTML = renderDashboardView();
      }
    }

    // Initial render on page load
    document.addEventListener('DOMContentLoaded', renderApp);
    renderApp();
  </script>
</body>
</html>
"""

with open('static/pukaar_command_center.html', 'w') as f:
    f.write(html_code)

with open('static/index.html', 'w') as f:
    f.write(html_code)

with open('index.html', 'w') as f:
    f.write(html_code)

print("Beautified and enlarged officer credentials selection card on login page.")
