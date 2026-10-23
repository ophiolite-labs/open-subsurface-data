// E32 design 5: phone-width screenshots of North Dakota's wells at a town zoom (Watford City) and of
// the dataset panel after one well is clicked. Serves site/ (run `make build` first), live basemap.
//   node docs/program/evidence/e32/shots.mjs docs/program/evidence/e32
import { join } from 'node:path';
process.env.OSD_SITE_ONLINE = '1';
const { serve, launch, offline, errorsOf, ready } = await import('../../../../tests/site/harness.mjs');

const out = process.argv[2] || 'build/shots';
const server = await serve(), browser = await launch();
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
await offline(context);
const page = await context.newPage();
const errors = errorsOf(page);
// The bottom sheet covers the lower half: centre south of town. The record is selected in the hash
// because headless Chromium at phone width leaves the basemap unpainted (body colour through the
// canvas) until a record is selected; every earlier phone shot (E15, E21, E27) selects one too.
await page.goto(server.url + '#sel=nd-dmr/wells&map=12/47.765/-103.28');
await ready(page);
await page.waitForFunction(() => {   // basemap and wells drawn, not just the style
  const m = window.osdMap;
  return m.loaded() && m.areTilesLoaded() && m.queryRenderedFeatures({ layers: ['wells-tiles'] }).length > 0;
}, null, { timeout: 60000, polling: 500 });
await page.waitForTimeout(3000);
await page.screenshot({ path: join(out, 'nd-wells-phone.png') });
const wells = await page.evaluate(() => {
  const m = window.osdMap, c = m.getCanvas(), w = c.clientWidth, h = c.clientHeight;
  const fs = m.queryRenderedFeatures({ layers: ['wells-tiles'] }).filter(f => f.properties.record_id === 'nd-dmr/wells');
  const near = fs.map(f => ({ id: f.properties.feature_id, name: f.properties.name, p: m.project(f.geometry.coordinates) }))
    .filter(x => x.p.y > 60 && x.p.y < h * 0.4 && x.p.x > 20 && x.p.x < w - 60)   // above the sheet, off the controls
    .sort((a, b) => Math.hypot(a.p.x - w / 2, a.p.y - h / 4) - Math.hypot(b.p.x - w / 2, b.p.y - h / 4));
  return { count: fs.length, first: near[0] && { id: near[0].id, name: near[0].name, x: near[0].p.x, y: near[0].p.y } };
});
console.log('North Dakota wells rendered:', wells.count, 'clicking', JSON.stringify(wells.first));
const box = await page.locator('#map canvas').boundingBox();
await page.mouse.click(box.x + wells.first.x, box.y + wells.first.y);
await page.waitForTimeout(2500);
await page.screenshot({ path: join(out, 'nd-dataset-panel-phone.png') });
console.log('detail', JSON.stringify(await page.locator('#detail h3 .title').innerText().catch(() => null)),
  'hash', await page.evaluate(() => location.hash), 'errors', JSON.stringify(errors).slice(0, 400));
await context.close(); await browser.close(); server.close();
