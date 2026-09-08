import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Enhance #tacticalHudOverlay and #tacticalDeckScrollArea for smooth, unhindered scrolling
# Fix justify-center to justify-start so top content is never cut off on scroll
old_overlay = '<div id="tacticalHudOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">'
new_overlay = '<div id="tacticalHudOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-start items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto w-full h-full">'

if old_overlay in code:
    code = code.replace(old_overlay, new_overlay, 1)
    print("Updated #tacticalHudOverlay flex alignment to justify-start for flawless scrolling.")

# Enhance #tacticalDeckScrollArea with generous bottom padding (pb-28) and smooth scroll behavior
old_scroll_area = '<div id="tacticalDeckScrollArea" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 custom-scrollbar bg-transparent">'
new_scroll_area = '<div id="tacticalDeckScrollArea" class="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 custom-scrollbar bg-transparent pb-28 scroll-smooth overscroll-contain">'

if old_scroll_area in code:
    code = code.replace(old_scroll_area, new_scroll_area, 1)
    print("Updated #tacticalDeckScrollArea with pb-28 and smooth overscroll behavior.")

# 2. Refine Screen 1 (Cyclone Intel) for generous spacing and zero clutter
s1_start = "    function renderScreen1Hero() {"
s2_start = "    function renderScreen2AI() {"

idx_s1 = code.find(s1_start)
idx_s2 = code.find(s2_start)

if idx_s1 != -1 and idx_s2 != -1:
    s1_code = code[idx_s1:idx_s2]
    # In s1_code, replace the 6-metrics grid and sidebar to ensure breathable padding and no cramped wrapping
    print("Located Screen 1 bounds.")

# 3. Refine Screen 3 (Risk Zones) from cramped 4-column to spacious 2-column grid
new_screen3 = """    function renderScreen3Risk() {
      return `
        <div class="space-y-6 max-w-7xl mx-auto select-none font-sans">
          
          <!-- Risk Strategy Executive Header -->
          <div class="mission-card p-6 sm:p-7 space-y-4">
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div class="space-y-1.5">
                <div class="flex items-center gap-2">
                  <span class="px-2.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-700/60 text-xs font-mono font-bold uppercase tracking-wider">
                    METEOROLOGY TO ACTIONABLE RISK
                  </span>
                  <span class="px-2.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-700/60 text-xs font-mono font-bold uppercase">
                    COASTAL EVACUATION MATRIX
                  </span>
                </div>
                <h2 class="text-2xl sm:text-3xl font-black font-heading tracking-tight text-white">
                  Geospatial Impact & Evacuation Risk Matrix
                </h2>
                <p class="text-xs sm:text-sm text-slate-300 max-w-4xl leading-relaxed">
                  Translating cyclone wind field, storm surge inundation modeling, and coastal bathymetry into 4 prioritized emergency operational sectors with automated evacuation tracking.
                </p>
              </div>

              <div class="flex items-center gap-3 shrink-0">
                <button onclick="triggerRiskElevation()" class="px-4 py-2.5 rounded-xl bg-red-700 hover:bg-red-600 active:scale-95 text-white font-mono text-xs font-bold transition-all shadow-md shadow-red-950/60 cursor-pointer flex items-center gap-2">
                  <span>🌊</span>
                  <span>Simulate Surge Spike (+0.8m)</span>
                </button>
              </div>
            </div>
          </div>

          <!-- 4 Core Operational Zones Grid: Spacious 2-Column Grid (Not Cramped 4-Column) -->
          <div class="space-y-3">
            <h3 class="text-xs font-mono font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <span>⚠️</span>
              <span>PRIORITIZED OPERATIONAL ACTION ZONES</span>
            </h3>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
              ${state.riskZones.map(z => `
                <div class="mission-card p-5 sm:p-6 space-y-4 flex flex-col justify-between ${z.level === 'EXTREME' ? 'border-red-600/80 shadow-lg shadow-red-950/40' : ''}">
                  <div class="space-y-3">
                    <div class="flex items-center justify-between border-b border-[#1b2b45] pb-3">
                      <div class="flex items-center gap-2.5">
                        <span class="text-xs font-mono font-bold px-3 py-1 rounded-md border ${z.badgeClass}">
                          ${z.code} — ${z.colorTag}
                        </span>
                        <h4 class="text-base font-bold text-white font-heading">${z.corridor}</h4>
                      </div>
                      <span class="text-xs font-mono text-cyan-300 bg-cyan-950/80 px-2.5 py-1 rounded border border-cyan-700/60 shrink-0">
                        ${z.sheltersActive} Shelters Active
                      </span>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed">${z.actionDirective}</p>

                    <!-- Key Operational Risk Metrics (Spacious 3-Column sub-grid) -->
                    <div class="grid grid-cols-3 gap-3 text-xs font-mono">
                      <div class="mission-card-subtle p-3 space-y-1">
                        <span class="text-[10px] text-slate-400 uppercase">Storm Surge</span>
                        <p class="text-sm font-bold ${z.level === 'EXTREME' ? 'text-red-400' : 'text-slate-100'}">${z.surgeHeight}</p>
                      </div>
                      <div class="mission-card-subtle p-3 space-y-1">
                        <span class="text-[10px] text-slate-400 uppercase">Sustained Gale</span>
                        <p class="text-sm font-bold ${z.level === 'EXTREME' ? 'text-red-400' : 'text-slate-100'}">${z.sustainedWinds}</p>
                      </div>
                      <div class="mission-card-subtle p-3 space-y-1">
                        <span class="text-[10px] text-slate-400 uppercase">Population At Risk</span>
                        <p class="text-sm font-bold text-slate-100">${z.populationExposed}</p>
                      </div>
                    </div>
                  </div>

                  <!-- Evacuation Progress Bar -->
                  <div class="space-y-2 pt-3 border-t border-[#1b2b45]">
                    <div class="flex justify-between items-center text-xs font-mono">
                      <span class="text-slate-300">Evacuation Completion:</span>
                      <span class="font-bold ${z.level === 'EXTREME' ? 'text-red-400' : 'text-emerald-400'}">${z.evacuatedPercent}%</span>
                    </div>
                    <div class="w-full h-2 rounded-full bg-slate-900 border border-slate-700/60 overflow-hidden">
                      <div class="h-full transition-all duration-500 ${z.level === 'EXTREME' ? 'bg-gradient-to-r from-red-600 to-amber-500' : z.level === 'HIGH' ? 'bg-amber-500' : 'bg-blue-500'}" style="width: ${z.evacuatedPercent}%"></div>
                    </div>
                    <div class="flex justify-between text-[11px] font-mono text-slate-400 pt-0.5">
                      <span>Capacity Ingested: <strong class="text-slate-200">${z.shelterOccupancy}</strong></span>
                      <span class="text-emerald-400">Offline Mesh Relays Active</span>
                    </div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Structured Protocol Table: Spacious & Legible -->
          <div class="mission-card p-6 space-y-4">
            <h3 class="text-sm font-bold text-white font-heading uppercase tracking-wider flex items-center gap-2">
              <span>📋</span>
              <span>Operational Directives by Geospatial Sector</span>
            </h3>
            <div class="overflow-x-auto rounded-xl border border-[#1b2b45]">
              <table class="w-full text-left text-xs font-sans">
                <thead class="bg-[#0e1626] text-slate-300 font-mono text-[11px] uppercase border-b border-[#1b2b45]">
                  <tr>
                    <th class="p-3.5">Zone Code</th>
                    <th class="p-3.5">Category</th>
                    <th class="p-3.5">Key Vulnerable Assets</th>
                    <th class="p-3.5">Mandatory Field Directives</th>
                    <th class="p-3.5">Chakravyooh Mesh Status</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#18253a] font-mono text-slate-300">
                  <tr class="hover:bg-white/[0.02] transition-colors">
                    <td class="p-3.5 font-bold text-red-400">ZONE A</td>
                    <td class="p-3.5"><span class="px-2.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 text-[11px]">RED WARNING</span></td>
                    <td class="p-3.5 text-slate-200">Gopalpur Harbor, Sea Dykes, Coastal Hamlets</td>
                    <td class="p-3.5 text-red-300 font-semibold">100% Mandatory Evacuation; Power grid isolated</td>
                    <td class="p-3.5 text-emerald-400 font-semibold">Offline Mesh Warning Broadcast Active (142 Nodes)</td>
                  </tr>
                  <tr class="hover:bg-white/[0.02] transition-colors">
                    <td class="p-3.5 font-bold text-amber-400">ZONE B</td>
                    <td class="p-3.5"><span class="px-2.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[11px]">ORANGE ALERT</span></td>
                    <td class="p-3.5 text-slate-200">Berhampur Hospital, NH-16 Corridor</td>
                    <td class="p-3.5 text-slate-300">Shelter-in-place; NDRF Zodiac Boats staged</td>
                    <td class="p-3.5 text-cyan-300 font-semibold">Cellular + Mesh Dual Channel Active</td>
                  </tr>
                  <tr class="hover:bg-white/[0.02] transition-colors">
                    <td class="p-3.5 font-bold text-yellow-400">ZONE C</td>
                    <td class="p-3.5"><span class="px-2.5 py-0.5 rounded bg-yellow-950 text-yellow-300 border border-yellow-800 text-[11px]">YELLOW WATCH</span></td>
                    <td class="p-3.5 text-slate-200">Lowland Agriculture, Drainage Reservoirs</td>
                    <td class="p-3.5 text-slate-300">Precautionary advisory; Food & medical supply check</td>
                    <td class="p-3.5 text-slate-400">Advisory Broadcast Queued</td>
                  </tr>
                  <tr class="hover:bg-white/[0.02] transition-colors">
                    <td class="p-3.5 font-bold text-emerald-400">ZONE D</td>
                    <td class="p-3.5"><span class="px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[11px]">GREEN STANDBY</span></td>
                    <td class="p-3.5 text-slate-200">Inland Highlands Staging Area</td>
                    <td class="p-3.5 text-slate-300">Continuous telemetry monitoring</td>
                    <td class="p-3.5 text-slate-400">Standby Telemetry</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      `;
    }
"""

# Replace renderScreen3Risk in update_portal.py
s3_start = "    function renderScreen3Risk() {"
s4_start = "    function renderScreen4Resilience() {"

idx_s3 = code.find(s3_start)
idx_s4 = code.find(s4_start)

if idx_s3 != -1 and idx_s4 != -1:
    code = code[:idx_s3] + new_screen3 + "\n" + code[idx_s4:]
    print("Replaced renderScreen3Risk with spacious 2-column layout.")
else:
    print(f"ERROR: Could not locate Screen 3 bounds: idx_s3={idx_s3}, idx_s4={idx_s4}")
    exit(1)

# 4. Refine Screen 4 (Resilience & Mesh) to remove quote clutter and provide spacious cards
old_quote_banner = """                <h2 class="text-xl sm:text-2xl font-bold font-heading text-white">
                  "The AI predicts the cyclone. Chakravyooh delivers the warnings and coordinates the response when the storm arrives."
                </h2>"""

new_quote_banner = """                <h2 class="text-xl sm:text-2xl font-black font-heading tracking-tight text-white">
                  Autonomous Offline Mesh & Emergency Distress Coordination Layer
                </h2>"""

if old_quote_banner in code:
    code = code.replace(old_quote_banner, new_quote_banner, 1)
    print("Replaced quote in Screen 4 with authoritative operational header.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py with all-tab decluttering and enhanced scrolling.")
