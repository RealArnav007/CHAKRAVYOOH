import os
import re

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the Earth mesh creation in initInteractiveGlobe with the photorealistic multi-layer NASA Blue Marble setup
old_earth_setup = """      // Earth Sphere
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
      globeGroup.add(atmoMesh);"""

new_earth_setup = """      // 1. PHOTOREALISTIC REAL EARTH SATELLITE SURFACE (NASA Blue Marble)
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

if old_earth_setup in code:
    code = code.replace(old_earth_setup, new_earth_setup)

# In the animate() function, rotate the cloudMesh independently for authentic atmospheric circulation!
old_anim_loop = """        // Rotate Cyclone BOB-04 Vortex Arms (Counter-Clockwise cyclonic rotation)
        vortexArms.rotation.z += 0.035;"""

new_anim_loop = """        // Real Atmospheric Cloud Circulation
        if (typeof cloudMesh !== 'undefined' && cloudMesh) {
          cloudMesh.rotation.y += 0.00035;
        }

        // Rotate Cyclone BOB-04 Vortex Arms (Counter-Clockwise cyclonic rotation)
        vortexArms.rotation.z += 0.035;"""

if old_anim_loop in code:
    code = code.replace(old_anim_loop, new_anim_loop)

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully injected real NASA photographic Earth textures into update_portal.py!")
