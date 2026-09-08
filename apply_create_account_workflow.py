import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add registeredUsers to state
state_users = """      // Registered Users & Super Admin Approval State
      registeredUsers: [
        {
          name: 'Insp. A. Kumar',
          email: 'a.kumar@ndrf.gov.in',
          role: 'ndrf',
          badge: 'IMD-NDRF-882',
          approved: true,
          status: 'approved'
        },
        {
          name: 'Dr. S. Roy',
          email: 's.roy@imd.gov.in',
          role: 'imd',
          badge: 'IMD-RSMC-401',
          approved: true,
          status: 'approved'
        }
      ],
"""

if "registeredUsers:" not in code:
    code = code.replace("      // Login Credentials & Preset State", state_users + "      // Login Credentials & Preset State", 1)
    print("Added registeredUsers to state.")

# 2. Add openCreateAccountModal, closeCreateAccountModal, handleCreateAccountSubmit, simulateSuperAdminApproval
account_js = """    function openCreateAccountModal() {
      const loginModal = document.getElementById('officerLoginModal');
      const createModal = document.getElementById('createAccountModal');
      if (loginModal) {
        loginModal.classList.remove('opacity-100', 'pointer-events-auto');
        loginModal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { loginModal.classList.add('hidden'); }, 200);
      }
      if (createModal) {
        // Reset form view
        const formC = document.getElementById('regFormContainer');
        const succC = document.getElementById('regSuccessContainer');
        if (formC) formC.classList.remove('hidden');
        if (succC) succC.classList.add('hidden');

        createModal.classList.remove('hidden');
        void createModal.offsetWidth;
        createModal.classList.remove('opacity-0', 'pointer-events-none');
        createModal.classList.add('opacity-100', 'pointer-events-auto');
      }
    }

    function closeCreateAccountModal() {
      const createModal = document.getElementById('createAccountModal');
      if (createModal) {
        createModal.classList.remove('opacity-100', 'pointer-events-auto');
        createModal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { createModal.classList.add('hidden'); }, 200);
      }
      openLoginModal();
    }

    function handleCreateAccountSubmit(e) {
      if (e && e.preventDefault) e.preventDefault();
      const nameInp = document.getElementById('regNameInput');
      const emailInp = document.getElementById('regEmailInput');
      const roleSel = document.getElementById('regRoleSelect');
      const badgeInp = document.getElementById('regBadgeInput');
      const passInp = document.getElementById('regPassInput');

      const name = nameInp ? nameInp.value.trim() : 'Officer';
      const email = emailInp ? emailInp.value.trim() : '';
      const role = roleSel ? roleSel.value : 'ndrf';
      const badge = badgeInp ? badgeInp.value.trim() : '';
      const pass = passInp ? passInp.value.trim() : '';

      if (!email) {
        alert('Please enter your official identification email.');
        return;
      }

      // Check if already registered
      let user = state.registeredUsers.find(u => u.email.toLowerCase() === email.toLowerCase());
      if (!user) {
        user = {
          name,
          email,
          role,
          badge,
          pass,
          approved: false,
          status: 'pending_super_admin',
          submittedAt: new Date().toLocaleTimeString()
        };
        state.registeredUsers.push(user);
      }

      // Switch to Confirmation Screen: Dispatched to Super Admin (NO OTP REQUIRED)
      const formC = document.getElementById('regFormContainer');
      const succC = document.getElementById('regSuccessContainer');
      if (formC) formC.classList.add('hidden');
      if (succC) {
        succC.innerHTML = `
          <div class="text-center space-y-4 py-2 select-none">
            <div class="w-16 h-16 mx-auto rounded-full bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center text-3xl shadow-[0_0_25px_rgba(14,165,233,0.5)]">
              ✉️
            </div>
            
            <div class="space-y-1">
              <h3 class="text-xl font-bold text-white font-heading">Authorization Mail Sent</h3>
              <p class="text-[11px] font-mono text-cyan-300 tracking-wider uppercase">DISPATCHED TO NATIONAL SUPER ADMIN CELL</p>
            </div>

            <div class="bg-[#0b1b36] border border-cyan-500/30 rounded-xl p-4 text-left text-xs space-y-2.5 font-mono">
              <div class="flex items-center justify-between text-[11px] pb-1.5 border-b border-cyan-500/20">
                <span class="text-cyan-200">Registration Status:</span>
                <span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40 animate-pulse">PENDING SUPER ADMIN APPROVAL</span>
              </div>
              <div class="text-slate-200">
                <span class="text-cyan-300 font-semibold">Officer:</span> ${name}
              </div>
              <div class="text-slate-200">
                <span class="text-cyan-300 font-semibold">Official Email:</span> ${email}
              </div>
              <div class="text-slate-200">
                <span class="text-cyan-300 font-semibold">Role:</span> ${role.toUpperCase()} • Badge: ${badge || 'AUTO-ASSIGNED'}
              </div>
              <div class="text-cyan-100 text-[11px] leading-relaxed pt-1.5 border-t border-cyan-500/10">
                🔒 <strong class="text-white">NO OTP REQUIRED.</strong> Per security protocol, credentials will only be unlocked once the <strong>Super Admin</strong> reviews and approves the authorization verification mail dispatched to <code class="text-cyan-300 font-bold">superadmin@chakravyooh.gov.in</code>.
              </div>
            </div>

            <!-- Interactive Super Admin Approval Simulator for Evaluation -->
            <div class="p-3 rounded-xl bg-cyan-950/60 border border-cyan-500/40 space-y-2">
              <div class="text-[11px] text-cyan-200 flex items-center justify-between font-mono">
                <span>Super Admin Mail Inbox:</span>
                <span class="text-emerald-400 text-[10px] font-bold">1 PENDING REQUEST</span>
              </div>
              <button type="button" onclick="simulateSuperAdminApproval('${email}')" class="w-full py-2.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:scale-95 text-white font-bold text-xs tracking-wide transition-all cursor-pointer shadow-lg shadow-emerald-950/60 flex items-center justify-center gap-1.5">
                <span>⚡</span>
                <span>Simulate Super Admin Approval (Approve Email Now)</span>
              </button>
            </div>

            <div class="pt-1 flex items-center justify-center gap-2">
              <button type="button" onclick="closeCreateAccountModal()" class="px-5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors cursor-pointer">
                Return to Login Screen
              </button>
            </div>
          </div>
        `;
        succC.classList.remove('hidden');
      }
    }

    function simulateSuperAdminApproval(email) {
      const user = state.registeredUsers.find(u => u.email.toLowerCase() === email.toLowerCase());
      if (user) {
        user.approved = true;
        user.status = 'approved';
      }
      alert('SUPER ADMIN APPROVAL VERIFIED:\\n\\nSuper Admin has reviewed and authorized access for:\\n' + email + '\\n\\nCredentials are now ACTIVE. You may now log in directly without any OTP.');
      closeCreateAccountModal();
      // Prepopulate email and role in login inputs
      const emailInput = document.getElementById('loginEmailInput');
      const roleSelect = document.getElementById('loginRoleSelect');
      if (emailInput) emailInput.value = email;
      if (roleSelect && user) roleSelect.value = user.role;
    }
"""

if "function openCreateAccountModal" not in code:
    code = code.replace("    function handleFormLogin(e) {", account_js + "\n    function handleFormLogin(e) {", 1)
    print("Added account modal handler functions.")

# 3. Update handleFormLogin to check super admin approval
old_login_handler = """    function handleFormLogin(e) {
      if (e && e.preventDefault) e.preventDefault();
      const roleSel = document.getElementById('loginRoleSelect');
      const emailInp = document.getElementById('loginEmailInput');
      const passInp = document.getElementById('loginPassInput');
      if (roleSel) state.loginRole = roleSel.value;
      if (emailInp) state.loginEmail = emailInp.value;
      if (passInp) state.loginPass = passInp.value;
      
      const m = document.getElementById('officerLoginModal');
      if (m) {
        m.classList.remove('opacity-100', 'pointer-events-auto');
        m.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { m.classList.add('hidden'); }, 300);
      }
      launchTacticalDeck();
    }"""

new_login_handler = """    function handleFormLogin(e) {
      if (e && e.preventDefault) e.preventDefault();
      const roleSel = document.getElementById('loginRoleSelect');
      const emailInp = document.getElementById('loginEmailInput');
      const passInp = document.getElementById('loginPassInput');
      const email = emailInp ? emailInp.value.trim() : '';

      // Check if user is registered and whether Super Admin has approved the account
      if (email) {
        const found = state.registeredUsers.find(u => u.email.toLowerCase() === email.toLowerCase());
        if (found && !found.approved) {
          alert('ACCESS DENIED (PENDING SUPER ADMIN APPROVAL):\\n\\nYour account has been submitted but is currently awaiting Super Admin email authorization.\\n\\nPlease wait for superadmin@chakravyooh.gov.in to approve your registration.');
          return;
        }
      }

      if (roleSel) state.loginRole = roleSel.value;
      if (emailInp) state.loginEmail = emailInp.value;
      if (passInp) state.loginPass = passInp.value;
      
      const m = document.getElementById('officerLoginModal');
      if (m) {
        m.classList.remove('opacity-100', 'pointer-events-auto');
        m.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { m.classList.add('hidden'); }, 300);
      }
      launchTacticalDeck();
    }"""

if old_login_handler in code:
    code = code.replace(old_login_handler, new_login_handler, 1)
    print("Updated handleFormLogin with approval verification.")

# 4. Replace Request Login button with Create Account button
# Find and replace Request Login in both modals
req_btn_pattern = r'<button type="button" onclick="alert\(\'ACCESS REQUEST:[^\']+\'\)" class="[^"]+">\s*Request Login\s*</button>'
create_btn_html = """<button type="button" onclick="openCreateAccountModal()" class="px-3 py-1.5 rounded-md bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white border border-cyan-400/40 text-[11px] font-semibold transition-all cursor-pointer shadow-sm flex items-center gap-1">
                    <span>✨</span>
                    <span>Create Account</span>
                  </button>"""

code = re.sub(req_btn_pattern, create_btn_html, code)
print("Replaced Request Login button with Create Account button.")

# 5. Build renderCreateAccountModal
create_account_modal_html = """    function renderCreateAccountModal() {
      return `
        <div id="createAccountModal" class="fixed inset-0 z-50 hidden opacity-0 pointer-events-none transition-all duration-500 ease-out flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4 sm:p-8 select-none font-sans overflow-y-auto">
          
          <!-- Outer Card Split into 2 Panels (Matching Pic 2 & Preface Dark Theme) -->
          <div class="relative w-full max-w-4xl bg-[#060b16]/95 backdrop-blur-2xl rounded-3xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85),0_0_40px_rgba(14,165,233,0.18)] overflow-hidden flex flex-col md:flex-row border border-cyan-500/30 login-split-card">
            
            <!-- Close Button (Top Right of Card) -->
            <button onclick="closeCreateAccountModal()" class="absolute top-4 right-4 z-30 text-cyan-200/70 hover:text-white p-2 rounded-full bg-slate-900/60 hover:bg-slate-800 border border-cyan-500/20 text-xs transition-all cursor-pointer" title="Return to Login">
              ✕
            </button>

            <!-- LEFT PANEL: Frosted Deep Space Curved Brand Section -->
            <div class="w-full md:w-[45%] bg-gradient-to-br from-[#0c182e]/95 via-[#0f203d]/90 to-[#070e1c]/95 backdrop-blur-xl flex flex-col items-center justify-center p-8 sm:p-10 relative login-left-curved shrink-0 text-center select-none border-r border-cyan-500/20">
              
              <!-- Circular Cyber Vortex Cyclone Logo -->
              <div class="relative flex items-center justify-center my-3">
                <svg width="125" height="125" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="drop-shadow-[0_0_15px_rgba(14,165,233,0.4)]">
                  <circle cx="50" cy="50" r="45" stroke="#0ea5e9" stroke-width="1.2" stroke-dasharray="3 3" opacity="0.4"/>
                  <circle cx="50" cy="50" r="32" stroke="#38bdf8" stroke-width="1" stroke-dasharray="4 2" opacity="0.3"/>
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
                  <circle cx="50" cy="50" r="8" fill="#070d1a" stroke="#0ea5e9" stroke-width="1.5"/>
                  <circle cx="50" cy="50" r="4" fill="#38bdf8"/>
                </svg>
              </div>

              <!-- Brand Name & Registration Banner -->
              <div class="mt-3 space-y-1 w-full">
                <h2 class="text-2xl sm:text-3xl font-black tracking-wider text-white uppercase font-sans drop-shadow-md">
                  CHAKRAVYOOH
                </h2>
                <div class="flex items-center justify-center gap-2 max-w-[200px] mx-auto">
                  <div class="h-0.5 flex-1 bg-gradient-to-r from-transparent to-cyan-400"></div>
                  <span class="text-[10px] font-bold text-cyan-300 tracking-wider uppercase font-mono">OFFICER ENROLLMENT</span>
                  <div class="h-0.5 flex-1 bg-gradient-to-l from-transparent to-cyan-400"></div>
                </div>
                <div class="mt-4 p-3 rounded-xl bg-blue-950/40 border border-cyan-500/20 text-left text-[11px] text-cyan-200/80 font-mono space-y-1.5">
                  <div class="text-white font-bold flex items-center gap-1">
                    <span>🛡️</span>
                    <span>Approval Protocol:</span>
                  </div>
                  <p class="leading-relaxed">
                    1. Submit your official credentials.<br>
                    2. <strong class="text-cyan-300">No OTP required.</strong><br>
                    3. Authorization mail dispatched to Super Admin.<br>
                    4. Login unlocks upon Super Admin approval.
                  </p>
                </div>
              </div>
            </div>

            <!-- RIGHT PANEL: Registration Form & Confirmation Container -->
            <div class="w-full md:w-[55%] bg-[#060b16]/95 backdrop-blur-xl p-7 sm:p-9 flex flex-col justify-center text-white relative">
              
              <!-- Form Container -->
              <div id="regFormContainer">
                <div class="mb-4">
                  <h3 class="text-lg font-bold text-white font-heading flex items-center gap-2">
                    <span>Create Officer Account</span>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">Super Admin Approval</span>
                  </h3>
                  <p class="text-xs text-cyan-200/70">Enter official service credentials to request tactical operations access.</p>
                </div>

                <form onsubmit="handleCreateAccountSubmit(event);" class="space-y-3 max-w-sm mx-auto w-full">
                  
                  <!-- Full Name -->
                  <div>
                    <label class="block text-cyan-200 font-semibold text-xs mb-1 tracking-wide font-sans">
                      Full Officer Name
                    </label>
                    <div class="relative flex items-center">
                      <div class="absolute left-2.5 w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                        👤
                      </div>
                      <input type="text" id="regNameInput" class="w-full pl-10 pr-4 py-2 rounded-full bg-[#0b1b36] text-white placeholder-cyan-300/40 font-medium text-xs border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]" placeholder="e.g. Insp. Vikram Rathore" required />
                    </div>
                  </div>

                  <!-- Official Email -->
                  <div>
                    <label class="block text-cyan-200 font-semibold text-xs mb-1 tracking-wide font-sans">
                      Official Identification Email
                    </label>
                    <div class="relative flex items-center">
                      <div class="absolute left-2.5 w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                        ✉️
                      </div>
                      <input type="email" id="regEmailInput" class="w-full pl-10 pr-4 py-2 rounded-full bg-[#0b1b36] text-white placeholder-cyan-300/40 font-medium text-xs border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]" placeholder="v.rathore@ndrf.gov.in" required />
                    </div>
                  </div>

                  <!-- Role & Position -->
                  <div>
                    <label class="block text-cyan-200 font-semibold text-xs mb-1 tracking-wide font-sans">
                      Operational Role & Position
                    </label>
                    <div class="relative flex items-center">
                      <div class="absolute left-2.5 w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                        🎖️
                      </div>
                      <select id="regRoleSelect" class="w-full pl-10 pr-9 py-2 rounded-full bg-[#0b1b36] hover:bg-[#0f244a] text-cyan-100 font-medium text-xs border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 appearance-none cursor-pointer transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]">
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

                  <!-- Service Badge / ID -->
                  <div>
                    <label class="block text-cyan-200 font-semibold text-xs mb-1 tracking-wide font-sans">
                      Service Badge / ID Number
                    </label>
                    <div class="relative flex items-center">
                      <div class="absolute left-2.5 w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                        🆔
                      </div>
                      <input type="text" id="regBadgeInput" class="w-full pl-10 pr-4 py-2 rounded-full bg-[#0b1b36] text-white placeholder-cyan-300/40 font-medium text-xs border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]" placeholder="e.g. NDRF-OD-8924" required />
                    </div>
                  </div>

                  <!-- Password -->
                  <div>
                    <label class="block text-cyan-200 font-semibold text-xs mb-1 tracking-wide font-sans">
                      Create Password
                    </label>
                    <div class="relative flex items-center">
                      <div class="absolute left-2.5 w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                        🔒
                      </div>
                      <input type="password" id="regPassInput" class="w-full pl-10 pr-4 py-2 rounded-full bg-[#0b1b36] text-white placeholder-cyan-300/40 font-medium text-xs border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]" placeholder="Create a secure password" required />
                    </div>
                  </div>

                  <!-- Submit Button -->
                  <div class="pt-3 flex items-center justify-between gap-3">
                    <button type="button" onclick="closeCreateAccountModal()" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors cursor-pointer">
                      ← Back to Login
                    </button>
                    <button type="submit" class="flex-1 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 active:scale-95 text-white font-bold text-xs tracking-wide shadow-[0_8px_25px_rgba(14,165,233,0.4)] border border-cyan-300/30 transition-all cursor-pointer flex items-center justify-center gap-1.5">
                      <span>✉️</span>
                      <span>Request Super Admin Approval</span>
                    </button>
                  </div>
                </form>
              </div>

              <!-- Success / Confirmation Container -->
              <div id="regSuccessContainer" class="hidden"></div>
            </div>
          </div>
        </div>
      `;
    }
"""

if "function renderCreateAccountModal" not in code:
    code = code.replace("    function renderOfficerLoginModal() {", create_account_modal_html + "\n    function renderOfficerLoginModal() {", 1)
    print("Added renderCreateAccountModal.")

# 6. Make sure renderApp renders renderCreateAccountModal
render_app_modals = "${renderOfficerLoginModal()}\n        ${renderCreateAccountModal()}"
if "${renderCreateAccountModal()}" not in code:
    code = code.replace("${renderOfficerLoginModal()}", render_app_modals, 1)
    print("Mounted renderCreateAccountModal in renderApp.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py successfully.")
