import React, { useState } from 'react';
import { Play, CheckCircle2, ShieldAlert, Radio, ArrowRight, Zap, RefreshCw, X } from 'lucide-react';

interface DemoProps {
  onClose: () => void;
  onSimulateStage: (stage: number) => void;
}

export const LiveDemoSimulationBar: React.FC<DemoProps> = ({ onClose, onSimulateStage }) => {
  const [currentStage, setCurrentStage] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const stages = [
    { num: 1, title: 'Stage 1: Network Topology', desc: '5 nodes active in mesh network (P1→P5)' },
    { num: 2, title: 'Stage 2: Offline SOS Trigger', desc: 'Node 1 airplane mode, triggers manual SOS' },
    { num: 3, title: 'Stage 3: Hop Transit', desc: 'Packet advances P1→P2→P3→P4→P5 without bouncing' },
    { num: 4, title: 'Stage 4: Gateway Upload', desc: 'Node 5 Gateway connects to Internet & POSTs API' },
    { num: 5, title: 'Stage 5: AI Groq Triage', desc: 'Regex + Groq AI + Location correlation runs' },
    { num: 6, title: 'Stage 6: Incident Created', desc: 'Website pops 🚨 CRITICAL INCIDENT #104 (Score 82)' },
    { num: 7, title: 'Stage 7: Zone Expansion', desc: 'Incoming reports: 1→3→7→18, Score 82→91→97' }
  ];

  const handleStageClick = (stageNum: number) => {
    setCurrentStage(stageNum);
    onSimulateStage(stageNum);
  };

  const handleNextStage = () => {
    const next = currentStage < 7 ? currentStage + 1 : 1;
    setCurrentStage(next);
    onSimulateStage(next);
  };

  return (
    <div className="bg-slate-900 border-b border-amber-500/40 px-4 py-3 sticky top-16 z-30 shadow-2xl backdrop-blur-md">
      <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40">
            <Zap className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-xs font-extrabold text-amber-300 font-mono uppercase tracking-wider">
              INTERACTIVE 7-STAGE HACKATHON DEMO SIMULATOR
            </h3>
            <p className="text-[11px] text-slate-300 font-mono">
              Simulate offline victim SOS, 5-hop mesh transit, gateway upload, AI triage & zone expansion
            </p>
          </div>
        </div>

        {/* Stage Stepper Buttons */}
        <div className="flex items-center space-x-1.5 overflow-x-auto py-1 max-w-full font-mono text-xs">
          {stages.map((stg) => {
            const isActive = currentStage === stg.num;
            return (
              <button
                key={stg.num}
                onClick={() => handleStageClick(stg.num)}
                className={`px-3 py-1.5 rounded-lg border text-xs font-bold transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-amber-500 text-slate-950 border-amber-400 shadow-lg shadow-amber-500/30 scale-105'
                    : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700 hover:text-slate-100'
                }`}
                title={stg.desc}
              >
                S{stg.num}
              </button>
            );
          })}
        </div>

        {/* Next & Close Buttons */}
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={handleNextStage}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow"
          >
            <span>Run Stage {currentStage < 7 ? currentStage + 1 : 1}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
