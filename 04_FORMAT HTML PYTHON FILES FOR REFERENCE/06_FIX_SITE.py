#!/usr/bin/env python3
"""
fix_site.py - makes the study site portable (move folder / GitHub Pages) and
adds Previous/Next buttons driven by the global INDEX.

Put it in 00_PLAN (or anywhere) and run:   python fix_site.py
Options:
  --root  PATH   study root (default: parent of 00_PLAN; auto-detected)
  --check FILE   FILE_CHECK.TXT location (default: searched automatically)
  --fix-html     also rewrite the ../../00_PLAN prefix inside HTML files if a
                 page was moved (otherwise only reported)
  --no-github    skip .nojekyll / index.html / .gitignore creation

What it changes:
  00_PLAN/nav_data.json, nav_data.js   -> relative paths + index (originals -> .bak)
  00_PLAN/02_NAV_SCRIPT.js             -> relative links, Prev/Next bars
  00_PLAN/02_NAV_STYLE.css             -> Prev/Next styles appended
  HTML files are NOT rewritten (they already load 00_PLAN via relative paths
  and the Prev/Next bars are injected by the script at page load).
"""
import argparse, json, os, re, shutil, sys
from datetime import datetime
from urllib.parse import unquote

# ----------------------------------------------------------------- JS / CSS
NAV_JS = r'''/* 02_NAV_SCRIPT.js
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
'''

CSS_MARK = "NAV_STYLE_PN_V1"
NAV_CSS_ADD = '''
/* NAV_STYLE_PN_V1 : previous / next bars (appended by fix_site.py) */
.pn-bar { display:flex; align-items:stretch; justify-content:space-between; gap:12px;
  font-family: var(--nv-font); }
.pn-top    { margin:0 0 24px; padding-bottom:14px; border-bottom:1px solid var(--nv-rule); }
.pn-bottom { margin:32px 0 8px; padding-top:16px;  border-top:1px solid var(--nv-rule); }
.pn-btn { flex:0 1 38%; min-width:0; display:flex; flex-direction:column; gap:2px;
  padding:8px 14px; border:1px solid var(--nv-rule); border-radius:6px;
  background:var(--nv-paper); color:var(--nv-link) !important; text-decoration:none !important;
  transition: background 120ms ease, border-color 120ms ease; }
.pn-next { text-align:right; margin-left:auto; }
a.pn-btn:hover { background:var(--nv-hover); border-color:var(--nv-link); }
.pn-lbl { font-size:.62rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
  color:var(--nv-ink-subtle); }
.pn-title { font-size:.82rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.pn-disabled { opacity:.35; pointer-events:none; }
.pn-pos { align-self:center; font-size:.72rem; color:var(--nv-ink-subtle); white-space:nowrap; }
.gnav .gnav-missing { display:block; padding:5px 8px; opacity:.45; cursor:default;
  font-style:italic; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
@media (max-width: 600px) { .pn-title { display:none; } .pn-btn { flex-basis:auto; } }
'''


NAV_CSS_MOBILE_MARK = "NAV_STYLE_MOBILE_V1"
NAV_CSS_MOBILE = '''
/* NAV_STYLE_MOBILE_V1 : phone layout - content first, side panels as drawers */
#sb-backdrop { display:none; }
@media (max-width: 900px) {
  html { -webkit-text-size-adjust:100%; }
  html body { overflow-x:hidden; }

  /* panels become slide-in drawers (closed by default) */
  body .page-sidebar {
    position:fixed; top:0; bottom:0; height:auto;
    width:min(86vw, 340px) !important; opacity:1 !important; pointer-events:auto;
    z-index:60; background:var(--nv-paper);
    transition:transform 220ms ease;
  }
  body .page-sidebar-left  { left:0;  transform:translateX(-105%); }
  body .page-sidebar-right { right:0; transform:translateX(105%); }
  body .page-sidebar.is-open { transform:none; }
  body .page-sidebar .page-sidebar-scroll { overflow-y:auto !important; -webkit-overflow-scrolling:touch; }

  body.sb-open #sb-backdrop { display:block; position:fixed; inset:0; z-index:55;
    background:rgba(0,0,0,.45); }

  /* edge tabs to open / close the drawers */
  body .side-toggle { display:flex !important; width:30px; height:56px; z-index:80; opacity:.9; }
  body .side-toggle-left  { left:0;  border-left:none;  border-radius:0 8px 8px 0; }
  body .side-toggle-right { right:0; border-right:none; border-radius:8px 0 0 8px; }
  body.sb-left-open  .side-toggle-left  { left:calc(min(86vw, 340px) - 30px); }
  body.sb-right-open .side-toggle-right { right:calc(min(86vw, 340px) - 30px); }

  /* readable content on small screens */
  body .content-pane { padding:12px 10px 40px; }
  body .content { padding:20px 12px 36px; }
  .content img { max-width:100%; height:auto; }
  .content table { display:block; max-width:100%; overflow-x:auto; }
  .content pre { overflow-x:auto; max-width:100%; }
  mjx-container[display="true"] { overflow-x:auto; overflow-y:hidden; max-width:100%; }
  .content p { text-align:left; }
}
'''

GITIGNORE = """# local-only files (safe to edit)
00_PLAN/01_AUTOMATION/LOG/
00_PLAN/01_AUTOMATION/pointer.json
*.bak
~$*
Thumbs.db
desktop.ini
"""

# ----------------------------------------------------------------- helpers
def find_root(arg):
    if arg:
        return os.path.abspath(arg)
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here).lower() == "00_plan":
        return os.path.dirname(here)
    if os.path.isdir(os.path.join(here, "00_PLAN")):
        return here
    cur = here
    while True:  # walk upwards
        if os.path.isdir(os.path.join(cur, "00_PLAN")):
            return cur
        up = os.path.dirname(cur)
        if up == cur:
            sys.exit("Cannot find the root (folder containing 00_PLAN). Use --root.")
        cur = up

def find_check(arg, root, plan):
    cands = [arg] if arg else [
        os.path.join(plan, "01_AUTOMATION", "FILE_CHECK.TXT"),
        os.path.join(plan, "FILE_CHECK.TXT"),
        os.path.join(root, "FILE_CHECK.TXT"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "FILE_CHECK.TXT"),
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    sys.exit("FILE_CHECK.TXT not found. Use --check PATH.")

_dir_cache = {}
def exact_exists(path):
    """True only if every path part matches in exact case (what GitHub needs)."""
    path = os.path.abspath(path)
    drive, rest = os.path.splitdrive(path)
    cur = drive + os.sep
    for part in [p for p in rest.split(os.sep) if p]:
        if cur not in _dir_cache:
            try: _dir_cache[cur] = set(os.listdir(cur))
            except OSError: return False
        if part not in _dir_cache[cur]:
            return False
        cur = os.path.join(cur, part)
    return True

def backup_once(p):
    if os.path.isfile(p) and not os.path.isfile(p + ".bak"):
        shutil.copy2(p, p + ".bak")

def write(p, text):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

# ----------------------------------------------------------------- nav data
def build_nav(root, plan, check_file):
    old = {}
    oj = os.path.join(plan, "nav_data.json")
    if os.path.isfile(oj):
        try:
            for f in json.load(open(oj, encoding="utf-8")).get("files", []):
                p = f.get("path") or f.get("key_path", "")
                p = p.replace("\\", "/")
                m = re.search(re.escape(os.path.basename(root)) + r"/(.*)$", p, re.I)
                old[(m.group(1) if m else p).lower()] = f
        except Exception as e:
            print("  note: could not read old nav_data.json:", e)

    rname = os.path.basename(root).lower()
    files, skipped, seen = [], 0, set()
    for line in open(check_file, encoding="utf-8-sig").read().splitlines():
        parts = line.strip().strip("|").split("|")
        if len(parts) < 3 or not parts[0].strip().isdigit():
            continue
        idx, folder, fname = int(parts[0]), parts[1].strip(), parts[2].strip()
        segs = [s for s in re.split(r"[\\/]+", folder) if s]
        low = [s.lower() for s in segs]
        if rname in low:
            segs = segs[low.index(rname) + 1:]
        else:
            skipped += 1
            print(f"  WARNING: row {idx:04d} path does not contain '{os.path.basename(root)}': {folder}")
            continue
        stem = os.path.splitext(fname)[0]
        rel = "/".join(segs + [stem + ".html"])
        if rel.lower() in seen:
            print(f"  WARNING: duplicate path for index {idx:04d}: {rel}")
        seen.add(rel.lower())
        o = old.get(rel.lower(), {})
        files.append({
            "index": idx,
            "path": rel,
            "title": stem,
            "filename": stem + ".html",
            "levels": segs,
            "exists": exact_exists(os.path.join(root, *rel.split("/"))),
            "description": o.get("description", ""),
        })
    files.sort(key=lambda f: f["index"])
    return {"version": 2, "generated": datetime.now().isoformat(timespec="seconds"),
            "files": files}, skipped

# ----------------------------------------------------------------- scans
ATTR = re.compile(r'(?:src|href)\s*=\s*"([^"]*)"', re.I)
ABS  = re.compile(r'^(?:file:|[A-Za-z]:[\\/])', re.I)
PLANREF = re.compile(r'((?:\.\./)*)00_PLAN')

def scan_html(root, plan, fix):
    pages = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in (".git", "00_PLAN") and not d.endswith("_assets")]
        for f in fn:
            if f.lower().endswith(".html") and dp != root:
                pages.append(os.path.join(dp, f))
    abs_refs, missing, wrong_depth, fixed = [], [], [], 0
    for pth in pages:
        raw = open(pth, "r", encoding="utf-8", errors="replace", newline="").read()
        d = os.path.dirname(pth)
        rel = os.path.relpath(plan, d).replace("\\", "/")      # e.g. ../../00_PLAN
        for m in PLANREF.finditer(raw):
            want = rel[: -len("00_PLAN")]
            if m.group(1) != want:
                wrong_depth.append(pth); break
        for ref in ATTR.findall(raw):
            r = ref.strip()
            if not r or r.startswith(("#", "http:", "https:", "mailto:", "data:", "javascript:", "//")):
                continue
            if ABS.match(r):
                abs_refs.append((pth, r)); continue
            target = unquote(re.split(r"[?#]", r)[0])
            if target and not exact_exists(os.path.normpath(os.path.join(d, target))):
                missing.append((pth, r))
        if fix and pth in wrong_depth:
            new = PLANREF.sub(lambda m: rel[: -len("00_PLAN")] + "00_PLAN", raw)
            if new != raw:
                open(pth, "w", encoding="utf-8", newline="").write(new); fixed += 1
    return pages, abs_refs, missing, wrong_depth, fixed

def github_files(root, plan, nav):
    made = []
    nj = os.path.join(root, ".nojekyll")
    if not os.path.isfile(nj):
        write(nj, ""); made.append(".nojekyll")
    gi = os.path.join(root, ".gitignore")
    if not os.path.isfile(gi):
        write(gi, GITIGNORE); made.append(".gitignore")
    ix = os.path.join(root, "index.html")
    if not os.path.isfile(ix):
        target = None
        if os.path.isfile(os.path.join(plan, "03_HTML_INDEX.html")):
            target = "00_PLAN/03_HTML_INDEX.html"
        else:
            for f in nav["files"]:
                if f["exists"]:
                    target = f["path"]; break
        if target:
            write(ix, f'<!DOCTYPE html><html><head><meta charset="utf-8">'
                      f'<meta http-equiv="refresh" content="0; url={target}">'
                      f'<title>Study</title></head><body>'
                      f'<a href="{target}">Open the study index</a></body></html>\n')
            made.append("index.html")
    return made

def size_report(root):
    total, big = 0, []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            p = os.path.join(dp, f)
            try: s = os.path.getsize(p)
            except OSError: continue
            total += s
            if s > 50 * 1024 * 1024: big.append((p, s))
    return total, big

# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root"); ap.add_argument("--check")
    ap.add_argument("--fix-html", action="store_true")
    ap.add_argument("--no-github", action="store_true")
    a = ap.parse_args()

    root = find_root(a.root)
    plan = os.path.join(root, "00_PLAN")
    os.makedirs(plan, exist_ok=True)
    chk = find_check(a.check, root, plan)
    print(f"Root       : {root}\nFILE_CHECK : {chk}")

    nav, skipped = build_nav(root, plan, chk)
    n = len(nav["files"]); ex = sum(1 for f in nav["files"] if f["exists"])
    print(f"Nav entries: {n}  (HTML present: {ex}, not generated yet: {n - ex}, skipped rows: {skipped})")

    for name in ("nav_data.json", "nav_data.js", "02_NAV_SCRIPT.js", "02_NAV_STYLE.css"):
        backup_once(os.path.join(plan, name))
    js = json.dumps(nav, indent=2, ensure_ascii=False)
    write(os.path.join(plan, "nav_data.json"), js + "\n")
    write(os.path.join(plan, "nav_data.js"),
          "/* nav_data.js - auto-generated (relative paths, no drive letters). */\nwindow.NAV_DATA = " + js + ";\n")
    write(os.path.join(plan, "02_NAV_SCRIPT.js"), NAV_JS)

    cssp = os.path.join(plan, "02_NAV_STYLE.css")
    css = open(cssp, encoding="utf-8").read() if os.path.isfile(cssp) else "/* 02_NAV_STYLE.css\n   NAV_STYLE_V2  (marker: do not remove) */\n"
    added = []
    for mark, block in ((CSS_MARK, NAV_CSS_ADD), (NAV_CSS_MOBILE_MARK, NAV_CSS_MOBILE)):
        if mark not in css:
            css = css.rstrip() + "\n" + block
            added.append(mark)
    if added:
        write(cssp, css)
    print("CSS        :", ("appended " + ", ".join(added)) if added else "already up to date")
    print("JS / JSON  : written (backups saved as *.bak, first run only)")

    pages, abs_refs, missing, wrong, fixed = scan_html(root, plan, a.fix_html)
    print(f"\nHTML scan  : {len(pages)} page(s) checked")
    print(f"  absolute D:\\ or file:/// references : {len(abs_refs)}")
    for p, r in abs_refs[:10]: print("     ", os.path.relpath(p, root), "->", r)
    print(f"  missing / wrong-case local files    : {len(missing)}")
    for p, r in missing[:10]: print("     ", os.path.relpath(p, root), "->", r)
    print(f"  pages with wrong 00_PLAN depth      : {len(wrong)}"
          + (f"  (fixed {fixed})" if a.fix_html else "  (run with --fix-html to repair)"))

    if not a.no_github:
        made = github_files(root, plan, nav)
        total, big = size_report(root)
        print(f"\nGitHub     : created {', '.join(made) if made else 'nothing new'}")
        print(f"  repo size now {total / 1024 / 1024:.1f} MB (GitHub: keep under ~1 GB, files under 100 MB)")
        for p, s in big: print(f"  TOO BIG: {p} ({s / 1024 / 1024:.0f} MB)")
    print("\nDone.")

if __name__ == "__main__":
    main()
