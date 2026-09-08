import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update CSS for login-split-card and login-left-curved to match preface theme
old_css_needle = """    /* Split Card Styling (Matching Pic 2) */
    .login-split-card {
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.2);
    }
    @media (min-width: 768px) {
      .login-left-curved {
        border-top-right-radius: 120px 50%;
        border-bottom-right-radius: 120px 50%;
        box-shadow: 15px 0 30px -5px rgba(0, 0, 0, 0.25);
        z-index: 10;
      }
    }
    @media (max-width: 767px) {
      .login-left-curved {
        border-bottom-left-radius: 36px;
        border-bottom-right-radius: 36px;
      }
    }"""

new_css = """    /* Split Card Styling Harmonized with Preface Color Theme & Pic 2 Layout */
    .login-split-card {
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.85), 0 0 40px rgba(14, 165, 233, 0.18), 0 0 0 1px rgba(56, 189, 248, 0.25);
    }
    @media (min-width: 768px) {
      .login-left-curved {
        border-top-right-radius: 120px 50%;
        border-bottom-right-radius: 120px 50%;
        box-shadow: 14px 0 30px -4px rgba(2, 132, 199, 0.35);
        z-index: 10;
      }
    }
    @media (max-width: 767px) {
      .login-left-curved {
        border-bottom-left-radius: 36px;
        border-bottom-right-radius: 36px;
      }
    }"""

if old_css_needle in code:
    code = code.replace(old_css_needle, new_css, 1)
    print("Updated login split card CSS to preface theme.")
else:
    print("Could not find old_css_needle directly; checking regex.")
    code = re.sub(r"/\* Split Card Styling.*?\n    }", new_css, code, flags=re.DOTALL)
    print("Replaced CSS via regex.")

# 2. Update openLoginModal and closeLoginModal to swoop Earth forward and rotate
login_functions_needle = """    function openLoginModal() {
      const m = document.getElementById('officerLoginModal');
      if (m) {
        m.classList.remove('hidden');
        try { window.location.hash = 'login'; } catch(e) {}
      } else {
        setState({ activePortalView: 'login' });
      }
    }

    function closeLoginModal() {
      const m = document.getElementById('officerLoginModal');
      if (m) {
        m.classList.add('hidden');
        try {
          if (window.location.hash === '#login') {
            history.pushState("", document.title, window.location.pathname + window.location.search);
          }
        } catch(e) {}
      } else {
        setState({ activePortalView: 'portal' });
      }
    }"""

new_login_functions = """    let isLoginOpen = false;

    function openLoginModal() {
      isLoginOpen = true;
      const hero = document.getElementById('heroGlobeSection');
      const textCard = document.getElementById('heroTextCard');
      const heroDock = document.getElementById('heroDock');
      const inst = activeGlobeInstances['prefaceInteractiveGlobe'];
      const m = document.getElementById('officerLoginModal');

      // 1. Expand Hero Globe Section to fullscreen behind the modal
      if (hero) {
        hero.classList.remove('relative', 'min-h-[640px]', 'lg:min-h-[700px]');
        hero.classList.add('fixed', 'inset-0', 'z-40', 'w-screen', 'h-screen');
      }
      if (textCard) {
        textCard.classList.add('opacity-0', 'pointer-events-none', '-translate-y-8', 'scale-95');
      }
      if (heroDock) {
        heroDock.classList.add('opacity-0', 'pointer-events-none');
      }
      document.body.style.overflow = 'hidden';

      // 2. Swoop 3D Earth camera forward and rotate towards viewer (coming in front!)
      if (inst) {
        inst.setTargetRotation(0.28, Math.PI * 0.965, 1.46);
        const start = performance.now();
        function smoothResize() {
          if (inst && inst.camera && inst.renderer) {
            const w = window.innerWidth;
            const h = window.innerHeight;
            inst.camera.aspect = w / h;
            inst.camera.updateProjectionMatrix();
            inst.renderer.setSize(w, h);
          }
          if (performance.now() - start < 2000) {
            requestAnimationFrame(smoothResize);
          }
        }
        requestAnimationFrame(smoothResize);
      }

      // 3. Reveal the translucent login modal floating smoothly over the rotating 3D Earth
      if (m) {
        m.classList.remove('hidden');
        void m.offsetWidth;
        m.classList.remove('opacity-0', 'pointer-events-none');
        m.classList.add('opacity-100', 'pointer-events-auto');
        try { window.location.hash = 'login'; } catch(e) {}
      } else {
        setState({ activePortalView: 'login' });
      }
    }

    function closeLoginModal() {
      isLoginOpen = false;
      const m = document.getElementById('officerLoginModal');
      if (m) {
        m.classList.remove('opacity-100', 'pointer-events-auto');
        m.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { m.classList.add('hidden'); }, 300);
        try {
          if (window.location.hash === '#login') {
            history.pushState("", document.title, window.location.pathname + window.location.search);
          }
        } catch(e) {}
      } else {
        setState({ activePortalView: 'portal' });
      }

      // If tactical deck is not open, smoothly restore hero section and zoom Earth back to normal orbit
      if (!isTacticalExpanded) {
        const hero = document.getElementById('heroGlobeSection');
        const textCard = document.getElementById('heroTextCard');
        const heroDock = document.getElementById('heroDock');
        const inst = activeGlobeInstances['prefaceInteractiveGlobe'];

        if (hero) {
          hero.classList.remove('fixed', 'inset-0', 'z-40', 'w-screen', 'h-screen');
          hero.classList.add('relative', 'min-h-[640px]', 'lg:min-h-[700px]');
        }
        if (textCard) {
          textCard.classList.remove('opacity-0', 'pointer-events-none', '-translate-y-8', 'scale-95');
        }
        if (heroDock) {
          heroDock.classList.remove('opacity-0', 'pointer-events-none');
        }
        document.body.style.overflow = '';

        if (inst) {
          inst.setTargetRotation(0.35, Math.PI * 0.98, 2.45);
          const start = performance.now();
          function smoothResizeBack() {
            if (inst && inst.camera && inst.renderer) {
              const w = hero ? hero.clientWidth : window.innerWidth;
              const h = hero ? hero.clientHeight : 700;
              inst.camera.aspect = w / h;
              inst.camera.updateProjectionMatrix();
              inst.renderer.setSize(w, h);
            }
            if (performance.now() - start < 1800) {
              requestAnimationFrame(smoothResizeBack);
            }
          }
          requestAnimationFrame(smoothResizeBack);
        }
      }
    }"""

if login_functions_needle in code:
    code = code.replace(login_functions_needle, new_login_functions, 1)
    print("Updated openLoginModal / closeLoginModal with 3D Earth swooping and rotation.")
else:
    print("ERROR: Could not locate login_functions_needle!")

# 3. Redesign the login card HTML to match the preface page dark aerospace palette
pic2_preface_card_html = """
          <!-- Outer Card Split into 2 Panels (Matching Pic 2 & Harmonized with Preface Dark Theme) -->
          <div class="relative w-full max-w-4xl bg-[#060b16]/95 backdrop-blur-2xl rounded-3xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85),0_0_40px_rgba(14,165,233,0.18)] overflow-hidden flex flex-col md:flex-row border border-cyan-500/30 login-split-card">
            
            <!-- Close Button (Top Right of Card) -->
            <button onclick="closeLoginModal()" class="absolute top-4 right-4 z-30 text-cyan-200/70 hover:text-white p-2 rounded-full bg-slate-900/60 hover:bg-slate-800 border border-cyan-500/20 text-xs transition-all cursor-pointer" title="Return to Portal">
              ✕
            </button>

            <!-- LEFT PANEL: Frosted Deep Space Glass Curved Brand Section with CHAKRAVYOOH Logo & Name -->
            <div class="w-full md:w-[48%] bg-gradient-to-br from-[#0c182e]/95 via-[#0f203d]/90 to-[#070e1c]/95 backdrop-blur-xl flex flex-col items-center justify-center p-8 sm:p-12 relative login-left-curved shrink-0 text-center select-none border-r border-cyan-500/20">
              
              <!-- Circular Cyber Vortex Cyclone Logo (Chakravyooh Mesh Formation) -->
              <div class="relative flex items-center justify-center my-3">
                <svg width="140" height="140" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="drop-shadow-[0_0_15px_rgba(14,165,233,0.4)]">
                  <!-- Concentric Orbital Guides -->
                  <circle cx="50" cy="50" r="45" stroke="#0ea5e9" stroke-width="1.2" stroke-dasharray="3 3" opacity="0.4"/>
                  <circle cx="50" cy="50" r="32" stroke="#38bdf8" stroke-width="1" stroke-dasharray="4 2" opacity="0.3"/>

                  <!-- Outer Swirling Nodes & Conduits (Chakravyooh Cyber Vortex Formation from Pic 2) -->
                  <path d="M50 16 C68 16 82 28 82 48 C82 58 75 70 60 74" stroke="#0ea5e9" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="50" cy="16" r="5.5" fill="#38bdf8"/>
                  <circle cx="82" cy="48" r="5" fill="#0284c7"/>
                  <circle cx="60" cy="74" r="4.5" fill="#38bdf8"/>

                  <path d="M82 72 C74 84 56 90 38 84 C26 80 18 66 18 52" stroke="#0284c7" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="82" cy="72" r="5.5" fill="#0284c7"/>
                  <circle cx="38" cy="84" r="5" fill="#38bdf8"/>
                  <circle cx="18" cy="52" r="4.5" fill="#0ea5e9"/>

                  <path d="M18 38 C22 24 38 14 56 18 C66 20 74 28 76 40" stroke="#38bdf8" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="18" cy="38" r="5.5" fill="#38bdf8"/>
                  <circle cx="56" cy="18" r="5" fill="#0ea5e9"/>

                  <!-- Center Eye Core -->
                  <circle cx="50" cy="50" r="8" fill="#070d1a" stroke="#0ea5e9" stroke-width="1.5"/>
                  <circle cx="50" cy="50" r="4" fill="#38bdf8"/>
                </svg>
              </div>

              <!-- Brand Name & Tagline (Matching Pic 2 Layout & Preface Typography) -->
              <div class="mt-4 space-y-1.5 w-full">
                <h1 class="text-3xl sm:text-4xl font-black tracking-wider text-white uppercase font-sans drop-shadow-md">
                  CHAKRAVYOOH
                </h1>
                <div class="flex items-center justify-center gap-2 max-w-[220px] mx-auto">
                  <div class="h-0.5 flex-1 bg-gradient-to-r from-transparent to-cyan-400"></div>
                  <span class="text-[11px] font-bold text-cyan-300 tracking-wider uppercase font-mono">OPERATIONS</span>
                  <div class="h-0.5 flex-1 bg-gradient-to-l from-transparent to-cyan-400"></div>
                </div>
                <p class="text-[10px] font-mono tracking-widest font-semibold text-cyan-200/70 uppercase pt-1">
                  NATIONAL DISASTER RESILIENCE MESH
                </p>
              </div>
            </div>

            <!-- RIGHT PANEL: Deep Space Navy Authentication Form (Matching Pic 2 in Preface Theme) -->
            <div class="w-full md:w-[52%] bg-[#060b16]/95 backdrop-blur-xl p-7 sm:p-10 flex flex-col justify-center space-y-4 text-white relative">
              
              <form onsubmit="handleFormLogin(event);" class="space-y-4 max-w-sm mx-auto w-full">
                
                <!-- Role & Position Selector Button (As requested: "role button should be there to select roles and positions") -->
                <div>
                  <label class="block text-cyan-200 font-semibold text-xs sm:text-sm mb-1.5 tracking-wide font-sans">
                    Role & Position
                  </label>
                  <div class="relative flex items-center">
                    <div class="absolute left-3 w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                      🎖️
                    </div>
                    <select id="loginRoleSelect" onchange="state.loginRole = this.value;" class="w-full pl-11 pr-9 py-2.5 rounded-full bg-[#0b1b36] hover:bg-[#0f244a] text-cyan-100 font-medium text-xs sm:text-sm border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 appearance-none cursor-pointer transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]">
                      <option value="ndrf">NDRF — Field Incident Commander</option>
                      <option value="imd">IMD — Chief Meteorologist & Radar Lead</option>
                      <option value="district">SDMA — District Magistrate (Evacuation Controller)</option>
                      <option value="coastguard">Coast Guard — Marine SAR Commander</option>
                      <option value="mesh">Emergency Mesh & Radio Ops Specialist</option>
                      <option value="guest">Public Observer & Research Evaluator</option>
                    </select>
                    <span class="absolute right-4 text-cyan-300 pointer-events-none text-xs">▼</span>
                  </div>
                </div>

                <!-- Username Input (Empty by default, No predefined data, Preface-harmonized cyan pill) -->
                <div>
                  <label class="block text-cyan-200 font-semibold text-xs sm:text-sm mb-1.5 tracking-wide font-sans">
                    Username
                  </label>
                  <div class="relative flex items-center">
                    <div class="absolute left-2.5 w-7 h-7 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                      👤
                    </div>
                    <input type="text" id="loginEmailInput" value="" autocomplete="off" class="w-full pl-11 pr-4 py-2.5 rounded-full bg-[#0b1b36] text-white placeholder-cyan-300/40 font-medium text-xs sm:text-sm border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]" placeholder="Enter username / officer ID" required />
                  </div>
                </div>

                <!-- Password Input (Empty by default, No predefined data, Preface-harmonized cyan pill) -->
                <div>
                  <label class="block text-cyan-200 font-semibold text-xs sm:text-sm mb-1.5 tracking-wide font-sans">
                    Password
                  </label>
                  <div class="relative flex items-center">
                    <div class="absolute left-2.5 w-7 h-7 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                      🔒
                    </div>
                    <input type="password" id="loginPassInput" value="" autocomplete="off" class="w-full pl-11 pr-4 py-2.5 rounded-full bg-[#0b1b36] text-white placeholder-cyan-300/40 font-medium text-xs sm:text-sm border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]" placeholder="Enter password" required />
                  </div>
                </div>

                <!-- Remember Me Checkbox (Matching Pic 2) -->
                <div class="flex items-center text-xs text-cyan-200/80 pt-0.5">
                  <label class="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" id="loginRememberMe" class="w-4 h-4 rounded border-cyan-500 bg-transparent text-cyan-400 focus:ring-0 cursor-pointer" />
                    <span class="text-xs">Remember Me</span>
                  </label>
                </div>

                <!-- Centered Glowing Login Button (Matching Pic 2 & Preface theme) -->
                <div class="pt-2 flex flex-col items-center">
                  <button type="submit" class="w-36 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 active:scale-95 text-white font-bold text-sm tracking-wide shadow-[0_8px_25px_rgba(14,165,233,0.4)] border border-cyan-300/30 transition-all cursor-pointer">
                    Login
                  </button>
                </div>

                <!-- Forgot Password? Link (Matching Pic 2) -->
                <div class="text-center pt-1">
                  <a href="javascript:void(0)" onclick="alert('Password reset instructions dispatched to your registered operational security terminal.')" class="text-cyan-400/80 hover:text-cyan-200 transition-colors text-xs font-medium">
                    Forgot Password?
                  </a>
                </div>

                <!-- Bottom Auxiliary Buttons (Matching Pic 2: How To Login, Request Login, ✕ Return) -->
                <div class="flex items-center justify-center gap-2 pt-3.5 border-t border-cyan-500/20 text-xs">
                  <button type="button" onclick="alert('CHAKRAVYOOH LOGIN GUIDE:\\n\\n1. Select your operational agency Role & Position (NDRF, IMD, SDMA, Coast Guard, or Mesh Ops).\\n2. Input your authorized service username/badge and password.\\n3. Click Login to enter the Real-Time Tactical Command Center.')" class="px-3 py-1.5 rounded-md bg-[#0b1b36] hover:bg-[#13284d] text-cyan-300 border border-cyan-500/30 text-[11px] font-semibold transition-all cursor-pointer shadow-sm">
                    How To Login
                  </button>
                  <button type="button" onclick="alert('ACCESS REQUEST:\\n\\nOfficial clearance request forwarded to National Disaster Response Force Command Cell & IMD Operations Directorate. Guest evaluator access granted immediately.')" class="px-3 py-1.5 rounded-md bg-[#0b1b36] hover:bg-[#13284d] text-cyan-300 border border-cyan-500/30 text-[11px] font-semibold transition-all cursor-pointer shadow-sm">
                    Request Login
                  </button>
                  <button type="button" onclick="closeLoginModal()" class="px-3 py-1.5 rounded-md bg-slate-900/90 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700/50 text-[11px] font-medium transition-all cursor-pointer">
                    ✕ Return
                  </button>
                </div>
              </form>
            </div>
          </div>
"""

# Replace renderOfficerLoginModal with the translucent floating overlay that reveals the 3D globe behind it
new_officer_modal = f"""    function renderOfficerLoginModal() {{
      return `
        <div id="officerLoginModal" class="fixed inset-0 z-50 hidden opacity-0 pointer-events-none transition-all duration-500 ease-out flex items-center justify-center bg-slate-950/45 backdrop-blur-sm p-4 sm:p-8 select-none font-sans overflow-y-auto">
{pic2_preface_card_html}
        </div>
      `;
    }}
"""

new_login_page = f"""    function renderLoginPage() {{
      return `
        <div class="min-h-screen text-slate-100 flex flex-col font-sans select-none bg-[#03060f] relative overflow-hidden">
          <!-- 100% Native WebGL Photorealistic NASA 3D Earth in dedicated view -->
          <div id="loginDedicatedGlobe" class="absolute inset-0 w-full h-full pointer-events-none z-0"></div>
          <div class="absolute inset-0 bg-slate-950/40 backdrop-blur-sm z-[1]"></div>

          <!-- Top Strip -->
          <div class="relative z-10 bg-[#070c18]/90 px-4 py-2 text-[11px] font-mono text-slate-300 flex items-center justify-between border-b border-[#142033]">
            <div class="flex items-center space-x-2">
              <span>🇮🇳</span>
              <span class="font-bold text-white">GOVERNMENT OF INDIA</span>
              <span class="text-blue-400">•</span>
              <span onclick="setState({{ activePortalView: 'portal' }}); window.scrollTo({{ top: 0, behavior: 'smooth' }});" class="text-cyan-400 font-bold cursor-pointer hover:underline">CHAKRAVYOOH SECURE GATEWAY</span>
            </div>
            <button onclick="setState({{ activePortalView: 'portal' }}); window.scrollTo({{ top: 0, behavior: 'smooth' }});" class="text-slate-300 hover:text-white flex items-center gap-1 transition-colors">
              <span>←</span>
              <span>Back to Launch Page</span>
            </button>
          </div>

          <!-- Main Page Center Container (Pic 2 Split Card floating over rotating Earth) -->
          <div class="relative z-10 flex-1 flex items-center justify-center p-4 sm:p-8 w-full">
{pic2_preface_card_html}
          </div>
        </div>
      `;
    }}
"""

# Find bounds of renderOfficerLoginModal and renderLoginPage
m_start = "    function renderOfficerLoginModal() {"
p_start = "    function renderLoginPage() {"
app_start = "    function renderApp() {"

idx_m = code.find(m_start)
idx_p = code.find(p_start)
idx_app = code.find(app_start)

if idx_m != -1 and idx_p != -1 and idx_app != -1:
    code = code[:idx_m] + new_officer_modal + "\n" + new_login_page + "\n" + code[idx_app:]
    print("Replaced renderOfficerLoginModal and renderLoginPage with Preface-harmonized Split Card.")
else:
    print(f"ERROR: Could not find modal bounds: idx_m={idx_m}, idx_p={idx_p}, idx_app={idx_app}")
    exit(1)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py with live globe background and preface theme.")
