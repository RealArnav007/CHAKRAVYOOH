import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add forgot password handler functions
forgot_js = """    function openForgotPasswordModal() {
      const loginModal = document.getElementById('officerLoginModal');
      const forgotModal = document.getElementById('forgotPasswordModal');
      if (loginModal) {
        loginModal.classList.remove('opacity-100', 'pointer-events-auto');
        loginModal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { loginModal.classList.add('hidden'); }, 200);
      }
      if (forgotModal) {
        // Reset form view
        const formC = document.getElementById('forgotFormContainer');
        const succC = document.getElementById('forgotSuccessContainer');
        const emailInp = document.getElementById('recoveryEmailInput');
        if (formC) formC.classList.remove('hidden');
        if (succC) succC.classList.add('hidden');
        if (emailInp) {
          const loginInp = document.getElementById('loginEmailInput');
          emailInp.value = (loginInp && loginInp.value) ? loginInp.value : '';
        }

        forgotModal.classList.remove('hidden');
        void forgotModal.offsetWidth;
        forgotModal.classList.remove('opacity-0', 'pointer-events-none');
        forgotModal.classList.add('opacity-100', 'pointer-events-auto');
      }
    }

    function closeForgotPasswordModal() {
      const forgotModal = document.getElementById('forgotPasswordModal');
      if (forgotModal) {
        forgotModal.classList.remove('opacity-100', 'pointer-events-auto');
        forgotModal.classList.add('opacity-0', 'pointer-events-none');
        setTimeout(() => { forgotModal.classList.add('hidden'); }, 200);
      }
      openLoginModal();
    }

    function handleForgotPasswordSubmit(e) {
      if (e && e.preventDefault) e.preventDefault();
      const emailInp = document.getElementById('recoveryEmailInput');
      const recoveryEmail = emailInp ? emailInp.value.trim() : '';

      if (!recoveryEmail) {
        alert('Please enter your recovery email address.');
        return;
      }

      // Display confirmation screen with recovery email
      const formC = document.getElementById('forgotFormContainer');
      const succC = document.getElementById('forgotSuccessContainer');
      if (formC) formC.classList.add('hidden');
      if (succC) {
        succC.innerHTML = `
          <div class="text-center space-y-4 py-2 select-none">
            <div class="w-16 h-16 mx-auto rounded-full bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center text-3xl shadow-[0_0_25px_rgba(14,165,233,0.5)]">
              📬
            </div>
            
            <div class="space-y-1">
              <h3 class="text-xl font-bold text-white font-heading">Recovery Email Sent</h3>
              <p class="text-[11px] font-mono text-cyan-300 tracking-wider uppercase">PASSWORD RESET TOKEN DISPATCHED</p>
            </div>

            <div class="bg-[#0b1b36] border border-cyan-500/30 rounded-xl p-4 text-left text-xs space-y-2.5 font-mono">
              <div class="flex items-center justify-between text-[11px] pb-1.5 border-b border-cyan-500/20">
                <span class="text-cyan-200">Dispatch Status:</span>
                <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40">TRANSMITTED VIA ENCRYPTED RELAY</span>
              </div>
              <div class="text-slate-200">
                <span class="text-cyan-300 font-semibold">Target Recovery Mail:</span>
                <span class="text-white font-bold bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-500/40 ml-1 break-all">${recoveryEmail}</span>
              </div>
              <div class="text-cyan-100 text-[11px] leading-relaxed pt-1.5 border-t border-cyan-500/10">
                A cryptographic verification key and one-time password reconfiguration link have been dispatched to <strong>${recoveryEmail}</strong>. Please check your inbox and spam folders to reset your credentials.
              </div>
            </div>

            <div class="pt-2 flex items-center justify-center gap-2">
              <button type="button" onclick="closeForgotPasswordModal()" class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-lg transition-all cursor-pointer">
                Return to Login Screen
              </button>
            </div>
          </div>
        `;
        succC.classList.remove('hidden');
      }
    }
"""

if "function openForgotPasswordModal" not in code:
    code = code.replace("    function openCreateAccountModal() {", forgot_js + "\n    function openCreateAccountModal() {", 1)
    print("Added forgot password modal handler functions.")

# 2. Update Forgot Password? links to call openForgotPasswordModal()
old_forgot_link = """onclick="alert('Password reset instructions dispatched to your registered operational security terminal.')" """
new_forgot_link = """onclick="openForgotPasswordModal()" """

code = code.replace(old_forgot_link, new_forgot_link)
print("Updated Forgot Password? links to call openForgotPasswordModal().")

# 3. Add renderForgotPasswordModal definition
forgot_modal_html = """    function renderForgotPasswordModal() {
      return `
        <div id="forgotPasswordModal" class="fixed inset-0 z-50 hidden opacity-0 pointer-events-none transition-all duration-500 ease-out flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4 sm:p-8 select-none font-sans overflow-y-auto">
          
          <!-- Outer Card Split into 2 Panels (Matching Preface Dark Theme) -->
          <div class="relative w-full max-w-4xl bg-[#060b16]/95 backdrop-blur-2xl rounded-3xl shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85),0_0_40px_rgba(14,165,233,0.18)] overflow-hidden flex flex-col md:flex-row border border-cyan-500/30 login-split-card">
            
            <!-- Close Button (Top Right of Card) -->
            <button onclick="closeForgotPasswordModal()" class="absolute top-4 right-4 z-30 text-cyan-200/70 hover:text-white p-2 rounded-full bg-slate-900/60 hover:bg-slate-800 border border-cyan-500/20 text-xs transition-all cursor-pointer" title="Return to Login">
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

              <!-- Brand Name & Recovery Banner -->
              <div class="mt-3 space-y-1 w-full">
                <h2 class="text-2xl sm:text-3xl font-black tracking-wider text-white uppercase font-sans drop-shadow-md">
                  CHAKRAVYOOH
                </h2>
                <div class="flex items-center justify-center gap-2 max-w-[200px] mx-auto">
                  <div class="h-0.5 flex-1 bg-gradient-to-r from-transparent to-cyan-400"></div>
                  <span class="text-[10px] font-bold text-cyan-300 tracking-wider uppercase font-mono">CREDENTIAL RECOVERY</span>
                  <div class="h-0.5 flex-1 bg-gradient-to-l from-transparent to-cyan-400"></div>
                </div>
                <div class="mt-4 p-3 rounded-xl bg-blue-950/40 border border-cyan-500/20 text-left text-[11px] text-cyan-200/80 font-mono space-y-1.5">
                  <div class="text-white font-bold flex items-center gap-1">
                    <span>🛡️</span>
                    <span>Recovery Process:</span>
                  </div>
                  <p class="leading-relaxed">
                    1. Input your official recovery mail.<br>
                    2. Cryptographic reset link dispatched.<br>
                    3. Configure new secure password.<br>
                    4. Re-authenticate via tactical gateway.
                  </p>
                </div>
              </div>
            </div>

            <!-- RIGHT PANEL: Recovery Email Input & Confirmation Container -->
            <div class="w-full md:w-[55%] bg-[#060b16]/95 backdrop-blur-xl p-7 sm:p-10 flex flex-col justify-center text-white relative">
              
              <!-- Form Container -->
              <div id="forgotFormContainer">
                <div class="mb-5">
                  <h3 class="text-lg font-bold text-white font-heading flex items-center gap-2">
                    <span>Forgot Password?</span>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">Secure Recovery</span>
                  </h3>
                  <p class="text-xs text-cyan-200/70 mt-1">Enter your registered recovery email to receive an instant credential reset token.</p>
                </div>

                <form onsubmit="handleForgotPasswordSubmit(event);" class="space-y-4 max-w-sm mx-auto w-full">
                  
                  <!-- Recovery Email Input Option -->
                  <div>
                    <label class="block text-cyan-200 font-semibold text-xs mb-1.5 tracking-wide font-sans">
                      Recovery Email Address
                    </label>
                    <div class="relative flex items-center">
                      <div class="absolute left-2.5 w-7 h-7 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-xs pointer-events-none text-cyan-200">
                        ✉️
                      </div>
                      <input type="email" id="recoveryEmailInput" class="w-full pl-11 pr-4 py-2.5 rounded-full bg-[#0b1b36] text-white placeholder-cyan-300/40 font-medium text-xs sm:text-sm border border-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 transition-all shadow-[0_4px_15px_rgba(0,0,0,0.4)]" placeholder="Enter recovery email address" required />
                    </div>
                  </div>

                  <div class="p-3 rounded-xl bg-blue-950/30 border border-cyan-500/20 text-[11px] font-mono text-cyan-200/80 leading-relaxed">
                    ℹ️ Instructions and password re-keying parameters will be dispatched immediately to this recovery email.
                  </div>

                  <!-- Actions -->
                  <div class="pt-2 flex items-center justify-between gap-3">
                    <button type="button" onclick="closeForgotPasswordModal()" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors cursor-pointer">
                      ← Back to Login
                    </button>
                    <button type="submit" class="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 active:scale-95 text-white font-bold text-xs tracking-wide shadow-[0_8px_25px_rgba(14,165,233,0.4)] border border-cyan-300/30 transition-all cursor-pointer flex items-center justify-center gap-1.5">
                      <span>📤</span>
                      <span>Send Recovery Email</span>
                    </button>
                  </div>
                </form>
              </div>

              <!-- Success / Confirmation Container -->
              <div id="forgotSuccessContainer" class="hidden"></div>
            </div>
          </div>
        </div>
      `;
    }
"""

if "function renderForgotPasswordModal" not in code:
    code = code.replace("    function renderCreateAccountModal() {", forgot_modal_html + "\n    function renderCreateAccountModal() {", 1)
    print("Added renderForgotPasswordModal definition.")

# 4. Mount renderForgotPasswordModal in renderApp
target_mount = "${renderCreateAccountModal()}"
new_mount = "${renderCreateAccountModal()}\n        ${renderForgotPasswordModal()}"

if "${renderForgotPasswordModal()}" not in code:
    code = code.replace(target_mount, new_mount, 1)
    print("Mounted renderForgotPasswordModal in renderApp.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py with forgot password workflow.")
