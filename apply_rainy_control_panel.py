import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Locate tacticalHudOverlay inside update_portal.py
old_overlay_pattern = r'<div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-between p-4 sm:p-6 select-none font-mono">[\s\S]*?<\/div>\s*<\/section>'

new_overlay = """<div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-4 sm:p-8 select-none font-sans overflow-y-auto">
              
              <!-- MAIN CONTROL PANEL (EXACT USER REFERENCE: RAINY WINDOW STORM BACKGROUND) -->
              <div class="relative w-full max-w-5xl rounded-3xl overflow-hidden shadow-2xl border border-white/20 text-white pointer-events-auto my-auto backdrop-blur-2xl bg-cover bg-center transition-all duration-500" style="background-image: linear-gradient(to right, rgba(8, 12, 22, 0.86) 0%, rgba(8, 12, 22, 0.68) 45%, rgba(8, 12, 22, 0.82) 100%), url('/static/rainy_storm_bg.jpg'); box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 40px rgba(14, 165, 233, 0.15);">
                
                <!-- TOP HEADER STRIP -->
                <div class="flex items-center justify-between px-6 py-3.5 border-b border-white/10 bg-black/40 backdrop-blur-md">
                  <div class="flex items-center gap-2.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                    <span class="font-extrabold text-sm sm:text-base tracking-wider font-heading text-white">CHAKRAVYOOH MAIN CONTROL PANEL</span>
                    <span class="text-[11px] font-mono text-blue-300 bg-blue-950/80 border border-blue-700/80 px-2 py-0.5 rounded ml-1">BOB-04 ACTIVE</span>
                  </div>

                  <!-- Exit / Dismiss Button -->
                  <div class="flex items-center gap-2">
                    <button onclick="exitTacticalDeck()" class="px-3.5 py-1.5 rounded-xl bg-red-600/90 hover:bg-red-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-red-950/50 flex items-center gap-1.5 cursor-pointer">
                      <span>✕</span>
                      <span>Exit Panel</span>
                    </button>
                  </div>
                </div>

                <!-- 2-COLUMN RAINY WEATHER FORECAST LAYOUT (USER REFERENCE IMAGE) -->
                <div class="grid grid-cols-1 lg:grid-cols-12 min-h-[440px]">
                  
                  <!-- LEFT FROSTED GLASS SIDEBAR (4 COLS) -->
                  <div class="lg:col-span-4 p-6 sm:p-8 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-white/10 bg-black/35 backdrop-blur-md">
                    
                    <!-- Search / Location Box with Cloud Icon -->
                    <div class="flex items-center justify-between px-3.5 py-2.5 rounded-2xl bg-white/10 border border-white/15 text-xs text-slate-200 font-mono shadow-inner">
                      <div class="flex items-center gap-2 truncate">
                        <span>🌧️</span>
                        <span class="text-slate-100 font-medium truncate">Gopalpur, Odisha</span>
                      </div>
                      <span class="text-slate-400 text-xs shrink-0">🔍</span>
                    </div>

                    <!-- Huge Temperature Readout -->
                    <div class="my-6">
                      <div class="text-6xl sm:text-7xl font-extralight tracking-tighter text-white font-sans">
                        30.5°
                      </div>
                      <div class="text-xs text-slate-300 font-mono mt-1">
                        Feels like: <strong class="text-white font-semibold">35.5°</strong>
                      </div>
                    </div>

                    <!-- Atmospheric Percentages (Exact from User Screenshot) -->
                    <div class="space-y-3 pt-5 border-t border-white/10 font-sans">
                      <div class="flex items-baseline gap-3">
                        <span class="text-2xl sm:text-3xl font-bold text-white font-mono">98%</span>
                        <span class="text-xs text-slate-300">of clouds</span>
                      </div>
                      <div class="flex items-baseline gap-3">
                        <span class="text-2xl sm:text-3xl font-bold text-white font-mono">88%</span>
                        <span class="text-xs text-slate-300">of humidity</span>
                      </div>
                      <div class="flex items-baseline gap-3">
                        <span class="text-2xl sm:text-3xl font-bold text-emerald-400 font-mono">948 mb</span>
                        <span class="text-xs text-slate-300">central pressure</span>
                      </div>
                    </div>

                  </div>

                  <!-- RIGHT WEATHER FORECAST CONTENT & 5-HOUR TIMELINE (8 COLS) -->
                  <div class="lg:col-span-8 p-6 sm:p-8 flex flex-col justify-between backdrop-blur-sm bg-black/20">
                    
                    <!-- Weather Forecast Header & Description -->
                    <div class="space-y-2.5">
                      <div class="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
                        Weather Forecast • Tropical Cyclone Warning
                      </div>
                      
                      <h2 class="text-3xl sm:text-4xl font-extrabold text-white font-heading tracking-tight leading-tight">
                        Torrential rain & gale nearby
                      </h2>

                      <div class="flex items-center gap-2 text-xs text-slate-300 font-mono pt-0.5">
                        <span>📍</span>
                        <span>Gopalpur, Odisha, 2026-09-08 15:15 IST</span>
                      </div>

                      <p class="text-xs sm:text-sm text-slate-200/95 leading-relaxed font-sans max-w-2xl pt-2">
                        SSE wind 155 kilometres per hour. Pressure is 948 mb. Chance of torrential rain is 98%. Chance of storm surge is 92%. Maximum sustained wind gusts up to 180 km/h. Minimum temperature is 22.6°. Severe Cyclonic Storm BOB-04 tracking northwest toward imminent landfall.
                      </p>
                    </div>

                    <!-- 5-Hour Forecast Station Columns (Exact layout from screenshot) -->
                    <div class="pt-8 sm:pt-10 space-y-3">
                      <div class="grid grid-cols-5 gap-2 text-center">
                        
                        <div class="space-y-1">
                          <div class="text-[11px] font-mono text-slate-400">15:00</div>
                          <div class="text-xl sm:text-2xl font-semibold text-white font-sans">28.8°</div>
                          <div class="text-[10px] font-mono text-slate-300">Wind: 155kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-[11px] font-mono text-slate-400">16:00</div>
                          <div class="text-xl sm:text-2xl font-semibold text-white font-sans">27.3°</div>
                          <div class="text-[10px] font-mono text-slate-300">Wind: 162kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-[11px] font-mono text-slate-400">17:00</div>
                          <div class="text-xl sm:text-2xl font-semibold text-white font-sans">23.5°</div>
                          <div class="text-[10px] font-mono text-slate-300">Wind: 175kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-[11px] font-mono text-slate-400">18:00</div>
                          <div class="text-xl sm:text-2xl font-semibold text-white font-sans">22.8°</div>
                          <div class="text-[10px] font-mono text-slate-300">Wind: 180kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-[11px] font-mono text-slate-400">19:00</div>
                          <div class="text-xl sm:text-2xl font-semibold text-white font-sans">22.6°</div>
                          <div class="text-[10px] font-mono text-slate-300">Wind: 165kph</div>
                        </div>

                      </div>

                      <!-- Smooth Curved Trendline SVG (Exact from reference image) -->
                      <div class="w-full h-8 pt-1">
                        <svg class="w-full h-full overflow-visible" viewBox="0 0 500 40" preserveAspectRatio="none">
                          <defs>
                            <linearGradient id="trendGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stop-color="#f97316"/>
                              <stop offset="45%" stop-color="#eab308"/>
                              <stop offset="100%" stop-color="#84cc16"/>
                            </linearGradient>
                          </defs>
                          <path d="M 50,8 C 150,12 200,32 300,34 C 380,36 420,36 450,36" fill="none" stroke="url(#trendGradient)" stroke-width="2.5" stroke-linecap="round"/>
                          <circle cx="50" cy="8" r="3.5" fill="#f97316"/>
                          <circle cx="150" cy="14" r="3" fill="#fb923c"/>
                          <circle cx="250" cy="30" r="3" fill="#eab308"/>
                          <circle cx="350" cy="35" r="3" fill="#a3e635"/>
                          <circle cx="450" cy="36" r="3" fill="#84cc16"/>
                        </svg>
                      </div>
                    </div>

                  </div>
                </div>

                <!-- BOTTOM METRICS & GEOGRAPHIC PRESETS STRIP -->
                <div class="flex flex-wrap items-center justify-between px-6 py-3 border-t border-white/10 bg-black/50 backdrop-blur-md text-xs font-mono">
                  <div class="flex items-center gap-3 text-slate-300">
                    <span class="text-emerald-400 font-bold">● INSAT-3DR TIR-1 + EOS-06 SCATTEROMETER FUSED</span>
                    <span class="text-slate-600 hidden sm:inline">•</span>
                    <span class="text-slate-300 hidden sm:inline">Chakravyooh Offline Resilient Mesh: 142 Nodes Armed</span>
                  </div>

                  <!-- Quick Focus Controls -->
                  <div class="flex items-center gap-2 pt-2 sm:pt-0">
                    <button onclick="selectPrefaceTarget('cyclone'); const inst = activeGlobeInstances['prefaceInteractiveGlobe']; if (inst) inst.setTargetRotation(0.32, Math.PI * 0.965, 1.32);" class="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-slate-200 text-[11px] transition-colors flex items-center gap-1 cursor-pointer">
                      <span>🌀</span>
                      <span>Storm Eye</span>
                    </button>
                    <button onclick="selectPrefaceTarget('gopalpur'); const inst = activeGlobeInstances['prefaceInteractiveGlobe']; if (inst) inst.setTargetRotation(0.35, Math.PI * 0.96, 1.38);" class="px-2.5 py-1 rounded-lg bg-red-950/80 hover:bg-red-900 text-red-200 border border-red-700/60 text-[11px] transition-colors flex items-center gap-1 cursor-pointer">
                      <span>📍</span>
                      <span>Gopalpur</span>
                    </button>
                    <button onclick="selectPrefaceTarget('india'); const inst = activeGlobeInstances['prefaceInteractiveGlobe']; if (inst) inst.setTargetRotation(0.35, Math.PI * 0.94, 1.6);" class="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-slate-200 text-[11px] transition-colors flex items-center gap-1 cursor-pointer">
                      <span>🇮🇳</span>
                      <span>India</span>
                    </button>
                    <button onclick="toggleGlobeAutoRotate()" class="px-2 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-slate-200 text-[11px] transition-colors cursor-pointer" title="Toggle Auto-Spin">
                      ▶️
                    </button>
                  </div>
                </div>

              </div>

            </div>
          </section>"""

if re.search(old_overlay_pattern, code):
    code = re.sub(old_overlay_pattern, new_overlay, code)
    with open('update_portal.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Successfully replaced tacticalHudOverlay with user reference image background and layout!")
else:
    print("Pattern not found!")
