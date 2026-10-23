// Desktop and phone screenshots of the local site: node tools/shot.mjs <out-dir> [hash]
// Serves site/ itself (run `make build` first). Uses the live basemap; OSD_SITE_OFFLINE=1 swaps
// in a blank one. Prints list count, detail title and console errors for each shot.
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
if (process.env.OSD_SITE_OFFLINE !== '1') process.env.OSD_SITE_ONLINE = '1';
const { serve, launch, offline, errorsOf, ready } = await import('../tests/site/harness.mjs');

const out = process.argv[2] || 'build/shots';
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
