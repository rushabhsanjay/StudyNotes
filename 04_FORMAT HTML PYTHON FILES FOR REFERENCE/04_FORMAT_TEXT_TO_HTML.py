#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_FORMAT_TEXT_TO_HTML.py

Reads the clipboard, writes <out_dir>\\<base_name>.html, and rebuilds
the global navigation data from the Excel master table.

- Works with positional args from 02: <out_dir> <base_name>
- Falls back to D:\\00_ADMIN_FILES\\_py_args.txt (two lines)
- Falls back to cwd + "clipboard"
- Logs EVERYTHING to D:\\00_ADMIN_FILES\\04_last_run.log
- Never fails silently: every error is logged with traceback

Static assets (written once, never touched again):
    D:\\03_STUDY_FOR_CAREER\\00_PLAN\\02_NAV_SCRIPT.js
    D:\\03_STUDY_FOR_CAREER\\00_PLAN\\02_NAV_STYLE.css
Dynamic asset (regenerated every run from the Excel master table):
    D:\\03_STUDY_FOR_CAREER\\00_PLAN\\nav_data.js
    D:\\03_STUDY_FOR_CAREER\\00_PLAN\\nav_data.json

Dependencies:
    pip install pyperclip markdown openpyxl
"""

import html as _html
import json
import os
import re
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    import pyperclip
except ImportError:
    pyperclip = None
try:
    import markdown
except ImportError:
    markdown = None
try:
    import openpyxl
except ImportError:
    openpyxl = None


# ==================================================================
#  Paths / constants
# ==================================================================
ROOT_DIR   = r"D:\03_STUDY_FOR_CAREER"
PLAN_DIR   = os.path.join(ROOT_DIR, "00_PLAN")
EXCEL_PATH = os.path.join(PLAN_DIR, "00_STUDY_INDEX.xlsm")

NAV_JS_FILE   = os.path.join(PLAN_DIR, "02_NAV_SCRIPT.js")
NAV_CSS_FILE  = os.path.join(PLAN_DIR, "02_NAV_STYLE.css")
NAV_DATA_JS   = os.path.join(PLAN_DIR, "nav_data.js")
NAV_DATA_JSON = os.path.join(PLAN_DIR, "nav_data.json")

ARGS_FILE = r"D:\00_ADMIN_FILES\_py_args.txt"
LOG_FILE  = r"D:\00_ADMIN_FILES\04_last_run.log"
HTML_INDEX_FILE = os.path.join(PLAN_DIR, "03_HTML_INDEX.html")

STRIP_LONE_DIGITS = True
DOWNLOAD_TIMEOUT  = 25
DOWNLOAD_RETRIES  = 2

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")

IMG_LINK_RE   = re.compile(r'!?\[([^\]]*)\]\((https?://images\.openai\.com/[^)]+)\)')
LONE_DIGIT_RE = re.compile(r'^\s*\d{1,3}\s*$')


# ==================================================================
#  Logging
# ==================================================================
_LOG_STARTED = False

def log_reset():
    global _LOG_STARTED
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass
    _LOG_STARTED = True

def log(msg=""):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    try:
        print(line)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def log_exc(prefix):
    log(prefix)
    for line in traceback.format_exc().splitlines():
        log("    " + line)


# ==================================================================
#  Argument resolution
# ==================================================================
def resolve_args():
    argv = sys.argv[1:]
    if len(argv) >= 2:
        log(f"args from CLI: {argv[0]!r}  {argv[1]!r}")
        return argv[0], argv[1]

    if os.path.isfile(ARGS_FILE):
        try:
            with open(ARGS_FILE, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
            try:
                os.remove(ARGS_FILE)
            except OSError:
                pass
            if len(lines) >= 2 and lines[0].strip():
                log(f"args from _py_args.txt: {lines[0]!r}  {lines[1]!r}")
                return lines[0].strip(), lines[1].strip()
            log("_py_args.txt exists but has fewer than 2 non-empty lines")
        except Exception as e:
            log(f"could not read _py_args.txt: {e}")

    log("no args supplied; using cwd + 'clipboard'")
    return str(Path.cwd()), "clipboard"


# ==================================================================
#  Markdown cleanup
# ==================================================================
def clean_markdown(text):
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out, in_code, gap = [], False, 99
    for ln in lines:
        s = ln.strip()
        if s.startswith('```'):
            in_code = not in_code; out.append(ln); gap = 99; continue
        if in_code:
            out.append(ln); continue
        if s == '':
            out.append(ln); gap += 1; continue
        if STRIP_LONE_DIGITS and gap <= 3 and LONE_DIGIT_RE.match(s):
            gap += 1; continue
        gap = 99; out.append(ln)
    t = '\n'.join(out)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip() + '\n'

def split_first_h1(md_text):
    lines = md_text.split('\n')
    for i, ln in enumerate(lines):
        m = re.match(r'^#\s+(.+?)\s*#*\s*$', ln)
        if m:
            title = m.group(1).strip()
            del lines[i]
            while i < len(lines) and not lines[i].strip():
                del lines[i]
            return title, '\n'.join(lines)
    return None, md_text


# ==================================================================
#  Image download
# ==================================================================
def _download_one(url, dest_dir, idx):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "image/webp,image/png,image/jpeg,image/*;q=0.8,*/*;q=0.5",
    })
    last = None
    for _ in range(DOWNLOAD_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as r:
                data = r.read()
                ctype = (r.headers.get("Content-Type") or "").lower()
            if not data:
                last = "empty"; continue
            ext = ".jpg"
            if   "png"  in ctype: ext = ".png"
            elif "webp" in ctype: ext = ".webp"
            elif "gif"  in ctype: ext = ".gif"
            elif "jpeg" in ctype or "jpg" in ctype: ext = ".jpg"
            else:
                _, e2 = os.path.splitext(urllib.parse.urlparse(url).path)
                if e2.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                    ext = e2.lower()
            final = dest_dir / f"img_{idx:03d}{ext}"
            final.write_bytes(data); return final
        except Exception as e:
            last = e
    log(f"      ! download failed: {last}")
    return None

def process_images(text, assets_dir, rel_prefix):
    try:
        assets_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log(f"WARNING: could not create assets dir: {e}")
        return text, {"downloaded": 0, "failed": 0, "reused": 0}

    cache, stats = {}, {"downloaded": 0, "failed": 0, "reused": 0}
    def repl(m):
        alt = (m.group(1) or "image").strip() or "image"
        url = m.group(2)
        if url in cache:
            local = cache[url]; stats["reused"] += 1
        else:
            idx = stats["downloaded"] + stats["failed"] + 1
            log(f"  [{idx:>3}] {alt[:70]}")
            local = _download_one(url, assets_dir, idx)
            cache[url] = local
            if local is None: stats["failed"] += 1
            else:             stats["downloaded"] += 1
        if local is None:
            return f'[{alt}]({url})'
        return f'![{alt}]({rel_prefix}/{local.name})'
    return IMG_LINK_RE.sub(repl, text), stats


# ==================================================================
#  Math
# ==================================================================
def extract_math(text):
    store = []
    def si(m):
        i = len(store); store.append((m.group(1), False)); return f"\x00MATHI{i}\x00"
    def sd(m):
        i = len(store); store.append((m.group(1), True));  return f"\x00MATHD{i}\x00"
    text = re.sub(r'\\{1,2}\[(.+?)\\{1,2}\]', sd, text, flags=re.DOTALL)
    text = re.sub(r'\$\$(.+?)\$\$',             sd, text, flags=re.DOTALL)
    text = re.sub(r'\\{1,2}\((.+?)\\{1,2}\)',   si, text)
    return text, store

def _tex_esc(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def restore_math(h, store):
    def ri(m):
        l,_ = store[int(m.group(1))]
        return f'<span class="math-inline">\\({_tex_esc(l)}\\)</span>'
    def rd(m):
        l,_ = store[int(m.group(1))]
        return f'<div class="math-display">\\[{_tex_esc(l)}\\]</div>'
    h = re.sub(r'\x00MATHI(\d+)\x00', ri, h)
    h = re.sub(r'\x00MATHD(\d+)\x00', rd, h)
    h = re.sub(r'<p>\s*(<div class="math-display">.*?</div>)\s*</p>',
               r'\1', h, flags=re.DOTALL)
    return h


# ==================================================================
#  Excel  ->  nav data
# ==================================================================
def build_nav_data():
    base = {
        "version": 1,
        "root": ROOT_DIR.replace("\\", "/"),
        "generated": datetime.now().isoformat(timespec="seconds"),
        "files": [],
    }

    if openpyxl is None:
        log("WARNING: openpyxl not installed -> nav data will be empty")
        return base
    if not os.path.isfile(EXCEL_PATH):
        log(f"WARNING: Excel not found: {EXCEL_PATH} -> nav data will be empty")
        return base

    try:
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, read_only=True)
    except Exception as e:
        log(f"WARNING: could not open Excel: {e} -> nav data will be empty")
        return base

    try:
        if "MASTER" not in wb.sheetnames:
            log('WARNING: sheet "MASTER" not found -> nav data will be empty')
            return base

        ws = wb["MASTER"]

        tbl_ref = None
        try:
            for tname, t in ws.tables.items():
                if str(tname).strip() == "MASTER":
                    tbl_ref = t.ref
                    break
        except Exception:
            tbl_ref = None

        if tbl_ref:
            from openpyxl.utils.cell import range_boundaries
            min_col, min_row, max_col, max_row = range_boundaries(tbl_ref)
        else:
            min_col, min_row = 1, 1
            max_col = ws.max_column or 1
            max_row = ws.max_row    or 1

        rows = list(ws.iter_rows(min_row=min_row, max_row=max_row,
                                 min_col=min_col, max_col=max_col,
                                 values_only=True))
    finally:
        try: wb.close()
        except Exception: pass

    if not rows:
        log("WARNING: MASTER table is empty -> nav data will be empty")
        return base

    header = {}
    for i, h in enumerate(rows[0]):
        if h is not None:
            header[str(h).strip()] = i

    mc_i   = header.get("MasterColumn")
    tt_i   = header.get("TOPIC_TYPE")
    desc_i = header.get("Description")
    lvl_is = [header.get(f"LEVEL{i}") for i in range(1, 8)]
    lvl_is = [i for i in lvl_is if i is not None]

    if mc_i is None or tt_i is None:
        log("WARNING: MasterColumn or TOPIC_TYPE column not found -> nav data will be empty")
        return base

    root_abs = os.path.abspath(ROOT_DIR)
    files = []

    for row in rows[1:]:
        def cell(i):
            return row[i] if i is not None and i < len(row) else None

        mc = cell(mc_i)
        tt = cell(tt_i)
        if mc is None or tt is None:
            continue
        mc = str(mc).strip()
        tt = str(tt).strip().upper()
        if not mc or mc.lower() == "masterlevels":
            continue
        if tt != "FILE":
            continue

        parts = [mc]
        for li in lvl_is:
            v = cell(li)
            if v is None or str(v).strip() == "":
                break
            parts.append(str(v).strip())

        if len(parts) < 2:
            continue

        filename     = parts[-1]
        folder_parts = parts[:-1]
        full_path    = os.path.join(root_abs, *folder_parts, filename + ".html")

        desc  = cell(desc_i)

        key = full_path.replace("\\", "/")
        url = "file:///" + urllib.parse.quote(key, safe="/:")

        entry = {
            "key_path": key,
            "url":      url,
            "title":    filename,
            "filename": filename + ".html",
            "levels":   folder_parts,
        }
        if desc:
            entry["description"] = str(desc).strip()
        files.append(entry)

    files.sort(key=lambda f: f["key_path"].lower())
    base["files"] = files
    log(f"  excel: {len(files)} FILE entries, "
        f"{sum(1 for f in files if f['exists'])} exist on disk")
    return base


# ==================================================================
#  Static nav assets  (only written when missing)
# ==================================================================
STATIC_NAV_CSS = r"""/* 02_NAV_STYLE.css
   Static. Loaded by every generated HTML. Never rewritten by Python. */

:root {
  --nv-ink:#1a1a1a; --nv-ink-soft:#4a4a4a; --nv-ink-subtle:#6b6b6b;
  --nv-navy:#1a2e4a; --nv-link:#1a4e8a;
  --nv-paper:#ffffff; --nv-rule:#e7e7e5;
  --nv-hover:#f5f5f4; --nv-current:#eef2f7; --nv-current-fg:#1a2e4a;
  --nv-font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
            "Helvetica Neue",Arial,sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --nv-ink:#e8e8e6; --nv-ink-soft:#b8b8b6; --nv-ink-subtle:#8a8a88;
    --nv-navy:#8fb0d4; --nv-link:#7fb4e6;
    --nv-paper:#16181c; --nv-rule:#2a2e35;
    --nv-hover:#1f2228; --nv-current:#22262e; --nv-current-fg:#8fb0d4;
  }
}
.gnav { font-family:var(--nv-font); font-size:.82rem; line-height:1.4;
        color:var(--nv-ink-soft); padding:4px 0; }
.gnav .gnav-empty { padding:8px 2px; font-style:italic; color:var(--nv-ink-subtle); }
.gnav ul { list-style:none; padding-left:14px; margin:0; }
.gnav > ul { padding-left:0; }
.gnav li { margin:1px 0; }
.gnav details > summary {
  cursor:pointer; list-style:none; padding:5px 6px; border-radius:4px;
  color:var(--nv-ink-soft); display:flex; align-items:center; gap:5px;
  user-select:none; transition:background 120ms ease,color 120ms ease;
}
.gnav details > summary::-webkit-details-marker { display:none; }
.gnav details > summary::before {
  content:"\25B8"; display:inline-block; width:10px; font-size:.9em;
  color:var(--nv-ink-subtle); transition:transform 140ms ease;
}
.gnav details[open] > summary::before { transform:rotate(90deg); }
.gnav details > summary:hover { background:var(--nv-hover); color:var(--nv-link); }
.gnav .gnav-folder-name { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.gnav a.gnav-file, .gnav span.gnav-file {
  display:block; padding:5px 8px; margin:1px 0; border-radius:4px;
  color:var(--nv-ink-soft); text-decoration:none;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  transition:background 120ms ease,color 120ms ease;
}
.gnav a.gnav-file:hover { color:var(--nv-link); background:var(--nv-hover); }
.gnav span.gnav-file.is-current {
  color:var(--nv-current-fg); font-weight:600; background:var(--nv-current);
  cursor:default;
}
.gnav a.gnav-file.is-missing { color:var(--nv-ink-subtle); opacity:.75; }
.gnav a.gnav-file.is-missing:hover {
  color:var(--nv-ink-subtle); background:var(--nv-hover);
  text-decoration:line-through;
}
.side-toggle {
  position:fixed; top:50%; transform:translateY(-50%);
  width:20px; height:46px; background:var(--nv-paper); color:var(--nv-ink-soft);
  border:1px solid var(--nv-rule); border-radius:6px; padding:0;
  font-size:13px; line-height:1; cursor:pointer; z-index:40;
  display:flex; align-items:center; justify-content:center;
  transition:background 150ms ease,color 150ms ease,opacity 150ms ease;
}
.side-toggle:hover { background:var(--nv-hover); color:var(--nv-link); }
.side-toggle-left  { left:6px; }
.side-toggle-right { right:6px; }
.page-sidebar {
  background:var(--nv-paper);
  transition:width 200ms ease,opacity 180ms ease;
  overflow:hidden; display:flex; flex-direction:column;
}
.page-sidebar.is-collapsed { width:0 !important; opacity:0; pointer-events:none; }
.page-sidebar .page-sidebar-header {
  flex:0 0 auto; padding:22px 20px 14px; border-bottom:1px solid var(--nv-rule);
}
.page-sidebar .page-sidebar-scroll {
  flex:1 1 auto; min-height:0;
  overflow-y:auto; overflow-x:hidden; padding:14px 20px 24px;
}
.page-sidebar .page-sidebar-title {
  font-family:var(--nv-font); font-size:.92rem; font-weight:700;
  color:var(--nv-navy); margin:0 0 4px; line-height:1.25;
  letter-spacing:-.01em;
}
.page-sidebar .page-sidebar-sub {
  font-family:var(--nv-font); font-size:.65rem; text-transform:uppercase;
  letter-spacing:.14em; color:var(--nv-ink-subtle); margin:0;
}
.gonav-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-top: 14px;
  padding: 8px 14px;
  background: #1a2e4a;
  color: #ffffff !important;
  border: 1px solid #1a2e4a;
  border-radius: 6px;
  text-decoration: none !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, sans-serif;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  line-height: 1;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: background 140ms ease, box-shadow 140ms ease,
              transform 100ms ease;
}
.gonav-btn:hover {
  background: #1a4e8a;
  border-color: #1a4e8a;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
  color: #ffffff !important;
  text-decoration: none !important;
}
.gonav-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

@media (max-width:900px) {
  .side-toggle { display:none; }
  .page-sidebar { width:auto !important; opacity:1 !important; }
  .page-sidebar .page-sidebar-scroll { overflow:visible; }
}
"""


STATIC_NAV_JS = r"""/* 02_NAV_SCRIPT.js
   NAV_SCRIPT_V2  (marker: do not remove)
   Static. Loaded by every generated HTML. Never rewritten by Python. */

(function () {
  'use strict';

  function normPath(s) {
    if (!s) return '';
    try { s = decodeURIComponent(s); } catch (e) {}
    return s.replace(/\\/g, '/').replace(/^\/+/, '').toLowerCase();
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c];
    });
  }
  function cmp(a, b) {
    return String(a).localeCompare(String(b), undefined,
      { numeric: true, sensitivity: 'base' });
  }

  function buildTree(files) {
    var root = { children: {}, files: [] };
    files.forEach(function (f) {
      var node = root;
      (f.levels || []).forEach(function (lv) {
        if (!node.children[lv])
          node.children[lv] = { name: lv, children: {}, files: [] };
        node = node.children[lv];
      });
      node.files.push(f);
    });
    return root;
  }

  function markCurrent(node, currentKey) {
    var hit = false;
    (node.files || []).forEach(function (f) {
      if (normPath(f.key_path) === currentKey) hit = true;
    });
    Object.keys(node.children || {}).forEach(function (k) {
      if (markCurrent(node.children[k], currentKey)) hit = true;
    });
    node._hasCurrent = hit;
    return hit;
  }

  function renderNode(node, currentKey) {
    var folderKeys = Object.keys(node.children || {}).sort(cmp);
    var files = (node.files || []).slice().sort(function (a, b) {
      return cmp(a.title || a.filename, b.title || b.filename);
    });
    if (!folderKeys.length && !files.length) return '';

    var out = ['<ul>'];
    folderKeys.forEach(function (k) {
      var child = node.children[k];
      var inner = renderNode(child, currentKey);
      if (!inner) return;
      out.push('<li>');
      out.push('<details' + (child._hasCurrent ? ' open' : '') + '>');
      out.push('<summary><span class="gnav-folder-name">' + esc(k) + '</span></summary>');
      out.push(inner);
      out.push('</details></li>');
    });
    files.forEach(function (f) {
      var isCur = normPath(f.key_path) === currentKey;
      var label = esc(f.title || f.filename || '(untitled)');
      var exists = f.exists !== false;
      var cls = 'gnav-file'
              + (isCur ? ' is-current' : '')
              + (!isCur && !exists ? ' is-missing' : '');
      out.push('<li>');
      if (isCur) {
        out.push('<span class="' + cls + '">' + label + '</span>');
      } else {
        out.push('<a class="' + cls + '" href="' + esc(f.url) + '"'
                 + ' data-exists="' + (exists ? '1' : '0') + '"'
                 + ' data-path="' + esc(f.key_path) + '">'
                 + label + '</a>');
      }
      out.push('</li>');
    });
    out.push('</ul>');
    return out.join('');
  }

  function renderNav() {
    var container = document.getElementById('global-nav');
    if (!container) return;

    var data = window.NAV_DATA;
    if (!data || !Array.isArray(data.files)) {
      container.innerHTML = '<div class="gnav"><div class="gnav-empty">'
        + 'Navigation data not loaded (nav_data.js missing).</div></div>';
      return;
    }
    if (!data.files.length) {
      container.innerHTML = '<div class="gnav"><div class="gnav-empty">'
        + 'No HTML files generated yet.</div></div>';
      return;
    }

    var here = normPath(window.location.pathname);
    var currentKey = '';
    for (var i = 0; i < data.files.length; i++) {
      if (normPath(data.files[i].key_path) === here) { currentKey = here; break; }
    }

    var tree = buildTree(data.files);
    if (currentKey) markCurrent(tree, currentKey);
    var body = renderNode(tree, currentKey);

    container.innerHTML = '<div class="gnav">'
      + (body || '<div class="gnav-empty">Nothing to show.</div>')
      + '</div>';

    container.querySelectorAll('a.gnav-file[data-exists="0"]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        alert('File does not exist:\n\n' + a.getAttribute('data-path')
              + '\n\nGenerate it first.');
      });
    });

    var cur = container.querySelector('.gnav-file.is-current');
    if (cur) {
      setTimeout(function () {
        try { cur.scrollIntoView({ block: 'center' }); } catch (e) {}
      }, 40);
    }
  }

  function wireToggles() {
    [['side-toggle-left',  'page-sidebar-left'],
     ['side-toggle-right', 'page-sidebar-right']].forEach(function (p) {
      var btn = document.getElementById(p[0]);
      var sb  = document.getElementById(p[1]);
      if (!btn || !sb) return;
      var key = 'nav-collapsed-' + p[1];
      try { if (localStorage.getItem(key) === '1') sb.classList.add('is-collapsed'); } catch (e) {}
      btn.addEventListener('click', function () {
        sb.classList.toggle('is-collapsed');
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
        t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  function wireProgress() {
    var pane = document.getElementById('content-pane');
    var bar  = document.getElementById('progress-bar');
    if (!pane || !bar) return;
    var upd = function () {
      var max = pane.scrollHeight - pane.clientHeight;
      bar.style.transform = 'scaleX(' + (max > 0 ? pane.scrollTop / max : 0) + ')';
    };
    pane.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    upd();
  }

  function init() {
    wireToggles();
    wireTOC();
    wireProgress();
    renderNav();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
"""


def ensure_static_nav_assets():
    os.makedirs(PLAN_DIR, exist_ok=True)
    pairs = (
        (NAV_CSS_FILE, STATIC_NAV_CSS, "CSS", "NAV_STYLE_V2"),
        (NAV_JS_FILE,  STATIC_NAV_JS,  "JS",  "NAV_SCRIPT_V2"),
    )
    for path, content, label, marker in pairs:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    head = f.read(4000)
                if marker in head:
                    log(f"  {label} present and current: {path}")
                    continue
                log(f"  {label} outdated, refreshing: {path}")
            except Exception:
                pass
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            log(f"  {label} written: {path}")
        except Exception as e:
            log(f"WARNING: could not write nav {label}: {e}")


def write_nav_data(nav_data):
    try:
        os.makedirs(PLAN_DIR, exist_ok=True)
        js = json.dumps(nav_data, indent=2, ensure_ascii=False)
        with open(NAV_DATA_JSON, "w", encoding="utf-8") as f:
            f.write(js + "\n")
        with open(NAV_DATA_JS, "w", encoding="utf-8") as f:
            f.write("/* nav_data.js - auto-generated from the Excel master table. */\n")
            f.write("window.NAV_DATA = ")
            f.write(js)
            f.write(";\n")
        log(f"  nav data written: {NAV_DATA_JS}")
    except Exception as e:
        log(f"WARNING: could not write nav data: {e}")


# ==================================================================
#  Content CSS + template
# ==================================================================
CSS_MAIN = r"""
:root {
  --ink:#1a1a1a; --ink-soft:#4a4a4a; --ink-subtle:#6b6b6b;
  --paper:#ffffff; --paper-tint:#f7f7f5;
  --rule:#e7e7e5; --rule-strong:#cfcfcd;
  --navy:#1a2e4a; --link:#1a4e8a;
  --code-bg:#f5f5f4; --code-ink:#2b2b2b; --code-border:#e5e5e4;
  --table-alt:#fafafa; --table-header:#eef2f7; --quote-bar:#9fb0c0;
  --shadow-1:0 1px 3px rgba(0,0,0,.05),0 6px 20px rgba(0,0,0,.05);
  --shadow-side:0 0 14px -6px rgba(0,0,0,.15);
  --radius:8px;
  --scrollbar-thumb:#d0d0ce; --scrollbar-thumb-hover:#9a9a98;
  --scrollbar-track:transparent;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink:#e8e8e6; --ink-soft:#b8b8b6; --ink-subtle:#8a8a88;
    --paper:#16181c; --paper-tint:#101216;
    --rule:#2a2e35; --rule-strong:#3a3f48;
    --navy:#8fb0d4; --link:#7fb4e6;
    --code-bg:#1f2228; --code-ink:#d8d8d6; --code-border:#2c3038;
    --table-alt:#1b1e24; --table-header:#22262e; --quote-bar:#4a5a6a;
    --shadow-1:0 1px 3px rgba(0,0,0,.4),0 6px 20px rgba(0,0,0,.3);
    --shadow-side:0 0 14px -6px rgba(0,0,0,.7);
    --scrollbar-thumb:#3a3f48; --scrollbar-thumb-hover:#5a6068;
  }
}
*{box-sizing:border-box;}
html,body{height:100%;margin:0;overflow:hidden;}
body{
  background:var(--paper-tint);color:var(--ink);
  font-family:"Iowan Old Style","Palatino Linotype",Palatino,
              "Book Antiqua",Georgia,"Times New Roman",serif;
  font-size:17px;line-height:1.66;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
}
*{scrollbar-width:thin;scrollbar-color:var(--scrollbar-thumb) var(--scrollbar-track);}
::-webkit-scrollbar{width:10px;height:10px;}
::-webkit-scrollbar-track{background:var(--scrollbar-track);}
::-webkit-scrollbar-thumb{
  background-color:var(--scrollbar-thumb);border-radius:6px;
  border:2px solid transparent;background-clip:padding-box;
  transition:background-color 150ms ease;
}
::-webkit-scrollbar-thumb:hover,::-webkit-scrollbar-thumb:active{
  background-color:var(--scrollbar-thumb-hover);background-clip:padding-box;
}
::-webkit-scrollbar-corner{background:transparent;}

#progress-bar{
  position:fixed;top:0;left:0;right:0;height:2px;
  background:var(--link);transform-origin:0 50%;transform:scaleX(0);
  transition:transform 80ms linear;z-index:100;pointer-events:none;
}

.app{display:flex;height:100vh;width:100%;}

.page-sidebar{
  flex:0 0 auto;height:100vh;
  border-right:1px solid var(--rule);
  box-shadow:var(--shadow-side);
  position:relative;z-index:2;
}
.page-sidebar-right{border-right:none;border-left:1px solid var(--rule);}
.page-sidebar-left {width:clamp(240px,20vw,320px);}
.page-sidebar-right{width:clamp(260px,22vw,340px);}

.content-pane{
  flex:1 1 auto;min-width:0;height:100vh;
  overflow-y:auto;overflow-x:hidden;
  background:var(--paper-tint);
  padding:28px 40px 60px;
  scroll-behavior:smooth;
}
.content{
  max-width:1080px;margin:0 auto;padding:52px 68px 90px;
  background:var(--paper);border-radius:var(--radius);
  box-shadow:var(--shadow-1);
}
.content h1,.content h2,.content h3,.content h4,.content h5,.content h6{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
              "Helvetica Neue",Arial,sans-serif;
  color:var(--navy);line-height:1.25;letter-spacing:-.01em;font-weight:600;
  margin:1.9em 0 .55em;scroll-margin-top:32px;
}
.content h1{font-size:1.75em;padding-bottom:.3em;
  border-bottom:2px solid var(--rule-strong);margin-top:0;}
.content h2{font-size:1.4em;padding-bottom:.22em;
  border-bottom:1px solid var(--rule);}
.content h3{font-size:1.18em;}
.content h4{font-size:1.05em;}
.content h5{font-size:1em;font-style:italic;}
.content h6{font-size:1em;font-style:italic;color:var(--ink-soft);}
.content p{margin:0 0 1em;text-align:justify;hyphens:auto;}
.content ul,.content ol{margin:.6em 0 1.1em;padding-left:1.6em;}
.content li{margin:.25em 0;}
.content strong{color:var(--ink);font-weight:700;}
.content em{font-style:italic;}
.content code{
  font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,
              "Liberation Mono",monospace;
  font-size:.88em;background:var(--code-bg);color:var(--code-ink);
  padding:.14em .4em;border-radius:4px;border:1px solid var(--code-border);
  white-space:nowrap;
}
.content pre{
  background:var(--code-bg);border:1px solid var(--code-border);
  border-radius:var(--radius);padding:16px 18px;overflow-x:auto;
  font-size:.85em;line-height:1.55;margin:1.2em 0;
}
.content pre code{background:none;border:none;padding:0;font-size:1em;white-space:pre;}
.content table{
  border-collapse:collapse;width:100%;margin:1.4em 0;font-size:.94em;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
              "Helvetica Neue",Arial,sans-serif;
  overflow:hidden;border-radius:6px;box-shadow:0 0 0 1px var(--rule);
}
.content thead th{
  background:var(--table-header);color:var(--navy);font-weight:600;
  text-align:left;padding:10px 14px;border:1px solid var(--rule-strong);
  font-size:.93em;letter-spacing:.01em;
}
.content tbody td{padding:9px 14px;border:1px solid var(--rule);
  vertical-align:top;line-height:1.55;}
.content tbody tr:nth-child(even){background:var(--table-alt);}
.content blockquote{
  margin:1.2em 0;padding:.5em 0 .5em 1.2em;
  border-left:4px solid var(--quote-bar);
  color:var(--ink-soft);font-style:italic;
}
.content blockquote p:last-child{margin-bottom:0;}
.content img{
  max-width:100%;height:auto;display:block;margin:1.6em auto;
  border-radius:var(--radius);border:1px solid var(--rule);
  box-shadow:var(--shadow-1);background:var(--paper);
}
.content a{color:var(--link);text-decoration:underline;
  text-decoration-color:rgba(128,128,128,.4);text-underline-offset:2px;}
.content a:hover{text-decoration-color:currentColor;}
.content hr{border:none;border-top:1px solid var(--rule-strong);margin:2.4em 0;}
.content .math-inline{font-size:1.02em;}
.content .math-display{margin:1.6em 0;text-align:center;
  overflow-x:auto;overflow-y:hidden;padding:4px 0;}

.page-toc{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
          "Helvetica Neue",Arial,sans-serif;
  font-size:.82rem;line-height:1.45;}
.page-toc-title{font-size:.66rem;text-transform:uppercase;
  letter-spacing:.16em;color:var(--ink-subtle);font-weight:700;margin:0 0 10px;}
.page-toc ul{list-style:none;padding:0;margin:0;}
.page-toc ul ul{padding-left:12px;margin-left:4px;border-left:1px solid var(--rule);}
.page-toc li{margin:0;}
.page-toc a{display:block;padding:5px 8px;margin:1px 0;border-radius:4px;
  color:var(--ink-soft);text-decoration:none;cursor:pointer;
  transition:color 120ms ease,background 120ms ease;}
.page-toc a:hover{color:var(--link);background:var(--code-bg);}

@media (max-width:900px){
  html,body{height:auto;overflow:auto;}
  .app{display:block;height:auto;}
  .page-sidebar,.content-pane{height:auto;overflow:visible;}
  .page-sidebar-left,.page-sidebar-right{width:auto;}
  .content-pane{padding:18px 16px 40px;}
  .content{padding:32px 22px 48px;box-shadow:none;border-radius:0;background:transparent;}
}
@media print{
  #progress-bar,.page-sidebar,.side-toggle{display:none !important;}
  html,body{height:auto;overflow:visible;}
  .app{display:block;height:auto;}
  .content-pane{height:auto;overflow:visible;padding:0;background:#fff;}
  .content{max-width:none;margin:0;padding:0;box-shadow:none;border-radius:0;background:#fff;}
  body{background:#fff;font-size:11pt;line-height:1.5;}
  .content a{color:inherit;text-decoration:none;}
}
"""

INDEX_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Study Index - Navigation</title>
<meta name="generator" content="04_FORMAT_TEXT_TO_HTML.py">
<link rel="stylesheet" href="./02_NAV_STYLE.css">
<script>
  window.NAV_SHOW_ALL_OPEN = true;
  (function () {
    var v = 'v=' + Date.now() + '_' + Math.floor(Math.random() * 1e9);
    var urls = ['./nav_data.js?' + v, './02_NAV_SCRIPT.js?' + v];
    for (var i = 0; i < urls.length; i++) {
      var s = document.createElement('script');
      s.src = urls[i];
      s.async = false;
      document.head.appendChild(s);
    }
  })();
</script>
<style>
  :root {
    --ix-ink:#1a1a1a; --ix-ink-subtle:#6b6b6b;
    --ix-navy:#1a2e4a; --ix-rule:#e7e7e5;
    --ix-bg:#f7f7f5; --ix-card:#ffffff;
    --ix-shadow:0 1px 3px rgba(0,0,0,.05),0 6px 20px rgba(0,0,0,.05);
    --ix-font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
              "Helvetica Neue",Arial,sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --ix-ink:#e8e8e6; --ix-ink-subtle:#8a8a88;
      --ix-navy:#8fb0d4; --ix-rule:#2a2e35;
      --ix-bg:#101216; --ix-card:#16181c;
      --ix-shadow:0 1px 3px rgba(0,0,0,.4),0 6px 20px rgba(0,0,0,.3);
    }
  }
  *{box-sizing:border-box;}
  html,body{height:100%;margin:0;}
  body{
    background:var(--ix-bg);color:var(--ix-ink);
    font-family:var(--ix-font);font-size:14px;line-height:1.5;
  }
  *{scrollbar-width:thin;scrollbar-color:#d0d0ce transparent;}
  @media (prefers-color-scheme: dark){*{scrollbar-color:#3a3f48 transparent;}}
  ::-webkit-scrollbar{width:10px;height:10px;}
  ::-webkit-scrollbar-track{background:transparent;}
  ::-webkit-scrollbar-thumb{
    background-color:#d0d0ce;border-radius:6px;
    border:2px solid transparent;background-clip:padding-box;
  }
  @media (prefers-color-scheme: dark){::-webkit-scrollbar-thumb{background-color:#3a3f48;}}
  .ix-shell{
    max-width:1000px;margin:0 auto;
    padding:44px 40px 80px;min-height:100vh;
    display:flex;flex-direction:column;
  }
  .ix-header{
    flex:0 0 auto;padding:0 0 22px;
    border-bottom:2px solid var(--ix-rule);margin-bottom:24px;
  }
  .ix-header h1{
    margin:0 0 6px;font-size:1.65rem;font-weight:700;
    letter-spacing:-.02em;color:var(--ix-navy);
  }
  .ix-header p{
    margin:0;font-size:.82rem;color:var(--ix-ink-subtle);letter-spacing:.01em;
  }
  .ix-card{
    flex:1 1 auto;background:var(--ix-card);border-radius:8px;
    box-shadow:var(--ix-shadow);padding:24px 28px 32px;
  }
  #global-nav{font-size:.92rem;}
  #global-nav .gnav{padding:0;}
  #global-nav a.gnav-file{padding:6px 10px;}
  #global-nav details > summary{padding:6px 8px;}
</style>
</head>
<body>
  <div class="ix-shell">
    <header class="ix-header">
      <h1>Study Index</h1>
      <p>All HTML files generated from the Excel master table</p>
    </header>
    <main class="ix-card">
      <div id="global-nav"></div>
    </main>
  </div>
</body>
</html>
"""


def write_html_index():
    """Write the global index page once. Never overwrites."""
    if os.path.isfile(HTML_INDEX_FILE):
        log(f"  index present: {HTML_INDEX_FILE}")
        return
    try:
        with open(HTML_INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(INDEX_HTML_TEMPLATE)
        log(f"  index created: {HTML_INDEX_FILE}")
    except Exception as e:
        log(f"WARNING: could not write index: {e}")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<meta name="generator" content="04_FORMAT_TEXT_TO_HTML.py">

<link rel="stylesheet" href="{{NAV_REL}}/02_NAV_STYLE.css">
<script>
(function () {
  var base = "{{NAV_REL}}";
  var v = 'v=' + Date.now() + '_' + Math.floor(Math.random() * 1e9);
  var urls = [
    base + '/nav_data.js?' + v,
    base + '/02_NAV_SCRIPT.js?' + v
  ];
  for (var i = 0; i < urls.length; i++) {
    var s = document.createElement('script');
    s.src = urls[i];
    s.async = false;                 /* keeps insertion order */
    document.head.appendChild(s);
  }
})();
</script>

<script>
  window.MathJax = {
    tex: {
      inlineMath:  [['\\(', '\\)']],
      displayMath: [['\\[', '\\]']],
      processEscapes: true,
      tags: 'none'
    },
    options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] },
    chtml: { scale: 1.0, displayAlign: 'center' }
  };
</script>
<script id="MathJax-script" async
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
{{CSS}}
</style>
</head>
<body>
<div id="progress-bar"></div>

<div class="app">

  <aside class="page-sidebar page-sidebar-left" id="page-sidebar-left">
    <div class="page-sidebar-header">
      <div class="page-sidebar-header-text">
        <h1 class="page-sidebar-title">{{TITLE}}</h1>
        <p class="page-sidebar-sub">Contents</p>
      </div>
    </div>
    <div class="page-sidebar-scroll">
      <nav class="page-toc" id="page-toc" aria-label="Table of contents">
        <div class="page-toc-title">Contents</div>
        {{TOC}}
      </nav>
    </div>
  </aside>

  <main class="content-pane" id="content-pane">
    <article class="content">{{BODY}}</article>
  </main>

  <aside class="page-sidebar page-sidebar-right" id="page-sidebar-right">
    <div class="page-sidebar-header">
      <div class="page-sidebar-header-text">
        <h1 class="page-sidebar-title">Navigation</h1>
        <p class="page-sidebar-sub">Study Index</p>
      </div>
      <a class="gonav-btn" href="{{NAV_REL}}/03_HTML_INDEX.html">Index</a>
    </div>
    <div class="page-sidebar-scroll">
      <div id="global-nav"></div>
    </div>
  </aside>

</div>

<button class="side-toggle side-toggle-left"  id="side-toggle-left"  aria-label="Toggle contents">&#8249;</button>
<button class="side-toggle side-toggle-right" id="side-toggle-right" aria-label="Toggle navigation">&#8250;</button>

</body>
</html>
"""


# ==================================================================
#  Build page
# ==================================================================
def _count_words(html_text):
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = _html.unescape(text)
    return len(re.findall(r'\S+', text))


def compute_nav_rel(out_dir):
    try:
        rel = os.path.relpath(os.path.abspath(PLAN_DIR),
                              os.path.abspath(out_dir))
    except ValueError:
        return "."
    return rel.replace("\\", "/")


def build_html(md_text, out_dir, base_name, nav_rel):
    md_text = clean_markdown(md_text)
    title, md_text = split_first_h1(md_text)
    if not title:
        title = base_name or "Formatted Notes"

    assets_dir = Path(out_dir) / f"{base_name}_assets"
    rel_prefix = assets_dir.name
    md_text, stats = process_images(md_text, assets_dir, rel_prefix)
    log(f"  images: {stats['downloaded']} downloaded, "
        f"{stats['reused']} reused, {stats['failed']} failed")

    md_text, math_store = extract_math(md_text)
    log(f"  math:   {len(math_store)} equation(s)")

    md = markdown.Markdown(extensions=['extra', 'sane_lists', 'toc'])
    body = md.convert(md_text)
    toc_html = md.toc
    m = re.search(r'<div class="toc">(.*?)</div>\s*$', toc_html, re.DOTALL)
    if m:
        toc_html = m.group(1).strip()
    toc_html = toc_html or '<p style="color:var(--ink-subtle);font-size:.8rem;">(no headings)</p>'

    body = restore_math(body, math_store)
    body = body.replace('<img ', '<img loading="lazy" decoding="async" ')

    words   = _count_words(body)
    minutes = max(1, round(words / 220))
    reading = f" · {words:,} words · ~{minutes} min read"
    timestamp = datetime.now().strftime("%d %b %Y, %H:%M")

    page = (HTML_TEMPLATE
            .replace("{{TITLE}}",     _html.escape(title))
            .replace("{{TIMESTAMP}}", _html.escape(timestamp))
            .replace("{{READING}}",   reading)
            .replace("{{CSS}}",       CSS_MAIN)
            .replace("{{BODY}}",      body)
            .replace("{{TOC}}",       toc_html)
            .replace("{{NAV_REL}}",   nav_rel))
    return page, assets_dir, stats, title


# ==================================================================
#  Main
# ==================================================================
def main():
    log_reset()
    log("=" * 68)
    log("04_FORMAT_TEXT_TO_HTML.py")
    log(f"python    : {sys.executable}")
    log(f"cwd       : {os.getcwd()}")
    log(f"script    : {os.path.abspath(__file__)}")
    log(f"command   : {' '.join(sys.argv)}")
    log("")

    # dependency check
    if pyperclip is None:
        log("ERROR: pyperclip not installed (pip install pyperclip)")
        return 2
    if markdown is None:
        log("ERROR: markdown not installed (pip install markdown)")
        return 3

    try:
        out_dir_str, base_name = resolve_args()
    except Exception:
        log_exc("FATAL: argument resolution crashed")
        return 90

    out_dir = os.path.normpath(out_dir_str)
    log("")
    log(f"out_dir   : {out_dir}")
    log(f"base_name : {base_name}")

    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        log(f"FATAL: cannot create out_dir: {e}")
        return 91

    out_path = os.path.join(out_dir, base_name + ".html")

    log("")
    log("Static nav assets:")
    try:
        ensure_static_nav_assets()
    except Exception:
        log_exc("WARNING: static nav asset step crashed (continuing)")

    log("")
    log("Nav data from Excel:")
    try:
        nav_data = build_nav_data()
        write_nav_data(nav_data)
    except Exception:
        log_exc("WARNING: nav data step crashed (continuing without nav)")

    log("")
    log("Global index:")
    try:
        write_html_index()
    except Exception:
        log_exc("WARNING: index step crashed (continuing)")


    nav_rel = compute_nav_rel(out_dir)
    log(f"  relative path to 00_PLAN: {nav_rel}")

    log("")
    try:
        text = pyperclip.paste()
    except Exception as e:
        log(f"ERROR: clipboard read failed: {e}")
        return 4
    if not text or not text.strip():
        log("ERROR: clipboard is empty.")
        return 4
    log(f"clipboard : {len(text)} characters")

    log("")
    log(f"Building HTML -> {out_path}")
    try:
        page, assets_dir, stats, title = build_html(text, out_dir, base_name, nav_rel)
    except Exception:
        log_exc("FATAL: HTML build crashed")
        return 5

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
    except Exception as e:
        log(f"FATAL: could not save HTML: {e}")
        return 6

    if not os.path.isfile(out_path):
        log("FATAL: output file was not created.")
        return 7

    try:
        if os.path.isdir(assets_dir) and not os.listdir(assets_dir):
            os.rmdir(assets_dir)
    except Exception:
        pass

    log("")
    log(f"OK -> {out_path}")
    log(f"HTML size: {os.path.getsize(out_path)} bytes")
    log("=" * 68)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except SystemExit:
        raise
    except Exception:
        try:
            log_reset()
        except Exception:
            pass
        log_exc("FATAL: unhandled exception in __main__")
        code = 99
    sys.exit(code)