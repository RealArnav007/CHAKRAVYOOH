import os

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Replace the JS functions block
js_start = "    let godsEyeMap = null;"
js_end = "    function launchTacticalDeck() {"

idx1 = code.find(js_start)
idx2 = code.find(js_end)

if idx1 == -1 or idx2 == -1:
    print(f"ERROR: Could not locate JS bounds! idx1={idx1}, idx2={idx2}")
    exit(1)

pure_mosdac_js = """    function transitionToSatelliteMap() {
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      const godsEyeIframe = document.getElementById('godsEyeIframe');
      
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

      // Ensure iframe loads live ISRO MOSDAC Scorpio relay
      if (godsEyeIframe && (!godsEyeIframe.src || godsEyeIframe.src.indexOf('/scorpio_feed') === -1)) {
        godsEyeIframe.src = '/scorpio_feed';
      }
    }

    function refreshGodsEyeFeed() {
      const iframe = document.getElementById('godsEyeIframe');
      if (iframe) {
        iframe.src = '/scorpio_feed?t=' + Date.now();
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
"""

code = code[:idx1] + pure_mosdac_js + "\n" + code[idx2:]
print("Updated JS functions to pure MOSDAC relay.")

# 2. Replace the godsEyeFullscreenFeed HTML modal
html_start = '          <!-- FULLSCREEN REAL-LIFE LIVE SATELLITE FEED MAP (GOD\'S EYE) -->'
html_end = '          <!-- 4. PIXEL-ART WEATHER WIDGETS DECK'

h_idx1 = code.find(html_start)
h_idx2 = code.find(html_end)

if h_idx1 == -1 or h_idx2 == -1:
    print(f"ERROR: Could not locate HTML bounds! h_idx1={h_idx1}, h_idx2={h_idx2}")
    exit(1)

pure_mosdac_html = """          <!-- FULLSCREEN REAL-LIFE ISRO MOSDAC SATELLITE RELAY (GOD'S EYE) -->
          <div id="godsEyeFullscreenFeed" class="hidden fixed inset-0 z-50 bg-[#060b14] flex flex-col transition-opacity duration-700 opacity-0 pointer-events-none select-none font-sans">
            
            <!-- MOSDAC REAL LIFE RELAY HEADER -->
            <header class="h-14 px-4 sm:px-6 bg-[#060b14]/95 backdrop-blur-xl border-b border-white/10 flex items-center justify-between z-30 shrink-0 select-none">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded-lg bg-red-950/80 border border-red-500/60 flex items-center justify-center text-red-400 font-bold text-sm shadow-lg animate-pulse">
                  👁️
                </div>
                <div>
                  <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-sm text-white tracking-wide font-heading">
                      GOD'S EYE
                    </span>
                    <span class="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-700/60 px-2 py-0.5 rounded flex items-center gap-1">
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                      ISRO MOSDAC SCORPIO • REAL-TIME SATELLITE RELAY
                    </span>
                  </div>
                  <p class="text-[10px] font-mono text-slate-400 hidden sm:block">
                    INSAT-3DR / 3DS RAPID SCAN MULTI-SPECTRAL THERMAL INFRARED • BAY OF BENGAL
                  </p>
                </div>
              </div>

              <!-- Right: Telemetry, Refresh & Exit -->
              <div class="flex items-center space-x-3 text-xs font-mono">
                <div class="hidden md:flex items-center space-x-2 bg-black/60 border border-white/10 px-3 py-1 rounded-lg text-[11px]">
                  <span class="text-slate-400">Target Lock:</span>
                  <span class="text-red-400 font-bold">16.82°N, 84.48°E (BOB-04)</span>
                </div>

                <button onclick="refreshGodsEyeFeed()" class="px-3 py-1.5 rounded-lg bg-[#0e1726] hover:bg-[#162338] border border-[#20314a] text-slate-200 hover:text-white transition-colors flex items-center gap-1.5 cursor-pointer shadow" title="Refresh Live MOSDAC Feed">
                  <span>🔄</span>
                  <span class="hidden sm:inline">Refresh</span>
                </button>

                <button onclick="exitGodsEye()" class="px-3.5 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 border border-red-500/60 text-white font-semibold transition-all flex items-center gap-1.5 cursor-pointer shadow-md">
                  <span>✕</span>
                  <span>Exit God's Eye</span>
                </button>
              </div>
            </header>

            <!-- Real-Life ISRO MOSDAC SCORPIO Feed Viewport (Fulfills Entire Screen) -->
            <div class="relative flex-1 w-full h-full overflow-hidden bg-[#060b14]">
              <iframe id="godsEyeIframe" src="/scorpio_feed" class="w-full h-full border-0" allow="fullscreen; geolocation"></iframe>
            </div>
          </div>
"""

code = code[:h_idx1] + pure_mosdac_html + "\n" + code[h_idx2:]
print("Updated HTML to pure MOSDAC relay modal.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("update_portal.py written successfully.")
