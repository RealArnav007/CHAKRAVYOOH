#!/usr/bin/env python3
"""
tune_rainy_deck_background.py
Applies the exact rainy window storm background from Image 1 to the Command Panel
housing all the Master PRD data from Image 2, ensuring optimal frosted glass transparency.
"""

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update CSS for frosted glass cards so the rainy window is clearly visible behind them
old_css = """    /* Professional Mission Control Matte Cards with Frosted Depth */
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

new_css = """    /* High-Fidelity Frosted Glass Mission Control Cards over Rainy Window */
    .mission-card {
      background: rgba(10, 18, 34, 0.60);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 16px;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      box-shadow: 0 10px 30px -4px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .mission-card-subtle {
      background: rgba(7, 13, 25, 0.48);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }"""

if old_css in code:
    code = code.replace(old_css, new_css, 1)
    print("1. Updated mission-card CSS for translucent frosted glass.")
else:
    print("Warning: old_css not found directly.")

# 2. Update the background-image and styling of renderTacticalDeckContent
old_deck_container = """        <div class="relative w-full max-w-7xl h-[92vh] flex flex-col rounded-[26px] overflow-hidden border border-white/20 text-white pointer-events-auto backdrop-blur-2xl transition-all duration-500 my-auto shadow-2xl" style="background-image: linear-gradient(to bottom, rgba(6, 12, 24, 0.90) 0%, rgba(9, 16, 30, 0.84) 45%, rgba(4, 8, 18, 0.94) 100%), url('/static/rainy_storm_bg.jpg'); background-size: cover; background-position: center; box-shadow: 0 35px 85px -12px rgba(0, 0, 0, 0.96), 0 0 0 1px rgba(255, 255, 255, 0.12);">
          
          <!-- TACTICAL COMMAND DECK TOP BAR -->
          <header class="h-16 px-4 sm:px-6 bg-slate-950/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between shrink-0 select-none z-20">"""

new_deck_container = """        <div class="relative w-full max-w-7xl h-[94vh] flex flex-col rounded-[26px] overflow-hidden border border-white/20 text-white pointer-events-auto backdrop-blur-xl transition-all duration-500 my-auto shadow-2xl bg-cover bg-center" style="background-image: linear-gradient(180deg, rgba(4, 8, 16, 0.40) 0%, rgba(6, 12, 22, 0.32) 45%, rgba(3, 6, 14, 0.48) 100%), url('/static/rainy_storm_bg.jpg'); box-shadow: 0 35px 90px -10px rgba(0, 0, 0, 0.96), 0 0 0 1px rgba(255, 255, 255, 0.14);">
          
          <!-- TACTICAL COMMAND DECK TOP BAR -->
          <header class="h-16 px-4 sm:px-6 bg-[#060b14]/65 backdrop-blur-xl border-b border-white/10 flex items-center justify-between shrink-0 select-none z-20">"""

if old_deck_container in code:
    code = code.replace(old_deck_container, new_deck_container, 1)
    print("2. Updated Tactical Command Deck container to show rainy window storm background clearly.")
else:
    print("Warning: old_deck_container not found directly.")

# 3. Make the scroll area transparent so the rainy window shines through without a 25% black mask
old_scroll_area = '<div id="tacticalDeckScrollArea" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 custom-scrollbar bg-black/25 backdrop-blur-[2px]">'
new_scroll_area = '<div id="tacticalDeckScrollArea" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 custom-scrollbar bg-transparent">'

if old_scroll_area in code:
    code = code.replace(old_scroll_area, new_scroll_area, 1)
    print("3. Made tacticalDeckScrollArea transparent.")
else:
    print("Warning: old_scroll_area not found directly.")

# 4. Check for URL parameter ?view=command or hash #command to auto-open if desired
old_dom_ready = """    document.addEventListener('DOMContentLoaded', () => {
      renderApp();
      mountAllGlobes();
      fetchRealtimeWeather('gopalpur');
      const btn = document.getElementById('launchTacticalBtn');
      if (btn) btn.addEventListener('click', () => launchTacticalDeck());
    });"""

new_dom_ready = """    document.addEventListener('DOMContentLoaded', () => {
      renderApp();
      mountAllGlobes();
      fetchRealtimeWeather('gopalpur');
      const btn = document.getElementById('launchTacticalBtn');
      if (btn) btn.addEventListener('click', () => launchTacticalDeck());
      // Auto-launch if URL contains view=command or hash #command
      if (window.location.search.includes('view=command') || window.location.hash.includes('command')) {
        setTimeout(launchTacticalDeck, 200);
      }
    });"""

if old_dom_ready in code:
    code = code.replace(old_dom_ready, new_dom_ready, 1)
    print("4. Added auto-launch URL parameter support (?view=command).")
else:
    print("Warning: old_dom_ready not found directly.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py. Now generating HTML files...")
