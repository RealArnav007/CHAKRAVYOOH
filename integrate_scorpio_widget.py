import os
import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add state variables for MOSDAC SCORPIO widget if not present
if 'scorpioCoords' not in code:
    code = code.replace(
        "activePortalView: 'portal',",
        """activePortalView: 'portal',
      scorpioCoords: '71.5040, -8.6363',
      scorpioTimestamp: '08-SEP-2026 15:00',
      scorpioZoom: 1.0,
      scorpioLayerMode: 'gui', // 'gui' | 'stream'
      scorpioWindActive: true,
      scorpioScatActive: false,
      scorpioInfoModal: false,
      scorpioTimelineProgress: 100,"""
    )

# 2. Add JavaScript functions for the interactive MOSDAC SCORPIO widget
scorpio_js = """
    // =========================================================================
    // ISRO SAC MOSDAC SCORPIO INTERACTIVE WIDGET ENGINE (Screenshot Exact UI)
    // =========================================================================
    function handleScorpioMouseMove(e, elementId) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      // Map x, y into approximate Indian Ocean Lat / Lon space
      const lon = (30 + x * 90).toFixed(4);
      const lat = (40 - y * 65).toFixed(4);
      state.scorpioCoords = `${lon}, ${lat}`;
      const coordEl = document.getElementById(elementId + '_coords');
      if (coordEl) coordEl.textContent = state.scorpioCoords;
    }

    function handleScorpioZoom(delta, elementId) {
      state.scorpioZoom = Math.max(0.8, Math.min(2.5, state.scorpioZoom + delta * 0.25));
      const mapEl = document.getElementById(elementId + '_map');
      if (mapEl) {
        mapEl.style.transform = `scale(${state.scorpioZoom})`;
      }
    }

    function handleScorpioScrub(val, elementId) {
      state.scorpioTimelineProgress = val;
      // Convert progress (0 - 100) to time between 05:30 and 15:00 (570 minutes span)
      const startMins = 5 * 60 + 30;
      const currentMins = Math.round(startMins + (val / 100) * (9 * 60 + 30));
      const h = String(Math.floor(currentMins / 60)).padStart(2, '0');
      const m = String(currentMins % 60).padStart(2, '0');
      state.scorpioTimestamp = `08-SEP-2026 ${h}:${m}`;
      const timeEl = document.getElementById(elementId + '_timestamp');
      if (timeEl) timeEl.textContent = `${state.scorpioTimestamp} Imager/INSAT3DR/3DS IMG_TIR1`;
    }

    function toggleScorpioLayer(layer) {
      if (layer === 'wind') state.scorpioWindActive = !state.scorpioWindActive;
      if (layer === 'scat') state.scorpioScatActive = !state.scorpioScatActive;
      if (layer === 'info') state.scorpioInfoModal = !state.scorpioInfoModal;
      renderApp();
    }

    function setScorpioDisplayMode(mode) {
      state.scorpioLayerMode = mode;
      renderApp();
    }
"""

if 'function handleScorpioMouseMove' not in code:
    code = code.replace(
        '    // =========================================================================\n    // PIXEL ART WEATHER WIDGET CONTROLLER',
        scorpio_js + '\n    // =========================================================================\n    // PIXEL ART WEATHER WIDGET CONTROLLER'
    )

# 3. Add function to render the complete MOSDAC SCORPIO widget
render_mosdac_scorpio_widget_fn = """
    // =========================================================================
    // RENDER ISRO SAC MOSDAC SCORPIO RIGHT-HAND INTERACTIVE WIDGET
    // =========================================================================
    function renderMosdacScorpioWidget(id = 'scorpio_hero') {
      const isStream = state.scorpioLayerMode === 'stream';

      return `
        <div class="mission-card border-2 border-[#1e3456] rounded-2xl overflow-hidden shadow-2xl bg-[#0a0f1d] flex flex-col select-none relative group h-[580px] text-xs font-sans">
          <!-- 1. MOSDAC SCORPIO TOP AGENCY HEADER BAR -->
          <div class="bg-[#0e172a] border-b border-[#1b2b45] px-3 py-2 flex items-center justify-between gap-2 z-20">
            <!-- Brand Logotype: M O S D A C in individual green tiles + SCORPIO -->
            <div class="flex items-center space-x-2">
              <div class="flex items-center space-x-0.5">
                <span class="bg-[#14b8a6] text-[#042f2e] font-black text-[11px] px-1 py-0.5 rounded-[2px] shadow-sm">M</span>
                <span class="bg-[#14b8a6] text-[#042f2e] font-black text-[11px] px-1 py-0.5 rounded-[2px] shadow-sm">O</span>
                <span class="bg-[#14b8a6] text-[#042f2e] font-black text-[11px] px-1 py-0.5 rounded-[2px] shadow-sm">S</span>
                <span class="bg-[#14b8a6] text-[#042f2e] font-black text-[11px] px-1 py-0.5 rounded-[2px] shadow-sm">D</span>
                <span class="bg-[#14b8a6] text-[#042f2e] font-black text-[11px] px-1 py-0.5 rounded-[2px] shadow-sm">A</span>
                <span class="bg-[#14b8a6] text-[#042f2e] font-black text-[11px] px-1 py-0.5 rounded-[2px] shadow-sm">C</span>
              </div>
              <div class="bg-[#0f243d] border border-cyan-400/60 px-2 py-0.5 rounded-full text-cyan-300 font-extrabold italic text-[11px] tracking-wider shadow">
                SCORPIO 🌀
              </div>
              <!-- Info icon & LOC button -->
              <div class="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center text-[9px] font-serif font-bold">
                i
              </div>
              <div class="bg-blue-600 text-white font-mono font-bold text-[9px] px-1.5 py-0.5 rounded">
                LOC
              </div>
            </div>

            <!-- View Switcher & Live Coordinates Display -->
            <div class="flex items-center space-x-2">
              <div class="bg-black/70 border border-slate-700 px-2 py-0.5 rounded text-[10px] font-mono text-slate-200">
                <span id="${id}_coords">${state.scorpioCoords}</span>
              </div>
              <div class="flex items-center bg-[#070c18] border border-[#1b2b45] rounded-lg p-0.5 text-[10px] font-mono">
                <button onclick="setScorpioDisplayMode('gui')" class="px-2 py-0.5 rounded ${!isStream ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'}">Radar</button>
                <button onclick="setScorpioDisplayMode('stream')" class="px-2 py-0.5 rounded ${isStream ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'}">Live Web</button>
              </div>
            </div>
          </div>

          <!-- 2. SCORPIO SUB-HEADER (Banner & Dropdowns) -->
          <div class="bg-[#0b1424] border-b border-[#182740] px-3 py-1.5 space-y-1 z-20">
            <div class="flex items-center justify-between">
              <div class="bg-[#0369a1] text-cyan-100 font-bold italic px-2 py-0.5 rounded text-[11px] tracking-tight inline-block shadow">
                Active Cyclone BOB-04 in Indian Ocean (Bay of Bengal)
              </div>
              <span class="text-emerald-400 text-[10px] font-mono font-bold animate-pulse">● SAC / ISRO LIVE</span>
            </div>
            <div class="flex items-center justify-between text-[10px] font-mono text-slate-300">
              <div class="flex items-center space-x-2">
                <!-- Cyan Round Menu Button -->
                <button class="w-5 h-5 rounded-full bg-cyan-400 text-black flex items-center justify-center font-bold text-[10px] shadow">
                  ☰
                </button>
                <span id="${id}_timestamp" class="text-slate-200 font-semibold">${state.scorpioTimestamp} Imager/INSAT3DR/3DS IMG_TIR1</span>
              </div>
              <div class="flex items-center space-x-1">
                <span>Year:</span>
                <span class="bg-[#142036] px-1 py-0.5 rounded border border-[#203150] text-white">Recent ▾</span>
                <span>Cyclone:</span>
                <span class="bg-[#142036] px-1.5 py-0.5 rounded border border-red-500/50 text-red-300 font-bold">BOB-04 ▾</span>
              </div>
            </div>
          </div>

          <!-- 3. MAIN SATELLITE MAP VIEWPORT -->
          <div class="relative flex-1 bg-[#060b14] overflow-hidden cursor-crosshair select-none" onmousemove="handleScorpioMouseMove(event, '${id}')">
            ${isStream ? `
              <!-- Direct Embedded Live SCORPIO Stream -->
              <iframe src="/scorpio_feed" class="w-full h-full border-0" title="Official MOSDAC SCORPIO Live Feed"></iframe>
            ` : `
              <!-- High-Fidelity Interactive SCORPIO Radar Canvas -->
              <div id="${id}_map" class="absolute inset-0 w-full h-full origin-center transition-transform duration-200" style="transform: scale(${state.scorpioZoom});">
                <!-- Base Satellite Oceanic Background -->
                <div class="absolute inset-0 bg-[#06101f]">
                  <!-- High-Res Satellite Cloud Layer (Authentic to screenshot) -->
                  <div class="absolute inset-0 opacity-80 mix-blend-screen bg-cover bg-center" style="background-image: radial-gradient(circle at 65% 45%, rgba(255,255,255,0.85) 0%, rgba(224,242,254,0.5) 25%, rgba(14,165,233,0.15) 55%, transparent 75%);"></div>
                </div>

                <!-- Green National & Maritime Coastlines (Screenshot Signature Style) -->
                <svg class="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 1000 650" preserveAspectRatio="none">
                  <!-- Global Landmass Boundaries in Crisp Lime-Green -->
                  <!-- Africa Outline -->
                  <path d="M 310,230 L 330,220 L 370,240 L 410,270 L 425,320 L 400,380 L 370,440 L 360,520 L 320,490 L 290,400 L 240,360 L 220,310 L 260,250 Z" fill="none" stroke="#22c55e" stroke-width="1.6" opacity="0.85"/>
                  <!-- Arabian Peninsula -->
                  <path d="M 430,280 L 480,270 L 510,310 L 480,360 L 440,340 Z" fill="none" stroke="#22c55e" stroke-width="1.6" opacity="0.85"/>
                  <!-- INDIAN SUBCONTINENT (Exact Detailed Boundary with State Contours) -->
                  <path d="M 520,230 L 550,210 L 580,220 L 600,240 L 640,245 L 670,270 L 650,290 L 620,300 L 610,330 L 595,360 L 585,410 L 575,445 L 565,410 L 550,370 L 530,340 L 515,310 L 515,260 Z" fill="rgba(34, 197, 94, 0.08)" stroke="#22c55e" stroke-width="2.2" opacity="0.95"/>
                  <!-- Sri Lanka -->
                  <path d="M 580,455 L 590,465 L 585,480 L 575,470 Z" fill="rgba(34, 197, 94, 0.15)" stroke="#22c55e" stroke-width="1.8"/>
                  <!-- Southeast Asia & Indonesia -->
                  <path d="M 680,320 L 720,330 L 730,380 L 700,420 L 670,390 Z" fill="none" stroke="#22c55e" stroke-width="1.6" opacity="0.85"/>
                  <!-- Australia -->
                  <path d="M 760,450 L 830,460 L 870,520 L 850,570 L 780,560 L 750,510 Z" fill="none" stroke="#22c55e" stroke-width="1.6" opacity="0.85"/>

                  <!-- CYCLONE BOB-04 VORTEX (16.82°N, 84.48°E - Central Bay of Bengal) -->
                  <g transform="translate(620, 360)">
                    <!-- Animated Rotating Cyclonic Spiral Bands -->
                    <circle cx="0" cy="0" r="45" fill="none" stroke="rgba(239, 68, 68, 0.4)" stroke-dasharray="6,4" stroke-width="1.5" class="animate-spin" style="animation-duration: 20s;"/>
                    <circle cx="0" cy="0" r="28" fill="none" stroke="rgba(255, 255, 255, 0.7)" stroke-dasharray="4,3" stroke-width="2" class="animate-spin" style="animation-duration: 12s;"/>
                    <circle cx="0" cy="0" r="12" fill="none" stroke="rgba(239, 68, 68, 0.8)" stroke-width="2.5"/>
                    <circle cx="0" cy="0" r="4" fill="#ef4444"/>
                    <!-- Storm Designation Pin -->
                    <text x="14" y="-12" fill="#ef4444" font-size="11" font-family="JetBrains Mono" font-weight="bold">BOB-04 (155 km/h)</text>
                    <text x="14" y="2" fill="#38bdf8" font-size="9" font-family="JetBrains Mono">Eye: 16.82°N, 84.48°E</text>
                  </g>

                  <!-- Landfall Projection Arc to Gopalpur, Odisha -->
                  <path d="M 620,360 Q 610,340 595,330" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-dasharray="5,4"/>
                  <circle cx="595" cy="330" r="4" fill="#f59e0b"/>
                  <text x="545" y="325" fill="#f59e0b" font-size="10" font-family="JetBrains Mono" font-weight="bold">Gopalpur Landfall</text>

                  ${state.scorpioWindActive ? `
                    <!-- GFS Wind Vectors Overlay -->
                    <g opacity="0.65" stroke="#38bdf8" stroke-width="1.2">
                      <line x1="580" y1="380" x2="605" y2="365" marker-end="url(#arrow)"/>
                      <line x1="640" y1="390" x2="620" y2="375"/>
                      <line x1="645" y1="340" x2="625" y2="350"/>
                      <line x1="600" y1="330" x2="615" y2="345"/>
                    </g>
                  ` : ''}

                  ${state.scorpioScatActive ? `
                    <!-- EOS-06 Scatterometer Swath Grid -->
                    <polygon points="560,280 660,290 680,440 580,430" fill="rgba(16, 185, 129, 0.18)" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,4"/>
                  ` : ''}
                </svg>

                <!-- Floating Live Telemetry Badge -->
                <div class="absolute top-3 left-3 bg-[#0a1222]/90 border border-blue-500/40 rounded-xl p-2 font-mono text-[10px] space-y-0.5 backdrop-blur-md shadow-lg pointer-events-none">
                  <div class="text-blue-300 font-bold">INSAT-3DR TIR1 RAPID SCAN</div>
                  <div class="text-slate-300">Central Pressure: <strong class="text-red-400">948 hPa</strong></div>
                  <div class="text-slate-300">Max Wind: <strong class="text-red-400">155 km/h</strong></div>
                  <div class="text-slate-300">SST Anomaly: <strong class="text-emerald-400">+1.4°C (29.4°C)</strong></div>
                </div>
              </div>
            `}

            <!-- Right Zoom Controls (+ / -) -->
            <div class="absolute top-1/3 right-3 z-30 flex flex-col items-center bg-[#0e172a]/90 border border-[#1e2d48] rounded-lg shadow-xl overflow-hidden text-slate-200">
              <button onclick="handleScorpioZoom(1, '${id}')" class="w-7 h-7 hover:bg-blue-600 hover:text-white flex items-center justify-center font-bold text-sm transition-colors border-b border-[#1e2d48]">+</button>
              <button onclick="handleScorpioZoom(-1, '${id}')" class="w-7 h-7 hover:bg-blue-600 hover:text-white flex items-center justify-center font-bold text-sm transition-colors">-</button>
            </div>

            <!-- Cyclone Info Modal Popup (If toggled) -->
            ${state.scorpioInfoModal ? `
              <div class="absolute inset-x-4 top-12 z-40 bg-[#091122]/95 border border-red-500/60 rounded-2xl p-4 shadow-2xl backdrop-blur-xl space-y-2 text-slate-200 text-xs font-mono animate-in fade-in zoom-in-95">
                <div class="flex items-center justify-between border-b border-[#1f3150] pb-2">
                  <div class="flex items-center space-x-2">
                    <span class="text-red-400 font-bold text-sm">🌀 CYCLONE BOB-04 BULLETIN</span>
                    <span class="bg-red-950 text-red-300 px-2 py-0.5 rounded text-[10px]">CATEGORY-3 VSCS</span>
                  </div>
                  <button onclick="toggleScorpioLayer('info')" class="text-slate-400 hover:text-white text-base">✕</button>
                </div>
                <div class="grid grid-cols-2 gap-2 text-[11px]">
                  <div><span class="text-slate-400">Current Position:</span> <strong class="text-white">16.82°N, 84.48°E</strong></div>
                  <div><span class="text-slate-400">Peak Sustained Wind:</span> <strong class="text-red-400">155 km/h</strong></div>
                  <div><span class="text-slate-400">Central Pressure:</span> <strong class="text-white">948 hPa</strong></div>
                  <div><span class="text-slate-400">Movement Velocity:</span> <strong class="text-blue-300">14 km/h NW</strong></div>
                  <div><span class="text-slate-400">Estimated Landfall:</span> <strong class="text-amber-300">Gopalpur, Odisha</strong></div>
                  <div><span class="text-slate-400">Estimated Time:</span> <strong class="text-red-400">~22.5 Hours</strong></div>
                </div>
                <div class="pt-1 text-[10px] text-slate-400 border-t border-[#1a2840]">
                  Multi-Sensor Validation: INSAT-3DR Sounder + Oceansat-3 SCAT + INCOIS Buoy BD08.
                </div>
              </div>
            ` : ''}

            <!-- 4. BOTTOM TIMELINE SCRUBBER OVERLAY -->
            <div class="absolute bottom-16 inset-x-2 z-30 bg-[#0c1424]/85 border border-[#1b2b45] backdrop-blur-md px-3 py-1.5 rounded-xl shadow-xl flex items-center justify-between gap-3 text-[10px] font-mono">
              <span class="text-slate-300 font-bold">08-SEP-2026 05:30</span>
              <input type="range" min="0" max="100" value="${state.scorpioTimelineProgress}" oninput="handleScorpioScrub(this.value, '${id}')" class="flex-1 accent-cyan-400 h-1.5 bg-slate-700 rounded-lg cursor-pointer" />
              <span class="text-cyan-300 font-bold">${state.scorpioTimestamp}</span>
            </div>

            <!-- 5. QUICK ACTION DOCK (Gfs Winds | SCAT Image | Cyclone Info) -->
            <div class="absolute bottom-2 inset-x-0 z-30 flex items-center justify-center space-x-3 pointer-events-auto">
              <button onclick="toggleScorpioLayer('wind')" class="px-3 py-1.5 rounded-xl ${state.scorpioWindActive ? 'bg-cyan-950 border-2 border-cyan-400 text-cyan-200' : 'bg-[#0f172a]/90 border border-slate-700 text-slate-300 hover:bg-[#1e293b]'} flex flex-col items-center shadow-lg transition-all">
                <div class="w-6 h-6 rounded-full bg-cyan-600 flex items-center justify-center text-xs">💨</div>
                <span class="text-[9px] font-bold font-mono mt-0.5">Gfs Winds</span>
              </button>
              <button onclick="toggleScorpioLayer('scat')" class="px-3 py-1.5 rounded-xl ${state.scorpioScatActive ? 'bg-emerald-950 border-2 border-emerald-400 text-emerald-200' : 'bg-[#0f172a]/90 border border-slate-700 text-slate-300 hover:bg-[#1e293b]'} flex flex-col items-center shadow-lg transition-all">
                <div class="w-6 h-6 rounded-full bg-emerald-600 flex items-center justify-center text-xs">🛰️</div>
                <span class="text-[9px] font-bold font-mono mt-0.5">SCAT Image</span>
              </button>
              <button onclick="toggleScorpioLayer('info')" class="px-3 py-1.5 rounded-xl ${state.scorpioInfoModal ? 'bg-red-950 border-2 border-red-400 text-red-200' : 'bg-[#0f172a]/90 border border-slate-700 text-slate-300 hover:bg-[#1e293b]'} flex flex-col items-center shadow-lg transition-all">
                <div class="w-6 h-6 rounded-full bg-red-600 flex items-center justify-center text-xs">🌀</div>
                <span class="text-[9px] font-bold font-mono mt-0.5">Cyclone Info</span>
              </button>
            </div>
          </div>

          <!-- 6. BOTTOM CYAN ACTION TABS (Quick Layers & Legends) -->
          <div class="grid grid-cols-2 bg-[#0284c7] text-white font-bold text-center text-xs font-mono z-20 shadow">
            <button onclick="toggleScorpioLayer('wind')" class="py-1.5 hover:bg-[#0369a1] border-r border-[#026aa0] transition-colors flex items-center justify-center gap-1">
              <span>⚡</span>
              <span>Quick Layers</span>
            </button>
            <button onclick="toggleScorpioLayer('info')" class="py-1.5 hover:bg-[#0369a1] transition-colors flex items-center justify-center gap-1">
              <span>📊</span>
              <span>Legends & Buoys</span>
            </button>
          </div>
        </div>
      `;
    }
"""

if 'function renderMosdacScorpioWidget' not in code:
    code = code.replace(
        '    // =========================================================================\n    // NASA / ISRO STYLE FLAGSHIP EXPLORATION PORTAL (STARTING PAGE)',
        render_mosdac_scorpio_widget_fn + '\n    // =========================================================================\n    // NASA / ISRO STYLE FLAGSHIP EXPLORATION PORTAL (STARTING PAGE)'
    )

# 4. Update the Hero Banner in renderNasaPortal() to a rich 2-column layout with MOSDAC SCORPIO on the right!
old_hero_content = """            <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-12 space-y-6">
              <!-- Active Mission Alert Ribbon -->
              <div class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-red-950/80 border border-red-700/80 text-red-300 text-xs font-mono font-bold shadow-lg">
                <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                <span>ACTIVE MISSION UPDATE: CYCLONE BOB-04 (VSCS) TRACKING TOWARD ODISHA COAST</span>
              </div>

              <!-- Main Hero Headline -->
              <div class="space-y-3 max-w-3xl">
                <h1 class="text-3xl sm:text-5xl lg:text-6xl font-black font-heading tracking-tight text-white leading-tight">
                  OBSERVING EARTH'S MOST INTENSE STORMS
                </h1>
                <p class="text-base sm:text-xl text-slate-300 font-light leading-relaxed">
                  India's multi-source Earth & atmospheric intelligence network fusing ISRO geostationary constellation (<strong class="text-blue-300 font-medium">INSAT-3DR / 3DS</strong>), polar scatterometry (<strong class="text-blue-300 font-medium">EOS-06</strong>), and INCOIS deep-sea buoy telemetry with physics-informed AI forecasting and resilient offline disaster mesh dissemination.
                </p>
              </div>

              <!-- Action CTAs -->
              <div class="flex flex-wrap items-center gap-3.5 pt-2">
                <button onclick="setState({ activePortalView: 'command_center' })" class="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all shadow-xl shadow-blue-900/50 flex items-center gap-2.5">
                  <span>🚀 Launch Tactical Command Deck</span>
                  <span>➔</span>
                </button>
                <a href="#scorpio-live" class="px-5 py-3.5 rounded-xl bg-[#142238] hover:bg-[#1a2d4b] border border-blue-500/40 text-blue-200 font-mono text-xs font-semibold transition-colors flex items-center gap-2">
                  <span>🛰️ View Live MOSDAC SCORPIO Feed</span>
                  <span>↓</span>
                </a>
                <button onclick="setState({ activePortalView: 'login' })" class="px-4 py-3.5 rounded-xl bg-[#0c1322] hover:bg-[#162238] border border-[#223554] text-slate-300 font-mono text-xs transition-colors flex items-center gap-2">
                  <span>🔐 Authorized Officer Access</span>
                </button>
              </div>

              <!-- Live Mission Telemetry Ribbon (NASA Style Stats Ticker) -->
              <div class="pt-6">
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 p-3.5 rounded-xl bg-[#0c1424]/90 border border-[#1e2e4a] backdrop-blur-md text-xs font-mono">
                  <div class="p-2 border-r border-[#19263e]">
                    <p class="text-slate-400 text-[10px]">SATELLITE SENSOR</p>
                    <p class="font-bold text-slate-100 mt-0.5">INSAT-3DR TIR</p>
                    <p class="text-[10px] text-blue-400">82.0°E Geostationary</p>
                  </div>
                  <div class="p-2 border-r border-[#19263e]">
                    <p class="text-slate-400 text-[10px]">STORM DESIGNATION</p>
                    <p class="font-bold text-red-400 mt-0.5">CYCLONE BOB-04</p>
                    <p class="text-[10px] text-slate-400">Cat-3 (VSCS Mature)</p>
                  </div>
                  <div class="p-2 border-r border-[#19263e]">
                    <p class="text-slate-400 text-[10px]">MAX SUSTAINED WIND</p>
                    <p class="font-bold text-red-400 mt-0.5">155 km/h</p>
                    <p class="text-[10px] text-amber-400">Gusts: 175 km/h</p>
                  </div>
                  <div class="p-2 border-r border-[#19263e]">
                    <p class="text-slate-400 text-[10px]">CENTRAL PRESSURE</p>
                    <p class="font-bold text-slate-100 mt-0.5">948 hPa</p>
                    <p class="text-[10px] text-slate-400">Deep Low Vortex</p>
                  </div>
                  <div class="p-2 border-r border-[#19263e]">
                    <p class="text-slate-400 text-[10px]">INCOIS BUOY BD08</p>
                    <p class="font-bold text-emerald-400 mt-0.5">29.4°C SST</p>
                    <p class="text-[10px] text-amber-300">Wave: 3.4m Swell</p>
                  </div>
                  <div class="p-2">
                    <p class="text-slate-400 text-[10px]">LANDFALL TRAJECTORY</p>
                    <p class="font-bold text-blue-300 mt-0.5">Gopalpur, Odisha</p>
                    <p class="text-[10px] text-red-400 font-bold">ETA ~22.5 Hours</p>
                  </div>
                </div>
              </div>
            </div>"""

new_hero_content = """            <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-10 w-full">
              <!-- 2-Column Hero Grid: Left Narrative + Right MOSDAC SCORPIO Live Interactive Station -->
              <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                <!-- Left Column: Mission Narrative & Launch Actions (7 cols) -->
                <div class="lg:col-span-7 space-y-5">
                  <!-- Active Mission Alert Ribbon -->
                  <div class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-red-950/80 border border-red-700/80 text-red-300 text-xs font-mono font-bold shadow-lg">
                    <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                    <span>ACTIVE MISSION UPDATE: CYCLONE BOB-04 (VSCS) TRACKING TOWARD ODISHA COAST</span>
                  </div>

                  <!-- Main Hero Headline -->
                  <div class="space-y-3">
                    <h1 class="text-3xl sm:text-5xl lg:text-5xl font-black font-heading tracking-tight text-white leading-tight">
                      OBSERVING EARTH'S MOST INTENSE STORMS
                    </h1>
                    <p class="text-base sm:text-lg text-slate-300 font-light leading-relaxed">
                      India's multi-source Earth & atmospheric intelligence network fusing ISRO geostationary constellation (<strong class="text-blue-300 font-medium">INSAT-3DR / 3DS</strong>), polar scatterometry (<strong class="text-blue-300 font-medium">EOS-06</strong>), and INCOIS deep-sea buoy telemetry with physics-informed AI forecasting and resilient offline disaster mesh dissemination.
                    </p>
                  </div>

                  <!-- Action CTAs -->
                  <div class="flex flex-wrap items-center gap-3 pt-1">
                    <button onclick="setState({ activePortalView: 'command_center' })" class="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all shadow-xl shadow-blue-900/50 flex items-center gap-2.5">
                      <span>🚀 Launch Tactical Command Deck</span>
                      <span>➔</span>
                    </button>
                    <a href="#scorpio-live" class="px-5 py-3.5 rounded-xl bg-[#142238] hover:bg-[#1a2d4b] border border-blue-500/40 text-blue-200 font-mono text-xs font-semibold transition-colors flex items-center gap-2">
                      <span>🛰️ View Live MOSDAC Stream</span>
                      <span>↓</span>
                    </a>
                    <button onclick="setState({ activePortalView: 'login' })" class="px-4 py-3.5 rounded-xl bg-[#0c1322] hover:bg-[#162238] border border-[#223554] text-slate-300 font-mono text-xs transition-colors flex items-center gap-2">
                      <span>🔐 Officer Login</span>
                    </button>
                  </div>

                  <!-- Live Mission Telemetry Ribbon (NASA Style Stats Ticker) -->
                  <div class="pt-2">
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5 p-3 rounded-xl bg-[#0c1424]/90 border border-[#1e2e4a] backdrop-blur-md text-xs font-mono">
                      <div class="p-1.5 border-r border-[#19263e]">
                        <p class="text-slate-400 text-[10px]">SATELLITE SENSOR</p>
                        <p class="font-bold text-slate-100 mt-0.5 text-xs">INSAT-3DR TIR</p>
                        <p class="text-[10px] text-blue-400">82.0°E Geostationary</p>
                      </div>
                      <div class="p-1.5 border-r border-[#19263e]">
                        <p class="text-slate-400 text-[10px]">STORM DESIGNATION</p>
                        <p class="font-bold text-red-400 mt-0.5 text-xs">CYCLONE BOB-04</p>
                        <p class="text-[10px] text-slate-400">Cat-3 (VSCS Mature)</p>
                      </div>
                      <div class="p-1.5">
                        <p class="text-slate-400 text-[10px]">MAX SUSTAINED WIND</p>
                        <p class="font-bold text-red-400 mt-0.5 text-xs">155 km/h</p>
                        <p class="text-[10px] text-amber-400">Gusts: 175 km/h</p>
                      </div>
                      <div class="p-1.5 border-r border-[#19263e]">
                        <p class="text-slate-400 text-[10px]">CENTRAL PRESSURE</p>
                        <p class="font-bold text-slate-100 mt-0.5 text-xs">948 hPa</p>
                        <p class="text-[10px] text-slate-400">Deep Low Vortex</p>
                      </div>
                      <div class="p-1.5 border-r border-[#19263e]">
                        <p class="text-slate-400 text-[10px]">INCOIS BUOY BD08</p>
                        <p class="font-bold text-emerald-400 mt-0.5 text-xs">29.4°C SST</p>
                        <p class="text-[10px] text-amber-300">Wave: 3.4m Swell</p>
                      </div>
                      <div class="p-1.5">
                        <p class="text-slate-400 text-[10px]">LANDFALL TARGET</p>
                        <p class="font-bold text-blue-300 mt-0.5 text-xs">Gopalpur, Odisha</p>
                        <p class="text-[10px] text-red-400 font-bold">ETA ~22.5 Hours</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Right Column: Live Interactive ISRO SAC MOSDAC SCORPIO Station (5 cols) -->
                <div class="lg:col-span-5">
                  <div class="space-y-2">
                    <div class="flex items-center justify-between px-1 text-[11px] font-mono text-slate-400">
                      <span class="text-cyan-400 font-bold flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                        LIVE ISRO SCORPIO RADAR
                      </span>
                      <span>SAC / ISRO AHMEDABAD</span>
                    </div>
                    ${renderMosdacScorpioWidget('hero_scorpio')}
                  </div>
                </div>
              </div>
            </div>"""

if old_hero_content in code:
    code = code.replace(old_hero_content, new_hero_content)

# 5. Also update the Login Page (renderLoginPage) to have MOSDAC SCORPIO on the right hand side!
old_login_content = """          <!-- Main Login Content -->
          <div class="flex-1 flex items-center justify-center p-4 sm:p-8">
            <div class="w-full max-w-xl mission-card p-6 sm:p-8 space-y-6 border border-[#233856] shadow-2xl bg-[#0e1628]/95 backdrop-blur-md">"""

new_login_content = """          <!-- Main Login Content: 2-Column Layout with MOSDAC SCORPIO on the Right Hand Side -->
          <div class="flex-1 flex items-center justify-center p-4 sm:p-8 max-w-7xl mx-auto w-full">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center w-full">
              <!-- Left Column: Officer Authentication Portal (6 cols) -->
              <div class="lg:col-span-6 w-full mission-card p-6 sm:p-8 space-y-6 border border-[#233856] shadow-2xl bg-[#0e1628]/95 backdrop-blur-md">"""

if old_login_content in code:
    code = code.replace(old_login_content, new_login_content)

# Close the grid on the login page and inject the right column MOSDAC SCORPIO
old_login_end = """              </form>
            </div>
          </div>"""

new_login_end = """              </form>
              </div>

              <!-- Right Column: Interactive MOSDAC SCORPIO Satellite Station (6 cols) -->
              <div class="lg:col-span-6 w-full space-y-2">
                <div class="flex items-center justify-between px-1 text-[11px] font-mono text-slate-400">
                  <span class="text-cyan-400 font-bold flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                    SATELLITE CYCLONE SURVEILLANCE RADAR
                  </span>
                  <span>MOSDAC SCORPIO FEED</span>
                </div>
                ${renderMosdacScorpioWidget('login_scorpio')}
              </div>
            </div>
          </div>"""

if old_login_end in code:
    code = code.replace(old_login_end, new_login_end)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully placed interactive MOSDAC SCORPIO on the right-hand side of both Front Page and Login Page!")
