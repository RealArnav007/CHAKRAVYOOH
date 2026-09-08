import os
import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the lighting and Earth material in initInteractiveGlobe
old_lighting_and_material = """      // 2. Lighting (Deep Space Sun + Subtle Atmospheric Specular)
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

      // 1. PHOTOREALISTIC REAL EARTH SATELLITE SURFACE (NASA Blue Marble)
      const earthRadius = 1.0;
      const earthGeo = new THREE.SphereGeometry(earthRadius, 64, 64);
      const textureLoader = new THREE.TextureLoader();

      // Load authentic photographic NASA Earth textures
      const earthMap = textureLoader.load('/static/earth_atmos_2048.jpg');
      const normalMap = textureLoader.load('/static/earth_normal_2048.jpg');
      const specularMap = textureLoader.load('/static/earth_specular_2048.jpg');

      const earthMat = new THREE.MeshPhongMaterial({
        map: earthMap,
        normalMap: normalMap,
        normalScale: new THREE.Vector2(0.85, 0.85),
        specularMap: specularMap,
        specular: new THREE.Color(0x335577),
        shininess: 18
      });
      const earthMesh = new THREE.Mesh(earthGeo, earthMat);
      globeGroup.add(earthMesh);

      // 2. REAL SATELLITE CLOUD COVER LAYER (Transparent Atmospheric Shell)
      const cloudMap = textureLoader.load('/static/earth_clouds_1024.png');
      const cloudGeo = new THREE.SphereGeometry(earthRadius * 1.018, 64, 64);
      const cloudMat = new THREE.MeshLambertMaterial({
        map: cloudMap,
        transparent: true,
        opacity: 0.85,
        blending: THREE.NormalBlending
      });
      const cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
      globeGroup.add(cloudMesh);

      // 3. REAL ATMOSPHERIC FRESNEL GLOW SHELL
      const atmoGeo = new THREE.SphereGeometry(earthRadius * 1.032, 64, 64);
      const atmoMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.18,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending
      });
      const atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
      globeGroup.add(atmoMesh);"""

new_lighting_and_material = """      // Enable authentic color space rendering
      if (renderer.outputEncoding !== undefined) {
        renderer.outputEncoding = THREE.sRGBEncoding;
      }

      // 2. REALISTIC SPACE LIGHTING (Natural Solar Spectrum + Deep Space Contrast)
      // Deep space ambient light (subtle, prevents washed-out grey tones)
      const ambientLight = new THREE.AmbientLight(0x061120, 0.5);
      scene.add(ambientLight);

      // Primary Warm Solar Direct Light (illuminates Indian subcontinent naturally)
      const sunLight = new THREE.DirectionalLight(0xfffdf5, 2.6);
      sunLight.position.set(6, 2.5, 4.5);
      scene.add(sunLight);

      // Soft Deep-Space Earthshine Rim Light (soft royal blue, no artificial neon)
      const rimLight = new THREE.DirectionalLight(0x1d4ed8, 0.35);
      rimLight.position.set(-6, -2, -4);
      scene.add(rimLight);

      // 3. Main Rotating Globe Group
      const globeGroup = new THREE.Group();
      // Default orientation: Center Indian Subcontinent & Bay of Bengal directly in camera
      globeGroup.rotation.y = Math.PI * 0.96;
      globeGroup.rotation.x = 0.28;
      scene.add(globeGroup);

      // 1. PHOTOREALISTIC NASA BLUE MARBLE SURFACE
      const earthRadius = 1.0;
      const earthGeo = new THREE.SphereGeometry(earthRadius, 64, 64);
      const textureLoader = new THREE.TextureLoader();

      // Authentic NASA Blue Marble photographic satellite textures
      const earthMap = textureLoader.load('/static/earth_atmos_2048.jpg');
      if (earthMap.encoding !== undefined) earthMap.encoding = THREE.sRGBEncoding;
      const normalMap = textureLoader.load('/static/earth_normal_2048.jpg');
      const specularMap = textureLoader.load('/static/earth_specular_2048.jpg');

      const earthMat = new THREE.MeshPhongMaterial({
        map: earthMap,
        normalMap: normalMap,
        normalScale: new THREE.Vector2(0.55, 0.55),
        specularMap: specularMap,
        specular: new THREE.Color(0x223a54),
        shininess: 25
      });
      const earthMesh = new THREE.Mesh(earthGeo, earthMat);
      globeGroup.add(earthMesh);

      // 2. REAL TRANSPARENT SATELLITE CLOUDS (Subtle 50% opacity so vivid oceans & continents show through)
      const cloudMap = textureLoader.load('/static/earth_clouds_1024.png');
      const cloudGeo = new THREE.SphereGeometry(earthRadius * 1.014, 64, 64);
      const cloudMat = new THREE.MeshLambertMaterial({
        map: cloudMap,
        transparent: true,
        opacity: 0.52,
        blending: THREE.NormalBlending
      });
      const cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
      globeGroup.add(cloudMesh);

      // 3. NATURAL RAYLEIGH ATMOSPHERIC GLOW (Soft Royal Azure, NOT Neon Cyan)
      const atmoGeo = new THREE.SphereGeometry(earthRadius * 1.025, 64, 64);
      const atmoMat = new THREE.MeshBasicMaterial({
        color: 0x2563eb,
        transparent: true,
        opacity: 0.12,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending
      });
      const atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
      globeGroup.add(atmoMesh);"""

if old_lighting_and_material in code:
    code = code.replace(old_lighting_and_material, new_lighting_and_material)

# Also tone down the artificial equator and tropic lines so the real Earth looks pristine
code = code.replace(
    'const equatorMat = new THREE.LineBasicMaterial({ color: 0x0284c7, transparent: true, opacity: 0.45 });',
    'const equatorMat = new THREE.LineBasicMaterial({ color: 0x0284c7, transparent: true, opacity: 0.12 });'
)
code = code.replace(
    'const cancerMat = new THREE.LineDashedMaterial({ color: 0xf59e0b, dashSize: 0.05, gapSize: 0.04, transparent: true, opacity: 0.5 });',
    'const cancerMat = new THREE.LineDashedMaterial({ color: 0xf59e0b, dashSize: 0.05, gapSize: 0.04, transparent: true, opacity: 0.14 });'
)

# Refine Cyclone BOB-04 Vortex Arms to look like authentic cloud spirals instead of neon circles
old_vortex_rings = """      // Multi-layer rotating spiral vortex
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
      cycloneGroup.add(vortexArms);"""

new_vortex_rings = """      // Realistic Cyclone BOB-04 Spiral Cloud Arms
      const vortexArms = new THREE.Group();
      for (let layer = 0; layer < 4; layer++) {
        const radius = 0.05 + layer * 0.032;
        const ringGeo = new THREE.RingGeometry(radius - 0.015, radius, 32);
        const ringMat = new THREE.MeshBasicMaterial({
          color: layer === 0 ? 0xef4444 : 0xffffff,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: layer === 0 ? 0.7 : (0.45 - layer * 0.1),
          blending: THREE.AdditiveBlending
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 2;
        vortexArms.add(ring);
      }
      cycloneGroup.add(vortexArms);"""

if old_vortex_rings in code:
    code = code.replace(old_vortex_rings, new_vortex_rings)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully tuned Earth color coding, solar lighting, and atmospheric realism in update_portal.py!")
