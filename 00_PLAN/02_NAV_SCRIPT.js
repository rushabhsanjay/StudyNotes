/* 02_NAV_SCRIPT.js
   NAV_SCRIPT_V2  (marker: do not remove)
   V5: Enhanced Reader & Interactivity Engine:
   - Dynamic Process Flows (turns A → B → C lines into visual interactive pipelines)
   - Specialized Callout Wrappers (Distinctions, Examples, Case Studies)
   - Interactive Tables: sticky headers, real-time table search/filter, and TSV copy
   - Code & Schematic Panels with action headers (Logic, Diagram, Code)
   - Floating Action Dock: Dynamic % reading badge, Zen/Focus Mode, Theme, Back to Top
   - Left TOC Search Filter for long topic indexes
   - Keyboard Navigation shortcuts: [ and ] for Prev/Next, Z for Zen, T for Theme, ? for Help
   - Preserves window.NAV_SHOW_ALL_OPEN for 03_HTML_INDEX.html
   Static. Loaded by every generated HTML. Never rewritten by Python. */

(function () {
  'use strict';

  /* ---------- theme (applied immediately to avoid a flash) ---------- */
  var THEME_KEY = 'nav-theme';
  function applyTheme(t) {
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
    else document.documentElement.removeAttribute('data-theme');
  }
  try { applyTheme(localStorage.getItem(THEME_KEY)); } catch (e) {}
  function effectiveTheme() {
    var a = document.documentElement.getAttribute('data-theme');
    if (a) return a;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  // ---- locate the study root = parent folder of the folder holding this script
  var SELF = (document.currentScript && document.currentScript.src) || '';
  if (!SELF) {
    var ss = document.getElementsByTagName('script');
    for (var i = 0; i < ss.length; i++)
      if (/02_NAV_SCRIPT\.js/.test(ss[i].src)) SELF = ss[i].src;
  }
  var ROOT = SELF ? new URL('../', SELF.split('?')[0]) : new URL('./', location.href);

  /* ===== PWA: manifest + service worker (added) ===== */
  try {
    if (!document.querySelector('link[rel="manifest"]')) {
      var mf = document.createElement('link');
      mf.rel = 'manifest';
      mf.href = new URL('manifest.json', ROOT).href;
      document.head.appendChild(mf);
    }
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register(new URL('sw.js', ROOT).href, { scope: ROOT.href });
    }
  } catch (e) { /* PWA is optional; never break navigation */ }
  /* ===== end PWA ===== */

  /* ===== System bar colour + edge blur (added) ===== */
  function syncThemeColor() {
    try {
      var c = getComputedStyle(document.documentElement).getPropertyValue('--nv-canvas').trim();
      if (!c) return;
      var metas = document.querySelectorAll('meta[name="theme-color"]');
      if (!metas.length) {
        var m = document.createElement('meta');
        m.name = 'theme-color';
        document.head.appendChild(m);
        metas = [m];
      }
      for (var i = 0; i < metas.length; i++) {
        metas[i].removeAttribute('media');
        metas[i].setAttribute('content', c);
      }
    } catch (e) {}
  }
  try {
    new MutationObserver(syncThemeColor)
      .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      if (mq.addEventListener) mq.addEventListener('change', syncThemeColor);
    }
    document.addEventListener('DOMContentLoaded', syncThemeColor);
    window.addEventListener('load', syncThemeColor);
    syncThemeColor();
  } catch (e) {}

  document.addEventListener('DOMContentLoaded', function () {
    try {
      ['top', 'bottom'].forEach(function (pos) {
        var d = document.createElement('div');
        d.className = 'edge-fade ' + pos;
        d.setAttribute('aria-hidden', 'true');
        document.body.appendChild(d);
      });
    } catch (e) {}
  });

  var CUR = null;            // current page entry from NAV_DATA (if found)

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c];
    });
  }
  function cmp(a, b) {
    return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
  }
  function keyOf(pathname) {
    var s = pathname || '';
    try { s = decodeURIComponent(s); } catch (e) {}
    return s.replace(/\\/g, '/').toLowerCase();
  }
  function hrefOf(f) {
    var rel = String(f.path || '').split('/').map(encodeURIComponent).join('/');
    return new URL(rel, ROOT);
  }

  function prettyLabel(raw) {
    var s = String(raw == null ? '' : raw), num = '', m = s.match(/^(\d+)[_\s.\-]+(.+)$/);
    if (m) { num = m[1]; s = m[2]; }
    s = s.replace(/(\d)_(\d)/g, '$1.$2').replace(/_/g, ' ').replace(/\.html?$/i, '');
    if (s === s.toUpperCase() && /[A-Z]/.test(s)) {
      s = s.toLowerCase().replace(/(^|\s)([a-z])/g, function (x, a, b) { return a + b.toUpperCase(); });
    }
    return (num ? '<span class="nn">' + esc(num) + '</span>' : '') + esc(s);
  }

  function buildTree(files) {
    var root = { children: {}, files: [] };
    files.forEach(function (f) {
      var node = root;
      (f.levels || []).forEach(function (lv) {
        if (!node.children[lv]) node.children[lv] = { name: lv, children: {}, files: [] };
        node = node.children[lv];
      });
      node.files.push(f);
    });
    return root;
  }

  function markCurrent(node) {
    var hit = false;
    (node.files || []).forEach(function (f) { if (f._cur) hit = true; });
    Object.keys(node.children || {}).forEach(function (k) {
      if (markCurrent(node.children[k])) hit = true;
    });
    node._hasCurrent = hit;
    return hit;
  }

  function renderNode(node) {
    var items = [];
    Object.keys(node.children || {}).forEach(function (k) {
      items.push({ name: k, kind: 'folder', payload: k });
    });
    (node.files || []).forEach(function (f) {
      items.push({ name: f.title || f.filename || '(untitled)', kind: 'file', payload: f });
    });
    if (!items.length) return '';
    items.sort(function (a, b) { return cmp(a.name, b.name); });

    var showAllOpen = (typeof window.NAV_SHOW_ALL_OPEN !== 'undefined' && window.NAV_SHOW_ALL_OPEN);

    var out = ['<ul>'];
    items.forEach(function (it) {
      if (it.kind === 'folder') {
        var child = node.children[it.payload];
        var inner = renderNode(child);
        if (!inner) return;
        var isOpen = showAllOpen || child._hasCurrent;
        out.push('<li><details' + (isOpen ? ' open' : '') + '>');
        out.push('<summary><span class="gnav-folder-name">' + prettyLabel(it.payload) + '</span></summary>');
        out.push(inner + '</details></li>');
      } else {
        var f = it.payload, label = prettyLabel(it.name);
        var tip = esc(f.description || f.title || '');
        if (f._cur) {
          out.push('<li><span class="gnav-file is-current" title="' + tip + '">' + label + '</span></li>');
        } else if (f.exists === false) {
          out.push('<li><span class="gnav-file gnav-missing" title="Not generated yet">' + label + '</span></li>');
        } else {
          out.push('<li><a class="gnav-file" href="' + esc(f._href) + '" title="' + tip + '">' + label + '</a></li>');
        }
      }
    });
    out.push('</ul>');
    return out.join('');
  }

  // ---- Previous / Next (global INDEX order)
  function pad(n) { n = String(n); while (n.length < 4) n = '0' + n; return n; }

  function pnButton(f, dir) {
    var isPrev = dir === 'prev';
    var lbl = isPrev ? '&larr; Previous Topic' : 'Next Topic &rarr;';
    var keyHint = isPrev ? '<kbd class="kb-key" style="margin-left:6px;font-size:.65rem;">[</kbd>' : '<kbd class="kb-key" style="margin-right:6px;font-size:.65rem;">]</kbd>';
    if (!f) return '<span class="pn-btn pn-' + dir + ' pn-disabled"><span class="pn-lbl">' + lbl + '</span></span>';
    return '<a class="pn-btn pn-' + dir + '" rel="' + dir + '" href="' + esc(f._href)
         + '" title="' + esc(f.title) + '"><span class="pn-lbl">' + (isPrev ? lbl + keyHint : keyHint + lbl)
         + '</span><span class="pn-title">' + esc(f.title) + '</span></a>';
  }
  function pnBar(where, prev, next, cur, total) {
    return '<nav class="pn-bar pn-' + where + '" aria-label="Page navigation">'
         + pnButton(prev, 'prev')
         + '<span class="pn-pos">' + pad(cur.index) + ' / ' + total + '</span>'
         + pnButton(next, 'next') + '</nav>';
  }
  function injectPrevNext(files, cur) {
    if (!cur) return;
    var pane = document.getElementById('content-pane');
    if (!pane) return;
    var seq = files.filter(function (f) { return f === cur || f.exists !== false; })
                    .sort(function (a, b) { return (a.index || 0) - (b.index || 0); });
    var pos = seq.indexOf(cur);
    var prev = pos > 0 ? seq[pos - 1] : null;
    var next = pos < seq.length - 1 ? seq[pos + 1] : null;
    var total = files.reduce(function (m, f) { return Math.max(m, f.index || 0); }, 0);
    var art = pane.querySelector('article') || pane;
    Array.prototype.forEach.call(pane.querySelectorAll('.pn-bar'), function (n) { n.remove(); });
    art.insertAdjacentHTML('afterbegin', pnBar('top', prev, next, cur, total));
    art.insertAdjacentHTML('beforeend',  pnBar('bottom', prev, next, cur, total));
  }

  /* ---------- sidebar search ---------- */
  function wireNavSearch(container) {
    if (!container || (container.previousElementSibling && container.previousElementSibling.classList.contains('gnav-search-wrap'))) return;
    var wrap = document.createElement('div');
    wrap.className = 'gnav-search-wrap';
    wrap.innerHTML = '<input type="search" class="gnav-search" placeholder="Filter topics..." aria-label="Filter topics" autocomplete="off">';
    container.parentNode.insertBefore(wrap, container);
    var input = wrap.firstChild, saved = null;

    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var lis = container.querySelectorAll('li');
      if (!q) {
        Array.prototype.forEach.call(lis, function (li) { li.hidden = false; });
        if (saved) {
          Array.prototype.forEach.call(container.querySelectorAll('details'), function (d, i) { d.open = saved[i]; });
          saved = null;
        }
        return;
      }
      if (!saved) saved = Array.prototype.map.call(container.querySelectorAll('details'), function (d) { return d.open; });
      for (var i = lis.length - 1; i >= 0; i--) {
        var li = lis[i], first = li.firstElementChild, hit;
        if (first && first.classList.contains('gnav-file')) {
          hit = (first.textContent + ' ' + (first.getAttribute('title') || '')).toLowerCase().indexOf(q) > -1;
        } else {
          var det = li.querySelector(':scope > details');
          var kids = det ? det.querySelectorAll(':scope > ul > li') : [];
          hit = Array.prototype.some.call(kids, function (k) { return !k.hidden; });
          if (det) det.open = hit;
        }
        li.hidden = !hit;
      }
    });
  }

  function renderNav() {
    var container = document.getElementById('global-nav');
    var data = window.NAV_DATA;
    var msg = function (t) {
      if (container) container.innerHTML = '<div class="gnav"><div class="gnav-empty">' + t + '</div></div>';
    };
    if (!data || !Array.isArray(data.files)) { msg('Navigation data not loaded (nav_data.js missing).'); return; }
    if (!data.files.length) { msg('No HTML files generated yet.'); return; }

    var here = keyOf(location.pathname), cur = null;
    data.files.forEach(function (f) {
      var u = hrefOf(f);
      f._href = u.href;
      f._cur = (keyOf(u.pathname) === here);
      if (f._cur) cur = f;
    });
    CUR = cur;

    injectPrevNext(data.files, cur);
    if (!container) return;

    var tree = buildTree(data.files);
    markCurrent(tree);
    var body = renderNode(tree);
    container.innerHTML = '<div class="gnav">' + (body || '<div class="gnav-empty">Nothing to show.</div>') + '</div>';
    wireNavSearch(container);

    var el = container.querySelector('.gnav-file.is-current');
    if (el) setTimeout(function () { try { el.scrollIntoView({ block: 'center' }); } catch (e) {} }, 40);
  }

  var MQ = window.matchMedia('(max-width: 900px)');

  function closeDrawers() {
    ['page-sidebar-left', 'page-sidebar-right'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.classList.remove('is-open');
    });
    document.body.classList.remove('sb-open', 'sb-left-open', 'sb-right-open');
  }

  function wireToggles() {
    var bd = document.createElement('div');
    bd.id = 'sb-backdrop';
    document.body.appendChild(bd);
    bd.addEventListener('click', closeDrawers);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeDrawers(); });

    [['side-toggle-left',  'page-sidebar-left',  'sb-left-open'],
     ['side-toggle-right', 'page-sidebar-right', 'sb-right-open']].forEach(function (p) {
      var btn = document.getElementById(p[0]), sb = document.getElementById(p[1]);
      if (!btn || !sb) return;
      var key = 'nav-collapsed-' + p[1];
      if (!MQ.matches) {
        try { if (localStorage.getItem(key) === '1') sb.classList.add('is-collapsed'); } catch (e) {}
      }
      btn.addEventListener('click', function () {
        if (MQ.matches) {
          var open = !sb.classList.contains('is-open');
          closeDrawers();
          if (open) { sb.classList.add('is-open'); document.body.classList.add('sb-open', p[2]); }
          return;
        }
        sb.classList.toggle('is-collapsed');
        try { localStorage.setItem(key, sb.classList.contains('is-collapsed') ? '1' : '0'); } catch (e) {}
        setTimeout(placeDock, 260);
      });
    });
  }

  function wireTOC() {
    var toc = document.getElementById('page-toc');
    if (toc && !toc.querySelector('.toc-filter-wrap')) {
      var fWrap = document.createElement('div');
      fWrap.className = 'toc-filter-wrap';
      fWrap.innerHTML = '<input type="search" class="toc-filter-input" placeholder="Filter contents..." aria-label="Filter contents">';
      toc.insertBefore(fWrap, toc.firstChild);
      var fInput = fWrap.firstChild;
      fInput.addEventListener('input', function () {
        var q = fInput.value.trim().toLowerCase();
        var lis = toc.querySelectorAll('li');
        lis.forEach(function (li) {
          var txt = li.textContent.toLowerCase();
          li.hidden = (q && txt.indexOf(q) === -1);
        });
      });
    }

    document.querySelectorAll('.page-toc a[href^="#"]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        var t = document.querySelector(a.getAttribute('href'));
        if (!t) return;
        e.preventDefault();
        if (MQ.matches) closeDrawers();
        t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  function wireProgress() {
    var pane = document.getElementById('content-pane');
    var bar = document.getElementById('progress-bar');
    var badge = document.getElementById('dock-progress');
    if (!pane || !bar) return;
    var upd = function () {
      var st, max;
      if (MQ.matches) {
        var de = document.documentElement;
        st = window.pageYOffset || de.scrollTop;
        max = de.scrollHeight - window.innerHeight;
      } else {
        st = pane.scrollTop;
        max = pane.scrollHeight - pane.clientHeight;
      }
      var frac = max > 0 ? Math.min(1, Math.max(0, st / max)) : 0;
      bar.style.transform = 'scaleX(' + frac + ')';
      if (badge) {
        badge.textContent = Math.round(frac * 100) + '%';
      }
    };
    pane.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    upd();
  }

  /* =====================================================================
     PAGE ENHANCER & NEW INTERACTIVE PROCESS FLOWS / CALLOUTS
     ===================================================================== */
  function textNodes(root, fn) {
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), n, list = [];
    while ((n = w.nextNode())) list.push(n);
    list.forEach(fn);
  }

  function buildQA(wrap) {
    var kids = [].slice.call(wrap.children), cur = null, count = 0, first = null;
    kids.shift();
    var isQ = function (el) { return el.tagName === 'P' && /^\s*Q\s?\d+[.)]/.test(el.textContent); };
    kids.forEach(function (el) {
      if (isQ(el)) {
        cur = document.createElement('details'); cur.className = 'qa';
        var sm = document.createElement('summary');
        while (el.firstChild) sm.appendChild(el.firstChild);
        var body = document.createElement('div'); body.className = 'qa-body';
        cur.appendChild(sm); cur.appendChild(body);
        el.parentNode.replaceChild(cur, el);
        if (!first) first = cur;
        count++;
      } else if (cur && el.tagName !== 'HR') {
        cur.lastChild.appendChild(el);
      }
    });
    if (count > 1 && first) {
      var tools = document.createElement('div'); tools.className = 'qa-tools';
      tools.innerHTML = '<button type="button" data-a="open">Expand all</button><button type="button" data-a="close">Collapse all</button>';
      tools.addEventListener('click', function (e) {
        var a = e.target.getAttribute && e.target.getAttribute('data-a');
        if (!a) return;
        [].forEach.call(wrap.querySelectorAll('details.qa'), function (d) { d.open = (a === 'open'); });
      });
      first.parentNode.insertBefore(tools, first);
    }
  }

  /* ---- Enhance Process Flow lines (A → B → C) ---- */
  function enhanceProcessFlows(art) {
    var ps = [].slice.call(art.querySelectorAll('p, h2, h3'));
    ps.forEach(function (p) {
      if (p.closest('pre, .doc-hero, .pn-bar, .gnav, .page-toc, .doc-flow')) return;
      var raw = p.textContent.trim();
      if ((raw.indexOf('→') > -1 || raw.indexOf('->') > -1) && !p.querySelector('img, pre, table')) {
        var parts = raw.split(/\s*(?:→|->)\s*/);
        if (parts.length >= 3 && parts.every(function (s) { return s.length < 70; })) {
          var flow = document.createElement('div');
          flow.className = 'doc-flow';
          flow.setAttribute('role', 'region');
          flow.setAttribute('aria-label', 'Process Flow');
          parts.forEach(function (step, i) {
            var stepEl = document.createElement('span');
            stepEl.className = 'doc-flow-step';
            stepEl.innerHTML = '<span class="doc-flow-num">' + (i + 1) + '</span><span>' + esc(step) + '</span>';
            flow.appendChild(stepEl);
            if (i < parts.length - 1) {
              var sep = document.createElement('span');
              sep.className = 'doc-flow-sep';
              sep.innerHTML = '&#10140;';
              flow.appendChild(sep);
            }
          });
          p.parentNode.replaceChild(flow, p);
        }
      }
    });
  }

  /* ---- Distinct Callout Boxes for Examples & Distinctions ---- */
  function enhanceCallouts(art) {
    var heads = [].slice.call(art.querySelectorAll('h3, h4'));
    heads.forEach(function (h) {
      var txt = h.textContent.trim();
      var kind = null;
      var title = txt;
      if (/^important distinction/i.test(txt) || /^important\b/i.test(txt) || /^note\b/i.test(txt)) {
        kind = 'distinction';
      } else if (/^example\b/i.test(txt) || /^case [a-z0-9]/i.test(txt)) {
        kind = 'example';
      } else if (/^advantages\b/i.test(txt)) {
        var nextUl = h.nextElementSibling;
        if (nextUl && nextUl.tagName === 'UL') nextUl.classList.add('list-pros');
      } else if (/^disadvantages\b|^limitations\b|^challenges\b/i.test(txt)) {
        var nextUl2 = h.nextElementSibling;
        if (nextUl2 && nextUl2.tagName === 'UL') nextUl2.classList.add('list-cons');
      }

      if (kind) {
        var callout = document.createElement('div');
        callout.className = 'doc-callout doc-callout-' + kind;
        var hdr = document.createElement('div');
        hdr.className = 'doc-callout-header';
        var icon = kind === 'distinction' ? '&#9888;' : '&#9881;';
        hdr.innerHTML = '<span class="doc-callout-icon">' + icon + '</span><span>' + esc(title) + '</span>';
        callout.appendChild(hdr);

        var body = document.createElement('div');
        body.className = 'doc-callout-body';
        callout.appendChild(body);

        h.parentNode.insertBefore(callout, h);
        var curr = h.nextElementSibling;
        h.remove();

        while (curr && !/^(H1|H2|H3|H4)$/i.test(curr.tagName) && !curr.classList.contains('pn-bar') && !curr.classList.contains('sec-wrap')) {
          var nxt = curr.nextElementSibling;
          body.appendChild(curr);
          curr = nxt;
        }
      }
    });

    // Check standalone paragraphs like "Advantages" or "Characteristics"
    var ps = [].slice.call(art.querySelectorAll('p'));
    ps.forEach(function (p) {
      var t = p.textContent.trim().toLowerCase();
      var next = p.nextElementSibling;
      if (next && next.tagName === 'UL') {
        if (t === 'advantages') {
          next.classList.add('list-pros');
          p.innerHTML = '<strong style="color:var(--nv-teal);">&#10003; ' + esc(p.textContent) + '</strong>';
        } else if (t === 'disadvantages' || t === 'limitations') {
          next.classList.add('list-cons');
          p.innerHTML = '<strong style="color:var(--nv-red);">&#9888; ' + esc(p.textContent) + '</strong>';
        } else if (t === 'characteristics') {
          p.innerHTML = '<strong style="color:var(--nv-navy);">&#9670; ' + esc(p.textContent) + '</strong>';
        }
      }
    });
  }

  /* ---- Terminology / Key Definition Badges ---- */
  function enhanceTerminology(art) {
    var ps = [].slice.call(art.querySelectorAll('p'));
    ps.forEach(function (p) {
      if (p.children.length === 0) {
        var txt = p.textContent.trim();
        var m = txt.match(/^([A-Za-z0-9\s\-/()]{2,30}):\s+(.+)$/);
        if (m && !p.closest('.doc-callout, .qa, .doc-hero')) {
          p.innerHTML = '<span class="term-badge">' + esc(m[1]) + '</span> ' + esc(m[2]);
        }
      }
    });
  }

  var spyItems = [];
  function runSpy() {
    if (!spyItems.length) return;
    var active = null;
    for (var i = 0; i < spyItems.length; i++) {
      if (spyItems[i].el.getBoundingClientRect().top <= 160) active = spyItems[i]; else break;
    }
    spyItems.forEach(function (it) {
      var on = (it === active);
      if (it.link.classList.contains('is-active') !== on) {
        it.link.classList.toggle('is-active', on);
        if (on) it.link.setAttribute('aria-current', 'true'); else it.link.removeAttribute('aria-current');
        if (on) {
          var sc = it.link.closest('.page-sidebar-scroll');
          if (sc) {
            var r = it.link.getBoundingClientRect(), s = sc.getBoundingClientRect();
            if (r.top < s.top + 40 || r.bottom > s.bottom - 40) sc.scrollTop += r.top - s.top - s.height / 2;
          }
        }
      }
    });
  }
  function wireSpy(art) {
    var links = {};
    [].forEach.call(document.querySelectorAll('.page-toc a[href^="#"]'), function (a) {
      links[decodeURIComponent(a.getAttribute('href').slice(1))] = a;
    });
    spyItems = [];
    [].forEach.call(art.querySelectorAll('h1[id],h2[id],h3[id]'), function (h) {
      if (links[h.id]) spyItems.push({ el: h, link: links[h.id] });
    });
    if (!spyItems.length) return;
    var pane = document.getElementById('content-pane'), ticking = false;
    var go = function () {
      if (ticking) return; ticking = true;
      requestAnimationFrame(function () { ticking = false; runSpy(); });
    };
    if (pane) pane.addEventListener('scroll', go, { passive: true });
    window.addEventListener('scroll', go, { passive: true });
    window.addEventListener('resize', go);
    runSpy();
  }

  function placeDock() {
    var dock = document.getElementById('fab-dock'), pane = document.getElementById('content-pane');
    if (!dock) return;
    if (MQ.matches || !pane) { dock.style.right = ''; return; }
    var r = pane.getBoundingClientRect();
    dock.style.right = Math.max(14, window.innerWidth - r.right + 18) + 'px';
  }

  function showShortcutsHelp() {
    if (document.getElementById('kb-modal')) return;
    var modal = document.createElement('div');
    modal.id = 'kb-modal';
    modal.className = 'kb-modal-backdrop';
    modal.innerHTML =
      '<div class="kb-modal">'
      + '<div class="kb-modal-header"><span>Keyboard Navigation</span><button type="button" class="kb-modal-close" aria-label="Close">&times;</button></div>'
      + '<div class="kb-modal-body">'
      + '<div class="kb-row"><span>Next Topic</span><kbd class="kb-key">]</kbd></div>'
      + '<div class="kb-row"><span>Previous Topic</span><kbd class="kb-key">[</kbd></div>'
      + '<div class="kb-row"><span>Zen Focus Mode (Toggle Sidebars)</span><kbd class="kb-key">Z</kbd></div>'
      + '<div class="kb-row"><span>Switch Theme (Dark / Light)</span><kbd class="kb-key">T</kbd></div>'
      + '<div class="kb-row"><span>Close Overlays</span><kbd class="kb-key">ESC</kbd></div>'
      + '</div></div>';
    document.body.appendChild(modal);
    modal.addEventListener('click', function (e) {
      if (e.target === modal || e.target.classList.contains('kb-modal-close')) modal.remove();
    });
  }

  function buildDock() {
    if (document.getElementById('fab-dock')) return;
    var dock = document.createElement('div');
    dock.id = 'fab-dock';
    dock.innerHTML =
      '<div class="fab-progress-badge" id="dock-progress" title="Reading Progress (Click to scroll down)">0%</div>'
      + '<button type="button" id="zen-toggle" aria-label="Zen Focus Mode" title="Zen Focus Mode (Z)">'
      + '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg></button>'
      + '<button type="button" id="theme-toggle" aria-label="Switch light / dark theme" title="Switch Theme (T)">'
      + '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 3v18" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none"/></svg></button>'
      + '<button type="button" id="to-top" aria-label="Back to top" title="Back to top">'
      + '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button>';
    document.body.appendChild(dock);

    document.getElementById('theme-toggle').addEventListener('click', function () {
      var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
    });

    document.getElementById('zen-toggle').addEventListener('click', function () {
      document.body.classList.toggle('zen-mode');
      setTimeout(placeDock, 260);
    });

    document.getElementById('dock-progress').addEventListener('click', function () {
      var pane = document.getElementById('content-pane');
      if (pane) pane.scrollBy({ top: 380, behavior: 'smooth' });
    });

    document.getElementById('to-top').addEventListener('click', function () {
      var pane = document.getElementById('content-pane');
      if (pane && pane.scrollTo) pane.scrollTo({ top: 0, behavior: 'smooth' });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Global keyboard shortcuts
    document.addEventListener('keydown', function (e) {
      if (/INPUT|TEXTAREA|SELECT/i.test(e.target.tagName)) return;
      var k = e.key;
      if (k === ']') {
        var n = document.querySelector('a.pn-next');
        if (n && n.href) location.href = n.href;
      } else if (k === '[') {
        var p = document.querySelector('a.pn-prev');
        if (p && p.href) location.href = p.href;
      } else if (k === 'z' || k === 'Z') {
        document.body.classList.toggle('zen-mode');
        setTimeout(placeDock, 260);
      } else if (k === 't' || k === 'T') {
        var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
      } else if (k === '?') {
        showShortcutsHelp();
      } else if (k === 'Escape') {
        var m = document.getElementById('kb-modal');
        if (m) m.remove();
      }
    });

    placeDock();
    window.addEventListener('resize', placeDock);
  }

  function enhanceContent() {
    var pane = document.getElementById('content-pane');
    if (!pane) return;
    var art = pane.querySelector('article') || pane;
    if (art.getAttribute('data-enhanced')) return;
    art.setAttribute('data-enhanced', '1');
    art.classList.add('doc');

    /* 1. stray paste artefacts from source markdown */
    textNodes(art, function (n) {
      if (/Pasted markdown\(\d+\)/.test(n.nodeValue))
        n.nodeValue = n.nodeValue.replace(/\s*Pasted markdown\(\d+\)/g, '');
    });

    /* 2. headings: first H1 = title, the rest = numbered sections */
    var heads = [].slice.call(art.querySelectorAll('h1,h2')).filter(function (h) {
      return !h.closest('.page-toc, nav, .pn-bar, .toc') && !/^\s*contents\s*$/i.test(h.textContent);
    });
    var title = null;
    if (heads.length && heads[0].tagName === 'H1' && !/^\s*\d+[.)]\s/.test(heads[0].textContent)) title = heads.shift();
    var secs = heads;

    secs.forEach(function (h) {
      h.classList.add('sec');
      var w = document.createTreeWalker(h, NodeFilter.SHOW_TEXT, null), t = w.nextNode(), m, num = null;
      if (t && (m = t.nodeValue.match(/^\s*(\d+)\.\s+/))) {
        t.nodeValue = t.nodeValue.slice(m[0].length);
        num = document.createElement('span'); num.className = 'sec-num'; num.textContent = m[1];
      } else h.classList.add('sec--plain');
      var ttl = document.createElement('span'); ttl.className = 'sec-title';
      while (h.firstChild) ttl.appendChild(h.firstChild);
      if (num) h.appendChild(num);
      h.appendChild(ttl);
    });

    /* 3. wrap each section so the ladder rail runs through it */
    var same = secs.length && secs.every(function (h) { return h.parentNode === secs[0].parentNode; });
    var wraps = [];
    if (same) {
      secs.forEach(function (h, i) {
        var next = secs[i + 1], wrap = document.createElement('section');
        wrap.className = 'sec-wrap';
        h.parentNode.insertBefore(wrap, h);
        var n = h;
        while (n && n !== next && !(n.classList && n.classList.contains('pn-bar'))) {
          var nx = n.nextSibling; wrap.appendChild(n); n = nx;
        }
        var txt = h.textContent;
        if (/mental model|consolidated definition/i.test(txt)) wrap.classList.add('is-key');
        if (/interview/i.test(txt)) buildQA(wrap);
        wraps.push(wrap);
      });
    }

    /* 4. Process flows & Callout boxes */
    enhanceProcessFlows(art);
    enhanceCallouts(art);
    enhanceTerminology(art);

    /* 5. Code blocks -> diagrams / logic / plain snippets with action headers */
    var nDiagram = 0;
    [].forEach.call(art.querySelectorAll('pre'), function (pre) {
      if (pre.parentNode.classList.contains('pre-box')) return;
      var code = pre.querySelector('code') || pre, txt = pre.textContent, kind;
      if (/\bIF\b/.test(txt) && /\bTHEN\b/.test(txt)) kind = 'logic';
      else if (/[\u2193\u2192\u2190\u2191\u2194\u2502\u250c\u2514\u251c\u2500\u2510\u2518\u2524]|->/.test(txt)) kind = 'diagram';
      else kind = 'plain';
      pre.classList.add(kind);
      if (kind === 'diagram') nDiagram++;

      if (!code.children.length && kind !== 'plain') {
        var html = esc(code.textContent);
        if (kind === 'logic') {
          html = html.replace(/\b(IF|THEN|AND|OR|NOT|ELSE)\b|\b(TRUE|FALSE)\b/g, function (m, a) {
            return '<span class="' + (a ? 'kw' : 'val') + '">' + m + '</span>';
          });
        } else {
          html = html.replace(/([\u250c\u2510\u2514\u2518\u2502\u2500\u251c\u2524\u252c\u2534\u253c]+)|([\u2193\u2192\u2190\u2191\u2194\u2195]+|-&gt;)|\b(PASS|YES)\b|\b(FAIL|FAULT|NO)\b|\b(STATE \d+)\b/g,
            function (m, a, b, c, d) {
              return '<span class="' + (a ? 'bx' : b ? 'ar' : c ? 'ok' : d ? 'bad' : 'st') + '">' + m + '</span>';
            });
        }
        code.innerHTML = html;
      }

      var box = document.createElement('div');
      box.className = 'pre-box has-header';
      pre.parentNode.insertBefore(box, pre);

      var hdr = document.createElement('div');
      hdr.className = 'pre-header';
      var tagText = kind === 'diagram' ? 'Schematic Diagram' : (kind === 'logic' ? 'Logic Sequence' : 'Code');
      hdr.innerHTML = '<span class="pre-tag">' + tagText + '</span><div class="pre-actions"><button type="button" class="pre-btn copy-btn">Copy</button></div>';

      var cpBtn = hdr.querySelector('.copy-btn');
      cpBtn.addEventListener('click', function () {
        var done = function () { cpBtn.textContent = 'Copied'; setTimeout(function () { cpBtn.textContent = 'Copy'; }, 1400); };
        try { navigator.clipboard.writeText(txt).then(done); } catch (e) {
          var ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); done();
        }
      });

      box.appendChild(hdr);
      box.appendChild(pre);
    });

    /* 6. Tables: scroll wrapper + toolbar with search & TSV copy */
    [].forEach.call(art.querySelectorAll('table'), function (t) {
      if (t.parentNode.classList.contains('table-wrap')) return;
      var w = document.createElement('div'); w.className = 'table-wrap';
      t.parentNode.insertBefore(w, t);

      var rows = [].slice.call(t.querySelectorAll('tbody tr'));
      if (rows.length > 2) {
        var tb = document.createElement('div');
        tb.className = 'table-toolbar';
        tb.innerHTML =
          '<input type="search" class="table-filter-input" placeholder="Search table rows..." aria-label="Search table">'
          + '<div style="display:flex;align-items:center;gap:8px;">'
          + '<span class="table-count">' + rows.length + ' rows</span>'
          + '<button type="button" class="table-btn" data-act="copy">Copy Table</button>'
          + '</div>';
        w.appendChild(tb);

        var filter = tb.querySelector('.table-filter-input');
        filter.addEventListener('input', function () {
          var q = filter.value.trim().toLowerCase();
          rows.forEach(function (r) {
            r.hidden = (q && r.textContent.toLowerCase().indexOf(q) === -1);
          });
        });

        var copyBtn = tb.querySelector('[data-act="copy"]');
        copyBtn.addEventListener('click', function () {
          var lines = [];
          [].forEach.call(t.querySelectorAll('tr'), function (tr) {
            var cols = [].map.call(tr.querySelectorAll('th, td'), function (c) { return c.textContent.trim().replace(/\t/g, ' '); });
            lines.push(cols.join('\t'));
          });
          var text = lines.join('\n');
          try {
            navigator.clipboard.writeText(text).then(function () {
              copyBtn.textContent = 'Copied!';
              setTimeout(function () { copyBtn.textContent = 'Copy Table'; }, 1400);
            });
          } catch (e) {}
        });
      }

      w.appendChild(t);
      if (t.rows && t.rows[0] && t.rows[0].cells.length === 2) t.classList.add('cmp');
    });

    /* 7. Short bullet lists become chips */
    [].forEach.call(art.querySelectorAll('ul'), function (ul) {
      if (ul.closest('.page-toc, nav, .qa, .doc-flow, .chips')) return;
      var lis = [].filter.call(ul.children, function (c) { return c.tagName === 'LI'; });
      if (lis.length < 4 || ul.querySelector('ul,ol,p,pre')) return;
      if (lis.every(function (li) { return li.textContent.trim().length <= 34; })) ul.classList.add('chips');
    });

    /* 8. Hero */
    if (title) {
      var hero = document.createElement('header'); hero.className = 'doc-hero';
      title.parentNode.insertBefore(hero, title);
      if (CUR && CUR.levels && CUR.levels.length) {
        var bc = document.createElement('div'); bc.className = 'doc-crumbs';
        bc.innerHTML = CUR.levels.map(function (l) { return '<span>' + prettyLabel(l).replace(/<span class="nn">\d+<\/span>/, '') + '</span>'; }).join('');
        hero.appendChild(bc);
      }
      hero.appendChild(title);
      var raw = title.textContent.trim(), m2 = raw.match(/^[^:]{1,40}:\s*(.+)$/);
      if (m2 && !title.children.length) title.textContent = m2[1];
      var shown = title.textContent.trim().toLowerCase();
      if (CUR && CUR.description && CUR.description.trim().toLowerCase() !== shown) {
        var sub = document.createElement('p'); sub.className = 'doc-hero-sub'; sub.textContent = CUR.description;
        hero.appendChild(sub);
      }
      var words = (art.textContent || '').split(/\s+/).length, mins = Math.max(1, Math.round(words / 210));
      var chips = [[secs.length, 'sections'], [nDiagram, 'diagrams'], [mins, 'min read']].filter(function (c) { return c[0] > 0; });
      var row = document.createElement('div'); row.className = 'doc-chips';
      row.innerHTML = chips.map(function (c) { return '<span class="doc-chip"><b>' + c[0] + '</b> ' + c[1] + '</span>'; }).join('');
      hero.appendChild(row);
      var pt = art.querySelector('.pn-top');
      if (pt) hero.insertAdjacentElement('afterend', pt);
    }

    wireSpy(art);
  }

  function init() {
    wireToggles(); wireTOC(); wireProgress(); renderNav();
    try { enhanceContent(); } catch (e) { if (window.console) console.warn('enhanceContent failed', e); }
    buildDock();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
