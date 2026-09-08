import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Define the clean, uncluttered, spacious renderScreen2AI
new_render_screen2 = """    function renderScreen2AI() {
      const ms = state.multiSource;

      return `
        <div class="space-y-6 max-w-7xl mx-auto select-none font-sans">
          
          <!-- 1. EXECUTIVE SATELLITE ARCHITECTURE & FUSION HEADER -->
          <div class="mission-card p-6 sm:p-7 space-y-4">
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div class="space-y-1.5">
                <div class="flex items-center gap-2">
                  <span class="px-2.5 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-700/60 text-xs font-mono font-bold uppercase tracking-wider">
                    ISRO & IMD SATELLITE ARCHITECTURE
                  </span>
                  <span class="px-2.5 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 text-xs font-mono font-bold uppercase">
                    AI FUSION ENGINE
                  </span>
                </div>
                <h2 class="text-2xl sm:text-3xl font-black font-heading tracking-tight text-white">
                  Indian Geostationary & Polar Satellite Data Fusion
                </h2>
                <p class="text-xs sm:text-sm text-slate-300 max-w-4xl leading-relaxed">
                  Real-time neural fusion of INSAT-3DR geostationary multispectral thermal soundings, EOS-06 scatterometer ocean surface winds, and INCOIS moored deep-sea buoy arrays for automated cyclonic vortex identification, classification, and landfall trajectory regression.
                </p>
              </div>

              <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
                <div class="px-3.5 py-2 rounded-xl bg-emerald-950/60 text-emerald-300 border border-emerald-700/60 text-xs font-mono font-medium flex items-center gap-2 shadow-sm">
                  <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>4 SATELLITE STREAMS SYNCHRONIZED</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 2. AI INTELLIGENCE TRI-STAGE OUTPUTS (CLEAN, PROMINENT, SPACIOUS) -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-mono font-bold text-cyan-300 uppercase tracking-widest flex items-center gap-2">
                <span>⚡</span>
                <span>AI FUSION INTELLIGENCE DELIVERABLES</span>
              </h3>
              <span class="text-[11px] font-mono text-emerald-400 font-semibold">OVERALL AI CONFIDENCE: 94.8%</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
              
              <!-- Deliverable 1: Identification -->
              <div class="mission-card p-5 space-y-3.5 border-t-2 border-t-cyan-400 flex flex-col justify-between">
                <div class="space-y-2.5">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-mono font-bold text-cyan-300 bg-cyan-950/80 px-2.5 py-1 rounded border border-cyan-700/60 flex items-center gap-1.5">
                      <span>🎯</span>
                      <span>1 • IDENTIFICATION</span>
                    </span>
                    <span class="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                      98.6% Conf
                    </span>
                  </div>

                  <div>
                    <h4 class="text-base font-bold text-white font-heading">Vortex Center Localized</h4>
                    <p class="text-xs text-slate-300 mt-1 leading-relaxed">
                      Deep convolutional network isolated vortex center at <strong class="text-cyan-300">16.82°N, 84.48°E</strong> in the Bay of Bengal with closed isobaric circulation and clear eye thermal isolation.
                    </p>
                  </div>
                </div>

                <div class="mission-card-subtle p-3 space-y-1.5 text-xs font-mono">
                  <div class="flex justify-between text-slate-400">
                    <span>Focal Coordinates:</span>
                    <span class="text-white font-bold">16.82°N, 84.48°E</span>
                  </div>
                  <div class="flex justify-between text-slate-400">
                    <span>Eye Thermal Core:</span>
                    <span class="text-cyan-300 font-semibold">+6.8°C Anomaly</span>
                  </div>
                  <div class="flex justify-between text-slate-400">
                    <span>Extraction Method:</span>
                    <span class="text-slate-200">CNN-ViT Spatial Model</span>
                  </div>
                </div>
              </div>

              <!-- Deliverable 2: Classification -->
              <div class="mission-card p-5 space-y-3.5 border-t-2 border-t-blue-500 flex flex-col justify-between">
                <div class="space-y-2.5">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-mono font-bold text-blue-300 bg-blue-950/80 px-2.5 py-1 rounded border border-blue-700/60 flex items-center gap-1.5">
                      <span>🏷️</span>
                      <span>2 • CLASSIFICATION</span>
                    </span>
                    <span class="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                      94.2% Conf
                    </span>
                  </div>

                  <div>
                    <h4 class="text-base font-bold text-white font-heading">Mature Cyclone (Category 3)</h4>
                    <p class="text-xs text-slate-300 mt-1 leading-relaxed">
                      Classified as <strong class="text-blue-300">Very Severe Cyclonic Storm (VSCS)</strong>. Dvorak intensity computed at <strong class="text-white">T4.5</strong> based on infrared eye-to-cloud-top thermal gradient.
                    </p>
                  </div>
                </div>

                <div class="mission-card-subtle p-3 space-y-1.5 text-xs font-mono">
                  <div class="flex justify-between text-slate-400">
                    <span>Central Pressure:</span>
                    <span class="text-white font-bold">948 hPa</span>
                  </div>
                  <div class="flex justify-between text-slate-400">
                    <span>Sustained Wind:</span>
                    <span class="text-red-400 font-bold">155 km/h (Gale)</span>
                  </div>
                  <div class="flex justify-between text-slate-400">
                    <span>Classification Grade:</span>
                    <span class="text-blue-300 font-semibold">IMD / JTWC VSCS (Cat-3)</span>
                  </div>
                </div>
              </div>

              <!-- Deliverable 3: Prediction -->
              <div class="mission-card p-5 space-y-3.5 border-t-2 border-t-emerald-500 flex flex-col justify-between">
                <div class="space-y-2.5">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-mono font-bold text-emerald-300 bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-700/60 flex items-center gap-1.5">
                      <span>📈</span>
                      <span>3 • PREDICTION</span>
                    </span>
                    <span class="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                      91.8% Conf
                    </span>
                  </div>

                  <div>
                    <h4 class="text-base font-bold text-white font-heading">24-Hour Landfall Trajectory</h4>
                    <p class="text-xs text-slate-300 mt-1 leading-relaxed">
                      Physics-Informed Neural Network (PINN) projected trajectory: <strong class="text-emerald-300">315° NW at 18 km/h</strong>, placing landfall at Gopalpur coast at <strong class="text-white">T+22.5h</strong> with ±14 km margin.
                    </p>
                  </div>
                </div>

                <div class="mission-card-subtle p-3 space-y-1.5 text-xs font-mono">
                  <div class="flex justify-between text-slate-400">
                    <span>Landfall Target:</span>
                    <span class="text-white font-bold">Gopalpur, Odisha Coast</span>
                  </div>
                  <div class="flex justify-between text-slate-400">
                    <span>Estimated ETA:</span>
                    <span class="text-emerald-300 font-semibold">T+22.5 Hours</span>
                  </div>
                  <div class="flex justify-between text-slate-400">
                    <span>Ensemble Model:</span>
                    <span class="text-slate-200">PINN + WRF-NWP</span>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <!-- 3. FOUR CORE DATA STREAMS (SPACIOUS 2x2 GRID INSTEAD OF CRAMPED 4-COLUMN) -->
          <div class="space-y-3">
            <h3 class="text-xs font-mono font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <span>🛰️</span>
              <span>MULTI-SOURCE INGESTION STREAMS & OCEANIC SENSORS</span>
            </h3>

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

          <!-- 4. ISRO MOSDAC SCORPIO DIRECT RELAY CARD -->
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
    print("Replaced renderScreen2AI with clean, decluttered, spacious layout.")
else:
    print(f"ERROR: Could not locate bounds: idx_s2={idx_s2}, idx_s3={idx_s3}")
    exit(1)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py successfully.")
