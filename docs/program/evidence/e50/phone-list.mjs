// E50 ruling 10 (26 Nov): on a phone, after the measuring mode's script ends, are the datasets the list
// names those whose places lie in what the map shows? Run on the controller, one browser at a time:
//
//   node docs/program/evidence/e50/phone-list.mjs [--browser chromium|webkit] [--url URL] [--out build/e50-phone-list-<browser>]
//
// A phone of 393 x 690 at 3x (Chromium), or Playwright's iPhone 15 (WebKit). It opens the address of the
// owner's note, waits for the script, then reads the map's view and bounds, the part of the map the list
// sheet covers, the list's count and first rows, and for each listed dataset where its box lies against
// the map's bounds and against the part of the map left visible above the sheet. Writes <out>.json and
// <out>.png (the whole screen).
import { chromium, webkit, devices } from 'playwright';
import { writeFileSync } from 'node:fs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i < 0 ? d : process.argv[i + 1]; };
const BROWSER = arg('browser', 'chromium');
const URL_ = arg('url', 'https://opensubsurfacedata.org/shop.html?measure=1#map=5.00/57.0000/3.0000');
const OUT = arg('out', `build/e50-phone-list-${BROWSER}`);
const browser = await (BROWSER === 'webkit' ? webkit : chromium).launch();
try {
  const context = await browser.newContext(BROWSER === 'webkit' ? devices['iPhone 15'] :
    { viewport: { width: 393, height: 690 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  await page.goto(URL_);
  const r = await page.evaluate(() => window.osdMeasure.done, null, { timeout: 240000 });
  await page.waitForTimeout(1500);
  const look = await page.evaluate(async () => {
    const m = window.osdMap, b = m.getBounds(), rect = el => { const q = el && el.getBoundingClientRect(); return q ? [q.left, q.top, q.right, q.bottom].map(Math.round) : null; };
    const mapRect = rect(document.getElementById('map')), sheet = rect(document.getElementById('side'));
    // The part of the map left above the sheet, as longitude and latitude.
    const visBottom = sheet && sheet[1] > mapRect[1] && sheet[1] < mapRect[3] ? sheet[1] - mapRect[1] : mapRect[3] - mapRect[1];
    const sw = m.unproject([0, visBottom]), ne = m.unproject([mapRect[2] - mapRect[0], 0]);
    const built = await fetch('data/records.json').then(x => x.json());
    const byId = Object.fromEntries(built.records.map(x => [x.id, x]));
    const ids = [...document.querySelectorAll('#list > ul > li')].map(li => li.dataset.id);
    const titles = [...document.querySelectorAll('#list > ul > li')].slice(0, 20).map(li => li.textContent.trim().slice(0, 70));
    const within = (bb, [w, s, e, n]) => !bb ? null : !(bb[1] > n || bb[3] < s || bb[0] > e || bb[2] < w);
    const box = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()], vis = [sw.lng, sw.lat, ne.lng, ne.lat];
    const rows = ids.slice(0, 20).map(id => { const x = byId[id], bb = x && x.region && x.region.bbox;
      return { id, bbox: bb || null, inBounds: within(bb, box), aboveSheet: within(bb, vis) }; });
    return { hash: location.hash, zoom: +m.getZoom().toFixed(2), center: m.getCenter().toArray().map(v => +v.toFixed(3)),
      bounds: box.map(v => +v.toFixed(3)), visibleAboveSheet: vis.map(v => +v.toFixed(3)), mapRect, sheet,
      count: (document.getElementById('count') || {}).textContent, listed: ids.length, titles, rows,
      allInBounds: rows.every(x => x.inBounds !== false), allAboveSheet: rows.every(x => x.aboveSheet !== false),
      controls: [...document.querySelectorAll('.maplibregl-ctrl-bottom-right > *, .maplibregl-ctrl-bottom-left > *')].map(el => ({ cls: el.className.slice(0, 60), rect: rect(el) })) };
  });
  const out = { at: new Date().toISOString(), browser: BROWSER, url: URL_, view: r.view, script: r.script, ...look };
  writeFileSync(OUT + '.json', JSON.stringify(out, null, 1));
  await page.screenshot({ path: OUT + '.png' });
  console.log(JSON.stringify({ view: r.view, hash: look.hash, zoom: look.zoom, center: look.center, count: look.count, allInBounds: look.allInBounds, allAboveSheet: look.allAboveSheet, first: look.titles.slice(0, 3) }));
} finally { await browser.close(); }
