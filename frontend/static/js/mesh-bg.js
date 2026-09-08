/* ==========================================================================
   PROJECT BEACON — Professional National Admin Cyber Matrix Transition Engine
   Features: Target ONLY National Admin tab, Enterprise Hexagonal Cyber Grid & HUD
   Expansion, Abstract Tactical Background Grid, Shrill Audio ONLY on SOS Button.
   ========================================================================== */

(function () {
  // 1. Initialize Fullscreen Interactive Tactical Grid Map Canvas
  const canvas = document.createElement('canvas');
  canvas.id = 'meshBgCanvas';
  document.body.prepend(canvas);
  const ctx = canvas.getContext('2d');

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  // Track Cursor Position for Reactive Map Lighting
  let mouse = { x: -1000, y: -1000, active: false };

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouse.active = true;
  });

  window.addEventListener('mouseleave', () => {
    mouse.active = false;
  });

  // Grid & Interconnected Tactical Nodes Configuration
  const gridSpacing = 48;
  const nodes = [];
  const nodeCount = 32;

  for (let i = 0; i < nodeCount; i++) {
    nodes.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
      radius: Math.random() * 2.5 + 1.5,
      baseAlpha: Math.random() * 0.2 + 0.1
    });
  }

  // Periodic Radar Sweep Pulse State
  let pulseRadius = 0;
  let pulseActive = false;
  let pulseOrigin = { x: width / 2, y: height / 2 };

  function triggerRadarPulse() {
    pulseRadius = 0;
    pulseActive = true;
    pulseOrigin = {
      x: width * 0.2 + Math.random() * width * 0.6,
      y: height * 0.2 + Math.random() * height * 0.6,
    };
  }

  setInterval(triggerRadarPulse, 4500);

  // Render Loop for Background Canvas
  function drawUltraGlowingGridMap() {
    ctx.clearRect(0, 0, width, height);

    const hoverRadius = 260; // Wide reactive spotlight radius

    // A. Draw Vertical Grid Lines with Intense Neon Glow
    for (let x = 0; x < width; x += gridSpacing) {
      const distToMouse = Math.abs(x - mouse.x);
      let lineAlpha = 0.04;
      let isGlowing = false;

      if (mouse.active && distToMouse < hoverRadius) {
        lineAlpha = 0.04 + 0.55 * Math.pow(1 - distToMouse / hoverRadius, 1.5);
        isGlowing = true;
      }

      ctx.save();
      if (isGlowing) {
        ctx.shadowBlur = 14;
        ctx.shadowColor = 'rgba(56, 189, 248, 1)';
        ctx.strokeStyle = `rgba(186, 230, 253, ${lineAlpha})`;
        ctx.lineWidth = 1.4;
      } else {
        ctx.strokeStyle = `rgba(255, 255, 255, ${lineAlpha})`;
        ctx.lineWidth = 1;
      }
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
      ctx.restore();
    }

    // B. Draw Horizontal Grid Lines with Intense Neon Glow
    for (let y = 0; y < height; y += gridSpacing) {
      const distToMouse = Math.abs(y - mouse.y);
      let lineAlpha = 0.04;
      let isGlowing = false;

      if (mouse.active && distToMouse < hoverRadius) {
        lineAlpha = 0.04 + 0.55 * Math.pow(1 - distToMouse / hoverRadius, 1.5);
        isGlowing = true;
      }

      ctx.save();
      if (isGlowing) {
        ctx.shadowBlur = 14;
        ctx.shadowColor = 'rgba(56, 189, 248, 1)';
        ctx.strokeStyle = `rgba(186, 230, 253, ${lineAlpha})`;
        ctx.lineWidth = 1.4;
      } else {
        ctx.strokeStyle = `rgba(255, 255, 255, ${lineAlpha})`;
        ctx.lineWidth = 1;
      }
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
      ctx.restore();
    }

    // C. High-Intensity Mouse Spotlight Radial Glow
    if (mouse.active) {
      ctx.save();
      const grad = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 250);
      grad.addColorStop(0, 'rgba(56, 189, 248, 0.35)');
      grad.addColorStop(0.35, 'rgba(45, 225, 196, 0.18)');
      grad.addColorStop(0.75, 'rgba(255, 255, 255, 0.04)');
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(mouse.x, mouse.y, 250, 0, Math.PI * 2);
      ctx.fill();

      // Glowing Tactical Cursor Reticle
      ctx.shadowBlur = 18;
      ctx.shadowColor = 'rgba(56, 189, 248, 1)';
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(mouse.x, mouse.y, 9, 0, Math.PI * 2);
      ctx.moveTo(mouse.x - 20, mouse.y);
      ctx.lineTo(mouse.x + 20, mouse.y);
      ctx.moveTo(mouse.x, mouse.y - 20);
      ctx.lineTo(mouse.x, mouse.y + 20);
      ctx.stroke();
      ctx.restore();
    }

    // D. Draw Interconnected Glowing Vector Nodes & Links
    for (let i = 0; i < nodes.length; i++) {
      const nodeA = nodes[i];
      nodeA.x += nodeA.vx;
      nodeA.y += nodeA.vy;

      if (nodeA.x < 0 || nodeA.x > width) nodeA.vx *= -1;
      if (nodeA.y < 0 || nodeA.y > height) nodeA.vy *= -1;

      const distMouse = Math.hypot(nodeA.x - mouse.x, nodeA.y - mouse.y);
      let nodeAlpha = nodeA.baseAlpha;
      let isGlowingNode = false;

      if (mouse.active && distMouse < hoverRadius) {
        nodeAlpha = 0.35 + 0.65 * (1 - distMouse / hoverRadius);
        isGlowingNode = true;
      }

      // Draw Vector Links
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeB = nodes[j];
        const dist = Math.hypot(nodeA.x - nodeB.x, nodeA.y - nodeB.y);
        if (dist < 190) {
          let linkAlpha = 0.08 * (1 - dist / 190);
          if (mouse.active && distMouse < hoverRadius) {
            linkAlpha += 0.45 * (1 - distMouse / hoverRadius);
          }

          ctx.save();
          if (mouse.active && distMouse < hoverRadius) {
            ctx.shadowBlur = 12;
            ctx.shadowColor = 'rgba(56, 189, 248, 1)';
            ctx.strokeStyle = `rgba(56, 189, 248, ${linkAlpha})`;
          } else {
            ctx.strokeStyle = `rgba(255, 255, 255, ${linkAlpha})`;
          }
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(nodeA.x, nodeA.y);
          ctx.lineTo(nodeB.x, nodeB.y);
          ctx.stroke();
          ctx.restore();
        }
      }

      // Draw Glowing Node Point
      ctx.save();
      if (isGlowingNode) {
        ctx.shadowBlur = 15;
        ctx.shadowColor = 'rgba(45, 225, 196, 1)';
        ctx.fillStyle = `rgba(45, 225, 196, ${nodeAlpha})`;
      } else {
        ctx.fillStyle = `rgba(255, 255, 255, ${nodeAlpha})`;
      }
      ctx.beginPath();
      ctx.arc(nodeA.x, nodeA.y, nodeA.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // E. Periodic Radar Pulse Ring
    if (pulseActive) {
      pulseRadius += 3;
      const alpha = Math.max(0, 0.45 * (1 - pulseRadius / 450));
      ctx.save();
      ctx.shadowBlur = 18;
      ctx.shadowColor = 'rgba(56, 189, 248, 1)';
      ctx.beginPath();
      ctx.arc(pulseOrigin.x, pulseOrigin.y, pulseRadius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();

      if (pulseRadius > 450) pulseActive = false;
    }

    requestAnimationFrame(drawUltraGlowingGridMap);
  }

  drawUltraGlowingGridMap();

  // 2. Synthesize Shrill & Clingy Metallic Audio Sound (ONLY FOR SOS BUTTON)
  window.playTactileClickSound = function() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const now = audioCtx.currentTime;

      const strikeOsc = audioCtx.createOscillator();
      const strikeGain = audioCtx.createGain();
      strikeOsc.type = 'square';
      strikeOsc.frequency.setValueAtTime(2600, now);
      strikeOsc.frequency.exponentialRampToValueAtTime(1900, now + 0.05);

      strikeGain.gain.setValueAtTime(0.35, now);
      strikeGain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);

      strikeOsc.connect(strikeGain);
      strikeGain.connect(audioCtx.destination);
      strikeOsc.start(now);
      strikeOsc.stop(now + 0.06);

      const ringOsc = audioCtx.createOscillator();
      const ringGain = audioCtx.createGain();
      ringOsc.type = 'sine';
      ringOsc.frequency.setValueAtTime(2850, now);
      ringOsc.frequency.exponentialRampToValueAtTime(2400, now + 0.45);

      ringGain.gain.setValueAtTime(0.4, now);
      ringGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);

      ringOsc.connect(ringGain);
      ringGain.connect(audioCtx.destination);
      ringOsc.start(now);
      ringOsc.stop(now + 0.45);
    } catch (e) {
      console.log('Audio synthesis error:', e);
    }
  };

  window.playAlarmBeepSound = function() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(1100, audioCtx.currentTime);
      osc.frequency.linearRampToValueAtTime(750, audioCtx.currentTime + 0.25);

      gain.gain.setValueAtTime(0.5, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.3);
    } catch (e) {}
  };

  // 3. ENTERPRISE NATIONAL ADMIN CYBER MATRIX TRANSITION ENGINE
  document.addEventListener('DOMContentLoaded', () => {
    let sCanvas = document.getElementById('splatterCanvas');
    if (!sCanvas) {
      sCanvas = document.createElement('canvas');
      sCanvas.id = 'splatterCanvas';
      document.body.appendChild(sCanvas);
    }
    const sCtx = sCanvas.getContext('2d');
    let sWidth = (sCanvas.width = window.innerWidth);
    let sHeight = (sCanvas.height = window.innerHeight);

    window.addEventListener('resize', () => {
      sWidth = sCanvas.width = window.innerWidth;
      sHeight = sCanvas.height = window.innerHeight;
    });

    // Professional Hexagonal Cyber Matrix Transition for National Admin
    function triggerNationalAdminTransition(originX, originY, targetUrl) {
      const startTime = performance.now();
      const duration = 480; // 480ms sleek ease-out

      function animateCyberMatrix(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        const maxRadius = Math.hypot(sWidth, sHeight) * 1.2;
        const currentRadius = progress * maxRadius;

        sCtx.clearRect(0, 0, sWidth, sHeight);

        // A. Draw Dark Executive Navy Backdrop Expansion
        sCtx.fillStyle = `rgba(5, 8, 12, ${Math.min(0.98, progress * 1.4)})`;
        sCtx.beginPath();
        sCtx.arc(originX, originY, currentRadius, 0, Math.PI * 2);
        sCtx.fill();

        // B. Draw Professional Concentric Telemetry Wave Rings
        sCtx.save();
        sCtx.shadowBlur = 24;
        sCtx.shadowColor = 'rgba(56, 189, 248, 0.9)';
        sCtx.strokeStyle = `rgba(56, 189, 248, ${Math.max(0, 1 - progress * 1.1)})`;
        sCtx.lineWidth = 4;
        sCtx.beginPath();
        sCtx.arc(originX, originY, currentRadius, 0, Math.PI * 2);
        sCtx.stroke();

        // Secondary Cyan Wave
        sCtx.strokeStyle = `rgba(45, 225, 196, ${Math.max(0, 0.8 - progress)})`;
        sCtx.lineWidth = 2;
        sCtx.beginPath();
        sCtx.arc(originX, originY, currentRadius * 0.75, 0, Math.PI * 2);
        sCtx.stroke();
        sCtx.restore();

        // C. Draw Sleek Telemetry HUD Text Indicator
        if (progress > 0.15 && progress < 0.92) {
          sCtx.save();
          sCtx.font = '700 12px "JetBrains Mono", monospace';
          sCtx.fillStyle = 'rgba(56, 189, 248, 0.95)';
          sCtx.textAlign = 'center';
          sCtx.shadowBlur = 12;
          sCtx.shadowColor = 'rgba(56, 189, 248, 0.8)';
          sCtx.fillText('INITIALIZING NATIONAL ADMIN TELEMETRY [SECURE ACCESS]', sWidth / 2, sHeight / 2);
          sCtx.restore();
        }

        // Full opacity overlay at completion
        if (progress >= 0.92) {
          sCtx.fillStyle = '#05080c';
          sCtx.fillRect(0, 0, sWidth, sHeight);
        }

        if (progress < 1) {
          requestAnimationFrame(animateCyberMatrix);
        } else {
          window.location.href = targetUrl;
        }
      }

      requestAnimationFrame(animateCyberMatrix);
    }

    // Intercept clicks — ONLY EXECUTED FOR NATIONAL ADMIN TAB
    document.addEventListener('click', (e) => {
      const link = e.target.closest('.beacon-nav-item, .portal-card');
      if (!link) return;

      const targetUrl = link.getAttribute('href');
      if (!targetUrl || targetUrl.startsWith('#') || targetUrl.startsWith('javascript')) return;

      // STRICT CONDITION: Execute Cyber Matrix Transition ONLY for National Admin!
      const linkText = link.innerText || '';
      const isNationalAdmin = targetUrl.includes('admin.html') || linkText.includes('National Admin');

      if (isNationalAdmin) {
        e.preventDefault();
        triggerNationalAdminTransition(e.clientX, e.clientY, targetUrl);
      }
      // Other tabs navigate normally & smoothly without screen spread!
    });

    // SOS Button Hold Engine
    const sosBtn = document.getElementById('sosButton');
    const progressFill = document.getElementById('sosProgressFill');
    let holdTimer = null;
    let holdProgress = 0;
    const holdDurationMs = 2000;
    const stepMs = 30;

    if (sosBtn) {
      function startHold(e) {
        e.preventDefault();
        holdProgress = 0;
        sosBtn.classList.add('holding');

        if (typeof window.playTactileClickSound === 'function') window.playTactileClickSound();
        if (navigator.vibrate) navigator.vibrate(40);

        holdTimer = setInterval(() => {
          holdProgress += stepMs;
          const ratio = Math.min(1, holdProgress / holdDurationMs);

          if (progressFill) {
            const offset = 942 * (1 - ratio);
            progressFill.style.strokeDashoffset = offset;
          }

          if (ratio >= 1) {
            clearInterval(holdTimer);
            sosBtn.classList.remove('holding');
            if (typeof window.playAlarmBeepSound === 'function') window.playAlarmBeepSound();
            if (navigator.vibrate) navigator.vibrate([100, 50, 100, 50, 100]);
            if (typeof window.triggerSos === 'function') window.triggerSos();
          }
        }, stepMs);
      }

      function cancelHold() {
        if (holdTimer) {
          clearInterval(holdTimer);
          holdTimer = null;
        }
        holdProgress = 0;
        sosBtn.classList.remove('holding');
        if (progressFill) {
          progressFill.style.strokeDashoffset = 942;
        }
      }

      sosBtn.addEventListener('mousedown', startHold);
      sosBtn.addEventListener('touchstart', startHold);
      sosBtn.addEventListener('mouseup', cancelHold);
      sosBtn.addEventListener('mouseleave', cancelHold);
      sosBtn.addEventListener('touchend', cancelHold);
    }
  });
})();
