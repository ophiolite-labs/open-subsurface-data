// Shared by the site test and tools/shot.mjs: a static server over site/, Chromium with software
// GL, and routes that keep the run offline (MapLibre from node_modules, a blank basemap style).
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

export const ROOT = fileURLToPath(new URL('../../', import.meta.url));
const SITE = join(ROOT, 'site');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.geojson': 'application/geo+json', '.txt': 'text/plain', '.pmtiles': 'application/octet-stream', '.map': 'application/json' };

export async function serve() {
  const server = createServer(async (req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.endsWith('/')) p += 'index.html';
    const file = normalize(join(SITE, p));
    if (!file.startsWith(SITE)) { res.writeHead(403).end(); return; }
    try {
      const body = await readFile(file);
      const type = TYPES[extname(file)] || 'application/octet-stream';
      // Byte ranges, as GitHub Pages serves them: the PMTiles reader asks for nothing else (E15).
      const range = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range || '');
      if (range) {
        const start = Number(range[1]), end = Math.min(range[2] ? Number(range[2]) : body.length - 1, body.length - 1);
        res.writeHead(206, { 'content-type': type, 'content-range': `bytes ${start}-${end}/${body.length}`,
          'accept-ranges': 'bytes', 'content-length': end - start + 1 }).end(body.subarray(start, end + 1));
      } else res.writeHead(200, { 'content-type': type, 'accept-ranges': 'bytes' }).end(body);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise(ok => server.listen(0, '127.0.0.1', ok));
  return { url: `http://127.0.0.1:${server.address().port}/`, close: () => server.close() };
}

export const launch = () => chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox'] });

const BLANK_STYLE = { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#e8eaed' } }] };
const MAPLIBRE = join(ROOT, 'node_modules', 'maplibre-gl', 'dist');
const PMTILES = join(ROOT, 'node_modules', 'pmtiles', 'dist');

// Offline unless OSD_SITE_ONLINE=1. Any other request off the local server fails the run.
export async function offline(context, unexpected = []) {
  if (process.env.OSD_SITE_ONLINE === '1') return;
  await context.route(/^https?:\/\/(?!127\.0\.0\.1)/, async route => {
    const u = new URL(route.request().url());
    if (u.host === 'unpkg.com' && u.pathname.startsWith('/maplibre-gl@4.7.1/dist/')) {
      const f = u.pathname.split('/').pop();
      return route.fulfill({ body: await readFile(join(MAPLIBRE, f)), contentType: TYPES[extname(f)] });
    }
    if (u.host === 'unpkg.com' && u.pathname.startsWith('/pmtiles@4.5.0/dist/')) {
      const f = u.pathname.split('/').pop();
      return route.fulfill({ body: await readFile(join(PMTILES, f)), contentType: TYPES[extname(f)] });
    }
    if (u.host === 'tiles.openfreemap.org' && u.pathname.startsWith('/styles/')) return route.fulfill({ json: BLANK_STYLE });
    unexpected.push(u.href);
    return route.abort();
  });
}

// Console errors and page errors, collected per page.
export function errorsOf(page) {
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  return errors;
}

// Resolves when the map has loaded its style and the list is drawn.
export async function ready(page) {
  await page.waitForFunction(() => window.osdMap && window.osdMap.loaded() && document.getElementById('count').textContent, null, { timeout: 30000 });
  await page.evaluate(() => new Promise(ok => window.osdMap.areTilesLoaded() ? ok() : window.osdMap.once('idle', ok)));
}
