import React from 'react';
import { LayoutDashboard, AlertOctagon, Map, Truck, BarChart3, ShieldCheck, PlayCircle } from 'lucide-react';
import { useAdminAuth } from '../../context/AdminAuthContext';

export type ActiveTab = 'dashboard' | 'incidents' | 'map' | 'dispatch' | 'analytics' | 'audit';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  unassignedCount: number;
  onOpenDemoBar?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, unassignedCount, onOpenDemoBar }) => {
  const { session } = useAdminAuth();

  const navItems = [
    {
      id: 'dashboard' as ActiveTab,
      label: 'Command Center',
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: 'incidents' as ActiveTab,
      label: 'Incident Queue',
      icon: AlertOctagon,
      badge: unassignedCount > 0 ? `${unassignedCount} New` : null,
      badgeColor: 'bg-red-500/20 text-red-400 border-red-500/30'
    },
    {
      id: 'map' as ActiveTab,
      label: 'Operations Map',
      icon: Map,
      badge: 'Live'
    },
    {
      id: 'dispatch' as ActiveTab,
      label: 'Dispatch & Fleet',
      icon: Truck,
      badge: null
    },
    {
      id: 'analytics' as ActiveTab,
      label: 'Zone Analytics',
      icon: BarChart3,
      badge: null
    },
    {
      id: 'audit' as ActiveTab,
      label: 'Audit & RBAC',
      icon: ShieldCheck,
      badge: session.role
    }
  ];

  return (
    <aside className="w-64 bg-slate-900/95 border-r border-slate-800 flex flex-col justify-between hidden md:flex shrink-0">
      <div className="p-4 space-y-6">
        {/* User Card */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-300 font-bold text-xs">
              {session.userName.charAt(0)}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-slate-200 truncate">{session.userName}</p>
              <p className="text-[10px] text-slate-400 font-mono truncate">{session.badgeNumber}</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-2">OPERATIONAL HUBS</p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-red-600/20 to-amber-600/20 text-slate-100 border border-red-500/30 font-semibold shadow-inner'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-red-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${item.badgeColor || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer Demo Trigger & Info */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        {onOpenDemoBar && (
          <button
            onClick={onOpenDemoBar}
            className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-medium transition-colors"
          >
            <PlayCircle className="w-4 h-4 text-amber-400" />
            <span>Interactive Demo Suite</span>
          </button>
        )}

        <div className="text-[10px] text-slate-500 font-mono text-center space-y-0.5">
          <p>CHAKRAVYOOH v3.0</p>
          <p className="text-slate-600">Strict Official Access Only</p>
        </div>
      </div>
    </aside>
  );
};
