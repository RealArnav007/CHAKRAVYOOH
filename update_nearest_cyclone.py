import os

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update the pill HTML to have id="nearestCyclonePill" and data-status="cyclone"
old_pill = """                <!-- Active Mission Pill (Subtle Titanium & Cyber-Slate) -->
                <div class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-slate-700/60 text-slate-300 text-xs font-mono font-semibold backdrop-blur-md shadow-lg">
                  <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span class="text-slate-200">CYCLONE BOB-04 (VSCS)</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-cyan-300">155 KM/H</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-slate-400">BAY OF BENGAL</span>
                </div>"""

new_pill = """                <!-- Dynamic Nearest Cyclone Status Pill -->
                <div id="nearestCyclonePill" data-status="cyclone" class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-slate-700/60 text-slate-300 text-xs font-mono font-semibold backdrop-blur-md shadow-lg transition-all duration-300 select-none">
                  <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span class="text-slate-200">CYCLONE BOB-04 (VSCS)</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-cyan-300">155 KM/H</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-slate-400">BAY OF BENGAL</span>
                </div>"""

if old_pill in code:
    code = code.replace(old_pill, new_pill, 1)
    print("Replaced active mission pill with dynamic nearestCyclonePill.")
else:
    print("ERROR: old_pill not found in code!")
    exit(1)

# 2. Add dynamic proximity calculation inside animate()
target_coord_end = "            coordElem.textContent = `${pad(latDeg)}° ${pad(latMin)}' ${latDir}   ${pad(lonDeg)}° ${pad(lonMin)}' ${lonDir}`;\n          }\n        }"

new_cyclone_tracking = """            coordElem.textContent = `${pad(latDeg)}° ${pad(latMin)}' ${latDir}   ${pad(lonDeg)}° ${pad(lonMin)}' ${lonDir}`;
          }

          // Dynamic Nearest Cyclone Telemetry Tracking
          const cyclonePill = document.getElementById('nearestCyclonePill');
          if (cyclonePill) {
            const activeCyclones = [
              { name: 'CYCLONE BOB-04 (VSCS)', speed: '155 KM/H', basin: 'BAY OF BENGAL', lat: 16.82, lon: 84.48 }
            ];

            let nearest = null;
            let minDist = Infinity;
            const toRad = Math.PI / 180;

            activeCyclones.forEach(c => {
              const dLat = (c.lat - lat) * toRad;
              const dLon = (c.lon - lon) * toRad;
              const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                        Math.cos(lat * toRad) * Math.cos(c.lat * toRad) *
                        Math.sin(dLon / 2) * Math.sin(dLon / 2);
              const dist = 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
              if (dist < minDist) {
                minDist = dist;
                nearest = c;
              }
            });

            // Proximity threshold: 3,200 KM
            if (nearest && minDist <= 3200) {
              if (cyclonePill.getAttribute('data-status') !== 'cyclone') {
                cyclonePill.setAttribute('data-status', 'cyclone');
                cyclonePill.innerHTML = `
                  <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span class="text-slate-200">${nearest.name}</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-cyan-300 font-bold">${nearest.speed}</span>
                  <span class="text-slate-600">•</span>
                  <span class="text-slate-400">${nearest.basin}</span>
                `;
              }
            } else {
              if (cyclonePill.getAttribute('data-status') !== 'calm') {
                cyclonePill.setAttribute('data-status', 'calm');
                cyclonePill.innerHTML = `
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  <span class="text-slate-300 font-medium tracking-wide">NO CYCLONE FORMATION NEARBY</span>
                `;
              }
            }
          }
        }"""

if target_coord_end in code:
    code = code.replace(target_coord_end, new_cyclone_tracking, 1)
    print("Injected dynamic nearest cyclone tracking into animate() loop.")
else:
    print("ERROR: target_coord_end not found in code!")
    exit(1)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("update_portal.py updated successfully.")
