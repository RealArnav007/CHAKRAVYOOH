import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

pattern = r'<div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-4 sm:p-8 select-none font-sans overflow-y-auto">[\s\S]*?<\/div>\s*<\/section>'

replacement = """<div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-3 sm:p-6 select-none font-sans overflow-y-auto">
              
              <!-- MAIN CONTROL PANEL (PERFECT MATCH TO USER REFERENCE IMAGE) -->
              <div class="relative w-full max-w-4xl rounded-[28px] overflow-hidden shadow-2xl border border-white/15 text-white pointer-events-auto my-auto backdrop-blur-md bg-cover bg-center transition-all duration-500" style="background-image: url('/static/rainy_storm_bg.jpg'); box-shadow: 0 30px 70px -15px rgba(0, 0, 0, 0.9), 0 0 0 1px rgba(255, 255, 255, 0.08);">
                
                <!-- Elegant Dismiss Button -->
                <button onclick="exitTacticalDeck()" class="absolute top-4 right-4 z-20 w-8 h-8 rounded-full bg-black/50 hover:bg-black/80 border border-white/20 text-white flex items-center justify-center text-xs font-bold transition-all shadow-lg cursor-pointer" title="Exit Panel">
                  ✕
                </button>

                <!-- 2-COLUMN USER REFERENCE DESIGN -->
                <div class="grid grid-cols-1 lg:grid-cols-12 min-h-[420px]">
                  
                  <!-- LEFT FROSTED COLUMN (4 COLS - ~30% WIDTH) -->
                  <div class="lg:col-span-4 p-6 sm:p-7 flex flex-col justify-between bg-[#111927]/60 backdrop-blur-xl border-b lg:border-b-0 lg:border-r border-white/10">
                    
                    <!-- Search Input with Cloud Icon -->
                    <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white/10 border border-white/10 text-xs text-slate-200 font-sans shadow-inner">
                      <div class="flex items-center gap-2 truncate">
                        <span class="text-sm">☁️</span>
                        <span class="text-slate-200 font-normal truncate">Gopalpur, India</span>
                      </div>
                      <span class="text-slate-400 text-xs shrink-0">🔍</span>
                    </div>

                    <!-- Large Temperature Readout (Exact User Font Styling) -->
                    <div class="my-5 sm:my-6">
                      <div class="text-6xl sm:text-7xl font-normal tracking-tight text-white font-sans leading-none">
                        30.5°
                      </div>
                      <div class="text-xs text-slate-300 font-sans mt-2 font-normal">
                        Feels like: <span class="text-white font-medium">35.5°</span>
                      </div>
                    </div>

                    <!-- Atmospheric Indicators (Exact User Alignment) -->
                    <div class="space-y-3.5 pt-4 border-t border-white/10 font-sans">
                      <div class="flex items-baseline justify-between">
                        <span class="text-2xl sm:text-3xl font-semibold text-white font-sans">79%</span>
                        <span class="text-xs text-slate-300 font-sans">of clouds</span>
                      </div>
                      <div class="flex items-baseline justify-between">
                        <span class="text-2xl sm:text-3xl font-semibold text-white font-sans">72%</span>
                        <span class="text-xs text-slate-300 font-sans">of humidity</span>
                      </div>
                      <div class="flex items-baseline justify-between">
                        <span class="text-xl sm:text-2xl font-semibold text-emerald-400 font-sans">948 mb</span>
                        <span class="text-xs text-slate-300 font-sans">of pressure</span>
                      </div>
                    </div>

                  </div>

                  <!-- RIGHT RAINY WINDOW CONTENT (8 COLS - ~70% WIDTH) -->
                  <div class="lg:col-span-8 p-6 sm:p-8 flex flex-col justify-between bg-black/20 backdrop-blur-[1px]">
                    
                    <!-- Forecast Header & Description (Exact Reference Typography) -->
                    <div class="space-y-2">
                      <div class="text-xs font-semibold text-slate-300 font-sans tracking-wide">
                        Weather Forecast
                      </div>
                      
                      <h2 class="text-3xl sm:text-4xl font-bold text-white tracking-tight font-sans leading-tight">
                        Patchy rain nearby
                      </h2>

                      <div class="flex items-center gap-1.5 text-xs text-slate-300 font-sans">
                        <span>📍</span>
                        <span>Mawsynram / Gopalpur, India, 2026-09-08 15:15 IST</span>
                      </div>

                      <p class="text-xs sm:text-sm text-slate-200/90 leading-relaxed font-sans max-w-xl pt-2 font-normal">
                        SSE wind 155 kilometres per hour. Pressure is 948mb. Chance of rain is 98%. Chance of snow is 0%. Maximum temperature is 32°, minimum temperature is 21.5°. Category 3 Severe Cyclonic Storm BOB-04 tracking northwest toward coastal landfall.
                      </p>
                    </div>

                    <!-- 5-Hour Milestone Timeline with Curved Trendline (Exact Reference Image) -->
                    <div class="pt-6 sm:pt-8 space-y-2">
                      <div class="grid grid-cols-5 gap-2 text-center font-sans">
                        
                        <div class="space-y-1">
                          <div class="text-xs text-slate-400 font-medium">15:00</div>
                          <div class="text-2xl sm:text-3xl font-medium text-white">28.8°</div>
                          <div class="text-[10px] text-slate-300">Wind speed: 9.9kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-xs text-slate-400 font-medium">16:00</div>
                          <div class="text-2xl sm:text-3xl font-medium text-white">27.3°</div>
                          <div class="text-[10px] text-slate-300">Wind speed: 11.2kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-xs text-slate-400 font-medium">17:00</div>
                          <div class="text-2xl sm:text-3xl font-medium text-white">23.5°</div>
                          <div class="text-[10px] text-slate-300">Wind speed: 7.5kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-xs text-slate-400 font-medium">18:00</div>
                          <div class="text-2xl sm:text-3xl font-medium text-white">22.8°</div>
                          <div class="text-[10px] text-slate-300">Wind speed: 7.1kph</div>
                        </div>

                        <div class="space-y-1">
                          <div class="text-xs text-slate-400 font-medium">19:00</div>
                          <div class="text-2xl sm:text-3xl font-medium text-white">22.6°</div>
                          <div class="text-[10px] text-slate-300">Wind speed: 7.4kph</div>
                        </div>

                      </div>

                      <!-- Smooth Colored Curve Trendline (Orange to Green - Exact Match) -->
                      <div class="w-full h-9 pt-1 px-4">
                        <svg class="w-full h-full overflow-visible" viewBox="0 0 460 36" preserveAspectRatio="none">
                          <defs>
                            <linearGradient id="userCurveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stop-color="#ea580c"/>
                              <stop offset="40%" stop-color="#f59e0b"/>
                              <stop offset="70%" stop-color="#a3e635"/>
                              <stop offset="100%" stop-color="#84cc16"/>
                            </linearGradient>
                          </defs>
                          <!-- Exact Bezier trajectory from 15:00 to 19:00 -->
                          <path d="M 20,4 C 95,8 150,22 230,28 C 300,32 370,33 440,33" fill="none" stroke="url(#userCurveGrad)" stroke-width="2.5" stroke-linecap="round"/>
                          <circle cx="20" cy="4" r="3.5" fill="#ea580c"/>
                          <circle cx="120" cy="12" r="3" fill="#f97316"/>
                          <circle cx="230" cy="28" r="3" fill="#eab308"/>
                          <circle cx="335" cy="32" r="3" fill="#a3e635"/>
                          <circle cx="440" cy="33" r="3" fill="#84cc16"/>
                        </svg>
                      </div>
                    </div>

                  </div>
                </div>

              </div>

            </div>
          </section>"""

if re.search(pattern, code):
    code = re.sub(pattern, replacement, code)
    with open('update_portal.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Successfully applied exact user reference design to main control panel!")
else:
    print("Pattern not found!")
