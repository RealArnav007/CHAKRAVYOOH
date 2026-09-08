import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update initInteractiveGlobe so it reuses existing active renderer canvas without tearing down
old_teardown = """      // Teardown any existing instance for this container
      if (activeGlobeInstances[containerId]) {
        try {
          cancelAnimationFrame(activeGlobeInstances[containerId].animId);
          activeGlobeInstances[containerId].renderer.dispose();
          container.innerHTML = '';
        } catch (e) {}
        delete activeGlobeInstances[containerId];
      }"""

new_teardown = """      // Reuse active renderer if container already holds canvas to preserve 60fps Earth state
      if (activeGlobeInstances[containerId] && container.querySelector('canvas')) {
        const inst = activeGlobeInstances[containerId];
        if (inst && inst.camera && inst.renderer) {
          const w = container.clientWidth || 800;
          const h = container.clientHeight || 500;
          inst.camera.aspect = w / h;
          inst.camera.updateProjectionMatrix();
          inst.renderer.setSize(w, h);
        }
        return;
      }
      if (activeGlobeInstances[containerId]) {
        try {
          cancelAnimationFrame(activeGlobeInstances[containerId].animId);
          activeGlobeInstances[containerId].renderer.dispose();
          container.innerHTML = '';
        } catch (e) {}
        delete activeGlobeInstances[containerId];
      }"""

if old_teardown in code:
    code = code.replace(old_teardown, new_teardown)
    print("Updated initInteractiveGlobe canvas persistence")

# 2. Add launchTacticalDeck, exitTacticalDeck, openLoginModal, closeLoginModal
tactical_functions = """    // =========================================================================
    // SEAMLESS 3D GLOBE LAUNCH & TACTICAL FULLSCREEN CONTROLLER
    // =========================================================================
    let isTacticalExpanded = false;

    function launchTacticalDeck() {
      isTacticalExpanded = true;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (hero) {
        hero.classList.remove('relative', 'min-h-[640px]', 'lg:min-h-[700px]');
        hero.classList.add('fixed', 'inset-0', 'z-50', 'w-screen', 'h-screen');
      }
      if (textCard) {
        textCard.classList.add('opacity-0', 'pointer-events-none', '-translate-y-8', 'scale-95');
      }
      if (heroDock) {
        heroDock.classList.add('opacity-0', 'pointer-events-none');
      }
      if (hud) {
        hud.classList.remove('opacity-0', 'pointer-events-none');
        hud.classList.add('opacity-100', 'pointer-events-auto');
      }
      document.body.style.overflow = 'hidden';

      // Three.js: Animate Globe forward in 3D perspective to fill screen!
      if (inst) {
        // Swoop camera close to Bay of Bengal & Cyclone BOB-04 vortex (dist: 1.32)
        inst.setTargetRotation(0.32, Math.PI * 0.965, 1.32);
        
        // Smoothly resize WebGL renderer across transition duration
        const start = performance.now();
        function smoothResize() {
          if (inst && inst.camera && inst.renderer) {
            const w = window.innerWidth;
            const h = window.innerHeight;
            inst.camera.aspect = w / h;
            inst.camera.updateProjectionMatrix();
            inst.renderer.setSize(w, h);
          }
          if (performance.now() - start < 850) {
            requestAnimationFrame(smoothResize);
          }
        }
        requestAnimationFrame(smoothResize);
      }
    }

    function exitTacticalDeck() {
      isTacticalExpanded = false;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (hud) {
        hud.classList.remove('opacity-100', 'pointer-events-auto');
        hud.classList.add('opacity-0', 'pointer-events-none');
      }
      if (textCard) {
        textCard.classList.remove('opacity-0', 'pointer-events-none', '-translate-y-8', 'scale-95');
      }
      if (heroDock) {
        heroDock.classList.remove('opacity-0', 'pointer-events-none');
      }
      if (hero) {
        hero.classList.remove('fixed', 'inset-0', 'z-50', 'w-screen', 'h-screen');
        hero.classList.add('relative', 'min-h-[640px]', 'lg:min-h-[700px]');
      }
      document.body.style.overflow = '';

      // Three.js: Animate Globe smoothly back out to overview!
      if (inst) {
        inst.setTargetRotation(0.28, Math.PI * 0.96, 2.45);
        const start = performance.now();
        function smoothResize() {
          if (hero && inst && inst.camera && inst.renderer) {
            const w = hero.clientWidth || window.innerWidth;
            const h = hero.clientHeight || 700;
            inst.camera.aspect = w / h;
            inst.camera.updateProjectionMatrix();
            inst.renderer.setSize(w, h);
          }
          if (performance.now() - start < 850) {
            requestAnimationFrame(smoothResize);
          }
        }
        requestAnimationFrame(smoothResize);
      }
    }

    function openLoginModal() {
      const m = document.getElementById('officerLoginModal');
      if (m) m.classList.remove('hidden');
    }

    function closeLoginModal() {
      const m = document.getElementById('officerLoginModal');
      if (m) m.classList.add('hidden');
    }
"""

if "function selectPrefaceTarget(target) {" in code and "function launchTacticalDeck()" not in code:
    code = code.replace("function selectPrefaceTarget(target) {", tactical_functions + "\n    function selectPrefaceTarget(target) {")
    print("Added tactical launch & exit functions")

# 3. Replace launch buttons in header and hero section with launchTacticalDeck()
code = code.replace(
    'onclick="setState({ activePortalView: \'command_center\' })"',
    'onclick="launchTacticalDeck()"'
)
print("Replaced launch button triggers with launchTacticalDeck()")

# 4. Replace Officer Access and Login buttons with openLoginModal()
code = code.replace(
    'onclick="setState({ activePortalView: \'login\' })"',
    'onclick="openLoginModal()"'
)
print("Replaced login navigation with openLoginModal()")

# 5. Update hero section structure to include ids and the tactical HUD overlay
old_hero_start = """          <!-- 3. CLEAN, BREATHABLE FULL-BLEED 3D HERO CANVAS -->
          <section class="relative min-h-[640px] lg:min-h-[700px] flex items-center overflow-hidden border-b border-[#142033] bg-[#03060f]">
            <!-- 100% Native WebGL Photorealistic NASA 3D Earth -->
            <div id="prefaceInteractiveGlobe" class="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing z-0"></div>

            <!-- Subtle Vignette to Guarantee Typography Readability -->
            <div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#03060f]/90 via-[#03060f]/50 to-transparent z-[1]"></div>
            <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#03060f] via-transparent to-[#03060f]/60 z-[1]"></div>

            <!-- HERO TEXT (Clean, Minimal, Authoritative) -->
            <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-12 w-full pointer-events-none">
              <div class="max-w-xl space-y-5 pointer-events-auto">"""

new_hero_start = """          <!-- 3. CLEAN, BREATHABLE FULL-BLEED 3D HERO CANVAS -->
          <section id="heroGlobeSection" class="relative min-h-[640px] lg:min-h-[700px] flex items-center overflow-hidden border-b border-[#142033] bg-[#03060f] transition-all duration-700 ease-out">
            <!-- 100% Native WebGL Photorealistic NASA 3D Earth -->
            <div id="prefaceInteractiveGlobe" class="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing z-0"></div>

            <!-- Subtle Vignette to Guarantee Typography Readability -->
            <div id="heroVignetteL" class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#03060f]/90 via-[#03060f]/50 to-transparent z-[1] transition-opacity duration-700"></div>
            <div id="heroVignetteB" class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#03060f] via-transparent to-[#03060f]/60 z-[1] transition-opacity duration-700"></div>

            <!-- HERO TEXT (Clean, Minimal, Authoritative) -->
            <div id="heroTextCard" class="relative z-10 max-w-7xl mx-auto px-4 sm:px-8 py-12 w-full pointer-events-none transition-all duration-500 transform">
              <div class="max-w-xl space-y-5 pointer-events-auto">"""

if old_hero_start in code:
    code = code.replace(old_hero_start, new_hero_start)
    print("Updated hero start with IDs and transitions")

# Give hero dock an id
code = code.replace(
    '<!-- UNIFIED ELEGANT FLOATING DOCK (Zoom Earth / Apple Minimal Style) -->\n            <div class="absolute bottom-6 inset-x-4 z-20 flex justify-center pointer-events-none">',
    '<!-- UNIFIED ELEGANT FLOATING DOCK (Zoom Earth / Apple Minimal Style) -->\n            <div id="heroDock" class="absolute bottom-6 inset-x-4 z-20 flex justify-center pointer-events-none transition-all duration-500">'
)

# 6. Inject Tactical HUD Overlay inside heroGlobeSection right before </section>
tactical_hud_html = """
            <!-- SEAMLESS FULLSCREEN TACTICAL HUD OVERLAY (ACTIVATES ON LAUNCH) -->
            <div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-between p-4 sm:p-6 select-none font-mono">
              
              <!-- TOP TACTICAL COMMAND BAR -->
              <div class="w-full flex items-center justify-between gap-3 pointer-events-auto">
                <div class="flex items-center gap-2.5 bg-[#080e1b]/85 border border-blue-500/30 backdrop-blur-xl px-4 py-2 rounded-2xl shadow-2xl text-xs">
                  <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                  <span class="font-extrabold text-white tracking-wide font-heading">CHAKRAVYOOH TACTICAL ORBITAL DECK</span>
                  <span class="text-slate-600 hidden sm:inline">|</span>
                  <span class="text-blue-300 font-bold hidden sm:inline">CYCLONE BOB-04 (VSCS)</span>
                  <span class="text-emerald-400 font-semibold hidden md:inline">155 km/h • 948 hPa</span>
                </div>

                <!-- Action Controls & Exit Button -->
                <div class="flex items-center gap-2">
                  <button onclick="selectPrefaceTarget('cyclone'); const inst = activeGlobeInstances['prefaceInteractiveGlobe']; if (inst) inst.setTargetRotation(0.32, Math.PI * 0.965, 1.32);" class="px-3 py-1.5 rounded-xl bg-[#0e1728]/85 hover:bg-blue-950 border border-blue-800/60 text-blue-200 text-xs transition-colors flex items-center gap-1">
                    <span>🌀</span>
                    <span class="hidden sm:inline">Storm Eye</span>
                  </button>
                  <button onclick="selectPrefaceTarget('gopalpur'); const inst = activeGlobeInstances['prefaceInteractiveGlobe']; if (inst) inst.setTargetRotation(0.35, Math.PI * 0.96, 1.38);" class="px-3 py-1.5 rounded-xl bg-[#0e1728]/85 hover:bg-red-950 border border-red-800/60 text-red-300 text-xs transition-colors flex items-center gap-1">
                    <span>📍</span>
                    <span class="hidden sm:inline">Landfall</span>
                  </button>
                  <button onclick="selectPrefaceTarget('india'); const inst = activeGlobeInstances['prefaceInteractiveGlobe']; if (inst) inst.setTargetRotation(0.35, Math.PI * 0.94, 1.6);" class="px-3 py-1.5 rounded-xl bg-[#0e1728]/85 hover:bg-slate-800 border border-slate-700/60 text-slate-300 text-xs transition-colors flex items-center gap-1">
                    <span>🇮🇳</span>
                    <span class="hidden sm:inline">India</span>
                  </button>
                  <button onclick="toggleGlobeAutoRotate()" class="px-2.5 py-1.5 rounded-xl bg-[#0e1728]/85 hover:bg-slate-800 border border-slate-700/60 text-slate-300 text-xs transition-colors" title="Toggle Spin">
                    ▶️
                  </button>
                  <!-- Exit Button -->
                  <button onclick="exitTacticalDeck()" class="px-4 py-1.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-lg shadow-red-900/50 transition-all flex items-center gap-1.5">
                    <span>✕</span>
                    <span>Exit Tactical View</span>
                  </button>
                </div>
              </div>

              <!-- MIDDLE ROW: FLOATING GLASSMETRIC INTEL DECKS -->
              <div class="w-full grid grid-cols-1 md:grid-cols-12 gap-4 my-auto pointer-events-none">
                
                <!-- LEFT DOCK: Multi-Source Satellite & AI Fusion -->
                <div class="md:col-span-4 lg:col-span-3 pointer-events-auto space-y-2.5">
                  <div class="mission-card p-4 space-y-3 bg-[#080e1b]/80 border border-blue-500/30 backdrop-blur-xl shadow-2xl rounded-2xl text-xs">
                    <div class="flex items-center justify-between border-b border-blue-900/40 pb-2">
                      <span class="text-blue-400 font-bold flex items-center gap-1.5">
                        <span>🛰️</span>
                        <span>LIVE SATELLITE FEEDS</span>
                      </span>
                      <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">15-min scan</span>
                    </div>

                    <div class="space-y-2 text-[11px]">
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">INSAT-3DR TIR-1:</span>
                        <span class="text-blue-300 font-bold">-78.4°C (Eye Core)</span>
                      </div>
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">EOS-06 Scatterometer:</span>
                        <span class="text-emerald-400 font-bold">148 km/h Ku-Band</span>
                      </div>
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">INCOIS BD08 Buoy:</span>
                        <span class="text-amber-400 font-bold">7.2m Swell • 29.4°C</span>
                      </div>
                      <div class="flex items-center justify-between border-t border-slate-800 pt-1.5">
                        <span class="text-slate-400">PINN Model Confidence:</span>
                        <span class="text-emerald-400 font-bold">94% (Mature Cat-3)</span>
                      </div>
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">Landfall ETA:</span>
                        <span class="text-red-400 font-bold">22h 45m (Gopalpur)</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Spacer Column -->
                <div class="hidden md:block md:col-span-4 lg:col-span-6"></div>

                <!-- RIGHT DOCK: Geospatial Risk Corridors & Resilient Mesh -->
                <div class="md:col-span-4 lg:col-span-3 pointer-events-auto space-y-2.5">
                  <div class="mission-card p-4 space-y-3 bg-[#080e1b]/80 border border-red-500/30 backdrop-blur-xl shadow-2xl rounded-2xl text-xs">
                    <div class="flex items-center justify-between border-b border-red-900/40 pb-2">
                      <span class="text-red-400 font-bold flex items-center gap-1.5">
                        <span>⚠️</span>
                        <span>GEOSPATIAL RISK ZONES</span>
                      </span>
                      <span class="text-[10px] px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 animate-pulse">EXTREME</span>
                    </div>

                    <div class="space-y-2 text-[11px]">
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">Zone A (Gopalpur):</span>
                        <span class="text-red-400 font-bold">92/100 • Surge 3.8m</span>
                      </div>
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">Zone B (Puri Coast):</span>
                        <span class="text-amber-400 font-bold">74/100 • Cat-2 Wind</span>
                      </div>
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">Zone C (Bhubaneswar):</span>
                        <span class="text-blue-300 font-bold">52/100 • Rain 210mm</span>
                      </div>
                      <div class="flex items-center justify-between border-t border-slate-800 pt-1.5">
                        <span class="text-slate-400">Chakravyooh Mesh Nodes:</span>
                        <span class="text-emerald-400 font-bold">142 Synced</span>
                      </div>
                      <div class="flex items-center justify-between">
                        <span class="text-slate-400">Offline P2P Alerting:</span>
                        <span class="text-emerald-400 font-bold">ARMED & ACTIVE ✓</span>
                      </div>
                    </div>
                  </div>
                </div>

              </div>

              <!-- BOTTOM TACTICAL FOOTER HUD -->
              <div class="w-full flex items-center justify-between gap-3 pointer-events-auto">
                <div class="bg-[#080e1b]/85 border border-white/10 backdrop-blur-xl px-4 py-2 rounded-2xl shadow-2xl text-xs flex items-center gap-3">
                  <span class="text-emerald-400 font-bold">16° 49' N  84° 28' E</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-slate-300">08-SEP-2026 15:15 IST</span>
                  <span class="text-slate-600 hidden sm:inline">•</span>
                  <span class="text-slate-400 hidden sm:inline">INSAT-3DR Multispectral Geostationary Sweep</span>
                </div>

                <div class="text-[11px] text-slate-400 bg-[#080e1b]/85 border border-white/10 backdrop-blur-xl px-3 py-2 rounded-2xl hidden md:block">
                  Drag to rotate 360° • Scroll to zoom • Click targets to focus
                </div>
              </div>

            </div>
"""

target_end_section = """            </div>
          </section>"""

if target_end_section in code and "tacticalHudOverlay" not in code:
    code = code.replace(target_end_section, "            </div>" + tactical_hud_html + "\n          </section>")
    print("Injected tactical HUD overlay into hero section")

# 7. Add renderOfficerLoginModal function
login_modal_html = """
    // =========================================================================
    // OFFICER LOGIN MODAL (INTEGRATED ON THE PUBLIC PORTAL)
    // =========================================================================
    function renderOfficerLoginModal() {
      return `
        <div id="officerLoginModal" class="fixed inset-0 z-[100] hidden flex items-center justify-center bg-black/80 backdrop-blur-md p-4 select-none font-sans">
          <div class="relative w-full max-w-lg mission-card p-6 sm:p-8 space-y-5 border border-[#1b2b45] shadow-2xl bg-[#090e1b] rounded-2xl">
            <!-- Close Button -->
            <button onclick="closeLoginModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg bg-[#142034] text-xs transition-colors">
              ✕ Close
            </button>

            <div class="flex items-center space-x-3 border-b border-[#162338] pb-3">
              <div class="w-10 h-10 rounded-xl bg-blue-900/60 border border-blue-500/40 flex items-center justify-center text-blue-300 font-bold text-lg">
                🔐
              </div>
              <div>
                <h2 class="text-base font-bold text-white font-heading">Officer Authentication</h2>
                <p class="text-xs font-mono text-slate-400">CHAKRAVYOOH Emergency Operations System</p>
              </div>
            </div>

            <!-- Role Switcher -->
            <div class="grid grid-cols-4 gap-1 p-1 bg-[#060a14] rounded-lg text-xs font-mono border border-[#142032]">
              <button onclick="handleSelectLoginRole('ndrf')" class="py-1.5 rounded ${state.loginRole === 'ndrf' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">NDRF</button>
              <button onclick="handleSelectLoginRole('imd')" class="py-1.5 rounded ${state.loginRole === 'imd' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">IMD</button>
              <button onclick="handleSelectLoginRole('district')" class="py-1.5 rounded ${state.loginRole === 'district' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">SDMA</button>
              <button onclick="handleSelectLoginRole('guest')" class="py-1.5 rounded ${state.loginRole === 'guest' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'} transition-colors">Guest</button>
            </div>

            <!-- 1-Click Fast Fill Credentials -->
            <div class="space-y-1.5">
              <div class="text-[11px] font-mono text-slate-400">1-Click Evaluator Presets:</div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
                <button onclick="handleQuickLogin('ndrf')" class="p-2 rounded-lg bg-[#0e1728] hover:bg-[#142238] border border-blue-900/50 text-blue-200 text-left transition-colors">
                  <div class="font-bold">⚡ Insp. Kumar</div>
                  <div class="text-[10px] text-slate-400">NDRF Field</div>
                </button>
                <button onclick="handleQuickLogin('imd')" class="p-2 rounded-lg bg-[#0e1728] hover:bg-[#142238] border border-blue-900/50 text-blue-200 text-left transition-colors">
                  <div class="font-bold">⚡ Dr. S. Roy</div>
                  <div class="text-[10px] text-slate-400">Chief Met</div>
                </button>
                <button onclick="handleQuickLogin('guest')" class="p-2 rounded-lg bg-[#0e1728] hover:bg-[#142238] border border-blue-900/50 text-blue-200 text-left transition-colors">
                  <div class="font-bold">⚡ Public Guest</div>
                  <div class="text-[10px] text-slate-400">Observer</div>
                </button>
              </div>
            </div>

            <!-- Form -->
            <form onsubmit="handleFormLogin(event); closeLoginModal(); launchTacticalDeck();" class="space-y-3 text-xs font-mono">
              <div>
                <label class="block text-slate-400 text-[11px] mb-1">Official Identification Email</label>
                <input type="text" id="loginEmailInput" value="${state.loginEmail}" oninput="state.loginEmail = this.value" class="w-full p-2.5 rounded-lg bg-[#060a14] border border-[#162338] text-slate-100 focus:outline-none focus:border-blue-500 font-mono" placeholder="officer@ndrf.gov.in" />
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-slate-400 text-[11px] mb-1">Service Badge ID</label>
                  <input type="text" id="loginBadgeInput" value="${state.loginBadge}" oninput="state.loginBadge = this.value" class="w-full p-2.5 rounded-lg bg-[#060a14] border border-[#162338] text-slate-100 focus:outline-none focus:border-blue-500 font-mono" />
                </div>
                <div>
                  <label class="block text-slate-400 text-[11px] mb-1">2FA Hardware Token</label>
                  <input type="text" id="login2faInput" value="${state.login2fa}" oninput="state.login2fa = this.value" class="w-full p-2.5 rounded-lg bg-[#060a14] border border-[#162338] text-emerald-300 font-bold focus:outline-none focus:border-blue-500 font-mono" />
                </div>
              </div>

              <div class="pt-2 flex items-center justify-end gap-2">
                <button type="button" onclick="closeLoginModal()" class="px-3 py-2 rounded-lg text-slate-400 hover:text-white transition-colors">
                  Cancel
                </button>
                <button type="submit" class="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold transition-all shadow-lg shadow-blue-900/50 flex items-center gap-1.5">
                  <span>Authorize & Launch Deck</span>
                  <span>➔</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      `;
    }
"""

if "function renderOfficerLoginModal()" not in code:
    code = code.replace("function renderLoginPage() {", login_modal_html + "\n    function renderLoginPage() {")
    print("Added renderOfficerLoginModal()")

# 8. Ensure renderApp() makes the public portal the ONLY interface page
old_render_app = """    function renderApp() {
      setTimeout(mountAllGlobes, 50);
      const container = document.getElementById('app');
      if (!container) return;

      // Starting Page: NASA / ISRO Style Exploration Portal
      if (state.activePortalView === 'portal') {
        container.innerHTML = `
          ${renderNasaPortal()}
          ${renderLoadingScreen()}
        `;
        return;
      }

      // Dedicated Login Portal Page
      if (state.activePortalView === 'login') {
        container.innerHTML = `
          ${renderLoginPage()}
          ${renderLoadingScreen()}
        `;
        return;
      }

      // Operational Tactical Command Center
      container.innerHTML = `
        <div class="min-h-screen text-slate-100 flex flex-col font-sans">
          ${renderGlobalHeader()}
          
          <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
            ${state.activeScreen === 'screen1_hero' ? renderScreen1Hero() : ''}
            ${state.activeScreen === 'screen2_ai' ? renderScreen2AI() : ''}
            ${state.activeScreen === 'screen3_risk' ? renderScreen3Risk() : ''}
            ${state.activeScreen === 'screen4_resilience' ? renderScreen4Resilience() : ''}
          </main>

          <!-- Clean Human Operational Footer -->
          <footer class="border-t border-[#1b2840] bg-[#0c1322] py-4 px-4 text-center text-xs font-mono text-slate-400">
            <p>CHAKRAVYOOH — National Cyclone Intelligence & Resilient Operations System</p>
            <p class="text-slate-500 text-[11px] mt-0.5">ISRO INSAT-3DR / 3DS Multispectral Fusion & Ad-Hoc Peer-to-Peer Mesh Warning Delivery</p>
          </footer>

          ${renderIngestModal()}
          ${renderLoadingScreen()}
        </div>
      `;
    }"""

new_render_app = """    function renderApp() {
      setTimeout(mountAllGlobes, 50);
      const container = document.getElementById('app');
      if (!container) return;

      // THE PUBLIC PORTAL IS THE ONLY INTERFACE PAGE
      container.innerHTML = `
        ${renderNasaPortal()}
        ${renderOfficerLoginModal()}
        ${renderLoadingScreen()}
      `;
    }"""

if old_render_app in code:
    code = code.replace(old_render_app, new_render_app)
    print("Locked renderApp to the single public portal interface page")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully updated update_portal.py!")
