import React, { useState } from 'react';
import { Layers, ShieldAlert, Truck, Radio, Eye, RefreshCw, Navigation } from 'lucide-react';
import { Incident, SeverityZone, ResourceUnit } from '../../types';

interface MapProps {
  incidents: Incident[];
  zones: SeverityZone[];
  resources: ResourceUnit[];
  onSelectIncident: (incident: Incident) => void;
}

export const InteractiveOperationsMap: React.FC<MapProps> = ({
  incidents,
  zones,
  resources,
  onSelectIncident
}) => {
  const [showZones, setShowZones] = useState(true);
  const [showIncidents, setShowIncidents] = useState(true);
  const [showResources, setShowResources] = useState(true);
  const [showMeshHops, setShowMeshHops] = useState(true);
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH'>('ALL');

  const filteredIncidents = incidents.filter(inc => {
    if (activeFilter === 'CRITICAL') return inc.severity === 'CRITICAL';
    if (activeFilter === 'HIGH') return inc.severity === 'HIGH' || inc.severity === 'CRITICAL';
    return true;
  });

  return (
    <div className="p-4 md:p-6 space-y-4 max-w-[1600px] mx-auto h-[calc(100vh-5rem)] flex flex-col">
      {/* Map Control Bar */}
      <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center space-x-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-bold text-slate-100 font-mono tracking-wider uppercase">DYNAMIC DISASTER OPERATIONS MAP</h2>
        </div>

        {/* Filter & Layer Toggles */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveFilter('ALL')}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${activeFilter === 'ALL' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              ALL ZONES
            </button>
            <button
              onClick={() => setActiveFilter('CRITICAL')}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${activeFilter === 'CRITICAL' ? 'bg-red-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              🔴 CRITICAL ONLY
            </button>
          </div>

          <button
            onClick={() => setShowZones(!showZones)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center space-x-1.5 transition-colors ${
              showZones ? 'bg-red-500/20 text-red-300 border-red-500/40' : 'bg-slate-950 text-slate-500 border-slate-800'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Zones ({zones.length})</span>
          </button>

          <button
            onClick={() => setShowResources(!showResources)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center space-x-1.5 transition-colors ${
              showResources ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-slate-950 text-slate-500 border-slate-800'
            }`}
          >
            <Truck className="w-3.5 h-3.5" />
            <span>Fleet ({resources.length})</span>
          </button>

          <button
            onClick={() => setShowMeshHops(!showMeshHops)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-mono flex items-center space-x-1.5 transition-colors ${
              showMeshHops ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' : 'bg-slate-950 text-slate-500 border-slate-800'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Mesh Topology (P1→P5)</span>
          </button>
        </div>
      </div>

      {/* Main Map Canvas Area */}
      <div className="flex-1 rounded-2xl bg-slate-950 border border-slate-800 relative overflow-hidden flex items-center justify-center shadow-2xl">
        {/* Background Grid Pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(#334155_1px,transparent_1px)] [background-size:24px_24px] opacity-40"></div>

        {/* Radar Sweep Effect */}
        <div className="absolute w-[600px] h-[600px] rounded-full border border-slate-800/40 pointer-events-none flex items-center justify-center">
          <div className="w-[400px] h-[400px] rounded-full border border-slate-800/60 flex items-center justify-center">
            <div className="w-[200px] h-[200px] rounded-full border border-slate-800"></div>
          </div>
        </div>

        {/* Layer 1: Dynamic Severity Zones */}
        {showZones && (
          <>
            {/* Zone Alpha — Sector 14 Critical Zone */}
            <div className="absolute top-[35%] left-[40%] transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
              <div className="w-80 h-80 rounded-full bg-red-600/15 border-2 border-red-500/60 animate-pulse flex items-center justify-center relative shadow-[0_0_50px_rgba(239,68,68,0.25)]">
                <div className="w-56 h-56 rounded-full bg-red-500/10 border border-red-400/40 animate-ping-slow"></div>
                <span className="absolute top-4 px-2 py-0.5 rounded bg-red-950/90 border border-red-500 text-[10px] font-mono font-bold text-red-300 shadow">
                  🔴 ZONE A: SECTOR 14 CRITICAL (850m • 18 Reports)
                </span>
              </div>
            </div>

            {/* Zone Bravo — Sector 19 High Zone */}
            <div className="absolute top-[25%] right-[25%] transform translate-x-1/2 -translate-y-1/2 flex flex-col items-center">
              <div className="w-48 h-48 rounded-full bg-amber-600/15 border-2 border-amber-500/60 flex items-center justify-center relative">
                <span className="absolute top-2 px-2 py-0.5 rounded bg-amber-950/90 border border-amber-500 text-[9px] font-mono text-amber-300">
                  🟠 ZONE B: SECTOR 19 HIGH (450m)
                </span>
              </div>
            </div>
          </>
        )}

        {/* Layer 2: Mesh Hop Link Lines Overlay */}
        {showMeshHops && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {/* Link from P1 to P2 */}
            <line x1="32%" y1="42%" x2="38%" y2="38%" stroke="#06b6d4" strokeWidth="2" strokeDasharray="4" className="animate-pulse" />
            {/* Link from P2 to P3 */}
            <line x1="38%" y1="38%" x2="44%" y2="32%" stroke="#06b6d4" strokeWidth="2" strokeDasharray="4" />
            {/* Link from P3 to P4 */}
            <line x1="44%" y1="32%" x2="48%" y2="28%" stroke="#06b6d4" strokeWidth="2" strokeDasharray="4" />
            {/* Link from P4 to P5 Gateway */}
            <line x1="48%" y1="28%" x2="55%" y2="22%" stroke="#10b981" strokeWidth="3" />
          </svg>
        )}

        {/* Layer 3: Incident Markers */}
        {showIncidents && filteredIncidents.map((incident) => {
          const isCritical = incident.severity === 'CRITICAL';
          return (
            <div
              key={incident.id}
              onClick={() => onSelectIncident(incident)}
              className={`absolute cursor-pointer transition-all transform hover:scale-125 z-30 ${
                incident.id === 'inc-104' ? 'top-[35%] left-[40%]' :
                incident.id === 'inc-105' ? 'top-[25%] right-[25%]' :
                'bottom-[25%] left-[30%]'
              }`}
            >
              <div className={`p-2.5 rounded-full border-2 flex items-center justify-center shadow-xl ${
                isCritical ? 'bg-red-600 border-white text-white animate-bounce' : 'bg-amber-600 border-white text-white'
              }`}>
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div className="mt-1 px-2 py-1 rounded bg-slate-900/90 border border-slate-700 text-[10px] font-mono font-bold text-slate-100 shadow whitespace-nowrap text-center">
                {incident.code}: {incident.title}
                <div className="text-red-400 font-extrabold">SCORE: {incident.aiBreakdown.finalPriorityScore}</div>
              </div>
            </div>
          );
        })}

        {/* Layer 4: Fleet Resource Unit Markers */}
        {showResources && resources.map((res) => (
          <div
            key={res.id}
            className={`absolute z-20 transform hover:scale-110 transition-all ${
              res.id === 'res-01' ? 'top-[42%] left-[45%]' :
              res.id === 'res-03' ? 'top-[36%] left-[38%]' :
              'top-[28%] right-[22%]'
            }`}
          >
            <div className="p-2 rounded-lg bg-slate-900 border border-emerald-500 text-emerald-400 flex items-center space-x-1.5 shadow-lg">
              <Truck className="w-4 h-4" />
              <span className="text-[10px] font-mono font-bold text-emerald-300">{res.callsign}</span>
            </div>
          </div>
        ))}

        {/* Map Legend Overlay */}
        <div className="absolute bottom-4 left-4 p-3 rounded-xl bg-slate-900/95 border border-slate-800 text-xs font-mono space-y-1.5 z-40 backdrop-blur-md">
          <p className="font-bold text-slate-300 text-[10px] uppercase tracking-wider mb-1">MAP LEGEND</p>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
            <span className="text-slate-300">🔴 Critical Zone (Score 90+)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-amber-500"></span>
            <span className="text-slate-300">🟠 High Risk Zone</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3.5 h-0.5 bg-cyan-400 border-dashed"></span>
            <span className="text-slate-300">Mesh Hop Routes (P1→P5)</span>
          </div>
          <div className="flex items-center space-x-2">
            <Truck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-300">Dispatched Rescue Fleet</span>
          </div>
        </div>
      </div>
    </div>
  );
};
