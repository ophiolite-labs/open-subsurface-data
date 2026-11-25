// Desktop and phone screenshots of the local site: node tools/shot.mjs <out-dir> [hash]
// The shop's six (E47): node tools/shot.mjs <out-dir> shop
// Serves site/ itself (run `make build` first). Uses the live basemap; OSD_SITE_OFFLINE=1 swaps
// in a blank one. Prints list count, detail title and console errors for each shot.
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
if (process.env.OSD_SITE_OFFLINE !== '1') process.env.OSD_SITE_ONLINE = '1';
const { serve, launch, offline, errorsOf, ready } = await import('../tests/site/harness.mjs');

const out = process.argv[2] || 'build/shots';
if (process.argv[3] === 'shop') {
  // Desktop first view (Europe), Filters open, a row opened, the bag with three datasets, phone list, phone bag.
  const { shopOffline, shopReady } = await import('../tests/site/shop-harness.mjs');
  await mkdir(out, { recursive: true });
  const server = await serve(), browser = await launch();
  const BAG = 'pick=nlog/nlog,opm/norne,equinor/volve';
  const shots = [
    ['desktop-first-view', { width: 1400, height: 900 }, '', null],
    ['desktop-filters-open', { width: 1400, height: 900 }, 'k=seismic-3d&l=0', p => p.locator('#filters-btn').click()],
    ['desktop-row-opened', { width: 1400, height: 900 }, 'sel=nlog/nlog&map=5.80/53.2000/5.0000', null],
    ['desktop-bag-three', { width: 1400, height: 900 }, `${BAG}&map=4.60/56.5000/4.0000`, p => p.locator('#bag-btn').click()],
    ['phone-list', { width: 390, height: 844 }, 'map=3.60/55.0000/6.0000', null],
    ['phone-bag', { width: 390, height: 844 }, `${BAG}&map=3.60/55.0000/6.0000`, async p => { await p.locator('#bag-btn').click(); await p.locator('#download').click(); }],
  ];
  for (const [name, viewport, h, act] of shots) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1, acceptDownloads: true });
    await shopOffline(context);
    const page = await context.newPage();
    const errors = errorsOf(page);
    await page.goto(server.url + 'shop.html' + (h ? '#' + h : ''));
    await shopReady(page);
    if (act) await act(page);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: join(out, name + '.png') });
    console.log(name, JSON.stringify(await page.locator('#count').innerText()), 'errors', JSON.stringify(errors).slice(0, 400));
    await context.close();
  }
  await browser.close(); server.close();
  process.exit(0);
}
const hash = process.argv[3] || 'sel=equinor/volve&map=4.3/57.5/3.5';
await mkdir(out, { recursive: true });
const server = await serve(), browser = await launch();
for (const [name, viewport] of [['desktop', { width: 1400, height: 900 }], ['phone', { width: 390, height: 844 }]]) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: name === 'phone' ? 2 : 1 });
  await offline(context);
  const page = await context.newPage();
  const errors = errorsOf(page);
  await page.goto(server.url + '#' + hash);
  await ready(page);
  await page.waitForTimeout(1500);
  await page.screenshot({ path: join(out, name + '.png') });
  console.log(name, 'list items', await page.locator('#list li').count(),
    'detail', JSON.stringify(await page.locator('#detail h3 .title').innerText().catch(() => null)),
    'errors', JSON.stringify(errors).slice(0, 400));
  await context.close();
}
await browser.close(); server.close();
