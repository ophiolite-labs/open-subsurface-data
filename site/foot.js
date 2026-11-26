// E54 foot line from data/build.json: map attribution, else page end
(async u => { try {
  const g = f => fetch(new URL('data/' + f, u)), D = document;
  if (!/^build\.json$/m.test(await (await g('files.txt')).text())) return;
  const b = await (await g('build.json')).json(), c = b.commit.replace(/\W/g, ''), [y, n, d] = b.date.split('-');
  const at = D.querySelector('.maplibregl-ctrl-attrib-inner'), to = at || D.body, s = D.createElement(at ? 'span' : 'p');
  s.id = 'osd-foot'; s.title = b.time;
  if (!at) s.style.cssText = 'margin:24px 16px;font-size:12px;color:var(--muted,#667)';
  s.innerHTML = `${at ? ' | ' : ''}Built ${+d} ${'JanFebMarAprMayJunJulAugSepOctNovDec'.substr(n * 3 - 3, 3)} ${y} from <a href="https://github.com/ophiolite-labs/open-subsurface-data/commit/${c}">${c}</a> · <a href="/changes.html">What changed</a>`;
  const p = () => to.contains(s) || to.append(s);
  p(); if (at) new MutationObserver(p).observe(at, { childList: true });
} catch {} })(document.currentScript.src);
