/* Open Subsurface Data, the browser cache for the shop's data files (E50, OSD-D40).

   Why: GitHub Pages gives one file different ETags from different servers, so after max-age the
   browser's own check of a cached file comes back as a full 200, and every return visit downloads
   records.json again (measured 25 Nov 2026, docs/program/evidence/e50/measurements.md).

   What it touches: only the files directly under data/ that end in .json, .txt or .pmtiles. Never
   HTML, JS or CSS, never anything else: every other request goes to the network as if it were not here.
   - A tile archive (.pmtiles), asked by byte range: from the cache when the file on the host is
     the one the cache holds, else from the network, kept. Whether it is the same file is asked with
     one HEAD per file (headers only, no body), once a visit (at most once a minute).
   - A data file (.json, .txt): from the cache at once; the same HEAD in the background, and when the
     file has changed it is fetched and kept for the next visit (stale-while-revalidate).
   "The same file": the size and the modification time the host gives (in the ETag, W/"mtime-size",
   or Content-Length and Last-Modified), the time within a minute (Pages' servers differ by seconds).

   Switching it off, for every visitor: publish site/sw-off.txt. Before it installs, and with each
   file check, the worker asks for it (HEAD); when it is there, the worker deletes its caches and
   unregisters itself, and a new one does not install. */
const PREFIX = 'osd-data|';
const OURS = /\/data\/[^/]+\.(json|txt|pmtiles)$/;
const OFF = new URL('sw-off.txt', self.registration.scope).href;
const CHECK_MS = 60e3, SAME_S = 60;

const head = url => fetch(url, { method: 'HEAD', cache: 'no-store' }).catch(() => null);
let offAsked = null;
const switchedOff = (fresh = false) => { // asked at most once a minute
  if (fresh || !offAsked || Date.now() - offAsked.at > CHECK_MS) offAsked = { at: Date.now(), p: head(OFF).then(r => !!(r && r.ok)) };
  return offAsked.p; };
async function off() {
  for (const k of await caches.keys()) if (k.startsWith(PREFIX)) await caches.delete(k);
  await self.registration.unregister();
}

self.addEventListener('install', e => e.waitUntil(switchedOff(true).then(o => { if (o) throw new Error('switched off (sw-off.txt)'); return self.skipWaiting(); })));
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

// The file on the host: { size, time } from one HEAD, or null when it cannot be told.
function versionOf(r) {
  if (!r || !r.ok) return null;
  const m = /^(?:W\/)?"([0-9a-f]+)-([0-9a-f]+)"$/.exec(r.headers.get('etag') || '');
  if (m) return { size: parseInt(m[2], 16), time: parseInt(m[1], 16) };
  const lm = Date.parse(r.headers.get('last-modified') || ''), size = Number(r.headers.get('content-length'));
  return Number.isFinite(lm) && size > 0 ? { size, time: Math.floor(lm / 1000) } : null;
}
const nameOf = (path, v) => `${PREFIX}${path}|${v.size}|${v.time}`;
const sameAs = (name, path, v) => { const [, p, size, time] = name.split('|');
  return p === path && Number(size) === v.size && Math.abs(Number(time) - v.time) <= SAME_S; };

// One check per file a minute, shared by the requests that come together; the switch asked beside it.
const checks = new Map();
function check(url) {
  const path = new URL(url).pathname, c = checks.get(path);
  if (c && Date.now() - c.at < CHECK_MS) return c.p;
  const p = Promise.all([head(url), switchedOff()]).then(async ([r, isOff]) => {
    if (isOff) { await off(); return { path, off: true }; }
    const v = versionOf(r);
    if (!v) return { path, v: null };
    const names = (await caches.keys()).filter(k => k.startsWith(PREFIX + path + '|'));
    const name = names.find(n => sameAs(n, path, v)) || nameOf(path, v);
    for (const n of names) if (n !== name) await caches.delete(n); // an older file: gone
    return { path, v, name };
  });
  checks.set(path, { at: Date.now(), p });
  return p;
}

// The Cache API keeps no 206: a range is kept as a 200 under its own key and given back as a 206.
const keyOf = (url, range) => range ? `${url}?range=${range.replace(/^bytes=/, '')}` : url;
// No If-Range and no If-None-Match from the HTTP cache (no stale-ETag 200), except for the page's own
// second reading of its first load (cache: 'force-cache'), which the HTTP cache answers.
async function fromNetwork(req, range) {
  return fetch(req.url, { headers: range ? { range } : {}, cache: req.cache === 'force-cache' ? 'force-cache' : 'no-store' });
}
async function keep(name, key, res) {
  if (!name || !(res.status === 200 || res.status === 206)) return;
  const h = new Headers(res.headers);
  if (res.status === 206) h.set('x-osd-status', '206');
  await (await caches.open(name)).put(key, new Response(await res.clone().arrayBuffer(), { status: 200, headers: h }));
}
function given(cached) {
  if (cached.headers.get('x-osd-status') !== '206') return cached;
  return new Response(cached.body, { status: 206, statusText: 'Partial Content', headers: cached.headers });
}

async function archive(req, range) {
  const c = await check(req.url);
  if (c.off || !c.name) return fromNetwork(req, range);
  const key = keyOf(req.url, range), hit = await (await caches.open(c.name)).match(key);
  if (hit) return given(hit);
  const res = await fromNetwork(req, range);
  // A range answered with the whole file is passed on (the reader refuses it) and not kept.
  if (!range || res.status === 206) await keep(c.name, key, res.clone()).catch(() => {});
  return res;
}

async function data(req, e) {
  const names = (await caches.keys()).filter(k => k.startsWith(PREFIX + new URL(req.url).pathname + '|'));
  const hit = names.length ? await (await caches.open(names[names.length - 1])).match(req.url) : null;
  const refresh = check(req.url).then(async c => {
    if (c.off || !c.name) return null;
    if (hit && names.includes(c.name) && await (await caches.open(c.name)).match(req.url)) return null; // unchanged
    const res = await fromNetwork(req);
    if (res.ok) await keep(c.name, req.url, res.clone());
    return res;
  });
  if (hit) { e.waitUntil(refresh.catch(() => {})); return hit; }
  return refresh.then(r => r || fromNetwork(req)).catch(() => fromNetwork(req));
}

self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.mode === 'navigate') { offAsked = null; checks.clear(); } // a new visit: every file and the switch asked afresh
  if (req.method !== 'GET' || url.origin !== self.location.origin || !OURS.test(url.pathname)) return; // not ours: the network
  const range = req.headers.get('range');
  if (url.pathname.endsWith('.pmtiles')) e.respondWith(archive(req, range).catch(() => fromNetwork(req, range)));
  else if (!range) e.respondWith(data(req, e).catch(() => fromNetwork(req)));
});
