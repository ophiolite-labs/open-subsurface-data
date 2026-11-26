/* Open Subsurface Data, the shop's measuring mode (E50, R-S7). Loaded by shop.js only when the
   address carries ?measure=1, so the normal page carries none of it. It watches the page load, then
   runs one fixed script, the same on every device, and shows four numbers in a small readout:
     1  usable: milliseconds from navigation start to the map's first `idle` (and to the list's
        first count);
     2  pictures a second over a scripted drag and zoom (and the longest frame);
     3  requests and bytes from the site while zooming out three levels and back (the coming back
        is an area visited before: target 0);
     4  requests and bytes from the site since load (records.json and the tiles named apart, with
        what the browser says it did: network, revalidated, from cache).
   Bytes are the Performance API's transferSize (headers and body over the wire; 0 when served from
   the browser's cache). Everything is in window.osdMeasure for a script that drives the browser.
   No dependency, nothing stored, nothing sent. */
(function () {
  const t0 = performance.now();
  try { performance.setResourceTimingBufferSize(10000); } catch (e) { /* the default 250 then */ }
  const R = { version: 1, loadedAt: Math.round(t0), userAgent: navigator.userAgent,
    screen: { w: innerWidth, h: innerHeight, dpr: devicePixelRatio }, idleMs: null, listMs: null,
    late: false, atIdle: null, firstLoad: null, script: null, zoomOutBack: null, site: null, layers: null, done: false };
  let ready, map = null;
  const done = new Promise(ok => { ready = ok; });
  window.osdMeasure = { result: R, done, run: () => runScript() };

  // ---- Watching the first load ----------------------------------------------------------------
  // shop.js sets window.osdMap right after it makes the map, before the map can be idle.
  const attach = m => {
    if (map) return;
    map = m;
    if (m.loaded() && m.areTilesLoaded()) { R.late = true; R.idleMs = Math.round(performance.now()); start(); return; }
    m.once('idle', () => { R.idleMs = Math.round(performance.now()); start(); });
  };
  if (window.osdMap) attach(window.osdMap);
  else {
    let v;
    Object.defineProperty(window, 'osdMap', { configurable: true, enumerable: true,
      get: () => v, set: m => { v = m; if (m) attach(m); } });
  }
  const watchList = () => {
    const c = document.getElementById('count');
    if (!c) return false;
    const seen = () => { if (R.listMs === null && c.textContent) { R.listMs = Math.round(performance.now()); return true; } return R.listMs !== null; };
    if (!seen()) new MutationObserver((_, o) => { if (seen()) o.disconnect(); }).observe(c, { childList: true, characterData: true, subtree: true });
    return true;
  };
  if (!watchList()) document.addEventListener('DOMContentLoaded', watchList, { once: true });

  // ---- What came from the site ----------------------------------------------------------------
  const ours = () => performance.getEntriesByType('resource').filter(e => e.name.startsWith(location.origin));
  // Chrome counts a response's headers as 300 bytes (Resource Timing): a body over the wire gives
  // transferSize = encodedBodySize + 300; a 304 gives 300 with the cached body's size beside it.
  const how = e => e.transferSize === undefined ? 'unknown' : e.transferSize === 0 ? (e.decodedBodySize > 0 ? 'cache' : 'no body')
    : e.transferSize < e.encodedBodySize + 300 ? 'revalidated' : 'network';
  function sum(entries) {
    const files = {};
    for (const e of entries) {
      const f = new URL(e.name).pathname.split('/').pop() || 'shop.html';
      const s = files[f] || (files[f] = { requests: 0, bytes: 0, body: 0, how: {}, status: {} });
      s.requests++; s.bytes += e.transferSize || 0; s.body += e.encodedBodySize || 0;
      s.how[how(e)] = (s.how[how(e)] || 0) + 1;
      if (e.responseStatus) s.status[e.responseStatus] = (s.status[e.responseStatus] || 0) + 1;
    }
    return { requests: entries.length, bytes: entries.reduce((a, e) => a + (e.transferSize || 0), 0), files };
  }
  function siteSinceLoad() {
    const nav = performance.getEntriesByType('navigation')[0];
    return sum(nav ? [nav, ...ours()] : ours());
  }

  // ---- The script: the same on every device ---------------------------------------------------
  // settled: the map is idle now or at its next `idle`; after a jump, always the next `idle` (a jump
  // renders, and tiles are only asked for in that render).
  const settled = () => new Promise(ok => map.loaded() && map.areTilesLoaded() && !map.isMoving() ? ok() : map.once('idle', ok));
  const jump = o => { const p = new Promise(ok => map.once('idle', ok)); map.jumpTo(o); return p; };
  const moved = () => new Promise(ok => map.once('moveend', ok));
  function frames(run) {
    return new Promise(ok => {
      const ts = [];
      let on = true;
      const tick = t => { ts.push(t); if (on) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
      run().then(() => { on = false; requestAnimationFrame(() => {
        const span = ts.length > 1 ? ts[ts.length - 1] - ts[0] : 0;
        let longest = 0;
        for (let i = 1; i < ts.length; i++) longest = Math.max(longest, ts[i] - ts[i - 1]);
        ok({ frames: ts.length - 1, ms: Math.round(span), fps: span ? Math.round((ts.length - 1) / span * 1000 * 10) / 10 : null, longestFrameMs: Math.round(longest) });
      }); });
    });
  }
  async function dragAndZoom() {
    // A drag is a pan of 40 % of the map's width and back by way of 30 % of its height, at the pace
    // of a hand (800 ms a stroke), then one level in and out; sized to the map, so the same on a phone.
    const c = map.getCanvas(), w = c.clientWidth, h = c.clientHeight, z = map.getZoom();
    for (const [dx, dy] of [[0.4 * w, 0], [-0.4 * w, 0.3 * h], [0, -0.3 * h]]) {
      const m = moved(); map.panBy([dx, dy], { duration: 800, easing: t => t }); await m;
    }
    for (const to of [z + 1, z]) { const m = moved(); map.zoomTo(to, { duration: 800 }); await m; }
  }
  async function outAndBack() {
    // Three levels out, then back where it was, each a jump (no in-between levels), each waited to idle.
    const z = map.getZoom(), before = ours().length;
    await jump({ zoom: Math.max(0, z - 3) });
    const mid = ours().length;
    await jump({ zoom: z });
    const all = ours();
    return { out: sum(all.slice(before, mid)), back: sum(all.slice(mid)) };
  }
  let running = false;
  async function runScript() {
    if (running || !map) return R;
    running = true;
    const view = { center: map.getCenter(), zoom: map.getZoom() };
    await settled();
    R.script = await frames(dragAndZoom);
    await settled();
    R.zoomOutBack = await outAndBack();
    await jump(view);
    R.site = siteSinceLoad();
    R.layers = map.getStyle().layers.map(l => ({ id: l.id, type: l.type, source: l.source || null,
      minzoom: l.minzoom ?? null, maxzoom: l.maxzoom ?? null }));
    R.done = true;
    running = false;
    show();
    ready(R);
    return R;
  }
  function start() {
    R.atIdle = siteSinceLoad(); // the first-load budget (R-S7, E36): under 1 MB from the site
    // Where the first load's time went: every request until the first idle, any origin, by when it ended.
    const nav = performance.getEntriesByType('navigation')[0];
    R.firstLoad = [nav, ...performance.getEntriesByType('resource')].filter(Boolean).map(e => ({
      name: e.name.replace(/^https?:\/\//, '').slice(0, 120), start: Math.round(e.startTime), end: Math.round(e.responseEnd),
      bytes: e.transferSize ?? null })).sort((a, b) => a.end - b.end);
    show();
    setTimeout(runScript, 500); // let the list settle; the readout already shows the load numbers
  }

  // ---- The readout ----------------------------------------------------------------------------
  const kb = b => b >= 1e6 ? `${(b / 1e6).toFixed(2)} MB` : `${Math.round(b / 1e3)} kB`;
  const hows = f => f ? Object.entries(f.how).map(([k, n]) => `${n} ${k}`).join(', ') : 'not asked';
  function show() {
    let box = document.getElementById('osd-measure');
    if (!box) {
      if (!document.body) return;
      box = document.createElement('section');
      box.id = 'osd-measure';
      box.setAttribute('aria-label', 'Measuring mode');
      box.style.cssText = 'position:fixed;left:8px;bottom:8px;z-index:9999;max-width:min(360px,calc(100vw - 16px));' +
        'background:#101824;color:#fff;font:12px/1.45 ui-monospace,Menlo,Consolas,monospace;padding:8px 10px;' +
        'border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.35);opacity:.94';
      document.body.appendChild(box);
    }
    const s = R.script, zb = R.zoomOutBack, site = R.site;
    const tiles = site && Object.entries(site.files).filter(([f]) => f.endsWith('.pmtiles'));
    const lines = [
      `<b>Measuring mode</b> (E50) ${R.done ? '' : '· running…'}`,
      `1 usable <b>${R.idleMs ?? '…'} ms</b>${R.late ? ' (late)' : ''} · list ${R.listMs ?? '…'} ms`,
      `2 drag+zoom <b>${s ? s.fps : '…'} fps</b>${s ? ` · longest frame ${s.longestFrameMs} ms` : ''}`,
      `3 zoom back <b>${zb ? `${zb.back.requests} req, ${kb(zb.back.bytes)}` : '…'}</b>${zb ? ` · out ${zb.out.requests} req, ${kb(zb.out.bytes)}` : ''}`,
      `4 site since load <b>${site ? `${site.requests} req, ${kb(site.bytes)}` : '…'}</b>${R.atIdle ? ` · at idle ${R.atIdle.requests} req, ${kb(R.atIdle.bytes)}` : ''}`,
    ];
    if (site) {
      lines.push(`&nbsp; records.json: ${hows(site.files['records.json'])}`);
      for (const [f, v] of tiles) lines.push(`&nbsp; ${f}: ${v.requests} ranges, ${kb(v.bytes)} (${hows(v)})`);
      lines.push(`&nbsp; layers ${R.layers.length} · ${R.screen.w}×${R.screen.h}@${R.screen.dpr}`);
    }
    box.innerHTML = lines.map(l => `<div>${l}</div>`).join('') +
      (R.done ? '<button type="button" style="margin-top:6px;font:inherit;color:#101824;background:#e0912f;border:0;border-radius:4px;padding:2px 8px">Run again</button>' : '');
    const b = box.querySelector('button');
    if (b) b.onclick = () => { R.done = false; show(); runScript(); };
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', show, { once: true });
})();
