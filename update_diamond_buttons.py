import os

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add diamond button CSS to <style>
diamond_css = """    /* Precision Diamond-Cut Tactical Button Styling */
    .diamond-btn-outer {
      position: relative;
      display: inline-flex;
      align-items: center;
      padding: 1px;
      clip-path: polygon(10px 0%, calc(100% - 10px) 0%, 100% 10px, 100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0% calc(100% - 10px), 0% 10px);
      transition: all 0.25s ease;
    }
    .diamond-btn-inner {
      display: inline-flex;
      align-items: center;
      gap: 0.65rem;
      width: 100%;
      height: 100%;
      padding: 0.75rem 1.35rem;
      clip-path: polygon(9px 0%, calc(100% - 9px) 0%, 100% 9px, 100% calc(100% - 9px), calc(100% - 9px) 100%, 9px 100%, 0% calc(100% - 9px), 0% 9px);
      transition: all 0.25s ease;
    }
"""

if ".diamond-btn-outer" not in code:
    code = code.replace("  <style>", "  <style>\n" + diamond_css, 1)
    print("Added diamond button CSS.")

# 2. Update the hero text block: subtle colors, diamond buttons, and remove the AI quote
s1 = '                <!-- Active Mission Pill -->'
s2 = '              </div>\n            </div>\n\n            <!-- REAL-TIME TRANSLUCENT COORDINATES HUD'

p1 = code.find(s1)
p2 = code.find(s2)

if p1 == -1 or p2 == -1:
    print(f"ERROR: Could not find markers! p1={p1}, p2={p2}")
    exit(1)

new_hero_content = """                <!-- Active Mission Pill (Subtle Titanium & Cyber-Slate) -->
                <div class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-slate-700/60 text-slate-300 text-xs font-mono font-semibold backdrop-blur-md shadow-lg">
                  <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span class="text-slate-200">CYCLONE BOB-04 (VSCS)</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-cyan-300">155 KM/H</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-slate-400">BAY OF BENGAL</span>
                </div>

                <!-- Main Headline -->
                <div class="space-y-2.5">
                  <h1 class="text-3xl sm:text-5xl lg:text-5xl font-black font-heading tracking-tight text-white leading-tight">
                    AI-Powered Tropical Cyclone Intelligence
                  </h1>
                  <p class="text-sm sm:text-base text-slate-300 font-light leading-relaxed">
                    Fusing Indian geostationary satellite telemetry (<strong class="text-slate-100 font-medium">INSAT-3DR/3DS</strong>), polar scatterometry, and oceanic buoy arrays to predict storm evolution — coupled with <strong class="text-cyan-300 font-medium">Chakravyooh's resilient emergency mesh</strong> network.
                  </p>
                </div>

                <!-- Minimal Primary Actions with Diamond Cut Form & Subtle Professional Color Coding -->
                <div class="flex flex-wrap items-center gap-3.5 pt-2">
                  <button id="launchTacticalBtn" onclick="launchTacticalDeck()" class="diamond-btn-outer bg-gradient-to-r from-slate-600/50 via-cyan-500/40 to-slate-600/50 hover:from-cyan-400 hover:to-cyan-400 active:scale-95 transition-all shadow-xl shadow-black/80 cursor-pointer group" title="Launch Operational Tactical Deck">
                    <span class="diamond-btn-inner bg-[#0b101a]/95 hover:bg-[#0f1726] text-slate-100 font-mono text-xs sm:text-sm font-semibold tracking-wider">
                      <span class="text-cyan-400 group-hover:scale-125 transition-transform text-xs">◆</span>
                      <span class="tracking-wide">Launch Tactical Command Deck</span>
                      <span class="text-slate-400 group-hover:text-cyan-300 group-hover:translate-x-1 transition-all text-xs">➔</span>
                    </span>
                  </button>

                  <button id="godsEyeHeroBtn" onclick="triggerGodsEyeSequence()" class="diamond-btn-outer bg-gradient-to-r from-slate-700/50 via-rose-500/35 to-slate-700/50 hover:from-rose-400 hover:to-rose-400 active:scale-95 transition-all shadow-xl shadow-black/80 cursor-pointer group" title="Engage God's Eye Live Satellite Reconnaissance">
                    <span class="diamond-btn-inner bg-[#120d14]/95 hover:bg-[#1a121c] text-slate-100 font-mono text-xs sm:text-sm font-semibold tracking-wider">
                      <span class="text-rose-400 group-hover:scale-125 transition-transform text-xs">◆</span>
                      <span class="tracking-wide">God's Eye</span>
                      <span class="text-[11px] text-slate-400 font-normal hidden sm:inline">• Live Recon</span>
                    </span>
                  </button>

                  <button onclick="selectPrefaceTarget('cyclone')" class="diamond-btn-outer bg-slate-700/40 hover:bg-slate-500/60 active:scale-95 transition-all shadow-lg cursor-pointer group" title="Center on Cyclone Vortex">
                    <span class="diamond-btn-inner bg-[#0a0f18]/95 hover:bg-[#101724] text-slate-300 hover:text-slate-100 font-mono text-xs font-medium">
                      <span class="text-slate-400 group-hover:text-slate-200 text-xs">◇</span>
                      <span>Focus Storm Eye</span>
                    </span>
                  </button>
                </div>"""

code = code[:p1] + new_hero_content + "\n" + code[p2:]
print("Updated hero section successfully.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("update_portal.py updated successfully.")
