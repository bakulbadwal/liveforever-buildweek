/* LiveForever · the genome as a double helix you can turn.
   three.js r128 is loaded lazily from cdnjs (pinned) only when the section
   nears the viewport and WebGL is available. Reduced motion or no WebGL
   gets a static two-strand drawing with the same ten lit base pairs.
   The lit rungs are the synthetic panel markers; nothing else is data. */
(function () {
  'use strict';

  var THREE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  var api = { init: init, select: select };
  var ctx = null;

  function reducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function webglAvailable() {
    try {
      var c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch (e) { return false; }
  }

  function init(container, findings, onSelect) {
    ctx = { container: container, findings: findings, onSelect: onSelect, selected: 0, rungs: [], ready: false };
    if (reducedMotion() || !webglAvailable()) {
      renderFallback();
      return;
    }
    var hint = document.createElement('p');
    hint.className = 'helix-hint';
    hint.textContent = 'Drag to turn. Tap a lit base pair, or choose one from the list.';
    container.parentNode.insertBefore(hint, container.nextSibling);
    var started = false;
    var start = function () {
      if (started) return;
      started = true;
      var s = document.createElement('script');
      s.src = THREE_URL;
      s.async = true;
      s.onload = build;
      s.onerror = function () { hint.remove(); renderFallback(); };
      document.head.appendChild(s);
    };
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries.some(function (e) { return e.isIntersecting; })) { start(); io.disconnect(); }
      }, { rootMargin: '600px 0px' });
      io.observe(container);
    } else {
      start();
    }
  }

  /* ---------- 3D scene ---------- */

  function build() {
    var T = window.THREE;
    var container = ctx.container;
    var w = container.clientWidth, h = container.clientHeight;
    var phone = window.innerWidth < 820;
    var renderer = new T.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, phone ? 1.5 : 2));
    renderer.setSize(w, h);
    renderer.outputEncoding = T.sRGBEncoding;
    container.insertBefore(renderer.domElement, container.firstChild);

    var scene = new T.Scene();
    // depth: the far side of the helix recedes into the plate colour
    scene.fog = new T.Fog(0x111a2d, 12, 19);
    var camera = new T.PerspectiveCamera(32, w / h, 0.1, 100);
    camera.position.set(0, 0, 13.5);

    scene.add(new T.AmbientLight(0xc9c2b4, 0.35));
    scene.add(new T.HemisphereLight(0xe3dccb, 0x0d1322, 0.5));
    var key = new T.DirectionalLight(0xfff1d6, 0.95);
    key.position.set(4, 6, 8);
    scene.add(key);
    var rim = new T.DirectionalLight(0x7f8da8, 0.7);
    rim.position.set(-6, -3, -4);
    scene.add(rim);
    var lamp = new T.PointLight(0xfff1d6, 0.55, 30, 2);
    lamp.position.set(3, 2, 9);
    scene.add(lamp);

    var group = new T.Group();
    scene.add(group);

    var height = 10, radius = 1.55, turns = 3.0;
    var strandMat = new T.MeshStandardMaterial({ color: 0x8f8a7e, roughness: 0.42, metalness: 0.3 });
    var rungMat = new T.MeshStandardMaterial({ color: 0x56627c, roughness: 0.6, metalness: 0.15 });
    var litMat = new T.MeshStandardMaterial({ color: 0xece6d8, emissive: 0xece6d8, emissiveIntensity: 0.5, roughness: 0.3, metalness: 0.1 });
    var selMat = new T.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff6e4, emissiveIntensity: 1.1, roughness: 0.2 });

    // a soft additive halo, drawn once to a canvas, used for the lit rungs' glow
    var haloCanvas = document.createElement('canvas');
    haloCanvas.width = haloCanvas.height = 128;
    var g2 = haloCanvas.getContext('2d');
    var grad = g2.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, 'rgba(255,250,238,0.9)');
    grad.addColorStop(0.25, 'rgba(236,230,216,0.45)');
    grad.addColorStop(0.6, 'rgba(236,230,216,0.1)');
    grad.addColorStop(1, 'rgba(236,230,216,0)');
    g2.fillStyle = grad;
    g2.fillRect(0, 0, 128, 128);
    var haloTex = new T.CanvasTexture(haloCanvas);
    function halo(opacity, scale) {
      var sp = new T.Sprite(new T.SpriteMaterial({ map: haloTex, color: 0xece6d8, transparent: true, opacity: opacity, blending: T.AdditiveBlending, depthWrite: false }));
      sp.scale.set(scale, scale, 1);
      return sp;
    }

    // dust: a slow field of motes around the helix for atmosphere (fewer on phones)
    var motes = phone ? 70 : 180;
    var dust = new Float32Array(motes * 3);
    for (var d = 0; d < motes; d++) {
      var ang = Math.random() * Math.PI * 2, rad = 2.4 + Math.random() * 2.6;
      dust[d * 3] = Math.cos(ang) * rad;
      dust[d * 3 + 1] = (Math.random() - 0.5) * 13;
      dust[d * 3 + 2] = Math.sin(ang) * rad;
    }
    var dustGeo = new T.BufferGeometry();
    dustGeo.setAttribute('position', new T.BufferAttribute(dust, 3));
    var dustPts = new T.Points(dustGeo, new T.PointsMaterial({ color: 0xaab3c6, size: 0.05, transparent: true, opacity: 0.55, depthWrite: false, sizeAttenuation: true }));
    scene.add(dustPts);

    function strandPoint(t, phase) {
      var y = -height / 2 + t * height;
      var a = t * turns * Math.PI * 2 + phase;
      return new T.Vector3(Math.cos(a) * radius, y, Math.sin(a) * radius);
    }
    [0, Math.PI].forEach(function (phase) {
      var pts = [];
      for (var i = 0; i <= 200; i++) pts.push(strandPoint(i / 200, phase));
      var curve = new T.CatmullRomCurve3(pts);
      var tube = new T.Mesh(new T.TubeGeometry(curve, 400, 0.085, 10, false), strandMat);
      group.add(tube);
    });

    var count = 44;
    var n = ctx.findings.length;
    // lit rungs spread along the helix, avoiding the very ends
    var litIndex = {};
    for (var k = 0; k < n; k++) litIndex[Math.round(4 + (count - 9) * k / (n - 1))] = k;
    var rungGeo = new T.CylinderGeometry(0.05, 0.05, 1, 8);
    var litGeo = new T.CylinderGeometry(0.095, 0.095, 1, 12);
    var bead = new T.SphereGeometry(0.13, 16, 12);
    for (var i = 0; i < count; i++) {
      var t = (i + 0.5) / count;
      var a = strandPoint(t, 0), b = strandPoint(t, Math.PI);
      var mid = a.clone().add(b).multiplyScalar(0.5);
      var dir = b.clone().sub(a);
      var lit = litIndex.hasOwnProperty(i);
      var mesh = new T.Mesh(lit ? litGeo : rungGeo, lit ? litMat : rungMat);
      mesh.position.copy(mid);
      mesh.scale.y = dir.length() - 0.2;
      mesh.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0), dir.clone().normalize());
      group.add(mesh);
      if (lit) {
        var finding = litIndex[i];
        var beads = [a, b].map(function (p) {
          var s = new T.Mesh(bead, litMat);
          s.position.copy(p);
          s.userData.finding = finding;
          group.add(s);
          return s;
        });
        mesh.userData.finding = finding;
        var glow = halo(0.28, 0.9);
        glow.position.copy(mid);
        group.add(glow);
        ctx.rungs[finding] = { mesh: mesh, beads: beads, glow: glow, angle: t * turns * Math.PI * 2, y: mid.y, lit: litMat, sel: selMat };
      }
    }

    ctx.T = T; ctx.renderer = renderer; ctx.scene = scene; ctx.camera = camera; ctx.group = group; ctx.dust = dustPts;
    ctx.targetRot = 0; ctx.targetY = 0; ctx.auto = true; ctx.visible = true; ctx.ready = true;
    ctx.scrollT = 0.5; ctx.camY = 0; ctx.tiltX = 0.08;
    group.rotation.x = 0.08;

    // scroll-linked camera: as the section passes through the viewport the eye drifts
    // down the helix and the tilt eases, so the strand reads as a solid object in space
    var readScroll = function () {
      var rect = container.getBoundingClientRect();
      var vh = window.innerHeight || 1;
      ctx.scrollT = Math.max(0, Math.min(1, (vh - rect.top) / (vh + rect.height)));
    };
    readScroll();
    window.addEventListener('scroll', readScroll, { passive: true });

    var raycaster = new T.Raycaster();
    var pointer = new T.Vector2();
    var drag = null;
    var el = renderer.domElement;
    el.style.cursor = 'grab';
    el.addEventListener('pointerdown', function (e) {
      drag = { x: e.clientX, y: e.clientY, rot: group.rotation.y, moved: false, id: e.pointerId };
      el.setPointerCapture(e.pointerId);
      el.style.cursor = 'grabbing';
    });
    el.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x;
      if (Math.abs(dx) > 4 || Math.abs(e.clientY - drag.y) > 4) drag.moved = true;
      if (drag.moved) {
        ctx.auto = false;
        group.rotation.y = drag.rot + dx * 0.012;
        ctx.targetRot = group.rotation.y;
      }
    });
    var end = function (e) {
      if (!drag) return;
      el.style.cursor = 'grab';
      if (!drag.moved) {
        var rect = el.getBoundingClientRect();
        pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, camera);
        var hits = raycaster.intersectObjects(group.children, false).filter(function (hit) { return hit.object.userData.finding != null; });
        if (hits.length) {
          var idx = hits[0].object.userData.finding;
          ctx.onSelect(idx);
          select(idx);
        }
      }
      drag = null;
      setTimeout(function () { ctx.auto = true; }, 4000);
    };
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', function () { drag = null; });

    if ('ResizeObserver' in window) {
      new ResizeObserver(function () {
        var cw = container.clientWidth, ch = container.clientHeight;
        if (!cw || !ch) return;
        renderer.setSize(cw, ch);
        camera.aspect = cw / ch;
        camera.updateProjectionMatrix();
      }).observe(container);
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        ctx.visible = entries.some(function (e) { return e.isIntersecting; });
      }).observe(container);
    }

    select(ctx.selected);
    var last = performance.now();
    function frame(now) {
      requestAnimationFrame(frame);
      if (!ctx.visible) return;
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      if (ctx.auto) ctx.targetRot += dt * 0.25;
      group.rotation.y += (ctx.targetRot - group.rotation.y) * Math.min(1, dt * 5);
      group.position.y += (ctx.targetY - group.position.y) * Math.min(1, dt * 4);
      // eased scroll camera and tilt
      var wantCamY = (0.5 - ctx.scrollT) * 1.4, wantTilt = 0.08 + (ctx.scrollT - 0.5) * 0.3;
      ctx.camY += (wantCamY - ctx.camY) * Math.min(1, dt * 3);
      ctx.tiltX += (wantTilt - ctx.tiltX) * Math.min(1, dt * 3);
      camera.position.y = ctx.camY;
      camera.lookAt(0, ctx.camY * 0.35, 0);
      group.rotation.x = ctx.tiltX;
      // dust drifts the other way, slowly
      dustPts.rotation.y -= dt * 0.03;
      dustPts.position.y = Math.sin(now / 9000) * 0.25;
      // the selected rung's halo breathes; the others hold a steady glow
      ctx.rungs.forEach(function (r, k) {
        var on = k === ctx.selected;
        var want = on ? 2.1 + Math.sin(now / 700) * 0.15 : 0.9;
        var s = r.glow.scale.x + (want - r.glow.scale.x) * Math.min(1, dt * 6);
        r.glow.scale.set(s, s, 1);
        r.glow.material.opacity += ((on ? 0.6 : 0.28) - r.glow.material.opacity) * Math.min(1, dt * 6);
      });
      renderer.render(scene, camera);
    }
    requestAnimationFrame(frame);
  }

  function select(i) {
    if (!ctx) return;
    ctx.selected = i;
    if (!ctx.ready) {
      if (ctx.fallback) ctx.fallback(i);
      return;
    }
    ctx.rungs.forEach(function (r, k) {
      var mat = k === i ? r.sel : r.lit;
      r.mesh.material = mat;
      r.beads.forEach(function (b) { b.material = mat; });
      r.mesh.scale.x = r.mesh.scale.z = k === i ? 1.5 : 1;
    });
    var r = ctx.rungs[i];
    if (!r) return;
    // bring the selected pair to the front and to the vertical centre
    var want = -r.angle;
    var cur = ctx.group.rotation.y;
    var twoPi = Math.PI * 2;
    var delta = ((want - cur) % twoPi + twoPi * 1.5) % twoPi - Math.PI;
    ctx.targetRot = cur + delta;
    // clamp the pan so the helix (10 tall, ~7.7 visible) never leaves the frame half empty
    ctx.targetY = Math.max(-1.1, Math.min(1.1, -r.y));
    ctx.auto = false;
    clearTimeout(ctx.autoTimer);
    ctx.autoTimer = setTimeout(function () { ctx.auto = true; }, 5000);
  }

  /* ---------- 2D fallback ---------- */

  function renderFallback() {
    var container = ctx.container;
    var n = ctx.findings.length;
    var w = Math.max(280, container.clientWidth), h = Math.max(240, container.clientHeight);
    var pad = 28, amp = Math.min(h * 0.28, 110), cy = h / 2;
    var turns = 2.5;
    var out = ['<svg class="fallback" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="A double helix with ' + n + ' lit base pairs">'];
    var strand = function (phase) {
      var d = [];
      for (var i = 0; i <= 160; i++) {
        var x = pad + (w - pad * 2) * i / 160;
        var y = cy + Math.sin(i / 160 * turns * Math.PI * 2 + phase) * amp;
        d.push((i ? 'L' : 'M') + x.toFixed(1) + ',' + y.toFixed(1));
      }
      return d.join(' ');
    };
    var rungs = [];
    var total = 36;
    for (var k = 0; k < total; k++) {
      var t = (k + 0.5) / total;
      var x = pad + (w - pad * 2) * t;
      var y1 = cy + Math.sin(t * turns * Math.PI * 2) * amp, y2 = cy + Math.sin(t * turns * Math.PI * 2 + Math.PI) * amp;
      rungs.push('<line x1="' + x.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="var(--slate-2)" stroke-width="2"/>');
    }
    out.push(rungs.join(''));
    out.push('<path d="' + strand(0) + '" fill="none" stroke="var(--ink-2)" stroke-width="3"/>');
    out.push('<path d="' + strand(Math.PI) + '" fill="none" stroke="var(--ink-2)" stroke-width="3"/>');
    var lit = [];
    for (var m = 0; m < n; m++) {
      var tt = (0.06 + 0.88 * m / (n - 1));
      var xx = pad + (w - pad * 2) * tt;
      var ya = cy + Math.sin(tt * turns * Math.PI * 2) * amp, yb = cy + Math.sin(tt * turns * Math.PI * 2 + Math.PI) * amp;
      lit.push('<g class="lit" data-lit="' + m + '"><line x1="' + xx.toFixed(1) + '" y1="' + ya.toFixed(1) + '" x2="' + xx.toFixed(1) + '" y2="' + yb.toFixed(1) + '" stroke="var(--self)" stroke-width="4"/><circle cx="' + xx.toFixed(1) + '" cy="' + ya.toFixed(1) + '" r="6" fill="var(--self)"/><circle cx="' + xx.toFixed(1) + '" cy="' + yb.toFixed(1) + '" r="6" fill="var(--self)"/></g>');
    }
    out.push(lit.join(''));
    out.push('</svg>');
    container.innerHTML = out.join('');
    ctx.fallback = function (i) {
      container.querySelectorAll('.lit').forEach(function (g) {
        var on = Number(g.dataset.lit) === i;
        g.querySelectorAll('line').forEach(function (l) { l.setAttribute('stroke-width', on ? '7' : '4'); l.setAttribute('stroke', on ? '#ffffff' : 'var(--self)'); });
        g.querySelectorAll('circle').forEach(function (c) { c.setAttribute('r', on ? '9' : '6'); c.setAttribute('fill', on ? '#ffffff' : 'var(--self)'); });
      });
    };
    container.querySelectorAll('.lit').forEach(function (g) {
      g.style.cursor = 'pointer';
      g.addEventListener('click', function () { var i = Number(g.dataset.lit); ctx.onSelect(i); ctx.fallback(i); });
    });
    ctx.fallback(ctx.selected);
  }

  window.LiveForeverGenome = api;
}());
