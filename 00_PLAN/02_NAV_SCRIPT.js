/* 02_NAV_SCRIPT.js
   NAV_SCRIPT_V2  (marker: do not remove)
   V3: relative links (works from any folder / GitHub Pages) + Prev/Next bars.
   Static. Loaded by every generated HTML. Never rewritten by Python. */

(function () {
  'use strict';

  // ---- locate the study root = parent folder of the folder holding this script
  var SELF = (document.currentScript && document.currentScript.src) || '';
  if (!SELF) {
    var ss = document.getElementsByTagName('script');
    for (var i = 0; i < ss.length; i++)
      if (/02_NAV_SCRIPT\.js/.test(ss[i].src)) SELF = ss[i].src;
  }
  var ROOT = SELF ? new URL('../', SELF.split('?')[0]) : new URL('./', location.href);

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

    var out = ['<ul>'];
    items.forEach(function (it) {
      if (it.kind === 'folder') {
        var child = node.children[it.payload];
        var inner = renderNode(child);
        if (!inner) return;
        out.push('<li><details' + (child._hasCurrent ? ' open' : '') + '>');
        out.push('<summary><span class="gnav-folder-name">' + esc(it.payload) + '</span></summary>');
        out.push(inner + '</details></li>');
      } else {
        var f = it.payload, label = esc(it.name);
        if (f._cur) {
          out.push('<li><span class="gnav-file is-current">' + label + '</span></li>');
        } else if (f.exists === false) {
          out.push('<li><span class="gnav-file gnav-missing" title="Not generated yet">' + label + '</span></li>');
        } else {
          out.push('<li><a class="gnav-file" href="' + esc(f._href) + '">' + label + '</a></li>');
        }
      }
    });
    out.push('</ul>');
    return out.join('');
  }

  // ---- Previous / Next (global INDEX order, skips pages not generated yet)
  function pad(n) { n = String(n); while (n.length < 4) n = '0' + n; return n; }

  function pnButton(f, dir) {
    var lbl = dir === 'prev' ? '&larr; Previous' : 'Next &rarr;';
    if (!f) return '<span class="pn-btn pn-' + dir + ' pn-disabled"><span class="pn-lbl">' + lbl + '</span></span>';
    return '<a class="pn-btn pn-' + dir + '" rel="' + dir + '" href="' + esc(f._href)
         + '" title="' + esc(f.title) + '"><span class="pn-lbl">' + lbl
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

    injectPrevNext(data.files, cur);
    if (!container) return;

    var tree = buildTree(data.files);
    markCurrent(tree);
    var body = renderNode(tree);
    container.innerHTML = '<div class="gnav">' + (body || '<div class="gnav-empty">Nothing to show.</div>') + '</div>';

    var el = container.querySelector('.gnav-file.is-current');
    if (el) setTimeout(function () { try { el.scrollIntoView({ block: 'center' }); } catch (e) {} }, 40);
  }

  var MQ = window.matchMedia('(max-width: 900px)');   // phone / narrow layout

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
        if (MQ.matches) {                       // phone: slide-in drawer
          var open = !sb.classList.contains('is-open');
          closeDrawers();
          if (open) { sb.classList.add('is-open'); document.body.classList.add('sb-open', p[2]); }
          return;
        }
        sb.classList.toggle('is-collapsed');    // desktop: collapse
        try { localStorage.setItem(key, sb.classList.contains('is-collapsed') ? '1' : '0'); } catch (e) {}
      });
    });
  }

  function wireTOC() {
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
    if (!pane || !bar) return;
    var upd = function () {
      var st, max;
      if (MQ.matches) {                         // phone: the whole page scrolls
        var de = document.documentElement;
        st = window.pageYOffset || de.scrollTop;
        max = de.scrollHeight - window.innerHeight;
      } else {
        st = pane.scrollTop;
        max = pane.scrollHeight - pane.clientHeight;
      }
      bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, st / max) : 0) + ')';
    };
    pane.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    upd();
  }

  function init() { wireToggles(); wireTOC(); wireProgress(); renderNav(); }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
