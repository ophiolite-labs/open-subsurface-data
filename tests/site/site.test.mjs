// Playwright site test for E05: `make site-test` (node --test tests/site/). Offline by default.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { ROOT, serve, launch, offline, errorsOf, ready } from './harness.mjs';

const OUT = join(ROOT, 'build', 'site-test');
let server, browser;
before(async () => { await mkdir(OUT, { recursive: true }); server = await serve(); browser = await launch(); });
after(async () => { await browser.close(); server.close(); });

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
  // the synthetic set replaces the committed outlines, so the budget measures these N points alone
  const { context, page, errors } = await open('map=5/59/5', { routes: c => c.route('**/data/outlines.geojson',
    route => route.fulfill({ json: { type: 'FeatureCollection', features: wells } })) });

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

  await browser.startTracing(page, { path: join(OUT, 'pan-trace.json'), screenshots: false });
  const frames = [];
  for (const [dx, dy] of [[300, 0], [0, 200], [-300, 0], [0, -200], [250, 150]]) {
    frames.push(await page.evaluate(([dx, dy]) => new Promise(ok => {
      const m = window.osdMap;
      m.once('moveend', () => { const t0 = performance.now(); requestAnimationFrame(() => ok(performance.now() - t0)); });
      m.panBy([dx, dy], { duration: 400 });
    }), [dx, dy]));
  }
  await browser.stopTracing();
  console.log('# 10k wellbores at zoom 5:', JSON.stringify(seen), 'frame after moveend (ms):', frames.map(f => f.toFixed(1)).join(', '));
  await page.screenshot({ path: join(OUT, 'clusters-10k.png') });
  assert.ok(Math.max(...frames) < 100, `frame after moveend ${Math.max(...frames).toFixed(1)} ms`);
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
// The GeoJSON path on the same build: files.txt without the tiles.
const withoutTiles = c => c.route('**/data/files.txt', async route =>
  route.fulfill({ body: (await (await route.fetch()).text()).split('\n').filter(f => f !== 'outlines.pmtiles').join('\n') }));
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

test('tiles: #q=sodir, a click on a wellbore shows the same detail title as the GeoJSON path', { skip: noTiles }, async () => {
  const hash = 'q=sodir&map=10/60.55/2.85';
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
