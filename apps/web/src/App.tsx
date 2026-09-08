import React, { useState } from 'react';
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext';
import { Header } from './components/layout/Header';
import { Sidebar, ActiveTab } from './components/layout/Sidebar';
import { LoginScreen } from './components/auth/LoginScreen';
import { CommandCenterDashboard } from './components/dashboard/CommandCenterDashboard';
import { IncidentDetailModal } from './components/incidents/IncidentDetailModal';
import { InteractiveOperationsMap } from './components/map/InteractiveOperationsMap';
import { DispatchFleetHub } from './components/dispatch/DispatchFleetHub';
import { ZoneAnalyticsEngine } from './components/analytics/ZoneAnalyticsEngine';
import { AuditLogViewer } from './components/audit/AuditLogViewer';
import { LiveDemoSimulationBar } from './components/simulation/LiveDemoSimulationBar';
import { INITIAL_INCIDENTS, INITIAL_SEVERITY_ZONES, INITIAL_RESOURCES, INITIAL_AUDIT_EVENTS } from './services/mockData';
import { Incident, SeverityZone, ResourceUnit, AuditEvent, UserRole } from './types';

interface RegisteredUser {
  badgeId: string;
  password: string;
  name: string;
  role: UserRole;
  contact: string;
}

const INITIAL_REGISTERED_USERS: RegisteredUser[] = [];

const MainContent: React.FC = () => {
  const { session, setRole } = useAdminAuth();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [registeredUsers, setRegisteredUsers] = useState<RegisteredUser[]>(INITIAL_REGISTERED_USERS);
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [incidents, setIncidents] = useState<Incident[]>(INITIAL_INCIDENTS);
  const [zones, setZones] = useState<SeverityZone[]>(INITIAL_SEVERITY_ZONES);
  const [resources, setResources] = useState<ResourceUnit[]>(INITIAL_RESOURCES);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>(INITIAL_AUDIT_EVENTS);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showDemoBar, setShowDemoBar] = useState<boolean>(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const triggerToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleLoginSuccess = (role: UserRole, badge: string, name: string) => {
    setRole(role);
    setIsAuthenticated(true);
    triggerToast(`Welcome ${name} (${badge}) — Session Active`);
  };

  const handleRegisterUser = (newUser: RegisteredUser) => {
    setRegisteredUsers([newUser, ...registeredUsers]);
    const newAudit: AuditEvent = {
      id: `aud-${Date.now()}`,
      timestamp: new Date().toLocaleTimeString('en-GB', { hour12: false }),
      userId: session.userId || 'ADMIN-INIT',
      userName: session.userName || 'Super Admin',
      role: 'SUPER_ADMIN',
      action: 'REGISTER_OFFICER',
      resourceId: newUser.badgeId,
      resourceName: `Provisioned ${newUser.name} (${newUser.role})`,
      result: 'SUCCESS',
      ipAddress: '10.240.12.89'
    };
    setAuditEvents([newAudit, ...auditEvents]);
    triggerToast(`Created account for ${newUser.name} (${newUser.badgeId})`);
  };

  const handleDispatchResource = (incidentId: string, resourceType: string) => {
    const targetIncident = incidents.find(i => i.id === incidentId);
    if (!targetIncident) return;

    const availRes = resources.find(r => r.status === 'AVAILABLE' && (resourceType ? r.type === resourceType : true)) || resources.find(r => r.status === 'AVAILABLE');

    if (availRes) {
      const updatedResources = resources.map(r => r.id === availRes.id ? {
        ...r,
        status: 'DISPATCHED' as const,
        assignedIncidentId: incidentId,
        assignedIncidentCode: targetIncident.code,
        etaMinutes: 4
      } : r);

      const updatedIncidents = incidents.map(i => i.id === incidentId ? {
        ...i,
        status: 'DISPATCHING' as const,
        assignedResources: [...i.assignedResources, availRes.id]
      } : i);

      setResources(updatedResources);
      setIncidents(updatedIncidents);

      const newAudit: AuditEvent = {
        id: `aud-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString('en-GB', { hour12: false }),
        userId: session.userId,
        userName: session.userName,
        role: session.role,
        action: 'DISPATCH_RESOURCE',
        resourceId: availRes.id,
        resourceName: `${availRes.callsign} → ${targetIncident.code}`,
        result: 'SUCCESS',
        ipAddress: '10.240.12.89'
      };
      setAuditEvents([newAudit, ...auditEvents]);
      triggerToast(`🚨 Dispatched ${availRes.callsign} to ${targetIncident.code}`);
    } else {
      triggerToast(`⚠️ No available ${resourceType} units currently in staging area.`);
    }
  };

  const handleUpdateResourceStatus = (resourceId: string, newStatus: ResourceUnit['status']) => {
    setResources(resources.map(r => r.id === resourceId ? { ...r, status: newStatus } : r));
    triggerToast(`Unit status updated to ${newStatus}`);
  };

  const handleResolveIncident = (incidentId: string) => {
    setIncidents(incidents.map(i => i.id === incidentId ? { ...i, status: 'RESOLVED' as const } : i));
    setSelectedIncident(null);
    triggerToast(`Incident resolved and logged`);
  };

  const handleSimulateStage = (stage: number) => {
    if (stage === 1) {
      triggerToast('Stage 1: 5 Mesh Nodes Active (P1→P5 Topology Established)');
    } else if (stage === 2) {
      triggerToast('Stage 2: Node 1 Offline SOS Triggered (Airplane Mode ON)');
    } else if (stage === 3) {
      triggerToast('Stage 3: Packet Multi-Hop Transit: P1 → P2 → P3 → P4 → P5');
    } else if (stage === 4) {
      triggerToast('Stage 4: Node 5 Gateway Connected → Cloud Ingest Endpoint POST /sos/ingest');
    } else if (stage === 5) {
      triggerToast('Stage 5: ScoreResult v2.0.0 Pipeline Executed (Regex + Triage + Entity Extraction)');
    } else if (stage === 6) {
      triggerToast('Stage 6: Incident INC-104 Created on Command Center UI (Severity Score: 82)');
      setActiveTab('dashboard');
    } else if (stage === 7) {
      const updatedIncidents = incidents.map(i => i.id === 'inc-104' ? {
        ...i,
        corroborationCount: 18,
        severity: 'CRITICAL' as const,
        aiScoreV2: {
          ...i.aiScoreV2,
          priority: 97,
          corroborationBonus: 8
        }
      } : i);
      const updatedZones = zones.map(z => z.id === 'zone-alpha' ? {
        ...z,
        reportCount: 18,
        radiusMeters: 850,
        severity: 'CRITICAL' as const
      } : z);
      setIncidents(updatedIncidents);
      setZones(updatedZones);
      triggerToast('Stage 7: Corroboration Spike! Reports 1→18, Zone Alpha Expanded to 850m (Score 97)');
      setActiveTab('incidents');
      setSelectedIncident(updatedIncidents[0]);
    }
  };

  if (!isAuthenticated) {
    return (
      <LoginScreen
        onLoginSuccess={handleLoginSuccess}
        registeredUsers={registeredUsers}
        onRegisterUser={handleRegisterUser}
      />
    );
  }

  const unassignedCount = incidents.filter(i => i.status === 'UNASSIGNED').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-red-500/30 selection:text-red-200">
      {/* Navigation Header */}
      <Header onOpenDemoBar={() => {}} />

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          unassignedCount={unassignedCount}
          onOpenDemoBar={() => setShowDemoBar(true)}
        />

        <main className="flex-1 overflow-y-auto pb-12">
          {activeTab === 'dashboard' && (
            <CommandCenterDashboard
              incidents={incidents}
              onSelectIncident={(inc) => setSelectedIncident(inc)}
              onNavigateToMap={() => setActiveTab('map')}
              onNavigateToDispatch={() => setActiveTab('dispatch')}
            />
          )}

          {activeTab === 'incidents' && (
            <CommandCenterDashboard
              incidents={incidents}
              onSelectIncident={(inc) => setSelectedIncident(inc)}
              onNavigateToMap={() => setActiveTab('map')}
              onNavigateToDispatch={() => setActiveTab('dispatch')}
            />
          )}

          {activeTab === 'map' && (
            <InteractiveOperationsMap
              incidents={incidents}
              zones={zones}
              resources={resources}
              onSelectIncident={(inc) => setSelectedIncident(inc)}
            />
          )}

          {activeTab === 'dispatch' && (
            <DispatchFleetHub
              resources={resources}
              incidents={incidents}
              onUpdateResourceStatus={handleUpdateResourceStatus}
              onAssignResource={handleDispatchResource}
            />
          )}

          {activeTab === 'analytics' && (
            <ZoneAnalyticsEngine zones={zones} />
          )}

          {activeTab === 'audit' && (
            <AuditLogViewer events={auditEvents} />
          )}
        </main>
      </div>

      {/* Dedicated Workspace Modal */}
      <IncidentDetailModal
        incident={selectedIncident}
        onClose={() => setSelectedIncident(null)}
        onDispatchResource={handleDispatchResource}
        onResolveIncident={handleResolveIncident}
      />

      {/* Live Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 p-4 rounded-xl bg-slate-900 border border-amber-500/50 text-xs font-mono text-amber-200 shadow-2xl animate-bounce flex items-center space-x-2">
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
};

export function App() {
  return (
    <AdminAuthProvider>
      <MainContent />
    </AdminAuthProvider>
  );
}

export default App;
