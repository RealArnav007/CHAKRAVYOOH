/* ==========================================================================
   PROJECT BEACON — Enterprise Authentication & Provisioning Console (Bottom Page Redirect)
   Handles: Smooth scroll redirect to #authSection, Brevo SMTP OTP, 6-Digit Verification,
   JWT token storage in localStorage, and Auth State Navigation Button.
   ========================================================================== */

(function () {
  let currentEmail = '';
  let otpTimer = null;
  let timerSeconds = 300;

  document.addEventListener('DOMContentLoaded', () => {
    // 1. Setup 6-digit OTP input auto-advance
    const otpInputs = document.querySelectorAll('.otp-digit-input-bottom');
    otpInputs.forEach((input, idx) => {
      input.addEventListener('input', (e) => {
        if (e.target.value && idx < otpInputs.length - 1) {
          otpInputs[idx + 1].focus();
        }
      });
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !e.target.value && idx > 0) {
          otpInputs[idx - 1].focus();
        }
      });
    });

    checkExistingAuth();
  });

  // Smooth Scroll Redirect Function to #authSection at bottom of page
  window.scrollToAuthSection = function () {
    const authSection = document.getElementById('authSection');
    if (authSection) {
      authSection.scrollIntoView({ behavior: 'smooth' });
      const emailInput = document.getElementById('authBottomEmailInput');
      if (emailInput) setTimeout(() => emailInput.focus(), 600);
    }
  };

  window.handleBottomSendOtp = async function () {
    const emailInput = document.getElementById('authBottomEmailInput');
    const msgDiv = document.getElementById('authBottomEmailMsg');
    const btn = document.getElementById('btnBottomSendOtp');
    const email = emailInput ? emailInput.value.trim() : '';

    if (!email || !email.includes('@')) {
      if (msgDiv) {
        msgDiv.style.color = 'var(--color-red)';
        msgDiv.innerText = 'Please enter a valid email address.';
        msgDiv.style.display = 'block';
      }
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerText = 'DISPATCHING OTP...';
    }
    if (msgDiv) {
      msgDiv.style.color = 'var(--color-cyan)';
      msgDiv.innerText = 'Dispatching Brevo SMTP OTP email...';
      msgDiv.style.display = 'block';
    }

    try {
      const res = await fetch('/api/v1/auth/request-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();

      if (res.ok) {
        currentEmail = email;
        document.getElementById('authBottomTargetEmail').innerText = email;
        document.getElementById('authBottomStepEmail').style.display = 'none';
        document.getElementById('authBottomStepOtp').style.display = 'block';
        startOtpCountdown();
      } else {
        if (msgDiv) {
          msgDiv.style.color = 'var(--color-red)';
          msgDiv.innerText = data.detail || 'Failed to dispatch OTP.';
        }
      }
    } catch (err) {
      if (msgDiv) {
        msgDiv.style.color = 'var(--color-red)';
        msgDiv.innerText = 'Network error. Could not connect to auth service.';
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'REQUEST 6-DIGIT OTP CODE ➔';
      }
    }
  };

  window.handleBottomVerifyOtp = async function () {
    const otpInputs = document.querySelectorAll('.otp-digit-input-bottom');
    const msgDiv = document.getElementById('authBottomOtpMsg');
    const btn = document.getElementById('btnBottomVerifyOtp');
    let otpCode = '';
    otpInputs.forEach(i => otpCode += i.value);

    if (otpCode.length < 6) {
      if (msgDiv) {
        msgDiv.innerText = 'Please enter all 6 digits.';
        msgDiv.style.display = 'block';
      }
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerText = 'VERIFYING...';
    }

    try {
      const res = await fetch('/api/v1/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: currentEmail, otp_code: otpCode })
      });
      const data = await res.json();

      if (res.ok && data.access_token) {
        localStorage.setItem('beacon_token', data.access_token);
        localStorage.setItem('beacon_user', JSON.stringify(data.user));
        updateAuthUI(data.user);
        alert(`Authenticated successfully! Welcome ${data.user.name} (${data.user.role})`);
      } else {
        if (msgDiv) {
          msgDiv.innerText = data.detail || 'Invalid or expired OTP code.';
          msgDiv.style.display = 'block';
        }
      }
    } catch (err) {
      if (msgDiv) {
        msgDiv.innerText = 'Verification failed. Connection error.';
        msgDiv.style.display = 'block';
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'VERIFY & AUTHENTICATE ➔';
      }
    }
  };

  function startOtpCountdown() {
    timerSeconds = 300;
    const timerSpan = document.getElementById('authBottomTimer');
    if (otpTimer) clearInterval(otpTimer);

    otpTimer = setInterval(() => {
      timerSeconds--;
      const mins = String(Math.floor(timerSeconds / 60)).padStart(2, '0');
      const secs = String(timerSeconds % 60).padStart(2, '0');
      if (timerSpan) timerSpan.innerText = `${mins}:${secs}`;

      if (timerSeconds <= 0) {
        clearInterval(otpTimer);
        const msgDiv = document.getElementById('authBottomOtpMsg');
        if (msgDiv) {
          msgDiv.innerText = 'OTP expired. Please request a new code.';
          msgDiv.style.display = 'block';
        }
      }
    }, 1000);
  }

  function checkExistingAuth() {
    const userJson = localStorage.getItem('beacon_user');
    if (userJson) {
      try {
        const user = JSON.parse(userJson);
        updateAuthUI(user);
      } catch (e) {}
    }
  }

  function updateAuthUI(user) {
    const btnNav = document.getElementById('navAuthBtn');
    if (btnNav) {
      btnNav.innerHTML = `👤 Logout (${user.name})`;
      btnNav.onclick = window.handleLogout;
      btnNav.style.background = 'rgba(239,68,68,0.2)';
      btnNav.style.color = 'var(--color-red)';
      btnNav.style.border = '1px solid var(--color-red)';
      btnNav.style.boxShadow = 'none';
    }
  }

  window.handleLogout = function () {
    localStorage.removeItem('beacon_token');
    localStorage.removeItem('beacon_user');
    const btnNav = document.getElementById('navAuthBtn');
    if (btnNav) {
      btnNav.innerHTML = `🔑 Login / Auth`;
      btnNav.onclick = window.scrollToAuthSection;
      btnNav.style.background = 'linear-gradient(135deg, var(--color-cyan) 0%, var(--color-green) 100%)';
      btnNav.style.color = 'var(--bg-gradient-bottom)';
      btnNav.style.border = 'none';
    }
  };
})();
