import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Build the ultra-high priority AI Fusion Intelligence Deliverables Screen 2
new_render_screen2 = """    function renderScreen2AI() {
      const ms = state.multiSource;

      return `
        <div class="space-y-7 max-w-7xl mx-auto select-none font-sans pb-16">
          
          <!-- ========================================================================= -->
          <!-- ★ HIGHEST OPERATIONAL PRIORITY: AI FUSION INTELLIGENCE DELIVERABLES        -->
          <!-- ========================================================================= -->
          <div class="relative overflow-hidden rounded-[26px] border-2 border-cyan-400/60 shadow-[0_0_50px_rgba(14,165,233,0.35),0_30px_70px_-15px_rgba(0,0,0,0.9)] bg-gradient-to-br from-[#0c1e3d]/95 via-[#050f24]/95 to-[#091733]/95 p-6 sm:p-8 space-y-6">
            
            <!-- Ambient Cyber Grid Background Glow Accent -->
            <div class="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none"></div>
            <div class="absolute -bottom-24 -left-24 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none"></div>

            <!-- Priority Badge & Executive Header -->
            <div class="relative z-10 space-y-3">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-950/90 border border-cyan-400/80 shadow-[0_0_20px_rgba(6,182,212,0.4)] text-xs font-mono font-bold tracking-widest text-cyan-200 uppercase">
                  <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                  <span>🚨 HIGHEST OPERATIONAL PRIORITY • CORE INTELLIGENCE DELIVERABLES</span>
                </div>

                <div class="flex items-center gap-2">
                  <span class="px-3.5 py-1.5 rounded-xl bg-emerald-950/80 text-emerald-300 border border-emerald-500/80 text-xs font-mono font-bold flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>OVERALL AI CONFIDENCE: 94.8%</span>
                  </span>
                </div>
              </div>

              <div class="space-y-1.5">
                <h1 class="text-2xl sm:text-4xl font-black font-heading tracking-tight text-white flex flex-wrap items-center gap-3">
                  <span>AI FUSION INTELLIGENCE DELIVERABLES</span>
                </h1>
                <p class="text-xs sm:text-sm text-cyan-100/90 max-w-4xl leading-relaxed font-sans">
                  Automated multi-modal neural intelligence engine synthesizing geostationary multispectral thermal soundings, ocean scatterometer wind vectors, and in-situ buoy telemetry into authoritative cyclone identification, intensity classification, and landfall trajectory regression.
                </p>
              </div>

              <!-- Executive Live KPI Command Strip -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                <div class="p-3.5 rounded-xl bg-[#09152b]/90 border border-cyan-500/40 shadow-inner space-y-0.5">
                  <span class="text-[10px] font-mono text-cyan-300/80 uppercase font-semibold">1. VORTEX IDENTIFIED</span>
                  <p class="text-base font-bold font-mono text-white">16.82°N, 84.48°E</p>
                  <p class="text-[11px] font-mono text-emerald-400 font-semibold">Bay of Bengal Vortex</p>
                </div>
                <div class="p-3.5 rounded-xl bg-[#09152b]/90 border border-cyan-500/40 shadow-inner space-y-0.5">
                  <span class="text-[10px] font-mono text-cyan-300/80 uppercase font-semibold">2. INTENSITY GRADE</span>
                  <p class="text-base font-bold font-mono text-white">VSCS (Cat-3)</p>
                  <p class="text-[11px] font-mono text-red-400 font-semibold">155 km/h • 948 hPa</p>
                </div>
                <div class="p-3.5 rounded-xl bg-[#09152b]/90 border border-cyan-500/40 shadow-inner space-y-0.5">
                  <span class="text-[10px] font-mono text-cyan-300/80 uppercase font-semibold">3. LANDFALL PREDICTION</span>
                  <p class="text-base font-bold font-mono text-white">Gopalpur, Odisha</p>
                  <p class="text-[11px] font-mono text-amber-300 font-semibold">T+22.5h Window (±14 km)</p>
                </div>
                <div class="p-3.5 rounded-xl bg-[#09152b]/90 border border-cyan-500/40 shadow-inner space-y-0.5">
                  <span class="text-[10px] font-mono text-cyan-300/80 uppercase font-semibold">4. ENSEMBLE CONSENSUS</span>
                  <p class="text-base font-bold font-mono text-emerald-300">94.8% Validated</p>
                  <p class="text-[11px] font-mono text-slate-300">PINN • CNN-ViT • ADT</p>
                </div>
              </div>
            </div>

            <!-- The 3 Core Deliverable Command Cards (Massive Visual Presence) -->
            <div class="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-5 pt-1">
              
              <!-- Deliverable 1: Identification -->
              <div class="mission-card p-5 sm:p-6 space-y-4 border-2 border-cyan-400/60 shadow-[0_10px_30px_-5px_rgba(6,182,212,0.3)] bg-[#071328]/95 flex flex-col justify-between">
                <div class="space-y-3">
                  <div class="flex items-center justify-between border-b border-cyan-500/30 pb-2.5">
                    <span class="text-xs font-mono font-bold text-cyan-200 bg-cyan-950 px-3 py-1 rounded-md border border-cyan-500/60 flex items-center gap-1.5">
                      <span>🎯</span>
                      <span>DELIVERABLE 1 • IDENTIFIED</span>
                    </span>
                    <span class="text-xs font-mono font-bold text-emerald-300 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-600">
                      98.6% Conf
                    </span>
                  </div>

                  <div>
                    <h3 class="text-lg font-bold text-white font-heading">Vortex Center Localized</h3>
                    <p class="text-xs text-slate-300 mt-1 leading-relaxed">
                      Deep convolutional network isolated vortex eye center at <strong class="text-cyan-300">16.82°N, 84.48°E</strong> with closed isobaric circulation and clear warm core isolation.
                    </p>
                  </div>
                </div>

                <div class="space-y-2 text-xs font-mono pt-2">
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Eye Coordinates:</span>
                    <span class="text-cyan-300 font-bold">16.82°N, 84.48°E</span>
                  </div>
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Eye Thermal Core:</span>
                    <span class="text-white font-semibold">+6.8°C Inversion</span>
                  </div>
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Neural Model:</span>
                    <span class="text-slate-200">CNN-ViT Spatial Extractor</span>
                  </div>
                </div>
              </div>

              <!-- Deliverable 2: Classification -->
              <div class="mission-card p-5 sm:p-6 space-y-4 border-2 border-blue-500/60 shadow-[0_10px_30px_-5px_rgba(37,99,235,0.3)] bg-[#071328]/95 flex flex-col justify-between">
                <div class="space-y-3">
                  <div class="flex items-center justify-between border-b border-blue-500/30 pb-2.5">
                    <span class="text-xs font-mono font-bold text-blue-200 bg-blue-950 px-3 py-1 rounded-md border border-blue-500/60 flex items-center gap-1.5">
                      <span>🏷️</span>
                      <span>DELIVERABLE 2 • CLASSIFIED</span>
                    </span>
                    <span class="text-xs font-mono font-bold text-emerald-300 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-600">
                      94.2% Conf
                    </span>
                  </div>

                  <div>
                    <h3 class="text-lg font-bold text-white font-heading">Mature Cyclone (Category 3)</h3>
                    <p class="text-xs text-slate-300 mt-1 leading-relaxed">
                      Classified as <strong class="text-blue-300">Very Severe Cyclonic Storm (VSCS)</strong>. Dvorak intensity computed at <strong class="text-white">T4.5</strong> based on infrared eye-to-cloud-top thermal gradient.
                    </p>
                  </div>
                </div>

                <div class="space-y-2 text-xs font-mono pt-2">
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Central Pressure:</span>
                    <span class="text-white font-bold">948 hPa</span>
                  </div>
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Max Sustained Gale:</span>
                    <span class="text-red-400 font-bold">155 km/h</span>
                  </div>
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Intensity Technique:</span>
                    <span class="text-blue-300 font-semibold">IMD Automated Dvorak (T4.5)</span>
                  </div>
                </div>
              </div>

              <!-- Deliverable 3: Prediction -->
              <div class="mission-card p-5 sm:p-6 space-y-4 border-2 border-emerald-500/60 shadow-[0_10px_30px_-5px_rgba(16,185,129,0.3)] bg-[#071328]/95 flex flex-col justify-between">
                <div class="space-y-3">
                  <div class="flex items-center justify-between border-b border-emerald-500/30 pb-2.5">
                    <span class="text-xs font-mono font-bold text-emerald-200 bg-emerald-950 px-3 py-1 rounded-md border border-emerald-500/60 flex items-center gap-1.5">
                      <span>📈</span>
                      <span>DELIVERABLE 3 • PREDICTED</span>
                    </span>
                    <span class="text-xs font-mono font-bold text-emerald-300 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-600">
                      91.8% Conf
                    </span>
                  </div>

                  <div>
                    <h3 class="text-lg font-bold text-white font-heading">24-Hour Landfall Trajectory</h3>
                    <p class="text-xs text-slate-300 mt-1 leading-relaxed">
                      Physics-Informed Neural Network (PINN) projected trajectory: <strong class="text-emerald-300">315° NW at 18 km/h</strong>, placing landfall at Gopalpur coast at <strong class="text-white">T+22.5h</strong> with ±14 km margin.
                    </p>
                  </div>
                </div>

                <div class="space-y-2 text-xs font-mono pt-2">
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Landfall Target:</span>
                    <span class="text-white font-bold">Gopalpur, Odisha Coast</span>
                  </div>
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Estimated ETA:</span>
                    <span class="text-emerald-300 font-bold">T+22.5 Hours</span>
                  </div>
                  <div class="mission-card-subtle p-2.5 flex justify-between items-center">
                    <span class="text-slate-400">Ensemble Regressor:</span>
                    <span class="text-slate-200">PINN + WRF-NWP</span>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <!-- ========================================================================= -->
          <!-- SUPPORTING FOUNDATION: MULTI-SOURCE SATELLITE & OCEANIC DATA INPUTS       -->
          <!-- ========================================================================= -->
          <div class="space-y-3 pt-2">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <span>🛰️</span>
                <span>MULTI-SOURCE SATELLITE & OCEANIC TELEMETRY FOUNDATION</span>
              </h3>
              <span class="text-[11px] font-mono text-slate-400">TELEMETRY INPUTS FOR AI PIPELINE</span>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
              
              <!-- Stream 1: ISRO INSAT-3DR -->
              <div class="mission-card p-5 sm:p-6 space-y-4">
                <div class="flex items-center justify-between border-b border-[#1b2b45] pb-3">
                  <div class="flex items-center gap-2.5">
                    <span class="text-xs font-mono font-bold text-blue-300 bg-blue-950 px-2.5 py-1 rounded border border-blue-800">
                      ISRO INSAT
                    </span>
                    <h4 class="text-base font-bold text-white font-heading">${ms.satA.name}</h4>
                  </div>
                  <span class="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>${ms.satA.sensorStatus}</span>
                  </span>
                </div>

                <p class="text-xs text-slate-300 leading-relaxed">${ms.satA.type}</p>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs font-mono">
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Scan Cadence</span>
                    <p class="text-sm font-bold text-blue-300">${ms.satA.refresh}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Cloud Top Temperature</span>
                    <p class="text-sm font-bold text-slate-100">${ms.satA.cloudTopTemp}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Eye Thermal Anomaly</span>
                    <p class="text-sm font-bold text-red-400">${ms.satA.eyeAnomaly}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Spectral Channels</span>
                    <p class="text-xs font-semibold text-slate-200 truncate" title="${ms.satA.channels}">TIR-1, TIR-2, WV, VIS</p>
                  </div>
                </div>
              </div>

              <!-- Stream 2: ISRO EOS-06 Scatterometer -->
              <div class="mission-card p-5 sm:p-6 space-y-4">
                <div class="flex items-center justify-between border-b border-[#1b2b45] pb-3">
                  <div class="flex items-center gap-2.5">
                    <span class="text-xs font-mono font-bold text-blue-300 bg-blue-950 px-2.5 py-1 rounded border border-blue-800">
                      ISRO EOS-06
                    </span>
                    <h4 class="text-base font-bold text-white font-heading">${ms.satB.name}</h4>
                  </div>
                  <span class="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>${ms.satB.sensorStatus}</span>
                  </span>
                </div>

                <p class="text-xs text-slate-300 leading-relaxed">${ms.satB.type}</p>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs font-mono">
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Max Surface Wind</span>
                    <p class="text-sm font-bold text-red-400">${ms.satB.maxSurfaceWind}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Resolution</span>
                    <p class="text-sm font-bold text-slate-100">12.5 km Cell</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Orbital Overpass</span>
                    <p class="text-sm font-bold text-blue-300">${ms.satB.refresh}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Radius of Max Winds</span>
                    <p class="text-sm font-bold text-slate-200">${ms.satB.rmw || '28 km'}</p>
                  </div>
                </div>
              </div>

              <!-- Stream 3: INCOIS Ocean Buoys -->
              <div class="mission-card p-5 sm:p-6 space-y-4">
                <div class="flex items-center justify-between border-b border-[#1b2b45] pb-3">
                  <div class="flex items-center gap-2.5">
                    <span class="text-xs font-mono font-bold text-amber-300 bg-amber-950 px-2.5 py-1 rounded border border-amber-800">
                      INCOIS BUOYS
                    </span>
                    <h4 class="text-base font-bold text-white font-heading">${ms.atmosphere.name}</h4>
                  </div>
                  <span class="text-xs font-mono text-amber-400 font-semibold">● FAVORABLE</span>
                </div>

                <p class="text-xs text-slate-300 leading-relaxed">Deep-Sea Moored Ocean Array providing real-time in-situ hydrothermal boundary validation.</p>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs font-mono">
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Sea Surface Temp (SST)</span>
                    <p class="text-sm font-bold text-red-400">${ms.atmosphere.sst}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Vertical Wind Shear</span>
                    <p class="text-sm font-bold text-emerald-400">${ms.atmosphere.windShear}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Low-Level Vorticity</span>
                    <p class="text-sm font-bold text-slate-100">${ms.atmosphere.vorticity}</p>
                  </div>
                  <div class="mission-card-subtle p-2.5 space-y-0.5">
                    <span class="text-[10px] text-slate-400 uppercase">Mid-Level Humidity</span>
                    <p class="text-sm font-bold text-blue-300">${ms.atmosphere.humidity}</p>
                  </div>
                </div>
              </div>

              <!-- Stream 4: IMD Climatological Archive -->
              <div class="mission-card p-5 sm:p-6 space-y-4">
                <div class="flex items-center justify-between border-b border-[#1b2b45] pb-3">
                  <div class="flex items-center gap-2.5">
                    <span class="text-xs font-mono font-bold text-slate-300 bg-slate-800 px-2.5 py-1 rounded border border-slate-700">
                      IMD ARCHIVE
                    </span>
                    <h4 class="text-base font-bold text-white font-heading">Bay of Bengal Climatology</h4>
                  </div>
                  <span class="text-xs font-mono text-slate-400">4,200+ Tracks</span>
                </div>

                <p class="text-xs text-slate-300 leading-relaxed">Top historical analogue matches with correlated landfall corridor and central pressure drop.</p>

                <div class="space-y-2 text-xs font-mono">
                  ${ms.historical.matches.map(m => `
                    <div class="mission-card-subtle p-2.5 flex items-center justify-between gap-2">
                      <div class="space-y-0.5 truncate">
                        <p class="font-bold text-slate-100 truncate">${m.name}</p>
                        <p class="text-[10px] text-slate-400">${m.analogScore || 'Correlated Track'}</p>
                      </div>
                      <span class="px-2 py-1 rounded bg-blue-950 text-blue-300 font-bold border border-blue-800 text-xs shrink-0">
                        ${m.correlation}
                      </span>
                    </div>
                  `).join('')}
                </div>
              </div>

            </div>
          </div>

          <!-- ========================================================================= -->
          <!-- OFFICIAL ISRO MOSDAC SCORPIO DIRECT RELAY CARD                            -->
          <!-- ========================================================================= -->
          <div class="mission-card p-5 sm:p-6 space-y-3 border-l-4 border-l-blue-500">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div class="space-y-1">
                <span class="text-xs font-mono font-bold text-blue-400 bg-blue-950/80 px-2.5 py-0.5 rounded border border-blue-800">
                  OFFICIAL SPACE APPLICATIONS CENTRE (ISRO) RELAY
                </span>
                <h3 class="text-lg font-bold text-white font-heading">
                  ISRO MOSDAC SCORPIO — Cyclone Observation & Prediction Engine
                </h3>
                <p class="text-xs text-slate-300">
                  Continuous geostationary multispectral imagery from INSAT-3DR & 3DS coupled with Ku-band scatterometer wind fields from EOS-06 SCAT-3.
                </p>
              </div>

              <div class="flex items-center gap-2.5 shrink-0">
                <a href="https://mosdac.gov.in/scorpio/" target="_blank" rel="noopener noreferrer" class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-blue-950/50">
                  <span>Launch SCORPIO External</span>
                  <span>↗</span>
                </a>
                <button onclick="setState({ activeScreen: 'screen1_hero', scorpioViewMode: 'live_feed' })" class="px-4 py-2 rounded-xl bg-[#16243b] hover:bg-[#1f3354] text-slate-200 font-mono text-xs border border-[#233554] transition-colors">
                  View Live Feed on Hero →
                </button>
              </div>
            </div>
          </div>

        </div>
      `;
    }
"""

# Replace renderScreen2AI in update_portal.py
s2_start = "    function renderScreen2AI() {"
s3_start = "    function renderScreen3Risk() {"

idx_s2 = code.find(s2_start)
idx_s3 = code.find(s3_start)

if idx_s2 != -1 and idx_s3 != -1:
    code = code[:idx_s2] + new_render_screen2 + "\n" + code[idx_s3:]
    print("Replaced renderScreen2AI with ultra-high priority flagship presentation.")
else:
    print(f"ERROR: Could not find bounds: idx_s2={idx_s2}, idx_s3={idx_s3}")
    exit(1)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py successfully.")
