// The speed practices of Shop 06 (E50; R-S7 of docs/program/charters/MAP-AS-A-SHOP-family.md), each
// checked over /shop.html, and the measuring mode (/shop.html?measure=1, site/measure.js) run once.
// A practice not yet in the page is a test.todo naming it: its body runs and reports, it does not
// fail the run. The tile archives' practices (1: tiles under 500 KB; 6: clustered, one leaf level)
// are read from the built files by tests/test_tiles.py. Offline, over the build in site/data, like
// shop.test.mjs; run by `make site-test`. Numbers here are a headless controller's: a method check,
// not a measurement of a real machine (docs/program/evidence/e50/measurements.md).
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { ROOT, serve, launch, errorsOf } from './harness.mjs';
import { shopOffline, shopReady } from './shop-harness.mjs';

const OUT = join(ROOT, 'build', 'site-test', 'e50');
const SHOP_JS = await readFile(join(ROOT, 'site', 'shop.js'), 'utf8');
const MEASURE_JS = join(ROOT, 'site', 'measure.js');
// Until shop.js carries its one hook line (`?measure=1` loads measure.js), the test loads the
// measuring mode itself, before any page script, as the hook will.
const HOOKED = /measure\.js/.test(SHOP_JS);
let server, browser;
before(async () => { await mkdir(OUT, { recursive: true }); server = await serve(); browser = await launch(); });
after(async () => { await browser.close(); server.close(); });

const DESKTOP = { width: 1400, height: 900 };
const NORTH_SEA = 'map=5.00/57.0000/3.0000', GULF = 'map=5.00/27.0000/-91.0000', NORTH_SEA_7 = 'map=7.50/58.5000/2.0000';

async function open(hash = NORTH_SEA, { query = '', measure = false, init, routes } = {}) {
  const context = await browser.newContext({ viewport: DESKTOP });
  const unexpected = [];
  await shopOffline(context, unexpected);
  if (measure && !HOOKED) await context.addInitScript({ path: MEASURE_JS });
  if (init) await context.addInitScript(init);
  if (routes) await routes(context);
  const page = await context.newPage();
  const errors = errorsOf(page);
  const requested = [];
  page.on('request', r => requested.push(r.url()));
  await page.goto(server.url + 'shop.html' + query + (hash ? '#' + hash : ''));
  await shopReady(page);
  return { context, page, errors, unexpected, requested };
}

// Counts calls of the named Map methods on the page's map from now on.
async function spy(page, names) {
  await page.evaluate(names => {
    const m = window.osdMap; window.__calls = Object.fromEntries(names.map(n => [n, 0]));
    for (const n of names) { const f = m[n].bind(m); m[n] = (...a) => { window.__calls[n]++; return f(...a); }; }
  }, names);
  return () => page.evaluate(() => ({ ...window.__calls }));
}
const settle = page => page.evaluate(() => new Promise(ok => { const m = window.osdMap;
  m.loaded() && m.areTilesLoaded() && !m.isMoving() ? ok() : m.once('idle', ok); }));
async function jump(page, hashView) {
  const [z, lat, lon] = hashView.slice(4).split('/').map(Number);
  await page.evaluate(([z, lat, lon]) => new Promise(ok => { window.osdMap.once('idle', ok); window.osdMap.jumpTo({ zoom: z, center: [lon, lat] }); }), [z, lat, lon]);
}

// ---- The measuring mode ---------------------------------------------------------------------------

test('measuring mode: /shop.html?measure=1 shows the four numbers and keeps them in window.osdMeasure', async () => {
  const { context, page, errors, unexpected } = await open(NORTH_SEA, { query: '?measure=1', measure: true });
  const r = await page.evaluate(() => window.osdMeasure.done);
  await page.locator('#osd-measure').screenshot({ path: join(OUT, 'readout.png') });
  await page.screenshot({ path: join(OUT, 'measure.png') });
  await writeFile(join(OUT, 'controller.json'), JSON.stringify(r, null, 2));
  const tiles = Object.entries(r.site.files).filter(([f]) => f.endsWith('.pmtiles'));
  console.log(`controller (headless Chromium, SwiftShader, ${r.screen.w}x${r.screen.h}): usable ${r.idleMs} ms, list ${r.listMs} ms; ` +
    `drag+zoom ${r.script.fps} fps (longest frame ${r.script.longestFrameMs} ms); zoom out ${r.zoomOutBack.out.requests} req ` +
    `${r.zoomOutBack.out.bytes} B, back ${r.zoomOutBack.back.requests} req ${r.zoomOutBack.back.bytes} B; site since load ` +
    `${r.site.requests} req ${r.site.bytes} B (at first idle ${r.atIdle.requests} req ${r.atIdle.bytes} B)` + tiles.map(([f, v]) => `; ${f} ${v.requests} ranges ${v.bytes} B`).join(''));
  assert.equal(r.done, true);
  assert.equal(r.late, false, 'the measuring mode saw the map before its first idle');
  for (const k of ['idleMs', 'listMs']) assert.ok(Number.isFinite(r[k]) && r[k] > 0, k);
  assert.ok(r.script.frames > 10 && r.script.fps > 0, 'frames were counted over the scripted drag and zoom');
  assert.ok(r.site.requests > 0 && r.site.files['records.json'], 'the site\'s files are counted, records.json among them');
  assert.ok(Number.isInteger(r.zoomOutBack.back.requests));
  const text = await page.locator('#osd-measure').innerText();
  for (const l of ['1 usable', '2 drag+zoom', '3 zoom back', '4 site since load']) assert.ok(text.includes(l), l);
  assert.deepEqual(errors, []); assert.deepEqual(unexpected, []);
  await context.close();
});

test('measuring mode: the normal page asks for no measure.js', async () => {
  const { context, requested } = await open(NORTH_SEA);
  assert.ok(!requested.some(u => u.includes('measure.js')));
  assert.equal(await context.pages()[0].evaluate(() => 'osdMeasure' in window), false);
  await context.close();
});

(HOOKED ? test : test.todo)('measuring mode: shop.js loads measure.js only with ?measure=1 (the one hook line; after E49 slice 4 releases shop.js)', () => {
  assert.ok(/measure=1|has\('measure'\)|get\('measure'\)/.test(SHOP_JS), 'shop.js names ?measure=1');
});

// ---- The eight practices --------------------------------------------------------------------------

test('practice 1 (zoomed out): wells are counted circles below the cluster zoom (E36, kept)', async () => {
  const { context, page } = await open(NORTH_SEA);
  const n = await page.evaluate(() => window.osdMap.querySourceFeatures('wells').filter(f => f.properties.point_count).length);
  const layer = await page.evaluate(() => window.osdMap.getLayer('wells-cluster') && window.osdMap.getLayer('wells-cluster').filter);
  console.log(`North Sea z5: ${n} counted circles`);
  assert.ok(layer, 'a wells-cluster layer is drawn');
  assert.ok(n > 0, 'counted circles at z5 over the North Sea');
  await context.close();
});

test('practice 2: the list follows the map window with no queryRenderedFeatures or querySourceFeatures call', async () => {
  const { context, page } = await open(NORTH_SEA);
  const calls = await spy(page, ['queryRenderedFeatures', 'querySourceFeatures']);
  const lists = [await page.evaluate(() => window.osdShop.listIds().join())];
  for (const v of [GULF, NORTH_SEA_7, NORTH_SEA]) { await jump(page, v); await settle(page); lists.push(await page.evaluate(() => window.osdShop.listIds().join())); }
  assert.notEqual(lists[0], lists[1], 'the list changed with the window');
  assert.equal(lists[0], lists[3], 'back where it was, the same list');
  assert.deepEqual(await calls(), { queryRenderedFeatures: 0, querySourceFeatures: 0 });
  await context.close();
});

const OURS = new Set(['fields-fill', 'fields-line', 'fields-dash', 'surveys-fill', 'surveys-line', 'surveys-dash',
  'wells-cluster', 'wells-count', 'wells', 'wells-tiles', 'boxes', 'boxes-name']);
const layersOf = page => page.evaluate(() => window.osdMap.getStyle().layers.map(l => ({ id: l.id, type: l.type,
  minzoom: l.minzoom ?? 0, maxzoom: l.maxzoom ?? 24 })));

test('practice 3: the shop\'s layers, their count and zoom ranges (printed for the PR)', async () => {
  const { context, page } = await open(NORTH_SEA);
  const all = await layersOf(page), ours = all.filter(l => OURS.has(l.id));
  console.log(`style: ${all.length} layers (${all.length - ours.length} of the base map, ${ours.length} of the shop)`);
  for (const l of ours) console.log(`  ${l.id.padEnd(14)} ${l.type.padEnd(7)} z${l.minzoom}-${l.maxzoom}`);
  await writeFile(join(OUT, 'layers.json'), JSON.stringify(all, null, 2));
  const tiles = ours.find(l => l.id === 'wells-tiles');
  if (tiles) assert.equal(tiles.minzoom, 7, 'single wells from the tiles only from the cluster zoom');
  assert.ok(ours.length <= OURS.size);
  await context.close();
});

test.todo('practice 3: the counted circles stop at the cluster zoom (wells-cluster, wells-count, wells maxzoom 7)', async () => {
  const { context, page } = await open(NORTH_SEA);
  const ours = (await layersOf(page)).filter(l => ['wells-cluster', 'wells-count', 'wells'].includes(l.id));
  await context.close();
  for (const l of ours) assert.equal(l.maxzoom, 7, l.id);
});

const option = read => async () => {
  const { context, page } = await open(NORTH_SEA);
  const v = await page.evaluate(read);
  await context.close();
  return v;
};
test.todo('practice 4: tiles of five zoom levels stay in memory (maxTileCacheZoomLevels set explicitly, 5 or more)', async () => {
  assert.ok(/maxTileCacheZoomLevels:\s*\d+/.test(SHOP_JS), 'shop.js sets maxTileCacheZoomLevels');
  const v = await option(() => window.osdMap._maxTileCacheZoomLevels)();
  assert.ok(v >= 5, String(v));
});
test.todo('practice 5: expired tiles are not asked for again (refreshExpiredTiles: false)', async () => {
  assert.equal(await option(() => window.osdMap._refreshExpiredTiles)(), false);
});

test('practice 6: the PMTiles protocol is registered once', () => {
  assert.equal((SHOP_JS.match(/addProtocol\(/g) || []).length, 1);
});

test('practice 7: hovering rows lights features by feature state; no setFilter, setPaintProperty or setLayoutProperty', async () => {
  const { context, page } = await open(NORTH_SEA);
  const calls = await spy(page, ['setFilter', 'setPaintProperty', 'setLayoutProperty', 'setFeatureState']);
  const rows = page.locator('#list > ul > li');
  const n = Math.min(await rows.count(), 6);
  assert.ok(n > 0, 'rows to hover');
  for (let i = 0; i < n; i++) await rows.nth(i).hover();
  await page.mouse.move(DESKTOP.width - 10, DESKTOP.height / 2);
  const c = await calls();
  console.log(`hovered ${n} rows:`, c);
  assert.deepEqual([c.setFilter, c.setPaintProperty, c.setLayoutProperty], [0, 0, 0]);
  assert.ok(c.setFeatureState > 0, 'the hovered records lit by feature state');
  await context.close();
});

test.todo('practice 8: names without the slow fade (fadeDuration 0)', async () => {
  assert.equal(await option(() => window.osdMap._fadeDuration)(), 0);
});

// ---- Measurement 2, the return visit ------------------------------------------------------------

test('return visit: a header range answered with the whole file (a stale ETag at the host) keeps the tiles on', async () => {
  // As measured on 25 Nov 2026 (docs/program/evidence/e50/measurements.md): after max-age, Chrome asks
  // for the cached range with If-Range and an ETag another GitHub Pages server no longer gives, and
  // gets 200 with the whole file. Here the first header request gets a 200 with more than it asked.
  const headers = [];
  const { context, page, requested } = await open(NORTH_SEA, { routes: async ctx => {
    await ctx.route(u => u.pathname.endsWith('/data/outlines.pmtiles'), async route => {
      const range = route.request().headers().range || '';
      if (range.startsWith('bytes=0-')) headers.push(range);
      if (range.startsWith('bytes=0-') && headers.length === 1) {
        const r = await route.fetch({ headers: { ...route.request().headers(), range: 'bytes=0-65535' } });
        return route.fulfill({ status: 200, body: await r.body(), headers: { 'content-type': 'application/octet-stream' } });
      }
      return route.continue();
    });
  } });
  assert.equal(headers.length, 2, 'the header was asked for twice');
  assert.ok(!requested.some(u => u.endsWith('outlines.geojson')), 'no fall back to the whole GeoJSON');
  assert.ok(await page.evaluate(() => !!window.osdMap.getLayer('wells-tiles')), 'the map draws from the tiles');
  await context.close();
});
