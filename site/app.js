/* Open Subsurface Data map. Static: reads what `make build` puts in data/ (records.json,
   outlines.geojson, and outlines.pmtiles or wellbores.geojson when the build produces them).
   No framework; one file on purpose (ENGINEERING.md, "surface"). The URL hash is the only state. */
(async function () {
  // Basemap: OSD-D3. Positron until a dark basemap without a key is confirmed; never add a key.
  const BASEMAP = 'https://tiles.openfreemap.org/styles/positron';
  const CLUSTER_BELOW_ZOOM = 7;
  const STALE_DAYS = 30;

  // data/files.txt lists what the build wrote, so optional files are known without a 404 probe.
  const files = (await fetch('data/files.txt').then(r => r.ok ? r.text() : '').catch(() => '')).split('\n');
  const has = f => files.includes(f);
  const pmtilesMode = has('outlines.pmtiles') && await new Promise(ok => {
    const s = document.createElement('script'); s.src = 'https://unpkg.com/pmtiles@4.5.0/dist/pmtiles.js';
    s.onload = () => ok(true); s.onerror = () => ok(false); document.head.appendChild(s);
  });

  const records = (await (await fetch('data/records.json')).json()).records;
  const outlines = pmtilesMode ? null : await (await fetch('data/outlines.geojson')).json();
  const wellPoints = has('wellbores.geojson')
    ? (await (await fetch('data/wellbores.geojson')).json()).features
    : (outlines ? outlines.features.filter(f => f.properties.kind === 'wellbore' && f.geometry.type === 'Point') : []);
  const byId = Object.fromEntries(records.map(r => [r.id, r]));
  const LEVEL = s => Number((s || 'L0').slice(1));
  const isStale = r => !!r.checked_at && Date.now() - Date.parse(r.checked_at) > STALE_DAYS * 864e5;
  const levelBadge = r => `<span class="lvl ${r.level}">${r.level}</span>${isStale(r) ? `<span class="stale" title="last checked ${esc(r.checked_at)}, more than ${STALE_DAYS} days ago">stale</span>` : ''}`;

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
  const DEFAULTS = { q: '', kinds: [], minLevel: 0, extents: true, approx: true, sel: null };
  const state = { ...DEFAULTS, kinds: new Set() };
  function readHash() {
    const h = new URLSearchParams(location.hash.slice(1));
    state.q = (h.get('q') || '').trim().toLowerCase();
    state.kinds = new Set((h.get('k') || '').split(',').filter(Boolean));
    state.minLevel = Math.max(0, Math.min(4, Number(h.get('l')) || 0));
    state.extents = h.get('ext') !== '0';
    state.approx = h.get('ph') !== '0';
    state.sel = byId[h.get('sel')] ? h.get('sel') : null;
    const m = (h.get('map') || '').split('/').map(Number);
    return m.length === 3 && m.every(Number.isFinite) ? { zoom: m[0], center: [m[2], m[1]] } : null;
  }
  function writeHash() {
    const h = new URLSearchParams();
    if (state.q) h.set('q', state.q);
    if (state.kinds.size) h.set('k', [...state.kinds].sort().join(','));
    if (state.minLevel) h.set('l', state.minLevel);
    if (!state.extents) h.set('ext', '0');
    if (!state.approx) h.set('ph', '0');
    if (state.sel) h.set('sel', state.sel);
    if (map.loaded() || moved) {
      const c = map.getCenter();
      h.set('map', `${map.getZoom().toFixed(2)}/${c.lat.toFixed(4)}/${c.lng.toFixed(4)}`);
    }
    const s = h.toString().replace(/%2F/g, '/').replace(/%2C/g, ',');
    history.replaceState(null, '', s ? '#' + s : location.pathname + location.search);
  }

  const view = readHash();
  let moved = !!view;

  if (pmtilesMode) maplibregl.addProtocol('pmtiles', new pmtiles.Protocol().tile);
  const map = new maplibregl.Map({
    container: 'map', style: BASEMAP,
    center: view ? view.center : [5, 55], zoom: view ? view.zoom : 3.2, attributionControl: { compact: false }
  });
  window.osdMap = map; // for the site test and the console; not an API
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'top-right');

  const allKinds = [...new Set(records.flatMap(r => r.kinds))].sort();

  function matches(r) {
    if (LEVEL(r.level) < state.minLevel) return false;
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
    // Clustered sources cannot be filtered per feature after clustering, so the wells source
    // gets the filtered points.
    map.getSource('wells').setData({ type: 'FeatureCollection',
      features: wellPoints.filter(f => idSet.has(f.properties.record_id) && (state.approx || !f.properties.approximate)) });
  }

  // line-dasharray takes no data expression in MapLibre 4, so derived and placeholder
  // outlines are two line layers each.
  const SURVEY = ['in', ['get', 'kind'], ['literal', ['survey-3d', 'survey-2d']]];
  const FIELD = ['in', ['get', 'kind'], ['literal', ['field', 'block']]];
  const DERIVED = ['!', ['get', 'approximate']];
  const PLACEHOLDER = ['==', ['get', 'approximate'], true];
  const LAYER_BASE = {
    'surveys-fill': SURVEY, 'surveys-line': ['all', SURVEY, DERIVED], 'surveys-dash': ['all', SURVEY, PLACEHOLDER],
    'fields-fill': FIELD, 'fields-line': ['all', FIELD, DERIVED], 'fields-dash': ['all', FIELD, PLACEHOLDER],
  };

  map.on('load', () => {
    // Outlines: PMTiles (source-layer "outlines", same properties as the GeoJSON) when the build
    // wrote data/outlines.pmtiles, else the one GeoJSON.
    const base = location.href.replace(/[#?].*$/, '').replace(/[^/]*$/, '');
    map.addSource('outlines', pmtilesMode
      ? { type: 'vector', url: 'pmtiles://' + base + 'data/outlines.pmtiles' }
      : { type: 'geojson', data: outlines });
    const src = pmtilesMode ? { source: 'outlines', 'source-layer': 'outlines' } : { source: 'outlines' };
    map.addSource('extents', { type: 'geojson', data: extents });
    map.addSource('wells', { type: 'geojson', data: { type: 'FeatureCollection', features: wellPoints },
      cluster: true, clusterMaxZoom: CLUSTER_BELOW_ZOOM - 1, clusterRadius: 40 });
    map.addLayer({ id: 'extents-fill', type: 'fill', source: 'extents', paint: { 'fill-color': '#6ea8fe', 'fill-opacity': 0.06 } });
    map.addLayer({ id: 'extents-line', type: 'line', source: 'extents', paint: { 'line-color': '#6ea8fe', 'line-width': 1, 'line-dasharray': [3, 3], 'line-opacity': 0.7 } });
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
    map.addLayer({ id: 'wells', type: 'circle', source: 'wells', filter: ['!', ['has', 'point_count']],
      paint: { 'circle-color': '#3dd68c', 'circle-radius': 4, 'circle-stroke-color': '#0f1419', 'circle-stroke-width': 1 } });

    for (const l of ['surveys-fill', 'fields-fill', 'wells', 'extents-fill']) {
      map.on('click', l, e => select(e.features[0].properties.record_id));
    }
    map.on('click', 'wells-cluster', async e => {
      const f = e.features[0];
      const zoom = await map.getSource('wells').getClusterExpansionZoom(f.properties.cluster_id);
      map.easeTo({ center: f.geometry.coordinates, zoom });
    });
    for (const l of ['surveys-fill', 'fields-fill', 'wells', 'wells-cluster', 'extents-fill']) {
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

  function syncControls() {
    for (const k of allKinds) chips[k].classList.toggle('on', state.kinds.has(k));
    $('minlevel').value = String(state.minLevel);
    $('extents').checked = state.extents;
    $('approx').checked = state.approx;
    if ($('q').value.trim().toLowerCase() !== state.q) $('q').value = state.q;
  }

  function renderList(ids) {
    const ul = document.querySelector('#list ul'); ul.innerHTML = '';
    $('count').textContent = `(${ids.length} of ${records.length})`;
    for (const id of ids) {
      const r = byId[id];
      const li = document.createElement('li'); li.className = id === state.sel ? 'sel' : '';
      li.dataset.id = id;
      li.innerHTML = `<span class="badges">${levelBadge(r)}</span><span class="t">${esc(r.title)}<span class="p">${esc(r.publisher.name)}</span></span>`;
      li.onclick = () => select(id, true);
      ul.appendChild(li);
    }
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

  function closeDetail() { $('detail').hidden = true; state.sel = null; renderList(visibleIds()); writeHash(); }

  function select(id, fly) {
    state.sel = id; const r = byId[id];
    renderList(visibleIds());
    writeHash();
    const d = $('detail'); d.hidden = false;
    const base = location.href.replace(/[#?].*$/, '').replace(/[^/]*$/, '');
    const geo = base + 'data/outlines.geojson';
    const issues = (r.known_issues || []).map(x => `<li>${esc(x)}</li>`).join('');
    d.innerHTML = `
      <span class="close" title="close">✕</span>
      <h3><span class="title">${esc(r.title)}</span> ${levelBadge(r)}</h3>
      <div style="color:var(--muted)">${esc(r.summary || '')}</div>
      <dl>
        <dt>Publisher</dt><dd><a href="${esc(r.publisher.url)}" target="_blank" rel="noopener">${esc(r.publisher.name)}</a></dd>
        <dt>Origin</dt><dd><a href="${esc(r.origin.url)}" target="_blank" rel="noopener">${esc(r.origin.url)}</a> (${esc(r.origin.access)})</dd>
        <dt>Licence</dt><dd>${esc(r.licence.name)}${r.licence.spdx ? ' (' + esc(r.licence.spdx) + ')' : ''}<br>redistribution ${esc(r.licence.redistribution)}, attribution ${esc(r.licence.attribution)}</dd>
        <dt>Holds</dt><dd>${r.kinds.map(esc).join(', ')}</dd>
        <dt>Region</dt><dd>${esc([r.region && r.region.basin, r.region && r.region.country].filter(Boolean).join(', ') || '—')}</dd>
        <dt>Checked</dt><dd>${esc(r.checked_at || 'not yet')}${isStale(r) ? ' (stale: older than ' + STALE_DAYS + ' days)' : ''}</dd>
      </dl>
      ${issues ? `<div><b>Known issues</b><ul>${issues}</ul></div>` : ''}
      <div class="cards">
        <div class="card"><b>Open in QGIS</b>Layer → Add Layer → Vector, protocol HTTP, this address; filter on record_id.<code>${esc(geo)}</code></div>
        <div class="card"><b>Read in Python</b><code>import json, urllib.request
fc = json.load(urllib.request.urlopen("${esc(geo)}"))
mine = [f for f in fc["features"] if f["properties"]["record_id"] == "${esc(r.id)}"]</code></div>
        <div class="card"><b>Get the data</b>Follow the origin link above. Retrieval by manifest and the Ophiolite source are chartered (E06, E09).</div>
      </div>
      <p class="how"><a href="how.html">What the levels mean, and these three cards explained</a></p>`;
    d.querySelector('.close').onclick = closeDetail;
    if (fly && r.region && r.region.bbox) map.fitBounds(r.region.bbox, { padding: 60, maxZoom: 9, duration: 700 });
  }

  // A pasted or edited hash in the same tab applies too.
  window.addEventListener('hashchange', () => {
    const v = readHash(); syncControls(); applyFilters();
    if (state.sel) select(state.sel, !v); else $('detail').hidden = true;
    if (v) map.jumpTo(v);
  });

  syncControls();
  applyFilters();
  if (state.sel) select(state.sel, !view);
})();
