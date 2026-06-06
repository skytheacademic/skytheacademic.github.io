/* ============================================================
   Split-screen redesign — behavior
   1. Animated mesh behind the identity panel (reduced-motion aware).
   2. Research paper explorer: FLIP filter + expand-in-place.
      Only runs on pages that contain #grid.
   Nav active state and the CV tab are rendered server-side, so
   no JS is needed for navigation.
   ============================================================ */
(function () {
  'use strict';

  var prefersReduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. Identity-panel mesh ---------- */
  (function mesh() {
    var c = document.getElementById('mesh');
    if (!c || !c.getContext) return;
    var ctx = c.getContext('2d');

    function size() { c.width = c.clientWidth; c.height = c.clientHeight; }
    size();
    window.addEventListener('resize', size);

    var N = 24, pts = [];
    for (var k = 0; k < N; k++) {
      pts.push({
        x: Math.random(), y: Math.random(),
        vx: (Math.random() - 0.5) * 0.0005,
        vy: (Math.random() - 0.5) * 0.0005
      });
    }

    function draw(move) {
      var W = c.width, H = c.height;
      if (!W) { size(); W = c.width; H = c.height; if (!W) return; }
      ctx.clearRect(0, 0, W, H);
      if (move) {
        pts.forEach(function (p) {
          p.x += p.vx; p.y += p.vy;
          if (p.x < 0 || p.x > 1) p.vx *= -1;
          if (p.y < 0 || p.y > 1) p.vy *= -1;
        });
      }
      for (var i = 0; i < N; i++) {
        for (var j = i + 1; j < N; j++) {
          var a = pts[i], b = pts[j];
          var dx = (a.x - b.x) * W, dy = (a.y - b.y) * H;
          var d = Math.sqrt(dx * dx + dy * dy);
          if (d < 140) {
            ctx.strokeStyle = 'rgba(8,24,48,' + (0.55 * (1 - d / 140)) + ')';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x * W, a.y * H);
            ctx.lineTo(b.x * W, b.y * H);
            ctx.stroke();
          }
        }
      }
      pts.forEach(function (p) {
        ctx.fillStyle = 'rgba(10,28,54,.8)';
        ctx.beginPath();
        ctx.arc(p.x * W, p.y * H, 1.7, 0, 7);
        ctx.fill();
      });
    }

    if (prefersReduced) {
      // Static single frame: texture without motion.
      requestAnimationFrame(function () { size(); draw(false); });
    } else {
      (function frame() { draw(true); requestAnimationFrame(frame); })();
    }
  })();

  /* ---------- 2. Research paper explorer ---------- */
  (function research() {
    var grid = document.getElementById('grid');
    if (!grid) return;

    var tabs = Array.prototype.slice.call(document.querySelectorAll('#tabs button'));
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
    var ct = document.getElementById('ct');
    var current = 'all';

    function matches(c, f) { return f === 'all' || c.dataset.c === f; }
    function setCount(f) {
      var n = cards.filter(function (c) { return matches(c, f); }).length;
      if (ct) ct.textContent = n + (n === 1 ? ' paper' : ' papers');
    }

    function applyFilter(f) {
      if (f === current) return;
      var shownNow = cards.filter(function (c) { return c.style.display !== 'none'; });
      var first = new Map();
      shownNow.forEach(function (c) { first.set(c, c.getBoundingClientRect()); });
      var willLeave = shownNow.filter(function (c) { return !matches(c, f); });
      willLeave.forEach(function (c) { c.classList.add('leaving'); });

      setTimeout(function () {
        willLeave.forEach(function (c) { c.style.display = 'none'; c.classList.remove('leaving'); });
        var newlyEnter = cards.filter(function (c) { return matches(c, f) && c.style.display === 'none'; });
        cards.forEach(function (c) { if (matches(c, f)) c.style.display = ''; });

        var staying = cards.filter(function (c) { return c.style.display !== 'none' && first.has(c); });
        staying.forEach(function (c) {
          var last = c.getBoundingClientRect(), fr = first.get(c);
          var dx = fr.left - last.left, dy = fr.top - last.top;
          if (dx || dy) {
            c.style.transform = 'translate(' + dx + 'px,' + dy + 'px)';
            c.classList.remove('flip-move');
            requestAnimationFrame(function () { c.classList.add('flip-move'); c.style.transform = ''; });
            c.addEventListener('transitionend', function () { c.classList.remove('flip-move'); }, { once: true });
          }
        });

        newlyEnter.forEach(function (c, i) {
          c.classList.add('entering');
          requestAnimationFrame(function () { setTimeout(function () { c.classList.add('enter-active'); }, 60 + i * 70); });
          setTimeout(function () { c.classList.remove('entering', 'enter-active'); }, 60 + i * 70 + 460);
        });
      }, willLeave.length ? 180 : 0);

      current = f;
      setCount(f);
    }

    tabs.forEach(function (t) {
      t.addEventListener('click', function () {
        tabs.forEach(function (x) { x.classList.remove('on'); });
        t.classList.add('on');
        applyFilter(t.dataset.f);
      });
    });

    function toggleCard(c) {
      var wasOpen = c.classList.contains('open');
      cards.forEach(function (x) { x.classList.remove('open'); });
      if (!wasOpen) c.classList.add('open');
    }

    cards.forEach(function (c) {
      // Keyboard operability: cards behave like buttons.
      c.setAttribute('tabindex', '0');
      c.setAttribute('role', 'button');
      c.addEventListener('click', function (e) {
        if (e.target.closest('.links a')) return;
        toggleCard(c);
      });
      c.addEventListener('keydown', function (e) {
        if (e.target.closest('.links a')) return;
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleCard(c); }
      });
    });

    setCount('all');
  })();
})();
