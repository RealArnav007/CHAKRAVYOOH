import os
import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Define the decluttered, elegant, world-class renderNasaPortal()
decluttered_preface_html = """    function renderNasaPortal() {
      const cyc = state.cyclone;
      const obs = state.liveObservation;
      const isFlat = state.pixelWidgetView === 'flat';

      return `
        <div class="min-h-screen text-slate-100 flex flex-col font-sans operational-bg select-none">
          
          <!-- 1. MINIMAL AGENCY STRIP -->
          <div class="bg-[#050811]/90 border-b border-[#141f33] px-4 sm:px-8 py-1.5 text-[11px] font-mono text-slate-400 flex items-center justify-between z-50">
            <div class="flex items-center space-x-2">
              <span class="text-sm">🇮🇳</span>
              <span class="text-slate-300 font-medium">ISRO SAC • IMD RSMC • INCOIS</span>
              <span class="text-slate-600">•</span>
              <span class="text-blue-400 font-semibold">Project Beacon</span>
            </div>
            <div class="flex items-center space-x-3 text-[11px]">
              <span class="text-emerald-400 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Telemetry Live</span>
              </span>
              <span class="text-slate-700">|</span>
              <button onclick="setState({ activePortalView: 'login' })" class="text-slate-300 hover:text-white transition-colors">
                Officer Access ➔
              </button>
            </div>
          </div>

          <!-- 2. SLEEK MINIMAL HEADER -->
          <header class="h-16 bg-[#070c18]/80 backdrop-blur-xl border-b border-[#142033] px-4 sm:px-8 flex items-center justify-between sticky top-0 z-40">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-700 to-indigo-900 border border-blue-400/40 flex items-center justify-center text-white font-bold text-lg shadow-md">
                🌀
              </div>
              <div class="flex items-center space-x-2">
                <span class="font-extrabold text-base sm:text-lg tracking-tight text-white font-heading">
                  CHAKRAVYOOH
                </span>
                <span class="hidden sm:inline-block text-[10px] font-mono text-blue-300 bg-blue-950/80 border border-blue-800 px-2 py-0.5 rounded-md">
                  CY-2026-BOB04
                </span>
              </div>
            </div>

            <!-- Minimal Center Anchors -->
            <nav class="hidden md:flex items-center space-x-6 text-xs font-mono text-slate-300">
              <button onclick="selectPrefaceTarget('cyclone')" class="hover:text-white transition-colors flex items-center gap-1">
                <span>🌀</span>
                <span>Storm Core</span>
              </button>
              <button onclick="selectPrefaceTarget('insat')" class="hover:text-white transition-colors flex items-center gap-1">
                <span>🛰️</span>
                <span>INSAT-3DR</span>
              </button>
              <a href="#widgets-section" class="hover:text-white transition-colors flex items-center gap-1">
                <span>📱</span>
                <span>Weather Cards</span>
              </a>
              <a href="#pipeline-section" class="hover:text-white transition-colors flex items-center gap-1">
                <span>⚡</span>
                <span>AI Pipeline</span>
              </a>
            </nav>

            <!-- Actions -->
            <div class="flex items-center space-x-3">
              <button onclick="setState({ activePortalView: 'login' })" class="px-3.5 py-1.5 rounded-lg bg-[#121c2e] hover:bg-[#1a2942] border border-[#20324e] text-slate-200 text-xs font-mono font-medium transition-colors">
                Login
              </button>
              <button onclick="setState({ activePortalView: 'command_center' })" class="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold font-mono transition-all shadow-md shadow-blue-900/50 flex items-center gap-1.5">
                <span>Launch Deck</span>
                <span>➔</span>
              </button>
            </div>
          </header>

          <!-- 3. CLEAN, BREATHABLE FULL-BLEED 3D HERO CANVAS -->
          <section class="relative min-h-[640px] lg:min-h-[700px] flex items-center overflow-hidden border-b border-[#142033] bg-[#03060f]">
            <!-- 100% Native WebGL Photorealistic NASA 3D Earth -->
            <div id="prefaceInteractiveGlobe" class="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing z-0"></div>

            <!-- Subtle Vignette to Guarantee Typography Readability -->
            <div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#03060f]/90 via-[#03060f]/50 to-transparent z-[1]"></div>
            <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#03060f] via-transparent to-[#03060f]/60 z-[1]"></div>

            <!-- HERO TEXT (Clean, Minimal, Authoritative) -->
            <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-12 w-full pointer-events-none">
              <div class="max-w-xl space-y-5 pointer-events-auto">
                
                <!-- Active Mission Pill -->
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-950/70 border border-red-700/60 text-red-300 text-xs font-mono font-semibold backdrop-blur-md">
                  <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                  <span>CYCLONE BOB-04 (VSCS) • 155 KM/H • BAY OF BENGAL</span>
                </div>

                <!-- Main Headline -->
                <div class="space-y-2.5">
                  <h1 class="text-3xl sm:text-5xl lg:text-5xl font-black font-heading tracking-tight text-white leading-tight">
                    AI-Powered Tropical Cyclone Intelligence
                  </h1>
                  <p class="text-sm sm:text-base text-slate-300 font-light leading-relaxed">
                    Fusing Indian geostationary satellite telemetry (<strong class="text-blue-300 font-medium">INSAT-3DR/3DS</strong>), polar scatterometry, and oceanic buoy arrays to predict storm evolution — enhanced with <strong class="text-red-300 font-medium">Pukar's</strong> resilient offline emergency mesh.
                  </p>
                </div>

                <!-- Minimal Primary Actions -->
                <div class="flex flex-wrap items-center gap-3 pt-1">
                  <button onclick="setState({ activePortalView: 'command_center' })" class="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs font-mono transition-all shadow-lg shadow-blue-900/50 flex items-center gap-2">
                    <span>Launch Tactical Command Deck</span>
                    <span>➔</span>
                  </button>
                  <button onclick="selectPrefaceTarget('cyclone')" class="px-4 py-2.5 rounded-xl bg-[#0e1726]/80 hover:bg-[#162338] border border-[#20314a] text-slate-200 font-mono text-xs backdrop-blur-md transition-colors flex items-center gap-1.5">
                    <span>🌀 Focus Storm Eye</span>
                  </button>
                </div>

                <!-- Clean Single-Line Pitch -->
                <p class="text-xs font-mono text-slate-400 italic pt-1">
                  "The AI tells us what is coming. Pukar helps people respond when it arrives."
                </p>
              </div>
            </div>

            <!-- UNIFIED ELEGANT FLOATING DOCK (Zoom Earth / Apple Minimal Style) -->
            <div class="absolute bottom-6 inset-x-4 z-20 flex justify-center pointer-events-none">
              <div class="pointer-events-auto flex flex-wrap items-center gap-2.5 sm:gap-3 bg-[#080e1b]/80 border border-white/10 backdrop-blur-2xl px-4 py-2 rounded-full shadow-2xl text-xs font-mono">
                
                <!-- Focus Presets -->
                <button onclick="selectPrefaceTarget('cyclone')" class="px-2.5 py-1 rounded-full bg-red-950/80 hover:bg-red-900 border border-red-700/60 text-red-300 text-[11px] font-bold transition-colors flex items-center gap-1">
                  <span>🌀</span>
                  <span>BOB-04</span>
                </button>
                <button onclick="selectPrefaceTarget('insat')" class="px-2.5 py-1 rounded-full bg-blue-950/80 hover:bg-blue-900 border border-blue-700/60 text-blue-300 text-[11px] font-semibold transition-colors flex items-center gap-1">
                  <span>🛰️</span>
                  <span>INSAT-3DR</span>
                </button>
                <button onclick="selectPrefaceTarget('india')" class="px-2.5 py-1 rounded-full bg-[#121c2e] hover:bg-[#1a2840] text-slate-300 text-[11px] transition-colors">
                  🇮🇳 India
                </button>

                <div class="h-3.5 w-px bg-slate-700 hidden sm:block"></div>

                <!-- Auto-Spin Toggle -->
                <button onclick="toggleGlobeAutoRotate()" class="text-slate-300 hover:text-white transition-colors" title="Toggle Auto-Spin">
                  ${state.globeAutoRotate ? '⏸️' : '▶️'}
                </button>

                <div class="h-3.5 w-px bg-slate-700 hidden sm:block"></div>

                <!-- Live Coordinates & Wind Telemetry -->
                <div class="text-[11px] text-slate-300 flex items-center gap-2">
                  <span class="text-emerald-400 font-bold">${state.prefaceCoords}</span>
                  <span class="text-slate-600 hidden sm:inline">•</span>
                  <span class="text-red-400 font-bold hidden sm:inline">155 km/h</span>
                </div>

                <div class="h-3.5 w-px bg-slate-700 hidden md:block"></div>

                <!-- Subtle Interaction Hint -->
                <span class="text-[10px] text-slate-500 hidden md:inline">
                  Drag to rotate • Scroll to zoom
                </span>
              </div>
            </div>
          </section>

          <!-- 4. PIXEL-ART WEATHER WIDGETS DECK (3D ISOMETRIC / FLAT GRID) -->
          <div id="widgets-section">
            ${renderPixelWeatherWidgetsDeck()}
          </div>

          <!-- 5. STREAMLINED AI PIPELINE (Multi-Source -> Fusion -> AI Engine -> Pukar) -->
          <section id="pipeline-section" class="max-w-7xl mx-auto px-4 sm:px-8 py-10 space-y-6">
            <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-2 border-b border-[#142033] pb-3">
              <div>
                <span class="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">PROJECT ARCHITECTURE</span>
                <h2 class="text-xl sm:text-2xl font-bold font-heading text-white mt-0.5">
                  Multi-Source Intelligence to Resilient Ground Delivery
                </h2>
              </div>
              <button onclick="setState({ activePortalView: 'command_center', activeScreen: 'screen2_ai' })" class="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1">
                <span>View Full AI Pipeline</span>
                <span>➔</span>
              </button>
            </div>

            <!-- 4 Clean Pipeline Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
              <div class="mission-card p-4 space-y-2">
                <span class="text-[10px] font-bold text-blue-400">01 • MULTI-SOURCE INGEST</span>
                <h3 class="text-sm font-bold text-white">4 Ingestion Feeds</h3>
                <p class="text-slate-400 text-[11px] font-sans">INSAT-3DR Imager, EOS-06 Scatterometer, INCOIS Buoys (BD08/10), and IMD historical tracks.</p>
              </div>

              <div class="mission-card p-4 space-y-2">
                <span class="text-[10px] font-bold text-blue-400">02 • FUSION & AI ENGINE</span>
                <h3 class="text-sm font-bold text-white">CNN-ViT + PINN</h3>
                <p class="text-slate-400 text-[11px] font-sans">94% detection confidence, Category-3 VSCS classification, and +24h trajectory cone.</p>
              </div>

              <div class="mission-card p-4 space-y-2">
                <span class="text-[10px] font-bold text-red-400">03 • RISK ENGINE</span>
                <h3 class="text-sm font-bold text-white">Zone A: Extreme</h3>
                <p class="text-slate-400 text-[11px] font-sans">Translates trajectory into danger corridors (Gopalpur 92/100, Puri 74/100) emitting CYCLONE_RISK_UPDATED.</p>
              </div>

              <div class="mission-card p-4 space-y-2 border-l-2 border-red-500">
                <span class="text-[10px] font-bold text-emerald-400">04 • PUKAR MESH</span>
                <h3 class="text-sm font-bold text-white">Offline P2P Warning</h3>
                <p class="text-slate-400 text-[11px] font-sans">Store-and-forward BLE / Wi-Fi Aware network delivers life-saving alerts when towers collapse.</p>
              </div>
            </div>
          </section>

          <!-- 6. MINIMAL CLEAN FOOTER -->
          <footer class="mt-auto border-t border-[#142033] bg-[#050811] py-6 px-4 sm:px-8 text-slate-500 text-xs font-mono">
            <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
              <div class="flex items-center space-x-2">
                <span>🌀</span>
                <span class="text-slate-300 font-bold">CHAKRAVYOOH</span>
                <span>• Project Beacon</span>
              </div>
              <div class="text-[11px]">
                ISRO SAC • IMD RSMC New Delhi • INCOIS Hyderabad • NDRF Command
              </div>
            </div>
          </footer>
        </div>
      `;
    }
"""

# Replace renderNasaPortal in update_portal.py
p_start = "    function renderNasaPortal() {"
p_end = "    function renderLoginPage() {"

i_start = code.find(p_start)
i_end = code.find(p_end)

if i_start != -1 and i_end != -1:
    code = code[:i_start] + decluttered_preface_html + '\n\n    ' + code[i_end:]

# Also declutter the login page: Clean, balanced, beautiful
decluttered_login_html = """    function renderLoginPage() {
      return `
        <div class="min-h-screen text-slate-100 flex flex-col font-sans operational-bg select-none">
          <!-- Top Flag Strip -->
          <div class="bg-[#050811] border-b border-[#141f33] px-4 py-2 text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span>🇮🇳</span>
              <span class="font-bold text-slate-200">GOVERNMENT OF INDIA</span>
              <span class="text-slate-600">•</span>
              <span class="text-blue-400">CHAKRAVYOOH SECURE GATEWAY</span>
            </div>
            <button onclick="setState({ activePortalView: 'portal' })" class="text-slate-400 hover:text-white flex items-center gap-1 transition-colors">
              <span>←</span>
              <span>Back to Overview</span>
            </button>
          </div>

          <!-- Main Login Content: Clean 2-Column Layout -->
          <div class="flex-1 flex items-center justify-center p-4 sm:p-8 max-w-6xl mx-auto w-full">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center w-full">
              
              <!-- LEFT COLUMN: Officer Authentication Portal (6 cols) -->
              <div class="lg:col-span-6 w-full mission-card p-6 sm:p-7 space-y-5 border border-[#1b2b45] shadow-2xl bg-[#090e1b]/95 backdrop-blur-xl">
                <!-- Header -->
                <div class="flex items-center justify-between border-b border-[#162338] pb-3">
                  <div class="flex items-center space-x-2.5">
                    <div class="w-9 h-9 rounded-xl bg-blue-900/60 border border-blue-500/40 flex items-center justify-center text-blue-300 font-bold text-lg">
                      🔐
                    </div>
                    <div>
                      <h2 class="text-sm font-bold text-white font-heading">Officer Authentication</h2>
                      <p class="text-[10px] font-mono text-slate-400">Cyclone Warning & Emergency Operations</p>
                    </div>
                  </div>
                  <span class="px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-[10px] font-mono text-blue-300">
                    Restricted
                  </span>
                </div>

                <!-- Role Selector -->
                <div class="space-y-1">
                  <label class="text-[11px] font-mono text-slate-400">Clearance Role:</label>
                  <div class="grid grid-cols-4 gap-1 bg-[#060a14] p-1 rounded-lg border border-[#162338] text-xs font-mono">
                    <button onclick="handleSelectLoginRole('ndrf')" class="py-1.5 rounded ${state.loginRole === 'ndrf' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">NDRF</button>
                    <button onclick="handleSelectLoginRole('imd')" class="py-1.5 rounded ${state.loginRole === 'imd' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">IMD</button>
                    <button onclick="handleSelectLoginRole('district')" class="py-1.5 rounded ${state.loginRole === 'district' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">SDMA</button>
                    <button onclick="handleSelectLoginRole('guest')" class="py-1.5 rounded ${state.loginRole === 'guest' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">Guest</button>
                  </div>
                </div>

                <!-- 1-Click Fast Evaluator Presets -->
                <div class="p-2.5 rounded-xl bg-[#060a14] border border-[#162338] space-y-1.5">
                  <div class="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span>⚡ 1-CLICK TEST CREDENTIALS:</span>
                    <span class="text-emerald-400">INSTANT AUTH</span>
                  </div>
                  <div class="grid grid-cols-3 gap-1.5 text-xs font-mono">
                    <button onclick="handleQuickLogin('ndrf')" class="p-2 rounded-lg bg-[#0e1728] hover:bg-[#142238] border border-blue-900/50 text-blue-200 text-left transition-colors">
                      <p class="font-bold text-white text-[11px]">Insp. Kumar</p>
                      <p class="text-[9px] text-slate-400">NDRF Command</p>
                    </button>
                    <button onclick="handleQuickLogin('imd')" class="p-2 rounded-lg bg-[#0e1728] hover:bg-[#142238] border border-blue-900/50 text-blue-200 text-left transition-colors">
                      <p class="font-bold text-white text-[11px]">Dr. S. Roy</p>
                      <p class="text-[9px] text-slate-400">Chief Met.</p>
                    </button>
                    <button onclick="handleQuickLogin('guest')" class="p-2 rounded-lg bg-[#0e1728] hover:bg-[#142238] border border-blue-900/50 text-blue-200 text-left transition-colors">
                      <p class="font-bold text-white text-[11px]">Observer</p>
                      <p class="text-[9px] text-slate-400">Public Guest</p>
                    </button>
                  </div>
                </div>

                <!-- Standard Credentials Form -->
                <form onsubmit="handleFormLogin(event)" class="space-y-3 text-xs font-mono">
                  <div class="space-y-1">
                    <label class="text-slate-400 text-[11px]">Official Email:</label>
                    <input type="text" id="loginEmailInput" value="${state.loginEmail}" oninput="state.loginEmail = this.value" class="w-full p-2.5 rounded-lg bg-[#060a14] border border-[#162338] text-slate-100 focus:outline-none focus:border-blue-500 font-mono" placeholder="officer@ndrf.gov.in" />
                  </div>

                  <div class="grid grid-cols-2 gap-2.5">
                    <div class="space-y-1">
                      <label class="text-slate-400 text-[11px]">Badge ID:</label>
                      <input type="text" id="loginBadgeInput" value="${state.loginBadge}" oninput="state.loginBadge = this.value" class="w-full p-2.5 rounded-lg bg-[#060a14] border border-[#162338] text-slate-100 focus:outline-none focus:border-blue-500 font-mono" />
                    </div>
                    <div class="space-y-1">
                      <label class="text-slate-400 text-[11px]">2FA Token:</label>
                      <input type="text" id="login2faInput" value="${state.login2fa}" oninput="state.login2fa = this.value" class="w-full p-2.5 rounded-lg bg-[#060a14] border border-[#162338] text-emerald-300 font-bold focus:outline-none focus:border-blue-500 font-mono" />
                    </div>
                  </div>

                  <div class="pt-2 flex items-center justify-between">
                    <button type="button" onclick="setState({ activePortalView: 'portal' })" class="px-3.5 py-2 rounded-lg text-slate-400 hover:text-white transition-colors">
                      Cancel
                    </button>
                    <button type="submit" class="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all shadow-md shadow-blue-900/50 flex items-center gap-1.5">
                      <span>Authenticate</span>
                      <span>➔</span>
                    </button>
                  </div>
                </form>
              </div>

              <!-- RIGHT COLUMN: 3D Tactical Pre-Flight Earth Canvas (6 cols) -->
              <div class="lg:col-span-6 w-full space-y-2">
                <div class="flex items-center justify-between px-1 text-[11px] font-mono text-slate-400">
                  <span class="text-blue-400 font-bold flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
                    BAY OF BENGAL RADAR LOCK
                  </span>
                  <span>16.82°N, 84.48°E</span>
                </div>

                <!-- 3D Earth Card -->
                <div class="mission-card border border-[#1b2b45] rounded-2xl overflow-hidden shadow-2xl bg-[#03060f] relative h-[440px]">
                  <div id="loginInteractiveGlobe" class="w-full h-full cursor-grab active:cursor-grabbing"></div>

                  <!-- Floating Badge -->
                  <div class="absolute top-3 left-3 z-10 p-2.5 rounded-xl bg-[#080e1b]/85 border border-white/10 backdrop-blur-md text-[10px] font-mono space-y-0.5 text-slate-300 pointer-events-none shadow-lg">
                    <div class="text-red-400 font-bold">CYCLONE BOB-04 (VSCS)</div>
                    <div>Peak Winds: <strong class="text-white">155 km/h</strong></div>
                    <div>Landfall: <strong class="text-amber-300">Gopalpur (~22.5h)</strong></div>
                  </div>

                  <!-- Usage cue -->
                  <div class="absolute bottom-2.5 inset-x-0 flex justify-center pointer-events-none">
                    <span class="px-3 py-0.5 rounded-full bg-black/60 text-[9px] font-mono text-slate-400 backdrop-blur-sm">
                      Drag to inspect orbital perspective
                    </span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      `;
    }"""

l_start = code.find("    function renderLoginPage() {")
l_end = code.find("    // =========================================================================\n    // MAIN APP RENDER DISPATCHER")

if l_start != -1 and l_end != -1:
    code = code[:l_start] + decluttered_login_html + '\n\n    ' + code[l_end:]

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully decluttered the interface while preserving full interactivity!")
