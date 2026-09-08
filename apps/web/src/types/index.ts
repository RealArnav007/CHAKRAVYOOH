export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'EMERGING' | 'NORMAL';
export type IncidentStatus = 'UNASSIGNED' | 'DISPATCHING' | 'IN_PROGRESS' | 'RESOLVED';
export type TransportType = 'Wi-Fi Aware' | 'BLE' | 'CELLULAR_GATEWAY';
export type ResourceType = 'RESCUE' | 'AMBULANCE' | 'FIRE' | 'POLICE';
export type ResourceStatus = 'AVAILABLE' | 'ASSIGNED' | 'DISPATCHED' | 'EN_ROUTE' | 'ON_SCENE' | 'UNAVAILABLE';
export type UserRole = 'SUPER_ADMIN' | 'COMMANDER' | 'RESPONDER' | 'ANALYST' | 'VIEWER';

export interface LocationCoords {
  lat: number;
  lng: number;
  accuracy?: number;
  address?: string;
  sector?: string;
}

export interface PacketHop {
  hopNumber: number;
  nodeId: string;
  nodeName: string;
  transport: TransportType;
  rssi: number;
  battery: number;
  timestamp: string;
  isGateway: boolean;
}

export interface SOSReport {
  id: string;
  packetId: string;
  originNodeId: string;
  originName: string;
  rawText: string;
  timestamp: string;
  triggerType: 'MANUAL_SOS' | 'FALL_DETECTION' | 'SCREAM_DETECTION' | 'MISSED_CHECKIN';
  location: LocationCoords;
  regexScore: number;
  localModelScore: number;
  hopsCount: number;
  hopsJourney: PacketHop[];
}

export interface ExtractedEntitiesV2 {
  people_count?: number;
  injuries?: string[];
  hazards?: string[];
  needs?: string[];
  landmarks?: string[];
  mobility?: 'trapped' | 'mobile';
  vulnerable?: string[];
}

export interface CorrelationV2 {
  match_id?: string;
  similarity?: number;
  is_duplicate?: boolean;
  cluster_hint?: string;
}

export interface BriefingV2 {
  headline: string;
  recommended_resources: string[];
  confidence: number;
}

export interface ScoreResultV2 {
  schema_version: '2.0.0';
  severity: SeverityLevel;
  priority: number;
  category: string;
  confidence: number;
  needs_human_review: boolean;
  injection_suspected: boolean;
  false_alarm_likelihood: number;
  escalation_signal: number;
  correlation_id: string;
  regexScore: number;
  groqScore: number;
  corroborationBonus: number;
  locationBonus: number;
  trendVelocityBonus: number;
  briefing: BriefingV2;
  recommended_resources: string[];
  entities: ExtractedEntitiesV2;
  correlation: CorrelationV2;
}

export interface Incident {
  id: string;
  code: string;
  title: string;
  category: 'BUILDING_COLLAPSE' | 'MEDICAL_EMERGENCY' | 'FIRE' | 'FLOOD' | 'CIVIL_DISTURBANCE';
  severity: SeverityLevel;
  status: IncidentStatus;
  location: LocationCoords;
  createdAt: string;
  updatedAt: string;
  corroborationCount: number;
  reports: SOSReport[];
  aiScoreV2: ScoreResultV2;
  assignedResources: string[];
  zoneId: string;
}

export interface SeverityZone {
  id: string;
  code: string;
  name: string;
  center: LocationCoords;
  radiusMeters: number;
  severity: SeverityLevel;
  reportCount: number;
  activeIncidentsCount: number;
  trend: 'EXPANDING' | 'STABLE' | 'CONTAINED';
  expansionHistory: { timestamp: string; radius: number; severity: SeverityLevel }[];
}

export interface ResourceUnit {
  id: string;
  callsign: string;
  type: ResourceType;
  status: ResourceStatus;
  crewCount: number;
  location: LocationCoords;
  assignedIncidentId?: string;
  assignedIncidentCode?: string;
  etaMinutes?: number;
  lastUpdated: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  userId: string;
  userName: string;
  role: UserRole;
  action: string;
  resourceId: string;
  resourceName: string;
  result: 'SUCCESS' | 'DENIED' | 'FAILED';
  ipAddress: string;
}

export interface UserSession {
  userId: string;
  userName: string;
  role: UserRole;
  badgeNumber: string;
  department: string;
  permissions: string[];
  mfaVerified: boolean;
}
