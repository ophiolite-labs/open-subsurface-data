/* Open Subsurface Data map. Static: reads data/records.json and data/outlines.geojson
   produced by `make build`. No framework; one file on purpose (ENGINEERING.md, "surface"). */
(async function () {
  const [recordsRes, outlinesRes] = await Promise.all([fetch('data/records.json'), fetch('data/outlines.geojson')]);
  const records = (await recordsRes.json()).records;
  const outlines = await outlinesRes.json();
  const byId = Object.fromEntries(records.map(r => [r.id, r]));
  const LEVEL = s => Number((s || 'L0').slice(1));

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

  const map = new maplibregl.Map({
    container: 'map', style: 'https://tiles.openfreemap.org/styles/positron',
    center: [5, 55], zoom: 3.2, attributionControl: { compact: false }
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'top-right');

  const state = { kinds: new Set(), minLevel: 0, extents: true, approx: true, q: '', sel: null };
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

  function applyFilters() {
    const ids = visibleIds();
    const idFilter = ['in', ['get', 'record_id'], ['literal', ids]];
    const approxFilter = state.approx ? true : ['!', ['get', 'approximate']];
    for (const l of Object.keys(LAYER_BASE)) {
      map.setFilter(l, ['all', LAYER_BASE[l], idFilter, approxFilter]);
    }
    for (const l of ['extents-fill', 'extents-line']) {
      map.setLayoutProperty(l, 'visibility', state.extents ? 'visible' : 'none');
      map.setFilter(l, ['all', idFilter]);
    }
    renderList(ids);
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
    'wells': ['==', ['get', 'kind'], 'wellbore'],
  };

  map.on('load', () => {
    map.addSource('outlines', { type: 'geojson', data: outlines });
    map.addSource('extents', { type: 'geojson', data: extents });
    map.addLayer({ id: 'extents-fill', type: 'fill', source: 'extents', paint: { 'fill-color': '#6ea8fe', 'fill-opacity': 0.06 } });
    map.addLayer({ id: 'extents-line', type: 'line', source: 'extents', paint: { 'line-color': '#6ea8fe', 'line-width': 1, 'line-dasharray': [3, 3], 'line-opacity': 0.7 } });
    map.addLayer({ id: 'fields-fill', type: 'fill', source: 'outlines', filter: LAYER_BASE['fields-fill'], paint: { 'fill-color': '#e5484d', 'fill-opacity': 0.18 } });
    map.addLayer({ id: 'fields-line', type: 'line', source: 'outlines', filter: LAYER_BASE['fields-line'], paint: { 'line-color': '#e5484d', 'line-width': 2 } });
    map.addLayer({ id: 'fields-dash', type: 'line', source: 'outlines', filter: LAYER_BASE['fields-dash'], paint: { 'line-color': '#e5484d', 'line-width': 2, 'line-dasharray': [2, 2] } });
    map.addLayer({ id: 'surveys-fill', type: 'fill', source: 'outlines', filter: LAYER_BASE['surveys-fill'], paint: { 'fill-color': '#f2a93b', 'fill-opacity': 0.2 } });
    map.addLayer({ id: 'surveys-line', type: 'line', source: 'outlines', filter: LAYER_BASE['surveys-line'], paint: { 'line-color': '#f2a93b', 'line-width': 2 } });
    map.addLayer({ id: 'surveys-dash', type: 'line', source: 'outlines', filter: LAYER_BASE['surveys-dash'], paint: { 'line-color': '#f2a93b', 'line-width': 2, 'line-dasharray': [2, 2] } });
    map.addLayer({ id: 'wells', type: 'circle', source: 'outlines', filter: LAYER_BASE['wells'], paint: { 'circle-color': '#3dd68c', 'circle-radius': 4, 'circle-stroke-color': '#0f1419', 'circle-stroke-width': 1 } });

    for (const l of ['surveys-fill', 'fields-fill', 'wells', 'extents-fill']) {
      map.on('click', l, e => select(e.features[0].properties.record_id));
      map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer');
      map.on('mouseleave', l, () => map.getCanvas().style.cursor = '');
    }
    applyFilters();
  });

  // Controls
  const kindsEl = document.getElementById('kinds');
  for (const k of allKinds) {
    const c = document.createElement('span'); c.className = 'chip'; c.textContent = k;
    c.onclick = () => { c.classList.toggle('on'); state.kinds.has(k) ? state.kinds.delete(k) : state.kinds.add(k); applyFilters(); };
    kindsEl.appendChild(c);
  }
  document.getElementById('minlevel').onchange = e => { state.minLevel = Number(e.target.value); applyFilters(); };
  document.getElementById('extents').onchange = e => { state.extents = e.target.checked; applyFilters(); };
  document.getElementById('approx').onchange = e => { state.approx = e.target.checked; applyFilters(); };
  document.getElementById('q').oninput = e => { state.q = e.target.value.trim().toLowerCase(); applyFilters(); };

  function renderList(ids) {
    const ul = document.querySelector('#list ul'); ul.innerHTML = '';
    document.getElementById('count').textContent = `(${ids.length} of ${records.length})`;
    for (const id of ids) {
      const r = byId[id];
      const li = document.createElement('li'); li.className = id === state.sel ? 'sel' : '';
      li.innerHTML = `<span class="lvl ${r.level}">${r.level}</span><span class="t">${r.title}<span class="p">${r.publisher.name}</span></span>`;
      li.onclick = () => select(id, true);
      ul.appendChild(li);
    }
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

  function select(id, fly) {
    state.sel = id; const r = byId[id];
    renderList(visibleIds());
    const d = document.getElementById('detail'); d.hidden = false;
    const base = location.origin + location.pathname.replace(/[^/]*$/, '');
    const geo = base + 'data/outlines.geojson';
    const issues = (r.known_issues || []).map(x => `<li>${esc(x)}</li>`).join('');
    d.innerHTML = `
      <span class="close" title="close">✕</span>
      <h3>${esc(r.title)} <span class="lvl ${r.level}">${r.level}</span></h3>
      <div style="color:var(--muted)">${esc(r.summary || '')}</div>
      <dl>
        <dt>Publisher</dt><dd><a href="${esc(r.publisher.url)}" target="_blank" rel="noopener">${esc(r.publisher.name)}</a></dd>
        <dt>Origin</dt><dd><a href="${esc(r.origin.url)}" target="_blank" rel="noopener">${esc(r.origin.url)}</a> (${esc(r.origin.access)})</dd>
        <dt>Licence</dt><dd>${esc(r.licence.name)}${r.licence.spdx ? ' (' + esc(r.licence.spdx) + ')' : ''}<br>redistribution ${esc(r.licence.redistribution)}, attribution ${esc(r.licence.attribution)}</dd>
        <dt>Holds</dt><dd>${r.kinds.map(esc).join(', ')}</dd>
        <dt>Region</dt><dd>${esc([r.region && r.region.basin, r.region && r.region.country].filter(Boolean).join(', ') || '—')}</dd>
        <dt>Checked</dt><dd>${esc(r.checked_at || 'not yet')}</dd>
      </dl>
      ${issues ? `<div><b>Known issues</b><ul>${issues}</ul></div>` : ''}
      <div class="cards">
        <div class="card"><b>Open in QGIS</b>Layer → Add Layer → Vector, protocol HTTP, this address; filter on record_id.<code>${esc(geo)}</code></div>
        <div class="card"><b>Read in Python</b><code>import json, urllib.request
fc = json.load(urllib.request.urlopen("${esc(geo)}"))
mine = [f for f in fc["features"] if f["properties"]["record_id"] == "${esc(r.id)}"]</code></div>
        <div class="card"><b>Get the data</b>Follow the origin link above. Retrieval by manifest and the Ophiolite source are chartered (E06, E09).</div>
      </div>`;
    d.querySelector('.close').onclick = () => { d.hidden = true; state.sel = null; renderList(visibleIds()); };
    if (fly && r.region && r.region.bbox) map.fitBounds(r.region.bbox, { padding: 60, maxZoom: 9, duration: 700 });
  }
})();
