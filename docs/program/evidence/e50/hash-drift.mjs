// E50 ruling 13 (26 Nov): does the page rewrite its address while the measuring script moves the map, so
// that a reload or a reopened tab measures another view? Opens the note's address, waits for the script,
// reads the address, reloads, and again, three times. One browser at a time, on the controller:
//
//   node docs/program/evidence/e50/hash-drift.mjs [--browser chromium|webkit] [--url URL] [--reloads 3]
//
// chromium: a phone, 393 x 690 at 3x; webkit: the owner's Safari window, 850 x 929 at 2x.
import { chromium, webkit } from 'playwright';

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i < 0 ? d : process.argv[i + 1]; };
const BROWSER = arg('browser', 'chromium'), RELOADS = Number(arg('reloads', '3'));
const URL_ = arg('url', 'https://opensubsurfacedata.org/shop.html?measure=1#map=5.00/57.0000/3.0000');
const browser = await (BROWSER === 'webkit' ? webkit : chromium).launch();
try {
  const context = await browser.newContext(BROWSER === 'webkit' ? { viewport: { width: 850, height: 929 }, deviceScaleFactor: 2 }
    : { viewport: { width: 393, height: 690 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  await page.goto(URL_);
  for (let i = 0; i <= RELOADS; i++) {
    if (i) await page.reload();
    const r = await page.evaluate(() => window.osdMeasure.done, null, { timeout: 240000 });
    await page.waitForTimeout(500);
    const after = await page.evaluate(() => location.hash);
    console.log(`${i ? `reload ${i}` : 'first'}: measured view z${r.view.zoom} (address z${r.view.addressZoom}) ${r.view.center.join('/')}; ` +
      `usable ${r.idleMs} ms; address after the script: ${after}`);
  }
} finally { await browser.close(); }
