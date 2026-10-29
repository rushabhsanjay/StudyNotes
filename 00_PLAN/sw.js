/* Study Notes service worker. Lives at repo root so its scope covers /StudyNotes/ */
const CACHE = 'study-v1';          // bump to v2, v3... to force-refresh everything
const CORE = [
  './', './index.html', './manifest.json',
  './00_PLAN/03_HTML_INDEX.html', './00_PLAN/02_NAV_STYLE.css',
  './00_PLAN/02_NAV_SCRIPT.js', './00_PLAN/nav_data.js'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => Promise.all(CORE.map(u => c.add(u).catch(() => {}))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// Cache first, refresh in background. Query strings (?v=...) are ignored.
self.addEventListener('fetch', e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || u.origin !== location.origin) return;
  u.search = '';
  const key = u.href;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(key);
    const net = fetch(u.href).then(res => { if (res.ok) c.put(key, res.clone()); return res; })
                             .catch(() => hit);
    return hit || net;
  }));
});

// Optional: page sends {type:'precache', urls:[...]} to download all notes for offline use
self.addEventListener('message', e => {
  if (!e.data || e.data.type !== 'precache') return;
  const port = e.ports && e.ports[0];
  e.waitUntil(caches.open(CACHE).then(async c => {
    let done = 0;
    for (const url of e.data.urls) {
      try { const res = await fetch(url); if (res.ok) await c.put(new URL(url).href, res); } catch (_) {}
      done++;
      if (port && done % 10 === 0) port.postMessage({done, total: e.data.urls.length});
    }
    if (port) port.postMessage({done, total: e.data.urls.length, finished: true});
  }));
});
