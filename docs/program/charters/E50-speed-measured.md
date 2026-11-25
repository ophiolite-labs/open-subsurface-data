## E50 Speed, measured: the Shop 06 practices in place and the four owed measurements with numbers — CHARTERED 25 Nov 2026 (Surface with build; no strategy, no Codex round) — QUEUED after E47; second pass after E48

Authority: family `MAP-AS-A-SHOP-family.md` (R-S7); OSD-D31; board Shop 06 (`b6.py`);
`speed-practices.md` beside the prototype (sources and quotes for every practice). E15, E36.

**The target the owner approved.**

| What | Target |
|---|---|
| Map usable after opening the page | within 2 seconds |
| Movement while dragging and zooming | 60 pictures a second |
| An area visited before, same visit | no download |
| An area visited before, another day | no download of our files |

**Order of work the owner approved:** keep the present host; measure a return visit in a real
browser first; only if that shows downloads, add a cache in the browser.

**Outcome.** The shop holds the eight practices of Shop 06, each with a test or a stated check,
and the PR carries four measurements made on real machines, as numbers against the target, with
the method so that anyone can repeat them.

**The practices (each is an acceptance line).**

1. Everything drawn comes as tiles, thinned where dense: every tile of `outlines.pmtiles` and
   `areas.pmtiles` is under 500 KB (checked over the real build; the tippecanoe flags used are
   stated). Zoomed out, wells are counted circles (E36, kept).
2. The list is filtered from the page's records by the map window (E47; a test here asserts no
   `queryRenderedFeatures` or `querySourceFeatures` call feeds the list).
3. Layers have `minzoom` and `maxzoom` where they cannot be read outside them, and are few: the
   style's layer count and each layer's zoom range are printed in the PR.
4. Tiles of five zoom levels stay in memory (`maxTileCacheZoomLevels` at the default or higher,
   set explicitly).
5. `refreshExpiredTiles: false`.
6. One file with its index at the front: the PMTiles header of each archive shows clustered = true
   and one leaf level (read by a test from the built file); the protocol is registered once.
7. Hover and selection use feature state (no `setFilter` or `setPaintProperty` on hover; test).
8. Names without the slow fade (`fadeDuration` 0 with names on).

**The measurements (acceptance; numbers in the PR and in `docs/program/evidence/e50/measurements.md`).**

A measuring mode ships with the page: `/shop.html?measure=1` shows a small readout (time from
navigation start to the map's first `idle` and to the list's first rows; frames per second over a
scripted drag and zoom; bytes and request count from the site since load, read from the
Performance API; the same after the scripted zoom out and back). It adds no weight to the normal
page (loaded only with the parameter). The script is the same on every device.

1. *A real laptop and a real phone.* The owner's MacBook over the tailnet (devices skill; Chrome
   driven by Playwright over SSH is acceptable as "real machine" only with the real GPU, headed)
   and a real phone. The phone needs a person: the lane writes an owner-actions item "open this
   address on the phone and read back four numbers" only at that moment, and does not wait for it
   to merge the rest. Usable-in-seconds and pictures-a-second, each against the target.
2. *A return visit in a browser.* Same profile, more than ten minutes later and again the next
   day: bytes of our files transferred (expected: `304`, 0 bytes of body for `records.json`; for
   the PMTiles range requests, what the browser really does: this is the unknown). Chrome and
   Safari both.
3. *Zooming out and back in.* Requests and bytes during the scripted zoom out three levels and
   back: target 0.
4. *The globe with all 166,412 wells.* Pictures a second on the laptop and the phone at the first
   view and at zoom 6 over North Dakota (second pass, after E48).

**Then, by the numbers.** If (2) shows our files downloaded again, the lane proposes the browser
cache (a service worker: cache-first for a versioned tile file name, stale-while-revalidate for
records; the 206 handling is an experiment) as a slice with its own acceptance, and records the
measured reason in DECISIONS before building it (ENGINEERING "What is deliberately absent").
If (1) misses 2 s, the PR names the largest three costs with their milliseconds. If (4) misses a
usable rate on the phone, the globe gets the lighter mode (fewer layers) or stays behind its switch
off by default on small screens; the lane states which and why.

**Out of scope.** Leaving GitHub Pages; a server; changing the tile builder; deck.gl.

**Stop rules.** No practice is switched on that the measurement shows slower than before: state
the two numbers and leave it off.

**Ownership and dependencies.** Coding lane (surface with build). Paths: `site/shop.js`,
`site/shop.html`, `site/shop.css` (after E47 has merged; shared with E48 by turns, never open at
the same time on the same file: the supervisor orders them), `site/measure.js` (new),
`src/osd/build.py` tile flags only (`write_tiles`; after E46 slice 1), `tests/site/speed.test.mjs`
(new), `tests/test_tiles.py` (new), `docs/program/evidence/e50/**`. Depends on E47; second pass
on E48.
