import os
import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Ensure Google Fonts link includes Pixelify Sans and Silkscreen
if 'Pixelify+Sans' not in code:
    code = code.replace(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">',
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Pixelify+Sans:wght@400;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Silkscreen:wght@400;700&display=swap" rel="stylesheet">'
    )

# 2. Add pixel art and isometric CSS in <style>
pixel_css = """
    /* Taras Boiko iOS Weather Widgets (Pixel Art & Isometric 3D Design) */
    .font-pixel {
      font-family: 'Pixelify Sans', 'Silkscreen', monospace;
      image-rendering: pixelated;
    }

    .font-silkscreen {
      font-family: 'Silkscreen', monospace;
      image-rendering: pixelated;
    }

    .isometric-stage {
      perspective: 1600px;
      perspective-origin: 50% 35%;
    }

    .isometric-grid {
      transform: rotateX(20deg) rotateZ(-12deg) skewX(3deg);
      transform-style: preserve-3d;
      transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .isometric-grid.flat-view {
      transform: rotateX(0deg) rotateZ(0deg) skewX(0deg);
    }

    .pixel-widget-card {
      border-radius: 28px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 24px 44px -10px rgba(0, 0, 0, 0.8), inset 0 1px 1px rgba(255, 255, 255, 0.25);
      transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease, border-color 0.2s;
      transform-style: preserve-3d;
      border: 2px solid rgba(255, 255, 255, 0.12);
    }

    .pixel-widget-card:hover {
      transform: translateY(-14px) translateZ(28px) scale(1.04);
      box-shadow: 0 36px 64px -12px rgba(0, 0, 0, 0.95), 0 0 32px rgba(56, 189, 248, 0.3), inset 0 1px 1px rgba(255, 255, 255, 0.45);
      border-color: rgba(56, 189, 248, 0.6);
      z-index: 10;
    }

    /* Pixel Art Weather Background Textures */
    .pixel-bg-sunny {
      background: linear-gradient(180deg, #9a3412 0%, #7c2d12 45%, #431407 100%);
    }

    .pixel-bg-storm {
      background: linear-gradient(180deg, #0c202d 0%, #081720 50%, #03080d 100%);
    }

    .pixel-bg-rainy {
      background: linear-gradient(180deg, #132e3b 0%, #0d212b 50%, #050d12 100%);
    }

    .pixel-bg-swell {
      background: linear-gradient(180deg, #0c2b54 0%, #081d38 50%, #030b17 100%);
    }

    .pixel-bg-cold {
      background: linear-gradient(180deg, #1b2838 0%, #111a24 50%, #070a0f 100%);
    }

    .pixel-bg-wind {
      background: linear-gradient(180deg, #063d30 0%, #032b22 50%, #011410 100%);
    }

    /* Animated Pixel Rain */
    @keyframes pixelRainDrop {
      0% { transform: translateY(-20px) translateX(0); opacity: 0; }
      50% { opacity: 0.8; }
      100% { transform: translateY(120px) translateX(-25px); opacity: 0; }
    }
    .pixel-raindrop {
      position: absolute;
      width: 2px;
      height: 10px;
      background: #38bdf8;
      opacity: 0.6;
      animation: pixelRainDrop 1.1s linear infinite;
    }

    /* Animated Pixel Lightning Flash */
    @keyframes pixelLightningFlash {
      0%, 92%, 100% { opacity: 0; }
      93%, 95% { opacity: 0.9; }
      94% { opacity: 0.2; }
    }
    .pixel-lightning {
      animation: pixelLightningFlash 4.5s ease-in-out infinite;
    }
"""

if '.pixel-widget-card' not in code:
    code = code.replace(
        '  <style>',
        '  <style>' + pixel_css
    )

# 3. Add pixelWidgetView to state
if 'pixelWidgetView' not in code:
    code = code.replace(
        "activePortalView: 'portal',",
        "activePortalView: 'portal',\n      pixelWidgetView: 'isometric', // 'isometric' | 'flat'"
    )

# 4. Add JavaScript helper functions for pixel widgets
pixel_js = """
    // =========================================================================
    // PIXEL ART WEATHER WIDGET CONTROLLER (Taras Boiko Reference Edition)
    // =========================================================================
    function setPixelWidgetView(viewMode) {
      state.pixelWidgetView = viewMode;
      const grid = document.getElementById('pixelWidgetsGrid');
      if (grid) {
        if (viewMode === 'flat') {
          grid.classList.add('flat-view');
        } else {
          grid.classList.remove('flat-view');
        }
      }
      renderApp();
    }

    function selectPixelWeatherStation(stationId) {
      if (stationId === 'bob04') {
        jumpToZoomEarthLocation(16.82, 84.48, 'Cyclone BOB-04 Vortex');
      } else if (stationId === 'gopalpur') {
        jumpToZoomEarthLocation(19.26, 84.91, 'Gopalpur Coastal Landfall');
      } else if (stationId === 'bd08') {
        jumpToZoomEarthLocation(18.2, 89.7, 'INCOIS BD08 (North Bay)');
      } else if (stationId === 'puri') {
        jumpToZoomEarthLocation(19.81, 85.83, 'Puri Pilgrim Coast');
      } else if (stationId === 'insat') {
        jumpToZoomEarthLocation(0, 82.0, 'INSAT-3DR Geostationary');
      }
    }
"""

if 'function setPixelWidgetView' not in code:
    code = code.replace(
        '    // =========================================================================\n    // ZOOM EARTH LIVE SATELLITE CONTROLLER & TIMELINE ENGINE',
        pixel_js + '\n    // =========================================================================\n    // ZOOM EARTH LIVE SATELLITE CONTROLLER & TIMELINE ENGINE'
    )

# 5. Build the Pixel Art Weather Cards Component
render_pixel_widgets_fn = """
    // =========================================================================
    // RENDER TARAS BOIKO PIXEL-ART WEATHER & CYCLONE WIDGETS DECK
    // =========================================================================
    function renderPixelWeatherWidgetsDeck() {
      const isFlat = state.pixelWidgetView === 'flat';

      return `
        <!-- PIXEL-ART WEATHER & CYCLONE WIDGETS SHOWCASE SECTION -->
        <section class="max-w-7xl mx-auto px-4 sm:px-8 py-12 space-y-6">
          <!-- Section Header with Perspective Controls -->
          <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-[#1b2b45] pb-4">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">PIXEL ART TELEMETRY WIDGETS</span>
                <span class="text-slate-600">•</span>
                <span class="text-slate-400 font-mono text-xs">Crafted iOS Meteorological Array</span>
              </div>
              <h2 class="text-2xl sm:text-3xl font-bold font-heading text-white mt-1">
                Live Cyclonic Weather & Basin Impact Widgets
              </h2>
              <p class="text-xs text-slate-400 mt-1">
                Inspired by modern pixel art weather interfaces. Real-time telemetry from Bay of Bengal sensors, radar sweeps, and satellite sounders.
              </p>
            </div>

            <!-- 3D Perspective Toggle (Isometric vs Flat Grid) -->
            <div class="flex items-center gap-2 bg-[#090e1a]/90 border border-[#1d2b45] backdrop-blur-md p-1.5 rounded-xl font-mono text-xs shadow-xl">
              <button onclick="setPixelWidgetView('isometric')" class="px-3 py-1.5 rounded-lg ${!isFlat ? 'bg-amber-600 text-white font-bold shadow' : 'text-slate-400 hover:text-slate-200'} transition-all flex items-center gap-1.5">
                <span>📐</span>
                <span>Isometric 3D</span>
              </button>
              <button onclick="setPixelWidgetView('flat')" class="px-3 py-1.5 rounded-lg ${isFlat ? 'bg-amber-600 text-white font-bold shadow' : 'text-slate-400 hover:text-slate-200'} transition-all flex items-center gap-1.5">
                <span>▦</span>
                <span>Flat Grid</span>
              </button>
            </div>
          </div>

          <!-- Isometric 3D Viewport Stage -->
          <div class="isometric-stage py-6 sm:py-10 overflow-hidden">
            <div id="pixelWidgetsGrid" class="isometric-grid ${isFlat ? 'flat-view' : ''} grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto px-4">
              
              <!-- CARD 1: SUNNY / PRE-STORM COASTAL HEAT -->
              <div onclick="selectPixelWeatherStation('puri')" class="pixel-widget-card pixel-bg-sunny p-6 h-[270px] flex flex-col justify-between cursor-pointer group">
                <!-- Pixel Art Mountain & Sun Backdrop Layer -->
                <div class="absolute inset-0 pointer-events-none opacity-40 overflow-hidden">
                  <!-- Pixel Sun -->
                  <div class="absolute top-6 right-6 w-14 h-14 bg-amber-200 rounded-full blur-[1px] shadow-[0_0_20px_#f59e0b]"></div>
                  <!-- Pixel Hill Silhouette 1 -->
                  <svg class="absolute bottom-0 inset-x-0 w-full h-24" viewBox="0 0 100 40" preserveAspectRatio="none">
                    <polygon points="0,40 15,22 35,30 55,18 75,25 100,12 100,40" fill="#431407" opacity="0.6"/>
                    <polygon points="0,40 25,28 45,35 65,22 85,32 100,20 100,40" fill="#290d04" opacity="0.9"/>
                  </svg>
                </div>

                <!-- Top: Big Pixel Temperature & Icon -->
                <div class="relative z-10 space-y-1">
                  <div class="flex items-start justify-between">
                    <div class="font-pixel text-5xl sm:text-6xl font-black text-white tracking-wider drop-shadow-md">
                      31°
                    </div>
                    <span class="text-[10px] font-mono font-bold bg-amber-950/80 text-amber-200 border border-amber-700/60 px-2 py-0.5 rounded-full">
                      PURI COAST
                    </span>
                  </div>
                  <!-- Condition Row -->
                  <div class="flex items-center space-x-2 text-amber-100 font-pixel text-base font-bold">
                    <span class="text-lg">☼</span>
                    <span>Sunny (Pre-Squall)</span>
                  </div>
                </div>

                <!-- Bottom: 3-Day Forecast Row -->
                <div class="relative z-10 pt-3 border-t border-amber-600/30 flex items-center justify-between text-xs font-pixel text-amber-200/90">
                  <div class="text-center">
                    <p class="text-[10px] text-amber-300/70">WED</p>
                    <p class="font-bold text-sm">31°</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-amber-300/70">THU</p>
                    <p class="font-bold text-sm text-red-200">27° ⚡</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-amber-300/70">FRI</p>
                    <p class="font-bold text-sm">28° 🌧</p>
                  </div>
                </div>
              </div>

              <!-- CARD 2: STORM / CYCLONE BOB-04 VORTEX CORE -->
              <div onclick="selectPixelWeatherStation('bob04')" class="pixel-widget-card pixel-bg-storm p-6 h-[270px] flex flex-col justify-between cursor-pointer group border-2 border-red-500/40">
                <!-- Pixel Art Storm Clouds & Lightning Layer -->
                <div class="absolute inset-0 pointer-events-none opacity-50 overflow-hidden">
                  <!-- Pixel Lightning Bolt -->
                  <svg class="pixel-lightning absolute top-4 right-10 w-12 h-20 text-yellow-300" viewBox="0 0 24 36" fill="currentColor">
                    <polygon points="12,0 0,18 10,18 6,36 22,14 12,14"/>
                  </svg>
                  <!-- Pixel Tempest Clouds -->
                  <div class="absolute -top-6 -left-6 w-32 h-24 bg-slate-700/60 rounded-full blur-[2px]"></div>
                  <div class="absolute top-2 right-2 w-36 h-28 bg-slate-800/80 rounded-full blur-[2px]"></div>
                </div>

                <!-- Top: Big Pixel Wind Velocity & Storm Label -->
                <div class="relative z-10 space-y-1">
                  <div class="flex items-start justify-between">
                    <div class="font-pixel text-4xl sm:text-5xl font-black text-red-400 tracking-wider drop-shadow-md">
                      155<span class="text-2xl text-slate-300">k</span>
                    </div>
                    <span class="text-[10px] font-mono font-bold bg-red-950 text-red-300 border border-red-700 px-2 py-0.5 rounded-full animate-pulse">
                      ● CAT-3 VSCS
                    </span>
                  </div>
                  <!-- Condition Row -->
                  <div class="flex items-center space-x-2 text-red-200 font-pixel text-base font-bold">
                    <span class="text-lg">⚡</span>
                    <span>Storm (BOB-04)</span>
                  </div>
                </div>

                <!-- Bottom: 3-Day Forecast Row -->
                <div class="relative z-10 pt-3 border-t border-slate-700/50 flex items-center justify-between text-xs font-pixel text-slate-300">
                  <div class="text-center">
                    <p class="text-[10px] text-slate-400">WED</p>
                    <p class="font-bold text-sm text-red-400">160k</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-slate-400">THU</p>
                    <p class="font-bold text-sm text-red-500 font-black">175k !</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-slate-400">FRI</p>
                    <p class="font-bold text-sm text-amber-300">85k</p>
                  </div>
                </div>
              </div>

              <!-- CARD 3: HEAVY RAIN / LANDFALL INUNDATION -->
              <div onclick="selectPixelWeatherStation('gopalpur')" class="pixel-widget-card pixel-bg-rainy p-6 h-[270px] flex flex-col justify-between cursor-pointer group">
                <!-- Pixel Raindrops & City Skyline Layer -->
                <div class="absolute inset-0 pointer-events-none overflow-hidden">
                  <span class="pixel-raindrop" style="left: 20%; animation-delay: 0.1s;"></span>
                  <span class="pixel-raindrop" style="left: 45%; animation-delay: 0.4s;"></span>
                  <span class="pixel-raindrop" style="left: 70%; animation-delay: 0.2s;"></span>
                  <span class="pixel-raindrop" style="left: 85%; animation-delay: 0.6s;"></span>
                  <!-- Pixel Coastal Skyline -->
                  <svg class="absolute bottom-0 inset-x-0 w-full h-16" viewBox="0 0 100 30" preserveAspectRatio="none">
                    <rect x="5" y="10" width="8" height="20" fill="#050d12" opacity="0.8"/>
                    <rect x="18" y="5" width="12" height="25" fill="#050d12" opacity="0.9"/>
                    <rect x="35" y="12" width="7" height="18" fill="#050d12" opacity="0.7"/>
                    <rect x="50" y="8" width="14" height="22" fill="#050d12" opacity="0.9"/>
                    <rect x="72" y="14" width="9" height="16" fill="#050d12" opacity="0.8"/>
                    <rect x="85" y="4" width="10" height="26" fill="#050d12" opacity="0.9"/>
                  </svg>
                </div>

                <!-- Top: Big Pixel Temperature & Icon -->
                <div class="relative z-10 space-y-1">
                  <div class="flex items-start justify-between">
                    <div class="font-pixel text-5xl sm:text-6xl font-black text-cyan-300 tracking-wider drop-shadow-md">
                      29°
                    </div>
                    <span class="text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-300 border border-cyan-800 px-2 py-0.5 rounded-full">
                      GOPALPUR
                    </span>
                  </div>
                  <!-- Condition Row -->
                  <div class="flex items-center space-x-2 text-cyan-100 font-pixel text-base font-bold">
                    <span class="text-lg">🌧</span>
                    <span>Rainy (280mm Peak)</span>
                  </div>
                </div>

                <!-- Bottom: 3-Day Forecast Row -->
                <div class="relative z-10 pt-3 border-t border-cyan-800/40 flex items-center justify-between text-xs font-pixel text-cyan-200">
                  <div class="text-center">
                    <p class="text-[10px] text-cyan-400/70">WED</p>
                    <p class="font-bold text-sm">29°</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-cyan-400/70">THU</p>
                    <p class="font-bold text-sm text-white">25° 🌧</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-cyan-400/70">FRI</p>
                    <p class="font-bold text-sm">26°</p>
                  </div>
                </div>
              </div>

              <!-- CARD 4: OCEAN SWELL / INCOIS BUOY BD08 -->
              <div onclick="selectPixelWeatherStation('bd08')" class="pixel-widget-card pixel-bg-swell p-6 h-[270px] flex flex-col justify-between cursor-pointer group">
                <!-- Pixel Wave Layers -->
                <div class="absolute inset-0 pointer-events-none opacity-45 overflow-hidden">
                  <svg class="absolute bottom-0 inset-x-0 w-full h-24" viewBox="0 0 100 40" preserveAspectRatio="none">
                    <path d="M0,30 Q25,15 50,30 T100,30 L100,40 L0,40 Z" fill="#081d38"/>
                    <path d="M0,35 Q20,22 40,35 T80,35 T100,35 L100,40 L0,40 Z" fill="#030b17"/>
                  </svg>
                </div>

                <!-- Top: Wave Height & Label -->
                <div class="relative z-10 space-y-1">
                  <div class="flex items-start justify-between">
                    <div class="font-pixel text-5xl sm:text-6xl font-black text-blue-300 tracking-wider drop-shadow-md">
                      7.2<span class="text-2xl text-slate-400">m</span>
                    </div>
                    <span class="text-[10px] font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded-full">
                      BUOY BD08
                    </span>
                  </div>
                  <!-- Condition Row -->
                  <div class="flex items-center space-x-2 text-blue-100 font-pixel text-base font-bold">
                    <span class="text-lg">🌊</span>
                    <span>Swell (High Hazard)</span>
                  </div>
                </div>

                <!-- Bottom: 3-Day Forecast Row -->
                <div class="relative z-10 pt-3 border-t border-blue-800/40 flex items-center justify-between text-xs font-pixel text-blue-200">
                  <div class="text-center">
                    <p class="text-[10px] text-blue-400/70">WED</p>
                    <p class="font-bold text-sm">5.8m</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-blue-400/70">THU</p>
                    <p class="font-bold text-sm text-red-300 font-bold">7.2m</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-blue-400/70">FRI</p>
                    <p class="font-bold text-sm">3.4m</p>
                  </div>
                </div>
              </div>

              <!-- CARD 5: COLD CLOUD TOPS / SOUNDER TIR (-78°C) -->
              <div onclick="selectPixelWeatherStation('insat')" class="pixel-widget-card pixel-bg-cold p-6 h-[270px] flex flex-col justify-between cursor-pointer group">
                <!-- Pixel Frost Cloud Flakes -->
                <div class="absolute inset-0 pointer-events-none opacity-40 overflow-hidden">
                  <div class="absolute top-8 left-8 w-2 h-2 bg-blue-200"></div>
                  <div class="absolute top-14 right-14 w-2 h-2 bg-blue-300"></div>
                  <div class="absolute bottom-12 left-24 w-2 h-2 bg-white"></div>
                  <div class="absolute bottom-16 right-8 w-3 h-3 bg-blue-200"></div>
                </div>

                <!-- Top: Infrared Temperature -->
                <div class="relative z-10 space-y-1">
                  <div class="flex items-start justify-between">
                    <div class="font-pixel text-5xl sm:text-6xl font-black text-indigo-200 tracking-wider drop-shadow-md">
                      -78°
                    </div>
                    <span class="text-[10px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded-full">
                      INSAT-3DR TIR
                    </span>
                  </div>
                  <!-- Condition Row -->
                  <div class="flex items-center space-x-2 text-indigo-100 font-pixel text-base font-bold">
                    <span class="text-lg">❄</span>
                    <span>Cold Core (Deep CDO)</span>
                  </div>
                </div>

                <!-- Bottom: Channel Profiles -->
                <div class="relative z-10 pt-3 border-t border-indigo-800/40 flex items-center justify-between text-xs font-pixel text-indigo-200">
                  <div class="text-center">
                    <p class="text-[10px] text-indigo-400/70">TIR-1</p>
                    <p class="font-bold text-sm">-78°C</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-indigo-400/70">WV</p>
                    <p class="font-bold text-sm">-62°C</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-indigo-400/70">MIR</p>
                    <p class="font-bold text-sm">-54°C</p>
                  </div>
                </div>
              </div>

              <!-- CARD 6: GALE WIND FIELDS / EOS-06 SCAT -->
              <div onclick="selectPixelWeatherStation('bob04')" class="pixel-widget-card pixel-bg-wind p-6 h-[270px] flex flex-col justify-between cursor-pointer group">
                <!-- Pixel Vector Wind Streamlines -->
                <div class="absolute inset-0 pointer-events-none opacity-40 overflow-hidden">
                  <div class="absolute top-10 left-4 w-36 h-0.5 bg-emerald-300"></div>
                  <div class="absolute top-14 left-16 w-28 h-0.5 bg-emerald-400"></div>
                  <div class="absolute top-24 left-8 w-44 h-0.5 bg-emerald-300"></div>
                  <div class="absolute bottom-12 left-12 w-32 h-0.5 bg-emerald-200"></div>
                </div>

                <!-- Top: Wind Vectors -->
                <div class="relative z-10 space-y-1">
                  <div class="flex items-start justify-between">
                    <div class="font-pixel text-5xl sm:text-6xl font-black text-emerald-300 tracking-wider drop-shadow-md">
                      148<span class="text-2xl text-slate-400">k</span>
                    </div>
                    <span class="text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded-full">
                      EOS-06 SCAT
                    </span>
                  </div>
                  <!-- Condition Row -->
                  <div class="flex items-center space-x-2 text-emerald-100 font-pixel text-base font-bold">
                    <span class="text-lg">💨</span>
                    <span>Gale Wind Vector</span>
                  </div>
                </div>

                <!-- Bottom: 3-Day Forecast Row -->
                <div class="relative z-10 pt-3 border-t border-emerald-800/40 flex items-center justify-between text-xs font-pixel text-emerald-200">
                  <div class="text-center">
                    <p class="text-[10px] text-emerald-400/70">WED</p>
                    <p class="font-bold text-sm">130k</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-emerald-400/70">THU</p>
                    <p class="font-bold text-sm text-red-300 font-bold">155k</p>
                  </div>
                  <div class="text-center">
                    <p class="text-[10px] text-emerald-400/70">FRI</p>
                    <p class="font-bold text-sm">90k</p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </section>
      `;
    }
"""

if 'function renderPixelWeatherWidgetsDeck' not in code:
    code = code.replace(
        '    // =========================================================================\n    // ZOOM EARTH FLOATING GLASSMORPHISM CONTROLS',
        render_pixel_widgets_fn + '\n    // =========================================================================\n    // ZOOM EARTH FLOATING GLASSMORPHISM CONTROLS'
    )

# 6. Insert renderPixelWeatherWidgetsDeck() into renderNasaPortal() right after the Hero Section
if '${renderPixelWeatherWidgetsDeck()}' not in code:
    code = code.replace(
        '          <!-- 3.4. DEDICATED ZOOM EARTH HIGH-DEFINITION SATELLITE OBSERVATORY -->',
        '          ${renderPixelWeatherWidgetsDeck()}\n\n          <!-- 3.4. DEDICATED ZOOM EARTH HIGH-DEFINITION SATELLITE OBSERVATORY -->'
    )

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully injected Taras Boiko iOS Weather Widgets into update_portal.py!")
