# E50: speed, measured — method and numbers

Charter: `docs/program/charters/E50-speed-measured.md` (family rule R-S7). The target the owner
approved:

| What | Target |
|---|---|
| Map usable after opening the page | within 2 seconds |
| Movement while dragging and zooming | 60 pictures a second |
| An area visited before, same visit | no download |
| An area visited before, another day | no download of our files |

## The method: the measuring mode

Open `/shop.html?measure=1`. `shop.js` then loads `site/measure.js` (and only then: the normal page
asks for no `measure.js`, a test checks it). After the map's first `idle` the mode waits half a
second and runs one fixed script, the same on every device; a dark box at the bottom left shows
four numbered lines:

| Line | What it is | How it is read |
|---|---|---|
| 1 usable | ms from navigation start to the map's first `idle`; then to the list's first count | `performance.now()` at the `idle` event and when `#count` first has text |
| 2 drag+zoom | pictures a second and the longest frame over the scripted moves | `requestAnimationFrame` timestamps; the moves: pan 40 % of the map's width, back by 30 % of its height, up again (800 ms each, linear), one level in and out (800 ms each) |
| 3 zoom back | requests and bytes from the site while coming back from three levels out | jump three levels out, wait for `idle`; jump back, wait for `idle`; the resource entries after each jump. "Back" is the area visited before: target 0. "Out" is shown beside it |
| 4 site since load | requests and bytes from the site since load, and at the first `idle` | Performance API: the navigation entry and every resource entry on our origin; `transferSize` (headers and body over the wire, 0 when the browser served it from its cache) |

Under line 4: what the browser did for `records.json` and for each `.pmtiles` archive (`network`,
`revalidated` = headers only, a `304`; `cache` = nothing over the wire; `no body` = nothing over
the wire and nothing kept, a request MapLibre cancelled while moving), the style's layer count and
the screen size. Everything is also in `window.osdMeasure.result` (`window.osdMeasure.done` is a
promise of it), so a script that drives a browser reads the same numbers as a person.

What the numbers are not: `transferSize` is 0 for other origins (the base map, unpkg) unless they
send `Timing-Allow-Origin`, so line 4 counts our files only, as the target does. Safari before 16.4
gives no `transferSize`; the readout then says `unknown`.

### Running it

- A person: open the address, wait until "running…" goes away (about 6 s), read the four bold
  numbers. "Run again" repeats the script on the same page (the area is then visited before).
- A return visit (measurement 2): the same browser profile, more than ten minutes later and again
  the next day; open the same address and read line 4 and the lines under it.
- The controller: `node --test --test-name-pattern="shows the four numbers" tests/site/speed.test.mjs`
  writes `build/site-test/e50/controller.json` and `readout.png`; with `OSD_SITE_ONLINE=1` the real
  base map and MapLibre come from the network, our files still from the local server.

## The practices: where each is checked

| # | Practice | Check | State at PR A |
|---|---|---|---|
| 1 | tiles under 500 KB, thinned where dense; zoomed out, counted circles | `tests/test_tiles.py` (built archives, `make check-full`); `speed.test.mjs` practice 1 | circles: yes (124 at z5 over the North Sea). Tiles: **no**, 2 tiles of `outlines.pmtiles` at z7 are over 500 KB (largest 1061 KB) because `write_tiles` passes `--no-tile-size-limit`; the flags change after E46 slice 1 (xfail until then) |
| 2 | the list from the page's records, never from tile queries | `speed.test.mjs` practice 2 (spies on both query calls while the window moves) | yes |
| 3 | `minzoom`/`maxzoom`; few layers | `speed.test.mjs` practice 3 (prints) and a todo | partly: `wells-tiles` z7-24; the counted circles have no `maxzoom` 7 yet |
| 4 | `maxTileCacheZoomLevels` set, 5 or more | todo | default (5), not set |
| 5 | `refreshExpiredTiles: false` | todo | not set (true) |
| 6 | one file, index at the front; protocol once | `tests/test_tiles.py` (gate on a fixture; the real archives in `make check-full`); `speed.test.mjs` practice 6 | yes: clustered, one leaf level, root directory ends at byte 360; `addProtocol` once |
| 7 | hover by feature state | `speed.test.mjs` practice 7 | yes: 0 `setFilter`/`setPaintProperty`/`setLayoutProperty` over six hovered rows |
| 8 | `fadeDuration` 0 with names on | todo | default (300 ms) |

The built archive (this host's tippecanoe 2.49.0; CI pins 2.79.0), read by
`uv run python tests/test_tiles.py`:

```
outlines.pmtiles: 211750 tiles z0-12, clustered=True, leaf levels 1, root directory ends at byte 360,
2 tiles >= 500 KB; largest per zoom: z0 155 KB, z1 100 KB, z2 117 KB, z3 94 KB, z4 106 KB, z5 119 KB,
z6 105 KB, z7 1061 KB, z8 418 KB, z9 364 KB, z10 248 KB, z11 98 KB, z12 68 KB
```

The style's layers, live base map (`OSD_SITE_ONLINE=1`): 123 layers, 111 of the base map
(OpenFreeMap Liberty) and 12 of the shop:

```
fields-fill    fill    z0-24      surveys-fill   fill    z0-24      wells-cluster  circle  z0-24
fields-line    line    z0-24      surveys-line   line    z0-24      wells-count    symbol  z0-24
fields-dash    line    z0-24      surveys-dash   line    z0-24      wells          circle  z0-24
wells-tiles    circle  z7-24      boxes          circle  z0-24      boxes-name     symbol  z0-24
```

## Numbers

### The controller (headless; not a real machine)

25 Nov 2026, the lane's VPS (16 vCPU AMD EPYC-Rome, no GPU): Playwright's headless Chromium
156.0.8078.4 with SwiftShader (software WebGL), 1400×900 at 1×, North Sea at z5
(`#map=5.00/57.0000/3.0000`), our files from the test's local server (byte ranges as GitHub Pages
serves them, no compression), three runs offline, four with the live base map. Software rendering on a server: frame rates here say
nothing about a laptop's or a phone's; they show the method works and give the request and byte
counts, which do not depend on the machine.

| | usable (first idle) | list | drag+zoom | longest frame | zoom back | zoom out | site at first idle | site after the script |
|---|---|---|---|---|---|---|---|---|
| offline (blank base map) | 1128–1250 ms | 499–535 ms | 36.6–37.1 fps | 50 ms | **0 req, 0 B** | 6 req, 206 kB | 15 req, 799 kB | 29 req, 1.04 MB |
| live base map | 3306–3472 ms | 1729–1903 ms | 9.3–9.7 fps | 150–167 ms | **0 req, 0 B** | 6 req, 206 kB | 15 req, 799 kB | 29 req, 1.07 MB |

Our files at the first idle (live base map run): `records.json` 608 kB (uncompressed here; GitHub
Pages sends it gzipped), `outlines.pmtiles` 9 ranges 111 kB, `shop.js` 46 kB, `wells-z5.json`
17 kB, `shop.css` 12 kB, `shop.html` 3 kB, `files.txt` 0.5 kB.

### The real machines (measurements 1–4)

Owed; measured against `https://opensubsurfacedata.org/shop.html?measure=1` once the measuring mode
is merged and published (the laptop: the owner's MacBook, headed Chrome and Safari with a temporary
profile; the phone: a person reads the four numbers back).
