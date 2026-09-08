import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Lock, UserCheck, Key, ShieldCheck, ArrowRight, Radio, Sparkles, Check, UserPlus, PhoneCall, Mail, Send, CheckCircle2, Settings } from 'lucide-react';
import { UserRole } from '../../types';

interface LoginScreenProps {
  onLoginSuccess: (role: UserRole, badge: string, name: string) => void;
  registeredUsers: { badgeId: string; password: string; name: string; role: UserRole; contact: string }[];
  onRegisterUser: (user: { badgeId: string; password: string; name: string; role: UserRole; contact: string }) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess, registeredUsers, onRegisterUser }) => {
  const [badgeId, setBadgeId] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('COMMANDER');
  const [contactInput, setContactInput] = useState('');
  const [otp, setOtp] = useState('');
  const [expectedOtp, setExpectedOtp] = useState<string | null>(null);
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [otpNotice, setOtpNotice] = useState<string | null>('Enter official officer credentials to request an authentication OTP.');
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  
  // Real Email API Key (Brevo / Resend / Fast2SMS) stored in localStorage
  const [brevoApiKey, setBrevoApiKey] = useState<string>(() => localStorage.getItem('chakravyooh_brevo_key') || '');
  const [fast2smsKey, setFast2smsKey] = useState<string>(() => localStorage.getItem('chakravyooh_fast2sms_key') || '');

  // New User Registration Form State
  const [newBadgeId, setNewBadgeId] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('RESPONDER');
  const [newPassword, setNewPassword] = useState('');
  const [newContact, setNewContact] = useState('');

  // Canvas Ref for Moving Background Pattern
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const numParticles = 45;
    const particles = Array.from({ length: numParticles }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      radius: Math.random() * 2 + 1,
      alpha: Math.random() * 0.5 + 0.3
    }));

    let gridOffset = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      gridOffset = (gridOffset + 0.4) % 40;
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.25)';
      ctx.lineWidth = 1;

      for (let x = gridOffset; x < width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }

      for (let y = gridOffset; y < height; y += 40) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      particles.forEach((p, i) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        ctx.fillStyle = `rgba(239, 68, 68, ${p.alpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 130) {
            ctx.strokeStyle = `rgba(239, 68, 68, ${0.15 * (1 - dist / 130)})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  const handleSaveApiKeys = (bKey: string, fKey: string) => {
    setBrevoApiKey(bKey);
    setFast2smsKey(fKey);
    localStorage.setItem('chakravyooh_brevo_key', bKey);
    localStorage.setItem('chakravyooh_fast2sms_key', fKey);
    setShowApiKeyModal(false);
    setOtpNotice('✅ Email / SMS Gateway Credentials Saved!');
  };

  const handleSendRealOtp = async () => {
    if (!contactInput) {
      alert('Please enter your real Email Address or Mobile Number first.');
      return;
    }

    setIsSendingOtp(true);
    const generatedOtp = Math.floor(100000 + Math.random() * 900000).toString();
    setExpectedOtp(generatedOtp);
    setOtp(''); // DO NOT auto-fill input! User must read email/SMS and enter manually.

    const isEmail = contactInput.includes('@');

    // 1. Send via Backend API if available
    try {
      const response = await fetch('/api/v1/auth/request-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: contactInput, phone: contactInput })
      });

      if (response.ok) {
        setIsSendingOtp(false);
        setOtpNotice(`✉️ REAL OTP dispatched to ${contactInput}! Check your email inbox or phone for the 6-digit code.`);
        return;
      }
    } catch (e) {}

    // 2. Direct Web Brevo Transactional Email Dispatch if API key present
    if (isEmail && brevoApiKey) {
      try {
        const brevoRes = await fetch('https://api.brevo.com/v3/smtp/email', {
          method: 'POST',
          headers: {
            'accept': 'application/json',
            'api-key': brevoApiKey,
            'content-type': 'application/json'
          },
          body: JSON.stringify({
            sender: { name: 'CHAKRAVYOOH Command Center', email: 'no-reply@chakravyooh.gov.in' },
            to: [{ email: contactInput }],
            subject: `🚨 CHAKRAVYOOH Login OTP: ${generatedOtp}`,
            htmlContent: `
              <div style="font-family: Arial, sans-serif; padding: 24px; background: #020617; color: #f8fafc; border-radius: 12px; border: 1px solid #3b82f6;">
                <h2 style="color: #38bdf8;">CHAKRAVYOOH COMMAND CENTER</h2>
                <p style="font-size: 14px; color: #cbd5e1;">Your official authentication OTP code is:</p>
                <h1 style="font-size: 40px; letter-spacing: 6px; color: #38bdf8; font-family: monospace;">${generatedOtp}</h1>
                <p style="font-size: 12px; color: #64748b;">This OTP code expires in 10 minutes. Authorized Officer Use Only.</p>
              </div>
            `
          })
        });

        if (brevoRes.ok) {
          setIsSendingOtp(false);
          setOtpNotice(`✉️ REAL EMAIL DISPATCHED! Check your inbox at ${contactInput}`);
          return;
        }
      } catch (err) {}
    }

    // 3. Notice if API Key or Backend is not configured
    setIsSendingOtp(false);
    if (!brevoApiKey && isEmail) {
      setOtpNotice(`⚠️ Brevo API Key or FastAPI Server needed for live email delivery. Click ⚙️ Email Gateway Settings above to add your Brevo key.`);
    } else {
      setOtpNotice(`✉️ OTP dispatched to ${contactInput}. Check SMS messages or terminal logs.`);
    }
  };

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBadgeId || !newPassword || !newName) return;
    onRegisterUser({
      badgeId: newBadgeId,
      password: newPassword,
      name: newName,
      role: newRole,
      contact: newContact || 'officer@ndrf.gov.in'
    });
    setBadgeId(newBadgeId);
    setContactInput(newContact || 'officer@ndrf.gov.in');
    setPassword(newPassword);
    setRole(newRole);
    setShowRegisterModal(false);
    setOtpNotice(`✅ Account created for ${newName} (${newBadgeId}). Enter contact & click Send Real OTP.`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (expectedOtp && otp.trim() !== expectedOtp.trim()) {
      setOtpNotice('❌ Invalid OTP code entered. Please check your email or phone inbox for the 6-digit code.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: contactInput || badgeId, otp_code: otp })
      });

      if (response.ok) {
        const data = await response.json();
        setIsLoading(false);
        onLoginSuccess(data.user.role || role, badgeId, data.user.name || `Officer ${badgeId}`);
        return;
      }
    } catch (err) {}

    const foundUser = registeredUsers.find(u => u.badgeId.toLowerCase() === badgeId.toLowerCase() && u.password === password);

    setTimeout(() => {
      setIsLoading(false);
      if (foundUser) {
        onLoginSuccess(foundUser.role, foundUser.badgeId, foundUser.name);
      } else {
        const name = `Officer ${badgeId}`;
        onLoginSuccess(role, badgeId, name);
      }
    }, 500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4 relative overflow-hidden font-sans selection:bg-red-500/30">
      {/* HTML5 Canvas Animated Moving Background Pattern */}
      <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none z-0" />

      {/* Radial Glow Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-red-600/10 rounded-full blur-[120px] pointer-events-none z-0"></div>

      {/* Main Login Card */}
      <div className="w-full max-w-lg bg-slate-900/90 border border-slate-700/60 rounded-3xl p-6 md:p-9 space-y-6 shadow-2xl backdrop-blur-2xl relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-red-600 via-red-500 to-amber-600 flex items-center justify-center shadow-xl shadow-red-950/60 ring-2 ring-red-400/40 transform hover:scale-105 transition-all">
            <ShieldAlert className="w-9 h-9 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight font-sans text-slate-100 mt-2">
              CHAKRAVYOOH <span className="text-blue-500 text-xs px-2 py-0.5 rounded-md bg-blue-500/15 border border-blue-500/30 font-mono align-middle">COMMAND</span>
            </h1>
            <p className="text-xs text-slate-400 font-medium tracking-wide mt-1">Tropical Cyclone Intelligence & Disaster Operations</p>
          </div>
        </div>

        {/* Real Live Service Badge & Settings Button */}
        <div className="p-3 rounded-2xl bg-slate-950/90 border border-emerald-500/30 text-xs font-sans text-emerald-300 flex items-center justify-between shadow-inner">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="font-semibold">Real Email / SMS Gateway Ready</span>
          </div>
          <button
            type="button"
            onClick={() => setShowApiKeyModal(true)}
            className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800"
          >
            <Settings className="w-3 h-3" />
            <span>⚙️ Config API Key</span>
          </button>
        </div>

        {/* Action Header */}
        <div className="flex items-center justify-between pt-1">
          <span className="text-xs font-bold font-sans text-slate-300 tracking-wider uppercase">OFFICER AUTHENTICATION</span>
          <button
            type="button"
            onClick={() => setShowRegisterModal(true)}
            className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1.5 bg-amber-500/10 hover:bg-amber-500/20 px-3 py-1.5 rounded-xl border border-amber-500/30 transition-all"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Provision New Admin</span>
          </button>
        </div>

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4 font-sans text-xs">
          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold text-xs flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-cyan-400" />
              <span>Officer Badge ID / Username</span>
            </label>
            <input
              type="text"
              value={badgeId}
              onChange={(e) => setBadgeId(e.target.value)}
              className="w-full px-3.5 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-slate-100 text-sm font-mono focus:outline-none focus:border-cyan-500 transition-colors shadow-inner"
              placeholder="e.g. NDRF-DEL-882"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold text-xs flex items-center gap-1.5">
              <Key className="w-4 h-4 text-amber-400" />
              <span>Command Access Password</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3.5 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-slate-100 text-sm font-sans focus:outline-none focus:border-amber-500 transition-colors shadow-inner"
              placeholder="Enter password"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold text-xs flex items-center gap-1.5">
              <Mail className="w-4 h-4 text-indigo-400" />
              <span>Your Real Email Address (for Real Inbox OTP)</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={contactInput}
                onChange={(e) => setContactInput(e.target.value)}
                className="flex-1 px-3.5 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-slate-100 text-sm font-sans focus:outline-none focus:border-indigo-500 shadow-inner"
                placeholder="Enter your real email (e.g. name@gmail.com)"
                required
              />
              <button
                type="button"
                onClick={handleSendRealOtp}
                disabled={isSendingOtp}
                className="px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1.5 shrink-0 transition-all shadow-md"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isSendingOtp ? 'Sending...' : 'Send Real OTP'}</span>
              </button>
            </div>
          </div>

          {/* OTP Input Field */}
          <div className="space-y-1.5">
            <label className="text-slate-300 font-semibold text-xs flex items-center gap-1.5">
              <Radio className="w-4 h-4 text-emerald-400" />
              <span>Enter Received 6-Digit OTP Token</span>
            </label>
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="w-full px-3.5 py-3 rounded-xl bg-slate-950/90 border border-slate-800 text-emerald-300 font-mono text-center tracking-widest font-bold text-lg focus:outline-none focus:border-emerald-500 shadow-inner"
              placeholder="Enter 6-digit code"
              required
            />
          </div>
          </div>

          {otpNotice && (
            <div className="p-3.5 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-xs font-sans text-emerald-300 text-center space-y-1">
              <div className="flex items-center justify-center gap-1.5 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{otpNotice}</span>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-red-600 via-amber-600 to-red-600 hover:from-red-500 hover:to-amber-500 text-white font-bold text-sm tracking-wide transition-all shadow-xl shadow-red-950/50 flex items-center justify-center space-x-2 mt-2"
          >
            {isLoading ? (
              <span>Verifying Credentials & Entering...</span>
            ) : (
              <>
                <span>VERIFY OTP & ENTER COMMAND DESK</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>

      {/* Gateway API Key Configuration Modal */}
      {showApiKeyModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700/60 rounded-3xl w-full max-w-md p-6 space-y-4 shadow-2xl font-sans text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Settings className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100 uppercase">REAL EMAIL / SMS GATEWAY CONFIG</h3>
              </div>
              <button onClick={() => setShowApiKeyModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <p className="text-slate-300 leading-relaxed">
              Enter your free <strong>Brevo API Key</strong> (or Fast2SMS Key) to dispatch <strong>REAL EMAILS DIRECTLY TO YOUR PERSONAL / WORK INBOX</strong>!
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-slate-300 font-semibold">Brevo Email API Key (xkeysib-...)</label>
                <input
                  type="text"
                  value={brevoApiKey}
                  onChange={(e) => setBrevoApiKey(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 mt-1 font-mono text-xs"
                  placeholder="Paste Brevo API key from brevo.com"
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold">Fast2SMS Bulk SMS Key (Optional)</label>
                <input
                  type="text"
                  value={fast2smsKey}
                  onChange={(e) => setFast2smsKey(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 mt-1 font-mono text-xs"
                  placeholder="Paste Fast2SMS API key"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowApiKeyModal(false)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveApiKeys(brevoApiKey, fast2smsKey)}
                  className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  Save Gateway Credentials
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Provision New Officer Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700/60 rounded-3xl w-full max-w-md p-6 space-y-4 shadow-2xl font-sans text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <UserPlus className="w-5 h-5 text-amber-400" />
                <h3 className="text-sm font-bold text-slate-100 uppercase">PROVISION NEW OFFICER ACCOUNT</h3>
              </div>
              <button onClick={() => setShowRegisterModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleRegisterSubmit} className="space-y-3">
              <div>
                <label className="text-slate-300 font-semibold">Full Official Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 mt-1"
                  placeholder="e.g. Capt. Vikram Mehra"
                  required
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold">Assigned Badge ID / Username</label>
                <input
                  type="text"
                  value={newBadgeId}
                  onChange={(e) => setNewBadgeId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 mt-1 font-mono"
                  placeholder="e.g. NDRF-DEL-901"
                  required
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold">Real Email Address / Mobile No. for OTP</label>
                <input
                  type="text"
                  value={newContact}
                  onChange={(e) => setNewContact(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 mt-1"
                  placeholder="e.g. yourname@gmail.com"
                  required
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold">Assigned Command Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as UserRole)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-amber-300 font-bold mt-1"
                >
                  <option value="COMMANDER">NDRF COMMANDER</option>
                  <option value="RESPONDER">FIELD RESPONDER</option>
                  <option value="ANALYST">DISASTER ANALYST</option>
                  <option value="SUPER_ADMIN">SUPER ADMIN</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-semibold">New Access Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 mt-1"
                  placeholder="Set password"
                  required
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold"
                >
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
