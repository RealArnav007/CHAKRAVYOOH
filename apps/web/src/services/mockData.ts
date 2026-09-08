import { Incident, SeverityZone, ResourceUnit, AuditEvent, UserSession } from '../types';

export const INITIAL_USER_SESSION: UserSession = {
  userId: 'OFFICER-001',
  userName: 'Duty Command Officer',
  role: 'COMMANDER',
  badgeNumber: 'NDRF-HQ-01',
  department: 'National Disaster Response Force — Operational Command',
  mfaVerified: true,
  permissions: [
    'incident.read',
    'incident.update',
    'incident.dispatch',
    'incident.resolve',
    'resource.read',
    'resource.update',
    'analytics.read',
    'audit.read'
  ]
};

export const INITIAL_INCIDENTS: Incident[] = [
  {
    id: 'inc-104',
    code: 'INC-104',
    title: 'Multi-Story Structural Collapse',
    category: 'BUILDING_COLLAPSE',
    severity: 'CRITICAL',
    status: 'DISPATCHING',
    location: {
      lat: 28.6139,
      lng: 77.2090,
      sector: 'Sector 14, Central Metro District',
      address: 'Plot 42, Connaught Inner Ring'
    },
    createdAt: '08:40:12',
    updatedAt: '08:47:35',
    corroborationCount: 18,
    assignedResources: ['res-01', 'res-03'],
    zoneId: 'zone-alpha',
    aiScoreV2: {
      schema_version: '2.0.0',
      severity: 'CRITICAL',
      priority: 97,
      category: 'rescue',
      confidence: 0.94,
      needs_human_review: false,
      injection_suspected: false,
      false_alarm_likelihood: 0.0,
      escalation_signal: 0.88,
      correlation_id: 'trace-8f92-a1b4-chakravyooh-v2',
      regexScore: 88,
      groqScore: 94,
      corroborationBonus: 8,
      locationBonus: 3,
      trendVelocityBonus: 2,
      briefing: {
        headline: 'Structural collapse, 3 trapped incl. child — rescue + ambulance, critical priority',
        recommended_resources: ['rescue_team', 'ambulance', 'medical_supplies'],
        confidence: 0.94
      },
      recommended_resources: ['rescue_team', 'ambulance', 'medical_supplies'],
      entities: {
        people_count: 3,
        injuries: ['general_trauma', 'head_injury'],
        hazards: ['structural_collapse', 'gas_leak_smell'],
        needs: ['rescue', 'medical'],
        landmarks: ['Sector 14 Connaught Inner Ring'],
        mobility: 'trapped',
        vulnerable: ['child']
      },
      correlation: {
        match_id: 'inc-104',
        similarity: 0.89,
        is_duplicate: true,
        cluster_hint: 'Central Metro Structural Collapse Zone A'
      }
    },
    reports: [
      {
        id: 'rep-01',
        packetId: 'pkt-9981-a1',
        originNodeId: 'NODE-P1-001',
        originName: 'Phone #1 (Victim)',
        rawText: 'Building collapse! 4 people trapped inside basement, heavy concrete debris, need rescue team fast!',
        timestamp: '08:41:05',
        triggerType: 'MANUAL_SOS',
        location: { lat: 28.6139, lng: 77.2090, sector: 'Sector 14' },
        regexScore: 88,
        localModelScore: 89,
        hopsCount: 5,
        hopsJourney: [
          { hopNumber: 1, nodeId: 'NODE-P1-001', nodeName: 'Victim Phone (P1)', transport: 'BLE', rssi: -62, battery: 42, timestamp: '08:41:05', isGateway: false },
          { hopNumber: 2, nodeId: 'NODE-P2-002', nodeName: 'Relay Phone (P2)', transport: 'Wi-Fi Aware', rssi: -71, battery: 78, timestamp: '08:41:12', isGateway: false },
          { hopNumber: 3, nodeId: 'NODE-P3-003', nodeName: 'Relay Phone (P3)', transport: 'Wi-Fi Aware', rssi: -68, battery: 65, timestamp: '08:41:19', isGateway: false },
          { hopNumber: 4, nodeId: 'NODE-P4-004', nodeName: 'Relay Phone (P4)', transport: 'BLE', rssi: -79, battery: 84, timestamp: '08:41:26', isGateway: false },
          { hopNumber: 5, nodeId: 'NODE-P5-005', nodeName: 'Gateway Phone (P5)', transport: 'CELLULAR_GATEWAY', rssi: -55, battery: 91, timestamp: '08:41:31', isGateway: true }
        ]
      },
      {
        id: 'rep-02',
        packetId: 'pkt-9982-b2',
        originNodeId: 'NODE-P1-008',
        originName: 'Phone #8 (Bystander)',
        rawText: 'Heavy dust cloud, building floor 3 collapsed down into shop floor. Send ambulances immediately.',
        timestamp: '08:42:30',
        triggerType: 'FALL_DETECTION',
        location: { lat: 28.6141, lng: 77.2092, sector: 'Sector 14' },
        regexScore: 82,
        localModelScore: 86,
        hopsCount: 3,
        hopsJourney: [
          { hopNumber: 1, nodeId: 'NODE-P1-008', nodeName: 'Bystander Phone', transport: 'BLE', rssi: -58, battery: 89, timestamp: '08:42:30', isGateway: false },
          { hopNumber: 2, nodeId: 'NODE-P4-004', nodeName: 'Relay Phone (P4)', transport: 'Wi-Fi Aware', rssi: -64, battery: 84, timestamp: '08:42:34', isGateway: false },
          { hopNumber: 3, nodeId: 'NODE-P5-005', nodeName: 'Gateway Phone (P5)', transport: 'CELLULAR_GATEWAY', rssi: -52, battery: 91, timestamp: '08:42:38', isGateway: true }
        ]
      }
    ]
  },
  {
    id: 'inc-105',
    code: 'INC-105',
    title: 'Transformer Fire & Smoke Spread',
    category: 'FIRE',
    severity: 'HIGH',
    status: 'DISPATCHING',
    location: {
      lat: 28.6210,
      lng: 77.2150,
      sector: 'Sector 19, North Grid',
      address: 'Substation 4B, Barakhamba'
    },
    createdAt: '08:35:00',
    updatedAt: '08:45:10',
    corroborationCount: 8,
    assignedResources: ['res-02'],
    zoneId: 'zone-bravo',
    aiScoreV2: {
      schema_version: '2.0.0',
      severity: 'HIGH',
      priority: 86,
      category: 'fire',
      confidence: 0.86,
      needs_human_review: true,
      injection_suspected: false,
      false_alarm_likelihood: 0.05,
      escalation_signal: 0.75,
      correlation_id: 'trace-4d11-b9c2-chakravyooh-v2',
      regexScore: 78,
      groqScore: 84,
      corroborationBonus: 5,
      locationBonus: 2,
      trendVelocityBonus: 1,
      briefing: {
        headline: 'Substation electrical explosion resulting in thick toxic smoke — fire engine advised',
        recommended_resources: ['fire_truck', 'evacuation'],
        confidence: 0.86
      },
      recommended_resources: ['fire_truck', 'evacuation'],
      entities: {
        hazards: ['electrical_explosion', 'toxic_smoke'],
        needs: ['fire_suppression', 'electrical_isolation'],
        landmarks: ['Substation 4B Barakhamba'],
        mobility: 'mobile'
      },
      correlation: {
        match_id: 'inc-105',
        similarity: 0.92,
        is_duplicate: false,
        cluster_hint: 'Sector 19 Substation Risk Zone B'
      }
    },
    reports: []
  }
];

export const INITIAL_SEVERITY_ZONES: SeverityZone[] = [
  {
    id: 'zone-alpha',
    code: 'ZONE-A',
    name: 'Sector 14 Disaster Hub',
    center: { lat: 28.6139, lng: 77.2090, sector: 'Sector 14' },
    radiusMeters: 850,
    severity: 'CRITICAL',
    reportCount: 18,
    activeIncidentsCount: 1,
    trend: 'EXPANDING',
    expansionHistory: [
      { timestamp: '08:40', radius: 250, severity: 'EMERGING' },
      { timestamp: '08:43', radius: 500, severity: 'HIGH' },
      { timestamp: '08:47', radius: 850, severity: 'CRITICAL' }
    ]
  },
  {
    id: 'zone-bravo',
    code: 'ZONE-B',
    name: 'Sector 19 Substation Risk',
    center: { lat: 28.6210, lng: 77.2150, sector: 'Sector 19' },
    radiusMeters: 450,
    severity: 'HIGH',
    reportCount: 8,
    activeIncidentsCount: 1,
    trend: 'STABLE',
    expansionHistory: [
      { timestamp: '08:35', radius: 300, severity: 'HIGH' },
      { timestamp: '08:45', radius: 450, severity: 'HIGH' }
    ]
  }
];

export const INITIAL_RESOURCES: ResourceUnit[] = [
  {
    id: 'res-01',
    callsign: 'NDRF Heavy Rescue-03',
    type: 'RESCUE',
    status: 'DISPATCHED',
    crewCount: 12,
    location: { lat: 28.6145, lng: 77.2085, sector: 'Sector 14' },
    assignedIncidentId: 'inc-104',
    assignedIncidentCode: 'INC-104',
    etaMinutes: 4,
    lastUpdated: '08:45:00'
  },
  {
    id: 'res-02',
    callsign: 'Delhi Fire Brigade Foam Engine-12',
    type: 'FIRE',
    status: 'EN_ROUTE',
    crewCount: 6,
    location: { lat: 28.6190, lng: 77.2135, sector: 'Sector 19' },
    assignedIncidentId: 'inc-105',
    assignedIncidentCode: 'INC-105',
    etaMinutes: 6,
    lastUpdated: '08:44:20'
  },
  {
    id: 'res-03',
    callsign: 'AIIMS ALS Ambulance-07',
    type: 'AMBULANCE',
    status: 'ON_SCENE',
    crewCount: 4,
    location: { lat: 28.6139, lng: 77.2090, sector: 'Sector 14' },
    assignedIncidentId: 'inc-104',
    assignedIncidentCode: 'INC-104',
    etaMinutes: 0,
    lastUpdated: '08:46:15'
  }
];

export const INITIAL_AUDIT_EVENTS: AuditEvent[] = [
  {
    id: 'aud-901',
    timestamp: '08:46:20',
    userId: 'SYS-001',
    userName: 'System Gateway',
    role: 'SUPER_ADMIN',
    action: 'BACKEND_PORTAL_INITIALIZED',
    resourceId: 'res-init',
    resourceName: 'Real-Time Ingest Pipeline Ready',
    result: 'SUCCESS',
    ipAddress: '127.0.0.1'
  }
];
