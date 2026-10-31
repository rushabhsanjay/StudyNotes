#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07_ENHANCE_PAGE_STYLING.py

Upgrades 02_NAV_STYLE.css and 02_NAV_SCRIPT.js in 00_PLAN to make every HTML study
page significantly more attractive, interactive, and clear:
  1. Process Step Flows: Transforms 'A → B → C' lines into interactive pipeline badges.
  2. Callout Cards: Distinct visual containers for 'Important distinctions', 'Examples',
     'Case studies', 'Advantages / Disadvantages', and 'Core Terminology'.
  3. Ordered List Hierarchy: Polished circular counter badges for sequential steps.
  4. Interactive Tables: Sticky headers, dynamic table row search, row count, and TSV copy.
  5. Diagram & Code Panels: Top action toolbar with Diagram/Logic tags, copy & expand buttons.
  6. Floating Action Dock: Reading progress % badge, Zen/Focus mode toggle, theme switcher,
     and back-to-top.
  7. In-Page TOC Search: Real-time heading filter in the left sidebar.
  8. Keyboard Shortcuts: [ / ] for Prev/Next topics, Z for Zen focus, T for theme, ? for help.
  9. Preserves NAV_STYLE_V2 / NAV_SCRIPT_V2 markers and all existing functionality.

Safe & non-destructive: creates backups before writing.
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Paths
DEFAULT_ROOT = r"D:\03_STUDY_FOR_CAREER"
DEFAULT_PLAN = os.path.join(DEFAULT_ROOT, "00_PLAN")

def resolve_plan_dir():
    # 1. From CLI arg
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        return os.path.abspath(sys.argv[1])
    # 2. DEFAULT_PLAN if exists
    if os.path.isdir(DEFAULT_PLAN):
        return DEFAULT_PLAN
    # 3. Check current working dir
    cwd = Path.cwd()
    if (cwd / "02_NAV_STYLE.css").is_file():
        return str(cwd)
    if (cwd / "00_PLAN" / "02_NAV_STYLE.css").is_file():
        return str(cwd / "00_PLAN")
    return DEFAULT_PLAN


# =====================================================================
#  UPGRADED CSS CONTENT (Preserves markers & enhances visual hierarchy)
# =====================================================================
UPGRADED_NAV_CSS = r"""/* 02_NAV_STYLE.css
   NAV_STYLE_V2  (marker: do not remove)
   V5 look: "Precision Industrial Engineering & Modern Technical Reader"
   - Distinct process flow diagrams (A → B → C pipelines)
   - Specialized callout cards (Examples, Case Studies, Distinctions, Principles)
   - Sticky-header tables with search/filter & copy support
   - Polished schematics & logic code panels with action headers
   - Refined ordered checklists and step-by-step procedure badges
   - Dynamic Floating Dock: Progress %, Zen Focus Mode, Theme Toggle, Back-to-Top
   - Left TOC quick filter & smooth scroll-spy
   - Prev/Next navigation cards with keyboard hints
   - Full dark & light mode support with high legibility
   Static. Loaded by every generated HTML. */

@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..600&display=swap');

:root {
  --nv-ink:          #14202d;
  --nv-ink-soft:     #3f4f60;
  --nv-ink-subtle:   #667587;
  --nv-navy:         #123763;
  --nv-link:         #1b58a8;
  --nv-paper:        #ffffff;     /* sidebars, panels, cards */
  --nv-canvas:       #f4f6f9;     /* reading surface */
  --nv-rule:         #d9dfe7;
  --nv-rule-subtle:  #edf1f6;
  --nv-hover:        #edf1f6;
  --nv-current:      #e6eef9;
  --nv-current-fg:   #123763;
  --nv-deep:         #123763;     /* hero / key panels */
  --nv-amber:        #e39a00;
  --nv-amber-soft:   rgba(227,154,0,.16);
  --nv-teal:         #0b8f7f;
  --nv-teal-soft:    rgba(11,143,127,.12);
  --nv-teal-deep:    #0b6f63;
  --nv-red:          #c8372d;
  --nv-red-soft:     rgba(200,55,45,.12);
  --nv-tint:         #fff8e8;
  --nv-grid:         rgba(18,55,99,.07);
  --nv-shadow:       0 1px 3px rgba(18,32,45,.08), 0 6px 18px rgba(18,32,45,.06);
  --nv-shadow-lg:    0 10px 28px rgba(18,32,45,.12), 0 2px 6px rgba(18,32,45,.08);
  --nv-font:  "IBM Plex Sans Condensed", "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto,
              "Helvetica Neue", Arial, sans-serif;
  --nv-serif: "Source Serif 4", "Iowan Old Style", Georgia, "Times New Roman", serif;
  --nv-mono:  "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  color-scheme: light;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --nv-ink:          #e4ebf2;
    --nv-ink-soft:     #b3c0ce;
    --nv-ink-subtle:   #8493a3;
    --nv-navy:         #9cc4f7;
    --nv-link:         #7db3f5;
    --nv-paper:        #101820;
    --nv-canvas:       #0c131b;
    --nv-rule:         #233242;
    --nv-rule-subtle:  #18232e;
    --nv-hover:        #182532;
    --nv-current:      #1a2b3f;
    --nv-current-fg:   #9cc4f7;
    --nv-deep:         #0f2745;
    --nv-amber:        #ffc24a;
    --nv-amber-soft:   rgba(255,194,74,.2);
    --nv-teal:         #38d3bd;
    --nv-teal-soft:    rgba(56,211,189,.15);
    --nv-teal-deep:    #0e6f63;
    --nv-red:          #ff7b6e;
    --nv-red-soft:     rgba(255,123,110,.18);
    --nv-tint:         #241f10;
    --nv-grid:         rgba(125,179,245,.09);
    --nv-shadow:       0 1px 3px rgba(0,0,0,.45), 0 6px 18px rgba(0,0,0,.35);
    --nv-shadow-lg:    0 10px 28px rgba(0,0,0,.55), 0 2px 6px rgba(0,0,0,.4);
    color-scheme: dark;
  }
}

:root[data-theme="dark"] {
  --nv-ink:          #e4ebf2;
  --nv-ink-soft:     #b3c0ce;
  --nv-ink-subtle:   #8493a3;
  --nv-navy:         #9cc4f7;
  --nv-link:         #7db3f5;
  --nv-paper:        #101820;
  --nv-canvas:       #0c131b;
  --nv-rule:         #233242;
  --nv-rule-subtle:  #18232e;
  --nv-hover:        #182532;
  --nv-current:      #1a2b3f;
  --nv-current-fg:   #9cc4f7;
  --nv-deep:         #0f2745;
  --nv-amber:        #ffc24a;
  --nv-amber-soft:   rgba(255,194,74,.2);
  --nv-teal:         #38d3bd;
  --nv-teal-soft:    rgba(56,211,189,.15);
  --nv-teal-deep:    #0e6f63;
  --nv-red:          #ff7b6e;
  --nv-red-soft:     rgba(255,123,110,.18);
  --nv-tint:         #241f10;
  --nv-grid:         rgba(125,179,245,.09);
  --nv-shadow:       0 1px 3px rgba(0,0,0,.45), 0 6px 18px rgba(0,0,0,.35);
  --nv-shadow-lg:    0 10px 28px rgba(0,0,0,.55), 0 2px 6px rgba(0,0,0,.4);
  color-scheme: dark;
}

/* keyboard focus everywhere */
a:focus-visible, button:focus-visible, summary:focus-visible, input:focus-visible {
  outline: 2px solid var(--nv-amber);
  outline-offset: 2px;
}

/* --- sidebar chrome --- */
.gnav {
  font-family: var(--nv-font);
  font-size: 0.86rem;
  line-height: 1.4;
  color: var(--nv-ink-soft);
  padding: 4px 0;
}
.gnav .gnav-empty {
  padding: 8px 2px;
  font-style: italic;
  color: var(--nv-ink-subtle);
}
.gnav ul { list-style: none; padding-left: 14px; margin: 0; }
.gnav > ul { padding-left: 0; }
.gnav li { margin: 1px 0; }
.gnav li[hidden] { display: none; }
.gnav .nn {
  font-family: var(--nv-mono);
  font-size: .7em;
  color: var(--nv-ink-subtle);
  margin-right: .55em;
  font-variant-numeric: tabular-nums;
}

.gnav details > summary {
  cursor: pointer;
  list-style: none;
  padding: 5px 6px;
  border-radius: 6px;
  color: var(--nv-ink);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 5px;
  user-select: none;
  transition: background 120ms ease, color 120ms ease;
}
.gnav details > summary::-webkit-details-marker { display: none; }
.gnav details > summary::before {
  content: "\25B8";
  display: inline-block;
  width: 10px;
  font-size: 0.9em;
  color: var(--nv-amber);
  transition: transform 140ms ease;
}
.gnav details[open] > summary::before { transform: rotate(90deg); }
.gnav details > summary:hover {
  background: var(--nv-hover);
  color: var(--nv-link);
}
.gnav .gnav-folder-name {
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.gnav a.gnav-file,
.gnav span.gnav-file {
  display: block;
  padding: 5px 8px;
  margin: 1px 0;
  border-radius: 6px;
  border-left: 3px solid transparent;
  color: var(--nv-ink-soft);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 120ms ease, color 120ms ease;
}
.gnav a.gnav-file:hover {
  color: var(--nv-link);
  background: var(--nv-hover);
}
.gnav span.gnav-file.is-current {
  color: var(--nv-current-fg);
  font-weight: 600;
  background: var(--nv-current);
  border-left-color: var(--nv-amber);
  cursor: default;
}

.gnav-search-wrap { padding: 0 0 8px; }
.gnav-search {
  width: 100%;
  box-sizing: border-box;
  font: 400 .84rem var(--nv-font);
  color: var(--nv-ink);
  background: var(--nv-canvas);
  border: 1px solid var(--nv-rule);
  border-radius: 8px;
  padding: 7px 10px;
  transition: border-color 140ms ease;
}
.gnav-search:focus {
  border-color: var(--nv-link);
  outline: none;
}
.gnav-search::placeholder { color: var(--nv-ink-subtle); }

/* --- page TOC (left sidebar, scroll-spy) --- */
.page-toc { font-family: var(--nv-font); font-size: .86rem; line-height: 1.35; }
.toc-filter-wrap { padding: 0 0 10px; margin-bottom: 8px; border-bottom: 1px solid var(--nv-rule); }
.toc-filter-input {
  width: 100%; box-sizing: border-box;
  font: 400 .78rem var(--nv-font); color: var(--nv-ink);
  background: var(--nv-canvas); border: 1px solid var(--nv-rule);
  border-radius: 6px; padding: 5px 8px;
}
.toc-filter-input::placeholder { color: var(--nv-ink-subtle); }
.page-toc ul { list-style: none; margin: 0; padding-left: 12px; }
.page-toc > ul, .page-toc > nav > ul { padding-left: 0; }
.page-toc li { margin: 1px 0; }
.page-toc li[hidden] { display: none; }
.page-toc a {
  display: block;
  padding: 4px 10px;
  border-left: 2px solid transparent;
  border-radius: 0 6px 6px 0;
  color: var(--nv-ink-soft);
  text-decoration: none;
  transition: background 120ms ease, color 120ms ease, border-color 120ms ease;
}
.page-toc a:hover { background: var(--nv-hover); color: var(--nv-link); }
.page-toc a.is-active {
  color: var(--nv-current-fg);
  background: var(--nv-current);
  border-left-color: var(--nv-amber);
  font-weight: 600;
}

/* --- side toggle buttons --- */
.side-toggle {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 46px;
  background: var(--nv-paper);
  color: var(--nv-ink-soft);
  border: 1px solid var(--nv-rule);
  border-radius: 6px;
  padding: 0;
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 150ms ease, color 150ms ease, opacity 150ms ease;
}
.side-toggle:hover {
  background: var(--nv-hover);
  color: var(--nv-link);
}
.side-toggle-left  { left: 6px; }
.side-toggle-right { right: 6px; }

/* --- sidebar shell --- */
.page-sidebar {
  background: var(--nv-paper);
  transition: width 200ms ease, opacity 180ms ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.page-sidebar.is-collapsed {
  width: 0 !important;
  opacity: 0;
  pointer-events: none;
}

/* --- sidebar header: title on the left, button on the top-right --- */
.page-sidebar .page-sidebar-header {
  flex: 0 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 16px 14px 12px 18px;
  border-bottom: 1px solid var(--nv-rule);
}
.page-sidebar .page-sidebar-header > .page-sidebar-header-text {
  min-width: 0;
  flex: 1 1 auto;
}
.page-sidebar .page-sidebar-scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 14px 20px 24px;
}
.page-sidebar .page-sidebar-title {
  font-family: var(--nv-font);
  font-size: 1rem;
  font-weight: 700;
  color: var(--nv-navy);
  margin: 0 0 4px;
  line-height: 1.25;
  letter-spacing: -0.005em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.page-sidebar .page-sidebar-sub {
  font-family: var(--nv-font);
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  color: var(--nv-ink-subtle);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --- go to nav button (top-right, compact) --- */
.gonav-btn {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  background: var(--nv-deep);
  color: #ffffff !important;
  border: 1px solid var(--nv-deep);
  border-radius: 6px;
  text-decoration: none !important;
  font-family: var(--nv-font);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: background 140ms ease, box-shadow 140ms ease, transform 100ms ease;
  white-space: nowrap;
}
.gonav-btn::before {
  content: "";
  display: inline-block;
  width: 9px;
  height: 9px;
  background: currentColor;
  -webkit-mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><path d='M2 3h5v5H2zM9 3h5v5H9zM2 9h5v5H2zM9 9h5v5H9z'/></svg>") center / contain no-repeat;
          mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><path d='M2 3h5v5H2zM9 3h5v5H9zM2 9h5v5H2zM9 9h5v5H9z'/></svg>") center / contain no-repeat;
  opacity: 0.9;
}
.gonav-btn:hover {
  background: var(--nv-link);
  border-color: var(--nv-link);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
  color: #ffffff !important;
  text-decoration: none !important;
}
.gonav-btn:active { transform: translateY(0); box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1); }

@media (max-width: 900px) {
  .side-toggle { display: none; }
  .page-sidebar { width: auto !important; opacity: 1 !important; }
  .page-sidebar .page-sidebar-scroll { overflow: visible; }
}

/* NAV_STYLE_PN_V1 : previous / next bars (appended by fix_site.py) */
.pn-bar {
  display: flex; align-items: stretch; justify-content: space-between; gap: 12px;
  font-family: var(--nv-font);
}
.pn-top    { margin: 0 0 24px; padding-bottom: 14px; border-bottom: 1px solid var(--nv-rule); }
.pn-bottom { margin: 36px 0 12px; padding-top: 18px;  border-top: 1px solid var(--nv-rule); }
.pn-btn {
  flex: 0 1 42%; min-width: 0; display: flex; flex-direction: column; gap: 3px;
  padding: 10px 16px; border: 1px solid var(--nv-rule); border-radius: 9px;
  background: var(--nv-paper); color: var(--nv-link) !important; text-decoration: none !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
  transition: background 140ms ease, border-color 140ms ease, transform 120ms ease, box-shadow 140ms ease;
}
.pn-next { text-align: right; margin-left: auto; }
a.pn-btn:hover {
  background: var(--nv-hover); border-color: var(--nv-link);
  transform: translateY(-1px); box-shadow: 0 3px 10px rgba(0,0,0,.08);
}
.pn-prev { border-left: 3px solid var(--nv-amber); }
.pn-next { border-right: 3px solid var(--nv-amber); }
.pn-lbl {
  font-size: .72rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
  color: var(--nv-ink-subtle); display: flex; align-items: center; gap: 5px;
}
.pn-next .pn-lbl { justify-content: flex-end; }
.pn-title { font-size: .92rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--nv-navy); }
.pn-disabled { opacity: .35; pointer-events: none; }
.pn-pos {
  align-self: center; font: 600 .75rem var(--nv-mono); color: var(--nv-ink-subtle);
  background: var(--nv-paper); border: 1px solid var(--nv-rule); padding: 4px 10px;
  border-radius: 6px; white-space: nowrap;
}
.gnav .gnav-missing { display: block; padding: 5px 8px; opacity: .45; cursor: default;
  font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
@media (max-width: 600px) { .pn-title { display: none; } .pn-btn { flex-basis: auto; } }

/* =====================================================================
   NAV_STYLE_V4_READING : the reading surface
   ===================================================================== */
body #progress-bar {
  position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 90;
  transform-origin: 0 50%; transform: scaleX(0); pointer-events: none;
  background: linear-gradient(90deg, var(--nv-link), var(--nv-amber));
}
html, body { background: var(--nv-canvas); }
body #content-pane, body .content-pane { background: var(--nv-canvas); color: var(--nv-ink); }

body .content, body .doc { background: transparent; box-shadow: none; border: 0; }

body .doc {
  --pad: 54px;
  position: relative;
  max-width: 920px;
  margin-inline: auto;
  padding: 28px 8px 50px calc(var(--pad) + 8px);
  font-family: var(--nv-serif);
  font-size: 1.12rem;
  line-height: 1.74;
  color: var(--nv-ink);
  font-feature-settings: "kern", "liga", "onum";
  transition: max-width 220ms ease;
}
body .doc p { margin: .9em 0; text-align: left; max-width: 68ch; }
body .doc a { color: var(--nv-link); text-underline-offset: 3px; text-decoration-thickness: 1px; }
body .doc strong { font-weight: 650; color: var(--nv-ink); }
body .doc ul { padding-left: 1.4rem; margin: .85em 0; }
body .doc li { margin: .35em 0; }
body .doc li::marker { color: var(--nv-amber); }
body .doc hr { border: 0; height: 0; margin: 0; }

/* ---- hero ---- */
body .doc .doc-hero {
  position: relative;
  overflow: hidden;
  margin: 0 0 28px calc(var(--pad) * -1);
  padding: 32px 36px 36px;
  border-radius: 14px;
  color: #eef4fb;
  background:
    linear-gradient(rgba(255,255,255,.055) 1px, transparent 1px) 0 0 / 28px 28px,
    linear-gradient(90deg, rgba(255,255,255,.055) 1px, transparent 1px) 0 0 / 28px 28px,
    linear-gradient(135deg, var(--nv-deep) 0%, #0b2140 100%);
  box-shadow: var(--nv-shadow-lg);
}
body .doc .doc-hero::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 4px;
  background:
    linear-gradient(90deg, transparent, #ffc24a 50%, transparent) -40% 0 / 35% 100% no-repeat,
    rgba(255,194,74,.3);
  animation: doc-sweep 2.6s cubic-bezier(.55,0,.2,1) .25s 1 forwards;
}
@keyframes doc-sweep { to { background-position: 140% 0, 0 0; } }
body .doc .doc-crumbs {
  display: flex; flex-wrap: wrap; gap: 4px 0;
  font: 500 .8rem var(--nv-font); color: #a9bdd4; margin-bottom: 14px;
}
body .doc .doc-crumbs span + span::before { content: "/"; margin: 0 .6em; opacity: .5; }
body .doc .doc-hero h1 {
  margin: 0; padding: 0; border: 0; background: none;
  font: 700 clamp(2.2rem, 5.2vw, 3.5rem)/1.04 var(--nv-font);
  letter-spacing: -.015em; color: #fff;
}
body .doc .doc-hero-sub {
  margin: 12px 0 0; max-width: 52ch; font: italic 400 1.15rem/1.5 var(--nv-serif); color: #cfddee;
}
body .doc .doc-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }
body .doc .doc-chip {
  font: 400 .8rem var(--nv-font); color: #dbe7f4;
  padding: 5px 11px; border: 1px solid rgba(255,255,255,.22); border-radius: 5px;
  background: rgba(255,255,255,.06);
}
body .doc .doc-chip b { font: 700 .86rem var(--nv-mono); color: #ffc24a; margin-right: 2px; }
body .doc .pn-top { margin: 0 0 26px; padding-bottom: 0; border-bottom: 0; }

/* ---- ladder: rail + numbered rungs ---- */
body .doc .sec-wrap { position: relative; padding: 1.6rem 0 1.8rem; }
body .doc .sec-wrap::before {
  content: ""; position: absolute; top: 0; bottom: 0;
  left: calc(var(--pad) * -1 + 14px); width: 2px; background: var(--nv-rule);
}
body .doc h1.sec, body .doc h2.sec {
  position: relative; display: flex; align-items: center; gap: 16px;
  min-height: 34px; margin: 0 0 1rem; padding: 0; border: 0; background: none;
  font: 700 1.65rem/1.2 var(--nv-font); letter-spacing: -.005em; color: var(--nv-navy);
  scroll-margin-top: 24px;
}
body .doc .sec::after {
  content: ""; flex: 1 1 28px; min-width: 28px; height: 2px; border-radius: 2px; background: var(--nv-rule);
}
body .doc .sec-title { min-width: 0; }
body .doc .sec-num {
  position: absolute; left: calc(var(--pad) * -1); top: 50%; transform: translateY(-50%);
  width: 30px; height: 30px; border-radius: 50%; z-index: 1;
  display: grid; place-items: center;
  background: var(--nv-canvas); border: 2px solid var(--nv-amber); color: var(--nv-ink);
  font: 600 .72rem/1 var(--nv-mono); font-variant-numeric: tabular-nums;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
body .doc .sec--plain::before {
  content: ""; position: absolute; left: calc(var(--pad) * -1 + 8px); top: 50%;
  width: 14px; height: 14px; margin-top: -7px; border-radius: 50%; background: var(--nv-amber);
}
body .doc .sec-wrap:first-of-type::before { top: 1.6rem; }
body .doc .sec-wrap:last-of-type::before { bottom: auto; height: calc(1.6rem + 17px); }

body .doc h3 {
  margin: 2.2rem 0 .7rem; padding: 4px 0 4px .9rem;
  font: 600 1.22rem/1.3 var(--nv-font); color: var(--nv-navy);
  border: 0; border-left: 3px solid var(--nv-amber); scroll-margin-top: 24px;
}
body .doc h4 {
  margin: 1.6rem 0 .5rem; font: 600 1.05rem var(--nv-font); color: var(--nv-ink-soft);
  letter-spacing: .02em; text-transform: uppercase;
}

/* =====================================================================
   NEW V5 ENHANCEMENTS: Process Flows, Callout Cards, Step Procedures
   ===================================================================== */

/* ---- 1. Interactive Step Flow Diagrams (A → B → C) ---- */
.doc-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin: 1.6rem 0;
  padding: 14px 18px;
  background: var(--nv-paper);
  border: 1px solid var(--nv-rule);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(18,32,45,.06);
  position: relative;
  overflow-x: auto;
}
.doc-flow-step {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  background: var(--nv-hover);
  border: 1px solid var(--nv-rule);
  border-radius: 8px;
  font: 600 .88rem/1.2 var(--nv-font);
  color: var(--nv-navy);
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
  transition: transform 140ms ease, background 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
  cursor: default;
}
.doc-flow-step:hover {
  background: var(--nv-current);
  border-color: var(--nv-amber);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(0,0,0,.09);
}
.doc-flow-num {
  font: 700 .72rem/1 var(--nv-mono);
  color: var(--nv-amber);
  background: var(--nv-canvas);
  border: 1px solid var(--nv-rule);
  border-radius: 4px;
  padding: 2px 6px;
}
.doc-flow-sep {
  display: inline-flex;
  align-items: center;
  color: var(--nv-amber);
  font-weight: 700;
  font-size: 1.15rem;
  padding: 0 2px;
  user-select: none;
}

/* ---- 2. Distinct Semantic Callout Boxes ---- */
.doc-callout {
  margin: 1.6rem 0;
  border-radius: 10px;
  border: 1px solid var(--nv-rule);
  background: var(--nv-paper);
  overflow: hidden;
  box-shadow: var(--nv-shadow);
  transition: border-color 140ms ease, box-shadow 140ms ease;
}
.doc-callout-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font: 700 .76rem/1 var(--nv-font);
  letter-spacing: .08em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--nv-rule);
}
.doc-callout-icon { font-size: 1rem; line-height: 1; }
.doc-callout-body {
  padding: 14px 18px;
  font-size: 1.05rem;
  line-height: 1.68;
}
.doc-callout-body > :first-child { margin-top: 0; }
.doc-callout-body > :last-child { margin-bottom: 0; }

/* Distinction (important distinction / note / warning) */
.doc-callout-distinction {
  border-left: 4px solid var(--nv-amber);
}
.doc-callout-distinction .doc-callout-header {
  background: var(--nv-amber-soft);
  color: var(--nv-ink);
  border-bottom-color: rgba(227,154,0,.25);
}
.doc-callout-distinction .doc-callout-body {
  background: rgba(227,154,0,.03);
}

/* Example / Case study */
.doc-callout-example {
  border-left: 4px solid var(--nv-link);
}
.doc-callout-example .doc-callout-header {
  background: rgba(27,88,168,.08);
  color: var(--nv-navy);
  border-bottom-color: rgba(27,88,168,.2);
}
.doc-callout-example .doc-callout-body {
  background: rgba(27,88,168,.02);
}

/* Key Takeaway / Summary */
.doc-callout-summary {
  border-left: 4px solid var(--nv-teal);
}
.doc-callout-summary .doc-callout-header {
  background: var(--nv-teal-soft);
  color: var(--nv-teal-deep);
  border-bottom-color: rgba(11,143,127,.2);
}

/* ---- 3. Ordered Sequential Lists with Number Badges ---- */
body .doc ol {
  counter-reset: doc-counter;
  list-style: none;
  padding-left: 0;
  margin: 1.1rem 0;
}
body .doc ol > li {
  position: relative;
  counter-increment: doc-counter;
  padding-left: 36px;
  margin: .65rem 0;
  line-height: 1.62;
}
body .doc ol > li::before {
  content: counter(doc-counter);
  position: absolute;
  left: 0;
  top: 2px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--nv-hover);
  border: 1.5px solid var(--nv-amber);
  color: var(--nv-navy);
  font: 700 .72rem/1 var(--nv-mono);
  display: grid;
  place-items: center;
  box-shadow: 0 1px 2px rgba(0,0,0,.05);
}

/* List variants */
body .doc ul.list-pros li::marker { color: var(--nv-teal); }
body .doc ul.list-cons li::marker { color: var(--nv-red); }

/* Term badges for terminology lines */
body .doc .term-badge {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 5px;
  background: var(--nv-hover);
  border: 1px solid var(--nv-rule);
  color: var(--nv-navy);
  font-weight: 700;
  font-family: var(--nv-font);
  font-size: .95em;
  margin-right: 6px;
}

/* ---- 4. Interactive Tables & Sticky Header ---- */
body .doc .table-wrap {
  margin: 1.6rem 0; overflow-x: auto;
  border: 1px solid var(--nv-rule); border-radius: 10px; background: var(--nv-paper);
  box-shadow: var(--nv-shadow);
}
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 14px;
  background: var(--nv-hover);
  border-bottom: 1px solid var(--nv-rule);
  font: 500 .8rem var(--nv-font);
}
.table-filter-input {
  flex: 1 1 180px;
  max-width: 240px;
  padding: 4px 10px;
  font: 400 .78rem var(--nv-font);
  color: var(--nv-ink);
  background: var(--nv-paper);
  border: 1px solid var(--nv-rule);
  border-radius: 6px;
}
.table-filter-input::placeholder { color: var(--nv-ink-subtle); }
.table-btn {
  font: 600 .74rem var(--nv-font);
  color: var(--nv-ink-soft);
  background: var(--nv-paper);
  border: 1px solid var(--nv-rule);
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  transition: all 120ms ease;
}
.table-btn:hover { color: var(--nv-link); border-color: var(--nv-link); }
.table-count {
  font: 600 .72rem var(--nv-mono);
  color: var(--nv-ink-subtle);
}
body .doc thead th {
  position: sticky;
  top: 0;
  z-index: 5;
  text-align: left; padding: .8rem 1rem; font-weight: 600; letter-spacing: .01em;
  background: var(--nv-deep); color: #fff; border: 0;
}
body .doc table {
  display: table; width: 100%; min-width: 520px; margin: 0;
  border-collapse: collapse; font: 400 .94rem/1.45 var(--nv-font);
}
body .doc table.cmp th:nth-child(2) { background: var(--nv-teal-deep); }
body .doc td { padding: .65rem 1rem; border: 0; border-top: 1px solid var(--nv-rule); vertical-align: top; }
body .doc tbody tr:nth-child(even) { background: var(--nv-hover); }
body .doc tbody tr:hover { background: var(--nv-current); }
body .doc table.cmp td:first-child  { box-shadow: inset 3px 0 0 var(--nv-link); }
body .doc table.cmp td:nth-child(2) { box-shadow: inset 3px 0 0 var(--nv-teal); }

/* ---- 5. Schematic & Code Panels ---- */
body .doc :not(pre) > code {
  font: 500 .84em var(--nv-mono); color: var(--nv-navy);
  background: var(--nv-hover); border: 1px solid var(--nv-rule);
  padding: .1em .44em; border-radius: 4px; white-space: normal;
}
body .doc blockquote {
  margin: 1.5rem 0; padding: 1.05rem 1.3rem 1.05rem 1.5rem;
  border: 0; border-left: 4px solid var(--nv-amber); border-radius: 0 10px 10px 0;
  background: var(--nv-tint); color: var(--nv-ink);
  font-size: 1.14rem; line-height: 1.6;
}
body .doc blockquote p { margin: .3em 0; max-width: none; }
body .doc .sec-wrap.is-key blockquote {
  background: var(--nv-deep); color: #eef4fb; border-left-color: #ffc24a; box-shadow: var(--nv-shadow);
}
body .doc .sec-wrap.is-key blockquote strong { color: #ffd780; }

.pre-box {
  position: relative; width: fit-content; max-width: 100%; margin: 1.4rem 0;
}
.pre-box pre {
  margin: 0 !important; width: 100%;
}
.pre-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 6px 12px; background: var(--nv-hover);
  border: 1px solid var(--nv-rule); border-bottom: 0; border-radius: 10px 10px 0 0;
}
.pre-box.has-header pre {
  border-top-left-radius: 0; border-top-right-radius: 0;
}
.pre-tag {
  font: 700 .68rem/1 var(--nv-mono); letter-spacing: .06em; text-transform: uppercase;
  color: var(--nv-ink-subtle);
}
.pre-actions {
  display: flex; align-items: center; gap: 6px;
}
.pre-btn {
  font: 600 .72rem/1 var(--nv-font); color: var(--nv-ink-soft);
  background: var(--nv-paper); border: 1px solid var(--nv-rule); border-radius: 5px;
  padding: 3px 8px; cursor: pointer; transition: all 120ms ease;
}
.pre-btn:hover { color: var(--nv-link); border-color: var(--nv-link); }

body .doc pre {
  position: relative; display: block; box-sizing: border-box;
  width: fit-content; min-width: min(100%, 17rem); max-width: 100%;
  padding: 1rem 1.3rem;
  font: 500 .86rem/1.6 var(--nv-mono); color: var(--nv-ink);
  background: var(--nv-paper); border: 1px solid var(--nv-rule); border-radius: 10px;
  overflow-x: auto; tab-size: 4; white-space: pre;
}
body .doc pre code { font: inherit; background: none; border: 0; padding: 0; color: inherit; }
body .doc pre.diagram {
  border-left: 4px solid var(--nv-link);
  background-image:
    linear-gradient(var(--nv-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--nv-grid) 1px, transparent 1px);
  background-size: 18px 18px;
}
body .doc pre.logic { border-left: 4px solid var(--nv-teal); }
body .doc pre.plain { border-left: 4px solid var(--nv-rule); }
body .doc .bx  { color: var(--nv-ink-subtle); }
body .doc .ar  { color: var(--nv-amber); font-weight: 700; }
body .doc .ok  { color: var(--nv-teal); font-weight: 700; }
body .doc .bad { color: var(--nv-red); font-weight: 700; }
body .doc .st, body .doc .kw { color: var(--nv-link); font-weight: 700; }
body .doc .val { color: var(--nv-teal); font-weight: 700; }

/* ---- chip lists ---- */
body .doc ul.chips { display: flex; flex-wrap: wrap; gap: 8px; padding: 0; margin: 1rem 0; list-style: none; }
body .doc ul.chips li {
  margin: 0; padding: 4px 12px; font: 500 .9rem/1.4 var(--nv-font); color: var(--nv-ink-soft);
  background: var(--nv-paper); border: 1px solid var(--nv-rule); border-radius: 6px;
  border-bottom: 2px solid var(--nv-amber);
}

/* ---- Q&A accordions ---- */
body .doc .qa-tools { display: flex; gap: 8px; margin: .6rem 0 .8rem; }
body .doc .qa-tools button {
  font: 600 .78rem var(--nv-font); color: var(--nv-ink-soft); cursor: pointer;
  background: var(--nv-paper); border: 1px solid var(--nv-rule); border-radius: 6px; padding: 5px 11px;
}
body .doc .qa-tools button:hover { color: var(--nv-link); border-color: var(--nv-link); }
body .doc details.qa {
  margin: .55rem 0; background: var(--nv-paper);
  border: 1px solid var(--nv-rule); border-radius: 10px; overflow: hidden;
  transition: border-color 140ms ease;
}
body .doc details.qa[open] { border-color: var(--nv-link); }
body .doc details.qa > summary {
  position: relative; cursor: pointer; list-style: none;
  padding: .9rem 3rem .9rem 1.15rem; font: 600 1rem/1.4 var(--nv-font); color: var(--nv-navy);
}
body .doc details.qa > summary::-webkit-details-marker { display: none; }
body .doc details.qa > summary::after {
  content: "+"; position: absolute; right: 1.1rem; top: 50%; transform: translateY(-50%);
  font: 500 1.3rem var(--nv-mono); color: var(--nv-amber);
}
body .doc details.qa[open] > summary::after { content: "\2212"; }
body .doc details.qa > summary:hover { background: var(--nv-hover); }
body .doc .qa-body { padding: .2rem 1.15rem 1rem; border-top: 1px dashed var(--nv-rule); }
body .doc .qa-body p { max-width: none; }

/* ---- 6. Floating Action Dock (Reading % + Zen mode + Theme + Top) ---- */
#fab-dock {
  position: fixed; right: 18px; bottom: 18px; z-index: 45;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
#fab-dock button {
  width: 42px; height: 42px; display: grid; place-items: center; padding: 0; cursor: pointer;
  color: var(--nv-ink-soft); background: var(--nv-paper);
  border: 1px solid var(--nv-rule); border-radius: 10px; box-shadow: var(--nv-shadow);
  transition: color 120ms ease, border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
}
#fab-dock button:hover {
  color: var(--nv-link); border-color: var(--nv-link); transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(18,32,45,.15);
}
.fab-progress-badge {
  font: 700 .72rem/1 var(--nv-mono);
  color: var(--nv-amber);
  background: var(--nv-paper);
  border: 1px solid var(--nv-rule);
  border-radius: 8px;
  padding: 5px 8px;
  box-shadow: var(--nv-shadow);
  cursor: pointer;
  user-select: none;
  transition: all 120ms ease;
}
.fab-progress-badge:hover {
  border-color: var(--nv-amber);
  transform: scale(1.05);
}

/* Zen / Focus Mode */
body.zen-mode .page-sidebar {
  width: 0 !important; opacity: 0 !important; pointer-events: none !important;
}
body.zen-mode .side-toggle { opacity: .25; }
body.zen-mode .doc { max-width: 980px; }

/* Keyboard Shortcuts Cheat Sheet Modal */
.kb-modal-backdrop {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,.5); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
}
.kb-modal {
  width: min(92vw, 420px);
  background: var(--nv-paper);
  border: 1px solid var(--nv-rule);
  border-radius: 14px;
  box-shadow: var(--nv-shadow-lg);
  overflow: hidden;
  font-family: var(--nv-font);
}
.kb-modal-header {
  padding: 14px 18px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--nv-rule);
  font-weight: 700; font-size: 1rem; color: var(--nv-navy);
}
.kb-modal-close {
  background: none; border: 0; font-size: 1.2rem; cursor: pointer; color: var(--nv-ink-subtle);
}
.kb-modal-body {
  padding: 16px 18px; display: flex; flex-direction: column; gap: 10px;
}
.kb-row {
  display: flex; align-items: center; justify-content: space-between; font-size: .88rem;
}
.kb-key {
  font: 700 .76rem/1 var(--nv-mono);
  background: var(--nv-hover);
  border: 1px solid var(--nv-rule);
  border-radius: 5px;
  padding: 3px 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,.08);
}

/* NAV_STYLE_MOBILE_V1 : phone layout - content first, side panels as drawers */
#sb-backdrop { display: none; }
@media (max-width: 900px) {
  html { -webkit-text-size-adjust: 100%; }
  html body { overflow-x: hidden; }

  /* panels become slide-in drawers (closed by default) */
  body .page-sidebar {
    position: fixed; top: 0; bottom: 0; height: auto;
    width: min(86vw, 340px) !important; opacity: 1 !important; pointer-events: auto;
    z-index: 60; background: var(--nv-paper);
    transition: transform 220ms ease;
  }
  body .page-sidebar-left  { left: 0;  transform: translateX(-105%); }
  body .page-sidebar-right { right: 0; transform: translateX(105%); }
  body .page-sidebar.is-open { transform: none; }
  body .page-sidebar .page-sidebar-scroll { overflow-y: auto !important; -webkit-overflow-scrolling: touch; }

  body.sb-open #sb-backdrop { display: block; position: fixed; inset: 0; z-index: 55;
    background: rgba(0,0,0,.45); }

  /* edge tabs to open / close the drawers */
  body .side-toggle { display: flex !important; width: 30px; height: 56px; z-index: 80; opacity: .9; }
  body .side-toggle-left  { left: 0;  border-left: none;  border-radius: 0 8px 8px 0; }
  body .side-toggle-right { right: 0; border-right: none; border-radius: 8px 0 0 8px; }
  body.sb-left-open  .side-toggle-left  { left: calc(min(86vw, 340px) - 30px); }
  body.sb-right-open .side-toggle-right { right: calc(min(86vw, 340px) - 30px); }

  /* readable content on small screens */
  body .content-pane { padding: 12px 10px 40px; }
  body .content { padding: 20px 12px 36px; }
  .content img { max-width: 100%; height: auto; }
  .content table { display: block; max-width: 100%; overflow-x: auto; }
  .content pre { overflow-x: auto; max-width: 100%; }
  mjx-container[display="true"] { overflow-x: auto; overflow-y: hidden; max-width: 100%; }
  .content p { text-align: left; }

  /* V4 reading surface on phones */
  body .doc { --pad: 36px; font-size: 1.02rem; padding: 14px 2px 32px calc(var(--pad) + 2px); }
  body .doc .doc-hero { padding: 22px 18px 26px; border-radius: 12px; }
  body .doc .doc-hero h1 { font-size: 2.1rem; }
  body .doc h1.sec, body .doc h2.sec { font-size: 1.3rem; gap: 10px; }
  body .doc .sec-num { width: 26px; height: 26px; font-size: .64rem; }
  body .doc .sec-wrap::before { left: calc(var(--pad) * -1 + 12px); }
  body .doc .sec--plain::before { left: calc(var(--pad) * -1 + 6px); }
  body .doc .sec::after { display: none; }
  body .doc table { min-width: 460px; }
  body .doc .doc-chip { font-size: .74rem; }
  #fab-dock { right: 12px; bottom: 12px; }
  #fab-dock button { width: 38px; height: 38px; }
}

/* reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
  body .doc .doc-hero::after { background-position: 0 0, 0 0; }
}

/* print: clean revision sheets */
@media print {
  .page-sidebar, .side-toggle, #fab-dock, #progress-bar, .pn-bar, .qa-tools, .pre-header, #sb-backdrop { display: none !important; }
  html, body, body #content-pane { background: #fff !important; color: #000 !important; overflow: visible !important; height: auto !important; }
  body .doc { max-width: none; padding-left: 0; font-size: 11pt; }
  body .doc .doc-hero { background: #fff; color: #000; border: 1px solid #999; box-shadow: none; margin-left: 0; }
  body .doc .doc-hero h1, body .doc .doc-hero-sub, body .doc .doc-crumbs, body .doc .doc-chip { color: #000; }
  body .doc .sec-wrap::before, body .doc .sec::after, body .doc .sec-num { display: none; }
  body .doc pre, body .doc details.qa, body .doc blockquote { break-inside: avoid; }
  body .doc details.qa > .qa-body { display: block; }
}

/* ===== Edge blur / fade (text blurs in from the bottom, out at the top) ===== */
.edge-fade {
  position: fixed; left: 0; right: 0; height: 72px;
  z-index: 30; pointer-events: none;
  -webkit-backdrop-filter: blur(7px); backdrop-filter: blur(7px);
}
.edge-fade.top {
  top: 0;
  background: linear-gradient(to bottom, var(--nv-canvas) 0%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, #000 0%, transparent 100%);
          mask-image: linear-gradient(to bottom, #000 0%, transparent 100%);
}
.edge-fade.bottom {
  bottom: 0;
  background: linear-gradient(to top, var(--nv-canvas) 0%, transparent 100%);
  -webkit-mask-image: linear-gradient(to top, #000 0%, transparent 100%);
          mask-image: linear-gradient(to top, #000 0%, transparent 100%);
}
@media print { .edge-fade { display: none !important; } }
"""


# =====================================================================
#  UPGRADED JS CONTENT (Preserves markers & enhances interactivity)
# =====================================================================
UPGRADED_NAV_JS = r"""/* 02_NAV_SCRIPT.js
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
"""


# =====================================================================
#  Main runner
# =====================================================================
def main():
    print("=" * 65)
    print("  07_ENHANCE_PAGE_STYLING - Technical Study Page Enhancer")
    print("=" * 65)

    plan_dir = resolve_plan_dir()
    print(f"Target 00_PLAN directory: {plan_dir}")

    if not os.path.isdir(plan_dir):
        print(f"ERROR: Directory '{plan_dir}' does not exist.")
        sys.exit(1)

    css_path = os.path.join(plan_dir, "02_NAV_STYLE.css")
    js_path = os.path.join(plan_dir, "02_NAV_SCRIPT.js")
    backup_dir = os.path.join(plan_dir, "AUTOMATION_BACKUPS")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Back up existing CSS
    if os.path.isfile(css_path):
        bk_css = os.path.join(backup_dir, f"02_NAV_STYLE_backup_{timestamp}.css")
        shutil.copy2(css_path, bk_css)
        print(f"Backed up CSS to: {bk_css}")

    # 2. Back up existing JS
    if os.path.isfile(js_path):
        bk_js = os.path.join(backup_dir, f"02_NAV_SCRIPT_backup_{timestamp}.js")
        shutil.copy2(js_path, bk_js)
        print(f"Backed up JS to:  {bk_js}")

    # 3. Write upgraded CSS
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(UPGRADED_NAV_CSS)
    print(f"Updated CSS: {css_path}")

    # 4. Write upgraded JS
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(UPGRADED_NAV_JS)
    print(f"Updated JS:  {js_path}")

    # 5. Verify markers
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()

    assert "NAV_STYLE_V2" in css_content, "NAV_STYLE_V2 marker missing in CSS!"
    assert "NAV_SCRIPT_V2" in js_content, "NAV_SCRIPT_V2 marker missing in JS!"
    assert "NAV_STYLE_PN_V1" in css_content, "NAV_STYLE_PN_V1 marker missing in CSS!"

    print("-" * 65)
    print("SUCCESS: Both CSS and JS upgraded successfully!")
    print("All study HTML pages loading 02_NAV_STYLE.css & 02_NAV_SCRIPT.js")
    print("will now render with enhanced interactive flows, callouts,")
    print("sticky search-enabled tables, code toolbars, Zen mode, and more.")
    print("=" * 65)


if __name__ == "__main__":
    main()
