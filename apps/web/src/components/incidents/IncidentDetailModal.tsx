import React from 'react';
import { X, ShieldAlert, Cpu, Sparkles, Radio, CheckCircle2, ArrowRight, MapPin, Truck, AlertTriangle, Layers, UserCheck, ShieldCheck, Tag, LifeBuoy } from 'lucide-react';
import { Incident } from '../../types';
import { useAdminAuth } from '../../context/AdminAuthContext';

interface IncidentDetailModalProps {
  incident: Incident | null;
  onClose: () => void;
  onDispatchResource: (incidentId: string, resourceType: string) => void;
  onResolveIncident: (incidentId: string) => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incident,
  onClose,
  onDispatchResource,
  onResolveIncident
}) => {
  const { hasPermission } = useAdminAuth();

  if (!incident) return null;

  const isCritical = incident.severity === 'CRITICAL';
  const scoreV2 = incident.aiScoreV2;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[92vh] overflow-y-auto shadow-2xl flex flex-col">
        {/* Modal Header */}
        <div className="p-4 md:p-6 border-b border-slate-800 flex items-start justify-between bg-slate-950/80 sticky top-0 z-20">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-xl ${isCritical ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-amber-500/20 text-amber-400'}`}>
              <ShieldAlert className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-mono font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">{incident.code}</span>
                <span className="text-xs font-mono text-slate-400">{incident.createdAt} IST</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  incident.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-amber-500/20 text-amber-400'
                }`}>
                  🔴 {incident.severity} (SCORE: {scoreV2.priority}/100)
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  Schema v{scoreV2.schema_version}
                </span>

                {/* Commander Review Badge */}
                {scoreV2.needs_human_review && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                    ⚠️ Needs Commander Review
                  </span>
                )}

                {/* Prompt Injection Shield Badge */}
                {scoreV2.injection_suspected && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-950 text-red-300 border border-red-500">
                    🛡️ Prompt Injection Shielded
                  </span>
                )}
              </div>
              <h2 className="text-lg md:text-xl font-extrabold text-slate-100 mt-1">{incident.title}</h2>
              <p className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                <span>{incident.location.address} ({incident.location.sector})</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 md:p-6 space-y-6">
          {/* Tactical Briefing Headline Banner */}
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-red-950/60 via-slate-900 to-amber-950/60 border border-red-500/30 flex items-start space-x-3">
            <Sparkles className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-mono font-bold text-amber-300 uppercase tracking-wider">COMMANDER TACTICAL BRIEFING (1-LINE AI HEADLINE)</p>
              <p className="text-sm font-bold text-slate-100 mt-0.5">{scoreV2.briefing.headline}</p>
            </div>
          </div>

          {/* AI Formula & Telemetry Breakdown */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100 font-mono tracking-wide uppercase">SCORE RESULT V2.0.0 INTELLIGENCE PIPELINE</h3>
              </div>
              <span className="text-xs font-mono text-cyan-300">Confidence: {(scoreV2.confidence * 100).toFixed(0)}%</span>
            </div>

            {/* Formula Score Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 font-mono text-center text-xs">
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <p className="text-[10px] text-slate-400">Regex Score</p>
                <p className="text-sm font-bold text-cyan-400 mt-0.5">{scoreV2.regexScore}%</p>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <p className="text-[10px] text-slate-400">Groq LLM Score</p>
                <p className="text-sm font-bold text-amber-400 mt-0.5">{scoreV2.groqScore}%</p>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <p className="text-[10px] text-slate-400">Corroboration</p>
                <p className="text-sm font-bold text-emerald-400 mt-0.5">+{scoreV2.corroborationBonus}</p>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <p className="text-[10px] text-slate-400">Location Density</p>
                <p className="text-sm font-bold text-indigo-400 mt-0.5">+{scoreV2.locationBonus}</p>
              </div>
              <div className="p-2 rounded bg-red-950/40 border border-red-500/50 col-span-2 sm:col-span-1">
                <p className="text-[10px] text-red-300 font-bold">Final Priority</p>
                <p className="text-sm font-extrabold text-red-400 mt-0.5">{scoreV2.priority}</p>
              </div>
            </div>

            {/* Extracted Entities Chips Grid */}
            {scoreV2.entities && (
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <p className="text-[10px] font-mono uppercase text-slate-400 tracking-wider">EXTRACTED STRUCTURED ENTITIES (v2.0.0)</p>
                <div className="flex flex-wrap gap-2 text-xs font-mono">
                  {scoreV2.entities.people_count !== undefined && (
                    <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200">
                      👥 Victims Count: <strong className="text-amber-300">{scoreV2.entities.people_count}</strong>
                    </span>
                  )}
                  {scoreV2.entities.mobility && (
                    <span className="px-2.5 py-1 rounded bg-red-950/40 border border-red-500/40 text-red-300 font-bold">
                      🔒 Mobility: {scoreV2.entities.mobility.toUpperCase()}
                    </span>
                  )}
                  {scoreV2.entities.vulnerable?.map((v, i) => (
                    <span key={i} className="px-2.5 py-1 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold">
                      ⚠️ Vulnerable: {v}
                    </span>
                  ))}
                  {scoreV2.entities.hazards?.map((h, i) => (
                    <span key={i} className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300">
                      🔥 Hazard: {h}
                    </span>
                  ))}
                  {scoreV2.entities.injuries?.map((inj, i) => (
                    <span key={i} className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300">
                      🚑 Injury: {inj}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Incident Correlation & Cluster Hint */}
            {scoreV2.correlation && scoreV2.correlation.cluster_hint && (
              <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-500/30 text-xs font-mono flex items-center justify-between text-indigo-300">
                <span>INCIDENT CLUSTER CORRELATION: {scoreV2.correlation.cluster_hint}</span>
                <span className="font-bold">Similarity: {((scoreV2.correlation.similarity || 0) * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

          {/* Mesh Packet Transit Journey (P1 -> P5) */}
          {incident.reports.length > 0 && incident.reports[0].hopsJourney && (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <Radio className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-sm font-bold text-slate-100 font-mono tracking-wide uppercase">MESH PACKET TRANSIT ROUTE (P1 → P5)</h3>
                </div>
                <span className="text-xs font-mono text-cyan-300">Packet ID: {incident.reports[0].packetId}</span>
              </div>

              <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-2 py-2">
                {incident.reports[0].hopsJourney.map((hop, index) => {
                  const isGateway = hop.isGateway;
                  const isOrigin = hop.hopNumber === 1;
                  return (
                    <React.Fragment key={hop.nodeId}>
                      <div className={`p-3 rounded-xl border flex-1 text-center font-mono space-y-1 ${
                        isOrigin ? 'bg-red-950/40 border-red-500/50 text-red-200' :
                        isGateway ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200' :
                        'bg-slate-900 border-slate-800 text-slate-300'
                      }`}>
                        <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                          <span>HOP #{hop.hopNumber}</span>
                          <span>{hop.transport}</span>
                        </div>
                        <p className="text-xs font-bold truncate">{hop.nodeName}</p>
                        <div className="flex items-center justify-center space-x-2 text-[10px] text-slate-400 pt-1">
                          <span>RSSI: {hop.rssi}dBm</span>
                          <span>Bat: {hop.battery}%</span>
                        </div>
                        {isGateway && <span className="inline-block mt-1 px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[9px] font-bold">GATEWAY UPLOAD</span>}
                      </div>

                      {index < incident.reports[0].hopsJourney.length - 1 && (
                        <div className="flex md:flex-col items-center justify-center text-cyan-500 py-1">
                          <ArrowRight className="w-4 h-4 md:rotate-0 rotate-90" />
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          )}

          {/* AI Transparency Box: Why is this critical? */}
          <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/40 space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-extrabold text-cyan-400 font-sans tracking-wide uppercase">AI TRANSPARENCY: WHY IS THIS CRITICAL?</h3>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Assisted Decision Support</span>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-200 font-sans">
              <li className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span><strong>18 corroborating reports</strong> received from victim devices</span>
              </li>
              <li className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span><strong>High rescue-related language</strong> ("trapped", "collapse", "ambulance")</span>
              </li>
              <li className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span><strong>Geographic concentration</strong> detected in Sector 14</span>
              </li>
              <li className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span><strong>Reports arriving rapidly</strong> (18 reports within 3 minutes)</span>
              </li>
              <li className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span><strong>Multiple users report people trapped</strong> underneath structural debris</span>
              </li>
            </ul>
          </div>

          {/* Aggregated Victim Reports */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-200 font-mono tracking-wider uppercase">AGGREGATED VICTIM REPORTS ({incident.reports.length})</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {incident.reports.map((rep) => (
                <div key={rep.id} className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between font-mono text-slate-400">
                    <span className="text-cyan-400 font-bold">{rep.originName}</span>
                    <span>{rep.timestamp} IST • {rep.triggerType}</span>
                  </div>
                  <p className="text-slate-200 font-sans">{rep.rawText}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Actions Footer */}
        <div className="p-4 md:p-6 border-t border-slate-800 bg-slate-950/80 flex flex-col sm:flex-row items-center justify-between gap-3 sticky bottom-0 z-20">
          <div className="text-xs font-mono text-slate-400">
            Recommended Actions: <span className="text-amber-400 font-bold">{scoreV2.recommended_resources.join(', ')}</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {hasPermission('incident.dispatch') && incident.status !== 'RESOLVED' && (
              <>
                <button
                  onClick={() => onDispatchResource(incident.id, 'RESCUE')}
                  className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition-all shadow-md flex items-center gap-1.5"
                >
                  <Truck className="w-4 h-4" />
                  <span>Dispatch Heavy Rescue</span>
                </button>

                <button
                  onClick={() => onDispatchResource(incident.id, 'AMBULANCE')}
                  className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold transition-all shadow-md flex items-center gap-1.5"
                >
                  <Truck className="w-4 h-4" />
                  <span>Dispatch ALS Ambulance</span>
                </button>
              </>
            )}

            {hasPermission('incident.resolve') && incident.status !== 'RESOLVED' && (
              <button
                onClick={() => onResolveIncident(incident.id)}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md"
              >
                Mark Incident Resolved
              </button>
            )}

            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
            >
              Close Workspace
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
