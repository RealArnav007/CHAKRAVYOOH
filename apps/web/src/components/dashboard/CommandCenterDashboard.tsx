import React from 'react';
import { AlertCircle, ShieldAlert, Zap, Truck, ArrowUpRight, Cpu, Radio, Sparkles, MapPin } from 'lucide-react';
import { Incident } from '../../types';

interface DashboardProps {
  incidents: Incident[];
  onSelectIncident: (incident: Incident) => void;
  onNavigateToMap: () => void;
  onNavigateToDispatch: () => void;
}

export const CommandCenterDashboard: React.FC<DashboardProps> = ({
  incidents,
  onSelectIncident,
  onNavigateToMap,
  onNavigateToDispatch
}) => {
  const criticalCount = incidents.filter(i => i.severity === 'CRITICAL').length;
  const highCount = incidents.filter(i => i.severity === 'HIGH').length;
  const activeCount = incidents.filter(i => i.status !== 'RESOLVED').length;
  const dispatchedCount = incidents.filter(i => i.status === 'DISPATCHING' || i.status === 'IN_PROGRESS').length;

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Banner Alert */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-red-950/80 via-slate-900 to-amber-950/60 border border-red-500/40 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-red-600/30 border border-red-500/50 text-red-400">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>PRIORITY RED ALERT — SECTOR 14 STRUCTURAL EMERGENCY</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-red-500/20 text-red-300 border border-red-500/30">SCORE: 97/100</span>
            </h2>
            <p className="text-xs text-slate-300">18 corroborating victim distress reports routed via 5-hop offline mesh (P1→P5). NDRF Heavy Rescue dispatched.</p>
          </div>
        </div>

        <button
          onClick={() => onSelectIncident(incidents[0])}
          className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-md shrink-0"
        >
          Inspect Incident #104 & AI Breakdown →
        </button>
      </div>

      {/* System Degradation & Resilience Status Banner (Requirement Item 39) */}
      <div className="p-3 rounded-xl bg-slate-950 border border-cyan-500/30 text-xs font-mono flex flex-wrap items-center justify-between gap-2 text-slate-300">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-bold text-cyan-400">SYSTEM RESILIENCE & DEGRADATION MATRIX:</span>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
            🤖 AI Fallback: Rule-Based Active
          </span>
          <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
            ⚡ Realtime Layer: Auto-Reconnect Enabled
          </span>
          <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            📡 Physical Layer: BLE Mesh Fallback Ready
          </span>
          <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
            📦 Gateway Outage: Store-and-Forward Upload Active
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Critical */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-red-500/30 backdrop-blur-md relative overflow-hidden group hover:border-red-500/60 transition-all">
          <div className="absolute top-0 right-0 w-24 h-24 bg-red-600/10 rounded-full blur-2xl group-hover:bg-red-600/20 transition-all"></div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-red-400 font-semibold">CRITICAL ALERTS</span>
            <AlertCircle className="w-4 h-4 text-red-500" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-red-400 mt-2">{criticalCount}</p>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Immediate Life Threat (Score 90+)</p>
        </div>

        {/* High */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-amber-500/30 backdrop-blur-md relative overflow-hidden group hover:border-amber-500/60 transition-all">
          <div className="absolute top-0 right-0 w-24 h-24 bg-amber-600/10 rounded-full blur-2xl group-hover:bg-amber-600/20 transition-all"></div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-amber-400 font-semibold">HIGH PRIORITY</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-amber-400 mt-2">{highCount}</p>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Substation Fire & Smoke (Score 75-89)</p>
        </div>

        {/* Active Incidents */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/30 backdrop-blur-md relative overflow-hidden group hover:border-cyan-500/60 transition-all">
          <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-600/10 rounded-full blur-2xl group-hover:bg-cyan-600/20 transition-all"></div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-cyan-400 font-semibold">ACTIVE INCIDENTS</span>
            <Radio className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-cyan-300 mt-2">{activeCount}</p>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">Across 3 Dynamic Severity Zones</p>
        </div>

        {/* Dispatched Units */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-emerald-500/30 backdrop-blur-md relative overflow-hidden group hover:border-emerald-500/60 transition-all">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-600/10 rounded-full blur-2xl group-hover:bg-emerald-600/20 transition-all"></div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-400 font-semibold">DISPATCHED UNITS</span>
            <Truck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-emerald-400 mt-2">{dispatchedCount}</p>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">NDRF, Fire & Medical Units On Scene</p>
        </div>
      </div>

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Priority Incident Queue (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-100 font-mono tracking-wide uppercase">AI PRIORITY TRIAGE QUEUE</h3>
              <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-mono">Sorted by Dynamic Score</span>
            </div>
            <span className="text-xs text-slate-400 font-mono">Groq AI Llama-3.3 Operational</span>
          </div>

          <div className="space-y-3">
            {incidents.map((incident) => {
              const isCritical = incident.severity === 'CRITICAL';
              const isHigh = incident.severity === 'HIGH';
              return (
                <div
                  key={incident.id}
                  onClick={() => onSelectIncident(incident)}
                  className={`p-4 rounded-xl bg-slate-900/90 border transition-all cursor-pointer ${
                    isCritical
                      ? 'border-red-500/40 hover:border-red-500/80 shadow-lg shadow-red-950/20'
                      : isHigh
                      ? 'border-amber-500/40 hover:border-amber-500/80'
                      : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                    <div className="flex items-center space-x-3">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-extrabold ${
                        isCritical ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                        isHigh ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                        'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40'
                      }`}>
                        SCORE: {incident.aiBreakdown.finalPriorityScore}
                      </span>
                      <div>
                        <h4 className="text-sm font-bold text-slate-100">{incident.title}</h4>
                        <p className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                          <MapPin className="w-3 h-3 text-slate-500" />
                          <span>{incident.location.sector}</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                        {incident.corroborationCount} Corroborating Reports
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                        incident.status === 'DISPATCHING' ? 'bg-amber-500/20 text-amber-300' :
                        incident.status === 'IN_PROGRESS' ? 'bg-emerald-500/20 text-emerald-300' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {incident.status}
                      </span>
                    </div>
                  </div>

                  {/* AI Summary Banner */}
                  <div className="mt-3 p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 flex items-start space-x-2">
                    <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-slate-200">AI Triage Summary: </span>
                      <span>{incident.aiBreakdown.groqSummary}</span>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t border-slate-800/80">
                    <div className="flex items-center space-x-4 font-mono text-[11px] text-slate-400">
                      <span>Regex: {incident.aiBreakdown.regexScore}%</span>
                      <span>Groq: {incident.aiBreakdown.groqScore}%</span>
                      <span>Corroboration: +{incident.aiBreakdown.corroborationBonus}</span>
                    </div>
                    <span className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 text-xs">
                      View Packet Journey & AI Formula <ArrowUpRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Live Map Mini & Activity Stream (1 Col) */}
        <div className="space-y-6">
          {/* Mini Operations Map Preview */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 font-mono tracking-wider uppercase">OPERATIONS MAP PREVIEW</h3>
              <button
                onClick={onNavigateToMap}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
              >
                Expand Map →
              </button>
            </div>

            <div
              onClick={onNavigateToMap}
              className="h-44 rounded-lg bg-slate-950 border border-slate-800 relative overflow-hidden cursor-pointer group flex items-center justify-center"
            >
              {/* Decorative Map Grid & Dynamic Zone Circles */}
              <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40"></div>

              {/* Dynamic Zone Alpha (Critical) */}
              <div className="absolute w-28 h-28 rounded-full bg-red-500/20 border border-red-500/50 animate-ping-slow flex items-center justify-center">
                <span className="text-[9px] font-mono text-red-300 font-bold">ZONE A (97)</span>
              </div>

              {/* Dynamic Zone Bravo (High) */}
              <div className="absolute top-4 right-6 w-16 h-16 rounded-full bg-amber-500/20 border border-amber-500/50 flex items-center justify-center">
                <span className="text-[8px] font-mono text-amber-300">ZONE B</span>
              </div>

              <div className="relative z-10 bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 font-mono shadow-lg group-hover:border-cyan-500 transition-colors">
                📍 Sector 14 Emergency Polygon Active
              </div>
            </div>
          </div>

          {/* Real-time Packet Ingestion Stream */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-slate-200 font-mono tracking-wider uppercase">LIVE MESH PACKET STREAM</h3>
              </div>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            </div>

            <div className="space-y-2 font-mono text-[11px]">
              <div className="p-2 rounded bg-slate-950 border border-slate-800/80 text-slate-300 space-y-0.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-cyan-400 font-bold">pkt-9981-a1</span>
                  <span>08:41:31 IST</span>
                </div>
                <p className="text-slate-200 text-xs truncate">"4 people trapped inside basement..."</p>
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                  <span>Hops: P1→P2→P3→P4→P5</span>
                  <span className="text-emerald-400 font-bold">Gateway Upload OK</span>
                </div>
              </div>

              <div className="p-2 rounded bg-slate-950 border border-slate-800/80 text-slate-300 space-y-0.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-cyan-400 font-bold">pkt-9982-b2</span>
                  <span>08:42:38 IST</span>
                </div>
                <p className="text-slate-200 text-xs truncate">"Heavy dust cloud, building floor 3..."</p>
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                  <span>Hops: P1→P4→P5</span>
                  <span className="text-emerald-400 font-bold">Dedup Verified</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
