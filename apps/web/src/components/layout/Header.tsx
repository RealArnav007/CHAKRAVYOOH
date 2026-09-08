import React, { useState, useEffect } from 'react';
import { Radio, ShieldAlert, Cpu, Download, UserCheck, Activity } from 'lucide-react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { UserRole } from '../../types';

interface HeaderProps {
  onOpenDemoBar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenDemoBar }) => {
  const { session, setRole } = useAdminAuth();
  const [currentTime, setCurrentTime] = useState<string>('');
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-GB', { hour12: false }));
    }, 1000);
    setCurrentTime(new Date().toLocaleTimeString('en-GB', { hour12: false }));
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const handleBeforeInstall = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
  }, []);

  const handleInstallClick = () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then((choiceResult: any) => {
        if (choiceResult.outcome === 'accepted') {
          setDeferredPrompt(null);
        }
      });
    } else {
      alert('CHAKRAVYOOH Command Center PWA is already installed or ready to add to your desktop/home screen.');
    }
  };

  return (
    <header className="h-16 bg-slate-900/90 border-b border-slate-800 backdrop-blur-md sticky top-0 z-40 px-4 md:px-6 flex items-center justify-between">
      {/* Brand & Connection Status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3 cursor-pointer group" onClick={() => window.location.href = '/'} title="Return to Main Launch Page">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 via-red-500 to-amber-600 flex items-center justify-center shadow-lg shadow-red-950/50 ring-1 ring-red-400/30 group-hover:scale-105 transition-transform">
            <ShieldAlert className="w-6 h-6 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-wider text-slate-100 group-hover:text-blue-400 font-mono transition-colors">CHAKRAVYOOH <span className="text-blue-500 text-xs px-1.5 py-0.5 rounded bg-blue-500/10 border border-blue-500/20">3.0 PWA</span></span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-2 h-2 rounded-full bg-emerald-500 mr-1.5 animate-ping-slow"></span>
                LIVE COMMAND
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono hidden sm:block">AI Cyclone Intelligence • Resilient Operations Center</p>
          </div>
        </div>

        {/* Live Network Telemetry */}
        <div className="hidden lg:flex items-center space-x-3 pl-4 border-l border-slate-800 text-xs">
          <div className="flex items-center space-x-1.5 bg-slate-950/60 px-2.5 py-1.5 rounded-md border border-slate-800">
            <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span className="text-slate-400 font-mono">Mesh Peers:</span>
            <span className="text-cyan-300 font-mono font-bold">5 Active</span>
          </div>

          <div className="flex items-center space-x-1.5 bg-slate-950/60 px-2.5 py-1.5 rounded-md border border-slate-800">
            <Cpu className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-400 font-mono">Gateway:</span>
            <span className="text-amber-300 font-mono font-bold">Node P5 🌐</span>
          </div>

          <div className="flex items-center space-x-1.5 bg-slate-950/60 px-2.5 py-1.5 rounded-md border border-slate-800">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400 font-mono">Groq AI:</span>
            <span className="text-emerald-300 font-mono font-bold">Connected</span>
          </div>
        </div>
      </div>

      {/* Right Controls: Role Selector, Demo Simulator, Time */}
      <div className="flex items-center space-x-3">
        {/* Demo Simulator Launcher Button */}
        {onOpenDemoBar && (
          <button
            onClick={onOpenDemoBar}
            className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-red-600/30 to-amber-600/30 hover:from-red-600/50 hover:to-amber-600/50 border border-red-500/40 text-xs font-semibold text-amber-200 transition-all shadow-md"
          >
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>Launch Live 7-Stage Demo</span>
          </button>
        )}

        {/* PWA Install Button */}
        <button
          onClick={handleInstallClick}
          className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300 transition-colors"
          title="Install PWA Command Center app"
        >
          <Download className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden md:inline">Install PWA</span>
        </button>

        {/* RBAC Role Selector Dropdown */}
        <div className="flex items-center space-x-2 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <UserCheck className="w-4 h-4 text-indigo-400" />
          <div className="text-left">
            <select
              value={session.role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="bg-transparent text-xs font-bold text-slate-200 font-mono focus:outline-none cursor-pointer"
            >
              <option value="COMMANDER" className="bg-slate-900 text-amber-300">COMMANDER</option>
              <option value="RESPONDER" className="bg-slate-900 text-emerald-300">RESPONDER</option>
              <option value="ANALYST" className="bg-slate-900 text-cyan-300">ANALYST</option>
              <option value="SUPER_ADMIN" className="bg-slate-900 text-red-400">SUPER ADMIN</option>
              <option value="VIEWER" className="bg-slate-900 text-slate-400">VIEWER</option>
            </select>
          </div>
        </div>

        {/* Operational Clock */}
        <div className="hidden xl:block bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-right">
          <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">LOCAL TIME IST</p>
          <p className="text-xs font-mono font-bold text-cyan-400">{currentTime}</p>
        </div>
      </div>
    </header>
  );
};
