// E50 measurements 1-3 on a real laptop: headed Google Chrome on the Mac, in a temporary profile of its
// own (never the owner's), driven from the controller over SSH and the DevTools protocol. Run from the
// repository root on the controller:
//
//   node docs/program/evidence/e50/drive-chrome.mjs [--host macbook] [--url URL] [--profile DIR]
//        [--keep] [--inject site/measure.js] [--serve DIR] [--out FILE] [--label TEXT]
//        [--window W,H] [--warm URL,URL,...]
//
// It opens a Chrome window on the Mac (the Mac's own GPU), opens URL (default the published
// /shop.html?measure=1#map=5.00/57.0000/3.0000), waits for the measuring mode's numbers
// (window.osdMeasure.done), adds the browser's own GPU line, writes them as JSON and closes Chrome.
// --keep leaves the profile on the Mac for the return visit (measurement 2: run again with the same
// --profile after more than ten minutes and the next day); without it the profile is removed.
// --inject loads a measure.js before any page script, for a page that has no hook line yet (a
// method check, not one of the four measurements).
// --window W,H sizes the Chrome window (default 1400,900; the owner's own visit was 1857x1173 inner).
// --warm URL,... visits these pages first in the same profile, each to its load event, so the
// measured visit meets a disk cache and connection pool of other sites (a used profile, ruling 1 of
// 26 Nov); no extension is installed in the temporary profile.
// --max-age N sets the served Cache-Control (default 600, as GitHub Pages).
// --serve DIR serves a site directory from the controller (byte ranges as GitHub Pages serves them,
// no compression) and reaches the Mac through a reverse tunnel, at http://127.0.0.1:8766/: the same
// server for a before and an after, when a practice's stop rule asks for both numbers.
import { chromium } from 'playwright';
import { spawn, execFileSync } from 'node:child_process';
import { readFileSync, statSync, writeFileSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i < 0 ? d : process.argv[i + 1]; };
const flag = k => process.argv.includes('--' + k);
const HOST = arg('host', 'macbook');
const SERVE = arg('serve') && resolve(arg('serve')), SERVE_PORT = 8766, MAX_AGE = Number(arg('max-age', '600'));
const URL_ = arg('url', `${SERVE ? `http://127.0.0.1:${SERVE_PORT}` : 'https://opensubsurfacedata.org'}/shop.html?measure=1#map=5.00/57.0000/3.0000`);
const PROFILE = arg('profile', '/tmp/osd-e50-chrome');
const PORT = Number(arg('port', '9333'));
const OUT = arg('out', `build/e50-chrome-${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
if (!/^\/tmp\/osd-e50-[a-z0-9-]+$/.test(PROFILE)) throw new Error('the profile must be /tmp/osd-e50-<name>: never the owner\'s');

const ssh = cmd => execFileSync('ssh', ['-o', 'BatchMode=yes', HOST, cmd], { encoding: 'utf8' });
const quit = () => { try { ssh(`pkill -f -- '--user-data-dir=${PROFILE}' || true`); } catch { /* gone */ } };

quit();
ssh(`mkdir -p ${PROFILE} && open -na 'Google Chrome' --args --user-data-dir=${PROFILE} --remote-debugging-port=${PORT} ` +
  `--no-first-run --no-default-browser-check --window-size=${arg('window', '1400,900')} about:blank`);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.txt': 'text/plain' };
const server = SERVE && createServer(async (req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const file = normalize(join(SERVE, p));
  if (!file.startsWith(SERVE)) { res.writeHead(403).end(); return; }
  try {
    // As GitHub Pages: an ETag from the file's time and size, a 304 for a matching If-None-Match.
    const st = statSync(file), etag = `"${Math.floor(st.mtimeMs / 1000).toString(16)}-${st.size.toString(16)}"`;
    const cache = { 'cache-control': `max-age=${MAX_AGE}`, etag };
    if (flag('log')) console.error(`served ${p} range=${req.headers.range || '-'} if-none-match=${req.headers['if-none-match'] || '-'} if-range=${req.headers['if-range'] || '-'}`);
    if (req.headers['if-none-match'] === etag) { res.writeHead(304, cache).end(); return; }
    const body = await readFile(file), type = TYPES[extname(file)] || 'application/octet-stream';
    // If-Range with an ETag that is no longer the file's: the whole file, as GitHub Pages answers.
    const range = req.headers['if-range'] && req.headers['if-range'] !== etag ? null : /^bytes=(\d+)-(\d*)$/.exec(req.headers.range || '');
    if (range) {
      const start = Number(range[1]), end = Math.min(range[2] ? Number(range[2]) : body.length - 1, body.length - 1);
      res.writeHead(206, { 'content-type': type, 'content-range': `bytes ${start}-${end}/${body.length}`, 'accept-ranges': 'bytes',
        'content-length': end - start + 1, ...cache }).end(body.subarray(start, end + 1));
    } else res.writeHead(200, { 'content-type': type, 'accept-ranges': 'bytes', ...cache }).end(body);
  } catch { res.writeHead(404).end(); }
});
if (server) await new Promise(ok => server.listen(SERVE_PORT, '127.0.0.1', ok));
const tunnel = spawn('ssh', ['-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes', '-N', '-L', `${PORT}:127.0.0.1:${PORT}`,
  ...(server ? ['-R', `${SERVE_PORT}:127.0.0.1:${SERVE_PORT}`] : []), HOST], { stdio: 'ignore' });
let browser;
try {
  for (let i = 0; i < 40 && !browser; i++) {
    await new Promise(ok => setTimeout(ok, 500));
    browser = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`).catch(() => null);
  }
  if (!browser) throw new Error('Chrome on the Mac did not answer on the DevTools port');
  const context = browser.contexts()[0];
  // What fetch() returned to the page for our data files: what the PMTiles reader sees.
  await context.addInitScript(() => { const f = window.fetch; window.__fetches = [];
    window.fetch = async (u, o) => { const url = String(u && u.url || u), rec = /\/data\//.test(url) ?
      { url: url.split('/').pop(), range: o && o.headers && (o.headers.get ? o.headers.get('range') : o.headers.range) || null, cache: o && o.cache || null } : null;
      if (rec) window.__fetches.push(rec);
      try { const r = await f(u, o); if (rec) rec.status = r.status; return r; } catch (e) { if (rec) rec.error = String(e); throw e; } }; });
  if (arg('inject')) await context.addInitScript({ content: readFileSync(arg('inject'), 'utf8') });
  const page = await context.newPage();
  const consoleLines = [];
  page.on('console', m => { if (['error', 'warning'].includes(m.type())) consoleLines.push(`${m.type()}: ${m.text()}`.slice(0, 300)); });
  page.on('pageerror', e => consoleLines.push(`pageerror: ${String(e)}`.slice(0, 300)));
  // What the browser asked for and got for our data files (the return visit's question).
  const exchanges = [];
  const ours = r => /\/data\/[^?]*\.(pmtiles|json)/.test(r.url());
  page.on('requestfinished', async r => { if (!ours(r)) return; const h = await r.allHeaders(), res = await r.response();
    exchanges.push({ url: r.url().split('/').pop(), range: h.range || null, ifNoneMatch: h['if-none-match'] || null, ifRange: h['if-range'] || null,
      status: res && res.status(), fromCache: res ? await res.headerValue('x-from-cache').catch(() => null) : null }); });
  page.on('requestfailed', async r => { if (!ours(r)) return; const h = await r.allHeaders();
    exchanges.push({ url: r.url().split('/').pop(), range: h.range || null, failed: r.failure() && r.failure().errorText }); });
  for (const p of context.pages()) if (p !== page) await p.close();
  const warmed = [];
  for (const u of (arg('warm') || '').split(',').filter(Boolean)) {
    const w = await context.newPage(), t = Date.now();
    await w.goto(u, { waitUntil: 'load', timeout: 60000 }).then(() => warmed.push({ url: u, ms: Date.now() - t }), e => warmed.push({ url: u, error: String(e).slice(0, 120) }));
    await w.close();
  }
  await page.goto(URL_);
  const result = await page.evaluate(() => window.osdMeasure ? window.osdMeasure.done : null, null, { timeout: 120000 });
  if (!result) throw new Error('no measuring mode on the page (no hook line? use --inject)');
  const fetches = await page.evaluate(() => window.__fetches);
  const gpu = await page.evaluate(() => { const gl = document.createElement('canvas').getContext('webgl');
    const x = gl && gl.getExtension('WEBGL_debug_renderer_info'); return x ? gl.getParameter(x.UNMASKED_RENDERER_WEBGL) : null; });
  const out = { label: arg('label', ''), url: URL_, at: new Date().toISOString(), host: HOST, profile: PROFILE,
    browser: browser.version(), gpu, injected: !!arg('inject'), warmed, console: consoleLines, exchanges, fetches, ...result };
  writeFileSync(OUT, JSON.stringify(out, null, 2));
  const z = result.zoomOutBack, s = result.site, rj = s.files['records.json'];
  console.log(`${out.at} ${out.browser} ${gpu}: usable ${result.idleMs} ms, list ${result.listMs} ms; ${result.script.fps} fps ` +
    `(longest ${result.script.longestFrameMs} ms); zoom back ${z.back.requests} req ${z.back.bytes} B (out ${z.out.requests} req ` +
    `${z.out.bytes} B); at idle ${result.atIdle.requests} req ${result.atIdle.bytes} B; since load ${s.requests} req ${s.bytes} B; ` +
    `records.json ${rj ? JSON.stringify(rj.how) + ' ' + JSON.stringify(rj.status) : '-'} -> ${OUT}`);
  await page.screenshot({ path: OUT.replace(/\.json$/, '.png') });
} finally {
  if (browser) await browser.close().catch(() => {});
  tunnel.kill();
  if (server) server.close();
  quit();
  if (!flag('keep')) ssh(`rm -rf ${PROFILE}`);
}
