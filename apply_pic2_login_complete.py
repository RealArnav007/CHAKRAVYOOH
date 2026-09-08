import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add CSS for login-left-curved and login-split-card if not present
login_css = """    /* Split Card Styling (Matching Pic 2) */
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
    }
"""

if ".login-left-curved" not in code:
    code = code.replace("  <style>", "  <style>\n" + login_css, 1)
    print("Added login split card CSS.")

# 2. Reset predefined login credentials in state
old_state_creds = """      // Login Credentials & Preset State
      loginRole: 'ndrf',
      loginBadge: 'IMD-NDRF-882',
      loginEmail: 'a.kumar@ndrf.gov.in',
      loginPass: '••••••••••••',
      login2fa: '482-910',
      loginNotice: '',"""

new_state_creds = """      // Login Credentials & Preset State (No Predefined Data)
      loginRole: 'ndrf',
      loginBadge: '',
      loginEmail: '',
      loginPass: '',
      login2fa: '',
      loginNotice: '',"""

if old_state_creds in code:
    code = code.replace(old_state_creds, new_state_creds, 1)
    print("Cleared predefined login credentials in state.")
else:
    print("Note: old_state_creds not found directly; searching regex.")
    code = re.sub(r"loginBadge:\s*'[^']*'", "loginBadge: ''", code)
    code = re.sub(r"loginEmail:\s*'[^']*'", "loginEmail: ''", code)
    code = re.sub(r"loginPass:\s*'[^']*'", "loginPass: ''", code)
    code = re.sub(r"login2fa:\s*'[^']*'", "login2fa: ''", code)
    print("Cleared state credentials with regex.")

# 3. Add handleFormLogin & helpers if missing
helper_js = """    function handleFormLogin(e) {
      if (e && e.preventDefault) e.preventDefault();
      const roleSel = document.getElementById('loginRoleSelect');
      const emailInp = document.getElementById('loginEmailInput');
      const passInp = document.getElementById('loginPassInput');
      if (roleSel) state.loginRole = roleSel.value;
      if (emailInp) state.loginEmail = emailInp.value;
      if (passInp) state.loginPass = passInp.value;
      closeLoginModal();
      launchTacticalDeck();
    }

    function handleSelectLoginRole(role) {
      state.loginRole = role;
      const roleSel = document.getElementById('loginRoleSelect');
      if (roleSel) roleSel.value = role;
    }

    function handleQuickLogin(role) {
      state.loginRole = role;
      const roleSel = document.getElementById('loginRoleSelect');
      if (roleSel) roleSel.value = role;
      closeLoginModal();
      launchTacticalDeck();
    }
"""

if "function handleFormLogin" not in code:
    code = code.replace("    function openLoginModal() {", helper_js + "\n    function openLoginModal() {", 1)
    print("Added handleFormLogin and helper JS.")

# 4. Make openLoginModal update hash and closeLoginModal clear hash
old_open_login = """    function openLoginModal() {
      const m = document.getElementById('officerLoginModal');
      if (m) m.classList.remove('hidden');
    }

    function closeLoginModal() {
      const m = document.getElementById('officerLoginModal');
      if (m) m.classList.add('hidden');
    }"""

new_open_login = """    function openLoginModal() {
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

if old_open_login in code:
    code = code.replace(old_open_login, new_open_login, 1)
    print("Updated openLoginModal and closeLoginModal with hash navigation.")

# 5. Build the complete split-card login HTML (Pic 2 layout)
pic2_card_html = """
          <!-- Outer Card Split into 2 Panels (Matching Pic 2) -->
          <div class="relative w-full max-w-4xl bg-[#1a2950] rounded-3xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.65)] overflow-hidden flex flex-col md:flex-row border border-white/20 login-split-card">
            
            <!-- Close Button (Top Right of Card) -->
            <button onclick="closeLoginModal()" class="absolute top-4 right-4 z-30 text-white/60 hover:text-white p-2 rounded-full bg-black/30 hover:bg-black/50 text-xs transition-all cursor-pointer" title="Return to Portal">
              ✕
            </button>

            <!-- LEFT PANEL: Light Off-White Curved Brand Section with CHAKRAVYOOH Logo & Name -->
            <div class="w-full md:w-[48%] bg-[#f3f6f9] flex flex-col items-center justify-center p-8 sm:p-12 relative login-left-curved shrink-0 text-center select-none">
              
              <!-- Circular Cyber Vortex Cyclone Logo (Chakravyooh Mesh Formation) -->
              <div class="relative flex items-center justify-center my-3">
                <svg width="136" height="136" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="drop-shadow-md">
                  <!-- Concentric Orbital Guides -->
                  <circle cx="50" cy="50" r="45" stroke="#0ea5e9" stroke-width="1.2" stroke-dasharray="3 3" opacity="0.35"/>
                  <circle cx="50" cy="50" r="32" stroke="#0284c7" stroke-width="1" stroke-dasharray="4 2" opacity="0.25"/>

                  <!-- Outer Swirling Nodes & Conduits (Exact Chakravyooh Cyber Vortex Formation from Pic 2) -->
                  <path d="M50 16 C68 16 82 28 82 48 C82 58 75 70 60 74" stroke="#0284c7" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="50" cy="16" r="5.5" fill="#0284c7"/>
                  <circle cx="82" cy="48" r="5" fill="#38bdf8"/>
                  <circle cx="60" cy="74" r="4.5" fill="#0369a1"/>

                  <path d="M82 72 C74 84 56 90 38 84 C26 80 18 66 18 52" stroke="#0369a1" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="82" cy="72" r="5.5" fill="#0369a1"/>
                  <circle cx="38" cy="84" r="5" fill="#0284c7"/>
                  <circle cx="18" cy="52" r="4.5" fill="#38bdf8"/>

                  <path d="M18 38 C22 24 38 14 56 18 C66 20 74 28 76 40" stroke="#38bdf8" stroke-width="5" stroke-linecap="round"/>
                  <circle cx="18" cy="38" r="5.5" fill="#38bdf8"/>
                  <circle cx="56" cy="18" r="5" fill="#0284c7"/>

                  <!-- Center Eye Core -->
                  <circle cx="50" cy="50" r="7.5" fill="#0f172a"/>
                  <circle cx="50" cy="50" r="4" fill="#38bdf8"/>
                </svg>
              </div>

              <!-- Brand Name & Tagline (Matching Pic 2 Typography Layout) -->
              <div class="mt-4 space-y-1.5 w-full">
                <h1 class="text-3xl sm:text-4xl font-black tracking-wider text-[#1a2950] uppercase font-sans">
                  CHAKRAVYOOH
                </h1>
                <div class="flex items-center justify-center gap-2 max-w-[220px] mx-auto">
                  <div class="h-0.5 flex-1 bg-[#1a2950]"></div>
                  <span class="text-[11px] font-bold text-[#0284c7] tracking-wider uppercase">OPERATIONS</span>
                  <div class="h-0.5 flex-1 bg-[#1a2950]"></div>
                </div>
                <p class="text-[10px] font-mono tracking-widest font-semibold text-slate-500 uppercase pt-1">
                  NATIONAL DISASTER RESILIENCE MESH
                </p>
              </div>
            </div>

            <!-- RIGHT PANEL: Deep Navy Blue Authentication Form (Matching Pic 2) -->
            <div class="w-full md:w-[52%] bg-[#1a2950] p-7 sm:p-10 flex flex-col justify-center space-y-4 text-white relative">
              
              <form onsubmit="handleFormLogin(event);" class="space-y-4 max-w-sm mx-auto w-full">
                
                <!-- Role & Position Selector Button (As requested by user) -->
                <div>
                  <label class="block text-white font-semibold text-xs sm:text-sm mb-1.5 tracking-wide">
                    Role & Position
                  </label>
                  <div class="relative flex items-center">
                    <div class="absolute left-3 w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-xs pointer-events-none text-white">
                      🎖️
                    </div>
                    <select id="loginRoleSelect" onchange="state.loginRole = this.value;" class="w-full pl-11 pr-9 py-2.5 rounded-full bg-[#0284c7] hover:bg-[#0369a1] text-white font-medium text-xs sm:text-sm border border-cyan-400/40 focus:outline-none focus:ring-2 focus:ring-cyan-300 appearance-none cursor-pointer transition-all shadow-md">
                      <option value="ndrf">NDRF — Field Incident Commander</option>
                      <option value="imd">IMD — Chief Meteorologist & Radar Lead</option>
                      <option value="district">SDMA — District Magistrate (Evacuation Controller)</option>
                      <option value="coastguard">Coast Guard — Marine SAR Commander</option>
                      <option value="mesh">Emergency Mesh & Radio Ops Specialist</option>
                      <option value="guest">Public Observer & Research Evaluator</option>
                    </select>
                    <span class="absolute right-4 text-white pointer-events-none text-xs">▼</span>
                  </div>
                </div>

                <!-- Username Input (Empty, No predefined data, matching Pic 2 cyan pill with user icon) -->
                <div>
                  <label class="block text-white font-semibold text-xs sm:text-sm mb-1.5 tracking-wide">
                    Username
                  </label>
                  <div class="relative flex items-center">
                    <div class="absolute left-2.5 w-7 h-7 rounded-full bg-white/20 flex items-center justify-center text-xs pointer-events-none text-white">
                      👤
                    </div>
                    <input type="text" id="loginEmailInput" value="" autocomplete="off" class="w-full pl-11 pr-4 py-2.5 rounded-full bg-[#0284c7] text-white placeholder-blue-100/60 font-medium text-xs sm:text-sm border border-cyan-400/30 focus:outline-none focus:ring-2 focus:ring-cyan-300 transition-all shadow-md" placeholder="Enter username / officer ID" required />
                  </div>
                </div>

                <!-- Password Input (Empty, No predefined data, matching Pic 2 cyan pill with lock icon) -->
                <div>
                  <label class="block text-white font-semibold text-xs sm:text-sm mb-1.5 tracking-wide">
                    Password
                  </label>
                  <div class="relative flex items-center">
                    <div class="absolute left-2.5 w-7 h-7 rounded-full bg-white/20 flex items-center justify-center text-xs pointer-events-none text-white">
                      🔒
                    </div>
                    <input type="password" id="loginPassInput" value="" autocomplete="off" class="w-full pl-11 pr-4 py-2.5 rounded-full bg-[#0284c7] text-white placeholder-blue-100/60 font-medium text-xs sm:text-sm border border-cyan-400/30 focus:outline-none focus:ring-2 focus:ring-cyan-300 transition-all shadow-md" placeholder="Enter password" required />
                  </div>
                </div>

                <!-- Remember Me Checkbox (Matching Pic 2) -->
                <div class="flex items-center text-xs text-blue-100 pt-0.5">
                  <label class="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" id="loginRememberMe" class="w-4 h-4 rounded border-cyan-400 bg-transparent text-cyan-400 focus:ring-0 cursor-pointer" />
                    <span class="text-xs">Remember Me</span>
                  </label>
                </div>

                <!-- Centered Login Button (Matching Pic 2) -->
                <div class="pt-2 flex flex-col items-center">
                  <button type="submit" class="w-36 py-2.5 rounded-xl bg-[#0ea5e9] hover:bg-[#38bdf8] active:scale-95 text-white font-bold text-sm tracking-wide shadow-lg shadow-black/40 transition-all cursor-pointer">
                    Login
                  </button>
                </div>

                <!-- Forgot Password? Link (Matching Pic 2) -->
                <div class="text-center pt-1">
                  <a href="javascript:void(0)" onclick="alert('Password reset instructions dispatched to your registered operational security terminal.')" class="text-blue-200 hover:text-white transition-colors text-xs font-medium">
                    Forgot Password?
                  </a>
                </div>

                <!-- Bottom Auxiliary Buttons (Matching Pic 2: How To Login, Request Login) -->
                <div class="flex items-center justify-center gap-2 pt-3.5 border-t border-white/10 text-xs">
                  <button type="button" onclick="alert('CHAKRAVYOOH LOGIN GUIDE:\\n\\n1. Select your operational agency Role & Position (NDRF, IMD, SDMA, Coast Guard, or Mesh Ops).\\n2. Input your authorized service username/badge and password.\\n3. Click Login to enter the Real-Time Tactical Command Center.')" class="px-3 py-1.5 rounded-md bg-[#0284c7] hover:bg-[#0369a1] text-white text-[11px] font-semibold transition-colors cursor-pointer shadow-sm">
                    How To Login
                  </button>
                  <button type="button" onclick="alert('ACCESS REQUEST:\\n\\nOfficial clearance request forwarded to National Disaster Response Force Command Cell & IMD Operations Directorate. Guest evaluator access granted immediately.')" class="px-3 py-1.5 rounded-md bg-[#0284c7] hover:bg-[#0369a1] text-white text-[11px] font-semibold transition-colors cursor-pointer shadow-sm">
                    Request Login
                  </button>
                  <button type="button" onclick="closeLoginModal()" class="px-3 py-1.5 rounded-md bg-slate-800/90 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-medium transition-colors cursor-pointer">
                    ✕ Return
                  </button>
                </div>
              </form>
            </div>
          </div>
"""

new_officer_modal = f"""    function renderOfficerLoginModal() {{
      return `
        <div id="officerLoginModal" class="fixed inset-0 z-[100] hidden flex items-center justify-center bg-[#cad2dc]/95 backdrop-blur-md p-4 sm:p-8 select-none font-sans overflow-y-auto">
{pic2_card_html}
        </div>
      `;
    }}
"""

new_login_page = f"""    function renderLoginPage() {{
      return `
        <div class="min-h-screen text-slate-100 flex flex-col font-sans select-none bg-[#cad2dc]">
          <!-- Top Strip -->
          <div class="bg-[#1a2950] px-4 py-2 text-[11px] font-mono text-slate-300 flex items-center justify-between border-b border-white/10">
            <div class="flex items-center space-x-2">
              <span>🇮🇳</span>
              <span class="font-bold text-white">GOVERNMENT OF INDIA</span>
              <span class="text-blue-300">•</span>
              <span onclick="setState({{ activePortalView: 'portal' }}); window.scrollTo({{ top: 0, behavior: 'smooth' }});" class="text-cyan-400 font-bold cursor-pointer hover:underline">CHAKRAVYOOH SECURE GATEWAY</span>
            </div>
            <button onclick="setState({{ activePortalView: 'portal' }}); window.scrollTo({{ top: 0, behavior: 'smooth' }});" class="text-slate-300 hover:text-white flex items-center gap-1 transition-colors">
              <span>←</span>
              <span>Back to Launch Page</span>
            </button>
          </div>

          <!-- Main Page Center Container (Matching Pic 2) -->
          <div class="flex-1 flex items-center justify-center p-4 sm:p-8 w-full">
{pic2_card_html}
          </div>
        </div>
      `;
    }}
"""

# Replace renderOfficerLoginModal and renderLoginPage
m_start = "    function renderOfficerLoginModal() {"
p_start = "    function renderLoginPage() {"
app_start = "    function renderApp() {"

idx_m = code.find(m_start)
idx_p = code.find(p_start)
idx_app = code.find(app_start)

if idx_m != -1 and idx_p != -1 and idx_app != -1:
    code = code[:idx_m] + new_officer_modal + "\n" + new_login_page + "\n" + code[idx_app:]
    print("Replaced renderOfficerLoginModal and renderLoginPage with Pic 2 layout.")
else:
    print(f"ERROR: Could not locate bounds: idx_m={idx_m}, idx_p={idx_p}, idx_app={idx_app}")
    exit(1)

# Check renderApp to ensure activePortalView === 'login' renders renderLoginPage
render_app_target = "      // THE PUBLIC PORTAL IS THE ONLY INTERFACE PAGE"
render_app_replacement = """      if (state.activePortalView === 'login') {
        container.innerHTML = `
          ${renderLoginPage()}
        `;
        return;
      }

      // THE PUBLIC PORTAL IS THE ONLY INTERFACE PAGE"""

if render_app_target in code:
    code = code.replace(render_app_target, render_app_replacement, 1)
    print("Updated renderApp to support dedicated login page view.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py successfully.")
