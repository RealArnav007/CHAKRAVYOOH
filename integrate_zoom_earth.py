import os
import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update state to support zoom_earth mode and timeline/layer controls
old_state_snippet = "heroBgMode: 'globe3d',"
new_state_snippet = """heroBgMode: 'zoom_earth', // 'zoom_earth' | 'globe3d' | 'scorpio_stream'
      zoomEarthLayer: 'satellite', // 'satellite' | 'radar' | 'precipitation' | 'wind' | 'temperature' | 'humidity' | 'pressure'
      zoomEarthSubMode: 'live', // 'live' | 'hd'
      zoomEarthPlaying: false,
      zoomEarthDate: '8 Sept',
      zoomEarthHour: 15,
      zoomEarthMinute: 15,
      zoomEarthCoords: "16° 49' N  84° 28' E",
      zoomEarthCity: 'Bay of Bengal (Cyclone BOB-04 Vortex)',"""

if old_state_snippet in code and 'zoomEarthLayer' not in code:
    code = code.replace(old_state_snippet, new_state_snippet)

# 2. Add Zoom Earth helper functions to javascript
zoom_earth_js = """
    // =========================================================================
    // ZOOM EARTH LIVE SATELLITE CONTROLLER & TIMELINE ENGINE
    // =========================================================================
    let zoomEarthTimer = null;

    function setZoomEarthLayer(layer) {
      state.zoomEarthLayer = layer;
      renderApp();
    }

    function setZoomEarthSubMode(subMode) {
      state.zoomEarthSubMode = subMode;
      renderApp();
    }

    function toggleZoomEarthPlayback() {
      state.zoomEarthPlaying = !state.zoomEarthPlaying;
      if (state.zoomEarthPlaying) {
        if (zoomEarthTimer) clearInterval(zoomEarthTimer);
        zoomEarthTimer = setInterval(() => {
          stepZoomEarthTime(15);
        }, 1200);
      } else {
        if (zoomEarthTimer) clearInterval(zoomEarthTimer);
        zoomEarthTimer = null;
      }
      renderApp();
    }

    function stepZoomEarthTime(deltaMinutes) {
      let totalMins = state.zoomEarthHour * 60 + state.zoomEarthMinute + deltaMinutes;
      if (totalMins < 0) totalMins = 24 * 60 - 15;
      if (totalMins >= 24 * 60) totalMins = 0;
      state.zoomEarthHour = Math.floor(totalMins / 60);
      state.zoomEarthMinute = totalMins % 60;
      renderApp();
    }

    function jumpToZoomEarthLocation(lat, lon, label) {
      state.zoomEarthCoords = `${lat > 0 ? lat.toFixed(2) + '° N' : Math.abs(lat).toFixed(2) + '° S'}  ${lon > 0 ? lon.toFixed(2) + '° E' : Math.abs(lon).toFixed(2) + '° W'}`;
      state.zoomEarthCity = label;
      const frame = document.getElementById('zoomEarthHeroFrame') || document.getElementById('zoomEarthDeckFrame');
      if (frame) {
        frame.src = `/zoom_earth_feed#view=${lat},${lon},6z`;
      }
      focusGlobeTarget('cyclone');
      renderApp();
    }
"""

if 'function setZoomEarthLayer' not in code:
    code = code.replace(
        '    // =========================================================================\n    // THREE.JS 3D INTERACTIVE GLOBE & CYCLONE OBSERVATORY ENGINE',
        zoom_earth_js + '\n    // =========================================================================\n    // THREE.JS 3D INTERACTIVE GLOBE & CYCLONE OBSERVATORY ENGINE'
    )

# 3. Create the Zoom Earth Glassmorphic HUD overlay component
render_zoom_earth_hud_fn = """
    // =========================================================================
    // ZOOM EARTH FLOATING GLASSMORPHISM CONTROLS (Screenshot Authentic UI)
    // =========================================================================
    function renderZoomEarthHUD() {
      const hStr = String(state.zoomEarthHour).padStart(2, '0');
      const mStr = String(state.zoomEarthMinute).padStart(2, '0');

      return `
        <!-- Zoom Earth Left Sidebar Menu (Live Maps & Forecast Maps) -->
        <div class="absolute top-4 left-4 z-20 w-52 sm:w-56 rounded-2xl bg-[#090e1a]/85 border border-[#1d2b45] backdrop-blur-xl p-3 shadow-2xl text-xs select-none space-y-3 font-sans transition-all">
          <!-- Zoom Earth Brand Header -->
          <div class="flex items-center justify-between border-b border-[#18253d] pb-2.5">
            <div class="flex items-center space-x-2">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-600 via-cyan-400 to-indigo-500 p-0.5 flex items-center justify-center shadow-lg">
                <span class="text-sm">🌐</span>
              </div>
              <div>
                <div class="font-black text-white text-xs tracking-wider flex items-center gap-1">
                  <span>ZOOM</span>
                  <span class="text-blue-400 font-medium">EARTH</span>
                </div>
                <div class="text-[9px] font-mono text-slate-400">CHAKRAVYOOH SATELLITE</div>
              </div>
            </div>
            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">15m SCAN</span>
          </div>

          <!-- Section: LIVE MAPS -->
          <div class="space-y-1">
            <div class="flex items-center justify-between text-[10px] font-mono font-bold text-slate-400 px-1 uppercase tracking-wider">
              <span>LIVE MAPS</span>
              <span class="text-emerald-400 text-[10px] animate-pulse">● LIVE</span>
            </div>

            <!-- Satellite Button with Live/HD Sub-toggles -->
            <div class="rounded-xl overflow-hidden ${state.zoomEarthLayer === 'satellite' ? 'bg-gradient-to-r from-blue-950/80 to-[#14233e] border border-blue-600/70' : 'hover:bg-[#121c2e] border border-transparent'} transition-all">
              <button onclick="setZoomEarthLayer('satellite')" class="w-full px-2.5 py-2 flex items-center justify-between text-left">
                <div class="flex items-center space-x-2">
                  <span class="text-sm">🛰️</span>
                  <span class="font-semibold ${state.zoomEarthLayer === 'satellite' ? 'text-white' : 'text-slate-300'}">Satellite</span>
                </div>
                <span class="text-[10px] text-blue-400">INSAT-3DR</span>
              </button>

              ${state.zoomEarthLayer === 'satellite' ? `
                <div class="px-2.5 pb-2 pt-0.5 flex items-center space-x-1.5 border-t border-blue-900/40 mt-1">
                  <button onclick="setZoomEarthSubMode('live')" class="flex-1 py-1 rounded-md text-[10px] font-mono font-bold ${state.zoomEarthSubMode === 'live' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'} transition-colors flex items-center justify-center gap-1">
                    <span>✓</span>
                    <span>Live</span>
                  </button>
                  <button onclick="setZoomEarthSubMode('hd')" class="flex-1 py-1 rounded-md text-[10px] font-mono font-bold ${state.zoomEarthSubMode === 'hd' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'} transition-colors flex items-center justify-center">
                    <span>HD</span>
                  </button>
                </div>
              ` : ''}
            </div>

            <!-- Radar Button -->
            <button onclick="setZoomEarthLayer('radar')" class="w-full px-2.5 py-2 rounded-xl flex items-center justify-between text-left ${state.zoomEarthLayer === 'radar' ? 'bg-gradient-to-r from-blue-950/80 to-[#14233e] border border-blue-600/70 text-white font-semibold' : 'text-slate-300 hover:bg-[#121c2e] border border-transparent'} transition-all">
              <div class="flex items-center space-x-2">
                <span class="text-sm">📡</span>
                <span>Radar</span>
              </div>
              <span class="text-[10px] text-slate-500 font-mono">DWR Array</span>
            </button>
          </div>

          <!-- Section: FORECAST MAPS -->
          <div class="space-y-1 border-t border-[#18253d] pt-2">
            <div class="text-[10px] font-mono font-bold text-slate-400 px-1 uppercase tracking-wider">
              FORECAST MAPS
            </div>

            <!-- Precipitation -->
            <button onclick="setZoomEarthLayer('precipitation')" class="w-full px-2.5 py-1.5 rounded-lg flex items-center space-x-2 text-left text-[11px] ${state.zoomEarthLayer === 'precipitation' ? 'bg-blue-950/90 text-blue-300 border border-blue-700/60 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-[#121c2e]'} transition-colors">
              <span>🌧️</span>
              <span>Precipitation</span>
            </button>

            <!-- Wind -->
            <button onclick="setZoomEarthLayer('wind')" class="w-full px-2.5 py-1.5 rounded-lg flex items-center space-x-2 text-left text-[11px] ${state.zoomEarthLayer === 'wind' ? 'bg-blue-950/90 text-blue-300 border border-blue-700/60 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-[#121c2e]'} transition-colors">
              <span>💨</span>
              <span>Wind Streams</span>
            </button>

            <!-- Temperature -->
            <button onclick="setZoomEarthLayer('temperature')" class="w-full px-2.5 py-1.5 rounded-lg flex items-center space-x-2 text-left text-[11px] ${state.zoomEarthLayer === 'temperature' ? 'bg-blue-950/90 text-blue-300 border border-blue-700/60 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-[#121c2e]'} transition-colors">
              <span>🌡️</span>
              <span>SST / Temperature</span>
            </button>

            <!-- Humidity -->
            <button onclick="setZoomEarthLayer('humidity')" class="w-full px-2.5 py-1.5 rounded-lg flex items-center space-x-2 text-left text-[11px] ${state.zoomEarthLayer === 'humidity' ? 'bg-blue-950/90 text-blue-300 border border-blue-700/60 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-[#121c2e]'} transition-colors">
              <span>💧</span>
              <span>Humidity</span>
            </button>

            <!-- Pressure -->
            <button onclick="setZoomEarthLayer('pressure')" class="w-full px-2.5 py-1.5 rounded-lg flex items-center space-x-2 text-left text-[11px] ${state.zoomEarthLayer === 'pressure' ? 'bg-blue-950/90 text-blue-300 border border-blue-700/60 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-[#121c2e]'} transition-colors">
              <span>🧭</span>
              <span>Pressure (hPa)</span>
            </button>
          </div>
        </div>

        <!-- Zoom Earth Right Action Toolbar (Search, Measure, Reticle, Layers) -->
        <div class="absolute top-4 right-4 z-20 flex flex-col items-center gap-2">
          <!-- Main Viewport Mode Switcher Pill -->
          <div class="flex items-center gap-1.5 bg-[#090e1a]/85 border border-[#1d2b45] backdrop-blur-xl px-2.5 py-1.5 rounded-2xl text-xs font-mono shadow-2xl">
            <button onclick="setGlobeBgMode('zoom_earth')" class="px-2.5 py-1 rounded-xl ${state.heroBgMode === 'zoom_earth' ? 'bg-blue-600 text-white font-bold shadow' : 'text-slate-300 hover:bg-[#15233c]'} transition-colors flex items-center gap-1">
              <span>🌍</span>
              <span class="hidden sm:inline">Zoom Earth HD</span>
            </button>
            <button onclick="setGlobeBgMode('globe3d')" class="px-2.5 py-1 rounded-xl ${state.heroBgMode === 'globe3d' ? 'bg-blue-600 text-white font-bold shadow' : 'text-slate-300 hover:bg-[#15233c]'} transition-colors flex items-center gap-1">
              <span>🌐</span>
              <span class="hidden sm:inline">3D Globe</span>
            </button>
            <button onclick="setGlobeBgMode('scorpio_stream')" class="px-2.5 py-1 rounded-xl ${state.heroBgMode === 'scorpio_stream' ? 'bg-blue-600 text-white font-bold shadow' : 'text-slate-300 hover:bg-[#15233c]'} transition-colors flex items-center gap-1">
              <span>📡</span>
              <span class="hidden sm:inline">SCORPIO</span>
            </button>
          </div>

          <!-- Tool Icons Stack -->
          <div class="bg-[#090e1a]/85 border border-[#1d2b45] backdrop-blur-xl p-1.5 rounded-2xl flex flex-col items-center gap-1.5 text-slate-300 shadow-xl text-xs">
            <button onclick="jumpToZoomEarthLocation(16.82, 84.48, 'Cyclone BOB-04 Vortex')" class="w-8 h-8 rounded-xl bg-red-950/70 hover:bg-red-900 border border-red-800/60 text-red-300 flex items-center justify-center transition-colors" title="Focus Cyclone BOB-04 (16.82°N, 84.48°E)">
              🌀
            </button>
            <button onclick="jumpToZoomEarthLocation(19.26, 84.91, 'Gopalpur Coastal Landfall')" class="w-8 h-8 rounded-xl bg-[#131f33] hover:bg-[#1c2c47] flex items-center justify-center transition-colors" title="Target Landfall (Gopalpur, Odisha)">
              📍
            </button>
            <button onclick="jumpToZoomEarthLocation(20.59, 78.96, 'Indian Subcontinent')" class="w-8 h-8 rounded-xl bg-[#131f33] hover:bg-[#1c2c47] flex items-center justify-center transition-colors" title="Center India & Bay of Bengal">
              🎯
            </button>
            <button onclick="toggleGlobeAutoRotate()" class="w-8 h-8 rounded-xl bg-[#131f33] hover:bg-[#1c2c47] flex items-center justify-center transition-colors" title="Toggle Auto-Spin">
              ${state.globeAutoRotate ? '⏸️' : '▶️'}
            </button>
            <a href="https://zoom.earth/maps/satellite/#view=18.5,84.5,5z" target="_blank" rel="noopener noreferrer" class="w-8 h-8 rounded-xl bg-[#131f33] hover:bg-[#1c2c47] flex items-center justify-center text-blue-400 hover:text-blue-300 transition-colors" title="Open Full Screen Official Zoom Earth">
              ↗
            </a>
          </div>
        </div>

        <!-- Zoom Earth Bottom Timeline Scrubber (Screenshot Exact Layout) -->
        <div class="absolute bottom-4 inset-x-4 z-20 flex flex-col sm:flex-row items-center justify-between gap-3 pointer-events-none select-none">
          <!-- Coordinates & City Info (Bottom Left) -->
          <div class="pointer-events-auto px-3.5 py-1.5 rounded-xl bg-[#090e1a]/90 border border-[#1d2b45] backdrop-blur-xl text-xs font-mono text-slate-300 shadow-xl flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-red-400 animate-ping"></span>
            <span class="font-bold text-white">${state.zoomEarthCoords}</span>
            <span class="text-slate-600">|</span>
            <span class="text-blue-400 text-[11px] font-sans">${state.zoomEarthCity}</span>
          </div>

          <!-- Interactive Time Controller & Scrubber (Center Bottom) -->
          <div class="pointer-events-auto flex items-center gap-3 bg-[#090e1a]/90 border border-[#1d2b45] backdrop-blur-xl px-4 py-2 rounded-2xl shadow-2xl font-mono text-xs">
            <!-- Play / Pause Button -->
            <button onclick="toggleZoomEarthPlayback()" class="w-8 h-8 rounded-xl ${state.zoomEarthPlaying ? 'bg-amber-600 hover:bg-amber-500' : 'bg-blue-600 hover:bg-blue-500'} text-white flex items-center justify-center transition-colors shadow">
              ${state.zoomEarthPlaying ? '⏸' : '▶'}
            </button>

            <!-- Date Indicator -->
            <div class="text-center font-bold text-slate-200 px-2 border-r border-[#1a283f]">
              <span>${state.zoomEarthDate}</span>
            </div>

            <!-- Time Stepper (Hours) -->
            <div class="flex items-center space-x-1">
              <div class="text-center">
                <button onclick="stepZoomEarthTime(60)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▲</button>
                <span class="font-bold text-white text-sm">${hStr}</span>
                <button onclick="stepZoomEarthTime(-60)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▼</button>
              </div>
              <span class="text-slate-400 font-bold">:</span>
              <!-- Time Stepper (Minutes) -->
              <div class="text-center">
                <button onclick="stepZoomEarthTime(15)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▲</button>
                <span class="font-bold text-blue-400 text-sm">${mStr}</span>
                <button onclick="stepZoomEarthTime(-15)" class="text-[10px] text-slate-400 hover:text-white block w-full leading-none">▼</button>
              </div>
            </div>

            <span class="text-slate-600">|</span>
            <span class="text-[10px] text-slate-400 uppercase tracking-wide">IST (UTC+5:30)</span>
          </div>

          <!-- Scale Indicator (Bottom Right) -->
          <div class="pointer-events-auto px-3.5 py-1.5 rounded-xl bg-[#090e1a]/90 border border-[#1d2b45] backdrop-blur-xl text-xs font-mono text-slate-300 shadow-xl flex items-center gap-2">
            <span>SCALE:</span>
            <span class="font-bold text-white">1000 km</span>
            <div class="w-12 h-1 bg-blue-500 rounded"></div>
          </div>
        </div>
      `;
    }
"""

if 'function renderZoomEarthHUD' not in code:
    code = code.replace(
        '    // =========================================================================\n    // NASA / ISRO STYLE FLAGSHIP EXPLORATION PORTAL (STARTING PAGE)',
        render_zoom_earth_hud_fn + '\n    // =========================================================================\n    // NASA / ISRO STYLE FLAGSHIP EXPLORATION PORTAL (STARTING PAGE)'
    )

# 4. Update the Hero Banner in renderNasaPortal() to embed Zoom Earth and its HUD
old_hero_block = """          <!-- 3. NASA FLAGSHIP HERO BANNER (SPACE/EARTH EXPLORATION AESTHETIC) -->
          <section class="relative min-h-[580px] flex items-center overflow-hidden border-b border-[#1b2b45] bg-[#070b14]">
            <!-- Interactive 3D Globe Background or Live SCORPIO Stream -->
            ${state.heroBgMode === 'globe3d' ? `
              <!-- Interactive 3D WebGL Earth & Cyclone Orbit Canvas -->
              <div id="nasaHeroGlobeContainer" class="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing overflow-hidden z-0"></div>
              <div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#070b14] via-[#070b14]/80 md:via-[#070b14]/65 to-transparent z-[1]"></div>
              <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/60 z-[1]"></div>
            ` : `
              <!-- Live ISRO MOSDAC SCORPIO Radar Stream -->
              <div class="absolute inset-0 w-full h-full pointer-events-none select-none z-0">
                <iframe src="/scorpio_feed" class="w-full h-full border-0 transform scale-105 opacity-35 filter contrast-125 saturate-125"></iframe>
                <div class="absolute inset-0 bg-gradient-to-r from-[#070b14] via-[#070b14]/85 to-transparent"></div>
                <div class="absolute inset-0 bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/70"></div>
              </div>
            `}

            <!-- Floating 3D Globe HUD Quick Controls Bar -->
            <div class="absolute top-4 right-4 z-20 flex flex-wrap items-center gap-2 bg-[#0c1424]/90 border border-[#1e2e4a] backdrop-blur-md px-3 py-2 rounded-xl text-xs font-mono shadow-2xl">
              <span class="text-slate-400 text-[11px] hidden sm:inline">VIEWPORT:</span>
              <button onclick="setGlobeBgMode('globe3d')" class="px-2.5 py-1 rounded ${state.heroBgMode === 'globe3d' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-[#142034]'} transition-colors flex items-center gap-1">
                <span>🌐</span>
                <span>3D Earth</span>
              </button>
              <button onclick="setGlobeBgMode('scorpio_stream')" class="px-2.5 py-1 rounded ${state.heroBgMode === 'scorpio_stream' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-[#142034]'} transition-colors flex items-center gap-1">
                <span>📡</span>
                <span>SCORPIO Stream</span>
              </button>
              <span class="text-slate-700">|</span>
              <button onclick="focusGlobeTarget('cyclone')" class="px-2 py-1 rounded text-red-300 hover:bg-red-950/60 border border-red-900/50 transition-colors" title="Center camera on Cyclone BOB-04 vortex">
                🌀 Eye Target
              </button>
              <button onclick="focusGlobeTarget('insat')" class="px-2 py-1 rounded text-blue-300 hover:bg-blue-950/60 border border-blue-900/50 transition-colors" title="Inspect INSAT-3DR Geostationary Orbit">
                🛰️ INSAT-3DR
              </button>
              <button onclick="toggleGlobeAutoRotate()" class="px-2 py-1 rounded text-slate-300 hover:bg-[#15233c] transition-colors" title="Toggle Auto-Rotation">
                ${state.globeAutoRotate ? '⏸️ Pause' : '▶️ Spin'}
              </button>
            </div>"""

new_hero_block = """          <!-- 3. NASA FLAGSHIP HERO BANNER (ZOOM EARTH / 3D GLOBE / SCORPIO INTEGRATED) -->
          <section class="relative min-h-[640px] flex items-center overflow-hidden border-b border-[#1b2b45] bg-[#050913]">
            <!-- Live Background Viewports: Zoom Earth HD, 3D Interactive WebGL Earth, or SCORPIO Radar -->
            ${state.heroBgMode === 'zoom_earth' ? `
              <!-- Live Zoom Earth Satellite Feed -->
              <div class="absolute inset-0 w-full h-full z-0 overflow-hidden select-none">
                <iframe id="zoomEarthHeroFrame" src="/zoom_earth_feed#view=18.5,84.5,5z" class="w-full h-full border-0 transform scale-100 filter brightness-95 contrast-110" title="Live Zoom Earth Satellite Map" allow="geolocation; fullscreen"></iframe>
                <!-- Subtle Dark Overlay for High-Contrast Institutional Legibility -->
                <div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#070b14]/90 via-[#070b14]/70 to-transparent z-[1]"></div>
                <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/50 z-[1]"></div>
              </div>
              ${renderZoomEarthHUD()}
            ` : state.heroBgMode === 'globe3d' ? `
              <!-- Interactive 3D WebGL Earth & Cyclone Orbit Canvas -->
              <div id="nasaHeroGlobeContainer" class="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing overflow-hidden z-0"></div>
              <div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#070b14] via-[#070b14]/80 md:via-[#070b14]/65 to-transparent z-[1]"></div>
              <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/60 z-[1]"></div>
              ${renderZoomEarthHUD()}
            ` : `
              <!-- Live ISRO MOSDAC SCORPIO Radar Stream -->
              <div class="absolute inset-0 w-full h-full pointer-events-none select-none z-0">
                <iframe src="/scorpio_feed" class="w-full h-full border-0 transform scale-105 opacity-40 filter contrast-125 saturate-125"></iframe>
                <div class="absolute inset-0 bg-gradient-to-r from-[#070b14] via-[#070b14]/85 to-transparent"></div>
                <div class="absolute inset-0 bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/70"></div>
              </div>
              ${renderZoomEarthHUD()}
            `}"""

if old_hero_block in code:
    code = code.replace(old_hero_block, new_hero_block)

# 5. Add a dedicated Zoom Earth Satellite & Radar Observatory Section
zoom_earth_deck_section = """
          <!-- 3.4. DEDICATED ZOOM EARTH HIGH-DEFINITION SATELLITE OBSERVATORY -->
          <section id="zoom-earth-section" class="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-4">
            <div class="mission-card border border-[#233856] overflow-hidden">
              <!-- Observatory Header -->
              <div class="p-4 sm:p-5 bg-[#091122] border-b border-[#1b2b45] flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping"></span>
                    <span class="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">LIVE GLOBAL SATELLITE & RADAR NETWORK</span>
                    <span class="text-slate-600">•</span>
                    <span class="text-slate-300 font-mono text-xs">Zoom Earth & INSAT-3DR High-Resolution Feeds</span>
                  </div>
                  <h3 class="text-lg sm:text-xl font-bold font-heading text-white mt-1">
                    Real-Time Atmospheric Satellite Imagery & Day/Night Cloud Terminator
                  </h3>
                  <p class="text-xs text-slate-400 mt-0.5">
                    Near real-time global weather satellite composite updated continuously. Pan across the Indian Ocean, inspect cloud spirals, and track active cyclone bands.
                  </p>
                </div>

                <!-- Action Controls -->
                <div class="flex flex-wrap items-center gap-2.5 text-xs font-mono">
                  <button onclick="jumpToZoomEarthLocation(16.82, 84.48, 'Cyclone BOB-04 Vortex')" class="px-3 py-1.5 rounded-lg bg-red-950/80 hover:bg-red-900 text-red-300 border border-red-700/60 font-semibold transition-colors flex items-center gap-1.5">
                    <span>🌀</span>
                    <span>Focus Cyclone BOB-04</span>
                  </button>
                  <a href="https://zoom.earth/maps/satellite/#view=18.5,84.5,5z" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors flex items-center gap-1.5">
                    <span>Open Zoom Earth Fullscreen</span>
                    <span>↗</span>
                  </a>
                </div>
              </div>

              <!-- High-Resolution Zoom Earth Embedded Canvas Viewport -->
              <div class="relative w-full h-[580px] bg-[#040813] overflow-hidden">
                <iframe id="zoomEarthDeckFrame" src="/zoom_earth_feed#view=18.5,84.5,5z" class="w-full h-full border-0" title="Zoom Earth Real-Time Satellite Map" allow="geolocation; fullscreen"></iframe>
              </div>

              <!-- Observatory Footer -->
              <div class="p-3 bg-[#070d1a] border-t border-[#1b2b45] flex flex-wrap items-center justify-between text-xs font-mono text-slate-400">
                <div class="flex items-center gap-4">
                  <span>🛰️ Sources: <strong class="text-slate-200">INSAT-3DR / GOES / Himawari / EUMETSAT</strong></span>
                  <span>⚡ Cadence: <strong class="text-blue-400">10-15 min Rapid Global Composite</strong></span>
                  <span>🧭 Vortex Eye: <strong class="text-red-400">16.82°N, 84.48°E (Cat-3 VSCS)</strong></span>
                </div>
                <span class="text-emerald-400 font-semibold">● REAL-TIME SYNCHRONIZATION ACTIVE</span>
              </div>
            </div>
          </section>
"""

if '<!-- 3.4. DEDICATED ZOOM EARTH' not in code:
    code = code.replace(
        '          <!-- 3.5. DEDICATED 3D CYCLONE ORBIT DECK',
        zoom_earth_deck_section + '\n          <!-- 3.5. DEDICATED 3D CYCLONE ORBIT DECK'
    )

# Write back update_portal.py
with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully updated update_portal.py with Zoom Earth Live Satellite & Glassmorphic HUD!")
