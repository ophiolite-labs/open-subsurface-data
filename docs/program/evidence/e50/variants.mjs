// E50 ruling 8 (26 Nov, second owner round): why the published shop got slower and heavier between the
// owner's two rounds. Each candidate is switched off in turn on the controller, never on the owner's
// machines, and the published page is measured with its own measuring mode (?measure=1):
//
//   node docs/program/evidence/e50/variants.mjs --browser chromium|webkit [--runs 3]
//        [--variants base,no-sw,no-areas,neither] [--url URL] [--out build/e50-variants-<browser>.json]
//
// Variants, each a clean profile, a first visit and then a return visit in the same profile:
//   base      the page as published
//   no-sw     no service worker: navigator.serviceWorker removed before any page script, so shop.js
//             takes its no-worker path (what sw-off.txt leaves a visitor with)
//   no-areas  the areas layer not added: files.txt is read without areas.pmtiles and areas.json, so
//             shop.js draws no area kind (areas.json is still fetched once, as the page asks for it
//             before it reads files.txt)
//   neither   both off: the page as it was at the owner's first round, less the cuts of #109
//   routed    the page as published, its HTML passed through Playwright's request routing (which
//             turns the browser's HTTP cache off): the yardstick for no-preload
//   no-preload  the HTML without its three `<link rel=preload as=fetch>` lines (files.txt,
//             records.json, areas.json), through the same routing
// Chromium: a phone, 393 x 690 at 3x, touch, the network held to 30 Mbit/s down, 15 up, 40 ms (DevTools
// protocol; a Wi-Fi phone); no CPU slowdown, as the controller draws WebGL in software (SwiftShader),
// slower than a phone's GPU already. WebKit: Playwright's WebKit at 850 x 929 at 2x, the owner's Safari
// window, the network as it is (WebKit has no throttling).
// Beside the page's own numbers, every request the browser makes (the worker's own included where the
// browser reports them) is logged with when it ended, so "at idle" can be read from the network too.
import { chromium, webkit } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i < 0 ? d : process.argv[i + 1]; };
const BROWSER = arg('browser', 'chromium'), RUNS = Number(arg('runs', '3'));
const VARIANTS = arg('variants', 'base,no-sw,no-areas,neither').split(',');
const URL_ = arg('url', 'https://opensubsurfacedata.org/shop.html?measure=1#map=5.00/57.0000/3.0000');
const OUT = arg('out', `build/e50-variants-${BROWSER}.json`);
const SITE = new URL(URL_).origin;

const noSw = () => { delete Navigator.prototype.serviceWorker; };
const noAreas = () => { const f = window.fetch;
  window.fetch = async (u, o) => { const r = await f(u, o);
    if (!/(^|\/)data\/files\.txt$/.test(String(u && u.url || u))) return r;
    const t = (await r.text()).split('\n').filter(l => l !== 'areas.pmtiles' && l !== 'areas.json').join('\n');
    return new Response(t, { status: r.status, headers: r.headers }); }; };

const browser = await (BROWSER === 'webkit' ? webkit : chromium).launch();
const options = BROWSER === 'webkit' ? { viewport: { width: 850, height: 929 }, deviceScaleFactor: 2 }
  : { viewport: { width: 393, height: 690 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true };

async function visit(context, label) {
  const page = await context.newPage();
  if (BROWSER === 'chromium') {
    const cdp = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 40, downloadThroughput: 30e6 / 8, uploadThroughput: 15e6 / 8 });
  }
  const net = [], t0 = Date.now();
  // bytes: what came over the wire (headers and body); a HEAD has no body (Playwright reports its
  // Content-Length as one), an answer from the worker came over no wire (the worker's own request did).
  const log = async r => { const res = await r.response().catch(() => null), s = await r.sizes().catch(() => null), tm = r.timing();
    const fromWorker = res ? res.fromServiceWorker() : null;
    net.push({ t: Date.now() - t0, start: tm && tm.startTime > 0 ? Math.round(tm.startTime - t0) : null, url: r.url().slice(0, 160), method: r.method(), range: (await r.allHeaders().catch(() => ({}))).range || null,
      status: res && res.status(), bytes: !s || fromWorker ? 0 : (r.method() === 'HEAD' ? 0 : Math.max(0, s.responseBodySize)) + s.responseHeadersSize,
      fromWorker, byWorker: !!(r.serviceWorker && r.serviceWorker()), failed: r.failure() && r.failure().errorText }); };
  context.on('requestfinished', log); context.on('requestfailed', log);
  await page.goto(URL_);
  const r = await page.evaluate(() => window.osdMeasure.done, null, { timeout: 240000 });
  const controlled = await page.evaluate(() => !!(navigator.serviceWorker && navigator.serviceWorker.controller));
  await page.waitForTimeout(3000); // the worker installs and the first load is read once more into its cache
  context.off('requestfinished', log); context.off('requestfailed', log);
  await page.screenshot({ path: OUT.replace(/\.json$/, `-${label}.png`) });
  await page.close();
  const site = e => e.url.startsWith(SITE) && !e.fromWorker, atIdle = net.filter(e => e.t <= r.idleMs + 50);
  const tally = es => ({ requests: es.length, bytes: es.reduce((a, e) => a + (e.bytes || 0), 0) });
  return { label, controlled, idleMs: r.idleMs, listMs: r.listMs, view: r.view, refreshHz: r.refreshHz, fps: r.script.fps,
    page: { atIdle: { requests: r.atIdle.requests, bytes: r.atIdle.bytes }, sinceLoad: { requests: r.site.requests, bytes: r.site.bytes },
      files: r.site.files, zoomOutBack: r.zoomOutBack },
    network: { siteAtIdle: tally(atIdle.filter(site)), otherAtIdle: tally(atIdle.filter(e => !site(e))),
      siteAll: tally(net.filter(site)), otherAll: tally(net.filter(e => !site(e))), byWorker: tally(net.filter(e => e.byWorker)) },
    firstLoad: r.firstLoad, requests: net };
}

const out = { at: new Date().toISOString(), browser: BROWSER, version: browser.version(), url: URL_, options, runs: [] };
mkdirSync(dirname(OUT), { recursive: true });
try {
  for (let run = 1; run <= RUNS; run++) for (const v of [...VARIANTS.slice((run - 1) % VARIANTS.length), ...VARIANTS.slice(0, (run - 1) % VARIANTS.length)]) {
    // each run starts with another variant, so none always meets the host's caches first
    const context = await browser.newContext(options);
    if (v === 'no-sw' || v === 'neither') await context.addInitScript(noSw);
    if (v === 'no-areas' || v === 'neither') await context.addInitScript(noAreas);
    if (v === 'routed' || v === 'no-preload') await context.route(u => u.pathname.endsWith('/shop.html'), async route => {
      const res = await route.fetch(), html = await res.text();
      await route.fulfill({ response: res, body: v === 'routed' ? html : html.split('\n').filter(l => !/rel="preload"[^>]*as="fetch"/.test(l)).join('\n') }); });
    for (const kind of ['first', 'return']) {
      const m = await visit(context, `${v}-${run}-${kind}`).catch(e => ({ label: `${v}-${run}-${kind}`, error: String(e).slice(0, 300) }));
      out.runs.push({ variant: v, run, kind, ...m });
      console.log(m.error ? `${m.label}: ${m.error}` : `${m.label}: usable ${m.idleMs} list ${m.listMs} controlled ${m.controlled}; page at idle ` +
        `${m.page.atIdle.requests} req ${Math.round(m.page.atIdle.bytes / 1e3)} kB, since load ${m.page.sinceLoad.requests} req ` +
        `${Math.round(m.page.sinceLoad.bytes / 1e3)} kB; network site at idle ${m.network.siteAtIdle.requests} req ` +
        `${Math.round(m.network.siteAtIdle.bytes / 1e3)} kB, all ${m.network.siteAll.requests} req; by worker ${m.network.byWorker.requests}; ` +
        `zoom back ${m.page.zoomOutBack.back.requests} req ${m.page.zoomOutBack.back.bytes} B`);
      writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
    await context.close();
  }
} finally { await browser.close(); }
