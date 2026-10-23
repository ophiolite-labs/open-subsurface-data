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
  const { context, page, errors } = await open('map=5/59/5', { routes: c => c.route('**/data/outlines.geojson', async route => {
    const fc = JSON.parse(await (await route.fetch()).text());
    fc.features.push(...wells);
    return route.fulfill({ json: fc });
  }) });

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
