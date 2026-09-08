import os

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add Leaflet CSS and JS to <head>
leaflet_head = """  <!-- Leaflet Map Engine for High-Definition Satellite Reconnaissance -->
  <link rel="stylesheet" href="/static/css/leaflet.css">
  <script src="/static/js/leaflet.js"></script>

  <!-- Three.js for 3D Interactive Earth & Satellite Globe -->"""

code = code.replace('  <!-- Three.js for 3D Interactive Earth & Satellite Globe -->', leaflet_head, 1)

# 2. Add pulse CSS to <style>
radar_css = """    .custom-radar-pulse {
      position: relative;
      width: 24px;
      height: 24px;
    }
    .custom-radar-pulse::before {
      content: '';
      position: absolute;
      inset: -12px;
      border-radius: 50%;
      border: 2px solid #ef4444;
      animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }
    .custom-radar-pulse::after {
      content: '';
      position: absolute;
      inset: 2px;
      background: #ef4444;
      border-radius: 50%;
      box-shadow: 0 0 12px #ef4444;
    }
    @keyframes pulse-ring {
      0% { transform: scale(0.5); opacity: 1; }
      100% { transform: scale(2.5); opacity: 0; }
    }
    .leaflet-control-attribution { background: rgba(3,7,18,0.85) !important; color: #94a3b8 !important; font-size: 10px; }
    .leaflet-control-attribution a { color: #38bdf8 !important; }
"""

code = code.replace('  <style>', '  <style>\n' + radar_css, 1)

# 3. Replace transitionToSatelliteMap, exitGodsEye, setGodsEyeSource with full native Leaflet implementation
old_js_block = """    function transitionToSatelliteMap() {
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      
      if (godsEyeHud) {
        godsEyeHud.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { godsEyeHud.classList.add('hidden'); }, 500);
      }

      if (godsEyeFeed) {
        godsEyeFeed.classList.remove('hidden');
        void godsEyeFeed.offsetWidth;
        godsEyeFeed.classList.remove('opacity-0', 'pointer-events-none');
        godsEyeFeed.classList.add('opacity-100', 'pointer-events-auto');
      }
    }

    function exitGodsEye() {
      isGodsEyeActive = false;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (godsEyeFeed) {
        godsEyeFeed.classList.remove('opacity-100', 'pointer-events-auto');
        godsEyeFeed.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { godsEyeFeed.classList.add('hidden'); }, 600);
      }
      if (godsEyeHud) {
        godsEyeHud.classList.add('hidden', 'opacity-0');
      }

      // Smoothly zoom camera back out to normal orbit
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
    }

    function setGodsEyeSource(source) {
      const iframe = document.getElementById('godsEyeIframe');
      const btnZoom = document.getElementById('btn-gods-zoom');
      const btnScorpio = document.getElementById('btn-gods-scorpio');

      if (source === 'scorpio') {
        if (iframe) iframe.src = '/scorpio_feed?t=' + Date.now();
        if (btnScorpio) {
          btnScorpio.className = 'px-3 py-1 rounded font-bold transition-all bg-emerald-600 text-white shadow cursor-pointer';
        }
        if (btnZoom) {
          btnZoom.className = 'px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer';
        }
      } else {
        if (iframe) iframe.src = '/zoom_earth_feed?t=' + Date.now();
        if (btnZoom) {
          btnZoom.className = 'px-3 py-1 rounded font-bold transition-all bg-blue-600 text-white shadow cursor-pointer';
        }
        if (btnScorpio) {
          btnScorpio.className = 'px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer';
        }
      }
    }"""

new_js_block = """    let godsEyeMap = null;
    let godsEyeRadarLayer = null;
    let isGodsEyeRadarVisible = true;

    function initGodsEyeMap() {
      const container = document.getElementById('godsEyeMapContainer');
      if (!container || typeof L === 'undefined') return;
      if (godsEyeMap) {
        setTimeout(() => { godsEyeMap.invalidateSize(); }, 50);
        return;
      }

      godsEyeMap = L.map('godsEyeMapContainer', {
        center: [16.82, 84.48],
        zoom: 6,
        zoomControl: true,
        attributionControl: false
      });

      // 1. ESRI High-Resolution Optical Satellite Feed (Real-Life Satellite Imagery)
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18,
        attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'
      }).addTo(godsEyeMap);

      // 2. Reference boundaries and places
      L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18
      }).addTo(godsEyeMap);

      // 3. Cyclone BOB-04 Vortex Eye Pulsating Marker
      const eyeIcon = L.divIcon({
        className: 'custom-radar-pulse',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      const eyeMarker = L.marker([16.82, 84.48], { icon: eyeIcon }).addTo(godsEyeMap);
      eyeMarker.bindPopup('<div style="font-family:monospace;color:#0f172a;font-size:12px;padding:4px;"><strong>CYCLONE BOB-04 EYE</strong><br>Coords: 16.82&deg;N, 84.48&deg;E<br>Sustained: 155 km/h (Cat 3 Equivalent)<br>Central Pressure: 968 hPa<br><span style="color:#ef4444;font-weight:bold;">Extreme Danger Zone</span></div>');

      // 4. Hazard Wind Radii
      L.circle([16.82, 84.48], { radius: 45000, color: '#ef4444', weight: 2, fillColor: '#ef4444', fillOpacity: 0.25 }).addTo(godsEyeMap).bindTooltip('64 kt / 155 km/h Hurricane Core');
      L.circle([16.82, 84.48], { radius: 110000, color: '#f97316', weight: 1.5, fillColor: '#f97316', fillOpacity: 0.15, dashArray: '4,4' }).addTo(godsEyeMap).bindTooltip('50 kt / 100 km/h Severe Wind Field');
      L.circle([16.82, 84.48], { radius: 220000, color: '#eab308', weight: 1, fillColor: '#eab308', fillOpacity: 0.08, dashArray: '6,6' }).addTo(godsEyeMap).bindTooltip('34 kt / 65 km/h Tropical Gale Zone');

      // 5. Projected Landfall Track
      const trackCoords = [
        [15.2, 85.5],
        [16.1, 84.9],
        [16.82, 84.48],
        [17.7, 84.6],
        [18.5, 84.8],
        [19.27, 84.91]
      ];
      L.polyline(trackCoords, { color: '#38bdf8', weight: 3, opacity: 0.85, dashArray: '8, 8' }).addTo(godsEyeMap);
      
      const landfallMarker = L.circleMarker([19.27, 84.91], { radius: 8, color: '#dc2626', fillColor: '#ef4444', fillOpacity: 0.95 }).addTo(godsEyeMap);
      landfallMarker.bindPopup('<div style="font-family:monospace;color:#0f172a;font-size:12px;padding:4px;"><strong>PROJECTED LANDFALL TARGET</strong><br>Gopalpur, Odisha Coast<br>ETA: ~22.5 Hours<br>Anticipated Wind: 145-155 km/h</div>');

      // Coastal Port Markers
      L.circleMarker([17.6868, 83.2185], { radius: 5, color: '#06b6d4', fillColor: '#22d3ee', fillOpacity: 0.8 }).addTo(godsEyeMap).bindTooltip('Visakhapatnam Naval Command');
      L.circleMarker([20.2644, 86.6713], { radius: 5, color: '#06b6d4', fillColor: '#22d3ee', fillOpacity: 0.8 }).addTo(godsEyeMap).bindTooltip('Paradip Port Coast');

      // 6. RainViewer Live Doppler Radar Overlay
      fetch('https://api.rainviewer.com/public/weather-maps.json')
        .then(res => res.json())
        .then(data => {
          if (data && data.radar && data.radar.past && data.radar.past.length > 0) {
            const lastRadar = data.radar.past[data.radar.past.length - 1];
            const radarUrl = data.host + lastRadar.path + '/256/{z}/{x}/{y}/2/1_1.png';
            godsEyeRadarLayer = L.tileLayer(radarUrl, { opacity: 0.65, maxZoom: 18 }).addTo(godsEyeMap);
          }
        }).catch(e => console.log('RainViewer radar fallback: ', e));

      setTimeout(() => {
        if (godsEyeMap) godsEyeMap.invalidateSize();
      }, 250);
    }

    function focusGodsEyeTarget(coords, zoom) {
      if (godsEyeMap) {
        godsEyeMap.flyTo(coords, zoom, { duration: 1.2 });
      }
    }

    function toggleGodsEyeRadar() {
      const btn = document.getElementById('btn-gods-radar');
      if (!godsEyeMap) return;
      if (godsEyeRadarLayer && godsEyeMap.hasLayer(godsEyeRadarLayer)) {
        godsEyeMap.removeLayer(godsEyeRadarLayer);
        isGodsEyeRadarVisible = false;
        if (btn) btn.className = 'px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer';
      } else if (godsEyeRadarLayer) {
        godsEyeMap.addLayer(godsEyeRadarLayer);
        isGodsEyeRadarVisible = true;
        if (btn) btn.className = 'px-3 py-1 rounded font-bold transition-all bg-amber-600 text-white shadow cursor-pointer';
      }
    }

    function transitionToSatelliteMap() {
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      
      if (godsEyeHud) {
        godsEyeHud.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { godsEyeHud.classList.add('hidden'); }, 500);
      }

      if (godsEyeFeed) {
        godsEyeFeed.classList.remove('hidden');
        void godsEyeFeed.offsetWidth;
        godsEyeFeed.classList.remove('opacity-0', 'pointer-events-none');
        godsEyeFeed.classList.add('opacity-100', 'pointer-events-auto');

        // Initialize and size the high-definition satellite map natively
        initGodsEyeMap();
        setTimeout(() => {
          if (godsEyeMap) godsEyeMap.invalidateSize();
        }, 200);
      }
    }

    function exitGodsEye() {
      isGodsEyeActive = false;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const godsEyeHud = document.getElementById('godsEyeReconOverlay');
      const godsEyeFeed = document.getElementById('godsEyeFullscreenFeed');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

      if (godsEyeFeed) {
        godsEyeFeed.classList.remove('opacity-100', 'pointer-events-auto');
        godsEyeFeed.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { godsEyeFeed.classList.add('hidden'); }, 600);
      }
      if (godsEyeHud) {
        godsEyeHud.classList.add('hidden', 'opacity-0');
      }

      // Smoothly zoom camera back out to normal orbit
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
    }

    function setGodsEyeSource(source) {
      const mapDiv = document.getElementById('godsEyeMapContainer');
      const scorpioFrame = document.getElementById('godsEyeScorpioFrame');
      const btnSatellite = document.getElementById('btn-gods-satellite');
      const btnScorpio = document.getElementById('btn-gods-scorpio');

      if (source === 'scorpio') {
        if (mapDiv) mapDiv.classList.add('hidden');
        if (scorpioFrame) {
          scorpioFrame.classList.remove('hidden');
          scorpioFrame.src = '/scorpio_feed?t=' + Date.now();
        }
        if (btnScorpio) {
          btnScorpio.className = 'px-3 py-1 rounded font-bold transition-all bg-emerald-600 text-white shadow cursor-pointer';
        }
        if (btnSatellite) {
          btnSatellite.className = 'px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer';
        }
      } else {
        if (scorpioFrame) scorpioFrame.classList.add('hidden');
        if (mapDiv) {
          mapDiv.classList.remove('hidden');
          if (godsEyeMap) godsEyeMap.invalidateSize();
        }
        if (btnSatellite) {
          btnSatellite.className = 'px-3 py-1 rounded font-bold transition-all bg-blue-600 text-white shadow cursor-pointer';
        }
        if (btnScorpio) {
          btnScorpio.className = 'px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer';
        }
      }
    }"""

if old_js_block in code:
    code = code.replace(old_js_block, new_js_block, 1)
    print("Replaced JS functions successfully.")
else:
    print("ERROR: old_js_block not found!")

# 4. Replace the godsEyeFullscreenFeed HTML modal
old_html_block = """          <!-- FULLSCREEN REAL-LIFE LIVE SATELLITE FEED MAP (GOD'S EYE) -->
          <div id="godsEyeFullscreenFeed" class="hidden fixed inset-0 z-50 bg-black flex flex-col transition-opacity duration-700 opacity-0 pointer-events-none select-none font-sans">
            
            <!-- RECON SATELLITE MAP HEADER -->
            <header class="h-14 px-4 sm:px-6 bg-[#060b14]/90 backdrop-blur-xl border-b border-white/10 flex items-center justify-between z-30 shrink-0 select-none">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded-lg bg-red-950/80 border border-red-500/60 flex items-center justify-center text-red-400 font-bold text-sm shadow-lg animate-pulse">
                  👁️
                </div>
                <div>
                  <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-sm text-white tracking-wide font-heading">
                      GOD'S EYE
                    </span>
                    <span class="text-[10px] font-mono font-bold text-red-300 bg-red-950/80 border border-red-800 px-2 py-0.5 rounded">
                      ● LIVE SATELLITE FEED
                    </span>
                    <span class="text-[10px] font-mono text-slate-400 hidden sm:inline">
                      REALTIME ORBITAL COMPOSITE • BAY OF BENGAL
                    </span>
                  </div>
                </div>
              </div>

              <!-- Center: Feed Mode Toggles -->
              <div class="flex items-center bg-[#070d1a] p-1 rounded-lg border border-white/10 text-xs font-mono">
                <button onclick="setGodsEyeSource('zoom_earth')" id="btn-gods-zoom" class="px-3 py-1 rounded font-bold transition-all bg-blue-600 text-white shadow cursor-pointer">
                  🛰️ HD Live Satellite
                </button>
                <button onclick="setGodsEyeSource('scorpio')" id="btn-gods-scorpio" class="px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer">
                  📡 ISRO MOSDAC Scorpio
                </button>
              </div>

              <!-- Right: Telemetry & Exit -->
              <div class="flex items-center space-x-3 text-xs font-mono">
                <span class="text-emerald-400 hidden lg:inline font-bold">16.82°N, 84.48°E</span>
                <span class="text-slate-600 hidden lg:inline">|</span>
                <button onclick="exitGodsEye()" class="px-3.5 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 border border-red-500/60 text-white font-semibold transition-all flex items-center gap-1.5 cursor-pointer shadow-md">
                  <span>✕</span>
                  <span>Exit God's Eye</span>
                </button>
              </div>
            </header>

            <!-- Real-Life Satellite Feed Viewport (Fulfills Entire Screen) -->
            <div class="relative flex-1 w-full h-full overflow-hidden bg-black">
              <iframe id="godsEyeIframe" src="/zoom_earth_feed" class="w-full h-full border-0" allow="fullscreen; geolocation"></iframe>
              
              <!-- Subtle Tactical Recon HUD Over Map -->
              <div class="absolute top-4 left-4 pointer-events-none select-none z-20">
                <div class="font-mono text-[11px] text-cyan-300 bg-black/75 px-3 py-2 rounded-xl border border-cyan-500/40 backdrop-blur-md space-y-0.5 shadow-xl">
                  <p class="font-bold text-white flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                    <span>ORBITAL RECONNAISSANCE TARGET LOCK</span>
                  </p>
                  <p class="text-slate-300">Target: Cyclone BOB-04 Vortex Eye (16.82°N, 84.48°E)</p>
                  <p class="text-cyan-400 text-[10px]">Sensor: INSAT-3DR High-Res Multispectral Imager</p>
                </div>
              </div>

              <!-- Bottom Telemetry HUD -->
              <div class="absolute bottom-4 inset-x-4 pointer-events-none select-none z-20 flex justify-between items-end">
                <div class="font-mono text-[11px] text-slate-300 bg-black/75 px-3 py-2 rounded-xl border border-white/10 backdrop-blur-md shadow-xl">
                  <span>Landfall Target: <strong class="text-white">Gopalpur, Odisha</strong></span>
                  <span class="mx-2 text-slate-600">•</span>
                  <span>ETA: <strong class="text-red-400">~22.5 Hours</strong></span>
                </div>

                <div class="font-mono text-[10px] text-slate-400 bg-black/75 px-3 py-1.5 rounded-xl border border-white/10 backdrop-blur-md">
                  Use map pan & scroll to explore live cloud fronts • Double-click to zoom
                </div>
              </div>
            </div>
          </div>"""

new_html_block = """          <!-- FULLSCREEN REAL-LIFE LIVE SATELLITE FEED MAP (GOD'S EYE) -->
          <div id="godsEyeFullscreenFeed" class="hidden fixed inset-0 z-50 bg-[#030712] flex flex-col transition-opacity duration-700 opacity-0 pointer-events-none select-none font-sans">
            
            <!-- RECON SATELLITE MAP HEADER -->
            <header class="h-14 px-4 sm:px-6 bg-[#060b14]/95 backdrop-blur-xl border-b border-white/10 flex items-center justify-between z-30 shrink-0 select-none">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 rounded-lg bg-red-950/80 border border-red-500/60 flex items-center justify-center text-red-400 font-bold text-sm shadow-lg animate-pulse">
                  👁️
                </div>
                <div>
                  <div class="flex items-center space-x-2">
                    <span class="font-extrabold text-sm text-white tracking-wide font-heading">
                      GOD'S EYE
                    </span>
                    <span class="text-[10px] font-mono font-bold text-red-300 bg-red-950/80 border border-red-800 px-2 py-0.5 rounded">
                      ● LIVE SATELLITE FEED
                    </span>
                    <span class="text-[10px] font-mono text-slate-400 hidden sm:inline">
                      REALTIME ORBITAL COMPOSITE • BAY OF BENGAL
                    </span>
                  </div>
                </div>
              </div>

              <!-- Center: Feed Mode Toggles & Fast Targeting -->
              <div class="flex items-center space-x-2">
                <div class="flex items-center bg-[#070d1a] p-1 rounded-lg border border-white/10 text-xs font-mono">
                  <button onclick="setGodsEyeSource('satellite')" id="btn-gods-satellite" class="px-3 py-1 rounded font-bold transition-all bg-blue-600 text-white shadow cursor-pointer">
                    🛰️ HD Satellite Recon
                  </button>
                  <button onclick="toggleGodsEyeRadar()" id="btn-gods-radar" class="px-3 py-1 rounded font-bold transition-all bg-amber-600 text-white shadow cursor-pointer">
                    🌧️ Live Doppler Radar
                  </button>
                  <button onclick="setGodsEyeSource('scorpio')" id="btn-gods-scorpio" class="px-3 py-1 rounded font-bold transition-all text-slate-400 hover:text-white cursor-pointer">
                    📡 ISRO MOSDAC Scorpio
                  </button>
                </div>

                <div class="hidden xl:flex items-center space-x-1.5 text-[11px] font-mono">
                  <button onclick="focusGodsEyeTarget([16.82, 84.48], 7)" class="px-2.5 py-1 rounded bg-black/50 border border-red-500/40 text-red-300 hover:bg-red-950/60 transition cursor-pointer">🌀 BOB-04 Eye</button>
                  <button onclick="focusGodsEyeTarget([19.27, 84.91], 8)" class="px-2.5 py-1 rounded bg-black/50 border border-amber-500/40 text-amber-300 hover:bg-amber-950/60 transition cursor-pointer">📍 Landfall</button>
                  <button onclick="focusGodsEyeTarget([17.6868, 83.2185], 10)" class="px-2.5 py-1 rounded bg-black/50 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-950/60 transition cursor-pointer">📍 Vizag</button>
                </div>
              </div>

              <!-- Right: Telemetry & Exit -->
              <div class="flex items-center space-x-3 text-xs font-mono">
                <span class="text-emerald-400 hidden lg:inline font-bold">16.82°N, 84.48°E</span>
                <span class="text-slate-600 hidden lg:inline">|</span>
                <button onclick="exitGodsEye()" class="px-3.5 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 border border-red-500/60 text-white font-semibold transition-all flex items-center gap-1.5 cursor-pointer shadow-md">
                  <span>✕</span>
                  <span>Exit God's Eye</span>
                </button>
              </div>
            </header>

            <!-- Real-Life Satellite Feed Viewport (Fulfills Entire Screen) -->
            <div class="relative flex-1 w-full h-full overflow-hidden bg-[#030712]">
              <!-- High-Definition Embedded Leaflet Satellite Reconnaissance Map (Zero-Redirect, 60fps) -->
              <div id="godsEyeMapContainer" class="w-full h-full"></div>

              <!-- Sandboxed ISRO MOSDAC Scorpio Frame (No Top-Level Navigation Allowed) -->
              <iframe id="godsEyeScorpioFrame" class="hidden w-full h-full border-0" sandbox="allow-scripts allow-same-origin allow-forms" src="/scorpio_feed"></iframe>
              
              <!-- Tactical Recon HUD Over Map -->
              <div class="absolute top-4 left-4 pointer-events-none select-none z-20">
                <div class="font-mono text-[11px] text-cyan-300 bg-black/80 px-3.5 py-2.5 rounded-xl border border-cyan-500/40 backdrop-blur-md space-y-0.5 shadow-2xl">
                  <p class="font-bold text-white flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                    <span>ORBITAL RECONNAISSANCE TARGET LOCK</span>
                  </p>
                  <p class="text-slate-300">Target: Cyclone BOB-04 Vortex Eye (16.82°N, 84.48°E)</p>
                  <p class="text-cyan-400 text-[10px]">Sensor: INSAT-3DR Multispectral + ESRI World Imagery HD</p>
                </div>
              </div>

              <!-- Bottom Telemetry HUD -->
              <div class="absolute bottom-4 inset-x-4 pointer-events-none select-none z-20 flex justify-between items-end">
                <div class="font-mono text-[11px] text-slate-300 bg-black/80 px-4 py-2.5 rounded-xl border border-white/10 backdrop-blur-md shadow-2xl flex items-center gap-3">
                  <div>
                    <span class="text-slate-400">Landfall Target:</span> <strong class="text-white">Gopalpur, Odisha</strong>
                  </div>
                  <div class="h-3 w-px bg-slate-700"></div>
                  <div>
                    <span class="text-slate-400">Peak Winds:</span> <strong class="text-red-400">155 km/h (Cat 3 Equivalent)</strong>
                  </div>
                  <div class="h-3 w-px bg-slate-700 hidden sm:block"></div>
                  <div class="hidden sm:block">
                    <span class="text-slate-400">ETA:</span> <strong class="text-amber-400">~22.5 Hours</strong>
                  </div>
                </div>

                <div class="font-mono text-[10px] text-slate-400 bg-black/80 px-3.5 py-2 rounded-xl border border-white/10 backdrop-blur-md shadow-2xl">
                  Drag to pan • Scroll to zoom • Click storm eye for telemetry
                </div>
              </div>
            </div>
          </div>"""

if old_html_block in code:
    code = code.replace(old_html_block, new_html_block, 1)
    print("Replaced HTML block successfully.")
else:
    print("ERROR: old_html_block not found!")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("update_portal.py successfully rewritten.")
