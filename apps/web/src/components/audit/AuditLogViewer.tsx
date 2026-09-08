import React from 'react';
import { ShieldCheck, Lock, UserCheck, CheckCircle2, AlertOctagon, Terminal } from 'lucide-react';
import { AuditEvent } from '../../types';
import { useAdminAuth } from '../../context/AdminAuthContext';

interface AuditProps {
  events: AuditEvent[];
}

export const AuditLogViewer: React.FC<AuditProps> = ({ events }) => {
  const { session } = useAdminAuth();

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <span>ENTERPRISE AUDIT & RBAC SECURITY PANEL</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono">Immutably logged officer dispatch actions, severity overrides, and security events</p>
        </div>

        <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
          Role Active: <span className="text-amber-400 font-bold">{session.role}</span>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <Terminal className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-100 font-mono tracking-wide uppercase">OFFICIAL AUDIT EVENT LOG STREAM</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 uppercase text-[10px]">
                <th className="py-2.5 px-3">Timestamp IST</th>
                <th className="py-2.5 px-3">Official User</th>
                <th className="py-2.5 px-3">Role</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Target Resource</th>
                <th className="py-2.5 px-3">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {events.map((evt) => (
                <tr key={evt.id} className="hover:bg-slate-850 transition-colors">
                  <td className="py-3 px-3 text-cyan-400 font-bold">{evt.timestamp}</td>
                  <td className="py-3 px-3 text-slate-200 font-semibold">{evt.userName}</td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                      {evt.role}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-amber-300 font-bold">{evt.action}</td>
                  <td className="py-3 px-3 text-slate-300">{evt.resourceName}</td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      {evt.result}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
