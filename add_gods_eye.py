#!/usr/bin/env python3
"""
add_gods_eye.py
Implements the cinematic God's Eye orbital reconnaissance sequence:
1. Adds 'God's Eye' button in the Hero text card, floating dock, and header.
2. When clicked, smoothly rotates Earth, expands to cover entire screen,
   zooms dramatically into the storm vortex, and fulfills the page with
   a real-life live satellite feed map (with Zoom Earth HD satellite & ISRO MOSDAC Scorpio toggles).
3. Smooth dismissal returns to rotating 3D Earth.
"""

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add God's Eye controller logic (triggerGodsEyeSequence, transitionToSatelliteMap, exitGodsEye, setGodsEyeSource)
gods_eye_controller = """    // =========================================================================
    // GOD'S EYE ORBITAL RECONNAISSANCE CONTROLLER
    // =========================================================================
    let isGodsEyeActive = false;

    function triggerGodsEyeSequence() {
      isGodsEyeActive = true;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      // 1. Expand Hero Globe to cover the entire screen seamlessly
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
      document.body.style.overflow = 'hidden';

      // 2. Show cinematic reconnaissance targeting reticle over the rotating Earth
      if (godsEyeHud) {
        godsEyeHud.classList.remove('hidden');
        void godsEyeHud.offsetWidth;
        godsEyeHud.classList.remove('opacity-0', 'pointer-events-none');
        godsEyeHud.classList.add('opacity-100', 'pointer-events-auto');
      }

      // 3. Smoothly rotate Earth directly to Bay of Bengal & Cyclone BOB-04 coordinates (16.82N, 84.48E)
      if (inst) {
        inst.setTargetRotation(0.32, Math.PI * 0.965, 2.45);
      }

      // 4. Dramatic Zoom In: Camera plunges down toward the storm center
      const start = performance.now();
      const zoomDuration = 1100;
      
      function plungeCamera(now) {
        const elapsed = now - start;
        const progress = Math.min(1, elapsed / zoomDuration);
        const easeProgress = progress * progress; // Quadratic ease-in plunge
        
        if (inst && inst.camera) {
          // Plunge from 2.45 down to 0.72 into the clouds
          inst.camera.position.z = 2.45 - (2.45 - 0.72) * easeProgress;
          inst.globeGroup.rotation.y = Math.PI * 0.965;
          inst.globeGroup.rotation.x = 0.32;
        }

        if (progress < 1) {
          requestAnimationFrame(plungeCamera);
        } else {
          // 5. Seamlessly fulfill the screen with the live real-life satellite feed map!
          transitionToSatelliteMap();
        }
      }

      // Brief delay for rotation alignment, then plunge camera
      setTimeout(() => {
        requestAnimationFrame(plungeCamera);
      }, 300);
    }

    function transitionToSatelliteMap() {
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      
      if (godsEyeHud) {
        godsEyeHud.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { godsEyeHud.classList.add('hidden'); }, 500);
      }

      if (godsEyeFeed) {
        godsEyeFeed.classList.remove('hidden');
        void godsEyeFeed.offsetWidth;
        godsEyeFeed.classList.remove('opacity-0', 'pointer-events-none');
        godsEyeFeed.classList.add('opacity-100', 'pointer-events-auto');
      }
    }

    function exitGodsEye() {
      isGodsEyeActive = false;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (godsEyeFeed) {
        godsEyeFeed.classList.remove('opacity-100', 'pointer-events-auto');
        godsEyeFeed.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { godsEyeFeed.classList.add('hidden'); }, 600);
      }
      if (godsEyeHud) {
        godsEyeHud.classList.add('hidden', 'opacity-0');
      }

      // Smoothly zoom camera back out to normal orbit
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
    }

    function setGodsEyeSource(source) {
      const iframe = document.getElementById('godsEyeIframe');
      const btnZoom = document.getElementById('btn-gods-zoom');
      const btnScorpio = document.getElementById('btn-gods-scorpio');

      if (source === 'scorpio') {
        if (iframe) iframe.src = '/scorpio_feed?t=' + Date.now();
        if (btnScorpio) {
          btnScorpio.className = 'px-3 py-1 rounded font-bold transition-all bg-emerald-600 text-white shadow cursor-pointer';
        }
        if (btnZoom) {
          btnZoom.className = 'px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer';
        }
      } else {
        if (iframe) iframe.src = '/zoom_earth_feed?t=' + Date.now();
        if (btnZoom) {
          btnZoom.className = 'px-3 py-1 rounded font-bold transition-all bg-blue-600 text-white shadow cursor-pointer';
        }
        if (btnScorpio) {
          btnScorpio.className = 'px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer';
        }
      }
    }
"""

launch_func_marker = "    function launchTacticalDeck() {"
code = code.replace(launch_func_marker, gods_eye_controller + "\n" + launch_func_marker, 1)
print("1. Added God's Eye controller logic.")

# 2. Add God's Eye button to Hero Text Card
old_hero_actions = """                <!-- Minimal Primary Actions -->
                <div class="flex flex-wrap items-center gap-3 pt-1">
                  <button id="launchTacticalBtn" onclick="launchTacticalDeck()" class="relative z-30 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 active:scale-95 text-white font-bold text-sm font-mono transition-all shadow-2xl shadow-blue-900/70 flex items-center gap-3 cursor-pointer border border-blue-400/40 group">
                    <span class="text-lg group-hover:scale-110 transition-transform">🚀</span>
                    <span class="tracking-wide">Launch Tactical Command Deck</span>
                    <span class="text-base group-hover:translate-x-1.5 transition-transform">➔</span>
                  </button>
                  <button onclick="selectPrefaceTarget('cyclone')" class="px-4 py-2.5 rounded-xl bg-[#0e1726]/80 hover:bg-[#162338] border border-[#20314a] text-slate-200 font-mono text-xs backdrop-blur-md transition-colors flex items-center gap-1.5">
                    <span>🌀 Focus Storm Eye</span>
                  </button>
                </div>"""

new_hero_actions = """                <!-- Minimal Primary Actions with God's Eye Satellite Recon -->
                <div class="flex flex-wrap items-center gap-3 pt-1">
                  <button id="launchTacticalBtn" onclick="launchTacticalDeck()" class="relative z-30 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 active:scale-95 text-white font-bold text-sm font-mono transition-all shadow-2xl shadow-blue-900/70 flex items-center gap-3 cursor-pointer border border-blue-400/40 group">
                    <span class="text-lg group-hover:scale-110 transition-transform">🚀</span>
                    <span class="tracking-wide">Launch Tactical Command Deck</span>
                    <span class="text-base group-hover:translate-x-1.5 transition-transform">➔</span>
                  </button>

                  <button id="godsEyeHeroBtn" onclick="triggerGodsEyeSequence()" class="relative z-30 px-5 py-3.5 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-amber-600 hover:from-red-500 hover:to-amber-500 active:scale-95 text-white font-bold text-sm font-mono transition-all shadow-2xl shadow-red-900/70 flex items-center gap-2.5 cursor-pointer border border-red-400/50 group" title="Engage God's Eye Live Satellite Reconnaissance">
                    <span class="text-lg group-hover:scale-125 transition-transform animate-pulse">👁️</span>
                    <span class="tracking-wide">God's Eye</span>
                    <span class="text-xs font-semibold text-amber-200 hidden sm:inline">• Live Satellite</span>
                  </button>

                  <button onclick="selectPrefaceTarget('cyclone')" class="px-4 py-2.5 rounded-xl bg-[#0e1726]/80 hover:bg-[#162338] border border-[#20314a] text-slate-200 font-mono text-xs backdrop-blur-md transition-colors flex items-center gap-1.5 cursor-pointer">
                    <span>🌀 Focus Storm Eye</span>
                  </button>
                </div>"""

if old_hero_actions in code:
    code = code.replace(old_hero_actions, new_hero_actions, 1)
    print("2. Added God's Eye button to Hero Text Card.")
else:
    print("Warning: old_hero_actions not found directly.")

# 3. Add God's Eye button to floating dock
old_dock_btns = """                <!-- Focus Presets -->
                <button onclick="selectPrefaceTarget('cyclone')" class="px-2.5 py-1 rounded-full bg-red-950/80 hover:bg-red-900 border border-red-700/60 text-red-300 text-[11px] font-bold transition-colors flex items-center gap-1">
                  <span>🌀</span>
                  <span>BOB-04</span>
                </button>"""

new_dock_btns = """                <!-- Focus Presets -->
                <button onclick="triggerGodsEyeSequence()" class="px-3 py-1 rounded-full bg-red-950/90 hover:bg-red-900 border border-red-500/70 text-red-300 text-[11px] font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-md shadow-red-900/40" title="Engage God's Eye Satellite Reconnaissance">
                  <span>👁️</span>
                  <span>God's Eye</span>
                </button>
                <button onclick="selectPrefaceTarget('cyclone')" class="px-2.5 py-1 rounded-full bg-[#162238] hover:bg-[#1e2f4c] border border-blue-800/60 text-blue-300 text-[11px] font-bold transition-colors flex items-center gap-1">
                  <span>🌀</span>
                  <span>BOB-04</span>
                </button>"""

if old_dock_btns in code:
    code = code.replace(old_dock_btns, new_dock_btns, 1)
    print("3. Added God's Eye button to floating dock.")
else:
    print("Warning: old_dock_btns not found directly.")

# 4. Add God's Eye button to top header
old_header_nav = """            <!-- Minimal Center Anchors -->
            <nav class="hidden md:flex items-center space-x-6 text-xs font-mono text-slate-300">
              <button onclick="selectPrefaceTarget('cyclone')" class="hover:text-white transition-colors flex items-center gap-1">
                <span>🌀</span>
                <span>Storm Core</span>
              </button>"""

new_header_nav = """            <!-- Minimal Center Anchors -->
            <nav class="hidden md:flex items-center space-x-6 text-xs font-mono text-slate-300">
              <button onclick="triggerGodsEyeSequence()" class="hover:text-red-300 text-red-400 font-bold transition-colors flex items-center gap-1 cursor-pointer">
                <span>👁️</span>
                <span>God's Eye</span>
              </button>
              <button onclick="selectPrefaceTarget('cyclone')" class="hover:text-white transition-colors flex items-center gap-1">
                <span>🌀</span>
                <span>Storm Core</span>
              </button>"""

if old_header_nav in code:
    code = code.replace(old_header_nav, new_header_nav, 1)
    print("4. Added God's Eye link to top header nav.")
else:
    print("Warning: old_header_nav not found directly.")

# 5. Add both godsEyeReconOverlay (plunge HUD) and godsEyeFullscreenFeed (real-life satellite map)
old_hud_block = """            <!-- SEAMLESS FULLSCREEN TACTICAL HUD OVERLAY (ACTIVATES ON LAUNCH) -->
            <div id="tacticalHudOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">
              ${renderTacticalDeckContent()}
            </div>
          </section>"""

new_hud_block = """            <!-- SEAMLESS FULLSCREEN TACTICAL HUD OVERLAY (ACTIVATES ON LAUNCH) -->
            <div id="tacticalHudOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">
              ${renderTacticalDeckContent()}
            </div>

            <!-- GOD'S EYE DESCENT RECON OVERLAY (ACTIVE DURING CAMERA PLUNGE) -->
            <div id="godsEyeReconOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-300 flex flex-col justify-between p-6 sm:p-10 select-none font-mono">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3 bg-black/75 border border-red-500/60 backdrop-blur-md px-4 py-2 rounded-xl text-xs">
                  <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></span>
                  <span class="font-bold text-red-400">GOD'S EYE: ENGAGING SATELLITE RECON PROTOCOL</span>
                  <span class="text-slate-500">•</span>
                  <span class="text-slate-300">TARGET: 16.82°N, 84.48°E (BOB-04)</span>
                </div>
                <div class="bg-black/75 border border-cyan-500/50 backdrop-blur-md px-3.5 py-2 rounded-xl text-xs text-cyan-300">
                  ALTITUDE: 35,786 KM ➔ LOW EARTH ORBIT (420 KM)
                </div>
              </div>

              <!-- Reticle Target -->
              <div class="relative flex items-center justify-center my-auto">
                <div class="w-56 h-56 border-2 border-dashed border-red-500/70 rounded-full animate-spin flex items-center justify-center" style="animation-duration: 10s;">
                  <div class="w-40 h-40 border border-cyan-400/60 rounded-full flex items-center justify-center">
                    <div class="w-2 h-2 rounded-full bg-red-500 animate-ping"></div>
                  </div>
                </div>
                <div class="absolute w-72 h-px bg-gradient-to-r from-transparent via-red-500 to-transparent"></div>
                <div class="absolute h-72 w-px bg-gradient-to-b from-transparent via-red-500 to-transparent"></div>
                <div class="absolute text-[11px] font-bold text-red-400 tracking-widest uppercase mt-36 bg-black/60 px-3 py-1 rounded">
                  LOCKING SATELLITE OPTICAL FEED [INSAT-3DR TIR]
                </div>
              </div>

              <div class="flex items-center justify-between text-xs text-slate-300">
                <div class="bg-black/75 border border-white/10 px-3.5 py-2 rounded-xl backdrop-blur-md">
                  RSMC IMD CYCLONE BOB-04 • 155 KM/H SUSTAINED WINDS
                </div>
                <div class="bg-black/75 border border-emerald-500/40 px-3.5 py-2 rounded-xl backdrop-blur-md text-emerald-400 font-bold">
                  FULFILLING REAL-TIME SATELLITE MAP...
                </div>
              </div>
            </div>
          </section>

          <!-- FULLSCREEN REAL-LIFE LIVE SATELLITE FEED MAP (GOD'S EYE) -->
          <div id="godsEyeFullscreenFeed" class="hidden fixed inset-0 z-50 bg-black flex flex-col transition-opacity duration-700 opacity-0 pointer-events-none select-none font-sans">
            
            <!-- RECON SATELLITE MAP HEADER -->
            <header class="h-14 px-4 sm:px-6 bg-[#060b14]/90 backdrop-blur-xl border-b border-white/10 flex items-center justify-between z-30 shrink-0 select-none">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded-lg bg-red-950/80 border border-red-500/60 flex items-center justify-center text-red-400 font-bold text-sm shadow-lg animate-pulse">
                  👁️
                </div>
                <div>
                  <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-sm text-white tracking-wide font-heading">
                      GOD'S EYE
                    </span>
                    <span class="text-[10px] font-mono font-bold text-red-300 bg-red-950/80 border border-red-800 px-2 py-0.5 rounded">
                      ● LIVE SATELLITE FEED
                    </span>
                    <span class="text-[10px] font-mono text-slate-400 hidden sm:inline">
                      REALTIME ORBITAL COMPOSITE • BAY OF BENGAL
                    </span>
                  </div>
                </div>
              </div>

              <!-- Center: Feed Mode Toggles -->
              <div class="flex items-center bg-[#070d1a] p-1 rounded-lg border border-white/10 text-xs font-mono">
                <button onclick="setGodsEyeSource('zoom_earth')" id="btn-gods-zoom" class="px-3 py-1 rounded font-bold transition-all bg-blue-600 text-white shadow cursor-pointer">
                  🛰️ HD Live Satellite
                </button>
                <button onclick="setGodsEyeSource('scorpio')" id="btn-gods-scorpio" class="px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer">
                  📡 ISRO MOSDAC Scorpio
                </button>
              </div>

              <!-- Right: Telemetry & Exit -->
              <div class="flex items-center space-x-3 text-xs font-mono">
                <span class="text-emerald-400 hidden lg:inline font-bold">16.82°N, 84.48°E</span>
                <span class="text-slate-600 hidden lg:inline">|</span>
                <button onclick="exitGodsEye()" class="px-3.5 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 border border-red-500/60 text-white font-semibold transition-all flex items-center gap-1.5 cursor-pointer shadow-md">
                  <span>✕</span>
                  <span>Exit God's Eye</span>
                </button>
              </div>
            </header>

            <!-- Real-Life Satellite Feed Viewport (Fulfills Entire Screen) -->
            <div class="relative flex-1 w-full h-full overflow-hidden bg-black">
              <iframe id="godsEyeIframe" src="/zoom_earth_feed" class="w-full h-full border-0" allow="fullscreen; geolocation"></iframe>
              
              <!-- Subtle Tactical Recon HUD Over Map -->
              <div class="absolute top-4 left-4 pointer-events-none select-none z-20">
                <div class="font-mono text-[11px] text-cyan-300 bg-black/75 px-3 py-2 rounded-xl border border-cyan-500/40 backdrop-blur-md space-y-0.5 shadow-xl">
                  <p class="font-bold text-white flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                    <span>ORBITAL RECONNAISSANCE TARGET LOCK</span>
                  </p>
                  <p class="text-slate-300">Target: Cyclone BOB-04 Vortex Eye (16.82°N, 84.48°E)</p>
                  <p class="text-cyan-400 text-[10px]">Sensor: INSAT-3DR High-Res Multispectral Imager</p>
                </div>
              </div>

              <!-- Bottom Telemetry HUD -->
              <div class="absolute bottom-4 inset-x-4 pointer-events-none select-none z-20 flex justify-between items-end">
                <div class="font-mono text-[11px] text-slate-300 bg-black/75 px-3 py-2 rounded-xl border border-white/10 backdrop-blur-md shadow-xl">
                  <span>Landfall Target: <strong class="text-white">Gopalpur, Odisha</strong></span>
                  <span class="mx-2 text-slate-600">•</span>
                  <span>ETA: <strong class="text-red-400">~22.5 Hours</strong></span>
                </div>

                <div class="font-mono text-[10px] text-slate-400 bg-black/75 px-3 py-1.5 rounded-xl border border-white/10 backdrop-blur-md">
                  Use map pan & scroll to explore live cloud fronts • Double-click to zoom
                </div>
              </div>
            </div>
          </div>"""

if old_hud_block in code:
    code = code.replace(old_hud_block, new_hud_block, 1)
    print("5. Added godsEyeReconOverlay and godsEyeFullscreenFeed elements.")
else:
    print("Warning: old_hud_block not found directly.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py. Now executing...")
