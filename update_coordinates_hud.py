import os

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update the dock markup to ONLY keep coordinates, increase font size, off-white and translucent
old_dock = """            <!-- UNIFIED ELEGANT FLOATING DOCK (Zoom Earth / Apple Minimal Style) -->
            <div id="heroDock" class="absolute bottom-6 inset-x-4 z-20 flex justify-center pointer-events-none transition-all duration-500">
              <div class="pointer-events-auto flex flex-wrap items-center gap-2.5 sm:gap-3 bg-[#080e1b]/80 border border-white/10 backdrop-blur-2xl px-4 py-2 rounded-full shadow-2xl text-xs font-mono">
                
                <!-- Focus Presets -->
                <button onclick="triggerGodsEyeSequence()" class="px-3 py-1 rounded-full bg-red-950/90 hover:bg-red-900 border border-red-500/70 text-red-300 text-[11px] font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-md shadow-red-900/40" title="Engage God's Eye Satellite Reconnaissance">
                  <span>👁️</span>
                  <span>God's Eye</span>
                </button>
                <button onclick="selectPrefaceTarget('cyclone')" class="px-2.5 py-1 rounded-full bg-[#162238] hover:bg-[#1e2f4c] border border-blue-800/60 text-blue-300 text-[11px] font-bold transition-colors flex items-center gap-1">
                  <span>🌀</span>
                  <span>BOB-04</span>
                </button>
                <button onclick="selectPrefaceTarget('insat')" class="px-2.5 py-1 rounded-full bg-blue-950/80 hover:bg-blue-900 border border-blue-700/60 text-blue-300 text-[11px] font-semibold transition-colors flex items-center gap-1">
                  <span>🛰️</span>
                  <span>INSAT-3DR</span>
                </button>
                <button onclick="selectPrefaceTarget('india')" class="px-2.5 py-1 rounded-full bg-[#121c2e] hover:bg-[#1a2840] text-slate-300 text-[11px] transition-colors">
                  🇮🇳 India
                </button>

                <div class="h-3.5 w-px bg-slate-700 hidden sm:block"></div>

                <!-- Auto-Spin Toggle -->
                <button onclick="toggleGlobeAutoRotate()" class="text-slate-300 hover:text-white transition-colors" title="Toggle Auto-Spin">
                  ${state.globeAutoRotate ? '⏸️' : '▶️'}
                </button>

                <div class="h-3.5 w-px bg-slate-700 hidden sm:block"></div>

                <!-- Live Coordinates & Wind Telemetry -->
                <div class="text-[11px] text-slate-300 flex items-center gap-2">
                  <span class="text-emerald-400 font-bold">${state.prefaceCoords}</span>
                  <span class="text-slate-600 hidden sm:inline">•</span>
                  <span class="text-red-400 font-bold hidden sm:inline">155 km/h</span>
                </div>

                <div class="h-3.5 w-px bg-slate-700 hidden md:block"></div>

                <!-- Subtle Interaction Hint -->
                <span class="text-[10px] text-slate-500 hidden md:inline">
                  Drag to rotate • Scroll to zoom
                </span>
              </div>
            </div>"""

new_dock = """            <!-- REAL-TIME TRANSLUCENT COORDINATES HUD (AT SCREEN BOTTOM) -->
            <div id="heroDock" class="absolute bottom-8 inset-x-0 z-20 flex justify-center pointer-events-none transition-all duration-500">
              <div class="pointer-events-auto bg-black/40 backdrop-blur-2xl border border-white/15 px-6 sm:px-9 py-2.5 sm:py-3.5 rounded-full shadow-2xl flex items-center justify-center select-none transition-all hover:bg-black/55 hover:border-white/25 group">
                <span id="livePrefaceCoordinates" class="text-slate-100/90 font-mono text-base sm:text-xl md:text-2xl font-semibold tracking-widest tabular-nums drop-shadow-md group-hover:text-white transition-colors">
                  ${state.prefaceCoords}
                </span>
              </div>
            </div>"""

if old_dock in code:
    code = code.replace(old_dock, new_dock, 1)
    print("Replaced heroDock markup successfully.")
else:
    print("ERROR: old_dock not found in code!")
    exit(1)

# 2. Add real-time coordinates calculation inside animate() in Three.js
target_animate_line = "        camera.position.z += (targetCamDist - camera.position.z) * 0.08;"
realtime_coords_calc = """        camera.position.z += (targetCamDist - camera.position.z) * 0.08;

        // Real-Time Earth Coordinate Calculation facing viewer
        if (containerId === 'prefaceInteractiveGlobe') {
          const localCamPos = globeGroup.worldToLocal(camera.position.clone()).normalize();
          const lat = Math.asin(Math.max(-1.0, Math.min(1.0, localCamPos.y))) * (180 / Math.PI);
          let lon = (Math.atan2(localCamPos.z, -localCamPos.x) * (180 / Math.PI)) - 180;
          while (lon < -180) lon += 360;
          while (lon > 180) lon -= 360;

          const coordElem = document.getElementById('livePrefaceCoordinates');
          if (coordElem) {
            const latDeg = Math.floor(Math.abs(lat));
            const latMin = Math.round((Math.abs(lat) - latDeg) * 60);
            const latDir = lat >= 0 ? 'N' : 'S';

            const lonDeg = Math.floor(Math.abs(lon));
            const lonMin = Math.round((Math.abs(lon) - lonDeg) * 60);
            const lonDir = lon >= 0 ? 'E' : 'W';

            const pad = (n) => n < 10 ? '0' + n : n;
            coordElem.textContent = `${pad(latDeg)}° ${pad(latMin)}' ${latDir}   ${pad(lonDeg)}° ${pad(lonMin)}' ${lonDir}`;
          }
        }"""

if target_animate_line in code:
    code = code.replace(target_animate_line, realtime_coords_calc, 1)
    print("Injected real-time coordinate calculation into animate() loop.")
else:
    print("ERROR: target_animate_line not found in code!")
    exit(1)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("update_portal.py updated successfully.")
