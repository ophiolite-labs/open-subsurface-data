// The journey of the family "The map as a shop" (docs/program/charters/MAP-AS-A-SHOP-family.md):
// fifteen steps by name, over /shop.html. A step no merged slice lights yet is a test.todo naming its
// epic. Offline, over the build in site/data (`make build`), like site.test.mjs; run by `make site-test`.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { ROOT, serve, launch, errorsOf, ready } from './harness.mjs';
import { shopOffline, shopReady } from './shop-harness.mjs';

const OUT = join(ROOT, 'build', 'site-test', 'shop');
const run = promisify(execFile);
let server, browser;
before(async () => { await mkdir(OUT, { recursive: true }); server = await serve(); browser = await launch(); });
after(async () => { await browser.close(); server.close(); });

const DESKTOP = { width: 1400, height: 900 }, PHONE = { width: 390, height: 844 };
const NORTH_SEA = 'map=5.00/57.0000/3.0000', WORLD = 'map=0.50/20.0000/0.0000';
const committed = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8'));
const committedAreas = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'areas.json'), 'utf8').catch(() => '{"kinds":{}}'));
const files = (await readFile(join(ROOT, 'site', 'data', 'files.txt'), 'utf8').catch(() => '')).split('\n');
const noTiles = !files.includes('outlines.pmtiles') && (process.env.CI ? false : 'no data/outlines.pmtiles (tippecanoe not installed)');

async function open(hash = '', { viewport = DESKTOP, routes, page: path = 'shop.html' } = {}) {
  const context = await browser.newContext({ viewport, acceptDownloads: true });
  const unexpected = [];
  await shopOffline(context, unexpected);
  if (routes) await routes(context);
  const page = await context.newPage();
  const errors = errorsOf(page);
  await page.goto(server.url + path + (hash ? '#' + hash : ''));
  await (path === 'shop.html' ? shopReady(page) : ready(page));
  return { context, page, errors, unexpected };
}

// ---- The rule of design 3, written again here: the test does not ask the page how it decides ----
// A record meets the window by its bbox, else the box of the countries the build placed it in
// (records[].areas.country, the boxes from areas.json), else it has no place and is listed only below
// the world zoom; wholly inside first, then by title. On the globe with the whole earth in view, every
// dataset is listed (E48 design 5).
const collator = new Intl.Collator('en');
async function windowOf(page) {
  return page.evaluate(() => { const b = window.osdMap.getBounds();
    const c = window.osdMap.getCanvas(), globe = (window.osdMap.getProjection() || {}).type === 'globe';
    return { w: b.getWest(), e: b.getEast(), s: b.getSouth(), n: b.getNorth(), zoom: window.osdMap.getZoom(),
      earth: globe && 512 * 2 ** window.osdMap.getZoom() / Math.PI <= Math.min(c.clientWidth, c.clientHeight), worldZoom: window.osdShop.worldZoom }; });
}
function boxOf(r, areas) {
  if (r.region && r.region.bbox) return r.region.bbox;
  const bs = ((r.areas || {}).country || []).map(id => ((areas.kinds.country || {}).areas || []).find(a => a.area_id === id)).filter(Boolean).map(a => a.bbox);
  if (bs.length < 2) return bs[0];
  if (bs.some(b => b[0] > b[2])) return [-180, Math.min(...bs.map(b => b[1])), 180, Math.max(...bs.map(b => b[3]))];
  return [Math.min(...bs.map(b => b[0])), Math.min(...bs.map(b => b[1])), Math.max(...bs.map(b => b[2])), Math.max(...bs.map(b => b[3]))];
}
function expected(recs, win, areas = committedAreas) {
  if (win.earth) Object.assign(win, { w: -180, e: 180, s: -90, n: 90, zoom: -1 });
  // the window's longitudes on [-180, 180]: one interval, two across the antimeridian, all when it wraps
  const w0 = ((win.w + 180) % 360 + 360) % 360 - 180, e0 = w0 + (win.e - win.w);
  const wr = win.e - win.w >= 360 ? [[-180, 180]] : e0 > 180 ? [[w0, 180], [-180, e0 - 360]] : [[w0, e0]];
  const inside = [], meets = [], noplace = [];
  for (const r of recs) {
    const b = boxOf(r, areas);
    if (!b) { if (win.zoom < win.worldZoom) noplace.push(r); continue; }
    const [w, s, e, n] = b, br = w <= e ? [[w, e]] : [[w, 180], [-180, e]];
    if (s > win.n || n < win.s || !br.some(([a, c]) => wr.some(([x, y]) => a <= y && c >= x))) continue;
    (s >= win.s && n <= win.n && br.every(([a, c]) => wr.some(([x, y]) => a >= x && c <= y)) ? inside : meets).push(r);
  }
  const t = (a, b) => collator.compare(a.title, b.title) || (a.id < b.id ? -1 : 1);
  return { ids: [...inside.sort(t), ...meets.sort(t)].map(r => r.id), noplace: noplace.sort(t).map(r => r.id) };
}
const listed = page => page.evaluate(() => ({ ids: window.osdShop.listIds(), noplace: window.osdShop.noPlaceIds(),
  dom: [...document.querySelectorAll('#list > ul > li')].map(l => l.dataset.id),
  domNoplace: [...document.querySelectorAll('#noplace li')].map(l => l.dataset.id),
  count: document.getElementById('count').textContent }));
const moveTo = (page, center, zoom) => page.evaluate(([center, zoom]) => new Promise(ok => {
  window.osdMap.once('moveend', () => setTimeout(ok, 0)); window.osdMap.jumpTo({ center, zoom }); }), [center, zoom]);

async function assertListFollows(page, recs, where, areas) {
  const win = await windowOf(page), want = expected(recs, win, areas), got = await listed(page);
  assert.deepEqual(got.ids, want.ids, `${where}: the list is the window's set, wholly inside first, then by title`);
  assert.deepEqual(got.noplace, want.noplace, `${where}: no place stated`);
  assert.deepEqual(got.dom, got.ids, `${where}: the rows drawn are the list`);
  assert.deepEqual(got.domNoplace, got.noplace);
  const n = got.ids.length + got.noplace.length;
  assert.equal(new Set([...got.ids, ...got.noplace]).size, n, `${where}: no dataset twice`);
  assert.equal(got.count, `${n} dataset${n === 1 ? '' : 's'} in this view`);
  return got;
}

// ---- Fixtures shared with site.test.mjs's shape: files on a local origin, the verifier's assets ----
const FIXTURE = { 'opm--norne': { 'norne/NORNE_ATW2013.DATA': 'RUNSPEC\nTITLE\nNORNE fixture\n' },
  'sodir--factpages': { 'wellbore_exploration_all.csv': 'wlbName,wlbWell\n1/9-1,1/9-1\n' } };
const MIRRORED = { record_id: 'opm/norne', path: 'norne/NORNE_ATW2013.EGRID', body: 'EGRID fixture\n' };
let fixture;
before(async () => {
  const bodies = Object.fromEntries(Object.values(FIXTURE).flatMap(o => Object.entries(o)).map(([k, b]) => ['/' + k, b]));
  bodies['/mirror/' + MIRRORED.path] = MIRRORED.body;
  const srv = createServer((req, res) => bodies[req.url] ? res.writeHead(200).end(bodies[req.url]) : res.writeHead(404).end());
  await new Promise(ok => srv.listen(0, '127.0.0.1', ok));
  const at = `http://127.0.0.1:${srv.address().port}`;
  const digest = b => createHash('sha256').update(b).digest('hex');
  const assets = Object.fromEntries(Object.entries(FIXTURE).map(([cid, fs]) => [cid, Object.fromEntries(Object.entries(fs)
    .map(([k, b]) => [k, { href: `${at}/${k}`, title: k, roles: ['data'], 'file:size': Buffer.byteLength(b), 'file:checksum': '1220' + digest(b) }]))]));
  const copies = [{ record_id: MIRRORED.record_id, path: MIRRORED.path, sha256: digest(MIRRORED.body), bytes: Buffer.byteLength(MIRRORED.body),
    href: `${at}/mirror/${MIRRORED.path}` }];
  fixture = { assets, copies, close: () => srv.close() };
});
after(() => fixture.close());
const withAssets = async c => {
  await c.route('**/data/collections.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    for (const col of body.collections) if (fixture.assets[col.id]) col.assets = fixture.assets[col.id];
    return route.fulfill({ json: body });
  });
  await c.route('**/data/mirror.json', route => route.fulfill({ json: { copies: fixture.copies } }));
};
const byId = Object.fromEntries(committed.records.map(r => [r.id, r]));
const withRecords = recs => c => c.route('**/data/records.json', route => route.fulfill({ json: { ...committed, count: recs.length, records: recs } }));

// The E27 and E43 fixture builds (osd.build over the committed fixtures), in this file's own folder.
const py = (code, ...args) => run(process.env.UV || 'uv', ['run', '--quiet', 'python', '-c', code, ...args], { cwd: ROOT });
const whyBuilt = (async () => {
  const dir = join(OUT, 'e27');
  await py('import sys; from pathlib import Path; from osd.build import build; build(Path(sys.argv[1]), Path(sys.argv[2]), mirror_dir=Path(sys.argv[3]))',
    dir, join(ROOT, 'tests', 'fixtures', 'site', 'verification'), join(OUT, 'e27-no-mirror'));
  return JSON.parse(await readFile(join(dir, 'records.json'), 'utf8'));
})();
const withWhy = async c => { const body = await whyBuilt; await c.route('**/data/records.json', route => route.fulfill({ json: body })); };
const F3 = 'terranubis/f3-demo-2020', FX = join(ROOT, 'tests', 'fixtures', 'starters'), E43 = join(OUT, 'e43');
const starterBuilt = (async () => {
  await py('import sys, shutil; from pathlib import Path; from osd.build import build\n' +
    'out, fx, custody, mirror = map(Path, sys.argv[1:5])\n' +
    'shutil.rmtree(mirror, ignore_errors=True); shutil.copytree(custody, mirror / "custody")\n' +
    'build(out, fx / "verification", mirror_dir=mirror, records_dir=fx / "records", starters_dir=fx / "packs", source_commit="1" * 40, verification_commit="2" * 40)',
    E43, FX, join(ROOT, 'tests', 'fixtures', 'custody'), join(OUT, 'e43-mirror'));
  const fx = JSON.parse(await readFile(join(E43, 'records.json'), 'utf8'));
  return { records: Object.fromEntries(fx.records.map(r => [r.id, r])), starters: JSON.parse(await readFile(join(E43, 'starters.json'), 'utf8')) };
})();
const withStarters = (edit = r => r) => async c => {
  const fx = await starterBuilt;
  await c.route('**/data/records.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    body.records = body.records.map(r => fx.records[r.id] ? edit(fx.records[r.id], body) : r);
    return route.fulfill({ json: body });
  });
  await c.route('**/data/starters.json', route => route.fulfill({ json: fx.starters }));
  await c.route('**/data/starters/**', route => route.fulfill({ contentType: 'application/json',
    path: join(E43, 'starters', decodeURIComponent(new URL(route.request().url()).pathname.replace(/^\/data\/starters\//, ''))) }));
};

// The page's one checks of the owner's rules (R-S2, R-S6), on any view.
async function assertOwnerRules(page) {
  assert.equal(await page.locator('legend, .legend, #key, [class*="legend"], [id*="legend"]').count(), 0, 'no legend');
  const top = await page.locator('#top a').evaluateAll(as => as.map(a => a.getAttribute('href')));
  assert.deepEqual(top.filter(h => /how|status|starters/.test(h)), [], 'no link to how, status or starters in the top bar');
  assert.equal(await page.getByText(/Open in Ophiolite/i).count(), 0, 'no "Open in Ophiolite" (R-S6)');
  // E48 design 2 and acceptance 6: the area layers have one colour each, no data-driven colour, no legend.
  const paints = await page.evaluate(() => window.osdMap.getStyle().layers.filter(l => /^areas-/.test(l.id)).map(l => [l.id, l.paint || {}]));
  for (const [id, paint] of paints) for (const k of ['fill-color', 'line-color', 'text-color', 'text-halo-color'])
    if (k in paint) assert.equal(typeof paint[k], 'string', `${id} ${k} is one colour, not an expression`);
}
const noHorizontalScroll = page => page.evaluate(() => [document.documentElement, document.body, ...document.querySelectorAll('#side, #list, #detail, #bag')]
  .filter(e => e.getClientRects().length).every(e => e.scrollWidth <= e.clientWidth));

// ---- J1 ----------------------------------------------------------------------------------------
async function j1(viewport, shot) {
  const { context, page, errors, unexpected } = await open('', { viewport });
  assert.equal(await page.locator('#q').isVisible(), true, 'the search bar');
  assert.match(await page.locator('#count').innerText(), /^\d+ datasets? in this view$/);
  assert.ok(await page.locator('#list > ul > li').count() > 0, 'a list');
  assert.equal(await page.locator('#map canvas').isVisible(), true, 'the map');
  assert.equal(await page.locator('#bag-btn').isVisible(), true);
  await assertOwnerRules(page);
  if (shot) await page.screenshot({ path: join(OUT, shot) });
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
}
test('J1 opens the page and sees the search bar, a list and the map; no legend, no side pages needed', () => j1(DESKTOP, 'j1-desktop.png'));

// ---- J2 ----------------------------------------------------------------------------------------
async function j2(viewport, tag, more = '') {
  const { context, page, errors } = await open(NORTH_SEA + more, { viewport });
  const sea = await assertListFollows(page, committed.records, 'North Sea');
  assert.ok(sea.ids.includes('equinor/volve') && sea.ids.includes('sodir/factpages'), 'the North Sea holds Volve and the Sodir FactPages');
  await moveTo(page, [134, -25], 4);
  const au = await assertListFollows(page, committed.records, 'Australia');
  assert.ok(au.ids.length > 0 && !au.ids.includes('equinor/volve'), 'the list changed with the window');
  await moveTo(page, [0, 20], 0.5);
  const world = await assertListFollows(page, committed.records, 'world');
  if (viewport === DESKTOP) assert.equal(world.ids.length + world.noplace.length, committed.records.length, 'the world view lists every dataset once');
  assert.ok(world.noplace.length > 0, 'datasets with no place stated are listed at the world view only');
  if (tag) await page.screenshot({ path: join(OUT, `j2-world-${tag}.png`) });
  assert.deepEqual(errors, []);
  await context.close();
}
test('J2 pans or zooms and the list is exactly the datasets of the map window, each once, with its count', () => j2(DESKTOP, 'desktop'));

test('J2 the list does not come from the tiles: with every map source removed it still follows the window', async () => {
  // records.json and the build's index of areas (records without a bbox are placed by their countries' boxes)
  const only = c => c.route('**/data/files.txt', route => route.fulfill({ body: 'records.json\nareas.json\ncollections.json\nmirror.json\n' }));
  const { context, page, errors } = await open(NORTH_SEA, { routes: only });
  await page.evaluate(() => new Promise(ok => { window.osdMap.once('idle', ok);
    window.osdMap.setStyle({ version: 8, sources: {}, layers: [] }, { diff: false }); }));
  assert.deepEqual(await page.evaluate(() => Object.keys(window.osdMap.getStyle().sources)), [], 'no source on the map');
  await assertListFollows(page, committed.records, 'North Sea, no sources');
  await moveTo(page, [134, -25], 4);
  const au = await assertListFollows(page, committed.records, 'Australia, no sources');
  assert.ok(au.ids.length > 0);
  assert.deepEqual(errors, []);
  await context.close();
});

// ---- J3 ----------------------------------------------------------------------------------------
test('J3 types in the search bar and the list and the map narrow', async () => {
  const { context, page, errors } = await open(NORTH_SEA);
  const before = await page.locator('#count').innerText();
  await page.fill('#q', 'volve');
  assert.deepEqual(await page.locator('#list li').evaluateAll(ls => ls.map(l => l.dataset.id)), ['equinor/volve']);
  assert.equal(await page.locator('#count').innerText(), '1 dataset in this view');
  const filter = await page.evaluate(() => JSON.stringify(window.osdMap.getFilter('fields-fill')));
  assert.match(filter, /\["literal",\["equinor\/volve"\]\]/, 'the map narrows to the same ids');
  assert.match(await page.evaluate(() => location.hash), /q=volve/);
  await page.screenshot({ path: join(OUT, 'j3-volve.png') });
  await page.fill('#q', '');
  assert.equal(await page.locator('#count').innerText(), before, 'clearing restores the window\'s count');
  assert.deepEqual(errors, []);
  await context.close();
});

// ---- J4 ----------------------------------------------------------------------------------------
test('J4 opens Filters (one button), sets kind and level, closes it; the button shows how many are set', async () => {
  const body = await whyBuilt;
  const { context, page, errors } = await open(WORLD, { routes: withWhy });
  const all = (await listed(page)).ids.length + (await listed(page)).noplace.length;
  assert.equal(await page.locator('#filters').isHidden(), true, 'Filters are closed on arrival');
  await page.locator('#filters-btn').click();
  assert.equal(await page.locator('#filters').isVisible(), true);
  const kind = 'wellbore-headers';
  await page.locator('#kinds .chip', { hasText: new RegExp(`^${kind}$`) }).click();
  await page.selectOption('#minlevel', '1');
  await page.screenshot({ path: join(OUT, 'j4-filters-open.png') });
  await page.locator('#filters-btn').click();
  assert.equal(await page.locator('#filters').isHidden(), true, 'the same button closes them');
  assert.equal(await page.locator('#filters-btn .n').innerText(), '2');
  const got = await listed(page);
  const want = body.records.filter(r => r.kinds.includes(kind) && Number(r.level.slice(1)) >= 1).map(r => r.id).sort();
  assert.ok(want.length > 0 && want.length < all, 'the fixture has some, not all');
  assert.deepEqual([...got.ids, ...got.noplace].sort(), want, 'the list narrows');
  const hash = await page.evaluate(() => location.hash);
  assert.match(hash, /k=wellbore-headers/); assert.match(hash, /l=1/);
  for (const k of ['years', 'access', 'dated', 'starter']) assert.equal(await page.locator('#filters').getByText(new RegExp(k === 'years' ? 'Years' : k === 'access' ? 'How it is obtained' : k === 'dated' ? 'dated only' : 'with a starter project')).count(), 1, k);
  assert.deepEqual(errors, []);
  await context.close();
});

test('J4 a live-page hash (q=, t=, starter=1, a kind) opened on /shop.html gives the same ids as the live page gives', async () => {
  for (const [hash, routes] of [['k=seismic-3d&t=1990-2010', null], ['q=no&k=wellbore-headers&dated=1', null],
    ['starter=1', withStarters()], ['q=f3&k=seismic-3d&starter=1&t=1980-', withStarters()]]) {
    const live = await open(hash, { page: '', routes });
    const liveIds = await live.page.locator('#list li').evaluateAll(ls => ls.map(l => l.dataset.id));
    await live.context.close();
    const shop = await open(`${hash}&${WORLD}`, { routes });
    const got = await listed(shop.page);
    assert.deepEqual([...got.ids, ...got.noplace].sort(), [...liveIds].sort(), hash);
    assert.ok(liveIds.length > 0, `${hash}: some datasets`);
    const h = await shop.page.evaluate(() => location.hash.slice(1));
    for (const kv of hash.split('&')) assert.ok(h.split('&').includes(kv), `${hash}: ${kv} kept in the shop's address (${h})`);
    assert.deepEqual(shop.errors, []);
    await shop.context.close();
  }
});

// ---- J5 ----------------------------------------------------------------------------------------
const styleOf = page => page.evaluate(() => JSON.stringify(window.osdMap.getStyle().layers));
async function j5(viewport, more = '') {
  const { context, page, errors } = await open(NORTH_SEA + more, { viewport });
  const row = page.locator('#list > ul > li').first(), id = await row.getAttribute('data-id');
  const plus = row.locator('.plus');
  const box = await plus.boundingBox();
  if (viewport === PHONE) assert.ok(box.width >= 44 && box.height >= 44, `the plus is at least 44 px (${box.width}×${box.height})`);
  assert.equal(await plus.getAttribute('aria-pressed'), 'false');
  const before = await styleOf(page);
  await plus.click();
  assert.equal(await plus.getAttribute('aria-pressed'), 'true', 'the plus became a tick');
  assert.equal(await page.locator('#bag-btn .n').innerText(), '1');
  await page.waitForTimeout(300);
  assert.equal(await styleOf(page), before, 'the map\'s layers and paint are the same (no bag colour)');
  assert.match(await page.evaluate(() => location.hash), new RegExp(`pick=${id.replace('/', '\\/')}`));
  assert.equal(await page.locator('#detail').isHidden(), true, 'the plus does not open the row');
  await plus.focus(); await page.keyboard.press('Enter');
  assert.equal(await plus.getAttribute('aria-pressed'), 'false', 'keyboard reachable; a second press takes it out');
  assert.equal(await page.locator('#bag-btn .n').innerText(), '0');
  assert.deepEqual(errors, []);
  await context.close();
}
test('J5 presses the green plus on a row: it becomes a tick, the bag count goes up; nothing on the map changes colour', () => j5(DESKTOP));

// ---- J6 ----------------------------------------------------------------------------------------
test('J6 reads from the row\'s small icon how the dataset is obtained (download, sign-in, API, on request, purchase)', async () => {
  const base = byId['opm/norne'];
  const set = ['anonymous', 'registration', 'api', 'request', 'purchase'].map((a, i) => ({ ...base, id: `j6/${a}`, title: `J6 ${i} ${a}`,
    origin: { ...base.origin, access: a }, region: { country: 'NO', bbox: [3, 60, 4, 61] } }));
  const { context, page, errors } = await open(NORTH_SEA, { routes: withRecords(set) });
  const icons = await page.locator('#list li .acc').evaluateAll(as => as.map(a => ({ access: a.dataset.access, role: a.getAttribute('role'),
    alt: a.getAttribute('aria-label'), svg: a.innerHTML })));
  assert.deepEqual(icons.map(i => i.access), ['anonymous', 'registration', 'api', 'request', 'purchase']);
  assert.equal(new Set(icons.map(i => i.svg)).size, 5, 'five different icons');
  assert.ok(icons.every(i => i.role === 'img' && i.alt), 'each with a text alternative');
  assert.deepEqual(icons.map(i => i.alt.split(':')[0]), ['download', 'sign-in', 'API', 'on request', 'purchase']);
  await page.locator('#list').screenshot({ path: join(OUT, 'j6-access-icons.png') });
  assert.deepEqual(errors, []);
  await context.close();
});

// ---- J7 ----------------------------------------------------------------------------------------
test('J7 opens a row and reads when, why at this level, and the starter project', async () => {
  const reason = 'origin-reachable: answers a browser, not the verifier (HTTP 404 to osd-verifier, HTTP 200 to a browser agent)';
  const edit = (r, body) => { body.reasons = { ...(body.reasons || {}), [r.id]: reason };
    return { ...r, period: { start: '1987', end: '1990', stated: 'Acquired 1987, interpreted to 1990.' },
      blocked_since: '2026-10-21T08:00:00Z', checked_at: '2026-10-23T09:00:00Z', level: 'L0' }; };
  const { context, page, errors } = await open(NORTH_SEA, { routes: withStarters(edit) });
  await page.locator(`#list li[data-id="${F3}"] .title`).click();
  const d = page.locator('#detail');
  await d.locator('section.starter .app').first().waitFor();
  assert.equal(await page.locator('#list').isHidden(), true, 'the detail takes the list\'s place');
  assert.equal(await d.locator('section.when p').first().innerText(), '1987 to 1990');
  assert.equal(await d.locator('section.when .stated').innerText(), 'Acquired 1987, interpreted to 1990.');
  assert.equal(await d.locator('section.why .reason').innerText(), reason);
  assert.equal(await d.locator('section.why .checked').innerText(), 'checked 23 Oct 2026');
  assert.deepEqual(await d.locator('.pub .blocked, .pub .lvl').allInnerTexts(), ['blocked since 2026-10-21']);
  assert.deepEqual(await d.locator('section.starter .app').allInnerTexts(), ['OpendTect 7.0.10', 'ResInsight 2025.04', 'Python 3.12']);
  assert.match(await d.locator('section.starter .steps').innerText(), /osd get terranubis__f3-demo-2020__starter\.manifest\.json/);
  for (const h of ['Licence', 'How to get it', 'Open in QGIS', 'Read in Python']) assert.equal(await d.locator('h3', { hasText: new RegExp(`^${h}$`, 'i') }).count(), 1, h);
  assert.equal(await d.locator('a[href*="http"]', { hasText: 'The origin page' }).count(), 1, 'the origin link');
  assert.equal(await page.locator('.card, .cards').count(), 0, 'plain sections, no cards');
  assert.match(await page.evaluate(() => location.hash), /sel=terranubis\/f3-demo-2020/);
  await page.screenshot({ path: join(OUT, 'j7-row-opened.png') });
  await d.locator('.back').click();
  assert.equal(await page.locator('#list').isVisible(), true, 'the back arrow returns to the list');
  assert.doesNotMatch(await page.evaluate(() => location.hash), /sel=/);
  assert.deepEqual(errors, []);
  await context.close();
});

test('J7 a click on a feature opens its row', async () => {
  const { context, page, errors } = await open(NORTH_SEA);
  // a dot alone under the pointer, well inside the map; the pointer is in page coordinates
  const at = await page.evaluate(() => { const m = window.osdMap, c = m.getCanvas().getBoundingClientRect();
    for (const f of m.queryRenderedFeatures({ layers: ['boxes'] })) {
      const p = m.project(f.geometry.coordinates);
      if (p.x < 40 || p.y < 40 || p.x > c.width - 60 || p.y > c.height - 40) continue;
      if (m.queryRenderedFeatures([[p.x - 8, p.y - 8], [p.x + 8, p.y + 8]]).filter(g => g.source !== 'openmaptiles' && !/^area/.test(g.source)).length === 1)
        return { id: f.properties.record_id, x: c.left + p.x, y: c.top + p.y };
    } });
  assert.ok(at, 'a box-only dataset is a dot');
  await page.mouse.click(at.x, at.y);
  await page.locator('#detail h2.title').waitFor();
  assert.equal(await page.locator('#detail h2.title').innerText(), byId[at.id].title);
  assert.deepEqual(errors, []);
  await context.close();
});

// ---- J8–J10: outlines, names and the globe (E48), over the E46 fixture areas ---------------------
// The fixture build: osd.build over tests/fixtures/areas (three countries, three provinces and two
// basins hold a dataset; basin usgs-1003 holds none), served in place of site/data.
const AREAS_FX = join(ROOT, 'tests', 'fixtures', 'areas'), E48 = join(OUT, 'e48');
const areasBuilt = (async () => {
  await py('import sys; from pathlib import Path; from osd.build import build\n' +
    'out, fx, none = map(Path, sys.argv[1:4])\n' +
    'build(out, none, mirror_dir=none, records_dir=fx / "records", areas_dir=fx / "areas", outlines_dir=fx / "outlines", starters_dir=none, source_commit="1" * 40, verification_commit="2" * 40)',
    E48, AREAS_FX, join(OUT, 'e48-none'));
  const names = (await readdir(E48)).filter(f => f !== 'files.txt');
  await writeFile(join(E48, 'files.txt'), names.join('\n') + '\n');
  const read = async f => JSON.parse(await readFile(join(E48, f), 'utf8'));
  const index = await read('areas.json');
  const drawn = Object.fromEntries(await Promise.all(Object.keys(index.kinds).map(async k => [k, await read(`areas-${k}.geojson`)])));
  return { records: (await read('records.json')).records, index, drawn };
})();
const withAreas = c => c.route('**/data/**', async route => {
  await areasBuilt;
  const f = decodeURIComponent(new URL(route.request().url()).pathname.replace(/^\/data\//, ''));
  return route.fulfill({ path: join(E48, f) }).catch(() => route.fulfill({ status: 404, body: '' }));
});
const FX_VIEW = 'map=4.50/5.0000/10.0000';
const KINDS = { country: 'Countries', province: 'Provinces', basin: 'Basins' };
const idle = page => page.evaluate(() => new Promise(ok => window.osdMap.areTilesLoaded() && !window.osdMap.isMoving()
  ? requestAnimationFrame(() => window.osdMap.loaded() ? ok() : window.osdMap.once('idle', ok)) : window.osdMap.once('idle', ok)));
const rendered = (page, layer) => page.evaluate(l => window.osdMap.getLayer(l)
  ? window.osdMap.queryRenderedFeatures({ layers: [l] }).map(f => f.properties.area_id ?? f.properties.record_id) : [], layer);
const areaLayers = page => page.evaluate(() => window.osdMap.getStyle().layers.filter(l => /^areas-(fill|line)$/.test(l.id)).map(l => [l.id, l.source, l['source-layer'] || null]));
const pressed = page => page.locator('.osd-ctrl button[aria-pressed="true"]').allInnerTexts();
async function openFx(hash = FX_VIEW, viewport = DESKTOP) {
  const requested = [];
  const o = await open(hash, { viewport, routes: c => { c.on('request', r => requested.push(new URL(r.url()).pathname)); return withAreas(c); } });
  await idle(o.page);
  return { ...o, requested };
}
// A point inside the area that no dataset feature covers, in page coordinates.
const pointIn = (page, id) => page.evaluate(id => {
  const m = window.osdMap, c = m.getCanvas().getBoundingClientRect(), mine = m.queryRenderedFeatures({ layers: ['areas-fill'] }).filter(f => f.properties.area_id === id);
  const datasets = ['surveys-fill', 'fields-fill', 'wells', 'wells-cluster', 'boxes', 'wells-tiles'].filter(l => m.getLayer(l));
  for (let x = 20; x < c.width - 20; x += 6) for (let y = 20; y < c.height - 20; y += 6) {
    const here = m.queryRenderedFeatures([[x - 10, y - 10], [x + 10, y + 10]], { layers: ['areas-fill', ...datasets] });
    if (mine.length && here.length && here.every(f => f.layer.id === 'areas-fill') && m.queryRenderedFeatures([x, y], { layers: ['areas-fill'] })
      .some(f => f.properties.area_id === id)) return { x: c.left + x, y: c.top + y };
  }
}, id);
const byTitleIds = (recs, ids) => recs.filter(r => ids.includes(r.id)).sort((a, b) => collator.compare(a.title, b.title) || (a.id < b.id ? -1 : 1)).map(r => r.id);

test('J8 the files: every area in areas.json holds a dataset, the drawn files hold those and no other (nothing with n = 0 exists)', async () => {
  const { index, drawn } = await areasBuilt;
  const all = JSON.parse(await readFile(join(AREAS_FX, 'areas', 'basin.geojson'), 'utf8')).features.map(f => f.properties.area_id);
  assert.ok(all.includes('usgs-1003'), 'the fixture has a basin that holds nothing');
  for (const [k, { areas }] of Object.entries(index.kinds)) {
    for (const a of areas) assert.ok(a.n > 0 && a.n === a.ids.length, `${k} ${a.area_id}: n = ${a.n}`);
    assert.deepEqual(drawn[k].features.map(f => f.properties.area_id).sort(), areas.map(a => a.area_id).sort(), `${k}: the drawn file holds the index's areas`);
  }
  assert.ok(!index.kinds.basin.areas.some(a => a.area_id === 'usgs-1003'), 'the empty basin is not in the index');
});

test('J8 switches Countries / Provinces / Basins: one on, only its areas drawn, only its file requested, its credit shown', async () => {
  const { index } = await areasBuilt;
  for (const k of Object.keys(KINDS)) {
    const { context, page, errors, requested } = await openFx(`${FX_VIEW}&o=${k}`);
    assert.deepEqual(await pressed(page), [KINDS[k], 'Flat'], 'exactly one kind on (and Flat)');
    assert.deepEqual([...new Set(await rendered(page, 'areas-fill'))].sort(), index.kinds[k].areas.map(a => a.area_id).sort(), `${k}: the drawn ids are areas.json's`);
    assert.deepEqual(await areaLayers(page), [['areas-fill', `areas-${k}`, null], ['areas-line', `areas-${k}`, null]], `${k}: no other kind's layer in the style`);
    assert.deepEqual(requested.filter(p => /areas/.test(p)).sort(), ['/data/areas.json', `/data/areas-${k}.geojson`].sort(), `${k}: only the chosen kind's file was requested`);
    assert.match(await page.locator('.maplibregl-ctrl-attrib-inner').innerText(), new RegExp(index.kinds[k].sources[0].credit), 'the kind\'s credit in the attribution line');
    await assertOwnerRules(page);
    assert.deepEqual(errors, []);
    await context.close();
  }
  // switching fetches the other kind on demand and keeps what was fetched
  const { context, page, errors, requested } = await openFx();
  assert.equal(await page.locator('.osd-ctrl .seg[aria-label="Areas drawn"] button').count(), 3, 'no Licences part without that kind in areas.json');
  await page.getByRole('button', { name: 'Basins', exact: true }).click(); await idle(page);
  assert.deepEqual(await pressed(page), ['Basins', 'Flat']);
  assert.deepEqual(await areaLayers(page), [['areas-fill', 'areas-basin', null], ['areas-line', 'areas-basin', null]]);
  assert.match(await page.evaluate(() => location.hash), /o=basin/);
  await page.getByRole('button', { name: 'Countries', exact: true }).click(); await idle(page);
  assert.deepEqual([...new Set(await rendered(page, 'areas-fill'))].sort(), index.kinds.country.areas.map(a => a.area_id).sort());
  assert.deepEqual(requested.filter(p => /areas/.test(p)), ['/data/areas.json', '/data/areas-country.geojson', '/data/areas-basin.geojson'],
    'Basins fetched once on demand; Countries not again');
  assert.deepEqual(errors, []);
  await context.close();
});

async function j8click(more = '') {
  const { records, index } = await areasBuilt;
  const basin = index.kinds.basin.areas.find(a => a.area_id === 'usgs-1002');
  const { context, page, errors } = await openFx(`${FX_VIEW}&o=basin${more}`);
  const before = await listed(page);
  const at = await pointIn(page, basin.area_id);
  assert.ok(at, 'a point of the basin with no dataset feature on it');
  await page.mouse.click(at.x, at.y);
  await page.locator('#area-chip:not([hidden])').waitFor();
  await idle(page);
  const got = await listed(page);
  assert.deepEqual(got.ids, byTitleIds(records, basin.ids), 'the list is exactly the basin\'s ids');
  assert.equal(got.count, `${basin.ids.length} datasets in ${basin.name}`);
  assert.equal(await page.locator('#area-chip span').innerText(), basin.name, 'the chip names the area');
  assert.match(await page.evaluate(() => location.hash), /area=usgs-1002/);
  assert.equal(await page.evaluate(() => window.osdMap.getFeatureState({ source: 'areas-basin', id: 'usgs-1002' }).sel), true, 'outlined stronger by feature state');
  // out of the window and still listed: the area's ids are not met with the map window
  await moveTo(page, [100, -30], 5);
  assert.deepEqual((await listed(page)).ids, byTitleIds(records, basin.ids), 'the area\'s datasets are listed when out of view');
  await page.locator('#area-chip button').click();
  await idle(page);
  assert.equal(await page.locator('#area-chip').isHidden(), true);
  assert.doesNotMatch(await page.evaluate(() => location.hash), /area=/);
  await assertListFollows(page, records, 'after the cross', index);
  assert.equal(await page.evaluate(() => window.osdMap.getFeatureState({ source: 'areas-basin', id: 'usgs-1002' }).sel), undefined);
  assert.deepEqual(errors, []);
  await context.close();
  return before;
}
test('J8 a click on a basin lists exactly its datasets, names it in a chip and the hash; the cross restores the window\'s list', () => j8click());

test('J8 a second click on the area clears it; a click on a dataset inside an area opens the dataset', async () => {
  const { records, index } = await areasBuilt;
  const { context, page, errors } = await openFx(`${FX_VIEW}&o=basin`);
  const before = await listed(page);
  const at = await pointIn(page, 'usgs-1001');
  await page.mouse.click(at.x, at.y);
  await page.locator('#area-chip:not([hidden])').waitFor();
  await page.waitForTimeout(400); await idle(page);
  const again = await pointIn(page, 'usgs-1001');
  await page.mouse.click(again.x, again.y);
  await page.locator('#area-chip').waitFor({ state: 'hidden' });
  assert.doesNotMatch(await page.evaluate(() => location.hash), /area=/);
  // the boxed record's dot sits in basin usgs-1001
  await page.evaluate(() => window.osdMap.jumpTo({ center: [10, 5], zoom: 4.5 })); await idle(page);
  const dot = await page.evaluate(() => { const m = window.osdMap, c = m.getCanvas().getBoundingClientRect();
    const f = m.queryRenderedFeatures({ layers: ['boxes'] }).find(f => f.properties.record_id === 'fixture/boxed');
    const p = m.project(f.geometry.coordinates); return { x: c.left + p.x, y: c.top + p.y,
      under: m.queryRenderedFeatures([p.x, p.y], { layers: ['areas-fill'] }).map(g => g.properties.area_id) }; });
  assert.deepEqual(dot.under, ['usgs-1001'], 'the dot is inside the basin');
  await page.mouse.click(dot.x, dot.y);
  await page.locator('#detail h2.title').waitFor();
  assert.equal(await page.locator('#detail h2.title').innerText(), records.find(r => r.id === 'fixture/boxed').title, 'the dataset wins');
  assert.equal(await page.locator('#area-chip').isHidden(), true, 'the area is not set by that click');
  assert.ok(before.ids.length > 0);
  assert.deepEqual(errors, []);
  await context.close();
});

test('J9 turns Names on and off: one name per drawn area at its label point, and the dataset dots\' names with them', async () => {
  const { index } = await areasBuilt;
  for (const k of Object.keys(KINDS)) {
    const { context, page, errors } = await openFx(`${FX_VIEW}&o=${k}`);
    const ids = index.kinds[k].areas.map(a => a.area_id).sort();
    assert.deepEqual(await rendered(page, 'areas-name'), [], `${k}: names off by default`);
    assert.deepEqual(await rendered(page, 'boxes-name'), [], 'no dataset names either');
    await page.getByRole('button', { name: 'Names', exact: true }).click(); await idle(page);
    const names = await rendered(page, 'areas-name');
    assert.deepEqual(names.sort(), ids, `${k}: one name per drawn area (${names.length} for ${ids.length})`);
    assert.ok((await rendered(page, 'boxes-name')).length > 0, 'the dataset dots show their names');
    assert.match(await page.evaluate(() => location.hash), /n=1/);
    assert.equal(await page.evaluate(() => window.osdMap._fadeDuration), 0, 'fadeDuration 0');
    await page.getByRole('button', { name: 'Names', exact: true }).click(); await idle(page);
    assert.deepEqual(await rendered(page, 'areas-name'), [], 'off shows none');
    assert.deepEqual(await rendered(page, 'boxes-name'), []);
    assert.doesNotMatch(await page.evaluate(() => location.hash), /n=1/);
    assert.deepEqual(errors, []);
    await context.close();
  }
});

// ---- J11 ---------------------------------------------------------------------------------------
async function saveDownload(page, name) {
  const [dl] = await Promise.all([page.waitForEvent('download'), page.locator('#download').click()]);
  assert.equal(dl.suggestedFilename(), 'osd.manifest.json');
  const file = join(OUT, name);
  await dl.saveAs(file);
  const doc = JSON.parse(await readFile(file, 'utf8'));
  return { file, doc, same: { ...doc, created: '' } };
}
async function roundTrip(file, tag) {
  const assets = join(OUT, `assets-${tag}.json`), dest = join(OUT, `retrieved-${tag}`);
  await writeFile(assets, JSON.stringify(fixture.assets));
  await rm(dest, { recursive: true, force: true });
  const { stdout } = await run(process.env.UV || 'uv', ['run', '--quiet', 'python', join(ROOT, 'tests', 'site', 'manifest_roundtrip.py'), file, assets, dest], { cwd: ROOT });
  return JSON.parse(stdout.trim().split('\n').pop());
}
// The live page's select mode (E06) on the same ids: the object the bag must write.
async function liveManifest(pick, name) {
  const { context, page } = await open(`pick=${pick.join(',')}`, { page: '', routes: withAssets });
  const [dl] = await Promise.all([page.waitForEvent('download'), page.locator('#download').click()]);
  await dl.saveAs(join(OUT, name));
  await context.close();
  const doc = JSON.parse(await readFile(join(OUT, name), 'utf8'));
  return { ...doc, created: '' };
}

async function j11(viewport, tag) {
  const pick = ['opm/norne', F3];
  const { context, page, errors, unexpected } = await open(`${NORTH_SEA}&pick=${pick.join(',')}`, { viewport, routes: withAssets });
  assert.equal(await page.locator('#bag-btn .n').innerText(), '2');
  await page.locator('#bag-btn').click();
  const bag = page.locator('#bag');
  assert.deepEqual(await bag.locator('.items > li').evaluateAll(ls => ls.map(l => l.dataset.id)), pick);
  assert.match(await bag.locator(`li[data-id="opm/norne"] .lic`).innerText(), /share-alike: derived work must carry ODbL-1\.0/);
  assert.match(await bag.locator(`li[data-id="${F3}"] .acc-line`).innerText(), /Sign in at the publisher's page/);
  assert.equal(await bag.getByText(/Open in Ophiolite/i).count(), 0);
  assert.equal(await bag.getByRole('button', { name: /python/i }).count(), 1, 'the Python file (E49), beside the amber button');
  const amber = await bag.locator('#download').evaluate(b => getComputedStyle(b).backgroundColor);
  assert.equal(amber, 'rgb(224, 145, 47)', 'the one amber button');
  if (viewport === PHONE) {
    const b = await bag.locator('#download').boundingBox();
    assert.ok(b.y + b.height <= PHONE.height && b.x >= 0 && b.x + b.width <= PHONE.width, 'the download button is on the phone screen');
  }
  const { file, doc, same } = await saveDownload(page, `shop-${tag}.json`);
  assert.deepEqual(same, await liveManifest(pick, `live-${tag}.json`), 'the object the live page\'s basket writes');
  assert.deepEqual(doc.entries.map(e => e.record_id), pick);
  const entries = await roundTrip(file, `shop-${tag}`);   // equal to `osd manifest` for the same ids, and `osd get` reads it
  assert.deepEqual(entries.map(e => [e.record_id, e.unresolved && e.unresolved.split(':')[0]]), [['opm/norne', null], [F3, 'access registration']]);
  const files = bag.locator('#files');
  await files.waitFor();
  assert.equal(await files.locator('pre code').first().innerText(), 'osd get osd.manifest.json --dest data');
  const links = await files.locator('li[data-id="opm/norne"] .file').evaluateAll(ls => ls.map(l => ({ href: l.querySelector('a').href,
    text: l.innerText })));
  const copy = fixture.copies[0], asset = fixture.assets['opm--norne']['norne/NORNE_ATW2013.DATA'];
  assert.deepEqual(links.map(l => l.href), [copy.href, asset.href], 'the mirror copy and the publisher\'s file');
  assert.match(links[0].text, new RegExp(`${copy.bytes} B · from our mirror\\s+sha256 ${copy.sha256}`));
  assert.match(links[1].text, new RegExp(`${asset['file:size']} B · from the publisher\\s+sha256 ${asset['file:checksum'].slice(4)}`));
  assert.match(await files.locator(`li[data-id="${F3}"] .none`).innerText(), /^Sign in at the publisher's page to get the files/);
  assert.ok(await noHorizontalScroll(page), 'no horizontal scroll');
  await page.screenshot({ path: join(OUT, `j11-bag-${tag}.png`) });
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
}
test('J11 opens the bag and downloads: a manifest for osd get, and direct links for files the catalogue holds', () => j11(DESKTOP, 'desktop'));

test('J11 a sold dataset with terms: the bag writes the manifest/4 the live page writes, equal to osd manifest', async () => {
  const PASA = 'pasa/national-petroleum-exploration-database', pick = [PASA, 'opm/norne'];
  const { context, page, errors } = await open(`pick=${pick.join(',')}`, { routes: withAssets });
  await page.locator('#bag-btn').click();
  const { file, doc, same } = await saveDownload(page, 'shop-v4.json');
  assert.equal(doc.format, 'osd.manifest/4');
  assert.deepEqual(same, await liveManifest(pick, 'live-v4.json'));
  const entries = await roundTrip(file, 'shop-v4');
  assert.deepEqual(entries.map(e => e.record_id), pick);
  assert.match(await page.locator(`#files li[data-id="${PASA}"] .none`).innerText(), /^Buy the files at the publisher's page/);
  assert.deepEqual(errors, []);
  await context.close();
});

// ---- J12 ---------------------------------------------------------------------------------------
// The fixture catalogue of tests/fixtures/api/ joins the build: its records (on a committed record's
// shape, so the page lists them) and its STAC Collections; the date is fixed, so the file equals the
// golden file `osd script` writes and tests/test_api.py runs as written.
const API = join(ROOT, 'tests', 'fixtures', 'api'), FXIDS = ['fx/mirrored', 'fx/publisher', 'fx/signin'];
const withApiCatalogue = async c => {
  const fx = JSON.parse(await readFile(join(API, 'catalog', 'records.json'), 'utf8')).records;
  const cols = await Promise.all(FXIDS.map(async id => JSON.parse(await readFile(join(API, 'catalog', 'stac', id.replace('/', '--'), 'collection.json'), 'utf8'))));
  await c.route('**/data/records.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    body.records.push(...fx.map(r => ({ ...byId['opm/norne'], ...r })));
    return route.fulfill({ json: { ...body, count: body.records.length } });
  });
  await c.route('**/data/collections.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    body.collections.push(...cols);
    return route.fulfill({ json: body });
  });
  await c.clock.setFixedTime(new Date(2026, 10, 25, 12));
};
async function pythonDownload(page, name) {
  const [dl] = await Promise.all([page.waitForEvent('download'), page.locator('#python').click()]);
  assert.equal(dl.suggestedFilename(), 'osd_get.py');
  await dl.saveAs(join(OUT, name));
  return readFile(join(OUT, name), 'utf8');
}
test('J12 takes "Get a Python file": the file osd script writes, a sign-in dataset as its comment line', async () => {
  const { context, page, errors, unexpected } = await open(`pick=${FXIDS.join(',')}`, { routes: withApiCatalogue });
  await page.locator('#bag-btn').click();
  const text = await pythonDownload(page, 'j12-fixture.py');
  assert.equal(text, await readFile(join(API, 'golden.py'), 'utf8'), 'the golden file');
  assert.match(text, /^signin = osd\.get\("fx\/signin"\) +# sign-in needed: left out, sign in at https:\/\/origin\.fixture\.invalid\/signin\/$/m);
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});
test('J12 on the built catalogue: the page writes what osd script writes from site/data', async () => {
  const pick = ['opm/norne', F3, 'sodir/factpages'];
  const { context, page, errors } = await open(`pick=${pick.join(',')}`, { routes: async c => c.clock.setFixedTime(new Date(2026, 10, 25, 12)) });
  await page.locator('#bag-btn').click();
  const text = await pythonDownload(page, 'j12-built.py');
  const { stdout } = await run(process.env.UV || 'uv', ['run', '--quiet', 'python', '-m', 'osd.script', ...pick, '--catalog',
    join(ROOT, 'site', 'data'), '--today', '2026-11-25'], { cwd: ROOT });
  assert.equal(text, stdout);
  assert.deepEqual(errors, []);
  await context.close();
});
test.todo('J13 switches to Licences where a regulator is read: licences holding a dataset are drawn, the row names the block (E51)');

// ---- J14 ---------------------------------------------------------------------------------------
test('J14 shares the address: a second browser shows the same window, filters, opened row and bag', async () => {
  const a = await open();
  await a.page.locator('#filters-btn').click();
  await a.page.locator('#kinds .chip', { hasText: /^seismic-3d$/ }).click();
  await a.page.locator('#access .chip', { hasText: /^Download$/ }).click();
  await a.page.locator('#filters-btn').click();
  await moveTo(a.page, [3, 59], 5.5);
  await a.page.locator('#list > ul > li .plus').first().click();
  await a.page.locator('#list > ul > li .plus').nth(1).click();
  await a.page.locator('#list > ul > li .title').nth(2).click();
  await a.page.locator('#detail h2.title').waitFor();
  const seen = async p => ({ count: await p.locator('#count').innerText(), ids: await p.evaluate(() => window.osdShop.listIds()),
    title: await p.locator('#detail h2.title').innerText(), bag: await p.locator('#bag-btn .n').innerText(),
    filters: await p.locator('#filters-btn .n').innerText(),
    pressed: await p.locator('#kinds .chip[aria-pressed="true"], #access .chip[aria-pressed="true"]').allInnerTexts(),
    view: await p.evaluate(() => [window.osdMap.getZoom().toFixed(2), window.osdMap.getCenter().lat.toFixed(3), window.osdMap.getCenter().lng.toFixed(3)]) });
  const want = await seen(a.page), hash = await a.page.evaluate(() => location.hash);
  assert.match(hash, /k=seismic-3d/); assert.match(hash, /a=anonymous/); assert.match(hash, /sel=/); assert.match(hash, /pick=/); assert.match(hash, /map=/);
  const b = await open(hash.slice(1));
  await b.page.locator('#detail h2.title').waitFor();
  assert.deepEqual(await seen(b.page), want);
  console.log('# shared address', hash);
  assert.deepEqual([...a.errors, ...b.errors], []);
  await a.context.close(); await b.context.close();
});

// ---- J15 ---------------------------------------------------------------------------------------
test('J15 does J1, J2, J5 and J11 on a phone-width screen (390 × 844): no horizontal scroll, the plus at least 44 px', async () => {
  await j1(PHONE, 'j15-phone-list.png');
  await j2(PHONE, 'phone');
  await j5(PHONE);
  await j11(PHONE, 'phone');
  const { context, page } = await open(NORTH_SEA, { viewport: PHONE });
  assert.ok(await noHorizontalScroll(page), 'no horizontal scroll on the list');
  const sheet = await page.locator('#side').boundingBox(), map = await page.locator('#map').boundingBox();
  assert.ok(map.y < sheet.y, 'the map on top, the list a sheet below');
  assert.equal(await page.locator('#filters-btn-sheet').isVisible(), true, 'Filters in the sheet\'s head');
  assert.equal(await page.locator('#filters-btn').isVisible(), false);
  await page.locator('#grip').click();
  await page.waitForTimeout(300);
  assert.ok((await page.locator('#side').boundingBox()).y < sheet.y - 200, 'the sheet pulls up');
  await context.close();
});

// ---- Budget (E36's method) and the live page --------------------------------------------------
test('budget: the first load of /shop.html on the real catalogue stays under 1 MB from the site; fonts and libraries reported apart', { skip: noTiles }, async () => {
  for (const hash of ['', NORTH_SEA]) {
    const context = await browser.newContext({ viewport: DESKTOP });
    const unexpected = [];
    await shopOffline(context, unexpected);
    const page = await context.newPage();
    const errors = errorsOf(page);
    const log = [];
    page.on('requestfinished', async r => log.push({ url: r.url(), bytes: (await r.sizes()).responseBodySize }));
    await page.goto(server.url + 'shop.html' + (hash ? '#' + hash : ''));
    await shopReady(page);
    await page.waitForTimeout(300);
    const sum = rs => rs.reduce((s, r) => s + Math.max(0, r.bytes), 0);
    const site = log.filter(r => r.url.startsWith(server.url));
    const fonts = log.filter(r => /fonts\.(googleapis|gstatic)\.com/.test(r.url)), libs = log.filter(r => /unpkg\.com/.test(r.url));
    console.log(`# shop first load #${hash}: site ${sum(site)} bytes in ${site.length} requests; libraries ${sum(libs)} bytes (unpkg, uncompressed here);`,
      `fonts ${sum(fonts)} bytes (answered empty offline; Google Fonts online)`);
    assert.deepEqual(site.filter(r => /outlines\.geojson|collections\.json|mirror\.json/.test(r.url)), [], 'nothing the first view does not need');
    assert.ok(sum(site) < 1e6, `site bytes ${sum(site)}`);
    assert.deepEqual(errors, []);
    assert.deepEqual(unexpected, []);
    await context.close();
  }
});

test('R-S1: no live page links to the shop', async () => {
  for (const f of ['index.html', 'how.html', 'status.html', 'starters.html', 'app.js'])
    assert.doesNotMatch(await readFile(join(ROOT, 'site', f), 'utf8'), /shop\.html/, f);
});
