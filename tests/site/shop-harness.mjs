// The shop's half of the offline harness (E47): MapLibre 5 from node_modules (the aliased dev
// dependency `maplibre-gl-5`, so the live page keeps 4.7.1) and the web fonts answered empty, on top
// of harness.mjs's routes (later routes are tried first). Used by shop.test.mjs and tools/shot.mjs.
import { readFile } from 'node:fs/promises';
import { extname, join } from 'node:path';
import { ROOT, offline } from './harness.mjs';

export const MAPLIBRE_5 = '5.24.0';
const DIST = join(ROOT, 'node_modules', 'maplibre-gl-5', 'dist');
const TYPES = { '.js': 'text/javascript', '.css': 'text/css', '.map': 'application/json' };

export async function shopOffline(context, unexpected = []) {
  await offline(context, unexpected);
  if (process.env.OSD_SITE_ONLINE === '1') return;
  await context.route(u => u.host === 'unpkg.com' && u.pathname.startsWith(`/maplibre-gl@${MAPLIBRE_5}/dist/`), async route => {
    const f = new URL(route.request().url()).pathname.split('/').pop();
    return route.fulfill({ body: await readFile(join(DIST, f)), contentType: TYPES[extname(f)] });
  });
  await context.route(u => u.host === 'fonts.googleapis.com' || u.host === 'fonts.gstatic.com',
    route => route.fulfill({ body: '', contentType: 'text/css' }));
}

// Resolves when the map has loaded its style, the list is counted and the tiles in view are drawn.
export async function shopReady(page) {
  await page.waitForFunction(() => window.osdMap && window.osdMap.loaded() && document.getElementById('count').textContent, null, { timeout: 30000 });
  await page.evaluate(() => new Promise(ok => window.osdMap.areTilesLoaded() ? ok() : window.osdMap.once('idle', ok)));
}
