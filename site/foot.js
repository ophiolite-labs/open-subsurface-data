// E54 foot line
(async u => { try {
  const g = f => fetch(new URL('data/' + f, u)), D = document;
  if (!/^build\.json$/m.test(await (await g('files.txt')).text())) return;
  const b = await (await g('build.json')).json(), c = b.commit, [y, n, d] = b.date.split('-'),
    at = D.querySelector('.maplibregl-ctrl-attrib-inner'), s = D.createElement(at ? 'span' : 'p'), a = at?.parentNode;
  s.id = 'osd-foot'; s.title = b.time;
  s.innerHTML = `${at ? ' | ' : ''}Built ${+d} ${'JanFebMarAprMayJunJulAugSepOctNovDec'.substr(n * 3 - 3, 3)} ${y} from <a href="https://github.com/ophiolite-labs/open-subsurface-data/commit/${c}">${c}</a> · <a href="/changes.html">What changed</a>`;
  if (!a) return s.style.cssText = 'margin:24px 16px;font-size:12px', D.body.append(s);
  const p = () => at.contains(s) || at.append(s); p(); new MutationObserver(p).observe(at, {childList: 1});
  if (a.offsetWidth * 2 > innerWidth) a.classList.remove('maplibregl-compact-show');
} catch {} })(document.currentScript.src);
