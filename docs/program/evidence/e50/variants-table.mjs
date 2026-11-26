// The table of ruling 8 from variants.mjs's output: medians over the runs, per variant and visit.
//   node docs/program/evidence/e50/variants-table.mjs build/e50-variants-chromium.json
import { readFileSync } from 'node:fs';
const o = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const med = xs => { const s = xs.filter(x => x != null).sort((a, b) => a - b); return s.length ? s[s.length >> 1] : null; };
const kb = b => b == null ? '–' : `${Math.round(b / 1e3)} kB`;
console.log(`${o.browser} ${o.version}, ${o.options.viewport.width}x${o.options.viewport.height}@${o.options.deviceScaleFactor}, ${o.at}`);
console.log('| variant | visit | runs | usable ms (each) | list ms | site at idle, wire | site since load, wire | of it by the worker | base map at idle |');
console.log('|---|---|---|---|---|---|---|---|---|');
for (const v of [...new Set(o.runs.map(r => r.variant))]) for (const kind of ['first', 'return']) {
  const rs = o.runs.filter(r => r.variant === v && r.kind === kind && !r.error);
  if (!rs.length) continue;
  const n = k => med(rs.map(k));
  console.log(`| ${v} | ${kind} | ${rs.length} | **${n(r => r.idleMs)}** (${rs.map(r => r.idleMs).join(', ')}) | ${n(r => r.listMs)} | ` +
    `${n(r => r.network.siteAtIdle.requests)} req, ${kb(n(r => r.network.siteAtIdle.bytes))} | ${n(r => r.network.siteAll.requests)} req, ` +
    `${kb(n(r => r.network.siteAll.bytes))} | ${n(r => r.network.byWorker.requests)} req, ${kb(n(r => r.network.byWorker.bytes))} | ${n(r => r.network.otherAtIdle.requests)} req, ${kb(n(r => r.network.otherAtIdle.bytes))} |`);
}
