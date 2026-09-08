#!/usr/bin/env python3
"""
apply_prd_tactical_deck.py
Integrates the complete Master PRD Command Center (Screens 1, 2, 3, 4 + Modals + Tabs)
into the launched Tactical Command Deck with the rainy window storm background.
"""

with open('update_portal.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update .mission-card and .mission-card-subtle with frosted glass styling
old_card_css = """    /* Professional Mission Control Matte Cards */
    .mission-card {
      background: #111a2d;
      border: 1px solid #1e2c45;
      border-radius: 14px;
      box-shadow: 0 4px 16px -2px rgba(0, 0, 0, 0.4);
    }

    .mission-card-subtle {
      background: #0d1526;
      border: 1px solid #1a273e;
      border-radius: 12px;
    }"""

new_card_css = """    /* Professional Mission Control Matte Cards with Frosted Depth */
    .mission-card {
      background: rgba(13, 21, 38, 0.80);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 16px;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.5);
    }

    .mission-card-subtle {
      background: rgba(9, 15, 28, 0.72);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }"""

if old_card_css in content:
    content = content.replace(old_card_css, new_card_css, 1)
    print("1. Successfully updated .mission-card CSS styles with frosted glass styling.")
else:
    print("Warning: old_card_css not found directly.")

# 2. Update setState to support tactical DOM refresh
old_set_state = """    // State Mutation Helper
    function setState(updater) {
      if (typeof updater === 'function') {
        state = updater(state);
      } else {
        state = { ...state, ...updater };
      }
      renderApp();
    }"""

new_set_state = """    // State Mutation Helper
    function setState(updater) {
      if (typeof updater === 'function') {
        state = updater(state);
      } else {
        state = { ...state, ...updater };
      }
      if (typeof isTacticalExpanded !== 'undefined' && isTacticalExpanded) {
        updateTacticalDeckDOM();
      } else {
        renderApp();
      }
    }

    function setTacticalScreen(screenId) {
      setState({ activeScreen: screenId });
    }

    function updateTacticalDeckDOM() {
      const hud = document.getElementById('tacticalHudOverlay');
      if (hud && typeof renderTacticalDeckContent === 'function') {
        hud.innerHTML = renderTacticalDeckContent();
      }
    }"""

if old_set_state in content:
    content = content.replace(old_set_state, new_set_state, 1)
    print("2. Successfully updated setState and added updateTacticalDeckDOM.")
else:
    print("Warning: old_set_state not found directly.")

# 3. Add renderTacticalIncidentModal and renderTacticalDeckContent right after renderIngestModal
target_ingest_end = "    }\n\n    // =========================================================================\n    // MISSION INITIALIZATION LOADING SCREEN"

tactical_deck_functions = """    }

    // =========================================================================
    // TACTICAL INCIDENT WORKSPACE MODAL
    // =========================================================================
    function renderTacticalIncidentModal() {
      const selectedInc = state.incidents.find(i => i.id === state.selectedIncidentId);
      if (!selectedInc) return '';

      return `
        <div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div class="w-full max-w-xl mission-card p-6 space-y-4 border border-white/20 shadow-2xl">
            <div class="flex items-center justify-between border-b border-[#1b2840] pb-3">
              <div>
                <span class="text-xs font-mono font-bold text-red-400 bg-red-950 px-2 py-0.5 rounded border border-red-800">${selectedInc.code}</span>
                <h3 class="text-base font-bold text-white mt-1 font-heading">${selectedInc.title}</h3>
                <p class="text-xs text-slate-400 mt-0.5">${selectedInc.location?.sector || 'Coastal Zone'}</p>
              </div>
              <button onclick="setState({ selectedIncidentId: null })" class="text-slate-400 hover:text-white text-lg cursor-pointer">✕</button>
            </div>

            <p class="text-xs text-slate-200 mission-card-subtle p-3.5 leading-relaxed font-sans">
              <strong class="text-red-400 font-mono">TACTICAL INCIDENT BRIEFING:</strong> ${selectedInc.aiScoreV2?.briefing?.headline || 'High-urgency emergency distress packet corroborated via multi-hop mesh.'}
            </p>

            <div class="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div class="mission-card-subtle p-2">Priority: <strong class="text-red-400">${selectedInc.aiScoreV2?.priority || 95}/100</strong></div>
              <div class="mission-card-subtle p-2">Corroboration: <strong class="text-emerald-400">${selectedInc.corroborationCount || 3} Nodes</strong></div>
              <div class="mission-card-subtle p-2">Hops: <strong class="text-blue-400">4 Mesh Hops</strong></div>
            </div>

            <div class="flex flex-wrap items-center justify-end gap-2 pt-3 border-t border-[#1b2840]">
              <button onclick="handleDispatch('${selectedInc.id}', 'BOAT_RESCUE')" class="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md cursor-pointer">
                Dispatch Rescue Boat
              </button>
              <button onclick="handleDispatch('${selectedInc.id}', 'AMPHIBIOUS')" class="px-4 py-2 rounded-lg bg-red-700 hover:bg-red-600 text-white font-medium text-xs shadow-md cursor-pointer">
                Dispatch Amphibious Vehicle
              </button>
              <button onclick="setState({ selectedIncidentId: null })" class="px-3.5 py-2 rounded-lg bg-[#16243b] hover:bg-[#20324e] text-slate-300 text-xs cursor-pointer">Close</button>
            </div>
          </div>
        </div>
      `;
    }

    // =========================================================================
    // TACTICAL COMMAND DECK (COMPLETE MASTER PRD SYSTEM OVER RAINY BACKGROUND)
    // =========================================================================
    function renderTacticalDeckContent() {
      let screenHtml = '';
      if (state.activeScreen === 'screen1_hero') screenHtml = renderScreen1Hero();
      else if (state.activeScreen === 'screen2_ai') screenHtml = renderScreen2AI();
      else if (state.activeScreen === 'screen3_risk') screenHtml = renderScreen3Risk();
      else if (state.activeScreen === 'screen4_resilience') screenHtml = renderScreen4Resilience();
      else screenHtml = renderScreen1Hero();

      return `
        <div class="relative w-full max-w-7xl h-[92vh] flex flex-col rounded-[26px] overflow-hidden border border-white/20 text-white pointer-events-auto backdrop-blur-2xl transition-all duration-500 my-auto shadow-2xl" style="background-image: linear-gradient(to bottom, rgba(6, 12, 24, 0.90) 0%, rgba(9, 16, 30, 0.84) 45%, rgba(4, 8, 18, 0.94) 100%), url('/static/rainy_storm_bg.jpg'); background-size: cover; background-position: center; box-shadow: 0 35px 85px -12px rgba(0, 0, 0, 0.96), 0 0 0 1px rgba(255, 255, 255, 0.12);">
          
          <!-- TACTICAL COMMAND DECK TOP BAR -->
          <header class="h-16 px-4 sm:px-6 bg-slate-950/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between shrink-0 select-none z-20">
            
            <!-- Left: Logo & Status -->
            <div onclick="exitTacticalDeck()" class="flex items-center space-x-3 cursor-pointer group" title="Return to Public Portal">
              <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-800 border border-blue-400/40 flex items-center justify-center text-white font-bold text-base shadow-lg group-hover:scale-105 transition-transform">
                🌀
              </div>
              <div>
                <div class="flex items-center space-x-2">
                  <span class="font-black text-sm sm:text-base tracking-tight text-white group-hover:text-blue-400 font-heading transition-colors">
                    CHAKRAVYOOH
                  </span>
                  <span class="text-[10px] font-mono font-bold text-blue-300 bg-blue-950/80 border border-blue-800/80 px-1.5 py-0.5 rounded">
                    TACTICAL COMMAND DECK
                  </span>
                  <span class="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-red-300 bg-red-950/80 border border-red-800/80 px-2 py-0.5 rounded">
                    <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                    BOB-04 ACTIVE
                  </span>
                </div>
                <p class="text-[10px] text-slate-400 font-mono hidden md:block">
                  Multi-Source AI Engine • ISRO Satellite Telemetry • Resilient Mesh Operations
                </p>
              </div>
            </div>

            <!-- Center: 4 Master PRD Tabs -->
            <nav class="flex items-center bg-[#050914]/90 p-1 rounded-xl border border-white/10 text-xs font-mono">
              <button onclick="setTacticalScreen('screen1_hero')" class="px-2.5 sm:px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${state.activeScreen === 'screen1_hero' ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-900/60' : 'text-slate-400 hover:text-slate-200'}">
                <span>🌀</span>
                <span class="hidden sm:inline">1 • Cyclone Intel</span>
                <span class="sm:hidden">Intel</span>
              </button>

              <button onclick="setTacticalScreen('screen2_ai')" class="px-2.5 sm:px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${state.activeScreen === 'screen2_ai' ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-900/60' : 'text-slate-400 hover:text-slate-200'}">
                <span>🧠</span>
                <span class="hidden sm:inline">2 • AI Fusion</span>
                <span class="sm:hidden">AI</span>
              </button>

              <button onclick="setTacticalScreen('screen3_risk')" class="px-2.5 sm:px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${state.activeScreen === 'screen3_risk' ? 'bg-blue-600 text-white font-bold shadow-md shadow-blue-900/60' : 'text-slate-400 hover:text-slate-200'}">
                <span>⚠️</span>
                <span class="hidden sm:inline">3 • Risk Zones</span>
                <span class="sm:hidden">Risk</span>
              </button>

              <button onclick="setTacticalScreen('screen4_resilience')" class="px-2.5 sm:px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${state.activeScreen === 'screen4_resilience' ? 'bg-red-700 text-white font-bold shadow-md shadow-red-900/60' : 'text-slate-400 hover:text-slate-200'}">
                <span>🛡️</span>
                <span class="hidden sm:inline">4 • Resilient Mesh</span>
                <span class="sm:hidden">Mesh</span>
              </button>
            </nav>

            <!-- Right: Actions & Exit -->
            <div class="flex items-center space-x-2">
              <button onclick="setState({ showIngestModal: true })" class="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/80 hover:bg-red-900 border border-red-700/80 text-red-200 text-xs font-mono font-bold transition-all cursor-pointer" title="Feed Live SOS Packet">
                <span>⚡</span>
                <span>Ingest SOS</span>
              </button>
              <button onclick="fetchRealtimeWeather()" class="hidden lg:flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#142034] hover:bg-[#1e2f4c] border border-white/10 text-slate-300 text-xs font-mono transition-colors cursor-pointer" title="Sync Realtime Weather Telemetry">
                <span>🔄</span>
                <span>Sync</span>
              </button>
              <button onclick="exitTacticalDeck()" class="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm" title="Exit Tactical View back to Portal">
                <span>✕</span>
                <span class="hidden sm:inline">Exit</span>
              </button>
            </div>
          </header>

          <!-- SCROLLABLE PRD CONTENT DECK -->
          <div id="tacticalDeckScrollArea" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 custom-scrollbar bg-black/25 backdrop-blur-[2px]">
            ${screenHtml}
          </div>

          <!-- EMBEDDED MODALS -->
          ${renderIngestModal()}
          ${renderTacticalIncidentModal()}
        </div>
      `;
    }

    // =========================================================================
    // MISSION INITIALIZATION LOADING SCREEN"""

if target_ingest_end in content:
    content = content.replace(target_ingest_end, tactical_deck_functions, 1)
    print("3. Successfully injected renderTacticalIncidentModal and renderTacticalDeckContent.")
else:
    print("Warning: target_ingest_end not found.")

# 4. Update launchTacticalDeck to trigger updateTacticalDeckDOM
old_launch = """    function launchTacticalDeck() {
      isTacticalExpanded = true;
      const hero = document.getElementById('heroGlobeSection');"""

new_launch = """    function launchTacticalDeck() {
      isTacticalExpanded = true;
      updateTacticalDeckDOM();
      const hero = document.getElementById('heroGlobeSection');"""

if old_launch in content:
    content = content.replace(old_launch, new_launch, 1)
    print("4. Successfully added updateTacticalDeckDOM to launchTacticalDeck.")
else:
    print("Warning: old_launch not found.")

# 5. Replace the static 2-column weather card inside tacticalHudOverlay with renderTacticalDeckContent()
old_hud_block_start = '            <!-- SEAMLESS FULLSCREEN TACTICAL HUD OVERLAY (ACTIVATES ON LAUNCH) -->\n            <div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-3 sm:p-6 select-none font-sans overflow-y-auto">\n              \n              <!-- MAIN CONTROL PANEL (PERFECT MATCH TO USER REFERENCE IMAGE) -->'
old_hud_block_end = '            </div>\n          </section>\n\n          <!-- 4. PIXEL-ART WEATHER WIDGETS DECK'

new_hud_block = """            <!-- SEAMLESS FULLSCREEN TACTICAL HUD OVERLAY (ACTIVATES ON LAUNCH) -->
            <div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">
              ${renderTacticalDeckContent()}
            </div>
          </section>

          <!-- 4. PIXEL-ART WEATHER WIDGETS DECK"""

if old_hud_block_start in content and old_hud_block_end in content:
    start_pos = content.find(old_hud_block_start)
    end_pos = content.find(old_hud_block_end) + len(old_hud_block_end)
    content = content[:start_pos] + new_hud_block + content[end_pos:]
    print("5. Successfully replaced static weather forecast with complete Master PRD Tactical Command Deck inside tacticalHudOverlay.")
else:
    print("Warning: HUD overlay start or end pattern not found directly.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved update_portal.py. Now executing update_portal.py to generate production HTML files...")
