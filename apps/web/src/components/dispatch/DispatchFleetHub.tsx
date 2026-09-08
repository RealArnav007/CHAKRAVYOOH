import React from 'react';
import { Truck, AlertCircle, CheckCircle2, Navigation, Clock, UserCheck } from 'lucide-react';
import { ResourceUnit, Incident } from '../../types';
import { useAdminAuth } from '../../context/AdminAuthContext';

interface DispatchProps {
  resources: ResourceUnit[];
  incidents: Incident[];
  onUpdateResourceStatus: (resourceId: string, status: ResourceUnit['status']) => void;
  onAssignResource: (resourceId: string, incidentId: string) => void;
}

export const DispatchFleetHub: React.FC<DispatchProps> = ({
  resources,
  incidents,
  onUpdateResourceStatus,
  onAssignResource
}) => {
  const { hasPermission } = useAdminAuth();

  const availableCount = resources.filter(r => r.status === 'AVAILABLE').length;
  const assignedCount = resources.filter(r => r.status !== 'AVAILABLE' && r.status !== 'UNAVAILABLE').length;

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
            <Truck className="w-6 h-6 text-emerald-400" />
            <span>DISPATCH & EMERGENCY FLEET HUB</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono">Resource allocation, unit status telemetry, and incident response tracking</p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
            Available Fleet: {availableCount}
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 font-bold">
            Deployed Fleet: {assignedCount}
          </div>
        </div>
      </div>

      {/* Fleet Resource Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {resources.map((res) => {
          const isDeployed = res.status !== 'AVAILABLE' && res.status !== 'UNAVAILABLE';
          return (
            <div
              key={res.id}
              className={`p-4 rounded-xl bg-slate-900/90 border transition-all space-y-3 ${
                res.status === 'ON_SCENE' ? 'border-emerald-500/50 shadow-lg shadow-emerald-950/20' :
                isDeployed ? 'border-amber-500/40' :
                'border-slate-800'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      res.type === 'RESCUE' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                      res.type === 'AMBULANCE' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                      'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                    }`}>
                      {res.type}
                    </span>
                    <span className="text-xs font-mono text-slate-400">{res.crewCount} Personnel</span>
                  </div>
                  <h3 className="text-base font-bold text-slate-100 mt-1">{res.callsign}</h3>
                </div>

                <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold ${
                  res.status === 'AVAILABLE' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
                  res.status === 'ON_SCENE' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' :
                  'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                }`}>
                  {res.status}
                </span>
              </div>

              {/* Assignment Details */}
              {res.assignedIncidentCode ? (
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between text-slate-300 font-mono">
                    <span>Assigned Incident:</span>
                    <span className="text-red-400 font-bold">{res.assignedIncidentCode}</span>
                  </div>
                  {res.etaMinutes !== undefined && (
                    <div className="flex items-center justify-between text-slate-400 font-mono text-[11px]">
                      <span>ETA to Site:</span>
                      <span className="text-amber-300 font-bold">{res.etaMinutes === 0 ? 'ON SITE NOW' : `${res.etaMinutes} min`}</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-500 font-mono">
                  Ready for Dispatch Assignment
                </div>
              )}

              {/* Status Update Actions */}
              {hasPermission('resource.update') && (
                <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center gap-1.5">
                  {res.status === 'DISPATCHED' && (
                    <button
                      onClick={() => onUpdateResourceStatus(res.id, 'EN_ROUTE')}
                      className="px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold"
                    >
                      Set En Route
                    </button>
                  )}
                  {res.status === 'EN_ROUTE' && (
                    <button
                      onClick={() => onUpdateResourceStatus(res.id, 'ON_SCENE')}
                      className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold"
                    >
                      Set On Scene
                    </button>
                  )}
                  {res.status === 'ON_SCENE' && (
                    <button
                      onClick={() => onUpdateResourceStatus(res.id, 'AVAILABLE')}
                      className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
                    >
                      Release Unit
                    </button>
                  )}
                  {res.status === 'AVAILABLE' && incidents.length > 0 && (
                    <button
                      onClick={() => onAssignResource(res.id, incidents[0].id)}
                      className="px-2.5 py-1 rounded bg-red-600 hover:bg-red-500 text-white text-xs font-semibold"
                    >
                      Assign to INC-104
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
