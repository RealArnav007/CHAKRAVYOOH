import os
import re

# Read current update_portal.py
with open('update_portal.py', 'r', encoding='utf-8') as f:
    portal_py = f.read()

# We need to ensure Three.js script is included in the <head>
if '/static/three.min.js' not in portal_py:
    portal_py = portal_py.replace(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">',
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">\n\n  <!-- Three.js for 3D Interactive Earth & Satellite Globe -->\n  <script src="/static/three.min.js"></script>'
    )

# Ensure state has heroBgMode and globeAutoRotate
if "heroBgMode: 'globe3d'" not in portal_py:
    portal_py = portal_py.replace(
        "activePortalView: 'portal',",
        "activePortalView: 'portal',\n\n      // Hero Exploration Background Mode: 'globe3d' | 'scorpio_stream'\n      heroBgMode: 'globe3d',\n      globeAutoRotate: true,\n      globeLayerSatellites: true,\n      globeLayerAtmosphere: true,\n      globeLayerBuoys: true,\n      globeLayerStormTrajectory: true,"
    )

# Prepare the JavaScript functions for 3D Globe
globe_js_code = '''
    // =========================================================================
    // THREE.JS 3D INTERACTIVE GLOBE & CYCLONE OBSERVATORY ENGINE
    // =========================================================================
    let activeGlobeInstances = {};
    let cachedEarthTexture = null;

    // Generate high-resolution procedural Earth texture with India & Bay of Bengal focus
    function createProceduralEarthCanvas() {
      if (cachedEarthTexture) return cachedEarthTexture;

      const canvas = document.createElement('canvas');
      canvas.width = 2048;
      canvas.height = 1024;
      const ctx = canvas.getContext('2d');
      if (!ctx) return null;

      // Deep Space Oceanic Gradient
      const oceanGrad = ctx.createLinearGradient(0, 0, 0, 1024);
      oceanGrad.addColorStop(0.0, '#040914');
      oceanGrad.addColorStop(0.2, '#06142a');
      oceanGrad.addColorStop(0.5, '#0b2347');
      oceanGrad.addColorStop(0.8, '#06142a');
      oceanGrad.addColorStop(1.0, '#040914');
      ctx.fillStyle = oceanGrad;
      ctx.fillRect(0, 0, 2048, 1024);

      // Lat / Lon Graticule Grid
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.12)';
      ctx.lineWidth = 1;
      for (let lat = -80; lat <= 80; lat += 20) {
        const y = ((90 - lat) / 180) * 1024;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(2048, y);
        ctx.stroke();
      }
      for (let lon = -180; lon <= 180; lon += 30) {
        const x = ((lon + 180) / 360) * 2048;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, 1024);
        ctx.stroke();
      }

      // Helper to project (lat, lon) -> (x, y)
      function coord(lat, lon) {
        return [
          ((lon + 180) / 360) * 2048,
          ((90 - lat) / 180) * 1024
        ];
      }

      function drawLandPoly(coords, fillColor, strokeColor, lineWidth = 1.2) {
        if (!coords || coords.length < 3) return;
        ctx.beginPath();
        const [x0, y0] = coord(coords[0][0], coords[0][1]);
        ctx.moveTo(x0, y0);
        for (let i = 1; i < coords.length; i++) {
          const [x, y] = coord(coords[i][0], coords[i][1]);
          ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();
        if (strokeColor) {
          ctx.strokeStyle = strokeColor;
          ctx.lineWidth = lineWidth;
          ctx.stroke();
        }
      }

      const landBase = '#0f1d33';
      const landBorder = '#1c3459';

      // Eurasia & North Africa
      drawLandPoly([
        [70, 20], [70, 160], [60, 170], [45, 140], [35, 120], [25, 105], [20, 95],
        [10, 78], [15, 65], [25, 55], [30, 32], [35, -5], [45, -5], [55, 10], [60, 25]
      ], landBase, landBorder, 1.2);

      // Africa
      drawLandPoly([
        [32, -5], [32, 32], [12, 51], [2, 45], [-12, 40], [-25, 33], [-35, 20],
        [-33, 17], [-15, 12], [5, 2], [15, -17], [25, -15]
      ], landBase, landBorder, 1.2);

      // Australia
      drawLandPoly([
        [-11, 132], [-14, 144], [-24, 153], [-37, 150], [-38, 140], [-32, 116], [-21, 114], [-15, 125]
      ], landBase, landBorder, 1.2);

      // Americas
      drawLandPoly([
        [70, -165], [70, -60], [50, -55], [30, -80], [20, -100], [30, -120], [55, -130], [65, -165]
      ], landBase, landBorder, 1.0);
      drawLandPoly([
        [12, -75], [5, -50], [-10, -35], [-35, -55], [-55, -70], [-40, -73], [-20, -70], [0, -80]
      ], landBase, landBorder, 1.0);

      // Southeast Asia / Malay Archipelago
      drawLandPoly([
        [22, 100], [15, 108], [5, 104], [-6, 106], [-8, 115], [-5, 120], [7, 117], [16, 106]
      ], '#132540', '#224470', 1.2);

      // HIGH-PRECISION FOCUS: INDIAN SUBCONTINENT (Bright Cyan Coastline & Institutional Glow)
      const indiaPolygon = [
        [35.5, 74.8], [34.5, 77.5], [32.0, 78.9], [29.5, 80.5], [27.0, 88.5],
        [27.5, 92.5], [26.0, 97.0], [24.0, 93.5], [22.5, 89.5], // Bengal Delta
        [21.5, 87.0], [19.8, 85.8], [19.26, 84.91], // Odisha (Gopalpur landfall target)
        [17.7, 83.3], [16.0, 80.8], [13.0, 80.3], [10.0, 79.8], [8.1, 77.5], // Kanyakumari
        [8.8, 76.5], [12.9, 74.8], [15.4, 73.8], [18.9, 72.8], [21.0, 72.5], // Mumbai / Konkan
        [21.7, 70.0], [22.5, 69.0], [23.8, 68.5], [24.5, 71.0], [28.0, 70.0], [31.0, 74.5], [35.5, 74.8]
      ];
      drawLandPoly(indiaPolygon, '#182f52', '#38bdf8', 2.6);

      // Sri Lanka
      drawLandPoly([
        [9.8, 80.2], [8.0, 81.8], [6.0, 80.6], [7.2, 79.8]
      ], '#182f52', '#38bdf8', 2.0);

      // Bay of Bengal Cyclone Operations Basin (Target Boundary & Hatching)
      const bobPolygon = [[22.5, 85.0], [22.5, 93.5], [9.0, 93.5], [9.0, 80.0], [15.0, 80.0]];
      ctx.beginPath();
      const [bx0, by0] = coord(bobPolygon[0][0], bobPolygon[0][1]);
      ctx.moveTo(bx0, by0);
      for (let i = 1; i < bobPolygon.length; i++) {
        const [bx, by] = coord(bobPolygon[i][0], bobPolygon[i][1]);
        ctx.lineTo(bx, by);
      }
      ctx.closePath();
      ctx.fillStyle = 'rgba(14, 165, 233, 0.14)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
      ctx.setLineDash([8, 6]);
      ctx.lineWidth = 1.6;
      ctx.stroke();
      ctx.setLineDash([]);

      // Cyclone BOB-04 Vortex Cloud Bands Texture on Map
      const [cx0, cy0] = coord(16.82, 84.48);
      const cycGrad = ctx.createRadialGradient(cx0, cy0, 6, cx0, cy0, 90);
      cycGrad.addColorStop(0.0, 'rgba(239, 68, 68, 0.85)');
      cycGrad.addColorStop(0.2, 'rgba(255, 255, 255, 0.7)');
      cycGrad.addColorStop(0.5, 'rgba(186, 230, 253, 0.35)');
      cycGrad.addColorStop(1.0, 'rgba(14, 165, 233, 0)');
      ctx.fillStyle = cycGrad;
      ctx.beginPath();
      ctx.arc(cx0, cy0, 90, 0, Math.PI * 2);
      ctx.fill();

      // Atmospheric cloud bands across equatorial ITCZ
      ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.beginPath();
      ctx.ellipse(1024, 512, 800, 40, 0.05, 0, Math.PI * 2);
      ctx.fill();

      const texture = new THREE.CanvasTexture(canvas);
      texture.wrapS = THREE.ClampToEdgeWrapping;
      texture.wrapT = THREE.ClampToEdgeWrapping;
      cachedEarthTexture = texture;
      return texture;
    }

    // Convert (Latitude, Longitude, Radius) to 3D Three.js Vector3
    function latLonToVector3(lat, lon, radius = 1.0) {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lon + 180) * (Math.PI / 180);
      const x = -(radius * Math.sin(phi) * Math.cos(theta));
      const y = radius * Math.cos(phi);
      const z = radius * Math.sin(phi) * Math.sin(theta);
      return new THREE.Vector3(x, y, z);
    }

    // Core interactive 3D Globe initializer
    function initInteractiveGlobe(containerId, options = {}) {
      const container = document.getElementById(containerId);
      if (!container || typeof THREE === 'undefined') return;

      // Teardown any existing instance for this container
      if (activeGlobeInstances[containerId]) {
        try {
          cancelAnimationFrame(activeGlobeInstances[containerId].animId);
          activeGlobeInstances[containerId].renderer.dispose();
          container.innerHTML = '';
        } catch (e) {}
        delete activeGlobeInstances[containerId];
      }

      const width = container.clientWidth || container.offsetWidth || 800;
      const height = container.clientHeight || container.offsetHeight || 500;

      // 1. Scene & Camera Setup
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 1000);
      const initialDist = options.initialDistance || 2.45;
      camera.position.set(0, 0.35, initialDist);

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setClearColor(0x000000, 0);
      container.appendChild(renderer.domElement);

      // 2. Lighting (Deep Space Sun + Subtle Atmospheric Specular)
      const ambientLight = new THREE.AmbientLight(0x334155, 1.2);
      scene.add(ambientLight);

      const sunLight = new THREE.DirectionalLight(0xffffff, 2.2);
      sunLight.position.set(5, 3, 5);
      scene.add(sunLight);

      const rimLight = new THREE.DirectionalLight(0x0ea5e9, 1.0);
      rimLight.position.set(-5, -2, -3);
      scene.add(rimLight);

      // 3. Main Rotating Globe Group
      const globeGroup = new THREE.Group();
      // Default orientation: Center Indian Subcontinent & Bay of Bengal
      globeGroup.rotation.y = Math.PI * 0.96;
      globeGroup.rotation.x = 0.28;
      scene.add(globeGroup);

      // Earth Sphere
      const earthRadius = 1.0;
      const earthGeo = new THREE.SphereGeometry(earthRadius, 64, 64);
      const earthTex = createProceduralEarthCanvas();
      const earthMat = new THREE.MeshStandardMaterial({
        map: earthTex,
        roughness: 0.65,
        metalness: 0.18,
        wireframe: false
      });
      const earthMesh = new THREE.Mesh(earthGeo, earthMat);
      globeGroup.add(earthMesh);

      // Earth Atmospheric Glow Outer Shell
      const atmoGeo = new THREE.SphereGeometry(earthRadius * 1.035, 48, 48);
      const atmoMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.16,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending
      });
      const atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
      globeGroup.add(atmoMesh);

      // Equator & Tropic of Cancer Reference Rings
      const equatorPts = [];
      for (let i = 0; i <= 64; i++) {
        const a = (i / 64) * Math.PI * 2;
        equatorPts.push(new THREE.Vector3(Math.cos(a) * 1.008, 0, Math.sin(a) * 1.008));
      }
      const equatorGeo = new THREE.BufferGeometry().setFromPoints(equatorPts);
      const equatorMat = new THREE.LineBasicMaterial({ color: 0x0284c7, transparent: true, opacity: 0.45 });
      const equatorLine = new THREE.Line(equatorGeo, equatorMat);
      globeGroup.add(equatorLine);

      // Tropic of Cancer (23.5°N) — Cyclone Genesis Belt
      const cancerPts = [];
      const cancerY = Math.sin(23.5 * Math.PI / 180) * 1.008;
      const cancerR = Math.cos(23.5 * Math.PI / 180) * 1.008;
      for (let i = 0; i <= 64; i++) {
        const a = (i / 64) * Math.PI * 2;
        cancerPts.push(new THREE.Vector3(Math.cos(a) * cancerR, cancerY, Math.sin(a) * cancerR));
      }
      const cancerGeo = new THREE.BufferGeometry().setFromPoints(cancerPts);
      const cancerMat = new THREE.LineDashedMaterial({ color: 0xf59e0b, dashSize: 0.05, gapSize: 0.04, transparent: true, opacity: 0.5 });
      const cancerLine = new THREE.Line(cancerGeo, cancerMat);
      cancerLine.computeLineDistances();
      globeGroup.add(cancerLine);

      // 4. CYCLONE BOB-04 3D VORTEX & LANDFALL TRAJECTORY
      const cycloneGroup = new THREE.Group();
      const cycPos = latLonToVector3(16.82, 84.48, earthRadius * 1.012);
      cycloneGroup.position.copy(cycPos);
      cycloneGroup.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), cycPos.clone().normalize());

      // Multi-layer rotating spiral vortex
      const vortexArms = new THREE.Group();
      for (let layer = 0; layer < 4; layer++) {
        const radius = 0.06 + layer * 0.035;
        const ringGeo = new THREE.RingGeometry(radius - 0.012, radius, 32);
        const ringMat = new THREE.MeshBasicMaterial({
          color: layer === 0 ? 0xef4444 : (layer === 1 ? 0xf97316 : 0x38bdf8),
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.7 - layer * 0.15,
          blending: THREE.AdditiveBlending
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 2;
        vortexArms.add(ring);
      }
      cycloneGroup.add(vortexArms);

      // Eye of the Storm: Glowing Center Core
      const eyeGeo = new THREE.SphereGeometry(0.02, 16, 16);
      const eyeMat = new THREE.MeshBasicMaterial({ color: 0xff0040, wireframe: false });
      const eyeMesh = new THREE.Mesh(eyeGeo, eyeMat);
      cycloneGroup.add(eyeMesh);
      globeGroup.add(cycloneGroup);

      // Projected Landfall Trajectory Arc (BOB-04 -> Gopalpur, Odisha)
      const gopalpurPos = latLonToVector3(19.26, 84.91, earthRadius * 1.012);
      const midPoint = new THREE.Vector3().addVectors(cycPos, gopalpurPos).multiplyScalar(0.5).normalize().multiplyScalar(earthRadius * 1.08);
      const curve = new THREE.QuadraticBezierCurve3(cycPos, midPoint, gopalpurPos);
      const arcPoints = curve.getPoints(32);
      const arcGeo = new THREE.BufferGeometry().setFromPoints(arcPoints);
      const arcMat = new THREE.LineDashedMaterial({ color: 0xef4444, dashSize: 0.025, gapSize: 0.018, transparent: true, opacity: 0.95 });
      const arcLine = new THREE.Line(arcGeo, arcMat);
      arcLine.computeLineDistances();
      globeGroup.add(arcLine);

      // Gopalpur Landfall Target Pin
      const targetPinGeo = new THREE.CylinderGeometry(0.003, 0.003, 0.04, 8);
      const targetPinMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
      const targetPin = new THREE.Mesh(targetPinGeo, targetPinMat);
      targetPin.position.copy(gopalpurPos);
      targetPin.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), gopalpurPos.clone().normalize());
      globeGroup.add(targetPin);

      // 5. INCOIS MOORED BUOY BEACONS (BD08 & BD10)
      const buoys = [
        { id: 'BD08', lat: 18.2, lon: 89.7, name: 'INCOIS BD08 (North Bay)' },
        { id: 'BD10', lat: 14.0, lon: 87.0, name: 'INCOIS BD10 (Central Bay)' }
      ];
      const buoyMeshes = [];
      buoys.forEach(b => {
        const bPos = latLonToVector3(b.lat, b.lon, earthRadius * 1.008);
        const bGroup = new THREE.Group();
        bGroup.position.copy(bPos);
        bGroup.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), bPos.clone().normalize());

        const buoyCore = new THREE.Mesh(new THREE.SphereGeometry(0.014, 12, 12), new THREE.MeshBasicMaterial({ color: 0x10b981 }));
        const buoyRing = new THREE.Mesh(new THREE.RingGeometry(0.02, 0.035, 16), new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.5, side: THREE.DoubleSide }));
        buoyRing.rotation.x = Math.PI / 2;
        bGroup.add(buoyCore);
        bGroup.add(buoyRing);
        globeGroup.add(bGroup);
        buoyMeshes.push({ group: bGroup, ring: buoyRing });
      });

      // 6. INDIAN SATELLITE FLEET (INSAT-3DR & EOS-06)
      // Geostationary Orbit Ring for INSAT-3DR (Distance ~2.35x Earth Radius)
      const geoRadius = 2.35;
      const geoRingPts = [];
      for (let i = 0; i <= 96; i++) {
        const a = (i / 96) * Math.PI * 2;
        geoRingPts.push(new THREE.Vector3(Math.cos(a) * geoRadius, 0, Math.sin(a) * geoRadius));
      }
      const geoOrbit = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(geoRingPts),
        new THREE.LineBasicMaterial({ color: 0x2563eb, transparent: true, opacity: 0.35 })
      );
      globeGroup.add(geoOrbit);

      // INSAT-3DR Satellite at 82.0°E Geostationary slot
      const insatPos = latLonToVector3(0, 82.0, geoRadius);
      const insatGroup = new THREE.Group();
      insatGroup.position.copy(insatPos);
      insatGroup.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), insatPos.clone().normalize());

      // Satellite Bus (Gold Foil Cube)
      const satBus = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.045, 0.06), new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.3, metalness: 0.8 }));
      insatGroup.add(satBus);

      // Solar Array Wings (Navy Blue Cells)
      const solarWing1 = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.035, 0.004), new THREE.MeshStandardMaterial({ color: 0x1e3a8a, metalness: 0.5 }));
      solarWing1.position.set(0.1, 0, 0);
      const solarWing2 = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.035, 0.004), new THREE.MeshStandardMaterial({ color: 0x1e3a8a, metalness: 0.5 }));
      solarWing2.position.set(-0.1, 0, 0);
      insatGroup.add(solarWing1);
      insatGroup.add(solarWing2);

      // Sensor Scanning Cone (projecting beam toward Bay of Bengal)
      const beamTarget = latLonToVector3(16.82, 84.48, earthRadius);
      const coneGeo = new THREE.ConeGeometry(0.42, geoRadius - earthRadius, 24, 1, true);
      const coneMat = new THREE.MeshBasicMaterial({
        color: 0x0284c7,
        transparent: true,
        opacity: 0.12,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending
      });
      const scanCone = new THREE.Mesh(coneGeo, coneMat);
      // Orient cone towards Earth center
      scanCone.position.set(0, 0, -(geoRadius - earthRadius) / 2);
      scanCone.rotation.x = -Math.PI / 2;
      insatGroup.add(scanCone);
      globeGroup.add(insatGroup);

      // EOS-06 Polar Orbit (Inclined 98°)
      const polarGroup = new THREE.Group();
      polarGroup.rotation.z = 1.71; // 98 deg inclination
      const polarPts = [];
      const polarRadius = 1.45;
      for (let i = 0; i <= 64; i++) {
        const a = (i / 64) * Math.PI * 2;
        polarPts.push(new THREE.Vector3(Math.cos(a) * polarRadius, 0, Math.sin(a) * polarRadius));
      }
      const polarOrbit = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(polarPts),
        new THREE.LineBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.3 })
      );
      polarGroup.add(polarOrbit);

      const eosSat = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.035, 0.04), new THREE.MeshStandardMaterial({ color: 0x34d399, metalness: 0.6 }));
      polarGroup.add(eosSat);
      globeGroup.add(polarGroup);

      // 7. Background Twinkling Starfield
      const starsCount = 650;
      const starGeo = new THREE.BufferGeometry();
      const starPos = [];
      for (let i = 0; i < starsCount; i++) {
        const r = 25 + Math.random() * 40;
        const u = Math.random();
        const v = Math.random();
        const theta = 2 * Math.PI * u;
        const phi = Math.acos(2 * v - 1);
        starPos.push(r * Math.sin(phi) * Math.cos(theta));
        starPos.push(r * Math.sin(phi) * Math.sin(theta));
        starPos.push(r * Math.cos(phi));
      }
      starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
      const starMat = new THREE.PointsMaterial({ color: 0x94a3b8, size: 0.6, transparent: true, opacity: 0.7 });
      const stars = new THREE.Points(starGeo, starMat);
      scene.add(stars);

      // 8. Interaction State & Event Listeners
      let isDragging = false;
      let prevMouseX = 0;
      let prevMouseY = 0;
      let targetRotY = globeGroup.rotation.y;
      let targetRotX = globeGroup.rotation.x;
      let targetCamDist = initialDist;
      let autoRotate = state.globeAutoRotate !== false;
      let polarAngle = 0;

      // Pointer Event Handlers
      function onPointerDown(e) {
        isDragging = true;
        prevMouseX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
        prevMouseY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
      }

      function onPointerMove(e) {
        if (!isDragging) return;
        const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
        const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
        const dx = clientX - prevMouseX;
        const dy = clientY - prevMouseY;
        prevMouseX = clientX;
        prevMouseY = clientY;

        targetRotY += dx * 0.0055;
        targetRotX += dy * 0.0055;
        // Clamp vertical pitch to prevent gimbal flip
        targetRotX = Math.max(-1.25, Math.min(1.25, targetRotX));
      }

      function onPointerUp() {
        isDragging = false;
      }

      function onWheel(e) {
        e.preventDefault();
        targetCamDist += e.deltaY * 0.0018;
        targetCamDist = Math.max(1.5, Math.min(4.8, targetCamDist));
      }

      container.addEventListener('mousedown', onPointerDown);
      window.addEventListener('mousemove', onPointerMove);
      window.addEventListener('mouseup', onPointerUp);

      container.addEventListener('touchstart', onPointerDown, { passive: true });
      window.addEventListener('touchmove', onPointerMove, { passive: true });
      window.addEventListener('touchend', onPointerUp);
      container.addEventListener('wheel', onWheel, { passive: false });

      // Window Resize Handler
      function handleResize() {
        if (!container) return;
        const w = container.clientWidth || container.offsetWidth || 800;
        const h = container.clientHeight || container.offsetHeight || 500;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      }
      window.addEventListener('resize', handleResize);

      // Animation Loop
      let animId = null;
      let pulseTime = 0;

      function animate() {
        animId = requestAnimationFrame(animate);
        pulseTime += 0.025;

        // Auto rotation when not dragging
        if (autoRotate && !isDragging) {
          targetRotY += 0.0012;
        }

        // Smooth damping interpolation
        globeGroup.rotation.y += (targetRotY - globeGroup.rotation.y) * 0.08;
        globeGroup.rotation.x += (targetRotX - globeGroup.rotation.x) * 0.08;
        camera.position.z += (targetCamDist - camera.position.z) * 0.08;

        // Rotate Cyclone BOB-04 Vortex Arms (Counter-Clockwise cyclonic rotation)
        vortexArms.rotation.z += 0.035;

        // Pulse Eye of Cyclone Core
        const eyeScale = 1.0 + Math.sin(pulseTime * 3) * 0.35;
        eyeMesh.scale.set(eyeScale, eyeScale, eyeScale);

        // Pulse INCOIS buoy rings
        buoyMeshes.forEach((bm, idx) => {
          const s = 1.0 + Math.sin(pulseTime * 2.5 + idx) * 0.4;
          bm.ring.scale.set(s, s, s);
        });

        // Orbit EOS-06 satellite around polar loop
        polarAngle += 0.015;
        eosSat.position.set(Math.cos(polarAngle) * polarRadius, 0, Math.sin(polarAngle) * polarRadius);

        // Slowly twinkle starfield
        stars.rotation.y += 0.00015;

        renderer.render(scene, camera);
      }

      animate();

      // Store instance handles for external controls
      activeGlobeInstances[containerId] = {
        scene,
        camera,
        renderer,
        globeGroup,
        animId,
        setTargetRotation: (rx, ry, dist) => {
          targetRotX = rx;
          targetRotY = ry;
          if (dist) targetCamDist = dist;
        },
        toggleAutoRotate: () => {
          autoRotate = !autoRotate;
          return autoRotate;
        },
        setAutoRotate: (val) => {
          autoRotate = val;
        }
      };
    }

    // Preset camera focus transitions
    function focusGlobeTarget(target) {
      Object.keys(activeGlobeInstances).forEach(id => {
        const inst = activeGlobeInstances[id];
        if (!inst) return;
        if (target === 'cyclone') {
          // Bay of Bengal Cyclone BOB-04 (16.82N, 84.48E)
          inst.setTargetRotation(0.32, Math.PI * 0.965, 1.85);
        } else if (target === 'insat') {
          // INSAT-3DR Geostationary Orbit slot (82.0E)
          inst.setTargetRotation(0.08, Math.PI * 0.95, 2.75);
        } else if (target === 'india') {
          // Centered on Indian Subcontinent (20N, 78E)
          inst.setTargetRotation(0.35, Math.PI * 0.94, 2.15);
        } else if (target === 'global') {
          // Full Earth Overview
          inst.setTargetRotation(0.25, Math.PI * 0.96, 3.2);
        }
      });
    }

    function toggleGlobeAutoRotate() {
      let isNowRunning = false;
      Object.keys(activeGlobeInstances).forEach(id => {
        isNowRunning = activeGlobeInstances[id].toggleAutoRotate();
      });
      state.globeAutoRotate = isNowRunning;
      renderApp();
    }

    function setGlobeBgMode(mode) {
      state.heroBgMode = mode;
      renderApp();
    }

    // Mount all visible globe containers
    function mountAllGlobes() {
      if (typeof THREE === 'undefined') return;
      if (document.getElementById('nasaHeroGlobeContainer') && state.heroBgMode === 'globe3d') {
        initInteractiveGlobe('nasaHeroGlobeContainer', { initialDistance: 2.35 });
      }
      if (document.getElementById('orbitDeckGlobeContainer')) {
        initInteractiveGlobe('orbitDeckGlobeContainer', { initialDistance: 2.1 });
      }
    }
'''

# Find the spot before `renderNasaPortal()` to inject the Globe functions
if 'function initInteractiveGlobe' not in portal_py:
    portal_py = portal_py.replace(
        '    // =========================================================================\n    // NASA / ISRO STYLE FLAGSHIP EXPLORATION PORTAL (STARTING PAGE)\n    // =========================================================================',
        globe_js_code + '\n\n    // =========================================================================\n    // NASA / ISRO STYLE FLAGSHIP EXPLORATION PORTAL (STARTING PAGE)\n    // ========================================================================='
    )

# Now update the Hero section in renderNasaPortal()
# Old hero section background:
old_hero_bg = '''            <!-- Live SCORPIO Stream Background or Cosmic Storm Atmosphere -->
            <div class="absolute inset-0 w-full h-full pointer-events-none select-none">
              <iframe src="/scorpio_feed" class="w-full h-full border-0 transform scale-110 opacity-30 filter contrast-125 saturate-125"></iframe>
              <div class="absolute inset-0 bg-gradient-to-r from-[#070b14] via-[#070b14]/85 to-transparent"></div>
              <div class="absolute inset-0 bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/70"></div>
              <div class="absolute inset-0 opacity-10 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:24px_24px]"></div>
            </div>'''

new_hero_bg = '''            <!-- Interactive 3D Globe Background or Live SCORPIO Stream -->
            ${state.heroBgMode === 'globe3d' ? `
              <!-- Interactive 3D WebGL Earth & Cyclone Orbit Canvas -->
              <div id="nasaHeroGlobeContainer" class="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing overflow-hidden z-0"></div>
              <div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#070b14] via-[#070b14]/80 md:via-[#070b14]/65 to-transparent z-[1]"></div>
              <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/60 z-[1]"></div>
            ` : `
              <!-- Live ISRO MOSDAC SCORPIO Radar Stream -->
              <div class="absolute inset-0 w-full h-full pointer-events-none select-none z-0">
                <iframe src="/scorpio_feed" class="w-full h-full border-0 transform scale-105 opacity-35 filter contrast-125 saturate-125"></iframe>
                <div class="absolute inset-0 bg-gradient-to-r from-[#070b14] via-[#070b14]/85 to-transparent"></div>
                <div class="absolute inset-0 bg-gradient-to-t from-[#070b14] via-transparent to-[#070b14]/70"></div>
              </div>
            `}

            <!-- Floating 3D Globe HUD Quick Controls Bar -->
            <div class="absolute top-4 right-4 z-20 flex flex-wrap items-center gap-2 bg-[#0c1424]/90 border border-[#1e2e4a] backdrop-blur-md px-3 py-2 rounded-xl text-xs font-mono shadow-2xl">
              <span class="text-slate-400 text-[11px] hidden sm:inline">VIEWPORT:</span>
              <button onclick="setGlobeBgMode('globe3d')" class="px-2.5 py-1 rounded ${state.heroBgMode === 'globe3d' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-[#142034]'} transition-colors flex items-center gap-1">
                <span>🌐</span>
                <span>3D Earth</span>
              </button>
              <button onclick="setGlobeBgMode('scorpio_stream')" class="px-2.5 py-1 rounded ${state.heroBgMode === 'scorpio_stream' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300 hover:bg-[#142034]'} transition-colors flex items-center gap-1">
                <span>📡</span>
                <span>SCORPIO Stream</span>
              </button>
              <span class="text-slate-700">|</span>
              <button onclick="focusGlobeTarget('cyclone')" class="px-2 py-1 rounded text-red-300 hover:bg-red-950/60 border border-red-900/50 transition-colors" title="Center camera on Cyclone BOB-04 vortex">
                🌀 Eye Target
              </button>
              <button onclick="focusGlobeTarget('insat')" class="px-2 py-1 rounded text-blue-300 hover:bg-blue-950/60 border border-blue-900/50 transition-colors" title="Inspect INSAT-3DR Geostationary Orbit">
                🛰️ INSAT-3DR
              </button>
              <button onclick="toggleGlobeAutoRotate()" class="px-2 py-1 rounded text-slate-300 hover:bg-[#15233c] transition-colors" title="Toggle Auto-Rotation">
                ${state.globeAutoRotate ? '⏸️ Pause' : '▶️ Spin'}
              </button>
            </div>'''

if old_hero_bg in portal_py:
    portal_py = portal_py.replace(old_hero_bg, new_hero_bg)

# Also add the dedicated 3D Orbit Deck Section right after Section 3 (Hero) or before Section 4
orbit_deck_section = '''
          <!-- 3.5. DEDICATED 3D CYCLONE ORBIT DECK & ATMOSPHERIC OBSERVATORY -->
          <section class="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-4">
            <div class="mission-card border border-[#233856] overflow-hidden">
              <!-- Orbit Deck Header -->
              <div class="p-4 sm:p-5 bg-[#091122] border-b border-[#1b2b45] flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-blue-400 animate-pulse"></span>
                    <span class="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">3D SATELLITE ORBIT DECK & CYCLONE SIMULATION</span>
                    <span class="text-slate-600">•</span>
                    <span class="text-slate-300 font-mono text-xs">Full Interactive Telemetry Viewport</span>
                  </div>
                  <h3 class="text-lg sm:text-xl font-bold font-heading text-white mt-1">
                    Interactive 3D Earth: ISRO INSAT-3DR Geostationary Beam & Cyclone BOB-04 Vortex
                  </h3>
                  <p class="text-xs text-slate-400 mt-0.5">
                    Drag anywhere to rotate 360° orbital perspective. Scroll to zoom from geostationary altitude (35,786 km) to sea-level cyclone core.
                  </p>
                </div>

                <!-- Deck Quick Actions -->
                <div class="flex flex-wrap items-center gap-2 text-xs font-mono">
                  <button onclick="focusGlobeTarget('cyclone')" class="px-3 py-1.5 rounded-lg bg-red-950/80 hover:bg-red-900/80 text-red-300 border border-red-700/60 font-semibold transition-colors flex items-center gap-1.5">
                    <span>🌀</span>
                    <span>Focus Cyclone BOB-04</span>
                  </button>
                  <button onclick="focusGlobeTarget('insat')" class="px-3 py-1.5 rounded-lg bg-blue-950/80 hover:bg-blue-900/80 text-blue-300 border border-blue-700/60 font-semibold transition-colors flex items-center gap-1.5">
                    <span>🛰️</span>
                    <span>Focus INSAT-3DR</span>
                  </button>
                  <button onclick="focusGlobeTarget('india')" class="px-3 py-1.5 rounded-lg bg-[#142034] hover:bg-[#1e2f4c] text-slate-200 border border-[#223554] transition-colors">
                    🇮🇳 India & Bay Basin
                  </button>
                  <button onclick="focusGlobeTarget('global')" class="px-3 py-1.5 rounded-lg bg-[#142034] hover:bg-[#1e2f4c] text-slate-200 border border-[#223554] transition-colors">
                    🌍 Global View
                  </button>
                  <button onclick="toggleGlobeAutoRotate()" class="px-3 py-1.5 rounded-lg bg-[#0d1628] hover:bg-[#172542] text-slate-300 border border-[#1b2b45] transition-colors">
                    ${state.globeAutoRotate ? '⏸️ Pause Orbit' : '▶️ Resume Orbit'}
                  </button>
                </div>
              </div>

              <!-- Interactive 3D Canvas Container -->
              <div class="relative w-full h-[520px] bg-[#040813] overflow-hidden select-none">
                <div id="orbitDeckGlobeContainer" class="w-full h-full cursor-grab active:cursor-grabbing"></div>

                <!-- Floating 3D Telemetry Coordinates HUD (Top-Left) -->
                <div class="absolute top-4 left-4 z-10 p-3 rounded-xl bg-[#091122]/90 border border-[#1c2c47] backdrop-blur-md font-mono text-[11px] space-y-1 text-slate-300 pointer-events-none shadow-xl">
                  <div class="flex items-center gap-2 text-blue-400 font-bold border-b border-[#18263e] pb-1">
                    <span>🛰️</span>
                    <span>ISRO ORBITAL TELEMETRY</span>
                  </div>
                  <div class="flex justify-between gap-4">
                    <span class="text-slate-500">Vortex Eye:</span>
                    <span class="text-red-400 font-bold">16.82°N, 84.48°E</span>
                  </div>
                  <div class="flex justify-between gap-4">
                    <span class="text-slate-500">INSAT-3DR Slot:</span>
                    <span class="text-blue-300 font-bold">82.0°E (35,786 km)</span>
                  </div>
                  <div class="flex justify-between gap-4">
                    <span class="text-slate-500">Buoys Online:</span>
                    <span class="text-emerald-400 font-bold">BD08 / BD10 Active</span>
                  </div>
                  <div class="flex justify-between gap-4">
                    <span class="text-slate-500">Landfall Target:</span>
                    <span class="text-amber-300 font-bold">Gopalpur (19.26°N)</span>
                  </div>
                </div>

                <!-- Interactive Usage Cue (Bottom-Center) -->
                <div class="absolute bottom-3 inset-x-0 flex justify-center pointer-events-none">
                  <div class="px-3.5 py-1 rounded-full bg-[#0a1224]/85 border border-[#1e2e4a] backdrop-blur-md text-[10px] font-mono text-slate-400 flex items-center gap-2 shadow-lg">
                    <span>🖱️ Drag to rotate Earth</span>
                    <span>•</span>
                    <span>Scroll to zoom</span>
                    <span>•</span>
                    <span>Touch gestures supported</span>
                  </div>
                </div>
              </div>

              <!-- Deck Footer Telemetry -->
              <div class="p-3 bg-[#070d1a] border-t border-[#1b2b45] flex flex-wrap items-center justify-between text-xs font-mono text-slate-400">
                <div class="flex items-center gap-4">
                  <span>🌐 Coordinate System: <strong class="text-slate-200">WGS84 Earth Sphere</strong></span>
                  <span>⚡ Scan Frequency: <strong class="text-blue-400">15-min Rapid Multispectral</strong></span>
                  <span>🛡️ Resilience: <strong class="text-emerald-400">Mesh Handshake Synced</strong></span>
                </div>
                <span class="text-blue-400">Click & Drag to explore Bay of Bengal cyclonic dynamics</span>
              </div>
            </div>
          </section>
'''

if '<!-- 3.5. DEDICATED 3D CYCLONE ORBIT DECK' not in portal_py:
    portal_py = portal_py.replace(
        '          <!-- 4. FEATURED SPACE & OCEAN MISSIONS (NASA Missions Grid) -->',
        orbit_deck_section + '\n          <!-- 4. FEATURED SPACE & OCEAN MISSIONS (NASA Missions Grid) -->'
    )

# Hook mountAllGlobes() into renderApp()
if 'mountAllGlobes();' not in portal_py:
    # Inside renderApp() at the end, and inside DOMContentLoaded
    portal_py = portal_py.replace(
        "    // Main App Render Dispatcher\n    function renderApp() {",
        "    // Main App Render Dispatcher\n    function renderApp() {\n      setTimeout(mountAllGlobes, 50);"
    )
    portal_py = portal_py.replace(
        "    // =========================================================================\n    // MAIN APP RENDER DISPATCHER\n    // =========================================================================\n    function renderApp() {",
        "    // =========================================================================\n    // MAIN APP RENDER DISPATCHER\n    // =========================================================================\n    function renderApp() {\n      setTimeout(mountAllGlobes, 50);"
    )
    portal_py = portal_py.replace(
        "    document.addEventListener('DOMContentLoaded', () => {\n      renderApp();\n      startLoadingSequence();\n      fetchRealtimeWeather('gopalpur');\n    });",
        "    document.addEventListener('DOMContentLoaded', () => {\n      renderApp();\n      mountAllGlobes();\n      startLoadingSequence();\n      fetchRealtimeWeather('gopalpur');\n    });"
    )

# Write back update_portal.py
with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(portal_py)

print("Updated update_portal.py with interactive 3D Globe.")
