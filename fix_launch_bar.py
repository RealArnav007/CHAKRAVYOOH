#!/usr/bin/env python3
"""
fix_launch_bar.py
Fixes the Launch Tactical Command Deck bar so it is 100% clickable, responsive,
and serves as the singular, smooth passage to the Tactical Command Deck.
"""

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Set isLoading: false by default so no loading screen blocks clicks
code = code.replace(
    "isLoading: true,",
    "isLoading: false,",
    1
)

# 2. Remove automatic startLoadingSequence() on initial load
code = code.replace(
    "    document.addEventListener('DOMContentLoaded', () => {\n      renderApp();\n      mountAllGlobes();\n      startLoadingSequence();\n      fetchRealtimeWeather('gopalpur');\n    });\n    renderApp();\n    startLoadingSequence();",
    "    document.addEventListener('DOMContentLoaded', () => {\n      renderApp();\n      mountAllGlobes();\n      fetchRealtimeWeather('gopalpur');\n      const btn = document.getElementById('launchTacticalBtn');\n      if (btn) btn.addEventListener('click', () => launchTacticalDeck());\n    });\n    renderApp();"
)

# 3. Add 'hidden' class to tacticalHudOverlay by default so it can NEVER intercept pointer events when inactive
old_hud_overlay = '<div id="tacticalHudOverlay" class="absolute inset-0 z-30 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">'
new_hud_overlay = '<div id="tacticalHudOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">'

if old_hud_overlay in code:
    code = code.replace(old_hud_overlay, new_hud_overlay, 1)
    print("Added 'hidden' and z-40 to tacticalHudOverlay.")
else:
    print("Warning: old_hud_overlay not found directly.")

# 4. Enhance launchTacticalDeck and exitTacticalDeck
old_launch_func = """    function launchTacticalDeck() {
      isTacticalExpanded = true;
      updateTacticalDeckDOM();
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

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
      if (hud) {
        hud.classList.remove('opacity-0', 'pointer-events-none');
        hud.classList.add('opacity-100', 'pointer-events-auto');
      }
      document.body.style.overflow = 'hidden';"""

new_launch_func = """    function launchTacticalDeck() {
      isTacticalExpanded = true;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (hud) {
        if (typeof renderTacticalDeckContent === 'function') {
          hud.innerHTML = renderTacticalDeckContent();
        }
        hud.classList.remove('hidden');
        void hud.offsetWidth; // Force reflow
        hud.classList.remove('opacity-0', 'pointer-events-none');
        hud.classList.add('opacity-100', 'pointer-events-auto');
      }
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
      document.body.style.overflow = 'hidden';"""

if old_launch_func in code:
    code = code.replace(old_launch_func, new_launch_func, 1)
    print("Updated launchTacticalDeck function.")
else:
    print("Warning: old_launch_func not found directly.")

old_exit_func = """    function exitTacticalDeck() {
      isTacticalExpanded = false;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (hud) {
        hud.classList.remove('opacity-100', 'pointer-events-auto');
        hud.classList.add('opacity-0', 'pointer-events-none');
      }"""

new_exit_func = """    function exitTacticalDeck() {
      isTacticalExpanded = false;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (hud) {
        hud.classList.remove('opacity-100', 'pointer-events-auto');
        hud.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => {
          if (!isTacticalExpanded && hud) {
            hud.classList.add('hidden');
          }
        }, 700);
      }"""

if old_exit_func in code:
    code = code.replace(old_exit_func, new_exit_func, 1)
    print("Updated exitTacticalDeck function.")
else:
    print("Warning: old_exit_func not found directly.")

# 5. Enhance the Hero Launch Button element
old_hero_btn = """                  <button onclick="launchTacticalDeck()" class="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs font-mono transition-all shadow-lg shadow-blue-900/50 flex items-center gap-2">
                    <span>Launch Tactical Command Deck</span>
                    <span>➔</span>
                  </button>"""

new_hero_btn = """                  <button id="launchTacticalBtn" onclick="launchTacticalDeck()" class="relative z-30 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 active:scale-95 text-white font-bold text-sm font-mono transition-all shadow-2xl shadow-blue-900/70 flex items-center gap-3 cursor-pointer border border-blue-400/40 group">
                    <span class="text-lg group-hover:scale-110 transition-transform">🚀</span>
                    <span class="tracking-wide">Launch Tactical Command Deck</span>
                    <span class="text-base group-hover:translate-x-1.5 transition-transform">➔</span>
                  </button>"""

if old_hero_btn in code:
    code = code.replace(old_hero_btn, new_hero_btn, 1)
    print("Enhanced Launch Tactical Command Deck button styling and ID.")
else:
    print("Warning: old_hero_btn not found directly.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py. Now executing update_portal.py...")
