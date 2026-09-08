import os
import re

# Read current update_portal.py
with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Make sure state has native preface variables
if 'prefaceActiveLayer' not in code:
    code = code.replace(
        "activePortalView: 'portal',",
        """activePortalView: 'portal',
      prefaceActiveLayer: 'tir1', // 'tir1' | 'radar' | 'buoy' | 'trajectory' | 'wind' | 'surge' | 'sst'
      prefaceTimeHour: 15,
      prefaceTimeMinute: 15,
      prefacePlaying: false,
      prefaceCoords: "16° 49' N  84° 28' E",
      prefaceTargetName: "Cyclone BOB-04 Vortex (Eye Center)",
      prefaceWindKmh: 155,
      prefacePressureHpa: 948,"""
    )

# Add native preface controller functions to javascript
native_preface_js = """
    // =========================================================================
    // NATIVE PREFACE & LOGIN INTERACTIVE ENGINE (100% BESPOKE & RESPONSIVE)
    // =========================================================================
    let prefacePlaybackTimer = null;

    function setPrefaceLayer(layer) {
      state.prefaceActiveLayer = layer;
      renderApp();
    }

    function togglePrefacePlayback() {
      state.prefacePlaying = !state.prefacePlaying;
      if (state.prefacePlaying) {
        if (prefacePlaybackTimer) clearInterval(prefacePlaybackTimer);
        prefacePlaybackTimer = setInterval(() => {
          stepPrefaceTime(15);
        }, 1100);
      } else {
        if (prefacePlaybackTimer) clearInterval(prefacePlaybackTimer);
        prefacePlaybackTimer = null;
      }
      renderApp();
    }

    function stepPrefaceTime(deltaMinutes) {
      let totalMins = state.prefaceTimeHour * 60 + state.prefaceTimeMinute + deltaMinutes;
      if (totalMins < 5 * 60 + 30) totalMins = 24 * 60 - 15;
      if (totalMins >= 24 * 60) totalMins = 5 * 60 + 30;
      state.prefaceTimeHour = Math.floor(totalMins / 60);
      state.prefaceTimeMinute = totalMins % 60;
      renderApp();
    }

    function selectPrefaceTarget(target) {
      if (target === 'cyclone') {
        state.prefaceCoords = "16° 49' N  84° 28' E";
        state.prefaceTargetName = "Cyclone BOB-04 Vortex (Eye Center)";
        focusGlobeTarget('cyclone');
      } else if (target === 'gopalpur') {
        state.prefaceCoords = "19° 15' N  84° 54' E";
        state.prefaceTargetName = "Gopalpur Landfall Target (Odisha Coast)";
        focusGlobeTarget('cyclone');
      } else if (target === 'insat') {
        state.prefaceCoords = "00° 00' N  82° 00' E";
        state.prefaceTargetName = "INSAT-3DR Geostationary Orbit (35,786 km)";
        focusGlobeTarget('insat');
      } else if (target === 'india') {
        state.prefaceCoords = "20° 35' N  78° 57' E";
        state.prefaceTargetName = "Indian Subcontinent & Bay of Bengal";
        focusGlobeTarget('india');
      } else if (target === 'global') {
        state.prefaceCoords = "00° 00' N  80° 00' E";
        state.prefaceTargetName = "Global Earth Constellation Overview";
        focusGlobeTarget('global');
      }
      renderApp();
    }
"""

if 'function setPrefaceLayer' not in code:
    code = code.replace(
        '    // =========================================================================\n    // ISRO SAC MOSDAC SCORPIO INTERACTIVE WIDGET ENGINE',
        native_preface_js + '\n    // =========================================================================\n    // ISRO SAC MOSDAC SCORPIO INTERACTIVE WIDGET ENGINE'
    )

# Update mountAllGlobes to target prefaceInteractiveGlobe and loginInteractiveGlobe
if 'prefaceInteractiveGlobe' not in code:
    code = code.replace(
        "      if (document.getElementById('nasaHeroGlobeContainer') && state.heroBgMode === 'globe3d') {\n        initInteractiveGlobe('nasaHeroGlobeContainer', { initialDistance: 2.35 });\n      }",
        """      if (document.getElementById('prefaceInteractiveGlobe')) {
        initInteractiveGlobe('prefaceInteractiveGlobe', { initialDistance: 2.4 });
      }
      if (document.getElementById('loginInteractiveGlobe')) {
        initInteractiveGlobe('loginInteractiveGlobe', { initialDistance: 2.1 });
      }
      if (document.getElementById('nasaHeroGlobeContainer')) {
        initInteractiveGlobe('nasaHeroGlobeContainer', { initialDistance: 2.35 });
      }"""
    )

# Now define the completely native, interactive renderNasaPortal()
native_preface_html = """    function renderNasaPortal() {
      const cyc = state.cyclone;
      const obs = state.liveObservation;
      const hStr = String(state.prefaceTimeHour).padStart(2, '0');
      const mStr = String(state.prefaceTimeMinute).padStart(2, '0');
      const isFlat = state.pixelWidgetView === 'flat';

      return `
        <div class="min-h-screen text-slate-100 flex flex-col font-sans operational-bg select-none">
          
          <!-- 1. OFFICIAL STRATEGIC HIERARCHY BANNER (PRD ALIGNED) -->
          <div class="bg-[#050811] border-b border-[#141f33] px-4 sm:px-8 py-2 text-[11px] font-mono text-slate-400 flex flex-wrap items-center justify-between gap-2 z-50">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-sm">🇮🇳</span>
              <span class="px-2.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-700 font-bold tracking-tight">
                PRIMARY: AI CYCLONE INTELLIGENCE SYSTEM
              </span>
              <span class="text-slate-600 hidden sm:inline">•</span>
              <span class="px-2.5 py-0.5 rounded bg-red-950/90 text-red-300 border border-red-700/80 font-bold tracking-tight">
                🛡️ ADDITIONAL: PUKAR RESILIENT EMERGENCY INFRASTRUCTURE
              </span>
            </div>
            <div class="hidden lg:flex items-center space-x-3 text-slate-300 text-[11px]">
              <span class="text-slate-400">ISRO SAC • IMD RSMC • INCOIS</span>
              <span class="text-slate-700">|</span>
              <button onclick="setState({ activePortalView: 'login' })" class="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1">
                <span>🔐</span>
                <span>Officer Clearance Gateway</span>
              </button>
            </div>
          </div>

          <!-- 2. INSTITUTIONAL NAVIGATION HEADER -->
          <header class="h-20 bg-[#070c18]/90 backdrop-blur-xl border-b border-[#18263d] px-4 sm:px-8 flex items-center justify-between sticky top-0 z-40">
            <div class="flex items-center space-x-3.5">
              <div class="w-11 h-11 rounded-2xl bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-950 border border-blue-500/50 flex items-center justify-center text-blue-300 font-bold text-2xl shadow-xl shadow-blue-950/60">
                🌀
              </div>
              <div>
                <div class="flex items-center space-x-2">
                  <span class="font-black text-xl sm:text-2xl tracking-tight text-white font-heading">
                    CHAKRAVYOOH
                  </span>
                  <span class="text-[10px] font-mono font-bold text-blue-300 bg-blue-950 border border-blue-700 px-2 py-0.5 rounded-full">
                    EARTH OBSERVATORY
                  </span>
                </div>
                <p class="text-[11px] font-mono text-slate-400">
                  AI-Powered Tropical Cyclone Intelligence Platform • Enhanced with Pukar Resilient Emergency Mesh
                </p>
              </div>
            </div>

            <!-- Header Quick Anchors -->
            <nav class="hidden xl:flex items-center space-x-1 text-xs font-semibold text-slate-300 font-mono">
              <button onclick="selectPrefaceTarget('cyclone')" class="px-3 py-2 rounded-xl hover:bg-[#121c30] hover:text-white transition-colors flex items-center gap-1.5">
                <span>🌀</span>
                <span>Cyclone BOB-04</span>
              </button>
              <button onclick="selectPrefaceTarget('insat')" class="px-3 py-2 rounded-xl hover:bg-[#121c30] hover:text-white transition-colors flex items-center gap-1.5">
                <span>🛰️</span>
                <span>INSAT-3DR Orbit</span>
              </button>
              <a href="#widgets-section" class="px-3 py-2 rounded-xl hover:bg-[#121c30] hover:text-white transition-colors flex items-center gap-1.5">
                <span>📱</span>
                <span>Pixel Weather Widgets</span>
              </a>
              <button onclick="setState({ activePortalView: 'command_center', activeScreen: 'screen4_resilience' })" class="px-3 py-2 rounded-xl hover:bg-[#121c30] hover:text-white transition-colors flex items-center gap-1.5 text-red-300">
                <span>🛡️</span>
                <span>Pukar Mesh</span>
              </button>
            </nav>

            <!-- Navigation Actions -->
            <div class="flex items-center space-x-3">
              <button onclick="setState({ activePortalView: 'login' })" class="px-4 py-2.5 rounded-xl bg-[#121c2e] hover:bg-[#1a2942] border border-[#20324e] text-slate-200 text-xs font-mono font-semibold transition-all flex items-center gap-1.5 shadow-sm">
                <span>🔐</span>
                <span class="hidden sm:inline">Officer Login</span>
              </button>
              <button onclick="setState({ activePortalView: 'command_center' })" class="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold font-mono transition-all shadow-lg shadow-blue-900/50 flex items-center gap-2">
                <span>Launch Tactical Deck</span>
                <span>➔</span>
              </button>
            </div>
          </header>

          <!-- 3. FULL-BLEED NATIVE 3D INTERACTIVE PREFACE HERO -->
          <section class="relative min-h-[720px] lg:min-h-[760px] flex items-center overflow-hidden border-b border-[#1b2b45] bg-[#040813]">
            <!-- 100% Native WebGL 3D Interactive Earth Canvas (Drag, Rotate, Zoom) -->
            <div id="prefaceInteractiveGlobe" class="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing z-0"></div>

            <!-- Soft Vignette Lighting to Preserve High Contrast -->
            <div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#040813]/95 via-[#040813]/75 lg:via-[#040813]/40 to-transparent z-[1]"></div>
            <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#040813] via-transparent to-[#040813]/70 z-[1]"></div>

            <!-- FLOATING GLASSMORPHIC CONTROLS: LEFT SIDEBAR (Layers & Models) -->
            <div class="absolute top-6 left-6 z-20 w-60 rounded-2xl bg-[#070d1a]/85 border border-[#1b2b45] backdrop-blur-xl p-3.5 shadow-2xl space-y-3 hidden md:block">
              <div class="flex items-center justify-between border-b border-[#162338] pb-2 text-[11px] font-mono font-bold">
                <span class="text-blue-400">METEOROLOGICAL LAYERS</span>
                <span class="text-emerald-400 text-[10px] animate-pulse">● LIVE FUSION</span>
              </div>

              <!-- Layer Buttons -->
              <div class="space-y-1 text-xs font-sans">
                <button onclick="setPrefaceLayer('tir1')" class="w-full px-2.5 py-2 rounded-xl flex items-center justify-between text-left ${state.prefaceActiveLayer === 'tir1' ? 'bg-gradient-to-r from-blue-950 to-[#122340] border border-blue-600/80 text-white font-semibold shadow' : 'text-slate-300 hover:bg-[#10192a]'} transition-all">
                  <div class="flex items-center space-x-2">
                    <span>🛰️</span>
                    <span>INSAT-3DR Multispectral</span>
                  </div>
                  <span class="text-[10px] font-mono text-blue-400">TIR-1</span>
                </button>

                <button onclick="setPrefaceLayer('radar')" class="w-full px-2.5 py-2 rounded-xl flex items-center justify-between text-left ${state.prefaceActiveLayer === 'radar' ? 'bg-gradient-to-r from-blue-950 to-[#122340] border border-blue-600/80 text-white font-semibold shadow' : 'text-slate-300 hover:bg-[#10192a]'} transition-all">
                  <div class="flex items-center space-x-2">
                    <span>📡</span>
                    <span>Doppler Radar Network</span>
                  </div>
                  <span class="text-[10px] font-mono text-emerald-400">DWR Array</span>
                </button>

                <button onclick="setPrefaceLayer('wind')" class="w-full px-2.5 py-2 rounded-xl flex items-center justify-between text-left ${state.prefaceActiveLayer === 'wind' ? 'bg-gradient-to-r from-blue-950 to-[#122340] border border-blue-600/80 text-white font-semibold shadow' : 'text-slate-300 hover:bg-[#10192a]'} transition-all">
                  <div class="flex items-center space-x-2">
                    <span>💨</span>
                    <span>EOS-06 Vector Winds</span>
                  </div>
                  <span class="text-[10px] font-mono text-cyan-400">148 km/h</span>
                </button>

                <button onclick="setPrefaceLayer('buoy')" class="w-full px-2.5 py-2 rounded-xl flex items-center justify-between text-left ${state.prefaceActiveLayer === 'buoy' ? 'bg-gradient-to-r from-blue-950 to-[#122340] border border-blue-600/80 text-white font-semibold shadow' : 'text-slate-300 hover:bg-[#10192a]'} transition-all">
                  <div class="flex items-center space-x-2">
                    <span>🌊</span>
                    <span>INCOIS Buoys (BD08/10)</span>
                  </div>
                  <span class="text-[10px] font-mono text-amber-300">3.4m Swell</span>
                </button>

                <button onclick="setPrefaceLayer('trajectory')" class="w-full px-2.5 py-2 rounded-xl flex items-center justify-between text-left ${state.prefaceActiveLayer === 'trajectory' ? 'bg-gradient-to-r from-blue-950 to-[#122340] border border-blue-600/80 text-white font-semibold shadow' : 'text-slate-300 hover:bg-[#10192a]'} transition-all">
                  <div class="flex items-center space-x-2">
                    <span>🌪️</span>
                    <span>Landfall Forecast Arc</span>
                  </div>
                  <span class="text-[10px] font-mono text-red-400 font-bold">Gopalpur</span>
                </button>
              </div>

              <!-- Pukar Resilience Badge -->
              <div class="p-2 rounded-xl bg-red-950/40 border border-red-800/50 text-[10px] font-mono text-red-300 space-y-0.5">
                <div class="flex items-center justify-between">
                  <span class="font-bold">PUKAR OFFLINE MESH</span>
                  <span class="text-emerald-400">ARMED</span>
                </div>
                <p class="text-slate-400 text-[9px] leading-tight">Zero-cellular BLE & Wi-Fi Aware store-and-forward relay ready.</p>
              </div>
            </div>

            <!-- FLOATING GLASSMORPHIC CONTROLS: RIGHT CAMERA & PRESETS TOOLBAR -->
            <div class="absolute top-6 right-6 z-20 flex flex-col items-end gap-2.5">
              <!-- Quick Camera Targets -->
              <div class="flex items-center gap-1.5 bg-[#070d1a]/90 border border-[#1b2b45] backdrop-blur-xl p-1.5 rounded-2xl shadow-2xl text-xs font-mono">
                <button onclick="selectPrefaceTarget('cyclone')" class="px-3 py-1.5 rounded-xl bg-red-950/80 hover:bg-red-900 border border-red-700/70 text-red-300 font-semibold transition-colors flex items-center gap-1.5">
                  <span>🌀</span>
                  <span>Focus Cyclone</span>
                </button>
                <button onclick="selectPrefaceTarget('insat')" class="px-3 py-1.5 rounded-xl bg-blue-950/80 hover:bg-blue-900 border border-blue-700/70 text-blue-300 font-semibold transition-colors flex items-center gap-1.5">
                  <span>🛰️</span>
                  <span>INSAT-3DR</span>
                </button>
                <button onclick="selectPrefaceTarget('gopalpur')" class="px-3 py-1.5 rounded-xl bg-[#131f33] hover:bg-[#1c2c47] text-slate-200 transition-colors">
                  <span>📍</span>
                  <span>Gopalpur</span>
                </button>
                <button onclick="selectPrefaceTarget('india')" class="px-3 py-1.5 rounded-xl bg-[#131f33] hover:bg-[#1c2c47] text-slate-200 transition-colors">
                  <span>🇮🇳</span>
                  <span>India</span>
                </button>
                <button onclick="toggleGlobeAutoRotate()" class="w-8 h-8 rounded-xl bg-[#131f33] hover:bg-[#1c2c47] text-slate-300 flex items-center justify-center transition-colors" title="Toggle Auto-Rotation">
                  ${state.globeAutoRotate ? '⏸' : '▶'}
                </button>
              </div>

              <!-- Satellite Telemetry Badge -->
              <div class="p-3 rounded-2xl bg-[#070d1a]/90 border border-[#1b2b45] backdrop-blur-xl text-right font-mono text-[11px] space-y-1 shadow-2xl text-slate-300 hidden sm:block">
                <div class="text-blue-400 font-bold">ORBITAL TELEMETRY</div>
                <div class="text-slate-400">Eye: <strong class="text-red-400">16.82°N, 84.48°E</strong></div>
                <div class="text-slate-400">Pressure: <strong class="text-white">948 hPa</strong> • Winds: <strong class="text-red-400">155 km/h</strong></div>
                <div class="text-slate-400">Cadence: <strong class="text-emerald-400">15-min Rapid Imager</strong></div>
              </div>
            </div>

            <!-- HERO CENTER CONTENT & NARRATIVE (PRD MASTER STATEMENT) -->
            <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-16 w-full pointer-events-none">
              <div class="max-w-2xl space-y-6 pointer-events-auto">
                
                <!-- Active Mission Alert Ribbon -->
                <div class="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-red-950/85 border border-red-700 text-red-300 text-xs font-mono font-bold shadow-2xl">
                  <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                  <span>MISSION LIVE: CYCLONE BOB-04 (VSCS) TRACKING TOWARD ODISHA COAST</span>
                </div>

                <!-- Main Hero Headline -->
                <div class="space-y-3">
                  <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black font-heading tracking-tight text-white leading-tight drop-shadow-lg">
                    AI-POWERED TROPICAL CYCLONE INTELLIGENCE
                  </h1>
                  <p class="text-base sm:text-lg text-slate-200 font-light leading-relaxed drop-shadow">
                    An AI-powered tropical cyclone intelligence system that uses multi-source satellite and atmospheric data to identify cyclone patterns, classify their evolution, predict future movement, and generate geospatial risk assessments.
                  </p>
                  <p class="text-xs sm:text-sm text-blue-300/90 font-mono leading-relaxed border-l-2 border-red-500 pl-3">
                    Enhanced using <strong class="text-red-300 font-semibold">Pukar's</strong> resilient communication and emergency-response infrastructure for real-time and offline warning delivery in vulnerable regions.
                  </p>
                </div>

                <!-- Action CTAs -->
                <div class="flex flex-wrap items-center gap-3.5 pt-2">
                  <button onclick="setState({ activePortalView: 'command_center' })" class="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all shadow-2xl shadow-blue-900/60 flex items-center gap-2.5">
                    <span>🚀 Launch Tactical Command Deck</span>
                    <span>➔</span>
                  </button>
                  <button onclick="selectPrefaceTarget('cyclone')" class="px-5 py-3.5 rounded-xl bg-[#142238]/90 hover:bg-[#1c2f4d] border border-blue-500/50 text-blue-200 font-mono text-xs font-semibold backdrop-blur-md transition-colors flex items-center gap-2">
                    <span>🌀 Inspect 3D Storm Core</span>
                  </button>
                  <button onclick="setState({ activePortalView: 'login' })" class="px-4 py-3.5 rounded-xl bg-[#090e1a]/90 hover:bg-[#141f33] border border-[#1e2e48] text-slate-300 font-mono text-xs backdrop-blur-md transition-colors flex items-center gap-2">
                    <span>🔐 Officer Access</span>
                  </button>
                </div>

                <!-- The Master Pitch Quote -->
                <div class="pt-2 text-xs font-mono text-slate-400 italic">
                  <span>"The AI tells us what is coming. Pukar helps people respond when it arrives."</span>
                </div>
              </div>
            </div>

            <!-- FLOATING GLASSMORPHIC CONTROLS: BOTTOM TIMELINE SCRUBBER & TELEMETRY -->
            <div class="absolute bottom-6 inset-x-6 z-20 flex flex-col sm:flex-row items-center justify-between gap-3 pointer-events-none select-none">
              <!-- Coordinates Telemetry Box (Bottom-Left) -->
              <div class="pointer-events-auto px-4 py-2 rounded-2xl bg-[#070d1a]/90 border border-[#1b2b45] backdrop-blur-xl text-xs font-mono text-slate-300 shadow-2xl flex items-center gap-2.5">
                <span class="w-2 h-2 rounded-full bg-red-400 animate-ping"></span>
                <span class="font-bold text-white">${state.prefaceCoords}</span>
                <span class="text-slate-600">|</span>
                <span class="text-blue-400 text-[11px]">${state.prefaceTargetName}</span>
              </div>

              <!-- Interactive Playback & 15-Minute Cadence Stepper (Center-Bottom) -->
              <div class="pointer-events-auto flex items-center gap-3 bg-[#070d1a]/90 border border-[#1b2b45] backdrop-blur-xl px-4 py-2 rounded-2xl shadow-2xl font-mono text-xs">
                <button onclick="togglePrefacePlayback()" class="w-8 h-8 rounded-xl ${state.prefacePlaying ? 'bg-amber-600 hover:bg-amber-500' : 'bg-blue-600 hover:bg-blue-500'} text-white flex items-center justify-center transition-colors shadow">
                  ${state.prefacePlaying ? '⏸' : '▶'}
                </button>
                <div class="text-center font-bold text-slate-200 px-2 border-r border-[#1a283f]">
                  <span>08-SEP-2026</span>
                </div>
                <div class="flex items-center space-x-1">
                  <div class="text-center">
                    <button onclick="stepPrefaceTime(60)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▲</button>
                    <span class="font-bold text-white text-sm">${hStr}</span>
                    <button onclick="stepPrefaceTime(-60)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▼</button>
                  </div>
                  <span class="text-slate-400 font-bold">:</span>
                  <div class="text-center">
                    <button onclick="stepPrefaceTime(15)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▲</button>
                    <span class="font-bold text-blue-400 text-sm">${mStr}</span>
                    <button onclick="stepPrefaceTime(-15)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▼</button>
                  </div>
                </div>
                <span class="text-slate-600">|</span>
                <span class="text-[10px] text-slate-400 uppercase">15m RAPID SCAN</span>
              </div>

              <!-- Live Storm Metrics Box (Bottom-Right) -->
              <div class="pointer-events-auto px-4 py-2 rounded-2xl bg-[#070d1a]/90 border border-[#1b2b45] backdrop-blur-xl text-xs font-mono text-slate-300 shadow-2xl flex items-center gap-3">
                <div>
                  <span class="text-slate-500 text-[10px] block">WIND SPEED</span>
                  <span class="font-bold text-red-400">155 km/h</span>
                </div>
                <div class="h-6 w-px bg-slate-800"></div>
                <div>
                  <span class="text-slate-500 text-[10px] block">PRESSURE</span>
                  <span class="font-bold text-white">948 hPa</span>
                </div>
                <div class="h-6 w-px bg-slate-800"></div>
                <div>
                  <span class="text-slate-500 text-[10px] block">LANDFALL ETA</span>
                  <span class="font-bold text-amber-300">~22.5h</span>
                </div>
              </div>
            </div>
          </section>

          <!-- 4. TARAS BOIKO PIXEL-ART WEATHER & CYCLONE WIDGETS DECK (3D ISOMETRIC) -->
          <div id="widgets-section">
            ${renderPixelWeatherWidgetsDeck()}
          </div>

          <!-- 5. CORE PROBLEM STATEMENT ARCHITECTURE: MULTI-SOURCE FUSION TO PUKAR MESH -->
          <section class="max-w-7xl mx-auto px-4 sm:px-8 py-10 space-y-6">
            <div class="border-b border-[#1b2b45] pb-4 flex flex-col sm:flex-row sm:items-end justify-between gap-2">
              <div>
                <span class="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">END-TO-END PIPELINE ARCHITECTURE</span>
                <h2 class="text-2xl sm:text-3xl font-bold font-heading text-white mt-1">
                  How Multi-Source Intelligence Reaches Vulnerable Coastal Communities
                </h2>
              </div>
              <button onclick="setState({ activePortalView: 'command_center', activeScreen: 'screen2_ai' })" class="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1">
                <span>View Live AI Pipeline</span>
                <span>➔</span>
              </button>
            </div>

            <!-- 4 Architecture Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 text-xs font-mono">
              <!-- Step 1: Ingestion -->
              <div class="mission-card p-5 space-y-3 flex flex-col justify-between">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded">STEP 01</span>
                    <span class="text-[10px] text-emerald-400">● 4 FEEDS ONLINE</span>
                  </div>
                  <h3 class="text-sm font-bold text-white">Multi-Source Ingestion</h3>
                  <p class="text-slate-300 text-xs font-sans leading-relaxed">
                    Fuses INSAT-3DR/3DS 6-channel Imager, EOS-06 Scatterometer Ku-band ocean surface wind vectors, and INCOIS deep-sea moored buoys (BD08/10).
                  </p>
                </div>
                <div class="mission-card-subtle p-2 text-slate-400 text-[11px]">
                  Cadence: 15-minute rapid scan
                </div>
              </div>

              <!-- Step 2: AI Engine -->
              <div class="mission-card p-5 space-y-3 flex flex-col justify-between">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded">STEP 02</span>
                    <span class="text-[10px] text-emerald-400">● 94% CONFIDENCE</span>
                  </div>
                  <h3 class="text-sm font-bold text-white">AI Detection & Prediction</h3>
                  <p class="text-slate-300 text-xs font-sans leading-relaxed">
                    Identifies tropical vortex patterns, classifies developmental maturity (Category-3 VSCS), and predicts 24-hour landfall trajectory with cone of uncertainty.
                  </p>
                </div>
                <div class="mission-card-subtle p-2 text-slate-400 text-[11px]">
                  Output: Trajectory to Gopalpur
                </div>
              </div>

              <!-- Step 3: Risk Engine -->
              <div class="mission-card p-5 space-y-3 flex flex-col justify-between">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold bg-red-950 text-red-300 border border-red-800 px-2 py-0.5 rounded">STEP 03</span>
                    <span class="text-[10px] text-red-400">● ZONE A: EXTREME</span>
                  </div>
                  <h3 class="text-sm font-bold text-white">Geospatial Risk Mapping</h3>
                  <p class="text-slate-300 text-xs font-sans leading-relaxed">
                    Translates meteorological trajectory into actionable danger zones (Zone A: 92/100 Extreme, Zone B: 74/100 High) triggering standardized event alarms.
                  </p>
                </div>
                <div class="mission-card-subtle p-2 text-slate-400 text-[11px]">
                  Event: CYCLONE_RISK_UPDATED
                </div>
              </div>

              <!-- Step 4: Pukar Resilience -->
              <div class="mission-card p-5 space-y-3 flex flex-col justify-between border-l-2 border-red-600">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold bg-red-950 text-red-300 border border-red-800 px-2 py-0.5 rounded">STEP 04</span>
                    <span class="text-[10px] text-emerald-400">● MESH ARMED</span>
                  </div>
                  <h3 class="text-sm font-bold text-white">Pukar Offline Mesh Delivery</h3>
                  <p class="text-slate-300 text-xs font-sans leading-relaxed">
                    When high winds destroy cellular towers and electrical power grids, Pukar's store-and-forward peer-to-peer mesh ensures life-saving warnings reach citizens.
                  </p>
                </div>
                <div class="mission-card-subtle p-2 text-red-300 text-[11px] font-bold">
                  Survives Network Collapse ✓
                </div>
              </div>
            </div>
          </section>

          <!-- 6. EXPLORATION FOOTER -->
          <footer class="mt-auto border-t border-[#1b2b45] bg-[#070b14] py-10 px-4 sm:px-8 text-slate-400 text-xs font-mono">
            <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
              <div class="flex items-center space-x-2">
                <span class="text-base">🌀</span>
                <span class="text-white font-bold text-sm">CHAKRAVYOOH</span>
                <span class="text-slate-600">•</span>
                <span>Project Beacon Tropical Cyclone Intelligence Platform</span>
              </div>
              <div class="text-[11px] text-slate-500">
                Joint Operations: ISRO SAC • IMD RSMC New Delhi • INCOIS Hyderabad • NDRF Command
              </div>
            </div>
          </footer>
        </div>
      `;
    }
"""

# Replace renderNasaPortal in update_portal.py
portal_start = "    function renderNasaPortal() {"
portal_end = "    function renderLoginPage() {"

idx_start = code.find(portal_start)
idx_end = code.find(portal_end)

if idx_start != -1 and idx_end != -1:
    code = code[:idx_start] + native_preface_html + '\n\n    ' + code[idx_end:]

# Now replace renderLoginPage() with a stunning interactive 2-column layout!
native_login_html = """    function renderLoginPage() {
      return `
        <div class="min-h-screen text-slate-100 flex flex-col font-sans operational-bg select-none">
          <!-- Top Flag Strip -->
          <div class="bg-[#050811] border-b border-[#141f33] px-4 py-2 text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span>🇮🇳</span>
              <span class="font-bold text-slate-200">GOVERNMENT OF INDIA</span>
              <span class="text-slate-600">•</span>
              <span class="text-blue-400">CHAKRAVYOOH SECURE ACCESS GATEWAY</span>
            </div>
            <button onclick="setState({ activePortalView: 'portal' })" class="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold transition-colors">
              <span>←</span>
              <span>Back to Exploration Portal</span>
            </button>
          </div>

          <!-- Main Login Content: 2-Column Responsive Layout -->
          <div class="flex-1 flex items-center justify-center p-4 sm:p-8 max-w-7xl mx-auto w-full">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center w-full">
              
              <!-- LEFT COLUMN: Officer Authentication Portal (6 cols) -->
              <div class="lg:col-span-6 w-full mission-card p-6 sm:p-8 space-y-6 border border-[#233856] shadow-2xl bg-[#0e1628]/95 backdrop-blur-xl">
                <!-- Header -->
                <div class="flex items-center justify-between border-b border-[#1b2b45] pb-4">
                  <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-xl bg-blue-900/60 border border-blue-500/50 flex items-center justify-center text-blue-400 font-bold text-xl">
                      🌀
                    </div>
                    <div>
                      <h2 class="text-base font-bold text-white font-heading tracking-tight">OFFICER AUTHENTICATION</h2>
                      <p class="text-[10px] font-mono text-slate-400">Cyclone Warning & Resilient Mesh Portal</p>
                    </div>
                  </div>
                  <span class="px-2.5 py-1 rounded bg-blue-950 border border-blue-800 text-[10px] font-mono text-blue-300 font-bold">
                    RESTRICTED
                  </span>
                </div>

                <!-- Role Switcher Tabs -->
                <div class="space-y-1.5">
                  <label class="text-xs font-mono font-semibold text-slate-300">SELECT AUTHENTICATION CLEARANCE:</label>
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-1.5 bg-[#080d18] p-1 rounded-xl border border-[#1b2b45] text-xs font-mono">
                    <button onclick="handleSelectLoginRole('ndrf')" class="py-2 px-2 rounded-lg font-medium transition-colors ${state.loginRole === 'ndrf' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'}">
                      NDRF
                    </button>
                    <button onclick="handleSelectLoginRole('imd')" class="py-2 px-2 rounded-lg font-medium transition-colors ${state.loginRole === 'imd' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'}">
                      IMD / ISRO
                    </button>
                    <button onclick="handleSelectLoginRole('district')" class="py-2 px-2 rounded-lg font-medium transition-colors ${state.loginRole === 'district' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'}">
                      SDMA
                    </button>
                    <button onclick="handleSelectLoginRole('guest')" class="py-2 px-2 rounded-lg font-medium transition-colors ${state.loginRole === 'guest' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'}">
                      Observer
                    </button>
                  </div>
                </div>

                <!-- 1-Click Fast Presets (For Evaluators) -->
                <div class="mission-card-subtle p-3 space-y-2 border border-[#1c2c46]">
                  <div class="flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>⚡ 1-CLICK TEST LOGINS FOR EVALUATORS:</span>
                    <span class="text-emerald-400">INSTANT AUTH</span>
                  </div>
                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
                    <button onclick="handleQuickLogin('ndrf')" class="p-2.5 rounded-xl bg-[#132034] hover:bg-[#1a2d48] border border-blue-500/40 text-blue-200 text-left transition-colors">
                      <p class="font-bold text-white">Inspector A. Kumar</p>
                      <p class="text-[10px] text-slate-400">NDRF Commander</p>
                    </button>
                    <button onclick="handleQuickLogin('imd')" class="p-2.5 rounded-xl bg-[#132034] hover:bg-[#1a2d48] border border-blue-500/40 text-blue-200 text-left transition-colors">
                      <p class="font-bold text-white">Dr. S. Roy</p>
                      <p class="text-[10px] text-slate-400">Chief Meteorologist</p>
                    </button>
                    <button onclick="handleQuickLogin('guest')" class="p-2.5 rounded-xl bg-[#132034] hover:bg-[#1a2d48] border border-blue-500/40 text-blue-200 text-left transition-colors">
                      <p class="font-bold text-white">Public Observer</p>
                      <p class="text-[10px] text-slate-400">Citizen Transparency</p>
                    </button>
                  </div>
                </div>

                <!-- Form -->
                <form onsubmit="handleFormLogin(event)" class="space-y-4 text-xs font-mono">
                  <div class="space-y-1.5">
                    <label class="text-slate-300 font-semibold">SERVICE IDENTIFIER / OFFICIAL EMAIL:</label>
                    <input type="text" id="loginEmailInput" value="${state.loginEmail}" oninput="state.loginEmail = this.value" class="w-full p-2.5 rounded-xl bg-[#070c16] border border-[#1b2b45] text-slate-100 focus:outline-none focus:border-blue-500 font-mono" placeholder="officer@ndrf.gov.in" />
                  </div>

                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div class="space-y-1.5">
                      <label class="text-slate-300 font-semibold">OFFICER BADGE ID:</label>
                      <input type="text" id="loginBadgeInput" value="${state.loginBadge}" oninput="state.loginBadge = this.value" class="w-full p-2.5 rounded-xl bg-[#070c16] border border-[#1b2b45] text-slate-100 focus:outline-none focus:border-blue-500 font-mono" />
                    </div>
                    <div class="space-y-1.5">
                      <label class="text-slate-300 font-semibold">2FA HARDWARE TOKEN:</label>
                      <input type="text" id="login2faInput" value="${state.login2fa}" oninput="state.login2fa = this.value" class="w-full p-2.5 rounded-xl bg-[#070c16] border border-[#1b2b45] text-emerald-300 font-bold focus:outline-none focus:border-blue-500 font-mono" />
                    </div>
                  </div>

                  <div class="pt-2 flex items-center justify-between">
                    <button type="button" onclick="setState({ activePortalView: 'portal' })" class="px-4 py-2.5 rounded-xl bg-[#142034] hover:bg-[#1a2d48] text-slate-300 font-medium transition-colors">
                      Return to Preface
                    </button>
                    <button type="submit" class="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all shadow-lg shadow-blue-900/50 flex items-center gap-2">
                      <span>Authenticate & Launch Deck</span>
                      <span>➔</span>
                    </button>
                  </div>
                </form>
              </div>

              <!-- RIGHT COLUMN: Interactive 3D Tactical Pre-Flight Station (6 cols) -->
              <div class="lg:col-span-6 w-full space-y-3">
                <div class="flex items-center justify-between px-1 text-[11px] font-mono text-slate-400">
                  <span class="text-cyan-400 font-bold flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                    TACTICAL PRE-FLIGHT 3D GLOBE MONITOR
                  </span>
                  <span>ISRO INSAT-3DR SYNCED</span>
                </div>

                <!-- 3D Pre-Flight Earth Canvas Card -->
                <div class="mission-card border border-[#233856] rounded-2xl overflow-hidden shadow-2xl bg-[#050914] relative h-[480px]">
                  <div id="loginInteractiveGlobe" class="w-full h-full cursor-grab active:cursor-grabbing"></div>

                  <!-- Floating Telemetry HUD (Top-Left) -->
                  <div class="absolute top-4 left-4 z-10 p-3 rounded-xl bg-[#070d1a]/90 border border-[#1b2b45] backdrop-blur-md text-[11px] font-mono space-y-1 text-slate-300 pointer-events-none shadow-xl">
                    <div class="text-blue-400 font-bold flex items-center gap-1.5">
                      <span>🛰️</span>
                      <span>BAY OF BENGAL RADAR LOCK</span>
                    </div>
                    <div>Vortex: <strong class="text-red-400">16.82°N, 84.48°E</strong></div>
                    <div>Winds: <strong class="text-red-400">155 km/h (Cat-3 VSCS)</strong></div>
                    <div>Landfall: <strong class="text-amber-300">Gopalpur, Odisha (~22.5h)</strong></div>
                  </div>

                  <!-- Floating Usage Cue (Bottom-Center) -->
                  <div class="absolute bottom-3 inset-x-0 flex justify-center pointer-events-none">
                    <div class="px-3.5 py-1 rounded-full bg-[#0a1224]/85 border border-[#1e2e4a] backdrop-blur-md text-[10px] font-mono text-slate-400 shadow-lg">
                      🖱️ Drag to rotate Earth • Scroll to zoom • Interactive Pre-Flight View
                    </div>
                  </div>
                </div>

                <!-- Footer Telemetry -->
                <div class="p-3 bg-[#0c1322] border border-[#1b2b45] rounded-xl flex items-center justify-between text-xs font-mono text-slate-400">
                  <span class="text-emerald-400">● Pukar Resilient Mesh Node: IDLE (Armed for Disruption)</span>
                  <span>Direct Encrypted Relay</span>
                </div>
              </div>

            </div>
          </div>
        </div>
      `;
    }"""

login_start = "    function renderLoginPage() {"
login_end = "    // =========================================================================\n    // MAIN APP RENDER DISPATCHER"

l_start = code.find(login_start)
l_end = code.find(login_end)

if l_start != -1 and l_end != -1:
    code = code[:l_start] + native_login_html + '\n\n    ' + code[l_end:]

# Write back update_portal.py
with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully crafted native interactive preface and login pages in update_portal.py!")
