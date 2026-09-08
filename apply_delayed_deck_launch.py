import os

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Locate launchTacticalDeck up to openLoginModal
start_marker = "    function launchTacticalDeck() {"
end_marker = "    function openLoginModal() {"

p1 = code.find(start_marker)
p2 = code.find(end_marker)

if p1 == -1 or p2 == -1:
    print(f"ERROR: Could not find function markers! p1={p1}, p2={p2}")
    exit(1)

new_launch_and_exit = """    let deckLaunchTimer = null;

    function launchTacticalDeck() {
      isTacticalExpanded = true;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const deckTelemetry = document.getElementById('deckLaunchTelemetry');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      // 1. Immediately expand Hero Section to cover the entire screen
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
      document.body.style.overflow = 'hidden';

      // 2. Show brief, sleek orbital synchronization indicator during the Earth rotation
      if (deckTelemetry) {
        deckTelemetry.classList.remove('hidden');
        void deckTelemetry.offsetWidth;
        deckTelemetry.classList.remove('opacity-0');
        deckTelemetry.classList.add('opacity-100');
      }

      // 3. Three.js: Rotate Earth & swoop camera forward so Earth covers the entire screen!
      if (inst) {
        // Rotate smoothly to Bay of Bengal & Cyclone BOB-04 vortex (dist: 1.35)
        inst.setTargetRotation(0.32, Math.PI * 0.965, 1.35);
        
        // Continuous smooth resizing of WebGL canvas as the container expands
        const start = performance.now();
        function smoothResize() {
          if (inst && inst.camera && inst.renderer) {
            const w = window.innerWidth;
            const h = window.innerHeight;
            inst.camera.aspect = w / h;
            inst.camera.updateProjectionMatrix();
            inst.renderer.setSize(w, h);
          }
          if (performance.now() - start < 2400) {
            requestAnimationFrame(smoothResize);
          }
        }
        requestAnimationFrame(smoothResize);
      }

      // 4. Delay Tactical Deck Panel by 1.8s so the user can fully appreciate the Earth rotating and covering the screen!
      if (deckLaunchTimer) clearTimeout(deckLaunchTimer);
      deckLaunchTimer = setTimeout(() => {
        if (!isTacticalExpanded) return;

        // Fade out transition telemetry
        if (deckTelemetry) {
          deckTelemetry.classList.remove('opacity-100');
          deckTelemetry.classList.add('opacity-0');
          setTimeout(() => { deckTelemetry.classList.add('hidden'); }, 500);
        }

        // Now smoothly reveal the Tactical Command Deck panel over the rainy glass background!
        if (hud) {
          if (typeof renderTacticalDeckContent === 'function') {
            hud.innerHTML = renderTacticalDeckContent();
          }
          hud.classList.remove('hidden');
          void hud.offsetWidth; // Force reflow
          hud.classList.remove('opacity-0', 'pointer-events-none');
          hud.classList.add('opacity-100', 'pointer-events-auto');
        }
      }, 1800);
    }

    function exitTacticalDeck() {
      isTacticalExpanded = false;
      if (deckLaunchTimer) clearTimeout(deckLaunchTimer);

      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const hud = document.getElementById('tacticalHudOverlay');
      const deckTelemetry = document.getElementById('deckLaunchTelemetry');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (deckTelemetry) {
        deckTelemetry.classList.add('hidden', 'opacity-0');
      }

      if (hud) {
        hud.classList.remove('opacity-100', 'pointer-events-auto');
        hud.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => {
          if (!isTacticalExpanded && hud) {
            hud.classList.add('hidden');
          }
        }, 700);
      }
      if (textCard) {
        textCard.classList.remove('opacity-0', 'pointer-events-none', '-translate-y-8', 'scale-95');
      }
      if (heroDock) {
        heroDock.classList.remove('opacity-0', 'pointer-events-none');
      }
      if (hero) {
        hero.classList.remove('fixed', 'inset-0', 'z-50', 'w-screen', 'h-screen');
        hero.classList.add('relative', 'min-h-[640px]', 'lg:min-h-[700px]');
      }
      document.body.style.overflow = '';

      // Reset Globe back to standard preface orbit
      if (inst) {
        inst.setTargetRotation(0.28, Math.PI * 0.96, 2.45);
        const start = performance.now();
        function smoothResize() {
          if (hero && inst && inst.camera && inst.renderer) {
            const w = hero.clientWidth || window.innerWidth;
            const h = hero.clientHeight || 700;
            inst.camera.aspect = w / h;
            inst.camera.updateProjectionMatrix();
            inst.renderer.setSize(w, h);
          }
          if (performance.now() - start < 850) {
            requestAnimationFrame(smoothResize);
          }
        }
        requestAnimationFrame(smoothResize);
      }
    }

"""

code = code[:p1] + new_launch_and_exit + code[p2:]
print("Updated launchTacticalDeck and exitTacticalDeck with 1.8s delay.")

# 2. Add deckLaunchTelemetry markup right before tacticalHudOverlay
old_hud_markup = """            <!-- SEAMLESS FULLSCREEN TACTICAL HUD OVERLAY (ACTIVATES ON LAUNCH) -->
            <div id="tacticalHudOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">"""

new_hud_markup = """            <!-- TACTICAL DECK LAUNCH TRANSITION OVERLAY (ACTIVE FOR 1.8s WHILE GLOBE ROTATES & EXPANDS) -->
            <div id="deckLaunchTelemetry" class="hidden absolute top-8 inset-x-0 z-40 pointer-events-none flex justify-center opacity-0 transition-opacity duration-500 font-mono select-none">
              <div class="inline-flex items-center gap-3 px-5 py-2.5 rounded-2xl bg-black/85 border border-blue-500/50 backdrop-blur-xl shadow-2xl text-xs text-white">
                <span class="w-2.5 h-2.5 rounded-full bg-blue-500 animate-ping"></span>
                <span class="font-bold tracking-wider text-blue-300 uppercase">SYNCHRONIZING TACTICAL DECK ORBIT</span>
                <span class="text-slate-600">•</span>
                <span class="text-slate-300">TARGET: BAY OF BENGAL (BOB-04)</span>
              </div>
            </div>

            <!-- SEAMLESS FULLSCREEN TACTICAL HUD OVERLAY (ACTIVATES ON LAUNCH) -->
            <div id="tacticalHudOverlay" class="hidden absolute inset-0 z-40 pointer-events-none opacity-0 transition-opacity duration-700 flex flex-col justify-center items-center p-2 sm:p-4 md:p-6 select-none font-sans overflow-y-auto">"""

if old_hud_markup in code:
    code = code.replace(old_hud_markup, new_hud_markup, 1)
    print("Added deckLaunchTelemetry markup successfully.")
else:
    print("ERROR: old_hud_markup not found!")
    exit(1)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("update_portal.py updated successfully.")
