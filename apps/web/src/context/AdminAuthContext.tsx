import React, { createContext, useContext, useState } from 'react';
import { UserSession, UserRole } from '../types';
import { INITIAL_USER_SESSION } from '../services/mockData';

interface AdminAuthContextType {
  session: UserSession;
  setRole: (role: UserRole) => void;
  hasPermission: (permission: string) => boolean;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export const AdminAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<UserSession>(INITIAL_USER_SESSION);

  const setRole = (role: UserRole) => {
    let permissions: string[] = [];
    let name = session.userName;
    let dept = session.department;

    switch (role) {
      case 'SUPER_ADMIN':
        name = session.userName || 'Super Admin Officer';
        dept = 'National Emergency Operations Command Center';
        permissions = ['*'];
        break;
      case 'COMMANDER':
        name = session.userName || 'NDRF Commander';
        dept = 'National Disaster Response Force — HQ';
        permissions = ['incident.read', 'incident.update', 'incident.dispatch', 'incident.resolve', 'resource.read', 'resource.update', 'analytics.read', 'audit.read'];
        break;
      case 'RESPONDER':
        name = session.userName || 'Field Lead Inspector';
        dept = 'NDRF Field Operations';
        permissions = ['incident.read', 'incident.update', 'resource.read', 'resource.update'];
        break;
      case 'ANALYST':
        name = session.userName || 'Disaster Data Analyst';
        dept = 'Disaster Mitigation Cell';
        permissions = ['incident.read', 'analytics.read'];
        break;
      case 'VIEWER':
        name = session.userName || 'Observer User';
        dept = 'Public Observer Terminal';
        permissions = ['incident.read'];
        break;
    }

    setSession({
      ...session,
      role,
      userName: name,
      department: dept,
      permissions
    });
  };

  const hasPermission = (permission: string) => {
    if (session.role === 'SUPER_ADMIN' || session.permissions.includes('*')) return true;
    return session.permissions.includes(permission);
  };

  return (
    <AdminAuthContext.Provider value={{ session, setRole, hasPermission }}>
      {children}
    </AdminAuthContext.Provider>
  );
};

export const useAdminAuth = () => {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
};
