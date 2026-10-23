/* Open Subsurface Data map. Static: reads what `make build` puts in data/ (records.json, and
   outlines.pmtiles when the build wrote it, else outlines.geojson; wellbores.geojson if present).
   No framework; one file on purpose (ENGINEERING.md, "surface"). The URL hash is the only state.
   Select mode (E06): tick datasets, download an osd.manifest/1 file (/4 when a dataset is sold or
   states terms, E19) that `osd get` reads. */
(async function () {
  // Basemap: OSD-D3. Positron until a dark basemap without a key is confirmed; never add a key.
  const BASEMAP = 'https://tiles.openfreemap.org/styles/positron';
  const CLUSTER_BELOW_ZOOM = 7;
  const STALE_DAYS = 30;

  // data/files.txt lists what the build wrote, so optional files are known without a 404 probe.
  const files = (await fetch('data/files.txt').then(r => r.ok ? r.text() : '').catch(() => '')).split('\n');
  const has = f => files.includes(f);
  // Tiles (E15) when the build wrote them and the server answers range requests (GitHub Pages does,
  // `python3 -m http.server` does not); otherwise the one GeoJSON, whole.
  const base = location.href.replace(/[#?].*$/, '').replace(/[^/]*$/, '');
  const tiles = has('outlines.pmtiles') && await new Promise(ok => {
    const s = document.createElement('script'); s.src = 'https://unpkg.com/pmtiles@4.5.0/dist/pmtiles.js';
    s.onload = () => ok(true); s.onerror = () => ok(false); document.head.appendChild(s);
  }) && new pmtiles.PMTiles(base + 'data/outlines.pmtiles');
  const pmtilesMode = !!tiles && await tiles.getHeader().then(() => true, () => false);

  const built = await (await fetch('data/records.json')).json();
  // Why each record is at its level (E27): `reasons` by id, the sentence `osd status` prints.
  const records = built.records.map(r => ({ ...r, reason: (built.reasons || {})[r.id] || '' }));
  const outlines = pmtilesMode ? null : await (await fetch('data/outlines.geojson')).json();
  // Clustering stays on the page: on the tile path the clustered source is fed the wellbores of the
  // tiles loaded so far (below CLUSTER_BELOW_ZOOM every tile keeps every point), keyed by feature_id.
  const tileWells = new Map();
  const wellPoints = has('wellbores.geojson')
    ? (await (await fetch('data/wellbores.geojson')).json()).features
    : (outlines ? outlines.features.filter(f => f.properties.kind === 'wellbore' && f.geometry.type === 'Point') : []);
  const byId = Object.fromEntries(records.map(r => [r.id, r]));
  const LEVEL = s => Number((s || 'L0').slice(1));
  const isStale = r => !!r.checked_at && Date.now() - Date.parse(r.checked_at) > STALE_DAYS * 864e5;
  // A blocked origin awards no level (OSD-D9): its badge says so instead of showing L0.
  const levelBadge = r => `${r.blocked_since ? `<span class="blocked" title="${esc(r.reason)}">blocked since ${esc(r.blocked_since.slice(0, 10))}</span>`
    : `<span class="lvl ${r.level}">${r.level}</span>`}${isStale(r) ? `<span class="stale" title="last checked ${esc(r.checked_at)}, more than ${STALE_DAYS} days ago">stale</span>` : ''}`;

  // Dataset extents: one rectangle per record bbox, drawn from the record, not the data.
  const extents = {
    type: 'FeatureCollection',
    features: records.filter(r => r.region && r.region.bbox).map(r => {
      const [w, s, e, n] = r.region.bbox;
      return { type: 'Feature', properties: { record_id: r.id, kind: 'dataset-extent', name: r.title,
        approximate: true, level: r.level, title: r.title, publisher: r.publisher.name, kinds: r.kinds },
        geometry: { type: 'Polygon', coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]] } };
    })
  };

  // State <-> URL hash. Defaults are left out so a plain link stays plain.
  //   #q=volve&k=field,survey-3d&l=2&ext=0&ph=0&sel=equinor/volve&map=6.2/58.40/2.00
  //   #pick=opm/norne,sodir/factpages   select mode with two datasets ticked (`pick=` alone: none yet)
  //   #t=1990-2000&dated=1   period overlaps 1990 to 2000 (either side may be empty), dated records only (E21)
  const DEFAULTS = { q: '', kinds: [], minLevel: 0, extents: true, approx: true, sel: null, pick: null,
    from: null, to: null, dated: false };
  const state = { ...DEFAULTS, kinds: new Set() };
  function readHash() {
    const h = new URLSearchParams(location.hash.slice(1));
    state.q = (h.get('q') || '').trim().toLowerCase();
    state.kinds = new Set((h.get('k') || '').split(',').filter(Boolean));
    state.minLevel = Math.max(0, Math.min(4, Number(h.get('l')) || 0));
    state.extents = h.get('ext') !== '0';
    state.approx = h.get('ph') !== '0';
    state.sel = byId[h.get('sel')] ? h.get('sel') : null;
    state.pick = h.has('pick') ? [...new Set(h.get('pick').split(',').filter(id => byId[id]))] : null;
    const t = /^(\d{4})?-(\d{4})?$/.exec(h.get('t') || '') || [];
    state.from = t[1] ? Number(t[1]) : null;
    state.to = t[2] ? Number(t[2]) : null;
    state.dated = h.get('dated') === '1';
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
    if (!state.extents) h.set('ext', '0');
    if (!state.approx) h.set('ph', '0');
    if (state.sel) h.set('sel', state.sel);
    if (state.pick) h.set('pick', state.pick.join(','));
    if (map.loaded() || moved) {
      const c = map.getCenter();
      h.set('map', `${map.getZoom().toFixed(2)}/${c.lat.toFixed(4)}/${c.lng.toFixed(4)}`);
    }
    const s = h.toString().replace(/%2F/g, '/').replace(/%2C/g, ',');
    history.replaceState(null, '', s ? '#' + s : location.pathname + location.search);
  }

  const view = readHash();
  let moved = !!view;

  if (pmtilesMode) {
    const protocol = new pmtiles.Protocol(); protocol.add(tiles); // reuses the header already read
    maplibregl.addProtocol('pmtiles', protocol.tile);
  }
  const map = new maplibregl.Map({
    container: 'map', style: BASEMAP,
    center: view ? view.center : [5, 55], zoom: view ? view.zoom : 3.2, attributionControl: { compact: false }
  });
  window.osdMap = map; // for the site test and the console; not an API
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'top-right');

  const allKinds = [...new Set(records.flatMap(r => r.kinds))].sort();

  // Period (E21): the publisher's stated interval, by year. Only a start runs to today; only an end
  // runs from the start of record. Undated records pass the window unless `dated` hides them.
  const year = s => s ? Number(String(s).slice(0, 4)) : null;
  const span = r => r.period && (r.period.start || r.period.end)
    ? [year(r.period.start) ?? -Infinity, year(r.period.end) ?? new Date().getUTCFullYear()] : null;
  const yearsLabel = r => {
    const [a, b] = [year(r.period.start), year(r.period.end)];
    return a === b ? String(a) : `${a ?? ''}–${b ?? 'today'}`;
  };

  function matches(r) {
    if (LEVEL(r.level) < state.minLevel) return false;
    const p = span(r);
    if (state.dated && !p) return false;
    if (p && ((state.to !== null && p[0] > state.to) || (state.from !== null && p[1] < state.from))) return false;
    if (state.kinds.size && !r.kinds.some(k => state.kinds.has(k))) return false;
    if (state.q) {
      const hay = [r.title, r.publisher.name, r.region && r.region.basin, r.region && r.region.country, r.id].join(' ').toLowerCase();
      if (!hay.includes(state.q)) return false;
    }
    return true;
  }

  function visibleIds() { return records.filter(matches).map(r => r.id); }

  let ready = false;
  function applyFilters() {
    const ids = visibleIds();
    renderList(ids);
    writeHash();
    if (!ready) return;
    const idSet = new Set(ids);
    const idFilter = ['in', ['get', 'record_id'], ['literal', ids]];
    const approxFilter = state.approx ? true : ['!', ['get', 'approximate']];
    for (const l of Object.keys(LAYER_BASE)) {
      map.setFilter(l, ['all', LAYER_BASE[l], idFilter, approxFilter]);
    }
    for (const l of ['extents-fill', 'extents-line']) {
      map.setLayoutProperty(l, 'visibility', state.extents ? 'visible' : 'none');
      map.setFilter(l, ['all', idFilter]);
    }
    map.setFilter('picked-line', ['in', ['get', 'record_id'], ['literal', state.pick || []]]);
    // Clustered sources cannot be filtered per feature after clustering, so the wells source
    // gets the filtered points.
    if (pmtilesMode) map.setFilter('wells-tiles', ['all', WELL, idFilter, approxFilter]);
    const points = pmtilesMode ? [...tileWells.values()] : wellPoints;
    map.getSource('wells').setData({ type: 'FeatureCollection',
      features: points.filter(f => idSet.has(f.properties.record_id) && (state.approx || !f.properties.approximate)) });
  }

  // line-dasharray takes no data expression in MapLibre 4, so derived and placeholder
  // outlines are two line layers each.
  const SURVEY = ['in', ['get', 'kind'], ['literal', ['survey-3d', 'survey-2d']]];
  const FIELD = ['in', ['get', 'kind'], ['literal', ['field', 'block']]];
  const DERIVED = ['!', ['get', 'approximate']];
  const PLACEHOLDER = ['==', ['get', 'approximate'], true];
  const WELL = ['all', ['==', ['get', 'kind'], 'wellbore'], ['==', ['geometry-type'], 'Point']];
  const LAYER_BASE = {
    'surveys-fill': SURVEY, 'surveys-line': ['all', SURVEY, DERIVED], 'surveys-dash': ['all', SURVEY, PLACEHOLDER],
    'fields-fill': FIELD, 'fields-line': ['all', FIELD, DERIVED], 'fields-dash': ['all', FIELD, PLACEHOLDER],
  };

  map.on('load', () => {
    // Outlines: PMTiles (source-layer "outlines", same properties as the GeoJSON) when the build
    // wrote data/outlines.pmtiles, else the one GeoJSON.
    // feature_id is the tile feature id (promoteId), as it is the GeoJSON feature's identity.
    map.addSource('outlines', pmtilesMode
      ? { type: 'vector', url: 'pmtiles://' + base + 'data/outlines.pmtiles', promoteId: { outlines: 'feature_id' } }
      : { type: 'geojson', data: outlines });
    const src = pmtilesMode ? { source: 'outlines', 'source-layer': 'outlines' } : { source: 'outlines' };
    map.addSource('extents', { type: 'geojson', data: extents });
    map.addSource('wells', { type: 'geojson', data: { type: 'FeatureCollection', features: wellPoints },
      cluster: true, clusterMaxZoom: CLUSTER_BELOW_ZOOM - 1, clusterRadius: 40 });
    map.addLayer({ id: 'extents-fill', type: 'fill', source: 'extents', paint: { 'fill-color': '#6ea8fe', 'fill-opacity': 0.06 } });
    map.addLayer({ id: 'extents-line', type: 'line', source: 'extents', paint: { 'line-color': '#6ea8fe', 'line-width': 1, 'line-dasharray': [3, 3], 'line-opacity': 0.7 } });
    map.addLayer({ id: 'picked-line', type: 'line', source: 'extents', filter: ['in', ['get', 'record_id'], ['literal', []]], paint: { 'line-color': '#ffffff', 'line-width': 2.5 } });
    map.addLayer({ id: 'fields-fill', type: 'fill', ...src, filter: LAYER_BASE['fields-fill'], paint: { 'fill-color': '#e5484d', 'fill-opacity': 0.18 } });
    map.addLayer({ id: 'fields-line', type: 'line', ...src, filter: LAYER_BASE['fields-line'], paint: { 'line-color': '#e5484d', 'line-width': 2 } });
    map.addLayer({ id: 'fields-dash', type: 'line', ...src, filter: LAYER_BASE['fields-dash'], paint: { 'line-color': '#e5484d', 'line-width': 2, 'line-dasharray': [2, 2] } });
    map.addLayer({ id: 'surveys-fill', type: 'fill', ...src, filter: LAYER_BASE['surveys-fill'], paint: { 'fill-color': '#f2a93b', 'fill-opacity': 0.2 } });
    map.addLayer({ id: 'surveys-line', type: 'line', ...src, filter: LAYER_BASE['surveys-line'], paint: { 'line-color': '#f2a93b', 'line-width': 2 } });
    map.addLayer({ id: 'surveys-dash', type: 'line', ...src, filter: LAYER_BASE['surveys-dash'], paint: { 'line-color': '#f2a93b', 'line-width': 2, 'line-dasharray': [2, 2] } });
    map.addLayer({ id: 'wells-cluster', type: 'circle', source: 'wells', filter: ['has', 'point_count'],
      paint: { 'circle-color': '#3dd68c', 'circle-opacity': 0.85, 'circle-stroke-color': '#0f1419', 'circle-stroke-width': 1,
        'circle-radius': ['step', ['get', 'point_count'], 10, 50, 14, 500, 19, 5000, 25] } });
    if (map.getStyle().glyphs) map.addLayer({ id: 'wells-count', type: 'symbol', source: 'wells', filter: ['has', 'point_count'],
      layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-size': 11, 'text-font': ['Noto Sans Regular'] },
      paint: { 'text-color': '#0f1419' } });
    const WELL_PAINT = { 'circle-color': '#3dd68c', 'circle-radius': 4, 'circle-stroke-color': '#0f1419', 'circle-stroke-width': 1 };
    // On the tile path single wells come from the tiles from CLUSTER_BELOW_ZOOM up (exact positions);
    // below it from the clustered source, like every cluster.
    map.addLayer({ id: 'wells', type: 'circle', source: 'wells', filter: ['!', ['has', 'point_count']], paint: WELL_PAINT,
      ...(pmtilesMode ? { maxzoom: CLUSTER_BELOW_ZOOM } : {}) });
    if (pmtilesMode) {
      map.addLayer({ id: 'wells-tiles', type: 'circle', ...src, filter: WELL, minzoom: CLUSTER_BELOW_ZOOM, paint: WELL_PAINT });
      let fresh = false;
      map.on('sourcedata', e => { if (e.sourceId === 'outlines' && e.tile) fresh = true; });
      map.on('idle', () => {
        if (!fresh || map.getZoom() >= CLUSTER_BELOW_ZOOM) return;
        fresh = false;
        const before = tileWells.size;
        for (const f of map.querySourceFeatures('outlines', { sourceLayer: 'outlines', filter: WELL })) {
          const p = f.properties;
          if (!tileWells.has(p.feature_id)) tileWells.set(p.feature_id, { type: 'Feature', geometry: f.geometry,
            properties: { record_id: p.record_id, kind: p.kind, name: p.name, approximate: p.approximate, feature_id: p.feature_id } });
        }
        if (tileWells.size > before) applyFilters();
      });
    }

    for (const l of ['surveys-fill', 'fields-fill', 'wells', 'extents-fill', ...(pmtilesMode ? ['wells-tiles'] : [])]) {
      map.on('click', l, e => state.pick ? tick(e.features[0].properties.record_id) : select(e.features[0].properties.record_id));
    }
    map.on('click', 'wells-cluster', async e => {
      const f = e.features[0];
      const zoom = await map.getSource('wells').getClusterExpansionZoom(f.properties.cluster_id);
      map.easeTo({ center: f.geometry.coordinates, zoom });
    });
    for (const l of ['surveys-fill', 'fields-fill', 'wells', 'wells-cluster', 'extents-fill', ...(pmtilesMode ? ['wells-tiles'] : [])]) {
      map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer');
      map.on('mouseleave', l, () => map.getCanvas().style.cursor = '');
    }
    map.on('moveend', () => { moved = true; writeHash(); });
    ready = true;
    applyFilters();
  });

  // Controls
  const kindsEl = document.getElementById('kinds');
  const chips = {};
  for (const k of allKinds) {
    const c = document.createElement('span'); c.className = 'chip'; c.textContent = k; c.dataset.kind = k;
    c.onclick = () => { state.kinds.has(k) ? state.kinds.delete(k) : state.kinds.add(k); syncControls(); applyFilters(); };
    kindsEl.appendChild(c); chips[k] = c;
  }
  const $ = id => document.getElementById(id);
  $('minlevel').onchange = e => { state.minLevel = Number(e.target.value); applyFilters(); };
  $('extents').onchange = e => { state.extents = e.target.checked; applyFilters(); };
  $('approx').onchange = e => { state.approx = e.target.checked; applyFilters(); };
  $('q').oninput = e => { state.q = e.target.value.trim().toLowerCase(); applyFilters(); };
  // A year counts once it has four digits; a half-typed one leaves that side open.
  const yearOf = v => /^\d{4}$/.test(v.trim()) ? Number(v) : null;
  $('from').oninput = e => { state.from = yearOf(e.target.value); applyFilters(); };
  $('to').oninput = e => { state.to = yearOf(e.target.value); applyFilters(); };
  $('dated').onchange = e => { state.dated = e.target.checked; applyFilters(); };

  function syncControls() {
    for (const k of allKinds) chips[k].classList.toggle('on', state.kinds.has(k));
    $('minlevel').value = String(state.minLevel);
    $('extents').checked = state.extents;
    $('approx').checked = state.approx;
    if ($('q').value.trim().toLowerCase() !== state.q) $('q').value = state.q;
    for (const k of ['from', 'to']) if (yearOf($(k).value) !== state[k]) $(k).value = state[k] ?? '';
    $('dated').checked = state.dated;
  }

  function renderList(ids) {
    const ul = document.querySelector('#list ul'); ul.innerHTML = '';
    $('count').textContent = `(${ids.length} of ${records.length})`;
    for (const id of ids) {
      const r = byId[id];
      const li = document.createElement('li'); li.className = id === state.sel ? 'sel' : '';
      li.dataset.id = id;
      const box = state.pick ? `<input type="checkbox" class="tick" aria-label="select ${esc(r.title)}"${state.pick.includes(id) ? ' checked' : ''}>` : '';
      li.innerHTML = `${box}<span class="badges">${levelBadge(r)}</span><span class="t">${esc(r.title)}<span class="p">${esc(r.publisher.name)}${span(r) ? `<span class="yr">${esc(yearsLabel(r))}</span>` : ''}</span></span>`;
      li.onclick = e => { if (state.pick) { e.preventDefault(); tick(id); } else select(id, true); };
      ul.appendChild(li);
    }
  }

  // "23 Oct 2026": the day the verifier established the level, in UTC as checked_at states it.
  const day = s => new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });

  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

  function closeDetail() { $('detail').hidden = true; state.sel = null; renderList(visibleIds()); writeHash(); }

  function select(id, fly) {
    if (state.pick) return;
    state.sel = id; const r = byId[id];
    renderList(visibleIds());
    writeHash();
    const d = $('detail'); d.hidden = false;
    const geo = base + 'data/outlines.geojson';
    const issues = (r.known_issues || []).map(x => `<li>${esc(x)}</li>`).join('');
    d.innerHTML = `
      <span class="close" title="close">✕</span>
      <h3><span class="title">${esc(r.title)}</span> ${levelBadge(r)}</h3>
      <div style="color:var(--muted)">${esc(r.summary || '')}</div>
      <dl>
        <dt>Why this level</dt><dd class="why"><span class="reason">${esc(r.reason || 'never verified')}</span>${r.checked_at
          ? `<br><span class="checked">checked ${esc(day(r.checked_at))}</span>${isStale(r) ? ` (stale: older than ${STALE_DAYS} days)` : ''}` : ''}</dd>
        <dt>Publisher</dt><dd><a href="${esc(r.publisher.url)}" target="_blank" rel="noopener">${esc(r.publisher.name)}</a></dd>
        <dt>Origin</dt><dd><a href="${esc(r.origin.url)}" target="_blank" rel="noopener">${esc(r.origin.url)}</a> (${esc(r.origin.access)})</dd>
        <dt>Licence</dt><dd>${esc(r.licence.name)}${r.licence.spdx ? ' (' + esc(r.licence.spdx) + ')' : ''}<br>redistribution ${esc(r.licence.redistribution)}, attribution ${esc(r.licence.attribution)}</dd>
        <dt>Holds</dt><dd>${r.kinds.map(esc).join(', ')}</dd>
        <dt>When</dt><dd class="when">${r.period ? esc(`${r.period.start || 'start of record'} to ${r.period.end || 'today'}`) + (r.period.stated ? '<br>' + esc(r.period.stated) : '') : 'not stated by the publisher'}</dd>
        <dt>Region</dt><dd>${esc([r.region && r.region.basin, r.region && r.region.country].filter(Boolean).join(', ') || '—')}</dd>
      </dl>
      ${issues ? `<div><b>Known issues</b><ul>${issues}</ul></div>` : ''}
      <div class="cards">
        <div class="card"><b>Open in QGIS</b>Layer → Add Layer → Vector, protocol HTTP, this address; filter on record_id.<code>${esc(geo)}</code></div>
        <div class="card"><b>Read in Python</b><code>import json, urllib.request
fc = json.load(urllib.request.urlopen("${esc(geo)}"))
mine = [f for f in fc["features"] if f["properties"]["record_id"] == "${esc(r.id)}"]</code></div>
        <div class="card"><b>Get the data</b>Follow the origin link above, or press Select above the list, tick datasets and download a manifest for osd get.</div>
      </div>
      <p class="how"><a href="how.html">What the levels mean, and these three cards explained</a></p>`;
    d.querySelector('.close').onclick = closeDetail;
    if (fly && r.region && r.region.bbox) map.fitBounds(r.region.bbox, { padding: 60, maxZoom: 9, duration: 700 });
  }

  // ---- Select mode (E06 slice 2). Deletable: this block, the `pick` hash key, #pickmode, #basket,
  // the picked-line layer and the tick() calls. The file it writes is osd.manifest/1 as
  // src/osd/manifest.py writes it for a Collection selection (schema/manifest.schema.json), or /4 with
  // the catalogue snapshot when an entry is sold or states terms (E19); the site test checks the two
  // agree entry for entry and that `osd get` reads it. `terms` is copied whole, as the record states it.
  const MANIFEST_FORMAT = 'osd.manifest/1';
  const MANIFEST_FORMAT_4 = 'osd.manifest/4';
  const LICENCE_FIELDS = ['name', 'spdx', 'url', 'redistribution', 'attribution', 'share_alike', 'statement', 'terms'];
  const ASSET_FIELDS = ['href', 'title', 'roles', 'file:size', 'file:checksum'];
  const collectionId = id => id.replaceAll('/', '--');
  let collections = null; // data/collections.json, fetched on the first tick: assets are the verifier's files
  const loadCollections = () => collections = collections || fetch('data/collections.json').then(r => r.json())
    .then(d => Object.fromEntries(d.collections.map(c => [c.id, c])));
  const pick = (o, keys) => Object.fromEntries(keys.filter(k => k in o).map(k => [k, o[k]]));
  const licenceLabel = l => l.spdx || l.name;

  // The manifest's `unresolved` repeats what `osd manifest` writes (src/osd/manifest.py), which goes by
  // access; what the person reads in the basket is the verifier's reason once the record was checked.
  const whyNoFiles = r => r.checked_at && LEVEL(r.level) < 2 && r.reason ? r.reason : noAssetsReason(r);
  function noAssetsReason(r) {
    const a = r.origin.access;
    return a === 'registration' || a === 'request'
      ? `access ${a}: sign in or ask at the origin page; no file address is published to us`
      : a === 'purchase' ? 'access purchase: the publisher sells the files; buy them at the origin page'
      : 'the verifier has hashed no file with a fetch address for this record; get the files at the origin page';
  }

  function manifestEntry(r, col) {
    const e = { collection_id: collectionId(r.id), record_id: r.id, title: r.title, origin_url: r.origin.url,
      access: r.origin.access, licence: pick(r.licence, LICENCE_FIELDS) };
    if (r.known_issues && r.known_issues.length) e.known_issues = [...r.known_issues];
    e.assets = Object.fromEntries(Object.entries((col && col.assets) || {}).map(([k, a]) => [k, pick(a, ASSET_FIELDS)]));
    if (Object.keys(e.assets).length) e.coverage = 'sampled'; else e.unresolved = noAssetsReason(r);
    return e;
  }

  async function buildManifest() {
    const cols = await loadCollections();
    const entries = state.pick.map(id => manifestEntry(byId[id], cols[collectionId(id)]));
    const v4 = entries.some(e => e.access === 'purchase' || 'terms' in e.licence);
    const doc = { format: v4 ? MANIFEST_FORMAT_4 : MANIFEST_FORMAT, created: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
      catalog_url: base + 'data/stac/catalog.json', selection: 'collections', entries };
    if (v4) doc.metadata = { catalog: { ...built.catalog } };
    return doc;
  }

  async function download() {
    const doc = await buildManifest();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(doc, null, 2) + '\n'], { type: 'application/json' }));
    a.download = 'osd.manifest.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  function setPickMode(on) {
    state.pick = on ? (state.pick || []) : null;
    if (on && state.sel) { state.sel = null; $('detail').hidden = true; }
    applyFilters(); renderBasket();
  }

  function tick(id) {
    const i = state.pick.indexOf(id);
    if (i < 0) state.pick.push(id); else state.pick.splice(i, 1);
    applyFilters(); renderBasket();
  }

  // What the person sees before the download: per dataset its licence, the publisher's statement
  // verbatim (or that none is stated), the stated terms (E19), the files and their digests or the to-do;
  // then share-alike.
  function renderBasket() {
    const b = $('basket'), on = !!state.pick;
    b.hidden = !on;
    $('pickmode').textContent = on ? 'Done' : 'Select';
    $('pickmode').classList.toggle('on', on);
    if (!on) return;
    if (!state.pick.length) {
      b.innerHTML = `<h2>Selected (0)</h2><p class="hint">Tick datasets in the list or on the map. The download is a manifest: <code>osd get osd.manifest.json --dest data</code> fetches the files and checks their sha256.</p>`;
      return;
    }
    const items = state.pick.map(id => {
      const r = byId[id], l = r.licence;
      const sa = l.share_alike === true ? `share-alike: derived work must carry ${esc(licenceLabel(l))}`
        : l.share_alike === false ? 'share-alike: no' : 'share-alike: not stated';
      return `<li data-id="${esc(id)}"><b>${esc(r.title)}</b> <span class="x" title="remove">✕</span>
        <div class="lic">${esc(l.name)}${l.spdx ? ' (' + esc(l.spdx) + ')' : ''} · attribution ${esc(l.attribution)} · ${sa}</div>
        ${l.terms ? `<div class="lic terms">terms, as the record states them: ${esc(l.terms.stated)}</div>` : ''}
        ${l.statement ? `<blockquote class="stmt">${esc(l.statement)}</blockquote>` : '<div class="stmt none">No attribution statement stated by the publisher in the record.</div>'}
        <div class="files" data-files="${esc(id)}">files: …</div></li>`;
    }).join('');
    const shared = {};
    for (const id of state.pick) if (byId[id].licence.share_alike === true) {
      const k = licenceLabel(byId[id].licence); shared[k] = (shared[k] || 0) + 1;
    }
    const saLines = Object.entries(shared).sort().map(([lic, n]) =>
      `<p class="sa">${n} item${n > 1 ? 's' : ''} require${n === 1 ? 's' : ''} derived work to carry ${esc(lic)}.</p>`).join('');
    b.innerHTML = `<h2>Selected (${state.pick.length})</h2><ul>${items}</ul>
      ${saLines || '<p class="sa none">No selected item states share-alike.</p>'}
      <div class="actions"><button id="download" type="button">Download osd.manifest.json</button>
      <p class="hint">Then <code>osd get osd.manifest.json --dest data</code>: fetches the files, checks each sha256, writes ATTRIBUTION.md. Files are the ones the verifier sampled, not the whole dataset.</p></div>`;
    b.querySelectorAll('li .x').forEach(x => x.onclick = () => tick(x.closest('li').dataset.id));
    $('download').onclick = download;
    loadCollections().then(cols => {
      for (const el of b.querySelectorAll('[data-files]')) {
        const id = el.dataset.files, r = byId[id], n = Object.keys((cols[collectionId(id)] || {}).assets || {}).length;
        el.textContent = n ? `${n} file${n > 1 ? 's' : ''} with the verifier's sha256 (a sample)` : `to-do: ${whyNoFiles(r)}`;
        el.classList.toggle('todo', !n);
      }
    });
  }

  $('pickmode').onclick = () => setPickMode(!state.pick);

  // A pasted or edited hash in the same tab applies too.
  window.addEventListener('hashchange', () => {
    const v = readHash(); syncControls(); applyFilters(); renderBasket();
    if (state.sel && !state.pick) select(state.sel, !v); else $('detail').hidden = true;
    if (v) map.jumpTo(v);
  });

  syncControls();
  applyFilters();
  renderBasket();
  if (state.sel && !state.pick) select(state.sel, !view);
})();
