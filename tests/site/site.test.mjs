// Playwright site test for E05: `make site-test` (node --test tests/site/). Offline by default.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { ROOT, serve, launch, offline, errorsOf, ready } from './harness.mjs';

const OUT = join(ROOT, 'build', 'site-test');
let server, browser;
before(async () => { await mkdir(OUT, { recursive: true }); server = await serve(); browser = await launch(); });
after(async () => { await browser.close(); server.close(); });

// The GeoJSON path on the same build: files.txt without the tiles.
const withoutTiles = c => c.route('**/data/files.txt', async route =>
  route.fulfill({ body: (await (await route.fetch()).text()).split('\n').filter(f => f !== 'outlines.pmtiles').join('\n') }));

async function open(hash = '', { viewport = { width: 1400, height: 900 }, routes } = {}) {
  const context = await browser.newContext({ viewport });
  const unexpected = [];
  await offline(context, unexpected);
  if (routes) await routes(context);
  const page = await context.newPage();
  const errors = errorsOf(page);
  await page.goto(server.url + (hash ? '#' + hash : ''));
  await ready(page);
  return { context, page, errors, unexpected };
}

test('no console error on load, map and how page', async () => {
  const { context, page, errors, unexpected } = await open();
  await page.goto(server.url + 'how.html');
  await page.waitForLoadState('networkidle');
  assert.equal(await page.locator('#card-python pre').count(), 1);
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

test('#q=volve lists one dataset', async () => {
  const { context, page, errors } = await open('q=volve');
  assert.equal(await page.locator('#list li').count(), 1);
  assert.match(await page.locator('#list li').first().innerText(), /Volve/);
  assert.equal(await page.inputValue('#q'), 'volve');
  await page.screenshot({ path: join(OUT, 'q-volve.png') });
  assert.deepEqual(errors, []);
  await context.close();
});

test('a hash with a kind filter and a selection renders the same view in a second context', async () => {
  const a = await open();
  await a.page.locator('.chip', { hasText: /^production$/ }).click();
  await a.page.locator('#list li').nth(1).click();
  await a.page.waitForFunction(() => /sel=/.test(location.hash) && /map=/.test(location.hash));
  await a.page.waitForTimeout(1000); // the fly-to ends and writes the viewport
  const hash = await a.page.evaluate(() => location.hash);
  assert.match(hash, /k=production/);
  const seen = async p => ({ count: await p.locator('#count').innerText(), items: await p.locator('#list li').count(),
    title: await p.locator('#detail h3 .title').innerText(), zoom: await p.evaluate(() => window.osdMap.getZoom().toFixed(1)) });
  const want = await seen(a.page);

  const b = await open(hash.slice(1));
  const got = await seen(b.page);
  assert.deepEqual(got, want);
  assert.equal(await b.page.locator('.chip.on').innerText(), 'production');
  assert.deepEqual([...a.errors, ...b.errors], []);
  console.log('# shared view', hash, JSON.stringify(got));
  await a.context.close(); await b.context.close();
});

test('stale: checked_at older than 30 days shows "stale" next to the level', async () => {
  const old = new Date(Date.now() - 40 * 864e5).toISOString(), fresh = new Date().toISOString();
  const { context, page, errors } = await open('q=volve', { routes: c => c.route('**/data/records.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    for (const r of body.records) { r.level = 'L1'; r.checked_at = r.id === 'equinor/volve' ? old : fresh; }
    return route.fulfill({ json: body });
  }) });
  assert.equal(await page.locator('#list li .stale').count(), 1);
  await page.fill('#q', '');
  assert.equal(await page.locator('#list li .stale').count(), 1);
  assert.ok(await page.locator('#list li').count() > 1);
  assert.deepEqual(errors, []);
  await context.close();
});

test('10,000 wellbores cluster at zoom 5 and the frame after moveend arrives under 100 ms', async () => {
  const N = 10000;
  const records = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8')).records;
  const rid = records.find(r => r.id === 'sodir/factpages')?.id || records[0].id;
  let seed = 1; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const wells = Array.from({ length: N }, (_, i) => ({ type: 'Feature',
    properties: { record_id: rid, kind: 'wellbore', name: `synthetic ${i}`, approximate: false },
    geometry: { type: 'Point', coordinates: [1 + rnd() * 8, 56 + rnd() * 6] } }));
  // the synthetic set replaces the committed outlines on the GeoJSON path (files.txt without tiles,
  // E15), so the budget measures these N points alone
  const { context, page, errors } = await open('map=5/59/5', { routes: async c => { await withoutTiles(c);
    await c.route('**/data/outlines.geojson', route => route.fulfill({ json: { type: 'FeatureCollection', features: wells } })); } });

  const seen = await page.evaluate(() => {
    const m = window.osdMap;
    const clusters = m.queryRenderedFeatures({ layers: ['wells-cluster'] });
    const singles = m.queryRenderedFeatures({ layers: ['wells'] });
    return { zoom: m.getZoom(), clusters: clusters.length, singles: singles.length,
      points: clusters.reduce((s, f) => s + f.properties.point_count, 0) + singles.length };
  });
  assert.equal(seen.zoom, 5);
  assert.ok(seen.clusters > 0, 'clusters drawn');
  assert.ok(seen.clusters + seen.singles < 500, 'points are grouped, not drawn one by one');
  assert.ok(seen.points > N * 0.9, `most of the ${N} points are on screen`);

  const pans = () => page.evaluate(async () => {
    const m = window.osdMap, out = [];
    for (const [dx, dy] of [[300, 0], [0, 200], [-300, 0], [0, -200], [250, 150]]) out.push(await new Promise(ok => {
      m.once('moveend', () => { const t0 = performance.now(); requestAnimationFrame(() => ok(performance.now() - t0)); });
      m.panBy([dx, dy], { duration: 400 });
    }));
    return out;
  });
  const median = fs => [...fs].sort((a, b) => a - b)[Math.floor(fs.length / 2)];
  const ms = fs => fs.map(f => f.toFixed(1)).join(', ');
  await browser.startTracing(page, { path: join(OUT, 'pan-trace.json'), screenshots: false });
  const frames = await pans();
  await browser.stopTracing();
  await page.screenshot({ path: join(OUT, 'clusters-10k.png') });
  // Runner speed, measured on the same page: the same five pans with the wells source emptied, so the
  // frame holds the base map, extents and swiftshader's fill but none of the 10,000 points. The budget is
  // 100 ms on a machine whose reference frame is REF_MS (this host, 23 Oct) and grows only in proportion
  // when the runner's reference frame is slower; the points' share of the frame is held to the same bound.
  await page.evaluate(() => new Promise(ok => { window.osdMap.getSource('wells').setData({ type: 'FeatureCollection', features: [] }); window.osdMap.once('idle', ok); }));
  const ref = await pans();
  const BUDGET = 100, REF_MS = 30;
  const budget = BUDGET * Math.max(1, median(ref) / REF_MS);
  console.log('# 10k wellbores at zoom 5:', JSON.stringify(seen), `frame after moveend (ms): ${ms(frames)}; reference without the points: ${ms(ref)}; budget ${budget.toFixed(1)} ms`);
  // Median of the five pans: one outlier on a shared runner is scheduler noise, not a regression; a real
  // regression moves the median (E05). A uniformly slow runner moves the reference too (PR #35, #36).
  assert.ok(median(frames) < budget, `median frame after moveend ${median(frames).toFixed(1)} ms over ${budget.toFixed(1)} ms (frames ${ms(frames)}; reference ${ms(ref)})`);
  assert.deepEqual(errors, []);
  await context.close();
});

test('phone width: the panel is a bottom sheet', async () => {
  const { context, page, errors } = await open('sel=equinor/volve', { viewport: { width: 390, height: 844 } });
  const box = await page.locator('#side').boundingBox();
  assert.equal(Math.round(box.x), 0);
  assert.ok(Math.abs(box.y + box.height - 844) < 2, 'sheet sits on the bottom edge');
  const detail = await page.locator('#detail').boundingBox();
  assert.ok(detail.y > box.y && detail.y < 844 - 100, 'the selected dataset shows at the top of the sheet');
  await page.screenshot({ path: join(OUT, 'phone.png') });
  assert.deepEqual(errors, []);
  await context.close();
});

// E15: tiles. The build writes data/outlines.pmtiles when tippecanoe is installed (CI installs it);
// these tests need it there and say so when it is absent locally.
const built = (await readFile(join(ROOT, 'site', 'data', 'files.txt'), 'utf8').catch(() => '')).split('\n');
const noTiles = !built.includes('outlines.pmtiles') && (process.env.CI ? false : 'no data/outlines.pmtiles (tippecanoe not installed)');
if (process.env.CI && !built.includes('outlines.pmtiles')) throw new Error('CI builds tiles: data/outlines.pmtiles missing');
const outlinesSource = page => page.evaluate(() => window.osdMap.getSource('outlines').type);

test('tiles: the page loads tiles for the viewport, under 1 MB from the site, and never outlines.geojson', { skip: noTiles }, async () => {
  for (const hash of ['', 'q=sodir', 'map=5/59/5']) {
    const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
    const unexpected = [];
    await offline(context, unexpected);
    const page = await context.newPage();
    const errors = errorsOf(page);
    const log = [];
    page.on('requestfinished', async r => log.push({ url: r.url(), bytes: (await r.sizes()).responseBodySize }));
    await page.goto(server.url + (hash ? '#' + hash : ''));
    await ready(page);
    await page.waitForTimeout(300); // the last sizes arrive
    assert.equal(await outlinesSource(page), 'vector');
    const site = log.filter(r => r.url.startsWith(server.url)), libs = log.filter(r => !r.url.startsWith(server.url));
    const sum = rs => rs.reduce((s, r) => s + r.bytes, 0);
    const tiles = site.filter(r => r.url.endsWith('data/outlines.pmtiles'));
    console.log(`# tiles, load #${hash}: site ${sum(site)} bytes (pmtiles ${tiles.length} ranges, ${sum(tiles)} bytes),`,
      `libraries off-site ${sum(libs)} bytes (uncompressed here, served by unpkg)`);
    assert.deepEqual(site.filter(r => r.url.includes('outlines.geojson')), []);
    assert.ok(tiles.length > 1, 'tiles requested by range');
    assert.ok(sum(site) < 1e6, `site bytes ${sum(site)} before any pan`);
    assert.deepEqual(errors, []);
    assert.deepEqual(unexpected, []);
    await context.close();
  }
});

test('tiles: #q=factpages, a click on a wellbore shows the same detail title as the GeoJSON path', { skip: noTiles }, async () => {
  const hash = 'q=factpages&map=10/60.55/2.85';
  const clickWell = async (page, layer, want) => {
    const f = await page.evaluate(([layer, want]) => {
      const m = window.osdMap;
      const fs = m.queryRenderedFeatures({ layers: [layer] }).filter(f => !want || f.properties.feature_id === want);
      const f = fs.find(f => f.properties.record_id === 'sodir/factpages');
      return f && { id: f.id, feature_id: f.properties.feature_id, at: m.project(f.geometry.coordinates) };
    }, [layer, want]);
    assert.ok(f, `a Sodir wellbore drawn on ${layer}`);
    await page.mouse.click(f.at.x, f.at.y);
    await page.locator('#detail h3 .title').waitFor();
    return { ...f, title: await page.locator('#detail h3 .title').innerText(), sel: await page.evaluate(() => location.hash) };
  };
  const a = await open(hash);
  assert.equal(await outlinesSource(a.page), 'vector');
  const t = await clickWell(a.page, 'wells-tiles');
  assert.equal(t.id, t.feature_id, 'feature_id is the tile feature id');
  await a.page.screenshot({ path: join(OUT, 'tiles-sodir-wellbore.png') });

  const b = await open(hash, { routes: withoutTiles });
  assert.equal(await outlinesSource(b.page), 'geojson');
  const g = await clickWell(b.page, 'wells', t.feature_id);
  console.log('# wellbore', t.feature_id, 'tiles:', t.title, '| geojson:', g.title);
  assert.equal(g.title, t.title);
  assert.match(t.sel, /sel=sodir\/factpages/);
  assert.deepEqual([...a.errors, ...b.errors], []);
  await a.context.close(); await b.context.close();
});

test('tiles: a server without byte ranges (python3 -m http.server) falls back to outlines.geojson', { skip: noTiles }, async () => {
  const { context, page, errors } = await open('map=5/59/5', { routes: c => c.route('**/data/outlines.pmtiles',
    route => route.fulfill({ status: 200, body: Buffer.alloc(20000) })) });
  assert.equal(await outlinesSource(page), 'geojson');
  const clusters = await page.evaluate(() => window.osdMap.queryRenderedFeatures({ layers: ['wells-cluster'] }).length);
  assert.ok(clusters > 0, 'wells cluster from the GeoJSON');
  assert.deepEqual(errors, []);
  await context.close();
});

test('tiles: phone width with tiles, Sodir wells clustered', { skip: noTiles }, async () => {
  const { context, page, errors } = await open('q=sodir&map=4.5/62/6', { viewport: { width: 390, height: 844 } });
  assert.equal(await outlinesSource(page), 'vector');
  await page.waitForFunction(() => window.osdMap.queryRenderedFeatures({ layers: ['wells-cluster'] }).length > 0);
  await page.screenshot({ path: join(OUT, 'tiles-phone.png') });
  assert.deepEqual(errors, []);
  await context.close();
});

// E36: below CLUSTER_BELOW_ZOOM the wells are clusters from the build's grids (data/wells-z<z>.json),
// not from tiles; the counts are exact: they sum to the committed outlines' wellbore points.
const committedWells = async () => {
  const { readdir } = await import('node:fs/promises');
  const n = {};
  for (const f of (await readdir(join(ROOT, 'outlines'))).filter(f => f.endsWith('.geojson'))) {
    for (const x of JSON.parse(await readFile(join(ROOT, 'outlines', f), 'utf8')).features) {
      if (x.properties.kind === 'wellbore' && x.geometry.type === 'Point') n[x.properties.record_id] = (n[x.properties.record_id] || 0) + 1;
    }
  }
  return n;
};
// What the clusters on the page count, every cell of the world, not only the viewport: the wells source's data.
const clusterTotal = page => page.evaluate(async () => (await window.osdMap.getSource('wells').getData()).features
  .reduce((s, f) => s + (f.properties.point_count || 1), 0));
async function until(page, f, want, what) {
  let got;
  for (let i = 0; i < 100; i++) { if ((got = await f(page)) === want) return got; await page.waitForTimeout(100); }
  assert.equal(got, want, what);
}
// The registers with wells committed (va-energy/gas-oil-wells waits: its host's certificate expired on
// 23 Oct 2026, so the verifier could not derive it; docs/program/evidence/e36/outlines.md).
const REGISTERS = ['sgudds/register-geotermalnych-vrtov', 'nzpam/petroleum-wells', 'wa-demirs/petroleum-wells',
  'bcer/well-surface-holes-permitted', 'sgc/banco-informacion-petrolera-pozos',
  'ut-dogm/oil-gas-wells', 'nd-dmr/wells'];

test('wells: at the world view the cluster total is every committed well; one register alone is its own count; period and approximate filters count the same', { skip: noTiles }, async () => {
  const want = await committedWells();
  const total = Object.values(want).reduce((a, b) => a + b, 0);
  const registers = REGISTERS.reduce((s, id) => s + (want[id] || 0), 0);
  console.log('# committed wellbore points:', total, 'of which the registers with wells', registers, JSON.stringify(want));
  for (const id of REGISTERS) assert.ok(want[id] > 0, `${id} has a committed outline`);
  const { context, page, errors, unexpected } = await open('', { viewport: { width: 390, height: 844 } });
  assert.ok(await page.evaluate(() => window.osdMap.getZoom()) < 7);
  await until(page, clusterTotal, total, 'world view: clusters count every committed well');
  const records = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8')).records;
  for (const id of REGISTERS) {   // the search box finds each register by its id and nothing else with wells
    assert.deepEqual(records.filter(r => r.id.includes(id) && want[r.id]).map(r => r.id), [id]);
    await page.evaluate(id => { location.hash = 'q=' + id; }, id);
    await until(page, clusterTotal, want[id], `filtered to ${id}`);
  }
  // Period: dated records only, then a window; the clusters follow the list of records.
  const dated = records.filter(r => r.period && (r.period.start || r.period.end));
  const yr = s => s ? Number(String(s).slice(0, 4)) : null;
  const overlaps = r => (yr(r.period.start) ?? -Infinity) <= 2000 && (yr(r.period.end) ?? 9999) >= 2000;
  const count = rs => rs.reduce((s, r) => s + (want[r.id] || 0), 0);
  await page.evaluate(() => { location.hash = 'dated=1'; });
  await until(page, clusterTotal, count(dated), 'dated records only');
  await page.evaluate(() => { location.hash = 't=2000-2000&dated=1'; });
  await until(page, clusterTotal, count(dated.filter(overlaps)), 'period 2000');
  // Approximate: no committed well is approximate today, so hiding them leaves the total.
  const approx = (await Promise.all((await (await import('node:fs/promises')).readdir(join(ROOT, 'site', 'data')))
    .filter(f => /^wells-z\d+\.json$/.test(f)).map(async f => JSON.parse(await readFile(join(ROOT, 'site', 'data', f), 'utf8')))))
    .map(g => g.rows.reduce((s, r) => s + r[4], 0));
  await page.evaluate(() => { location.hash = 'ph=0'; });
  await until(page, clusterTotal, total - approx[0], 'approximate wells hidden');
  await page.screenshot({ path: join(OUT, 'wells-world-phone.png') });
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

test('wells: the approximate toggle takes its wells out of the clusters (fixture grid)', { skip: noTiles }, async () => {
  const grid = { zoom: 3, cells: 64, records: ['nd-dmr/wells', 'equinor/volve'], rows: [[14, 22, 0, 5, 0, -103.3, 47.8], [14, 22, 1, 2, 3, -103.2, 47.9], [33, 18, 1, 0, 1, 2.0, 58.4]] };
  const { context, page, errors } = await open('map=3.2/55/5', { routes: c => c.route('**/data/wells-z3.json', r => r.fulfill({ json: grid })) });
  await until(page, clusterTotal, 11, 'every well');
  await page.evaluate(() => { location.hash = 'ph=0&map=3.2/55/5'; });
  await until(page, clusterTotal, 7, 'approximate wells hidden');
  await page.evaluate(() => { location.hash = 'q=volve&map=3.2/55/5'; });
  await until(page, clusterTotal, 6, 'one record');
  assert.deepEqual(errors, []);
  await context.close();
});

test('wells: below CLUSTER_BELOW_ZOOM clusters and no tile well; at it, a clicked North Dakota well opens its dataset panel', { skip: noTiles }, async () => {
  const { context, page, errors } = await open('map=6/47.8/-103.3', { viewport: { width: 390, height: 844 } });
  const drawn = () => page.evaluate(() => Object.fromEntries(['wells-cluster', 'wells', 'wells-tiles']
    .map(l => [l, window.osdMap.queryRenderedFeatures({ layers: [l] }).length])));
  const at6 = await drawn();
  assert.ok(at6['wells-cluster'] > 0 && at6['wells-tiles'] === 0, JSON.stringify(at6));
  await page.evaluate(() => new Promise(ok => { window.osdMap.once('idle', ok); window.osdMap.jumpTo({ zoom: 7 }); }));
  await page.waitForFunction(() => window.osdMap.queryRenderedFeatures({ layers: ['wells-tiles'] }).length > 0);
  const at7 = await drawn();
  assert.ok(at7['wells-cluster'] === 0 && at7.wells === 0, JSON.stringify(at7));
  const f = await page.evaluate(() => {
    const m = window.osdMap, c = m.getCanvas().getBoundingClientRect();
    const f = m.queryRenderedFeatures({ layers: ['wells-tiles'] }).find(f => { const p = m.project(f.geometry.coordinates);
      return f.properties.record_id === 'nd-dmr/wells' && p.x > 20 && p.x < c.width - 60 && p.y > 80 && p.y < c.height * 0.4; });
    return f && { id: f.id, feature_id: f.properties.feature_id, at: m.project(f.geometry.coordinates) };
  });
  assert.ok(f, 'a North Dakota well in the upper map');
  assert.equal(f.id, f.feature_id, 'feature_id is the tile feature id');
  await page.mouse.click(f.at.x, f.at.y);
  await page.locator('#detail h3 .title').waitFor();
  assert.match(await page.locator('#detail h3 .title').innerText(), /North Dakota/i);
  assert.match(await page.evaluate(() => location.hash), /sel=nd-dmr\/wells/);
  await page.screenshot({ path: join(OUT, 'wells-nd-panel-phone.png') });
  assert.deepEqual(errors, []);
  await context.close();
});

// E06 slice 2: select mode. A fixture origin on 127.0.0.1 holds one file per ticked dataset; the
// page's collections.json is given those files as Collection assets (the verifier's digests), so
// the downloaded manifest can be read by osd.manifest.read and fetched by `osd get` offline.
const FIXTURE = { 'opm--norne': { 'norne/NORNE_ATW2013.DATA': 'RUNSPEC\nTITLE\nNORNE fixture\n' },
  'sodir--factpages': { 'wellbore_exploration_all.csv': 'wlbName,wlbWell\n1/9-1,1/9-1\n' } };
let fixture;
before(async () => {
  const bodies = Object.fromEntries(Object.values(FIXTURE).flatMap(o => Object.entries(o)).map(([k, b]) => ['/' + k, b]));
  const srv = createServer((req, res) => bodies[req.url] ? res.writeHead(200).end(bodies[req.url]) : res.writeHead(404).end());
  await new Promise(ok => srv.listen(0, '127.0.0.1', ok));
  const at = `http://127.0.0.1:${srv.address().port}`;
  const assets = Object.fromEntries(Object.entries(FIXTURE).map(([cid, files]) => [cid, Object.fromEntries(Object.entries(files)
    .map(([k, b]) => [k, { href: `${at}/${k}`, title: k, roles: ['data'], 'file:size': Buffer.byteLength(b),
      'file:checksum': '1220' + createHash('sha256').update(b).digest('hex') }]))]));
  fixture = { assets, close: () => srv.close() };
});
after(() => fixture.close());

const records = Object.fromEntries(JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8')).records.map(r => [r.id, r]));
const withAssets = c => c.route('**/data/collections.json', async route => {
  const body = JSON.parse(await (await route.fetch()).text());
  for (const col of body.collections) if (fixture.assets[col.id]) col.assets = fixture.assets[col.id];
  return route.fulfill({ json: body });
});

async function downloadManifest(page, name) {
  const [dl] = await Promise.all([page.waitForEvent('download'), page.locator('#download').click()]);
  assert.equal(dl.suggestedFilename(), 'osd.manifest.json');
  const file = join(OUT, name);
  await dl.saveAs(file);
  return { file, doc: JSON.parse(await readFile(file, 'utf8')) };
}

// osd.manifest.read on the page's file, equality with `osd manifest`, then `osd get --dest`.
async function roundTrip(file, tag) {
  const assets = join(OUT, `assets-${tag}.json`), dest = join(OUT, `retrieved-${tag}`);
  await writeFile(assets, JSON.stringify(fixture.assets));
  await rm(dest, { recursive: true, force: true });
  const { stdout } = await promisify(execFile)(process.env.UV || 'uv',
    ['run', '--quiet', 'python', join(ROOT, 'tests', 'site', 'manifest_roundtrip.py'), file, assets, dest], { cwd: ROOT });
  console.log(stdout.trim().split('\n').slice(0, -1).map(l => '# ' + l).join('\n'));
  return { entries: JSON.parse(stdout.trim().split('\n').pop()), dest };
}

const sha = (cid, k) => fixture.assets[cid][k]['file:checksum'].slice(4);

for (const [path, routes, wellLayer] of [['tiles', withAssets, 'wells-tiles'],
  ['geojson', async c => { await withAssets(c); await withoutTiles(c); }, 'wells']]) {
  test(`select (${path}): tick a dataset on the map and one in the list, see the rights, download a manifest osd get reads`,
    { skip: path === 'tiles' && noTiles }, async () => {
    const { context, page, errors, unexpected } = await open('q=factpages&map=10/60.55/2.85', { routes });
    assert.equal(await outlinesSource(page), path === 'tiles' ? 'vector' : 'geojson');
    await page.locator('#pickmode').click();
    assert.equal(await page.locator('#list li .tick').count(), await page.locator('#list li').count());
    const at = await page.evaluate(layer => {
      const f = window.osdMap.queryRenderedFeatures({ layers: [layer] }).find(f => f.properties.record_id === 'sodir/factpages');
      return f && window.osdMap.project(f.geometry.coordinates);
    }, wellLayer);
    assert.ok(at, `a Sodir wellbore on ${wellLayer}`);
    await page.mouse.click(at.x, at.y);  // a wellbore ticks its dataset (Collection selection)
    await page.locator('#basket li[data-id="sodir/factpages"]').waitFor();
    assert.equal(await page.locator('#detail').isHidden(), true, 'select mode opens no detail');
    await page.fill('#q', 'norne');
    await page.locator('#list li[data-id="opm/norne"]').click();
    assert.equal(await page.locator('#list li[data-id="opm/norne"] .tick').isChecked(), true);

    // before the download: the attribution lines and the share-alike note
    assert.match(await page.locator('#basket h2').innerText(), /\(2\)$/);
    assert.equal(await page.locator('#basket li[data-id="sodir/factpages"] .stmt').innerText(), records['sodir/factpages'].licence.statement);
    assert.match(await page.locator('#basket li[data-id="opm/norne"] .stmt').innerText(), /No attribution statement stated/);
    assert.match(await page.locator('#basket li[data-id="opm/norne"] .lic').innerText(), /share-alike: derived work must carry ODbL-1\.0/);
    assert.match(await page.locator('#basket li[data-id="sodir/factpages"] .lic').innerText(), /share-alike: not stated/);
    assert.deepEqual(await page.locator('#basket .sa').allInnerTexts(), ['1 item requires derived work to carry ODbL-1.0.']);
    await page.waitForFunction(() => [...document.querySelectorAll('#basket .files')].every(e => /sha256/.test(e.textContent)));
    assert.match(await page.evaluate(() => location.hash), /pick=sodir\/factpages,opm\/norne/);
    await page.screenshot({ path: join(OUT, `select-${path}.png`) });

    const { file, doc } = await downloadManifest(page, `osd.manifest-${path}.json`);
    assert.equal(doc.format, 'osd.manifest/1');
    assert.equal(doc.selection, 'collections');
    assert.deepEqual(doc.entries.map(e => [e.record_id, e.collection_id, e.coverage, Object.keys(e.assets)]), [
      ['sodir/factpages', 'sodir--factpages', 'sampled', ['wellbore_exploration_all.csv']],
      ['opm/norne', 'opm--norne', 'sampled', ['norne/NORNE_ATW2013.DATA']]]);
    assert.deepEqual(doc.entries.map(e => e.licence), [records['sodir/factpages'].licence, records['opm/norne'].licence]);

    const { entries, dest } = await roundTrip(file, path);
    assert.deepEqual(entries.map(e => [e.record_id, e.sha256]), [
      ['sodir/factpages', { 'wellbore_exploration_all.csv': sha('sodir--factpages', 'wellbore_exploration_all.csv') }],
      ['opm/norne', { 'norne/NORNE_ATW2013.DATA': sha('opm--norne', 'norne/NORNE_ATW2013.DATA') }]]);
    assert.equal(await readFile(join(dest, 'opm--norne', 'norne', 'NORNE_ATW2013.DATA'), 'utf8'), FIXTURE['opm--norne']['norne/NORNE_ATW2013.DATA']);
    assert.ok((await readFile(join(dest, 'ATTRIBUTION.md'), 'utf8')).includes('> ' + records['sodir/factpages'].licence.statement));
    assert.deepEqual(errors, []);
    assert.deepEqual(unexpected, []);
    await context.close();
  });
}

const SHARED = 'pick=opm/norne,sodir/factpages,terranubis/f3-demo-2020';

test('select: a #pick= link restores the selection in a new context; a registration dataset is a to-do', async () => {
  const { context, page, errors } = await open(SHARED, { routes: withAssets });
  assert.equal(await page.locator('#pickmode').innerText(), 'Done');
  assert.deepEqual(await page.locator('#basket li').evaluateAll(ls => ls.map(l => l.dataset.id)), SHARED.slice(5).split(','));
  assert.equal(await page.locator('#list li .tick:checked').count(), 3);
  await page.waitForFunction(() => new Set(window.osdMap.queryRenderedFeatures({ layers: ['picked-line'] }).map(f => f.properties.record_id)).size === 3);
  await page.screenshot({ path: join(OUT, 'select-desktop.png') });
  await page.waitForFunction(() => document.querySelector('#basket .files.todo'));
  assert.match(await page.locator('#basket li[data-id="terranubis/f3-demo-2020"] .files').innerText(), /^to-do: access registration/);
  assert.deepEqual(await page.locator('#basket .sa').allInnerTexts(),
    ['1 item requires derived work to carry CC-BY-SA-3.0.', '1 item requires derived work to carry ODbL-1.0.']);
  const { file, doc } = await downloadManifest(page, 'osd.manifest-shared.json');
  const f3 = doc.entries[2];
  assert.deepEqual([f3.record_id, f3.assets, f3.coverage], ['terranubis/f3-demo-2020', {}, undefined]);
  assert.match(f3.unresolved, /^access registration/);
  const { entries } = await roundTrip(file, 'shared');
  assert.deepEqual(entries.map(e => e.record_id), SHARED.slice(5).split(','));
  // removing an item and leaving select mode rewrite the hash
  await page.locator('#basket li[data-id="sodir/factpages"] .x').click();
  assert.match(await page.evaluate(() => location.hash), /pick=opm\/norne,terranubis\/f3-demo-2020/);
  await page.locator('#pickmode').click();
  assert.doesNotMatch(await page.evaluate(() => location.hash), /pick=/);
  assert.equal(await page.locator('#basket').isHidden(), true);
  assert.deepEqual(errors, []);
  await context.close();
});

test('select: phone width, the basket and the download button are reachable in the sheet', async () => {
  const { context, page, errors } = await open(SHARED, { viewport: { width: 390, height: 844 }, routes: withAssets });
  const sheet = await page.locator('#side').boundingBox();
  const basket = await page.locator('#basket').boundingBox();
  assert.ok(basket.y >= sheet.y && basket.y < 844 - 100, 'the basket comes first in the sheet');
  assert.ok(basket.width <= 390, 'no horizontal overflow');
  await page.waitForFunction(() => document.querySelector('#basket .files.todo'));
  await page.screenshot({ path: join(OUT, 'select-phone.png') });
  // the map canvas can render black under swiftshader at phone width (HANDOFF known red): the sheet alone
  await page.screenshot({ path: join(OUT, 'select-phone-sheet.png'), clip: { x: 0, y: sheet.y, width: 390, height: sheet.height } });
  await page.locator('#download').scrollIntoViewIfNeeded();
  assert.ok(await page.locator('#download').isVisible());
  await page.screenshot({ path: join(OUT, 'select-phone-download.png'), clip: { x: 0, y: sheet.y, width: 390, height: sheet.height } });
  const { doc } = await downloadManifest(page, 'osd.manifest-phone.json');
  assert.equal(doc.entries.length, 3);
  assert.deepEqual(errors, []);
  await context.close();
});

// E19: the record/3 vocabulary on the page. Chips come from the records present; select mode carries
// purchase and licence.terms whole, as osd manifest writes them (manifest/4).
test('kinds: a potential-fields chip appears from the data and filters one record in, one out', async () => {
  const built = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8'));
  const gravity = { ...records['prime/national-oil-gas-database'], kinds: ['potential-fields', 'reports'] };
  const plain = { ...records['opm/norne'], kinds: ['reports'] };
  const fixtureCatalogue = async c => {
    await withoutTiles(c);
    await c.route('**/data/records.json', route => route.fulfill({ json: { ...built, count: 2, records: [gravity, plain] } }));
    await c.route('**/data/outlines.geojson', route => route.fulfill({ json: { type: 'FeatureCollection', features: [] } }));
  };
  const { context, page, errors, unexpected } = await open('', { routes: fixtureCatalogue });
  assert.deepEqual(await page.locator('#kinds .chip').allInnerTexts(), ['potential-fields', 'reports']);
  assert.equal(await page.locator('#list li').count(), 2);
  await page.locator('.chip', { hasText: /^potential-fields$/ }).click();
  assert.match(await page.evaluate(() => location.hash), /k=potential-fields/);
  assert.deepEqual(await page.locator('#list li').evaluateAll(ls => ls.map(l => l.dataset.id)), [gravity.id]);
  await page.screenshot({ path: join(OUT, 'kinds-potential-fields.png') });
  await page.locator('.chip', { hasText: /^reports$/ }).click();   // either kind: both again
  assert.equal(await page.locator('#list li').count(), 2);
  await page.locator('.chip', { hasText: /^potential-fields$/ }).click();
  assert.deepEqual(await page.locator('#list li').evaluateAll(ls => ls.map(l => l.dataset.id)).then(x => x.sort()), [gravity.id, plain.id].sort());
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

const PASA = 'pasa/national-petroleum-exploration-database';
test('select: a purchase dataset with terms: the page writes osd.manifest/4 with the same terms object osd manifest writes', async () => {
  const built = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8'));
  const { context, page, errors, unexpected } = await open(`pick=${PASA},opm/norne`, { routes: withAssets });
  await page.waitForFunction(() => document.querySelector('#basket .files.todo'));
  assert.match(await page.locator(`#basket li[data-id="${PASA}"] .files`).innerText(), /^to-do: access purchase/);
  await page.screenshot({ path: join(OUT, 'select-purchase-terms.png') });
  const { file, doc } = await downloadManifest(page, 'osd.manifest-purchase.json');
  assert.equal(doc.format, 'osd.manifest/4');
  assert.deepEqual(doc.metadata, { catalog: built.catalog });
  const [pasa, norne] = doc.entries;
  assert.equal(pasa.access, 'purchase');
  assert.deepEqual(pasa.licence, records[PASA].licence);
  assert.deepEqual(pasa.licence.terms, { stated: records[PASA].licence.terms.stated, duration: records[PASA].licence.terms.duration,
    review_before_publication: true, expires: null });
  assert.equal('terms' in norne.licence, false);
  const { entries, dest } = await roundTrip(file, 'purchase');   // equal to osd manifest, entry for entry
  assert.deepEqual(entries.map(e => [e.record_id, e.unresolved]), [
    [PASA, 'access purchase: the publisher sells the files; buy them at the origin page'], ['opm/norne', null]]);
  assert.ok((await readFile(join(dest, 'ATTRIBUTION.md'), 'utf8')).includes('  > ' + records[PASA].licence.terms.stated));
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

// E21: the map says when. A period filter by year (overlap), `t=` and `dated=1` in the hash, a When row
// in the detail, the years in the list. The map layer carries no dates; the filter works on record ids.
const periodCatalogue = async c => {
  const built = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8'));
  const base = records['opm/norne'];
  const at = (id, period) => ({ ...base, id, title: id, ...(period ? { period } : {}) });
  const set = [at('t/starts-2004', { start: '2004', end: '2010', stated: 'Acquired 2004 to 2010.' }),
    at('t/ends-1995', { start: '1980-05', end: '1995-03-01', stated: 'Acquired 1980 to 1995.' }),
    at('t/open-1999', { start: '1999' }),         // only a start: runs to today
    at('t/until-1989', { end: '1989' }),          // only an end: runs from the start of record
    at('t/undated')];
  await withoutTiles(c);
  await c.route('**/data/records.json', route => route.fulfill({ json: { ...built, count: set.length, records: set } }));
  await c.route('**/data/outlines.geojson', route => route.fulfill({ json: { type: 'FeatureCollection', features: [] } }));
};
const listed = page => page.locator('#list li').evaluateAll(ls => ls.map(l => l.dataset.id));

test('period: #t=1990-2000 lists the records whose period overlaps plus undated ones; dated=1 drops the undated', async () => {
  const { context, page, errors, unexpected } = await open('t=1990-2000', { routes: periodCatalogue });
  assert.deepEqual(await listed(page), ['t/ends-1995', 't/open-1999', 't/undated']);
  assert.deepEqual([await page.inputValue('#from'), await page.inputValue('#to'), await page.isChecked('#dated')], ['1990', '2000', false]);
  assert.equal(await page.locator('#list li[data-id="t/ends-1995"] .yr').innerText(), '1980–1995');
  assert.equal(await page.locator('#list li[data-id="t/open-1999"] .yr').innerText(), '1999–today');
  assert.equal(await page.locator('#list li[data-id="t/undated"] .yr').count(), 0);
  await page.check('#dated');
  assert.deepEqual(await listed(page), ['t/ends-1995', 't/open-1999']);
  assert.match(await page.evaluate(() => location.hash), /t=1990-2000&dated=1/);
  // typing: a half-typed year leaves that side open, four digits apply
  await page.fill('#to', '');
  await page.fill('#from', '200');
  assert.equal((await listed(page)).length, 4);
  await page.fill('#from', '2005');
  assert.deepEqual(await listed(page), ['t/starts-2004', 't/open-1999']);
  assert.match(await page.evaluate(() => location.hash), /t=2005-(&|$)/);
  await page.fill('#from', ''); await page.fill('#to', '1985');
  assert.deepEqual(await listed(page), ['t/ends-1995', 't/until-1989']);
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

test('period: a hash with t=, a kind and a selection renders the same list and detail in a second context', async () => {
  const a = await open();
  await a.page.fill('#from', '1990');
  await a.page.fill('#to', '2000');
  await a.page.locator('.chip', { hasText: /^seismic-3d$/ }).click();
  await a.page.locator('#list li[data-id="terranubis/penobscot"]').click();
  await a.page.waitForFunction(() => /sel=/.test(location.hash) && /map=/.test(location.hash));
  await a.page.waitForTimeout(1000); // the fly-to ends and writes the viewport
  const hash = await a.page.evaluate(() => location.hash);
  assert.match(hash, /t=1990-2000/);
  assert.match(hash, /k=seismic-3d/);
  const seen = async p => ({ count: await p.locator('#count').innerText(), items: await listed(p),
    title: await p.locator('#detail h3 .title').innerText(), when: await p.locator('#detail dd.when').innerText(),
    years: [await p.inputValue('#from'), await p.inputValue('#to')] });
  const want = await seen(a.page);
  assert.ok(want.items.includes('terranubis/penobscot'), 'Penobscot (1992) in');
  for (const id of want.items) {
    const p = records[id].period;
    assert.ok(!p || (Number(p.start.slice(0, 4)) <= 2000 && Number(p.end.slice(0, 4)) >= 1990), `${id} overlaps 1990–2000 or is undated`);
  }
  assert.ok(want.items.length < Object.values(records).filter(r => r.kinds.includes('seismic-3d')).length, 'the window drops some 3D records');
  const b = await open(hash.slice(1));
  assert.deepEqual(await seen(b.page), want);
  assert.deepEqual([...a.errors, ...b.errors], []);
  console.log('# shared period view', hash, want.count);
  await a.context.close(); await b.context.close();
});

test('period: the detail of a dated record shows the When row with the stated sentence; undated says not stated', async () => {
  const { context, page, errors } = await open('sel=equinor/volve');
  const volve = records['equinor/volve'].period;
  const when = page.locator('#detail dt', { hasText: /^When$/ });
  assert.equal(await when.count(), 1);
  assert.equal(await page.locator('#detail dd.when').innerText(), `${volve.start} to ${volve.end}\n${volve.stated}`);
  await page.locator('#detail').evaluate(d => { d.scrollTop = d.querySelector('dd.when').offsetTop - d.offsetTop - 120; });
  await page.screenshot({ path: join(OUT, 'when-detail.png') });
  await page.evaluate(() => { location.hash = 'sel=opm/norne'; });
  await page.waitForFunction(() => /Norne/.test(document.querySelector('#detail h3 .title').textContent));
  assert.equal(records['opm/norne'].period, undefined);
  assert.equal(await page.locator('#detail dd.when').innerText(), 'not stated by the publisher');
  assert.deepEqual(errors, []);
  await context.close();
});

test('period: the filter on the real catalogue, desktop and phone width; the year inputs fit the sheet', async () => {
  const d = await open('t=1990-2000&dated=1');
  const ids = await listed(d.page);
  for (const id of ids) {
    const p = records[id].period;
    assert.ok(Number(p.start.slice(0, 4)) <= 2000 && Number(p.end.slice(0, 4)) >= 1990, `${id} overlaps 1990–2000`);
  }
  assert.ok(ids.length > 5 && ids.length < Object.keys(records).length);
  await d.page.screenshot({ path: join(OUT, 'when-filter.png') });
  assert.deepEqual(d.errors, []);
  await d.context.close();

  const { context, page, errors } = await open('t=1990-2000&dated=1', { viewport: { width: 390, height: 844 } });
  const sheet = await page.locator('#side').boundingBox();
  for (const sel of ['#from', '#to', '#dated']) {
    const b = await page.locator(sel).boundingBox();
    assert.ok(b.x >= sheet.x && b.x + b.width <= sheet.x + sheet.width, `${sel} inside the sheet`);
  }
  assert.ok(await page.evaluate(() => { const s = document.getElementById('side'); return s.scrollWidth <= s.clientWidth; }), 'no horizontal overflow');
  await page.screenshot({ path: join(OUT, 'when-phone-sheet.png'), clip: { x: 0, y: sheet.y, width: 390, height: sheet.height } });
  assert.deepEqual(errors, []);
  await context.close();
});

// ---- E27: the map says why. A fixture catalogue with one verification per reason class
// (tests/fixtures/site/verification), built by osd.build into build/site-test/e27, served in place of
// data/records.json. The sentence is the one `osd status` prints (tests/test_build.py asserts that).
const WHY_DIR = join(OUT, 'e27');
const whyBuilt = (async () => {
  await promisify(execFile)(process.env.UV || 'uv', ['run', '--quiet', 'python', '-c',
    'import sys; from pathlib import Path; from osd.build import build; build(Path(sys.argv[1]), Path(sys.argv[2]), mirror_dir=Path(sys.argv[3]))',
    WHY_DIR, join(ROOT, 'tests', 'fixtures', 'site', 'verification'), join(OUT, 'e27-no-mirror')], { cwd: ROOT });
  return JSON.parse(await readFile(join(WHY_DIR, 'records.json'), 'utf8'));
})();
const withWhy = async c => { const body = await whyBuilt; await c.route('**/data/records.json', route => route.fulfill({ json: body })); };
const CLASSES = {   // record id -> what the panel must say, by class
  'bgs/single-onshore-borehole-index': /^files-checksummed: no file address is published to us/,
  'nzpam/kerry-3d': /no file address is published to us \(no origin\.manifest_url; access registration\)$/,
  'gsq/qped': /^files-checksummed: the listing \(ckan\) names no files$/,
  'ak-dggs/tax-credit-well-data': /^files-checksummed: robots\.txt disallows the listing /,
  'nm-ocd/oil-and-gas-wells': /^origin-reachable: answers a browser, not the verifier \(HTTP 404 to osd-verifier, HTTP 200 to a browser agent\)/,
  'seg/open-data-wiki': /^origin-reachable: blocked from this runner \(challenge page/,
  'geus/deep-subsurface-data': /^origin-reachable: HTTP 502 from /,
  'sodir/factpages': /^sample, not the whole dataset: 3 of 3 selected files hashed/,
  'nopims/poseidon': /^1 features derived from 1 inputs/,
  'equinor/volve': /^never verified$/,
};
const whyOf = page => page.evaluate(() => ({ title: document.querySelector('#detail h3 .title').textContent,
  reason: document.querySelector('#detail dd.why .reason').textContent,
  checked: document.querySelector('#detail dd.why .checked')?.textContent ?? null,
  badges: [...document.querySelectorAll('#detail h3 .lvl, #detail h3 .blocked')].map(b => b.textContent) }));

test('why: each reason class shows the verifier\'s sentence and the date it was checked in the detail panel', async () => {
  const body = await whyBuilt;
  const byId = Object.fromEntries(body.records.map(r => [r.id, r]));
  const { context, page, errors } = await open('sel=equinor/volve', { routes: withWhy });
  for (const [id, want] of Object.entries(CLASSES)) {
    // a click in the list selects directly; a hash written while the previous fly-to ends can be
    // replaced by that fly's own moveend before hashchange runs (slow runners, PR #36)
    await page.locator(`#list li[data-id="${id}"]`).click();
    await page.waitForFunction(t => document.querySelector('#detail h3 .title')?.textContent === t, byId[id].title);
    const got = await whyOf(page);
    assert.equal(await page.locator('#detail dt', { hasText: /^Why this level$/ }).count(), 1, id);
    assert.equal(got.reason, body.reasons[id], id);
    assert.match(got.reason, want, id);
    assert.equal(got.checked, byId[id].checked_at ? 'checked 23 Oct 2026' : null, id);
  }
  assert.deepEqual(errors, []);
  await context.close();
});

test('why: a blocked record shows the OSD-D20 sentence and no level badge, in the panel and the list', async () => {
  const { context, page, errors } = await open('sel=nm-ocd/oil-and-gas-wells', { routes: withWhy });
  const got = await whyOf(page);
  assert.match(got.reason, /answers a browser, not the verifier/);
  assert.deepEqual(got.badges, ['blocked since 2026-10-21']);
  assert.equal(await page.locator('#list li[data-id="nm-ocd/oil-and-gas-wells"] .lvl').count(), 0);
  assert.equal(await page.locator('#list li[data-id="nm-ocd/oil-and-gas-wells"] .blocked').innerText(), 'blocked since 2026-10-21');
  await page.locator('#list li[data-id="sodir/factpages"]').click();
  await page.waitForFunction(() => /^sample/.test(document.querySelector('#detail dd.why .reason').textContent));
  assert.deepEqual((await whyOf(page)).badges, ['L2']);
  assert.deepEqual(errors, []);
  await context.close();
});

test('why: phone width, the detail panel of a blocked and of an L2 record', async () => {
  for (const [id, name] of [['nm-ocd/oil-and-gas-wells', 'phone-detail-blocked'], ['sodir/factpages', 'phone-detail-l2']]) {
    const { context, page, errors } = await open(`sel=${id}`, { viewport: { width: 390, height: 844 }, routes: withWhy });
    const why = page.locator('#detail dd.why');
    await page.locator('#detail h3').scrollIntoViewIfNeeded();
    assert.ok(await why.isVisible(), 'the Why row shows with the title, first in the panel');
    const b = await why.boundingBox();
    assert.ok(b.x >= 0 && b.x + b.width <= 390, 'the Why row fits the sheet');
    assert.ok(await page.evaluate(() => { const s = document.getElementById('side'); return s.scrollWidth <= s.clientWidth; }), 'no horizontal overflow');
    // clipped to the sheet: full-viewport phone captures can show a black map canvas under swiftshader (HANDOFF)
    const sheet = await page.locator('#side').boundingBox();
    await page.screenshot({ path: join(OUT, `${name}.png`), clip: { x: 0, y: sheet.y, width: 390, height: sheet.height } });
    assert.deepEqual(errors, []);
    await context.close();
  }
});

test('why: the share hash and the filters are unchanged by the reason', async () => {
  const hash = 'k=wellbore-headers&l=1&sel=sodir/factpages';
  const { context, page, errors } = await open(hash, { routes: withWhy });
  assert.equal((await page.evaluate(() => location.hash)).replace(/&map=[^&]*/, ''), '#' + hash);
  const body = await whyBuilt;
  const want = body.records.filter(r => Number(r.level.slice(1)) >= 1 && r.kinds.includes('wellbore-headers')).map(r => r.id);
  assert.deepEqual((await listed(page)).sort(), want.sort());
  assert.ok(!want.includes('nm-ocd/oil-and-gas-wells') && want.includes('sodir/factpages'), 'blocked is L0 to the filter');
  assert.match(await page.locator('#detail dd.why .reason').innerText(), /^sample, not the whole dataset/);
  assert.deepEqual(errors, []);
  await context.close();
});

test('why: the basket to-do names the verifier\'s reason; a never-verified dataset keeps the access sentence', async () => {
  const { context, page, errors } = await open('pick=gsq/qped,terranubis/f3-demo-2020', { routes: withWhy });
  await page.waitForFunction(() => [...document.querySelectorAll('#basket .files')].every(e => !/…/.test(e.textContent)));
  assert.equal(await page.locator('#basket li[data-id="gsq/qped"] .files').innerText(), 'to-do: files-checksummed: the listing (ckan) names no files');
  assert.match(await page.locator('#basket li[data-id="terranubis/f3-demo-2020"] .files').innerText(), /^to-do: access registration/);
  assert.deepEqual(errors, []);
  await context.close();
});

test('why: the status page shows a sortable Why column on desktop and hides it at phone width', async () => {
  const body = await whyBuilt;
  const context = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
  await offline(context);
  await withWhy(context);
  const page = await context.newPage();
  const errors = errorsOf(page);
  await page.goto(server.url + 'status.html');
  await page.waitForFunction(() => document.querySelectorAll('#status tbody tr').length > 0);
  const rows = () => page.$$eval('#status tbody tr', trs => trs.map(tr => [tr.dataset.id, tr.querySelector('td.why').textContent]));
  const got = Object.fromEntries(await rows());
  for (const id of Object.keys(CLASSES)) assert.equal(got[id], body.reasons[id], id);
  assert.equal(await page.locator('th[data-key="reason"]').innerText(), 'Why');
  await page.click('th[data-key="reason"]');
  const up = (await rows()).map(r => r[1]);
  assert.deepEqual(up, [...up].sort());
  assert.equal(await page.getAttribute('th[data-key="reason"]', 'aria-sort'), 'ascending');
  await page.click('th[data-key="checked_at"]'); await page.click('th[data-key="checked_at"]');   // checked rows first
  assert.ok(await page.evaluate(() => document.querySelector('.wrap').scrollWidth <= document.querySelector('.wrap').clientWidth), 'the table fits a desktop screen');
  await page.screenshot({ path: join(OUT, 'status-desktop.png'), fullPage: false });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.locator('th[data-key="reason"]').isVisible(), false);
  assert.equal(await page.locator('#status tbody tr td.why').first().isVisible(), false);
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= 390), 'no horizontal overflow on the phone');
  await page.screenshot({ path: join(OUT, 'status-phone.png'), fullPage: false });
  assert.deepEqual(errors, []);
  await context.close();
});

test('why: how.html lists the reason sentences and what a publisher can do about each', async () => {
  const context = await browser.newContext();
  await offline(context);
  const page = await context.newPage();
  await page.goto(server.url + 'how.html');
  const text = await page.locator('#why').innerText();
  for (const s of ['never verified', 'no file address is published to us', 'names no files', 'robots.txt disallows',
    'answers a browser, not the verifier', 'blocked from this runner', 'HTTP 502', 'files were hashed'])
    assert.ok(text.includes(s), s);
  await context.close();
});

// ---- E43: starter projects. E40's fixture packs (tests/fixtures/starters, with the custody snapshot)
// built by osd.build into build/site-test/e43; the page is served the committed records.json with the
// two fixture records in place of the committed ones (they carry `starters`), and the fixture build's
// starters.json and data/starters/. Without these routes the build has no pack (until E42).
const E43_DIR = join(OUT, 'e43');
const F3_RECORD = 'terranubis/f3-demo-2020', F3_PACK = 'terranubis/f3-demo-2020/starter', F3_ANCHOR = 'terranubis__f3-demo-2020__starter';
const FX = join(ROOT, 'tests', 'fixtures', 'starters');
const starterBuilt = (async () => {
  await promisify(execFile)(process.env.UV || 'uv', ['run', '--quiet', 'python', '-c',
    'import sys, shutil; from pathlib import Path; from osd.build import build\n' +
    'out, fx, custody, mirror = map(Path, sys.argv[1:5])\n' +
    'shutil.rmtree(mirror, ignore_errors=True); shutil.copytree(custody, mirror / "custody")\n' +
    'build(out, fx / "verification", mirror_dir=mirror, records_dir=fx / "records", starters_dir=fx / "packs", source_commit="1" * 40, verification_commit="2" * 40)',
    E43_DIR, FX, join(ROOT, 'tests', 'fixtures', 'custody'), join(OUT, 'e43-mirror')], { cwd: ROOT });
  const fx = JSON.parse(await readFile(join(E43_DIR, 'records.json'), 'utf8'));
  return { records: Object.fromEntries(fx.records.map(r => [r.id, r])), starters: JSON.parse(await readFile(join(E43_DIR, 'starters.json'), 'utf8')) };
})();
const withStarters = async c => {
  const fx = await starterBuilt;
  await c.route('**/data/records.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    body.records = body.records.map(r => fx.records[r.id] || r);
    return route.fulfill({ json: body });
  });
  await c.route('**/data/starters.json', route => route.fulfill({ json: fx.starters }));
  await c.route('**/data/starters/**', route => route.fulfill({ contentType: 'application/json',
    path: join(E43_DIR, 'starters', decodeURIComponent(new URL(route.request().url()).pathname.replace(/^\/data\/starters\//, ''))) }));
};
// The same build with no pack: what the site shows until E42 publishes one.
const withoutStarters = async c => {
  await c.route('**/data/records.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    for (const r of body.records) delete r.starters;
    return route.fulfill({ json: body });
  });
  await c.route('**/data/starters.json', route => route.fulfill({ json: { starters: [] } }));
};
const fixturePack = name => JSON.parse(readFileSync(join(FX, 'packs', name), 'utf8'));
const asked = (page, path) => { const seen = []; page.on('request', q => { if (new URL(q.url()).pathname === path) seen.push(q.url()); }); return seen; };
const sheetOverflows = page => page.evaluate(() => { const s = document.getElementById('side'); return s.scrollWidth > s.clientWidth; });

test('starter: the F3-shaped record shows a fourth card with the pack\'s buttons, licence line and decision-log link', async () => {
  const pack = fixturePack(`${F3_ANCHOR}.json`);
  const { context, page, errors, unexpected } = await open(`sel=${F3_RECORD}`, { routes: withStarters });
  const card = page.locator('#detail .card.starter');
  await card.locator('.app').first().waitFor();
  assert.deepEqual(await page.locator('#detail .card > b').allInnerTexts(), ['Open in QGIS', 'Read in Python', 'Get the data', 'Starter project']);
  assert.deepEqual(await card.locator('.app').evaluateAll(bs => bs.map(b => b.dataset.app)), pack.targets.map(t => t.application));
  assert.deepEqual(await card.locator('.app').allInnerTexts(), ['OpendTect 7.0.10', 'ResInsight 2025.04', 'Python 3.12']);
  assert.match(await card.locator('.lic').innerText(), /^CC-BY-SA-3\.0 · attribution required · share-alike · what we decided$/);
  assert.match(await card.locator('.steps').innerText(), /^1\. download the pack manifest · 2\. osd get terranubis__f3-demo-2020__starter\.manifest\.json --dest terranubis__f3-demo-2020 · 3\. run opendtect\/import_f3\.py \(OpendTect 7\.0\.10\)$/);
  await card.locator('.app[data-app="resinsight"]').click();
  assert.match(await card.locator('.steps').innerText(), /run resinsight\/import_f3\.py \(ResInsight 2025\.04\)$/);
  assert.equal(await card.locator('.app[aria-pressed="true"]').innerText(), 'ResInsight 2025.04');
  assert.equal(await page.locator('#starterlink').isVisible(), true);
  await page.locator('#detail .card.starter').scrollIntoViewIfNeeded();
  const [cb, pb] = [await card.boundingBox(), await page.locator('#detail').boundingBox()];
  assert.ok(cb.x + cb.width <= pb.x + pb.width, 'the card fits the panel');
  await page.locator('#side').screenshot({ path: join(OUT, 'starter-card-desktop.png') });

  await card.locator('a', { hasText: 'what we decided' }).click();
  await page.waitForURL(`**/starters.html#${F3_ANCHOR}-decisions`);
  const log = page.locator(`#${F3_ANCHOR}-decisions`);
  await log.waitFor();
  assert.equal(await page.locator(`section#${F3_ANCHOR} #${F3_ANCHOR}-decisions`).count(), 1, 'the anchor is in the pack\'s section');
  assert.equal(await page.locator(`section#${F3_ANCHOR} table.log tbody tr`).count(), pack.decisions.length);
  assert.equal(await page.locator(`section#${F3_ANCHOR} table.log tr.chosen`).count(), pack.decisions.filter(d => d.source === 'chosen').length);
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

test('starter: with no pack in the build, no fourth card, no header link, no filter, and the page says so', async () => {
  const { context, page, errors, unexpected } = await open(`sel=${F3_RECORD}&starter=1`, { routes: withoutStarters });
  const all = await page.evaluate(() => window.osdMap && document.querySelectorAll('#list li').length);
  assert.ok(all > 100, 'starter=1 is ignored while no dataset has a pack');
  assert.equal(await page.locator('#detail .card').count(), 3);
  assert.equal(await page.locator('#detail .card.starter').count(), 0);
  assert.equal(await page.locator('#starterlink').isVisible(), false);
  assert.equal(await page.locator('#starterfilter').isVisible(), false);
  assert.doesNotMatch(await page.evaluate(() => location.hash), /starter=/);
  for (const p of ['how.html', 'status.html']) {
    await page.goto(server.url + p);
    await page.waitForLoadState('networkidle');
    assert.equal(await page.locator('#starterlink').isVisible(), false, p);
  }
  await page.goto(server.url + 'starters.html');
  await page.locator('#none').waitFor();
  assert.equal(await page.locator('#none').innerText(), 'No starter projects yet.');
  assert.equal(await page.locator('section.pack').count(), 0);
  assert.match(await page.locator('#ask a').getAttribute('href'), /issues\/new\?template=starter-request\.yml$/);
  await page.screenshot({ path: join(OUT, 'starters-empty.png'), fullPage: true });
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

test('starter: #starter=1 lists exactly the two fixture records; unticking restores the count; starters.json waits for a card', async () => {
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  await offline(context);
  await withStarters(context);
  const page = await context.newPage();
  const errors = errorsOf(page), fetched = asked(page, '/data/starters.json');
  await page.goto(server.url + '#starter=1');
  await ready(page);
  assert.deepEqual((await listed(page)).sort(), ['rmotc/teapot-dome', F3_RECORD]);
  assert.equal(await page.locator('#starter').isChecked(), true);
  assert.equal(await page.locator('#starterfilter').isVisible(), true);
  const total = await page.evaluate(() => document.getElementById('count').textContent.match(/of (\d+)/)[1]);
  assert.equal(await page.locator('#count').textContent(), `(2 of ${total})`);
  await page.locator('#starter').uncheck();
  assert.equal(await page.locator('#count').textContent(), `(${total} of ${total})`);
  assert.doesNotMatch(await page.evaluate(() => location.hash), /starter=/);
  await page.locator('#starter').check();
  assert.match(await page.evaluate(() => location.hash), /starter=1/);
  assert.deepEqual(fetched, [], 'the map does not load starters.json for the list or the filter');
  await page.locator(`#list li[data-id="${F3_RECORD}"]`).click();
  await page.locator('#detail .card.starter .app').first().waitFor();
  assert.equal(fetched.length, 1, 'starters.json is fetched once a card needs it');
  await page.screenshot({ path: join(OUT, 'starter-filter.png') });
  assert.deepEqual(errors, []);
  await context.close();
});

test('starter: "Download the pack manifest" writes the manifest/4 osd manifest --starter writes, artefacts equal by sha256', async () => {
  const pack = fixturePack(`${F3_ANCHOR}.json`);
  const { context, page, errors, unexpected } = await open(`sel=${F3_RECORD}`, { routes: withStarters });
  const button = page.locator('#detail .card.starter .starter-download');
  await button.waitFor();
  assert.equal(await button.innerText(), 'Download the pack manifest');
  const [dl] = await Promise.all([page.waitForEvent('download'), button.click()]);
  assert.equal(dl.suggestedFilename(), `${F3_ANCHOR}.manifest.json`);
  const file = join(OUT, `${F3_ANCHOR}.manifest.json`);
  await dl.saveAs(file);
  const doc = JSON.parse(await readFile(file, 'utf8'));
  assert.equal(doc.format, 'osd.manifest/4');
  // osd.manifest.read accepts it; its entries equal what `osd manifest --starter` writes from the same build
  const { stdout } = await promisify(execFile)(process.env.UV || 'uv', ['run', '--quiet', 'python', '-c',
    'import json, sys; from pathlib import Path; from osd import manifest as mf\n' +
    'page = json.loads(Path(sys.argv[1]).read_text()); m = mf.read(sys.argv[1])\n' +
    'want = mf.from_starter(sys.argv[3], catalog_dir=Path(sys.argv[2]), catalog_url=page["catalog_url"])\n' +
    'assert page["format"] == want["format"] and page["entries"] == want["entries"], (page["entries"], want["entries"])\n' +
    'print(json.dumps({a.key: a.sha256 for e in m.entries for a in e.assets}))',
    file, E43_DIR, F3_PACK], { cwd: ROOT });
  const got = JSON.parse(stdout.trim().split('\n').pop());
  const want = Object.fromEntries(pack.targets.flatMap(t => t.artefacts.map(a => [a.path, a.sha256])));
  const { 'starter.json': doc256, 'fidelity.json': fid256, ...artefacts } = got;
  assert.deepEqual(artefacts, want);
  assert.equal(doc256, createHash('sha256').update(readFileSync(join(FX, 'packs', `${F3_ANCHOR}.json`))).digest('hex'));
  assert.equal(fid256, createHash('sha256').update(readFileSync(join(FX, 'packs', pack.fidelity))).digest('hex'));
  console.log(`# pack manifest: ${Object.keys(artefacts).length} artefacts and 2 pack documents, entries equal to osd manifest --starter`);
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});
