// E50 ruling 11 (26 Nov): the owner's Safari return visit took 14 of 19 tile ranges from the network.
// Why did the worker not answer them? Playwright's WebKit does not report the worker's own requests, so
// the site is served from this checkout (tests/site/harness.mjs: Pages' validators and byte ranges) and
// the server's log says what crossed the network. One browser, on the controller:
//
//   node docs/program/evidence/e50/return-visit.mjs [--browser webkit|chromium] [--wait-min 11]
//
// Visit 1: the note's address (z5 over 57/3), the window of the owner's Safari (850 x 929 at 2x).
// After --wait-min minutes, in the same profile: visit 2 at the address the owner's return visit had
// (z4, one level out: the hash the first visit's script left, ruling 13), visit 3 at the note's address.
import { chromium, webkit } from 'playwright';
import { serve } from '../../../../tests/site/harness.mjs';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i < 0 ? d : process.argv[i + 1]; };
const BROWSER = arg('browser', 'webkit'), WAIT = Number(arg('wait-min', '11'));
const log = [], server = await serve({ log });
const browser = await (BROWSER === 'webkit' ? webkit : chromium).launch();
try {
  const context = await browser.newContext({ viewport: { width: 850, height: 929 }, deviceScaleFactor: 2 });
  const page = await context.newPage();
  const visit = async (label, hash) => {
    const from = log.length;
    await page.goto('about:blank');
    await page.goto(server.url + 'shop.html?measure=1#' + hash);
    const r = await page.evaluate(() => window.osdMeasure.done, null, { timeout: 240000 });
    const controlled = await page.evaluate(() => !!navigator.serviceWorker.controller);
    await page.waitForTimeout(3000);
    const ours = log.slice(from).filter(e => /\/data\//.test(e.path));
    const by = {};
    for (const e of ours) { const k = `${e.method} ${e.path.split('/').pop()}${e.range ? ' range' : ''}`; by[k] = by[k] || { n: 0, bytes: 0 }; by[k].n++; by[k].bytes += e.bytes; }
    console.log(`${label} (${hash}): usable ${r.idleMs} ms, view z${r.view.zoom}, controlled ${controlled}; ` +
      `from the server: ${JSON.stringify(by)}; zoom back ${JSON.stringify(r.zoomOutBack.back.files)}`);
  };
  // What the worker holds, read from a page of the site that is not the shop (shop.css).
  const probe = async label => { await page.goto(server.url + 'shop.css');
    const s = await page.evaluate(async () => { const keys = await caches.keys(), reg = await navigator.serviceWorker.getRegistration();
      let entries = 0; for (const k of keys) entries += (await (await caches.open(k)).keys()).length;
      return { caches: keys.length, entries, names: keys.map(k => k.split('|').slice(1).join('|')), worker: reg ? (reg.active ? reg.active.state : 'no active') : 'none' }; });
    console.log(`${label}: ${s.caches} caches, ${s.entries} entries, worker ${s.worker}; ${s.names.join(', ')}`); };
  await visit('visit 1, first', 'map=5.00/57.0000/3.0000');
  await probe('after visit 1');
  await page.goto('about:blank');
  await new Promise(ok => setTimeout(ok, WAIT * 60e3));
  await probe(`after ${WAIT} min`);
  await visit(`visit 2, +${WAIT} min, the owner's drifted address`, 'map=4.00/57.0000/3.0000');
  await visit('visit 3, the note\'s address', 'map=5.00/57.0000/3.0000');
} finally { await browser.close(); server.close(); }
