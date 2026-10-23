// Screenshot the local site. Until E05 adds Playwright as a devDependency, point PLAYWRIGHT at an
// installed copy: PLAYWRIGHT=/path/to/node_modules/playwright node tools/shot.mjs out.png
const { chromium } = await import((process.env.PLAYWRIGHT || "playwright") + "/index.mjs");
const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1400, height: 900 } });
const errors = [];
p.on('pageerror', e => errors.push(String(e)));
p.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
await p.goto('http://localhost:8765/', { waitUntil: 'networkidle', timeout: 30000 });
await p.waitForTimeout(4000);
await p.click('#list li:nth-child(1)');
await p.waitForTimeout(2500);
await p.screenshot({ path: process.argv[2] });
console.log('list items', await p.locator('#list li').count(), 'detail hidden', await p.locator('#detail').isHidden(), 'errors', JSON.stringify(errors).slice(0, 400));
await b.close();
