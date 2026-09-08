with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = """                <!-- Subtle Interaction Hint -->
                <span class="text-[10px] text-slate-500 hidden md:inline">
                  Drag to rotate • Scroll to zoom
                </span>
              </div>
            </div>
          </section>"""

tactical_hud_html = """                <!-- Subtle Interaction Hint -->
                <span class="text-[10px] text-slate-500 hidden md:inline">
                  Drag to rotate • Scroll to zoom
                </span>
              </div>
            </div>

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
          </section>"""

if target in code:
    code = code.replace(target, tactical_hud_html)
    with open('update_portal.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Successfully injected tacticalHudOverlay into update_portal.py!")
else:
    print("Target not found!")
