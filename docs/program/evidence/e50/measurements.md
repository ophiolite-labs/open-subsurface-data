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

| # | Practice | Check | State at PR A (#100) | State at PR B |
|---|---|---|---|---|
| 1 | tiles under 500 KB, thinned where dense; zoomed out, counted circles | `tests/test_tiles.py` (built archives, `make check-full`); `speed.test.mjs` practice 1 | circles yes; 2 tiles at z7 over 500 KB (1061 KB), `--no-tile-size-limit` | yes: `write_tiles` passes `--drop-densest-as-needed` instead; 0 tiles over 500 KB (largest z7 487 KB) |
| 2 | the list from the page's records, never from tile queries | `speed.test.mjs` practice 2 | yes | yes |
| 3 | `minzoom`/`maxzoom`; few layers | `speed.test.mjs` practice 3 | `wells-tiles` z7-24 only | also `wells-cluster`, `wells-count` and (PMTiles path) `wells` z0-7 |
| 4 | `maxTileCacheZoomLevels` set, 5 or more | `speed.test.mjs` practice 4 | default, not set | `maxTileCacheZoomLevels: 5` |
| 5 | `refreshExpiredTiles: false` | `speed.test.mjs` practice 5 | not set | set |
| 6 | one file, index at the front; protocol once | `tests/test_tiles.py`; `speed.test.mjs` practice 6 | yes | yes (both archives) |
| 7 | hover by feature state | `speed.test.mjs` practice 7 | yes | yes |
| 8 | `fadeDuration` 0 with names on | `speed.test.mjs` practice 8 | 300 ms | 0 |

**What the thinning costs (practice 1).** tippecanoe's `--drop-densest-as-needed` raises the
spacing between features for a whole zoom level until no tile of it is over 500 KB. Only z7
needed it. Counted from the archive (this host's tippecanoe):

| zoom | features before | after | wellbore points before | after |
|---|---|---|---|---|
| 7 | 184,220 | 79,734 | 178,339 | 74,325 |
| 8 | 192,271 | 192,271 (the same) | 182,565 | 182,565 |
| 12 | 649,505 | 649,505 (the same) | 180,340 | 180,340 |

At z7, the first level where the page draws single wells, dense areas show about four wells in
ten. From z8 up every well is there, as before (the E36 comparison at z12 is unchanged). Below z7
the wells are counted circles from the build's grids, which do not change.

The built archives (this host's tippecanoe 2.49.0; CI pins 2.79.0), read by
`uv run python tests/test_tiles.py`. At PR A:

```
outlines.pmtiles: 211750 tiles z0-12, clustered=True, leaf levels 1, root directory ends at byte 360,
2 tiles >= 500 KB; largest per zoom: z0 155 KB, z1 100 KB, z2 117 KB, z3 94 KB, z4 106 KB, z5 119 KB,
z6 105 KB, z7 1061 KB, z8 418 KB, z9 364 KB, z10 248 KB, z11 98 KB, z12 68 KB
```

At PR B:

```
outlines.pmtiles: 211750 tiles z0-12, clustered=True, leaf levels 1, root directory ends at byte 360,
0 tiles >= 500 KB; largest per zoom: z0 155 KB, z1 100 KB, z2 117 KB, z3 94 KB, z4 106 KB, z5 119 KB,
z6 105 KB, z7 487 KB, z8 418 KB, z9 364 KB, z10 248 KB, z11 98 KB, z12 68 KB
areas.pmtiles: 74358 tiles z0-8, clustered=True, leaf levels 1, root directory ends at byte 203,
0 tiles >= 500 KB; largest per zoom: z0 74 KB ... z8 2 KB
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

**The laptop, Chrome.** The owner's MacBook Pro (Apple M1 Pro, 16 GB, macOS 26.5.2, the built-in
Retina display and a 5K screen), Google Chrome 158.0.8127.38, headed, with the Mac's GPU (WebGL
renderer `ANGLE Metal Renderer: Apple M1 Pro`). It is driven from the controller by
`docs/program/evidence/e50/drive-chrome.mjs`. That script opens Chrome on the Mac over SSH in a
temporary profile of its own (`/tmp/osd-e50-<name>`; it refuses any other path), never the owner's,
and connects through an SSH tunnel to Chrome's DevTools port. It opens the address, waits for the
measuring mode's numbers, saves them with a screenshot, closes that Chrome and removes the profile.
With `--keep`, the profile stays for the return visit; it is removed after the next day's visit.

    node docs/program/evidence/e50/drive-chrome.mjs --label "first visit" --keep --profile /tmp/osd-e50-return
    # more than ten minutes later, and the next day:
    node docs/program/evidence/e50/drive-chrome.mjs --label "return +10 min" --keep --profile /tmp/osd-e50-return
    node docs/program/evidence/e50/drive-chrome.mjs --label "return next day" --profile /tmp/osd-e50-return

**The laptop, Safari, and the phone** need a person. Safari has no temporary profile, and the lane
does not touch the owner's own. The instructions for the owner are in the inbox note
(`~/.local/share/osd-program/inbox/e50-owner-note.md`): the address, the four bold numbers, and for
Safari the lines under line 4, now, after ten minutes, and the next day.

**Before and after the practices (the stop rule).** The same Chrome on the Mac was used for both.
Both versions of the page were served from the controller through a reverse SSH tunnel by the
script's `--serve` (byte ranges, no compression, `max-age=600`), with the same data. A is main with
the hook line; B is A with practices 3, 4, 5 and 8 switched on. There were five first visits each,
alternating B and A, each in a fresh profile. 25 Nov 2026:

| | usable (first idle), median (range) | list, median | drag+zoom | longest frame | zoom back |
|---|---|---|---|---|---|
| A (before) | 2149 ms (2057–2421) | 1591 ms | 60 fps in all five | 18–19 ms | 0 req, 0 B |
| B (after) | 2134 ms (2071–2265) | 1550 ms | 60 fps in all five | 18–19 ms | 0 req, 0 B |

B is not slower, so the practices stay on. These first visits go through a tunnel from a server in
Germany and carry `records.json` uncompressed (608 kB). They compare A with B. The numbers against
the target are the published page's, below.

### The published page, against the target

`https://opensubsurfacedata.org/shop.html?measure=1#map=5.00/57.0000/3.0000`, as published by
#101 (f29a69b) with main's `shop.js`: the practices of PR B are not on it yet. 25 Nov 2026, the
owner's MacBook, Chrome 158 headed, home broadband, the window 1400×813 at 2× on the 60 Hz display.

**Measurement 1, the laptop: map usable and pictures a second.** There were five first visits, each in
a fresh profile, with the CDN warm:

| | usable (first idle) | list | drag+zoom | longest frame | site at first idle |
|---|---|---|---|---|---|
| median of 5 | **1652 ms** (1387–2002) | 1331 ms | **59.8 fps** in all five | 32–33 ms | 14 req, 269 kB |
| target | within 2 s | | 60 | | under 1 MB |

The target is met. The display's own rate is 60 Hz, so 59.8 fps is every picture the screen can
show.

The first visit straight after the deploy took 4809 ms. Of that, 2866 ms was a single request:
the PMTiles header range of a freshly published `outlines.pmtiles`, while GitHub Pages' CDN went
to its origin for the 115 MB file. Once the CDN had it, the same request took 20 ms. So a visitor
right after a release can wait about 3 s more, once per CDN location. Where a warm first visit's
time goes (the median run, ms from navigation start):

| ms | what |
|---|---|
| 0–62 | `shop.html` |
| 66–468 | `maplibre-gl.js` from unpkg (the longest single item; `shop.js` waits for it) |
| 493–592 | `files.txt`, then `pmtiles.js` from unpkg, then the PMTiles header, one after another |
| 593–709 | `records.json` (153 kB gzipped) |
| 749–840 | the base map style, then its sprites, fonts and tiles until about 1300 |
| about 1350 | the list counted; the map idle at 1672 after the North Sea outline tiles |

The three largest costs: MapLibre's script (about 400 ms), the base map's own requests (about
550 ms), and our serial chain before the map starts (`files.txt` → `pmtiles.js` → header →
`records.json`, about 220 ms).

**Measurement 3, zooming out and back:** **0 requests, 0 bytes** coming back in every run, on the
laptop as on the controller. The way out fetched 5 requests, 85 kB, of new, lower-zoom tiles.

**Measurement 2, a return visit (Chrome).** One temporary profile, `/tmp/osd-e50-return`, is kept
on the Mac until the next-day visit and then removed. No deploy happened between the visits (the
last Pages deploy was at 16:56 UTC). Bytes are Chrome's `transferSize`: 300 means headers only,
i.e. the file came from the cache after a `304`.

| visit | UTC | map usable | records.json | outlines.pmtiles | our files at first idle |
|---|---|---|---|---|---|
| first | 17:12 | 2029 ms | 153 kB, downloaded | 6 ranges, 76 kB | 14 req, 269 kB |
| +11 min | 17:24 | **9514 ms** | 153 kB, **downloaded again** | header range **failed** | 10 req, 7.39 MB (the whole `outlines.geojson`) |
| +1 min | 17:25 | 703 ms | from cache, 0 B | 6 ranges, 76 kB | 14 req, 82 kB |
| +11 min | 17:37 | **11011 ms** | 153 kB, downloaded again | header range failed | 10 req, 7.40 MB |
| next day | 26 Nov 09:37 | 5055 ms | 145 kB, downloaded (a new deploy at 09:28 changed it) | 17 ranges, 160 kB; the header 3.0 s (CDN cold after the deploy) | 23 req, 366 kB |

The target is missed. What was recorded at 17:37: Chrome checked `records.json` with
`If-None-Match: W/"6b0713bf-aa295"`, but Pages now gives `W/"6b0713c0-aa295"` for the same deploy
(`"6b0713c1-…"` was also seen). **The ETag of one file differs between GitHub Pages' servers**, so
a check comes back as a full 200. The header range of `outlines.pmtiles`, asked with the old ETag
in `If-Range`, came back as **200 with the whole file**. PMTiles 4.5.0 refuses that and aborts, and
`shop.js` fell back to the GeoJSON. PR #105 asks for the header once more with `cache: 'reload'`.
Reproduced on the Mac with `--serve`, a 5 s max-age and an ETag changed between visits: main
11,541 ms (GeoJSON), #105 1,347 ms (tiles). Downloading `records.json` again on every return remains.
The charter's next step is the browser cache, proposed in the inbox for DECISIONS.

The next-day visit is not a clean return visit: four deploys came between, the last (E48, #104)
nine minutes before, so `records.json`, `areas.json` and both archives were new files and came over
the wire, and the header of the new `outlines.pmtiles` took 3.0 s at a cold CDN. With #105 on the
page, the tiles stayed on (no GeoJSON). The profile was removed afterwards.

### 26 Nov 2026: the owner's own visits (owner action 141) and four rulings

Read off the owner's screenshots by the owner, relayed by the supervisor; the screenshots stay in
the inbox (they show the owner's browser).

| | MacBook, the owner's own Chrome profile (not Safari) | iPhone 15, Wi-Fi, **Low Power Mode on** |
|---|---|---|
| 1 usable · list | **2326 ms** · 1988 ms | **875 ms** · 540 ms |
| 2 drag+zoom · longest frame | **60 fps** · 18 ms | 30.1 fps · 36 ms: **not a valid reading** (see below) |
| 3 zoom back · out | **0 req, 0 kB** · 1 req, 120 kB | **0 req, 0 kB** · 3 req, 25 kB |
| 4 since load · at idle | 32 req, 524 kB · 18 req, 305 kB | 19 req, 74 kB · 13 req, 37 kB |
| records.json | 1 network | 1 no body |
| outlines.pmtiles | 22 ranges, 316 kB (15 network, 7 no body) | 13 ranges, 73 kB |
| screen | 1857×1173@2, 123 layers | 393×690@3, 123 layers |

- **The phone's 30.1 fps** is a steady 30 Hz (longest frame 36 ms): iOS Low Power Mode halves
  `requestAnimationFrame`. It counts as neither met nor missed; one more visit with Low Power Mode
  off is asked of the owner. The measuring mode now measures the display's own rate at rest before
  the script and prints it beside line 2 ("30 fps of 30" is a capped display, "30 fps of 60" a slow
  page).
- **The phone opened "zoomed far in"** (four single dots, no country visible), so it measured
  another place. Not reproduced: the published page in an iPhone 15 Pro emulation opens the address
  at z5 over 57°N 3°E and comes back there after the script. Single dots mean zoom 7 or more, so
  the browser was not on the address's view; a remembered tab or a completed address is likely.
  The measuring mode now (a) prints the view it measured under **More**, and (b) on a map smaller
  than 900×600 zooms out before the first load to show the laptop's ground (z5 on the laptop is
  z3.8 on a 393 px phone).
- **The box covered the list rows on the phone.** On a narrow screen it now sits on the map's top
  left, shows only the four lines (More shows the files, Hide folds it). It is checked in
  `speed.test.mjs` ("measuring mode on a phone").
- **Safari on the Mac is still owed** (the owner's screenshot was Chrome). Safari's return-visit
  number stays open; it does not block the browser-cache slice.

**Laptop "usable within 2 s": not yet met as an acceptance line (ruling 1).** The owner's own
visit missed by 326 ms. The screenshot carries no clock, so whether it fell just after a deploy
cannot be read from it; its 18 requests and 305 kB at idle (against 14 and 269 kB in the 1400-wide
runs) come from the larger window (1857×1173): more base map and outline tiles. Five clean first
visits at the owner's window size, on the published page after E48 (OSD-D41's compact JSON in;
the area tiles new), 26 Nov 09:40–09:46 UTC:

| run | 1 | 2 | 3 | 4 | 5 | median | worst |
|---|---|---|---|---|---|---|---|
| usable (ms) | 2020 | 2294 | 1671 | 1729 | 1517 | **1729** | **2294** |

All five at 60 fps; 32 requests, 404 kB at first idle. The worst of five is over the line. Where
the median run's time goes (ms from navigation start):

| ms | what |
|---|---|
| 0–87 | `shop.html`, `shop.js` |
| 0–247 | `maplibre-gl.js`; `shop.js` runs only after it |
| 262–591 | **our serial chain**: `files.txt` → `pmtiles.js` → outlines header → areas header → `records.json` (191 ms) → `areas.json`, one after another |
| 617–1284 | the base map: style, sprites, Natural Earth tiles, then fonts in three waves |
| **1326–1720** | **our own tiles and the wells grid: asked for only at 1326**, after the base map's last font |
| 1729 | the map idle |

The three largest costs:
1. **Our tiles wait for the base map: about 400 ms.** `shop.js` added its sources at the map's
   `load` event, which fires only once every base map tile, sprite and font is in. Cut: add them at
   `style.load` (the style is read), so our tiles load beside the base map's.
2. **The base map's own requests: about 670 ms** (617–1284). Not ours to cut beyond a
   `preconnect` to its host, which saves its first connection.
3. **Our serial chain before the map is made: about 330 ms** (262–591), 460 ms in the worst run
   (`records.json` 186 ms and `areas.json` 147 ms one after the other). Cut: `records.json` and
   `areas.json` asked for at once beside `files.txt`, both tile headers read together, and
   `shop.html` preloading `files.txt`, `records.json`, `areas.json` and `pmtiles.js` while
   `maplibre-gl.js` downloads.

`maplibre-gl.js` (about 250 ms here, 400 ms on 25 Nov) stays: it is the map.

The after numbers (worst of five clean first visits, plus one visit in a used profile) are taken on
the published page once the cuts are merged. The owner capped the Chrome windows opened on the
MacBook at six a day, in one batch: the six of 26 Nov were the next-day return visit and the five
runs above, so the after batch runs on a later day.

### Measurement 4, the globe with every well: the method, and the controller's numbers

What is measured: the measuring mode's line 2 (pictures a second over the scripted drag and zoom,
beside the display's own rate) at two views, on the laptop and on the phone:

    https://opensubsurfacedata.org/shop.html?measure=1#p=globe
    https://opensubsurfacedata.org/shop.html?measure=1#map=6.00/47.5000/-100.5000&p=globe

On the laptop both ride on one Chrome window opening (`drive-chrome.mjs --then URL,URL`, after the
used-profile visit of ruling 1): the owner caps the windows opened on the MacBook at six a day, in
one batch. On a phone the measuring mode zooms out to the laptop's ground (z6 is z4.8 on a 393 px
phone); the view it measured is under More.

The controller's numbers (headless Chromium, SwiftShader: the GPU is the CPU, so these numbers say
how the globe compares with the flat map, not what a laptop does; `speed.test.mjs` "measurement 4"):

| view | width | projection | usable | drag+zoom | longest frame | at first idle |
|---|---|---|---|---|---|---|
| first view (z3.3) | laptop | globe | 1966 ms | 11.3 fps | 200 ms | 30 req, 1.08 MB |
| first view (z3.3) | laptop | flat | 1364 ms | 22.2 fps | 83 ms | 23 req, 1.01 MB |
| first view (z2.1) | phone | globe | 2114 ms | 11.8 fps | 117 ms | 24 req, 1.09 MB |
| first view (z2.1) | phone | flat | 1199 ms | 21.0 fps | 83 ms | 21 req, 1.05 MB |
| North Dakota z6 | laptop | globe | 1860 ms | 36.1 fps | 83 ms | 23 req, 0.90 MB |
| North Dakota z6 | laptop | flat | 1042 ms | 45.8 fps | 50 ms | 23 req, 0.90 MB |
| North Dakota z4.8 | phone | globe | 1467 ms | 46.0 fps | 100 ms | 15 req, 0.87 MB |
| North Dakota z4.8 | phone | flat | 1072 ms | 43.5 fps | 67 ms | 15 req, 0.87 MB |

On the controller, the globe halves the pictures a second at the first view (the whole earth with
every well's cluster) and costs about a fifth at zoom 6. The bytes are the local build's (records
not yet compact). The laptop's and the phone's own numbers are owed: the laptop in the next Mac
batch, the phone from the owner. If the phone misses a usable rate, the charter's choice follows
(the lighter globe or the globe off by default on small screens), stated with its reason.

### The browser cache (OSD-D40): `site/sw.js`

What it does: a service worker, registered by `shop.js` after the first idle, for the files directly
under `data/` that end in `.json`, `.txt` or `.pmtiles`, and nothing else. It never touches HTML, JS
or CSS.
- **Tile archives:** byte ranges come from the cache when the file on the host is the one the cache
  holds, otherwise from the network, and are kept.
- **JSON and text:** these come from the cache at once and are refreshed in the background when the
  host's file has changed (stale-while-revalidate).
- **How it tells "the same file":** one `HEAD` per file per visit, with no body. It reads the size
  and modification time from the host's `W/"mtime-size"` ETag, and allows a minute of difference
  between Pages' servers.
- **Its own network requests** carry no `If-Range`, so the stale-ETag 200 of measurement 2 can't
  happen through it.
- **On a first visit** the page isn't under the worker yet. Once it is, the page reads its first
  load's files and ranges once more from the browser's HTTP cache (`cache: 'force-cache'`, no
  network), so the worker holds them for the return visit.

The switch: publishing `site/sw-off.txt` switches it off for every visitor. With each visit the
worker asks for that file (`HEAD`); when it is there, the worker deletes its caches, unregisters,
and gives nothing from a cache.

Tested in `speed.test.mjs`, on the controller (the server's own log of bodies sent):

| | |
|---|---|
| a return visit | **0 bodies of our data files** from the server (48 on the first visit); 7 `HEAD`; the map from the tiles; only `data/` files kept |
| a file changed on the host | fetched once by the worker on the return visit (`HEAD`, `GET`), for the next visit |
| `sw-off.txt` published | caches deleted, the worker unregistered; the next visit takes every data file from the server and keeps nothing |

The return visit in Chrome on the laptop (the acceptance) is in the next Mac batch. Safari is reported
by the owner.
