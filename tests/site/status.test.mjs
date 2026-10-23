// Playwright test for E08: status.html lists every record with its level and last check date.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { ROOT, serve, launch, offline, errorsOf } from './harness.mjs';

const OUT = join(ROOT, 'build', 'site-test');
let server, browser, catalogue;
before(async () => {
  await mkdir(OUT, { recursive: true });
  catalogue = JSON.parse(await readFile(join(ROOT, 'site', 'data', 'records.json'), 'utf8'));
  server = await serve(); browser = await launch();
});
after(async () => { await browser.close(); server.close(); });

// The built catalogue as a verify run would leave it: every record checked, levels from a ladder.
function checked() {
  const records = catalogue.records.map((r, i) => ({ ...r, level: ['L1', 'L2', 'L0'][i % 3],
    checked_at: `2026-10-${String(1 + (i % 22)).padStart(2, '0')}T08:00:00+00:00`, stale: i % 7 === 0,
    blocked_since: i === 2 ? '2026-10-20T08:00:00+00:00' : null }));
  return { ...catalogue, records };
}

async function open(data) {
  const context = await browser.newContext({ viewport: { width: 1200, height: 900 } });
  const unexpected = [];
  await offline(context, unexpected);
  if (data) await context.route(/\/data\/records\.json$/, route => route.fulfill({ json: data }));
  const page = await context.newPage();
  const errors = errorsOf(page);
  await page.goto(server.url + 'status.html');
  await page.waitForFunction(() => document.querySelectorAll('#status tbody tr').length > 0);
  return { context, page, errors, unexpected };
}

const rowsOf = page => page.$$eval('#status tbody tr', trs => trs.map(tr => ({
  id: tr.dataset.id, level: tr.querySelector('.lvl').textContent, date: tr.querySelector('td.checked time').textContent,
  badges: [...tr.querySelectorAll('td.checked span')].map(s => s.textContent) })));

test('status.html lists every record with its level and the date it was checked', async () => {
  const data = checked();
  const { context, page, errors, unexpected } = await open(data);
  const rows = await rowsOf(page);
  assert.deepEqual(rows.map(r => r.id).sort(), data.records.map(r => r.id).sort());
  for (const r of data.records) {
    const row = rows.find(x => x.id === r.id);
    assert.equal(row.level, r.level, r.id);
    assert.equal(row.date, r.checked_at.slice(0, 10), r.id);
  }
  assert.deepEqual(rows.find(r => r.id === data.records[2].id).badges.filter(b => b.startsWith('blocked')), ['blocked since 2026-10-20']);
  await page.screenshot({ path: join(OUT, 'status.png'), fullPage: true });
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  await context.close();
});

test('the built catalogue renders: a record never checked says so', async () => {
  const { context, page, errors } = await open();
  const rows = await rowsOf(page);
  assert.equal(rows.length, catalogue.count);
  for (const r of catalogue.records) {
    const row = rows.find(x => x.id === r.id);
    assert.equal(row.level, r.level);
    assert.equal(row.date, r.checked_at ? r.checked_at.slice(0, 10) : 'never');
  }
  assert.deepEqual(errors, []);
  await context.close();
});

test('a column header sorts, a second click reverses', async () => {
  const { context, page } = await open(checked());
  await page.click('th[data-key="checked_at"]');
  const up = (await rowsOf(page)).map(r => r.date);
  assert.deepEqual(up, [...up].sort());
  assert.equal(await page.getAttribute('th[data-key="checked_at"]', 'aria-sort'), 'ascending');
  await page.click('th[data-key="checked_at"]');
  const down = (await rowsOf(page)).map(r => r.date);
  assert.deepEqual(down, [...up].sort().reverse());
  await context.close();
});
