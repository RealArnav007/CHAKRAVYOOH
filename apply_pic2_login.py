import os

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add CSS for login-left-curved and login-split-card
login_css = """    /* Split Card Styling (Matching Pic 2) */
    .login-split-card {
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.7);
    }
    @media (min-width: 768px) {
      .login-left-curved {
        border-top-right-radius: 120px 50%;
        border-bottom-right-radius: 120px 50%;
        box-shadow: 14px 0 28px -4px rgba(0, 0, 0, 0.25);
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

# 3. Replace renderOfficerLoginModal with the exact Pic 2 design
modal_start = "    function renderOfficerLoginModal() {"
modal_end = "    function renderLoginPage() {"

p1 = code.find(modal_start)
p2 = code.find(modal_end)

if p1 == -1 or p2 == -1:
    print(f"ERROR: Could not locate renderOfficerLoginModal bounds! p1={p1}, p2={p2}")
    exit(1)

new_officer_modal = """    function renderOfficerLoginModal() {
      return `
        <div id="officerLoginModal" class="fixed inset-0 z-[100] hidden flex items-center justify-center bg-slate-950/80 backdrop-blur-xl p-4 sm:p-6 select-none font-sans overflow-y-auto">
          
          <!-- Outer Card Split into 2 Panels (Matching Pic 2) -->
          <div class="relative w-full max-w-4xl bg-[#1a2950] rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row border border-white/20 login-split-card">
            
            <!-- Close Button (Top Right of Card) -->
            <button onclick="closeLoginModal()" class="absolute top-4 right-4 z-30 text-white/70 hover:text-white p-2 rounded-full bg-black/30 hover:bg-black/50 text-xs transition-all cursor-pointer" title="Return to Portal">
              ✕
            </button>

            <!-- LEFT PANEL: Light Off-White Curved Brand Section with CHAKRAVYOOH Logo -->
            <div class="w-full md:w-[46%] bg-[#f1f5f9] flex flex-col items-center justify-center p-8 sm:p-12 relative login-left-curved shrink-0 text-center">
              
              <!-- Circular Cyber Vortex Cyclone Logo -->
              <div class="relative flex items-center justify-center my-2">
                <svg width="130" height="130" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="drop-shadow-lg animate-spin" style="animation-duration: 25s;">
                  <!-- Concentric Orbital Guides -->
                  <circle cx="50" cy="50" r="44" stroke="#0ea5e9" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.35"/>
                  <circle cx="50" cy="50" r="32" stroke="#0284c7" stroke-width="1" stroke-dasharray="4 2" opacity="0.25"/>

                  <!-- Outer Swirling Nodes & Conduits (Chakravyooh Formation) -->
                  <path d="M50 18 C66 18 80 30 80 48 C80 58 74 68 62 72" stroke="#0284c7" stroke-width="4.5" stroke-linecap="round"/>
                  <circle cx="50" cy="18" r="5" fill="#0284c7"/>
                  <circle cx="80" cy="48" r="4.5" fill="#38bdf8"/>
                  <circle cx="62" cy="72" r="4" fill="#0369a1"/>

                  <path d="M80 70 C72 82 56 88 40 84 C28 80 20 68 20 54" stroke="#0369a1" stroke-width="4.5" stroke-linecap="round"/>
                  <circle cx="80" cy="70" r="5" fill="#0369a1"/>
                  <circle cx="40" cy="84" r="4.5" fill="#0284c7"/>
                  <circle cx="20" cy="54" r="4" fill="#38bdf8"/>

                  <path d="M20 40 C24 26 38 16 54 20 C64 22 72 30 74 42" stroke="#38bdf8" stroke-width="4.5" stroke-linecap="round"/>
                  <circle cx="20" cy="40" r="5" fill="#38bdf8"/>
                  <circle cx="54" cy="20" r="4.5" fill="#0284c7"/>

                  <!-- Eye Center -->
                  <circle cx="50" cy="50" r="7" fill="#0f172a"/>
                  <circle cx="50" cy="50" r="3.5" fill="#38bdf8"/>
                </svg>
              </div>

              <!-- Brand Name & Tagline -->
              <div class="mt-4 space-y-1">
                <h1 class="text-3xl font-black tracking-wider text-[#1e2f5b] uppercase font-heading">
                  CHAKRAVYOOH
                </h1>
                <div class="h-1 w-28 mx-auto bg-gradient-to-r from-cyan-500 via-blue-600 to-cyan-500 rounded-full"></div>
                <p class="text-[11px] font-mono tracking-[0.2em] font-bold text-slate-500 uppercase pt-0.5">
                  Emergency Intelligence System
                </p>
              </div>
            </div>

            <!-- RIGHT PANEL: Deep Navy Blue Authentication Form (Matching Pic 2) -->
            <div class="w-full md:w-[54%] bg-[#1a2950] p-7 sm:p-10 flex flex-col justify-center space-y-4 text-white">
              
              <form onsubmit="handleFormLogin(event); closeLoginModal(); launchTacticalDeck();" class="space-y-4">
                
                <!-- Role / Position Selector Button -->
                <div>
                  <label class="block text-white font-semibold text-xs sm:text-sm mb-1.5 tracking-wide">
                    Role & Position
                  </label>
                  <div class="relative flex items-center">
                    <span class="absolute left-3.5 text-blue-200 text-sm pointer-events-none">🎖️</span>
                    <select id="loginRoleSelect" onchange="state.loginRole = this.value;" class="w-full pl-10 pr-9 py-2.5 rounded-full bg-[#0284c7] hover:bg-[#0369a1] text-white font-medium text-xs sm:text-sm border border-cyan-400/40 focus:outline-none focus:ring-2 focus:ring-cyan-300 appearance-none cursor-pointer transition-all shadow-md">
                      <option value="ndrf">NDRF — Field Incident Commander</option>
                      <option value="imd">IMD — Chief Meteorologist & Radar Lead</option>
                      <option value="district">SDMA — District Magistrate (Evacuation)</option>
                      <option value="coastguard">Coast Guard — Marine Rescue Lead</option>
                      <option value="mesh">Emergency Mesh Operations Specialist</option>
                      <option value="guest">Public Observer & Academic Evaluator</option>
                    </select>
                    <span class="absolute right-3.5 text-white pointer-events-none text-xs">▼</span>
                  </div>
                </div>

                <!-- Username Input (Empty by default, no predefined data) -->
                <div>
                  <label class="block text-white font-semibold text-xs sm:text-sm mb-1.5 tracking-wide">
                    Username
                  </label>
                  <div class="relative flex items-center">
                    <span class="absolute left-3.5 text-blue-200 text-sm pointer-events-none">👤</span>
                    <input type="text" id="loginEmailInput" value="" class="w-full pl-10 pr-4 py-2.5 rounded-full bg-[#0284c7] text-white placeholder-blue-200/60 font-medium text-xs sm:text-sm border border-cyan-400/40 focus:outline-none focus:ring-2 focus:ring-cyan-300 transition-all shadow-md" placeholder="Enter username / badge ID" required />
                  </div>
                </div>

                <!-- Password Input (Empty by default, no predefined data) -->
                <div>
                  <label class="block text-white font-semibold text-xs sm:text-sm mb-1.5 tracking-wide">
                    Password
                  </label>
                  <div class="relative flex items-center">
                    <span class="absolute left-3.5 text-blue-200 text-sm pointer-events-none">🔒</span>
                    <input type="password" id="loginPassInput" value="" class="w-full pl-10 pr-4 py-2.5 rounded-full bg-[#0284c7] text-white placeholder-blue-200/60 font-medium text-xs sm:text-sm border border-cyan-400/40 focus:outline-none focus:ring-2 focus:ring-cyan-300 transition-all shadow-md" placeholder="••••••••" required />
                  </div>
                </div>

                <!-- Remember Me & Forgot Password -->
                <div class="flex items-center justify-between text-xs text-blue-100 pt-1 font-sans">
                  <label class="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" id="loginRememberMe" class="w-4 h-4 rounded border-cyan-400 bg-transparent text-cyan-400 focus:ring-0 cursor-pointer" />
                    <span>Remember Me</span>
                  </label>
                  <a href="javascript:void(0)" onclick="alert('Password reset instructions dispatched to your authorized agency officer terminal.')" class="text-blue-200 hover:text-white transition-colors text-xs">
                    Forgot Password?
                  </a>
                </div>

                <!-- Primary Login Button -->
                <div class="pt-2 flex flex-col items-center">
                  <button type="submit" class="w-36 py-2.5 rounded-xl bg-[#0ea5e9] hover:bg-[#38bdf8] active:scale-95 text-white font-bold text-sm tracking-wide shadow-lg shadow-cyan-950/60 transition-all cursor-pointer">
                    Login
                  </button>
                </div>

                <!-- Bottom Auxiliary Buttons (Pic 2: How To Login, Request Login) -->
                <div class="flex items-center justify-center gap-2.5 pt-3 border-t border-white/10 text-xs">
                  <button type="button" onclick="alert('Enter your official service username, password, and select your operational role (NDRF / IMD / SDMA / Coast Guard) to initialize the tactical deck.')" class="px-3 py-1 rounded bg-[#0369a1]/80 hover:bg-[#0284c7] text-white text-[11px] font-medium transition-colors cursor-pointer">
                    How To Login
                  </button>
                  <button type="button" onclick="alert('Access request submitted to Ministry of Home Affairs Disaster Operations cell. Temporary guest credentials enabled.')" class="px-3 py-1 rounded bg-[#0369a1]/80 hover:bg-[#0284c7] text-white text-[11px] font-medium transition-colors cursor-pointer">
                    Request Login
                  </button>
                  <button type="button" onclick="closeLoginModal()" class="px-3 py-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-medium transition-colors cursor-pointer">
                    ✕ Return
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    }
"""

code = code[:p1] + new_officer_modal + "\n" + code[p2:]
print("Replaced renderOfficerLoginModal with Pic 2 design.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("update_portal.py updated successfully.")
