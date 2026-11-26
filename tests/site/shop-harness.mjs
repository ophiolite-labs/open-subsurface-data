// The shop's half of the offline harness (E47): MapLibre 5 from node_modules (the aliased dev
// dependency `maplibre-gl-5`, so the live page keeps 4.7.1) and the web fonts answered empty, on top
// of harness.mjs's routes (later routes are tried first). Used by shop.test.mjs and tools/shot.mjs.
import { readFile } from 'node:fs/promises';
import { extname, join } from 'node:path';
import { ROOT, offline } from './harness.mjs';

export const MAPLIBRE_5 = '5.24.0';
const DIST = join(ROOT, 'node_modules', 'maplibre-gl-5', 'dist');
// A blank base map with glyphs (E48): the names are symbol layers, and a style without glyphs has none.
// Each glyph is an empty box of a fixed advance, so labels are placed and counted without a font file.
const GLYPH_STYLE = { version: 8, glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf', sources: {},
  layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#e8eaed' } }] };
const varint = n => { const b = []; for (; n > 127; n = Math.floor(n / 128)) b.push(n % 128 | 128); b.push(n); return b; };
const field = (tag, wire, body) => [...varint(tag * 8 + wire), ...body];
const bytes = (tag, b) => field(tag, 2, [...varint(b.length), ...b]);
const zigzag = n => n < 0 ? -2 * n - 1 : 2 * n;
function glyphRange(fontstack, range) {   // glyphs.proto: stacks { name, range, glyphs { id, width, height, left, top, advance } }
  const [lo, hi] = range.split('-').map(Number), glyphs = [];
  for (let id = lo; id <= hi; id++) glyphs.push(...bytes(3, [...field(1, 0, varint(id)), ...field(3, 0, [6]), ...field(4, 0, [10]),
    ...field(5, 0, [0]), ...field(6, 0, varint(zigzag(-12))), ...field(7, 0, [7])]));
  return Buffer.from(bytes(1, [...bytes(1, [...Buffer.from(fontstack)]), ...bytes(2, [...Buffer.from(range)]), ...glyphs]));
}
const TYPES = { '.js': 'text/javascript', '.css': 'text/css', '.map': 'application/json' };

export async function shopOffline(context, unexpected = [], { serviceWorker = false } = {}) {
  await offline(context, unexpected);
  // The browser cache (site/sw.js, E50) stays out of the way of tests that route the page's own data
  // requests: an empty worker in its place. speed.test.mjs tests the real one (serviceWorker: true).
  if (!serviceWorker) await context.route(u => u.pathname.endsWith('/sw.js'), r => r.fulfill({ body: '// off in this test', contentType: 'text/javascript' }));
  if (process.env.OSD_SITE_ONLINE === '1') return;
  await context.route(u => u.host === 'unpkg.com' && u.pathname.startsWith(`/maplibre-gl@${MAPLIBRE_5}/dist/`), async route => {
    const f = new URL(route.request().url()).pathname.split('/').pop();
    return route.fulfill({ body: await readFile(join(DIST, f)), contentType: TYPES[extname(f)] });
  });
  await context.route(u => u.host === 'tiles.openfreemap.org', route => {
    const p = decodeURIComponent(new URL(route.request().url()).pathname), m = /^\/fonts\/(.+)\/(\d+-\d+)\.pbf$/.exec(p);
    return m ? route.fulfill({ body: glyphRange(m[1], m[2]), contentType: 'application/x-protobuf' })
      : route.fulfill({ json: GLYPH_STYLE });
  });
  await context.route(u => u.host === 'fonts.googleapis.com' || u.host === 'fonts.gstatic.com',
    route => route.fulfill({ body: '', contentType: 'text/css' }));
}

// Resolves when the map has loaded its style, the list is counted and the tiles in view are drawn.
export async function shopReady(page) {
  await page.waitForFunction(() => window.osdMap && window.osdMap.loaded() && document.getElementById('count').textContent, null, { timeout: 30000 });
  await page.evaluate(() => new Promise(ok => window.osdMap.areTilesLoaded() ? ok() : window.osdMap.once('idle', ok)));
}
