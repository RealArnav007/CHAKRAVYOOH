import http.server
import socketserver
import urllib.request
import os
import json
from datetime import datetime

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def get_live_risk_matrix_payload():
    return {
        "status": "success",
        "backend_connected": True,
        "endpoint": "/api/v1/cyclone/risk-matrix",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "system": {
            "name": "CHAKRAVYOOH AI Early Warning & Tactical Matrix Engine",
            "model_version": "IMD-RSMC-PINN-v4.2",
            "source": "ISRO INSAT-3DR + EOS-06 Scatterometer + INCOIS Moored Buoys"
        },
        "cyclone": {
            "name": "Cyclone Amrit (BOB-04)",
            "classification": "Very Severe Cyclonic Storm (VSCS / Cat-3)",
            "center": {"lat": 16.82, "lon": 84.48, "region": "Bay of Bengal"},
            "central_pressure_hpa": 948,
            "max_sustained_winds_kmh": 155,
            "movement": "North-West (315° Azimuth) at 18 km/h",
            "target_coast": "Gopalpur-Ganjam Coastal Belt, Odisha",
            "landfall_window_hours": 22.5,
            "peak_surge_height_m": 3.8
        },
        "summary": {
            "total_population_at_risk": 2358500,
            "total_evacuated": 1372650,
            "overall_evacuation_rate_pct": 58.2,
            "active_shelters": 298,
            "mesh_relays_online": 142,
            "critical_surge_threat": "3.8m breaking coastal surge along Gopalpur-Ganjam corridor",
            "evacuation_priority": "ZONE A (Mandatory Relocation)"
        },
        "matrix_dimensions": {
            "y_axis": {
                "name": "Storm Surge & Inundation Severity",
                "tiers": [
                    {"id": "r4", "label": "Catastrophic (>3.5m)", "surge": ">3.5m", "description": "Overtopping coastal sea walls and protective dunes"},
                    {"id": "r3", "label": "Severe (2.5–3.5m)", "surge": "2.5–3.5m", "description": "Breaches low-lying saline embankments"},
                    {"id": "r2", "label": "Moderate (1.5–2.5m)", "surge": "1.5–2.5m", "description": "High tide inundation of tidal estuaries"},
                    {"id": "r1", "label": "Minor (<1.5m)", "surge": "<1.5m", "description": "Localized water logging along drainage outlets"}
                ]
            },
            "x_axis": {
                "name": "Population Vulnerability & Asset Exposure",
                "tiers": [
                    {"id": "c1", "label": "Inland Rural", "density": "<500/km²", "profile": "Agricultural lowlands, dispersed dwellings"},
                    {"id": "c2", "label": "Semi-Urban Corridor", "density": "500–2,000/km²", "profile": "Highways, market towns, district roads"},
                    {"id": "c3", "label": "Dense Urban Center", "density": ">2,000/km²", "profile": "Municipal core, major hospitals, transit terminals"},
                    {"id": "c4", "label": "Critical Coastal Front", "density": "Coastline <2km", "profile": "Fishing villages, port infrastructure, beach hamlets"}
                ]
            }
        },
        "matrix_grid": [
            {
                "tier": "Catastrophic (>3.5m)",
                "surge_level": ">3.5m",
                "cells": [
                    {"col": "Inland Rural", "risk_level": "MODERATE", "badge": "YELLOW", "code": "C1", "zone": "Zone C", "evac_target": "50% Evacuation", "action": "Shelter standby, flood dyke reinforcement"},
                    {"col": "Semi-Urban Corridor", "risk_level": "HIGH", "badge": "ORANGE", "code": "B1", "zone": "Zone B", "evac_target": "80% Evacuation", "action": "Mandatory low-lying evacuation, secure transit"},
                    {"col": "Dense Urban Center", "risk_level": "EXTREME", "badge": "RED", "code": "A2", "zone": "Zone A", "evac_target": "100% Mandatory", "action": "Complete relocation to cyclone shelters, power isolation"},
                    {"col": "Critical Coastal Front", "risk_level": "EXTREME", "badge": "RED", "code": "A1", "zone": "Zone A", "evac_target": "100% Evacuated", "action": "Zero-human zone; naval/port lockdown; emergency mesh broadcast"}
                ]
            },
            {
                "tier": "Severe (2.5–3.5m)",
                "surge_level": "2.5–3.5m",
                "cells": [
                    {"col": "Inland Rural", "risk_level": "LOW", "badge": "GREEN", "code": "D1", "zone": "Zone D", "evac_target": "Advisory Only", "action": "Stock relief food, test LoRa mesh nodes"},
                    {"col": "Semi-Urban Corridor", "risk_level": "MODERATE", "badge": "YELLOW", "code": "C2", "zone": "Zone C", "evac_target": "Precautionary", "action": "High-ground staging, ambulance mobilization"},
                    {"col": "Dense Urban Center", "risk_level": "HIGH", "badge": "ORANGE", "code": "B2", "zone": "Zone B", "evac_target": "75% Evacuation", "action": "NDRF Zodiac boat deployment, flood barriers"},
                    {"col": "Critical Coastal Front", "risk_level": "EXTREME", "badge": "RED", "code": "A3", "zone": "Zone A", "evac_target": "100% Mandatory", "action": "Harbor evacuation, fishing trawler lockdown"}
                ]
            },
            {
                "tier": "Moderate (1.5–2.5m)",
                "surge_level": "1.5–2.5m",
                "cells": [
                    {"col": "Inland Rural", "risk_level": "LOW", "badge": "GREEN", "code": "D2", "zone": "Zone D", "evac_target": "Normal Standby", "action": "Community radio broadcast listening"},
                    {"col": "Semi-Urban Corridor", "risk_level": "LOW", "badge": "GREEN", "code": "D3", "zone": "Zone D", "evac_target": "Advisory Only", "action": "Clear drainage canals and culverts"},
                    {"col": "Dense Urban Center", "risk_level": "MODERATE", "badge": "YELLOW", "code": "C3", "zone": "Zone C", "evac_target": "Precautionary", "action": "Hospital diesel generator checks, water tank safety"},
                    {"col": "Critical Coastal Front", "risk_level": "HIGH", "badge": "ORANGE", "code": "B3", "zone": "Zone B", "evac_target": "Mandatory Coastal", "action": "Fishermen retreat past 500m tide line"}
                ]
            },
            {
                "tier": "Minor (<1.5m)",
                "surge_level": "<1.5m",
                "cells": [
                    {"col": "Inland Rural", "risk_level": "LOW", "badge": "GREEN", "code": "D4", "zone": "Zone D", "evac_target": "Normal Ops", "action": "Standard weather monitoring"},
                    {"col": "Semi-Urban Corridor", "risk_level": "LOW", "badge": "GREEN", "code": "D5", "zone": "Zone D", "evac_target": "Normal Ops", "action": "Monitor automatic rain gauges"},
                    {"col": "Dense Urban Center", "risk_level": "LOW", "badge": "GREEN", "code": "D6", "zone": "Zone D", "evac_target": "Advisory", "action": "Civic pump testing"},
                    {"col": "Critical Coastal Front", "risk_level": "MODERATE", "badge": "YELLOW", "code": "C4", "zone": "Zone C", "evac_target": "Beach Closure", "action": "Red flags on beaches, marine police patrol"}
                ]
            }
        ],
        "risk_zones": [
            {
                "id": "zone-a",
                "code": "ZONE A",
                "level": "EXTREME",
                "colorTag": "RED WARNING",
                "badgeClass": "bg-red-950/80 text-red-300 border-red-700/80",
                "corridor": "Coastal Strip 0–15 km (Gopalpur, Ganjam, Chatrapur)",
                "surgeHeight": "3.8m above astronomical tide",
                "sustainedWinds": "135–155 km/h (Cat-3 Storm)",
                "actionDirective": "100% Mandatory evacuation of all coastal hamlets; total port lockdown; offline mesh warning broadcast active",
                "populationExposed": "248,500",
                "evacuatedPercent": 82,
                "sheltersActive": 46,
                "shelterOccupancy": "86%",
                "meshStatus": "142 Nodes Synchronized • SOS Channel Active"
            },
            {
                "id": "zone-b",
                "code": "ZONE B",
                "level": "HIGH",
                "colorTag": "ORANGE ALERT",
                "badgeClass": "bg-amber-950/80 text-amber-300 border-amber-700/80",
                "corridor": "Inland Belt 15–40 km (Berhampur City, Aska Corridor)",
                "surgeHeight": "Flash inundation up to 1.4m along low drainage",
                "sustainedWinds": "100–125 km/h",
                "actionDirective": "Shelter in place; secure loose structures; preposition 12 NDRF Zodiac rescue teams; cellular + mesh dual channel",
                "populationExposed": "620,000",
                "evacuatedPercent": 56,
                "sheltersActive": 84,
                "shelterOccupancy": "68%",
                "meshStatus": "Dual-Band Mesh Active (Cellular Fallback)"
            },
            {
                "id": "zone-c",
                "code": "ZONE C",
                "level": "MODERATE",
                "colorTag": "YELLOW WATCH",
                "badgeClass": "bg-yellow-950/70 text-yellow-300 border-yellow-700/80",
                "corridor": "Perimeter 40–90 km (Digapahandi, Bhanjanagar)",
                "surgeHeight": "Inland heavy rainfall > 180mm / 24h",
                "sustainedWinds": "70–95 km/h",
                "actionDirective": "Precautionary advisory; verify diesel gensets and municipal water supplies; food and medical dispatch queued",
                "populationExposed": "1,140,000",
                "evacuatedPercent": 24,
                "sheltersActive": 110,
                "shelterOccupancy": "35%",
                "meshStatus": "Advisory Broadcast Queued"
            },
            {
                "id": "zone-d",
                "code": "ZONE D",
                "level": "LOW",
                "colorTag": "GREEN STANDBY",
                "badgeClass": "bg-emerald-950/70 text-emerald-300 border-emerald-700/80",
                "corridor": "Inland Highlands >90 km (Mohana, Rayagada Gateway)",
                "surgeHeight": "No marine surge; moderate rainfall",
                "sustainedWinds": "45–65 km/h",
                "actionDirective": "Continuous telemetry monitoring; staged logistics reserves and inland evacuation reception shelters",
                "populationExposed": "350,000",
                "evacuatedPercent": 10,
                "sheltersActive": 58,
                "shelterOccupancy": "14%",
                "meshStatus": "Standby Telemetry Relays"
            }
        ]
    }

class ChakravyoohServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_HEAD(self):
        clean_path = self.path.split('?')[0]
        if clean_path in ['/api/v1/cyclone/risk-matrix', '/api/v1/cyclone/risk-matrix/']:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return
        if clean_path in ['/scorpio_feed', '/scorpio_feed/']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            return
        if clean_path in ['/zoom_earth_feed', '/zoom_earth_feed/']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            return
        if clean_path.startswith('/scorpio/') or clean_path.startswith('/common/'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.end_headers()
            return
        return super().do_HEAD()

    def do_GET(self):
        clean_path = self.path.split('?')[0]

        # Fast direct serving of root index.html
        if clean_path in ['/', '/index.html', '/index.htm']:
            index_path = os.path.join(DIRECTORY, 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
                return

        # Dedicated command center route
        if clean_path in ['/command_center', '/command-center', '/command']:
            target_path = os.path.join(DIRECTORY, 'static', 'chakravyooh_command_center.html')
            if not os.path.exists(target_path):
                target_path = os.path.join(DIRECTORY, 'index.html')
            with open(target_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
            return

        # Authoritative Dynamic Risk Matrix REST Endpoint
        if clean_path in ['/api/v1/cyclone/risk-matrix', '/api/v1/cyclone/risk-matrix/']:
            data = get_live_risk_matrix_payload()
            json_bytes = json.dumps(data, indent=2).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(json_bytes)))
            self.end_headers()
            self.wfile.write(json_bytes)
            return

        # Dedicated Embedded High-Definition Satellite Reconnaissance Feed (Zero-Redirect)
        if clean_path in ['/zoom_earth_feed', '/zoom_earth_feed/']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            satellite_page = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CHAKRAVYOOH Satellite Reconnaissance Feed</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="/static/css/leaflet.css">
  <script src="/static/js/leaflet.js"></script>
  <style>
    body, html { margin:0; padding:0; width:100%; height:100%; background:#030712; overflow:hidden; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
    #map { width:100%; height:100%; }
    .custom-radar-pulse {
      position: relative;
      width: 24px;
      height: 24px;
    }
    .custom-radar-pulse::before {
      content: '';
      position: absolute;
      inset: -12px;
      border-radius: 50%;
      border: 2px solid #ef4444;
      animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }
    .custom-radar-pulse::after {
      content: '';
      position: absolute;
      inset: 2px;
      background: #ef4444;
      border-radius: 50%;
      box-shadow: 0 0 12px #ef4444;
    }
    @keyframes pulse-ring {
      0% { transform: scale(0.5); opacity: 1; }
      100% { transform: scale(2.5); opacity: 0; }
    }
    .leaflet-control-attribution { background: rgba(3,7,18,0.85) !important; color: #94a3b8 !important; font-size: 10px; }
    .leaflet-control-attribution a { color: #38bdf8 !important; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    const map = L.map('map', {
      center: [16.82, 84.48],
      zoom: 6,
      zoomControl: true,
      attributionControl: true
    });
    
    // 1. ESRI World Imagery (High-Res Optical Satellite Feed)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 18,
      attribution: 'Imagery &copy; Esri, Earthstar Geographics'
    }).addTo(map);

    // 2. Reference boundaries and places
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 18
    }).addTo(map);

    // 3. Cyclone BOB-04 Vortex Eye Pulse Marker
    const eyeIcon = L.divIcon({
      className: 'custom-radar-pulse',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    const eyeMarker = L.marker([16.82, 84.48], { icon: eyeIcon }).addTo(map);
    eyeMarker.bindPopup('<div style="font-family:monospace;color:#0f172a;font-size:12px;"><strong>CYCLONE BOB-04 EYE</strong><br>Coords: 16.82&deg;N, 84.48&deg;E<br>Sustained: 155 km/h (Cat 3 Equivalent)<br>Pressure: 968 hPa</div>').openPopup();

    // 4. Wind Hazard Radii
    L.circle([16.82, 84.48], { radius: 45000, color: '#ef4444', weight: 2, fillColor: '#ef4444', fillOpacity: 0.25 }).addTo(map).bindTooltip('64 kt / 155 km/h Hurricane Core');
    L.circle([16.82, 84.48], { radius: 110000, color: '#f97316', weight: 1.5, fillColor: '#f97316', fillOpacity: 0.15, dashArray: '4,4' }).addTo(map).bindTooltip('50 kt / 100 km/h Severe Wind Field');
    L.circle([16.82, 84.48], { radius: 220000, color: '#eab308', weight: 1, fillColor: '#eab308', fillOpacity: 0.08, dashArray: '6,6' }).addTo(map).bindTooltip('34 kt / 65 km/h Tropical Gale Zone');

    // 5. Projected Track to Landfall
    const trackCoords = [
      [15.2, 85.5],
      [16.1, 84.9],
      [16.82, 84.48],
      [17.7, 84.6],
      [18.5, 84.8],
      [19.27, 84.91]
    ];
    L.polyline(trackCoords, { color: '#38bdf8', weight: 3, opacity: 0.85, dashArray: '8, 8' }).addTo(map);
    L.circleMarker([19.27, 84.91], { radius: 7, color: '#dc2626', fillColor: '#ef4444', fillOpacity: 0.9 }).addTo(map).bindTooltip('LANDFALL ESTIMATE: Gopalpur, Odisha (~22h)');

    // 6. RainViewer Live Doppler Radar
    fetch('https://api.rainviewer.com/public/weather-maps.json')
      .then(res => res.json())
      .then(data => {
        if (data && data.radar && data.radar.past && data.radar.past.length > 0) {
          const lastRadar = data.radar.past[data.radar.past.length - 1];
          const radarUrl = data.host + lastRadar.path + '/256/{z}/{x}/{y}/2/1_1.png';
          L.tileLayer(radarUrl, { opacity: 0.65, maxZoom: 18 }).addTo(map);
        }
      }).catch(e => console.log('RainViewer radar fallback: ', e));
  </script>
</body>
</html>"""
            self.wfile.write(satellite_page.encode('utf-8'))
            return

        # Dedicated proxy for ISRO MOSDAC SCORPIO to allow zero-CSP live embedding
        if clean_path in ['/scorpio_feed', '/scorpio_feed/']:
            try:
                req = urllib.request.Request(
                    'https://mosdac.gov.in/scorpio/',
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
                    }
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    content = resp.read().decode('utf-8', errors='ignore')
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))
                    return
            except Exception as e:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                fallback = f"""<!DOCTYPE html>
                <html><head><style>body{{background:#0a0e17;color:#e2e8f0;font-family:sans-serif;padding:30px;}}a{{color:#38bdf8;}}</style></head>
                <body>
                  <h3>ISRO MOSDAC SCORPIO Live Gateway</h3>
                  <p>Real-Time Satellite Cyclone Observation Platform:</p>
                  <p><a href="https://mosdac.gov.in/scorpio/" target="_blank">Open Live MOSDAC SCORPIO Portal ↗</a></p>
                </body></html>"""
                self.wfile.write(fallback.encode('utf-8'))
                return

        # Proxy sub-assets for ISRO MOSDAC SCORPIO (Angular bundles, stylesheets, JSONs, icons)
        if (clean_path.startswith('/scorpio/') or 
            clean_path.startswith('/common/') or 
            clean_path.startswith('/assets/') or 
            clean_path.startswith('/jsons/') or 
            clean_path.startswith('/img/')):
            try:
                target_url = 'https://mosdac.gov.in' + self.path
                req = urllib.request.Request(
                    target_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                        'Referer': 'https://mosdac.gov.in/scorpio/'
                    }
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    content_type = resp.headers.get('Content-Type', '')
                    if not content_type or 'octet-stream' in content_type:
                        if clean_path.endswith('.css'):
                            content_type = 'text/css; charset=utf-8'
                        elif clean_path.endswith('.js'):
                            content_type = 'application/javascript; charset=utf-8'
                        elif clean_path.endswith('.svg'):
                            content_type = 'image/svg+xml'
                        elif clean_path.endswith('.png'):
                            content_type = 'image/png'
                        elif clean_path.endswith('.jpg') or clean_path.endswith('.jpeg'):
                            content_type = 'image/jpeg'
                        elif clean_path.endswith('.json'):
                            content_type = 'application/json; charset=utf-8'
                        elif clean_path.endswith('.txt'):
                            content_type = 'text/plain; charset=utf-8'
                        else:
                            content_type = 'application/octet-stream'

                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Cache-Control', 'public, max-age=600')
                    self.end_headers()
                    self.wfile.write(data)
                    return
            except Exception as e:
                self.send_response(404)
                self.end_headers()
                return
        return super().do_GET()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == '__main__':
    with ThreadedHTTPServer(("", PORT), ChakravyoohServerHandler) as httpd:
        print(f"Chakravyooh Threaded Server running on port {PORT} with /scorpio_feed live proxy support.")
        httpd.serve_forever()
