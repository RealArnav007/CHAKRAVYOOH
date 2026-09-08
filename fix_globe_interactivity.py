#!/usr/bin/env python3
"""
fix_globe_interactivity.py
Upgrades the 3D Earth Globe interaction system with unified PointerEvents,
pointer capture, multi-target drag capture on #heroGlobeSection, and touch-action: none.
"""

with open('update_portal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update the interaction handlers and event listeners in initInteractiveGlobe
old_interaction_block = """      // 8. Interaction State & Event Listeners
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
      container.addEventListener('wheel', onWheel, { passive: false });"""

new_interaction_block = """      // 8. Interaction State & Unified Pointer Event Listeners
      let isDragging = false;
      let prevMouseX = 0;
      let prevMouseY = 0;
      let targetRotY = globeGroup.rotation.y;
      let targetRotX = globeGroup.rotation.x;
      let targetCamDist = initialDist;
      let autoRotate = state.globeAutoRotate !== false;
      let polarAngle = 0;

      // Prevent native selection / gesture hijacking on canvas
      container.style.touchAction = 'none';
      container.style.userSelect = 'none';
      if (renderer && renderer.domElement) {
        renderer.domElement.style.touchAction = 'none';
        renderer.domElement.style.userSelect = 'none';
        renderer.domElement.style.cursor = 'grab';
      }

      // Universal Pointer Down Handler
      function onPointerDown(e) {
        // If clicking on an active button, link, or the dock pill, let it handle its own click
        if (e.target && e.target.closest && e.target.closest('button, a, input, select, textarea, [role="button"], #heroDock')) {
          return;
        }
        isDragging = true;
        prevMouseX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
        prevMouseY = e.clientY || (e.touches && e.touches[0].clientY) || 0;

        container.style.cursor = 'grabbing';
        if (renderer && renderer.domElement) renderer.domElement.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';

        if (e.target && e.target.setPointerCapture && e.pointerId !== undefined) {
          try { e.target.setPointerCapture(e.pointerId); } catch (err) {}
        }
      }

      // Universal Pointer Move Handler
      function onPointerMove(e) {
        if (!isDragging) return;
        const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
        const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
        const dx = clientX - prevMouseX;
        const dy = clientY - prevMouseY;
        prevMouseX = clientX;
        prevMouseY = clientY;

        targetRotY += dx * 0.0065;
        targetRotX += dy * 0.0065;
        // Clamp vertical pitch to prevent gimbal flip
        targetRotX = Math.max(-1.35, Math.min(1.35, targetRotX));
      }

      // Universal Pointer Up / End Handler
      function onPointerUp(e) {
        if (!isDragging) return;
        isDragging = false;
        container.style.cursor = 'grab';
        if (renderer && renderer.domElement) renderer.domElement.style.cursor = 'grab';
        document.body.style.userSelect = '';
        if (e && e.target && e.target.releasePointerCapture && e.pointerId !== undefined) {
          try { e.target.releasePointerCapture(e.pointerId); } catch (err) {}
        }
      }

      // Zoom via Mouse Wheel
      function onWheel(e) {
        const isOverGlobe = e.target.closest('#' + containerId) || e.target.closest('#heroGlobeSection');
        if (isOverGlobe) {
          e.preventDefault();
          targetCamDist += e.deltaY * 0.0022;
          targetCamDist = Math.max(1.32, Math.min(4.5, targetCamDist));
        }
      }

      // Attach interaction listeners across container, canvas, and hero section
      const attachTargets = [container];
      if (renderer && renderer.domElement) attachTargets.push(renderer.domElement);
      const heroSection = document.getElementById('heroGlobeSection');
      if (containerId === 'prefaceInteractiveGlobe' && heroSection) {
        attachTargets.push(heroSection);
      }

      attachTargets.forEach(tgt => {
        if (!tgt) return;
        tgt.addEventListener('pointerdown', onPointerDown);
        tgt.addEventListener('mousedown', onPointerDown);
        tgt.addEventListener('touchstart', onPointerDown, { passive: true });
        tgt.addEventListener('wheel', onWheel, { passive: false });
      });

      window.addEventListener('pointermove', onPointerMove, { passive: false });
      window.addEventListener('pointerup', onPointerUp);
      window.addEventListener('pointercancel', onPointerUp);
      window.addEventListener('mousemove', onPointerMove);
      window.addEventListener('mouseup', onPointerUp);
      window.addEventListener('touchmove', onPointerMove, { passive: true });
      window.addEventListener('touchend', onPointerUp);"""

if old_interaction_block in code:
    code = code.replace(old_interaction_block, new_interaction_block, 1)
    print("Successfully upgraded globe interaction event listeners.")
else:
    print("Warning: old_interaction_block not found directly.")

with open('update_portal.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved update_portal.py. Now executing to regenerate HTML files...")
