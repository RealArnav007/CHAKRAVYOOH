import React from 'react';
import { BarChart3, TrendingUp, AlertTriangle, Activity, ShieldCheck, MapPin } from 'lucide-react';
import { SeverityZone } from '../../types';

interface AnalyticsProps {
  zones: SeverityZone[];
}

export const ZoneAnalyticsEngine: React.FC<AnalyticsProps> = ({ zones }) => {
  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto">
      <div>
        <h2 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-amber-400" />
          <span>DYNAMIC SEVERITY ZONE ANALYTICS & TIMELINE ENGINE</span>
        </h2>
        <p className="text-xs text-slate-400 font-mono">Geographic report density, area expansion velocities, and severity progression metrics</p>
      </div>

      {/* Zone Cards & Expansion Timelines */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {zones.map((zone) => (
          <div key={zone.id} className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">{zone.code}</span>
                <h3 className="text-base font-bold text-slate-100 mt-1">{zone.name}</h3>
              </div>
              <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold ${
                zone.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                zone.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400' :
                'bg-yellow-500/20 text-yellow-400'
              }`}>
                {zone.severity}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono text-center">
              <div className="p-2 rounded bg-slate-950 border border-slate-800">
                <p className="text-[10px] text-slate-400">Total Reports</p>
                <p className="text-base font-bold text-cyan-400 mt-0.5">{zone.reportCount}</p>
              </div>
              <div className="p-2 rounded bg-slate-950 border border-slate-800">
                <p className="text-[10px] text-slate-400">Radius</p>
                <p className="text-base font-bold text-amber-400 mt-0.5">{zone.radiusMeters}m</p>
              </div>
            </div>

            {/* Dynamic Expansion Timeline */}
            <div className="space-y-2">
              <p className="text-[11px] font-mono font-bold text-slate-300 uppercase tracking-wider">EXPANSION TIMELINE PROGRESSION</p>
              <div className="space-y-1.5 font-mono text-xs">
                {zone.expansionHistory.map((step, idx) => (
                  <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-400">{step.timestamp} IST</span>
                    <span className="text-slate-200">Radius: {step.radius}m</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                      step.severity === 'CRITICAL' ? 'text-red-400 font-bold' :
                      step.severity === 'HIGH' ? 'text-amber-400' : 'text-yellow-400'
                    }`}>
                      {step.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
