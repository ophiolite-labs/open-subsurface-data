/* Open Subsurface Data, the one-page shop (E47; family "The map as a shop"). Static, one file, no
   framework, nothing imported from app.js. Reads what `make build` puts in data/: records.json (the
   list and the map's filter), files.txt, outlines.pmtiles or outlines.geojson and wells-z<z>.json (the
   map), collections.json and mirror.json (the bag, fetched when it is used), starters.json (a
   detail with a starter project). The URL hash is the only state; its keys are the live page's
   (q, k, l, t, dated, starter, sel, pick, map) plus `a` for access. The list follows the map window
   and is computed from records.json, never from the tiles (R-S7). */
(async function () {
  if (/[?&]measure=1(&|$)/.test(location.search)) document.head.appendChild(Object.assign(document.createElement('script'), { src: 'measure.js' })); // E50: the measuring mode, only on ?measure=1
  const BASEMAP = 'https://tiles.openfreemap.org/styles/liberty';
  const PMTILES_JS = 'https://unpkg.com/pmtiles@4.5.0/dist/pmtiles.js';
  const CLUSTER_BELOW_ZOOM = 7;   // as the live page and the build's well grids (E36)
  const WORLD_ZOOM = 2;           // below it the window is the world: records with no place are listed
  const STALE_DAYS = 30;
  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // ---- Data ------------------------------------------------------------------------------------
  // E50: records.json and areas.json are asked for at once, beside files.txt and the tile headers,
  // not one after the other (shop.html preloads them while maplibre-gl.js downloads).
  const builtP = fetch('data/records.json').then(r => r.json());
  const indexP = fetch('data/areas.json').then(r => r.ok ? r.json() : null).catch(() => null);
  builtP.catch(() => {}); // awaited below, where a failure still stops the page
  const files = (await fetch('data/files.txt').then(r => r.ok ? r.text() : '').catch(() => '')).split('\n');
  const has = f => files.includes(f);
  const base = location.href.replace(/[#?].*$/, '').replace(/[^/]*$/, '');
  // E50: a return visit can hold a stale byte range whose ETag the host no longer gives (GitHub
  // Pages' ETag for one file differs between its servers); the range then comes back as the whole
  // file, which the reader refuses. Asked once more past the browser's cache, the tiles stay on.
  // E48: the same for the area tiles.
  // E50 (OSD-D40): the byte ranges the first load reads, read again through the browser cache once
  // it is in place, so a return visit finds them there (see warmCache below).
  const ranges = new Set(), cached = 'serviceWorker' in navigator && !!navigator.serviceWorker.controller;
  const archive = (f, fresh) => { const src = new pmtiles.FetchSource(base + 'data/' + f); src.mustReload = fresh;
    const get = src.getBytes.bind(src);
    src.getBytes = (offset, length, ...rest) => { if (!cached) ranges.add(`${src.url} ${offset}-${offset + length - 1}`); return get(offset, length, ...rest); };
    return new pmtiles.PMTiles(src); };
  const pmtilesJs = (has('outlines.pmtiles') || has('areas.pmtiles')) && await new Promise(ok => {
    const s = document.createElement('script'); s.src = PMTILES_JS;
    s.onload = () => ok(true); s.onerror = () => ok(false); document.head.appendChild(s);
  });
  const tilesOf = async f => { if (!pmtilesJs || !has(f)) return null;
    for (const fresh of [false, true]) { const t = archive(f, fresh); if (await t.getHeader().then(() => true, () => false)) return t; }
    return null; };
  const [tiles, areaTiles] = await Promise.all([tilesOf('outlines.pmtiles'), tilesOf('areas.pmtiles')]);
  const pmtilesMode = !!tiles;

  const built = await builtP;
  const records = built.records.map(r => ({ ...r, reason: (built.reasons || {})[r.id] || '' }));
  const byId = Object.fromEntries(records.map(r => [r.id, r]));
  const LEVEL = s => Number((s || 'L0').slice(1));
  const hasStarter = r => !!(r.starters && r.starters.length);
  const anyStarter = records.some(hasStarter);
  const isStale = r => !!r.checked_at && Date.now() - Date.parse(r.checked_at) > STALE_DAYS * 864e5;
  const collator = new Intl.Collator('en');
  const byTitle = (a, b) => collator.compare(a.title, b.title) || (a.id < b.id ? -1 : 1);

  // Which records the outlines draw: the tile set's own statistics (tippecanoe tilestats), or the
  // GeoJSON when that is the path. A record with a box and nothing drawn becomes one dot (design 6).
  const outlines = pmtilesMode ? null : has('outlines.geojson') ? await (await fetch('data/outlines.geojson')).json()
    : { type: 'FeatureCollection', features: [] };
  const drawn = new Set(pmtilesMode
    ? await tiles.getMetadata().then(m => {
      const a = ((m.tilestats || {}).layers || []).flatMap(l => l.attributes || []).find(a => a.attribute === 'record_id');
      return a && a.values.length === a.count ? a.values : [];
    }, () => [])
    : outlines.features.map(f => f.properties.record_id));

  // ---- Areas (E46, E48): the build's index of the areas that hold a dataset, per kind ---------------
  // areas.json is the authority for which areas exist (R-S3); the page computes no containment.
  const index = has('areas.json') ? await indexP : null;
  const KIND_LABEL = { country: 'Countries', province: 'Provinces', basin: 'Basins', licence: 'Licences' };
  const KINDS = Object.keys(KIND_LABEL).filter(k => index && index.kinds[k]);
  const areasOf = k => KINDS.includes(k) ? index.kinds[k].areas : [];
  const areaById = Object.fromEntries(KINDS.map(k => [k, Object.fromEntries(areasOf(k).map(a => [a.area_id, a]))]));
  const creditOf = k => [...new Set(index.kinds[k].sources.map(s => s.credit).filter(Boolean))].join(', ');

  // ---- Where a record is ------------------------------------------------------------------------
  // The record's bbox; without one the box of the countries the build placed it in (records[].areas,
  // the boxes from areas.json); without either, no place: listed only at the world view.
  function countriesBox(r) {
    const bs = ((r.areas || {}).country || []).map(id => (areaById.country || {})[id]).filter(Boolean).map(a => a.bbox);
    if (bs.length < 2) return bs[0] || null;
    if (bs.some(b => b[0] > b[2])) return [-180, Math.min(...bs.map(b => b[1])), 180, Math.max(...bs.map(b => b[3]))];
    return [Math.min(...bs.map(b => b[0])), Math.min(...bs.map(b => b[1])), Math.max(...bs.map(b => b[2])), Math.max(...bs.map(b => b[3]))];
  }
  const places = new Map(records.map(r => [r.id, (r.region && r.region.bbox) || countriesBox(r)]));
  const placeOf = r => places.get(r.id) || null;

  // The window as longitude ranges in [-180, 180] (two when it crosses the antimeridian) and latitudes.
  function windowOf() {
    const b = map.getBounds(), w = b.getWest(), e = b.getEast();
    let ranges;
    if (e - w >= 360) ranges = [[-180, 180]];
    else {
      const k = Math.floor((w + 180) / 360), w0 = w - 360 * k, e0 = e - 360 * k;
      ranges = e0 > 180 ? [[w0, 180], [-180, e0 - 360]] : [[w0, e0]];
    }
    const c = map.getCanvas(), earth = state.globe && 512 * 2 ** map.getZoom() / Math.PI <= Math.min(c.clientWidth, c.clientHeight);
    if (earth) return { ranges: [[-180, 180]], south: -90, north: 90, world: true };   // the whole globe in view: every dataset
    return { ranges, south: b.getSouth(), north: b.getNorth(), world: map.getZoom() < WORLD_ZOOM };
  }
  // 0 outside, 1 meets the window, 2 wholly inside it.
  function relation([w, s, e, n], win) {
    if (s > win.north || n < win.south) return 0;
    const box = w <= e ? [[w, e]] : [[w, 180], [-180, e]];
    if (!box.some(([a, b]) => win.ranges.some(([c, d]) => a <= d && b >= c))) return 0;
    return s >= win.south && n <= win.north && box.every(([a, b]) => win.ranges.some(([c, d]) => a >= c && b <= d)) ? 2 : 1;
  }

  // ---- State <-> hash ---------------------------------------------------------------------------
  //   #q=volve&k=field,seismic-3d&l=2&t=1990-2000&dated=1&a=anonymous&starter=1&sel=equinor/volve
  //   &pick=opm/norne,sodir/factpages&map=5.00/58.0000/3.0000&o=basin&area=usgs-5243&n=1&p=globe
  // o, area, n and p are E48's: the kind of area drawn, the area clicked, names on, the globe.
  const ACCESS = {
    anonymous: { label: 'Download', alt: 'download: anyone can take the files',
      line: 'Open to anyone: the files download without an account.',
      svg: '<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M5 20h14"/>' },
    registration: { label: 'Sign-in', alt: 'sign-in: an account at the publisher is needed',
      line: 'Sign in at the publisher\'s page to get the files.',
      svg: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>' },
    api: { label: 'API', alt: 'API: the publisher serves the data through an API',
      line: 'Through the publisher\'s API.',
      svg: '<path d="M9 4C7 4 6 5 6 7v2c0 1.5-1 2.5-2 3 1 .5 2 1.5 2 3v2c0 2 1 3 3 3"/><path d="M15 4c2 0 3 1 3 3v2c0 1.5 1 2.5 2 3-1 .5-2 1.5-2 3v2c0 2-1 3-3 3"/>' },
    request: { label: 'On request', alt: 'on request: ask the publisher for the files',
      line: 'On request: ask the publisher at its page.',
      svg: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>' },
    purchase: { label: 'Purchase', alt: 'purchase: the publisher sells the files',
      line: 'Sold by the publisher: buy the files at its page.',
      svg: '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>' },
  };
  const accessIcon = a => { const x = ACCESS[a] || ACCESS.request;
    return `<span class="acc" data-access="${esc(a)}" role="img" aria-label="${esc(x.alt)}" title="${esc(x.alt)}"><svg viewBox="0 0 24 24" aria-hidden="true">${x.svg}</svg></span>`; };

  const state = { q: '', kinds: new Set(), minLevel: 0, from: null, to: null, dated: false, access: new Set(), starter: false, sel: null, pick: [],
    kind: KINDS[0] || null, area: null, names: false, globe: false };
  function readHash() {
    const h = new URLSearchParams(location.hash.slice(1));
    state.q = (h.get('q') || '').trim().toLowerCase();
    state.kinds = new Set((h.get('k') || '').split(',').filter(Boolean));
    state.minLevel = Math.max(0, Math.min(4, Number(h.get('l')) || 0));
    const t = /^(\d{4})?-(\d{4})?$/.exec(h.get('t') || '') || [];
    state.from = t[1] ? Number(t[1]) : null;
    state.to = t[2] ? Number(t[2]) : null;
    state.dated = h.get('dated') === '1';
    state.access = new Set((h.get('a') || '').split(',').filter(a => ACCESS[a]));
    state.starter = anyStarter && h.get('starter') === '1';
    state.sel = byId[h.get('sel')] ? h.get('sel') : null;
    state.pick = [...new Set((h.get('pick') || '').split(',').filter(id => byId[id]))];
    state.kind = KINDS.includes(h.get('o')) ? h.get('o') : KINDS[0] || null;
    state.area = state.kind && areaById[state.kind][h.get('area')] ? h.get('area') : null;
    state.names = h.get('n') === '1';
    state.globe = h.get('p') === 'globe';
    const m = (h.get('map') || '').split('/').map(Number);
    return m.length === 3 && m.every(Number.isFinite) ? { zoom: m[0], center: [m[2], m[1]] } : null;
  }
  function writeHash() {
    const h = new URLSearchParams();
    if (state.q) h.set('q', state.q);
    if (state.kinds.size) h.set('k', [...state.kinds].sort().join(','));
    if (state.minLevel) h.set('l', state.minLevel);
    if (state.from !== null || state.to !== null) h.set('t', `${state.from ?? ''}-${state.to ?? ''}`);
    if (state.dated) h.set('dated', '1');
    if (state.access.size) h.set('a', [...state.access].sort().join(','));
    if (state.starter) h.set('starter', '1');
    if (state.sel) h.set('sel', state.sel);
    if (state.pick.length) h.set('pick', state.pick.join(','));
    if (state.kind && state.kind !== KINDS[0]) h.set('o', state.kind);
    if (state.area) h.set('area', state.area);
    if (state.names) h.set('n', '1');
    if (state.globe) h.set('p', 'globe');
    if (map && mapReady) {
      const c = map.getCenter();
      h.set('map', `${map.getZoom().toFixed(2)}/${c.lat.toFixed(4)}/${c.lng.toFixed(4)}`);
    }
    const s = h.toString().replace(/%2F/g, '/').replace(/%2C/g, ',');
    if (s !== location.hash.slice(1)) history.replaceState(null, '', s ? '#' + s : location.pathname + location.search);
  }

  // ---- Filters: the live page's meaning (app.js matches), plus access -----------------------------
  const year = s => s ? Number(String(s).slice(0, 4)) : null;
  const span = r => r.period && (r.period.start || r.period.end)
    ? [year(r.period.start) ?? -Infinity, year(r.period.end) ?? new Date().getUTCFullYear()] : null;
  const yearsLabel = r => { const [a, b] = [year(r.period.start), year(r.period.end)]; return a === b ? String(a) : `${a ?? ''}–${b ?? 'today'}`; };
  function matches(r) {
    if (LEVEL(r.level) < state.minLevel) return false;
    const p = span(r);
    if (state.dated && !p) return false;
    if (state.starter && !hasStarter(r)) return false;
    if (p && ((state.to !== null && p[0] > state.to) || (state.from !== null && p[1] < state.from))) return false;
    if (state.kinds.size && !r.kinds.some(k => state.kinds.has(k))) return false;
    if (state.access.size && !state.access.has(r.origin.access)) return false;
    if (state.q) {
      const hay = [r.title, r.publisher.name, r.region && r.region.basin, r.region && r.region.country, r.id].join(' ').toLowerCase();
      if (!hay.includes(state.q)) return false;
    }
    return true;
  }
  // The area clicked (E48): its datasets are the build's ids for it, met with the filters, not the window.
  const inArea = r => !state.area || areaById[state.kind][state.area].ids.includes(r.id);
  const filterCount = () => [state.kinds.size, state.minLevel, state.from !== null || state.to !== null, state.dated,
    state.access.size, state.starter].filter(Boolean).length;

  // ---- The map ----------------------------------------------------------------------------------
  const view = readHash();
  let map = null, mapReady = false;
  if (tiles || areaTiles) { const protocol = new pmtiles.Protocol(); for (const t of [tiles, areaTiles]) if (t) protocol.add(t);
    maplibregl.addProtocol('pmtiles', protocol.tile); }
  map = new maplibregl.Map({ container: 'map', style: BASEMAP, center: view ? view.center : [6, 56], zoom: view ? view.zoom : 3.3,
    attributionControl: { compact: true }, dragRotate: false, pitchWithRotate: false, touchPitch: false, maxPitch: 0,
    // E50 (R-S7): five zoom levels of tiles kept for zooming back; no refetch of tiles the host's
    // max-age=600 marks expired (the files do not change within a visit); names without the fade.
    maxTileCacheZoomLevels: 5, refreshExpiredTiles: false, fadeDuration: 0 });
  map.touchZoomRotate.disableRotation();
  map.keyboard.disableRotation();
  window.osdMap = map; // for the site test and the console; not an API
  // E50 (OSD-D40): the browser cache for data/ (site/sw.js), registered after the first idle so it never
  // competes with the first load. site/sw-off.txt, once published, switches it off for every visitor.
  // On the first visit the page is not yet under it: once it is, what the first load read is asked
  // once more (from the browser's HTTP cache, cache: 'force-cache'), and the worker keeps it.
  const warmCache = () => {
    for (const e of performance.getEntriesByType('resource')) if (/\/data\/[^/]+\.(json|txt)$/.test(new URL(e.name).pathname)) fetch(e.name, { cache: 'force-cache' }).catch(() => {});
    for (const r of ranges) { const [u, b] = r.split(' '); fetch(u, { cache: 'force-cache', headers: { range: 'bytes=' + b } }).catch(() => {}); }
    ranges.clear();
  };
  if ('serviceWorker' in navigator) map.once('idle', () => navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' })
    .then(() => cached || (navigator.serviceWorker.controller ? warmCache()
      : navigator.serviceWorker.addEventListener('controllerchange', warmCache, { once: true }))).catch(() => {}));
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

  // The map's own switches (E48): the kind of area and Names bottom left, Flat | Globe bottom right.
  const control = (html, at) => { const el = document.createElement('div'); el.className = 'maplibregl-ctrl osd-ctrl'; el.innerHTML = html;
    map.addControl({ onAdd: () => el, onRemove: () => el.remove() }, at); return el; };
  const seg = (label, items) => `<div class="seg" role="group" aria-label="${label}">${items.map(([v, t]) =>
    `<button type="button" data-v="${v}" aria-pressed="false">${t}</button>`).join('')}</div>`;
  const kindCtl = KINDS.length ? control(seg('Areas drawn', KINDS.map(k => [k, KIND_LABEL[k]])) +
    '<button type="button" class="names" aria-pressed="false">Names</button>', 'bottom-left') : null;
  const projCtl = control(seg('Projection', [['flat', 'Flat'], ['globe', 'Globe']]), 'bottom-right');
  if (kindCtl) {
    kindCtl.querySelectorAll('.seg button').forEach(b => b.onclick = () => setKind(b.dataset.v));
    kindCtl.querySelector('.names').onclick = () => setNames(!state.names);
  }
  projCtl.querySelectorAll('button').forEach(b => b.onclick = () => setGlobe(b.dataset.v === 'globe'));
  function syncMapControls() {
    if (kindCtl) {
      kindCtl.querySelectorAll('.seg button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.v === state.kind)));
      kindCtl.querySelector('.names').setAttribute('aria-pressed', String(state.names));
    }
    projCtl.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String((b.dataset.v === 'globe') === state.globe)));
  }
  syncMapControls();

  // Box-only records: one dot at the middle of the box, its name beside it (not a rectangle).
  const boxIds = records.filter(r => r.region && r.region.bbox && !drawn.has(r.id)).map(r => r.id);
  const boxes = { type: 'FeatureCollection', features: boxIds.map((id, i) => {
    const [w, s, e, n] = byId[id].region.bbox;
    return { type: 'Feature', id: i, properties: { record_id: id, name: byId[id].title },
      geometry: { type: 'Point', coordinates: [w <= e ? (w + e) / 2 : ((w + e + 360) / 2 + 180) % 360 - 180, (s + n) / 2] } };
  }) };

  // Wells below CLUSTER_BELOW_ZOOM: the build's grids (E36; rows [cx, cy, record index, exact, approx,
  // lon, lat]); on the GeoJSON path without them, the page counts its own points the same way.
  const gridCells = z => 2 ** (z + 3);
  function cellOf([lon, lat], n) {
    const y = Math.max(-85.05112878, Math.min(85.05112878, lat)) * Math.PI / 180;
    const cl = v => Math.min(n - 1, Math.max(0, Math.floor(v * n)));
    return [cl((lon + 180) / 360), cl((1 - Math.log(Math.tan(y) + 1 / Math.cos(y)) / Math.PI) / 2)];
  }
  const wellPoints = outlines ? outlines.features.filter(f => f.properties.kind === 'wellbore' && f.geometry.type === 'Point') : [];
  function countWells(z) {
    const n = gridCells(z), ri = new Map(), cells = new Map();
    for (const f of wellPoints) {
      const id = f.properties.record_id, [cx, cy] = cellOf(f.geometry.coordinates, n);
      if (!ri.has(id)) ri.set(id, ri.size);
      const k = `${cx}/${cy}/${ri.get(id)}`;
      const c = cells.get(k) || cells.set(k, [cx, cy, ri.get(id), 0, 0, 0, 0]).get(k);
      c[f.properties.approximate ? 4 : 3]++; c[5] += f.geometry.coordinates[0]; c[6] += f.geometry.coordinates[1];
    }
    return { records: [...ri.keys()], rows: [...cells.values()].map(c => (c[5] /= c[3] + c[4], c[6] /= c[3] + c[4], c)) };
  }
  const grids = {};
  const gridAt = z => grids[z] = grids[z] || (has(`wells-z${z}.json`)
    ? fetch(`data/wells-z${z}.json`).then(r => r.ok ? r.json() : { records: [], rows: [] }).catch(() => ({ records: [], rows: [] }))
    : Promise.resolve(countWells(z)));
  const abbrev = n => n >= 10000 ? `${Math.round(n / 1000)}k` : n >= 1000 ? `${Math.round(n / 100) / 10}k` : String(n);
  let wellRecords = [];   // wells feature id -> the record ids it counts (for the row highlight)
  function clusters(g, idSet) {
    const cells = new Map();
    for (const [cx, cy, ri, exact, approx, lon, lat] of g.rows) {
      const id = g.records[ri], k = idSet.has(id) ? exact + approx : 0;
      if (!k) continue;
      const key = cx * 1e5 + cy;
      const c = cells.get(key) || cells.set(key, { n: 0, lon: 0, lat: 0, ids: new Set() }).get(key);
      c.n += k; c.lon += lon * k; c.lat += lat * k; c.ids.add(id);
    }
    wellRecords = [...cells.values()].map(c => c.ids);
    return [...cells.values()].map((c, i) => ({ type: 'Feature', id: i, geometry: { type: 'Point', coordinates: [c.lon / c.n, c.lat / c.n] },
      properties: c.n > 1 ? { point_count: c.n, point_count_abbreviated: abbrev(c.n) } : { record_id: [...c.ids][0], kind: 'wellbore' } }));
  }
  let wellsShown = null;
  async function drawWells(force) {
    const z = Math.floor(map.getZoom()), want = z < CLUSTER_BELOW_ZOOM ? Math.max(0, z) : 'single';
    if (want === wellsShown && !force) return;
    wellsShown = want;
    const idSet = new Set(records.filter(inArea).filter(matches).map(r => r.id));
    let features;
    if (want !== 'single') features = clusters(await gridAt(want), idSet);
    else {
      features = pmtilesMode ? [] : wellPoints.filter(f => idSet.has(f.properties.record_id))
        .map((f, i) => ({ ...f, id: i }));
      wellRecords = features.map(f => new Set([f.properties.record_id]));
    }
    if (wellsShown === want && map.getSource('wells')) { map.getSource('wells').setData({ type: 'FeatureCollection', features }); highlight(lit.id); }
  }

  const HL = ['boolean', ['feature-state', 'hl'], false];
  const NIGHT = '#101824';
  const SURVEY = ['in', ['get', 'kind'], ['literal', ['survey-3d', 'survey-2d']]];
  const FIELD = ['in', ['get', 'kind'], ['literal', ['field', 'block']]];
  const DERIVED = ['!', ['get', 'approximate']];
  const PLACEHOLDER = ['==', ['get', 'approximate'], true];
  const WELL = ['all', ['==', ['get', 'kind'], 'wellbore'], ['==', ['geometry-type'], 'Point']];
  const LAYER_BASE = {
    'fields-fill': FIELD, 'fields-line': ['all', FIELD, DERIVED], 'fields-dash': ['all', FIELD, PLACEHOLDER],
    'surveys-fill': SURVEY, 'surveys-line': ['all', SURVEY, DERIVED], 'surveys-dash': ['all', SURVEY, PLACEHOLDER],
    ...(pmtilesMode ? { 'wells-tiles': WELL } : {}),
  };
  const CLICKABLE = ['surveys-fill', 'fields-fill', 'wells', 'boxes', ...(pmtilesMode ? ['wells-tiles'] : [])];

  // E50: our sources and layers go in as soon as the base map's style is read ('style.load'), not
  // at 'load', which waits for every base map tile, sprite and font: our tiles load beside them.
  map.once('style.load', () => {
    const src = pmtilesMode ? { source: 'outlines', 'source-layer': 'outlines' } : { source: 'outlines' };
    map.addSource('outlines', pmtilesMode
      ? { type: 'vector', url: 'pmtiles://' + base + 'data/outlines.pmtiles', promoteId: { outlines: 'feature_id' } }
      : { type: 'geojson', data: outlines, promoteId: 'feature_id' });
    map.addSource('wells', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addSource('boxes', { type: 'geojson', data: boxes });
    const line = (color, dash) => ({ 'line-color': ['case', HL, NIGHT, color], 'line-width': ['case', HL, 3.5, 2], ...(dash ? { 'line-dasharray': [2, 2] } : {}) });
    // Survey outlines step back below zoom 7 (a neutral ink, faint; dense grids would hide the areas)
    // and take their orange where one survey can be read; a lit one is night blue at every zoom.
    const SURVEY_INK = '#7b8592', SURVEY_ORANGE = '#d98a1c';
    const surveyLine = dash => ({ 'line-color': ['step', ['zoom'], ['case', HL, NIGHT, SURVEY_INK], 7, ['case', HL, NIGHT, SURVEY_ORANGE]],
      'line-width': ['case', HL, 3.5, 0.8], 'line-opacity': ['interpolate', ['linear'], ['zoom'], 4, ['case', HL, 1, 0.3], 7, ['case', HL, 1, 0.75]],
      ...(dash ? { 'line-dasharray': [2, 2] } : {}) });
    map.addLayer({ id: 'fields-fill', type: 'fill', ...src, filter: LAYER_BASE['fields-fill'], paint: { 'fill-color': '#e5484d', 'fill-opacity': ['case', HL, 0.4, 0.18] } });
    map.addLayer({ id: 'fields-line', type: 'line', ...src, filter: LAYER_BASE['fields-line'], paint: line('#e5484d') });
    map.addLayer({ id: 'fields-dash', type: 'line', ...src, filter: LAYER_BASE['fields-dash'], paint: line('#e5484d', true) });
    map.addLayer({ id: 'surveys-fill', type: 'fill', ...src, filter: LAYER_BASE['surveys-fill'], paint: { 'fill-color': '#f2a93b', 'fill-opacity': ['interpolate', ['linear'], ['zoom'], 4, ['case', HL, 0.45, 0], 7, ['case', HL, 0.45, 0.06]] } });
    map.addLayer({ id: 'surveys-line', type: 'line', ...src, filter: LAYER_BASE['surveys-line'], paint: surveyLine(false) });
    map.addLayer({ id: 'surveys-dash', type: 'line', ...src, filter: LAYER_BASE['surveys-dash'], paint: surveyLine(true) });
    const glyphs = !!map.getStyle().glyphs;
    map.addLayer({ id: 'wells-cluster', type: 'circle', source: 'wells', filter: ['has', 'point_count'], maxzoom: CLUSTER_BELOW_ZOOM,
      paint: { 'circle-color': '#2f9e63', 'circle-opacity': 0.85, 'circle-stroke-color': ['case', HL, NIGHT, '#ffffff'], 'circle-stroke-width': ['case', HL, 3, 1],
        'circle-radius': ['step', ['get', 'point_count'], 10, 50, 14, 500, 19, 5000, 25] } });
    if (glyphs) map.addLayer({ id: 'wells-count', type: 'symbol', source: 'wells', filter: ['has', 'point_count'], maxzoom: CLUSTER_BELOW_ZOOM,
      layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-size': 11, 'text-font': ['Noto Sans Regular'] },
      paint: { 'text-color': '#ffffff' } });
    const WELL_PAINT = { 'circle-color': '#2f9e63', 'circle-radius': ['case', HL, 6, 4], 'circle-stroke-color': ['case', HL, NIGHT, '#ffffff'], 'circle-stroke-width': ['case', HL, 2, 1] };
    map.addLayer({ id: 'wells', type: 'circle', source: 'wells', filter: ['!', ['has', 'point_count']], paint: WELL_PAINT,
      ...(pmtilesMode ? { maxzoom: CLUSTER_BELOW_ZOOM } : {}) }); // from it the tiles draw the wells
    if (pmtilesMode) map.addLayer({ id: 'wells-tiles', type: 'circle', ...src, filter: WELL, minzoom: CLUSTER_BELOW_ZOOM, paint: WELL_PAINT });
    map.addLayer({ id: 'boxes', type: 'circle', source: 'boxes',
      paint: { 'circle-color': NIGHT, 'circle-radius': ['case', HL, 7, 4.5], 'circle-stroke-color': '#ffffff', 'circle-stroke-width': ['case', HL, 2.5, 1.5] } });
    if (glyphs) map.addLayer({ id: 'boxes-name', type: 'symbol', source: 'boxes',
      layout: { 'text-field': ['get', 'name'], 'text-size': 10.5, 'text-font': ['Noto Sans Regular'], 'text-anchor': 'left', 'text-offset': [0.8, 0],
        'text-optional': true, 'text-max-width': 12, 'text-padding': 6, visibility: state.names ? 'visible' : 'none' },
      paint: { 'text-color': '#3d4756', 'text-halo-color': '#ffffff', 'text-halo-width': 1.4 } });

    if (KINDS.length) {
      map.addSource('area-labels', { type: 'geojson', data: labelsOf(state.kind) });
      if (glyphs) map.addLayer({ id: 'areas-name', type: 'symbol', source: 'area-labels',
        layout: { 'text-field': ['get', 'name'], 'text-size': 13, 'text-font': ['Noto Sans Bold'], 'text-max-width': 9,
          'text-padding': 1, visibility: state.names ? 'visible' : 'none' },
        paint: { 'text-color': AREA_TEXT, 'text-halo-color': '#ffffff', 'text-halo-width': 1.8 } });
      drawKind(state.kind);
      // A dataset feature under the pointer wins; otherwise the area is the filter (a second click clears it).
      map.on('click', 'areas-fill', e => {
        if (map.queryRenderedFeatures(e.point, { layers: [...CLICKABLE, 'wells-cluster'].filter(l => map.getLayer(l)) }).length) return;
        const id = e.features[0].properties.area_id;
        setArea(id === state.area ? null : id, true);
      });
    }
    for (const l of CLICKABLE) map.on('click', l, e => openRow(e.features[0].properties.record_id));
    map.on('click', 'wells-cluster', e => map.easeTo({ center: e.features[0].geometry.coordinates,
      zoom: Math.min(Math.floor(map.getZoom()) + 2, CLUSTER_BELOW_ZOOM) }));
    for (const l of [...CLICKABLE, 'wells-cluster', ...(KINDS.length ? ['areas-fill'] : [])]) {
      map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer');
      map.on('mouseleave', l, () => map.getCanvas().style.cursor = '');
    }
    map.on('zoom', () => drawWells());
    map.on('moveend', () => { renderList(); writeHash(); });
    // Tiles that arrive after the highlight get it too (debounced: sourcedata fires per tile).
    let again = 0;
    map.on('sourcedata', e => { if (e.sourceId === 'outlines' && e.tile && lit.id) { clearTimeout(again); again = setTimeout(() => highlight(lit.id), 120); } });
    if (state.globe) map.setProjection({ type: 'globe' });
    // On a phone the credits start folded under their (i), so the switches at the bottom stay reachable.
    if (matchMedia('(max-width: 720px)').matches) for (const el of document.querySelectorAll('.maplibregl-compact-show')) el.classList.remove('maplibregl-compact-show');
    mapReady = true;
    applyFilters();
    if (state.area) { selectArea(); if (!view) fitArea(); }
    if (state.sel) highlight(state.sel);
    if (state.sel && !view) fitTo(state.sel);
  });

  // ---- Areas on the map (E48): one kind at a time; its source added the first time it is chosen and
  // kept, its two layers the only area layers in the style; the same lilac for every area (R-S2).
  const AREA = '#34465f', AREA_TEXT = '#1d2838';   // one neutral slate for every area (R-S2)
  const SEL = ['boolean', ['feature-state', 'sel'], false];
  const labelsOf = k => ({ type: 'FeatureCollection', features: areasOf(k).map(a => ({ type: 'Feature',
    properties: { area_id: a.area_id, name: a.name }, geometry: { type: 'Point', coordinates: a.label } })) });
  const areaSource = k => `areas-${k}`;
  const areaTarget = (k, id) => ({ source: areaSource(k), ...(areaTiles ? { sourceLayer: `areas_${k}` } : {}), id });
  function drawKind(k) {
    for (const l of ['areas-fill', 'areas-line']) if (map.getLayer(l)) map.removeLayer(l);
    if (!map.getSource(areaSource(k))) map.addSource(areaSource(k), areaTiles
      ? { type: 'vector', url: 'pmtiles://' + base + 'data/areas.pmtiles', promoteId: { [`areas_${k}`]: 'area_id' }, attribution: creditOf(k) }
      : { type: 'geojson', data: base + `data/areas-${k}.geojson`, promoteId: 'area_id', attribution: creditOf(k) });
    const src = { source: areaSource(k), ...(areaTiles ? { 'source-layer': `areas_${k}` } : {}) };
    const below = map.getLayer('fields-fill') ? 'fields-fill' : undefined;
    map.addLayer({ id: 'areas-fill', type: 'fill', ...src, paint: { 'fill-color': AREA, 'fill-opacity': ['case', SEL, 0.3, 0.14] } }, below);
    map.addLayer({ id: 'areas-line', type: 'line', ...src, paint: { 'line-color': AREA, 'line-opacity': 0.85, 'line-width': ['case', SEL, 3, 1.4] } }, below);
    map.getSource('area-labels').setData(labelsOf(k));
  }
  function selectArea() {
    for (const k of KINDS) if (map.getSource(areaSource(k))) map.removeFeatureState({ source: areaSource(k), ...(areaTiles ? { sourceLayer: `areas_${k}` } : {}) });
    if (state.area) map.setFeatureState(areaTarget(state.kind, state.area), { sel: true });
  }
  function fitArea() {
    const b = areaById[state.kind][state.area].bbox;
    map.fitBounds(b[0] <= b[2] ? [[b[0], b[1]], [b[2], b[3]]] : [[b[0], b[1]], [b[2] + 360, b[3]]], { padding: 40, maxZoom: 9 });
  }
  function setArea(id, ease) {
    state.area = id;
    if (mapReady) { selectArea(); if (id && ease) fitArea(); }
    applyFilters();
  }
  function setKind(k) {
    if (k === state.kind) return;
    state.kind = k; state.area = null;
    if (mapReady) { drawKind(k); selectArea(); }
    syncMapControls(); applyFilters();
  }
  function setNames(on) {
    state.names = on;
    if (mapReady) for (const l of ['areas-name', 'boxes-name']) if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', on ? 'visible' : 'none');
    syncMapControls(); writeHash();
  }
  function setGlobe(on) {
    state.globe = on;
    if (mapReady) map.setProjection({ type: on ? 'globe' : 'mercator' });
    syncMapControls(); writeHash();
    if (mapReady) map.once('render', () => renderList());
  }

  function fitTo(id) {
    const b = placeOf(byId[id]);
    if (b && b[0] <= b[2]) map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 40, maxZoom: 9, duration: 0 });
  }

  // A row hovered or opened lights its features by feature state; the style itself never changes.
  const lit = { id: null, targets: [] };
  function highlight(id) {
    for (const t of lit.targets) map.removeFeatureState(t, 'hl');
    lit.id = id; lit.targets = [];
    if (!id || !mapReady) return;
    const add = t => { map.setFeatureState(t, { hl: true }); lit.targets.push(t); };
    const o = pmtilesMode ? { source: 'outlines', sourceLayer: 'outlines' } : { source: 'outlines' };
    if (drawn.has(id)) for (const f of map.querySourceFeatures('outlines', { ...(pmtilesMode ? { sourceLayer: 'outlines' } : {}),
      filter: ['==', ['get', 'record_id'], id] })) if (f.id !== undefined) add({ ...o, id: f.id });
    const b = boxIds.indexOf(id);
    if (b >= 0) add({ source: 'boxes', id: b });
    wellRecords.forEach((ids, i) => { if (ids.has(id)) add({ source: 'wells', id: i }); });
  }

  function applyFilters() {
    renderList();
    syncFilterButtons();
    writeHash();
    if (!mapReady) return;
    const ids = records.filter(inArea).filter(matches).map(r => r.id);
    const idFilter = ['in', ['get', 'record_id'], ['literal', ids]];
    for (const [l, f] of Object.entries(LAYER_BASE)) map.setFilter(l, ['all', f, idFilter]);
    map.setFilter('boxes', idFilter);
    if (map.getLayer('boxes-name')) map.setFilter('boxes-name', idFilter);
    drawWells(true);
  }

  // ---- The list ---------------------------------------------------------------------------------
  const levelBadge = r => `${r.blocked_since ? `<span class="blocked" title="${esc(r.reason)}">blocked since ${esc(r.blocked_since.slice(0, 10))}</span>`
    : `<span class="lvl ${esc(r.level)}">${esc(r.level)}</span>`}${isStale(r) ? `<span class="stale" title="last checked ${esc(r.checked_at)}, more than ${STALE_DAYS} days ago">stale</span>` : ''}`;
  const inBag = id => state.pick.includes(id);
  const plusButton = r => `<button type="button" class="plus" aria-pressed="${inBag(r.id)}" aria-label="${inBag(r.id) ? 'In the bag' : 'Add to the bag'}: ${esc(r.title)}"></button>`;
  const rows = new Map();
  function rowOf(r) {
    let li = rows.get(r.id);
    if (li) return li;
    li = document.createElement('li'); li.dataset.id = r.id; li.tabIndex = 0;
    li.innerHTML = `${plusButton(r)}<div class="t"><span class="title">${esc(r.title)}</span><span class="p">${esc(r.publisher.name)}</span>
      <span class="m">${esc(r.kinds.join(', '))}${span(r) ? ` · <span class="yr">${esc(yearsLabel(r))}</span>` : ''}</span></div>
      <div class="s"><span class="badges">${levelBadge(r)}</span>${accessIcon(r.origin.access)}</div>`;
    li.querySelector('.plus').onclick = e => { e.stopPropagation(); toggleBag(r.id); };
    li.onclick = () => openRow(r.id);
    li.onkeydown = e => { if (e.key === 'Enter' && e.target === li) openRow(r.id); };
    li.onmouseenter = () => highlight(r.id);
    li.onmouseleave = () => highlight(state.sel);
    rows.set(r.id, li);
    return li;
  }
  let shown = { ids: [], noplace: [] };
  function renderList() {
    if (!mapReady) { $('count').textContent = ''; return; }
    renderChip();
    if (state.area) {
      const a = areaById[state.kind][state.area], inIt = records.filter(r => a.ids.includes(r.id) && matches(r)).sort(byTitle);
      shown = { ids: inIt.map(r => r.id), noplace: [] };
      $('count').textContent = `${inIt.length} dataset${inIt.length === 1 ? '' : 's'} in ${a.name}`;
      document.querySelector('#list > ul').replaceChildren(...inIt.map(rowOf));
      $('noplace').hidden = true; $('more').hidden = true;
      return;
    }
    const win = windowOf(), placed = [], noplace = [], outside = [];
    for (const r of records) {
      if (!matches(r)) continue;
      const b = placeOf(r);
      if (!b) { if (win.world) noplace.push(r); else outside.push(r); continue; }
      const rel = relation(b, win);
      if (rel) placed.push([rel, r]); else outside.push(r);
    }
    placed.sort((x, y) => (y[0] - x[0]) || byTitle(x[1], y[1]));
    noplace.sort(byTitle);
    shown = { ids: placed.map(p => p[1].id), noplace: noplace.map(r => r.id) };
    const n = placed.length + noplace.length;
    $('count').textContent = `${n} dataset${n === 1 ? '' : 's'} in this view`;
    document.querySelector('#list > ul').replaceChildren(...placed.map(p => rowOf(p[1])));
    $('noplace').hidden = !noplace.length;
    $('noplace').querySelector('ul').replaceChildren(...noplace.map(rowOf));
    const more = $('more');
    more.hidden = !(state.q && outside.length);
    if (!more.hidden) {
      more.innerHTML = `<button type="button">${outside.length} more outside this view</button>`;
      more.firstChild.onclick = () => showAll(outside);
    }
  }
  function renderChip() {
    const c = $('area-chip'), a = state.area && areaById[state.kind][state.area];
    c.hidden = !a;
    if (!a) return;
    c.innerHTML = `<span>${esc(a.name)}</span><button type="button" aria-label="Clear the area ${esc(a.name)}">✕</button>`;
    c.querySelector('button').onclick = () => setArea(null);
  }
  function showAll(list) {
    const bs = list.map(placeOf).filter(b => b && b[0] <= b[2]);
    if (!bs.length) { map.easeTo({ zoom: WORLD_ZOOM - 0.5 }); return; }
    map.fitBounds([[Math.min(...bs.map(b => b[0])), Math.min(...bs.map(b => b[1]))], [Math.max(...bs.map(b => b[2])), Math.max(...bs.map(b => b[3]))]],
      { padding: 40, maxZoom: 8 });
  }
  function refreshRow(id) {
    const li = rows.get(id);
    if (li) { const p = li.querySelector('.plus'); p.setAttribute('aria-pressed', String(inBag(id)));
      p.setAttribute('aria-label', `${inBag(id) ? 'In the bag' : 'Add to the bag'}: ${byId[id].title}`); }
    const d = $('detail').querySelector(`.plus[data-id="${CSS.escape(id)}"]`);
    if (d) { d.setAttribute('aria-pressed', String(inBag(id))); d.lastChild.textContent = inBag(id) ? 'In the bag' : 'Add to the bag'; }
  }

  // ---- Filters panel ----------------------------------------------------------------------------
  const allKinds = [...new Set(records.flatMap(r => r.kinds))].sort();
  const chip = (el, value, label, set) => {
    const c = document.createElement('button'); c.type = 'button'; c.className = 'chip'; c.textContent = label; c.dataset.value = value;
    c.onclick = () => { set().has(value) ? set().delete(value) : set().add(value); syncControls(); applyFilters(); };
    el.appendChild(c); return c;
  };
  const kindChips = allKinds.map(k => chip($('kinds'), k, k, () => state.kinds));
  const accessValues = Object.keys(ACCESS).filter(a => records.some(r => r.origin.access === a));
  const accessChips = accessValues.map(a => chip($('access'), a, ACCESS[a].label, () => state.access));
  const yearOf = v => /^\d{4}$/.test(v.trim()) ? Number(v) : null;
  $('minlevel').onchange = e => { state.minLevel = Number(e.target.value); applyFilters(); };
  $('from').oninput = e => { state.from = yearOf(e.target.value); applyFilters(); };
  $('to').oninput = e => { state.to = yearOf(e.target.value); applyFilters(); };
  $('dated').onchange = e => { state.dated = e.target.checked; applyFilters(); };
  $('starter').onchange = e => { state.starter = e.target.checked; applyFilters(); };
  $('starterfilter').hidden = !anyStarter;
  $('q').oninput = e => { state.q = e.target.value.trim().toLowerCase(); applyFilters(); };
  $('clear').onclick = () => { Object.assign(state, { kinds: new Set(), minLevel: 0, from: null, to: null, dated: false, access: new Set(), starter: false });
    syncControls(); applyFilters(); };
  const setFilters = open => {
    $('filters').hidden = !open;
    for (const b of [$('filters-btn'), $('filters-btn-sheet')]) b.setAttribute('aria-expanded', String(open));
    if (open) { closeDetail(true); $('side').classList.add('up'); }
  };
  $('filters-btn').onclick = $('filters-btn-sheet').onclick = () => setFilters($('filters').hidden);
  $('filters-done').onclick = () => setFilters(false);

  function syncControls() {
    kindChips.forEach(c => c.setAttribute('aria-pressed', String(state.kinds.has(c.dataset.value))));
    accessChips.forEach(c => c.setAttribute('aria-pressed', String(state.access.has(c.dataset.value))));
    $('minlevel').value = String(state.minLevel);
    if ($('q').value.trim().toLowerCase() !== state.q) $('q').value = state.q;
    for (const k of ['from', 'to']) if (yearOf($(k).value) !== state[k]) $(k).value = state[k] ?? '';
    $('dated').checked = state.dated;
    $('starter').checked = state.starter;
  }
  function syncFilterButtons() {
    const n = filterCount();
    for (const b of [$('filters-btn'), $('filters-btn-sheet')]) { const s = b.querySelector('.n'); s.hidden = !n; s.textContent = n; }
  }

  // ---- The detail: today's panel as plain sections ------------------------------------------------
  const day = s => new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  function openRow(id) {
    state.sel = id;
    setFilters(false);
    renderDetail(byId[id]);
    highlight(id);
    writeHash();
  }
  function closeDetail(quiet) {
    if (!state.sel && $('detail').hidden) return;
    state.sel = null; $('detail').hidden = true; $('list').hidden = false;
    highlight(null);
    if (!quiet) writeHash();
  }
  function renderDetail(r) {
    const d = $('detail'), geo = base + 'data/outlines.geojson', l = r.licence;
    const issues = (r.known_issues || []).map(x => `<li>${esc(x)}</li>`).join('');
    const region = [r.region && r.region.basin, r.region && r.region.country].filter(Boolean).join(', ');
    d.innerHTML = `
      <button type="button" class="back" aria-label="Back to the list"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>Back</button>
      <h2 class="title">${esc(r.title)}</h2>
      <p class="pub"><a href="${esc(r.publisher.url)}" target="_blank" rel="noopener">${esc(r.publisher.name)}</a> <span class="badges">${levelBadge(r)}</span> ${accessIcon(r.origin.access)}</p>
      <button type="button" class="plus wide" data-id="${esc(r.id)}" aria-pressed="${inBag(r.id)}"><span>${inBag(r.id) ? 'In the bag' : 'Add to the bag'}</span></button>
      <p class="summary">${esc(r.summary || '')}</p>
      <section class="when"><h3>When</h3><p>${r.period ? esc(`${r.period.start || 'start of record'} to ${r.period.end || 'today'}`) + (r.period.stated ? `</p><p class="stated">${esc(r.period.stated)}` : '') : 'Not stated by the publisher.'}</p></section>
      <section class="why"><h3>Why this level</h3><p><span class="reason">${esc(r.reason || 'never verified')}</span>${r.checked_at
        ? ` <span class="checked">checked ${esc(day(r.checked_at))}</span>${isStale(r) ? ` (stale: older than ${STALE_DAYS} days)` : ''}` : ''}</p></section>
      <section class="get"><h3>How to get it</h3><p>${esc((ACCESS[r.origin.access] || ACCESS.request).line)} <a href="${esc(r.origin.url)}" target="_blank" rel="noopener">The origin page</a>.</p></section>
      <section class="licence"><h3>Licence</h3><p>${esc(l.name)}${l.spdx ? ' (' + esc(l.spdx) + ')' : ''}; redistribution ${esc(l.redistribution)}, attribution ${esc(l.attribution)}.</p></section>
      <section class="holds"><h3>Holds</h3><p>${esc(r.kinds.join(', '))}${region ? `. ${esc(region)}` : ''}.</p></section>
      ${issues ? `<section class="issues"><h3>Known issues</h3><ul>${issues}</ul></section>` : ''}
      ${hasStarter(r) ? '<section class="starter"><h3>Starter project</h3><p class="hint">…</p></section>' : ''}
      <section class="qgis"><h3>Open in QGIS</h3><p>Layer → Add Layer → Vector, protocol HTTP, this address; filter on record_id.</p><pre><code>${esc(geo)}</code></pre></section>
      <section class="python"><h3>Read in Python</h3><pre><code>import json, urllib.request
fc = json.load(urllib.request.urlopen("${esc(geo)}"))
mine = [f for f in fc["features"] if f["properties"]["record_id"] == "${esc(r.id)}"]</code></pre></section>
      <p class="how"><a href="how.html">What the levels mean</a></p>`;
    d.querySelector('.back').onclick = () => closeDetail();
    d.querySelector('.plus').onclick = () => toggleBag(r.id);
    d.hidden = false; $('list').hidden = true; d.scrollTop = 0;
    if (hasStarter(r)) starterSection(d.querySelector('section.starter'), r);
  }

  // ---- Starter projects (E43), rewritten small: the pack's buttons, licence line, steps, manifest ----
  const APPS = { opendtect: 'OpendTect', resinsight: 'ResInsight', python: 'Python' };
  let packs = null;
  const loadPacks = () => packs = packs || fetch('data/starters.json').then(r => r.ok ? r.json() : { starters: [] })
    .then(d => Object.fromEntries(d.starters.map(p => [p.id, p])), () => ({}));
  const anchor = id => id.replaceAll('/', '__');
  const packLicence = l => [l.spdx || l.name, l.attribution === 'required' ? 'attribution required' : '', l.share_alike === true ? 'share-alike' : ''].filter(Boolean).join(' · ');
  const manifestName = p => anchor(p.id) + '.manifest.json';
  const sha256 = async buf => [...new Uint8Array(await crypto.subtle.digest('SHA-256', buf))].map(b => b.toString(16).padStart(2, '0')).join('');
  async function starterManifest(p) {
    const r = byId[p.record_id], assets = {};
    for (const t of p.targets) for (const a of t.artefacts) {
      const title = assets[a.path] ? assets[a.path].title : `${a.path} (${t.application} ${t.version})`;
      assets[a.path] = { href: a.href, title, 'file:size': a.bytes, 'file:checksum': '1220' + a.sha256 };
    }
    for (const [key, rel, title] of [['starter.json', anchor(p.id) + '.json', 'the pack document with its decision log (osd.starter/1)'],
      ['fidelity.json', p.fidelity, 'the fidelity record (osd.fidelity/1)']]) {
      const buf = await (await fetch('data/starters/' + rel)).arrayBuffer();
      assets[key] = { href: base + 'data/starters/' + rel, title, 'file:size': buf.byteLength, 'file:checksum': '1220' + await sha256(buf) };
    }
    const { sources, ...licence } = p.licence;
    const entry = { collection_id: collectionId(r.id), record_id: r.id, title: p.title, origin_url: r.origin.url,
      access: r.origin.access, licence, assets, coverage: 'complete' };
    if (r.known_issues && r.known_issues.length) entry.known_issues = [...r.known_issues];
    return { format: MANIFEST_FORMAT_4, created: now(), catalog_url: base + 'data/stac/catalog.json', selection: 'collections',
      entries: [entry], metadata: { catalog: { ...built.catalog } } };
  }
  async function starterSection(sec, r) {
    const all = await loadPacks();
    if (!sec.isConnected) return;
    const list = r.starters.map(id => all[id]).filter(Boolean);
    if (!list.length) { sec.remove(); return; }
    sec.innerHTML = '<h3>Starter project</h3>' + list.map(p => `<div class="pack" data-pack="${esc(p.id)}">
      <div class="apps">${p.targets.map((t, i) => `<button type="button" class="app" data-app="${esc(t.application)}" aria-pressed="${i === 0}">${esc(APPS[t.application] || t.application)} <span>${esc(t.version)}</span></button>`).join('')}</div>
      <p class="lic">${esc(packLicence(p.licence))} · <a href="starters.html#${esc(anchor(p.id))}-decisions">what we decided</a></p>
      <p class="steps"></p>
      <button type="button" class="starter-download">Download the pack manifest</button></div>`).join('');
    for (const el of sec.querySelectorAll('.pack')) {
      const p = all[el.dataset.pack];
      const steps = app => {
        const t = p.targets.find(t => t.application === app);
        el.querySelector('.steps').innerHTML = `1. download the pack manifest · 2. <code>osd get ${esc(manifestName(p))} --dest ${esc(anchor(p.record_id))}</code> · 3. run <code>${esc(t.import)}</code> (${esc(APPS[app] || app)} ${esc(t.version)})`;
        for (const b of el.querySelectorAll('.app')) b.setAttribute('aria-pressed', String(b.dataset.app === app));
      };
      el.querySelectorAll('.app').forEach(b => b.onclick = () => steps(b.dataset.app));
      steps(p.targets[0].application);
      el.querySelector('.starter-download').onclick = async () => save(await starterManifest(p), manifestName(p));
    }
  }

  // ---- The bag ----------------------------------------------------------------------------------
  // The manifest is the object the live page's select mode writes (E06; /4 when an entry is sold or
  // states terms, E19), which `osd manifest` writes for the same ids. The direct links are the files
  // the catalogue holds: mirror copies (mirror.json) and the verifier's assets of anonymous datasets.
  const MANIFEST_FORMAT = 'osd.manifest/1', MANIFEST_FORMAT_4 = 'osd.manifest/4';
  const LICENCE_FIELDS = ['name', 'spdx', 'url', 'redistribution', 'attribution', 'share_alike', 'statement', 'terms'];
  const ASSET_FIELDS = ['href', 'title', 'roles', 'file:size', 'file:checksum'];
  const collectionId = id => id.replaceAll('/', '--');
  const now = () => new Date().toISOString().replace(/\.\d+Z$/, 'Z');
  const pickKeys = (o, keys) => Object.fromEntries(keys.filter(k => k in o).map(k => [k, o[k]]));
  let collections = null, mirror = null;
  const loadCollections = () => collections = collections || fetch('data/collections.json').then(r => r.json())
    .then(d => Object.fromEntries(d.collections.map(c => [c.id, c])));
  const loadMirror = () => mirror = mirror || fetch('data/mirror.json').then(r => r.ok ? r.json() : { copies: [] })
    .then(d => d.copies || [], () => []);
  function noAssetsReason(r) {
    const a = r.origin.access;
    return a === 'registration' || a === 'request' ? `access ${a}: sign in or ask at the origin page; no file address is published to us`
      : a === 'purchase' ? 'access purchase: the publisher sells the files; buy them at the origin page'
      : 'the verifier has hashed no file with a fetch address for this record; get the files at the origin page';
  }
  function manifestEntry(r, col) {
    const e = { collection_id: collectionId(r.id), record_id: r.id, title: r.title, origin_url: r.origin.url,
      access: r.origin.access, licence: pickKeys(r.licence, LICENCE_FIELDS) };
    if (r.known_issues && r.known_issues.length) e.known_issues = [...r.known_issues];
    e.assets = Object.fromEntries(Object.entries((col && col.assets) || {}).map(([k, a]) => [k, pickKeys(a, ASSET_FIELDS)]));
    if (Object.keys(e.assets).length) e.coverage = 'sampled'; else e.unresolved = noAssetsReason(r);
    return e;
  }
  async function buildManifest() {
    const cols = await loadCollections();
    const entries = state.pick.map(id => manifestEntry(byId[id], cols[collectionId(id)]));
    const v4 = entries.some(e => e.access === 'purchase' || 'terms' in e.licence);
    const doc = { format: v4 ? MANIFEST_FORMAT_4 : MANIFEST_FORMAT, created: now(),
      catalog_url: base + 'data/stac/catalog.json', selection: 'collections', entries };
    if (v4) doc.metadata = { catalog: { ...built.catalog } };
    return doc;
  }
  function save(doc, name) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(doc, null, 2) + '\n'], { type: 'application/json' }));
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  async function filesOf(r) {
    const [cols, held] = await Promise.all([loadCollections(), loadMirror()]);
    const out = held.filter(c => c.record_id === r.id)
      .map(c => ({ name: c.path, href: c.href, bytes: c.bytes, sha256: c.sha256, where: 'our mirror' }));
    if (r.origin.access === 'anonymous') for (const [k, a] of Object.entries((cols[collectionId(r.id)] || {}).assets || {}))
      if (a.href && !out.some(o => o.href === a.href)) out.push({ name: k, href: a.href, bytes: a['file:size'],
        sha256: String(a['file:checksum'] || '').replace(/^1220/, ''), where: 'the publisher' });
    return out;
  }
  const bytes = n => n == null ? 'size not stated' : n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} kB`
    : n < 1073741824 ? `${(n / 1048576).toFixed(1)} MB` : `${(n / 1073741824).toFixed(2)} GB`;
  const licenceLine = l => `${l.name}${l.spdx ? ' (' + l.spdx + ')' : ''} · attribution ${l.attribution} · ${l.share_alike === true
    ? `share-alike: derived work must carry ${l.spdx || l.name}` : l.share_alike === false ? 'share-alike: no' : 'share-alike: not stated'}`;

  // ---- The Python file (E49): the text `osd script <ids>` writes, rule table T1-T8 of
  // docs/program/charters/E49-the-python-file-STRATEGY.md; the site test holds it equal to the golden file.
  const PY_INSTALL = 'pip install "osd[readers] @ git+https://github.com/ophiolite-labs/open-subsurface-data"';
  const PY_KEYWORDS = new Set(('False None True and as assert async await break class continue def del elif else except finally ' +
    'for from global if import in is lambda nonlocal not or pass raise return try while with yield osd').split(' '));
  const PY_MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
  const PY_READERS = [[['.las'], 'logs', 'well_logs', 'a table per well'], [['.csv'], 'tables', 'tables', 'a table per file'],
    [['.sgy', '.segy'], 'cubes', 'segy', 'headers per SEG-Y file']];
  const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
  function pyVariable(id, taken) {
    let v = id.slice(id.indexOf('/') + 1).toLowerCase().replace(/[^a-z0-9_]/g, '_');
    if (/^[0-9]/.test(v)) v = 'd_' + v;
    if (PY_KEYWORDS.has(v)) v += '_';
    let out = v;
    for (let n = 2; taken.has(out); n++) out = `${v}_${n}`;
    taken.add(out);
    return out;
  }
  function pyComment(r, assets) {
    const a = Object.values(assets);
    if (!a.length) return ({ registration: 'sign-in needed: left out, sign in at ', request: 'request needed: left out, ask at ',
      purchase: 'for sale: left out, see ' }[r.origin.access] || 'no file address known: left out, see ') + r.origin.url;
    const summed = a.filter(x => 'file:checksum' in x), m = summed.filter(x => x.alternate && Object.keys(x.alternate).length).length;
    const p = a.length - m, k = summed.length;
    const where = !p ? `${plural(m, 'file')} from our mirror` : !m ? `${plural(p, 'file')} from the publisher`
      : `${plural(a.length, 'file')}: ${m} from our mirror and ${p} from the publisher`;
    return `${where}, ${k === a.length ? 'checked' : !k ? 'no checksum recorded' : k + ' checked'}`;
  }
  async function pythonFile(today = new Date()) {
    const cols = await loadCollections(), taken = new Set();
    const ds = [...new Set(state.pick)].map(id => ({ id, assets: (cols[collectionId(id)] || {}).assets || {} }))
      .map(d => ({ ...d, code: `${pyVariable(d.id, taken)} = osd.get("${d.id}")`, why: pyComment(byId[d.id], d.assets) }));
    const width = Math.max(...ds.map(d => d.code.length)) + 2, name = d => d.code.split(' = ')[0];
    const lines = [`# open-subsurface-data, made ${today.getDate()} ${PY_MONTHS[today.getMonth()]} ${today.getFullYear()} for ${plural(ds.length, 'dataset')}`,
      `# ${PY_INSTALL}`, '', 'import osd', '', ...ds.map(d => d.code.padEnd(width) + '# ' + d.why), '', ...ds.map(d => `print(${name(d)})`)];
    for (const [ext, v, method, what] of PY_READERS) {
      const d = ds.find(x => Object.keys(x.assets).some(k => ext.some(e => k.toLowerCase().endsWith(e))));
      if (d) { lines.push('', `${v} = ${name(d)}.${method}()  # ${what}`, method === 'segy' ? `print(next(iter(${v}.values())))`
        : `print(next(iter(${v}.values())).head())`); break; }
    }
    return lines.join('\n') + '\n';
  }
  function saveText(text, name) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/x-python' }));
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  function toggleBag(id) {
    const i = state.pick.indexOf(id);
    if (i < 0) state.pick.push(id); else state.pick.splice(i, 1);
    refreshRow(id); renderBag(); writeHash();
  }
  const setBag = open => {
    $('bag').hidden = !open; $('bag-btn').setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('bag-open', open);
    if (open) renderBag();
  };
  $('bag-btn').onclick = () => setBag($('bag').hidden);
  function renderBag() {
    const n = state.pick.length;
    $('bag-btn').querySelector('.n').textContent = n;
    const b = $('bag');
    if (b.hidden) return;
    const items = state.pick.map(id => { const r = byId[id];
      return `<li data-id="${esc(id)}"><div class="h"><b>${esc(r.title)}</b><button type="button" class="x" aria-label="Remove ${esc(r.title)} from the bag">Remove</button></div>
        <p class="lic">${esc(licenceLine(r.licence))}</p>
        <p class="acc-line">${accessIcon(r.origin.access)} ${esc((ACCESS[r.origin.access] || ACCESS.request).line)}</p></li>`; }).join('');
    b.innerHTML = `<header><h2>Bag <span class="n">${n}</span></h2><button type="button" class="close" aria-label="Close the bag">✕</button></header>
      ${n ? `<ul class="items">${items}</ul>
      <button id="download" type="button" class="amber">Download the files</button>
      <button id="python" type="button" class="quiet">Get a Python file</button>
      <div id="files" hidden></div>`
      : '<p class="empty">Nothing in the bag yet. The green plus on a row adds a dataset.</p>'}`;
    b.querySelector('.close').onclick = () => setBag(false);
    b.querySelectorAll('.x').forEach(x => x.onclick = () => toggleBag(x.closest('li').dataset.id));
    if (n) { $('download').onclick = download; $('python').onclick = async () => saveText(await pythonFile(), 'osd_get.py'); }
  }
  async function download() {
    save(await buildManifest(), 'osd.manifest.json');
    const per = await Promise.all(state.pick.map(async id => [byId[id], await filesOf(byId[id])]));
    const f = $('files');
    if (!f) return;
    f.innerHTML = `<h3>The manifest</h3><p><code>osd.manifest.json</code> is saved. Run, in the same folder:</p>
      <pre><code>osd get osd.manifest.json --dest data</code></pre>
      <p class="hint">It fetches the files, checks each sha256 and writes ATTRIBUTION.md.</p>
      <h3>Direct links</h3><ul class="links">${per.map(([r, fs]) => `<li data-id="${esc(r.id)}"><b>${esc(r.title)}</b>${fs.length
        ? `<ul>${fs.map(x => `<li class="file"><a href="${esc(x.href)}" download>${esc(x.name)}</a> <span class="size">${esc(bytes(x.bytes))}</span> · from ${esc(x.where)}<br><span class="sha">sha256 <code>${esc(x.sha256)}</code></span></li>`).join('')}</ul>`
        : `<p class="none">${r.origin.access === 'registration' || r.origin.access === 'request'
          ? `Sign in at <a href="${esc(r.origin.url)}" target="_blank" rel="noopener">the publisher's page</a> to get the files: no file address is published to us.`
          : r.origin.access === 'purchase' ? `Buy the files at <a href="${esc(r.origin.url)}" target="_blank" rel="noopener">the publisher's page</a>.`
          : `No file address yet: get the files at <a href="${esc(r.origin.url)}" target="_blank" rel="noopener">the origin page</a>.`}</p>`}</li>`).join('')}</ul>`;
    f.hidden = false;
  }

  // ---- Phone: the list is a sheet under the map, pulled up by its head ---------------------------
  const sheet = $('side');
  $('grip').onclick = () => sheet.classList.toggle('up');
  let drag = null;
  $('sheet-head').addEventListener('pointerdown', e => { drag = { y: e.clientY }; });
  window.addEventListener('pointerup', e => {
    if (!drag) return;
    const dy = e.clientY - drag.y; drag = null;
    if (dy < -30) sheet.classList.add('up'); else if (dy > 30) sheet.classList.remove('up');
  });

  // A pasted or edited hash in the same tab applies too.
  window.addEventListener('hashchange', () => {
    const was = { kind: state.kind, globe: state.globe, names: state.names };
    const v = readHash(); syncControls(); syncMapControls();
    if (mapReady) {
      if (state.kind !== was.kind) drawKind(state.kind);
      selectArea();
      if (state.globe !== was.globe) map.setProjection({ type: state.globe ? 'globe' : 'mercator' });
      if (state.names !== was.names) for (const l of ['areas-name', 'boxes-name']) if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', state.names ? 'visible' : 'none');
    }
    applyFilters(); renderBag();
    if (state.sel) { renderDetail(byId[state.sel]); highlight(state.sel); } else closeDetail(true);
    for (const id of rows.keys()) refreshRow(id);
    if (v) map.jumpTo(v);
  });

  // For the site test and the console; not an API.
  window.osdShop = { listIds: () => [...shown.ids], noPlaceIds: () => [...shown.noplace], worldZoom: WORLD_ZOOM };

  syncControls();
  applyFilters();
  renderBag();
  if (state.sel) { renderDetail(byId[state.sel]); }
})();
