# 26 Nov 2026: the second owner round explained on the controller (rulings 8-13)

The owner's second round (Safari first visit 3499 ms; phone 1916 ms against 875 ms; Safari return
visit 2126 ms with 14 of 19 tile ranges from the network) tested on the controller, never on the
owner's machines, one browser at a time. Scripts in this folder: `variants.mjs` (ruling 8's table),
`variants-table.mjs` (the medians), `hash-drift.mjs` (ruling 13), `return-visit.mjs` (rulings 11, 12),
`phone-list.mjs` (ruling 10). The published page, 26 Nov 12:06-13:00 UTC. Controller numbers are a
method check: WebGL is drawn in software (SwiftShader), and the host was shared with other lanes
(its load rose to 200 after 13:15 UTC, when the site tests timed out; no variant run was made then).

## Ruling 13 first: the page rewrote its own address (cause of rulings 11 and 13)

shop.js writes the view into the hash at every move; the measuring mode's ground fit (a map narrower
than 900 px is zoomed out to the laptop's ground) and its script moved the map, so the address after a
visit was the fitted view, and a reload or reopened tab measured one step further out each time:

| | measured view (address) on a 393 px phone, published page |
|---|---|
| first | z3.8 (z5) |
| reload 1 | z2.6 (z3.8) |
| reload 2 | z1.4 (z2.6) |
| reload 3 | z0.2 (z1.4) |
| reload 4 | z-1 (z0.2), latitude 0: the whole world |

On the owner's Safari window (map 450 px wide) the step is one level: address z5 measured z4, the next
visit read address z4 and measured z3, exactly the owner's two Safari visits. **Fixed** in
`site/measure.js`: the measuring mode holds the address it was opened with until its script ends (a
test reloads and gets the same view). The phone's "zoomed far in" (ruling 3, ruling 10) is **not** this
drift, which only zooms out: see ruling 10.

## Ruling 11: the Safari return visit's 14 network ranges

Playwright WebKit, 850 x 929 at 2x, this checkout served locally with the host's validators; the
server's log is what crossed the network:

| visit | view | our files from the server |
|---|---|---|
| 1, first, note's address | z4 | everything (and records.json 4 times, see ruling 8) |
| 2, the drifted address z4 (the owner's return) | z3 | **14 tile ranges** (9 areas, 5 outlines), 411 kB, + 2 wells files |
| 3, the note's address again | z4 | **nothing** |

The worker was in control and answered every range it had kept; the 14 were tiles of a view the first
visit never showed, because the address had drifted. With the address held, a return visit of the
note's address takes no body of our data files from the server (visit 3; in the published-page runs below the
31 kB left are the HTML, CSS and the two scripts, which the worker never touches). Those three visits were back to back.

**Still open: the same with 11 minutes between the visits.** With the visits 11 minutes apart and the
tab on about:blank in between, visit 3 (the note's address) took 24 tile ranges and records.json,
areas.json and files.txt from the server again: the worker answered nothing it had kept. The worker
checks each file with one HEAD per visit and does not depend on max-age, so the time itself should not
matter. Suspected, not yet shown: Playwright's WebKit contexts keep their storage in memory (no
profile on disk), and WebKit may drop the Cache Storage of an origin with no page open. Real Safari
keeps it on disk. `return-visit.mjs` reads what the caches hold before and after the wait. The run
that would tell was stopped when the host ran out of memory (26 Nov), and it waits until local browsers
are allowed again. It is then run with an on-disk WebKit profile in /tmp/osd-e50-<name>, removed
afterwards.

## Rulings 9 and 12: zoom back, 2 requests in Safari

Both are ours, not the base map's: two areas.pmtiles tile ranges (bytes 945791-948109 and
1197511-1200059 at the note's view) that MapLibre asks for again when the script comes back. The
worker answers both from its cache: nothing reaches the server (visit 3 above). Chromium at the same
window asks for the same two and reads them as "2 req, 0 B, cache"; Safari's Resource Timing gives a
worker's answer the response's size, so the readout shows 6-7 kB that never crossed the network.
Line 3's target (0 requests) is therefore missed by the map, at a laptop window this size, in both
browsers; the bytes are 0. Why MapLibre drops those two areas tiles is in shop.js's area source
(E51 holds shop.js): inbox note 8.

## Ruling 8: the variants

Chromium, phone 393 x 690 at 3x, network held to 30/15 Mbit/s and 40 ms; 7 runs each (3, then 4 with
the order rotated), medians. "Wire" is what crossed the network, the worker's own requests included.

chromium 156.0.8078.4, 393x690@3, 2026-11-26T12:06:36.404Z
| variant | visit | runs | usable ms (each) | list ms | site at idle, wire | site since load, wire | of it by the worker | base map at idle |
|---|---|---|---|---|---|---|---|---|
| base | first | 7 | **2224** (2661, 2180, 2381, 2542, 2224, 2174, 2076) | 634 | 18 req, 367 kB | 51 req, 898 kB | 34 req, 532 kB | 49 req, 3868 kB |
| base | return | 7 | **1511** (1520, 1502, 1490, 1553, 1511, 1506, 1514) | 235 | 11 req, 3 kB | 13 req, 3 kB | 9 req, 0 kB | 62 req, 42 kB |
| no-sw | first | 7 | **2155** (2219, 2036, 2125, 2395, 2155, 2311, 2039) | 624 | 17 req, 366 kB | 28 req, 748 kB | 0 req, 0 kB | 49 req, 3868 kB |
| no-sw | return | 7 | **1534** (1620, 1519, 1657, 1528, 1574, 1534, 1455) | 287 | 17 req, 152 kB | 28 req, 257 kB | 0 req, 0 kB | 49 req, 42 kB |
| no-areas | first | 7 | **2164** (2099, 2164, 2185, 2248, 2092, 2328, 2059) | 602 | 14 req, 300 kB | 37 req, 614 kB | 24 req, 315 kB | 49 req, 3868 kB |
| no-areas | return | 7 | **1359** (1354, 1442, 1394, 1336, 1326, 1359, 1405) | 219 | 10 req, 3 kB | 12 req, 3 kB | 8 req, 0 kB | 58 req, 42 kB |
| neither | first | 7 | **2079** (2058, 2079, 2030, 2279, 2263, 2291, 2069) | 593 | 13 req, 299 kB | 19 req, 531 kB | 0 req, 0 kB | 49 req, 3868 kB |
| neither | return | 7 | **1480** (1480, 1470, 1523, 1401, 1507, 1639, 1404) | 264 | 13 req, 86 kB | 19 req, 136 kB | 0 req, 0 kB | 49 req, 42 kB |

Playwright WebKit, 850 x 929 at 2x (the owner's Safari window), the network as it is, 3-4 runs
rotated. WebKit does not report the worker's own requests, so "wire" undercounts with the worker on
(the local server log of ruling 11 counts them).

webkit 27.2, 850x929@2, 2026-11-26T12:18:36.675Z
| variant | visit | runs | usable ms (each) | list ms | site at idle, wire | site since load, wire | of it by the worker | base map at idle |
|---|---|---|---|---|---|---|---|---|
| base | first | 3 | **1670** (1599, 1742, 1670) | 614 | 24 req, 589 kB | 24 req, 589 kB | 0 req, 0 kB | 47 req, 5060 kB |
| base | return | 3 | **1705** (2138, 1705, 1540) | 619 | 4 req, 31 kB | 4 req, 31 kB | 0 req, 0 kB | 66 req, 5059 kB |
| no-sw | first | 3 | **1721** (2067, 1721, 1714) | 667 | 23 req, 586 kB | 48 req, 1095 kB | 0 req, 0 kB | 47 req, 5060 kB |
| no-sw | return | 3 | **1548** (1548, 1621, 1536) | 526 | 23 req, 586 kB | 48 req, 1095 kB | 0 req, 0 kB | 47 req, 5059 kB |
| no-areas | first | 3 | **1665** (1753, 1665, 1633) | 619 | 18 req, 507 kB | 20 req, 507 kB | 0 req, 0 kB | 47 req, 5060 kB |
| no-areas | return | 3 | **1623** (1813, 1620, 1623) | 553 | 4 req, 31 kB | 4 req, 31 kB | 0 req, 0 kB | 60 req, 5059 kB |
| neither | first | 4 | **1694** (1764, 1694, 1620, 1614) | 627 | 17 req, 504 kB | 28 req, 799 kB | 0 req, 0 kB | 47 req, 5060 kB |
| neither | return | 4 | **1550** (1549, 1550, 1516, 1753) | 527 | 17 req, 504 kB | 28 req, 800 kB | 0 req, 0 kB | 47 req, 5058 kB |

The fetch preloads (`<link rel=preload as=fetch>` for files.txt, records.json, areas.json, from #109),
each variant through the same request routing (which turns the HTTP cache off), 4 runs each:

chromium 156.0.8078.4, 393x690@3, 2026-11-26T12:52:43.023Z
| variant | visit | runs | usable ms (each) | list ms | site at idle, wire | site since load, wire | of it by the worker | base map at idle |
|---|---|---|---|---|---|---|---|---|
| routed | first | 4 | **2271** (2370, 2208, 2271, 2241) | 733 | 18 req, 391 kB | 51 req, 1126 kB | 34 req, 738 kB | 48 req, 3868 kB |
| routed | return | 4 | **2064** (2064, 1964, 2122, 1986) | 481 | 11 req, 34 kB | 13 req, 34 kB | 9 req, 0 kB | 61 req, 3867 kB |
| no-preload | first | 4 | **2258** (2231, 2258, 2419, 2190) | 696 | 18 req, 391 kB | 51 req, 1126 kB | 34 req, 738 kB | 48 req, 3868 kB |
| no-preload | return | 4 | **2181** (2181, 2055, 2237, 2060) | 490 | 11 req, 34 kB | 13 req, 34 kB | 9 req, 0 kB | 61 req, 3867 kB |

webkit 27.2, 850x929@2, 2026-11-26T12:55:50.425Z
| variant | visit | runs | usable ms (each) | list ms | site at idle, wire | site since load, wire | of it by the worker | base map at idle |
|---|---|---|---|---|---|---|---|---|
| routed | first | 4 | **1883** (1883, 1696, 1686, 2394) | 713 | 23 req, 587 kB | 35 req, 590 kB | 0 req, 0 kB | 49 req, 6039 kB |
| routed | return | 4 | **1730** (1951, 1612, 1730, 1578) | 557 | 23 req, 587 kB | 48 req, 1096 kB | 0 req, 0 kB | 49 req, 6038 kB |
| no-preload | first | 4 | **1792** (1792, 1814, 1689, 1692) | 651 | 21 req, 404 kB | 21 req, 404 kB | 0 req, 0 kB | 49 req, 6039 kB |
| no-preload | return | 4 | **1689** (1689, 1695, 1633, 1563) | 551 | 20 req, 401 kB | 45 req, 910 kB | 0 req, 0 kB | 49 req, 6038 kB |

Read:
- **No candidate moves "usable" on the controller.** In both browsers the four variants lie within
  each other's spread (Chromium 2079-2224 ms, WebKit 1665-1721 ms). The worker registers at the
  first idle, after usable, so it cannot delay a first visit; the area tiles end before the base map's
  (Chromium: our last range at ~1.08 s, the base map's vector tiles at ~1.3 s and its 30 glyph ranges
  at ~1.8 s; usable ~2.1 s).
- **(a) areas.pmtiles** costs bytes, not time: 4-6 requests and 66-83 kB more at idle.
- **(b) the worker** costs a first visit bytes after usable: Chromium +23 requests, +150 kB on the
  wire (the first view's ranges read once more to fill its cache: Chromium's and WebKit's HTTP caches
  do not answer a byte range with a weak ETag). It saves every return visit: Chromium 257 kB to 3 kB,
  WebKit 586 kB (no worker: everything again) to 31 kB. It is worth keeping. The page-side "since
  load" count rises with it (Safari: 48 to 57-68 requests), because the cache-filling reads are page
  requests and Safari gives a worker's answers a size.
- **(c) Safari and ranges**: Safari reuses no byte range from its HTTP cache (no-sw return visit:
  everything again); with the worker it reuses all of them.
- **Found beside them: the fetch preloads.** WebKit does not hand a fetch preload to the page's
  fetch(), so files.txt, records.json and areas.json came twice in every Safari first visit: 183 kB
  and 3 requests more at idle (587 to 404 kB without them). In Chromium they bought nothing
  measurable. **Cut** in `site/shop.html`.
- **The owner's phone pair is not a regression measurement.** Round 1 (875 ms) read records.json
  with no body (from the browser's cache, so not a first visit) and opened "zoomed far in"; round 2
  (1916 ms) showed a view in California ("San Diego Trough"). Neither measured the note's ground, and
  the first was warm. The Safari pair (3499 / 2126 ms) was two different views (ruling 13).

## Ruling 10: the phone's list

At 393 x 690 at 3x with the note's address, after the script: the view is z3.8 over 57/3 (the North
Sea, 55 datasets), and every listed dataset's box lies in the map's bounds and in the part above the
list sheet; the map element ends where the sheet begins, so its bounds count nothing under the sheet
(`phone-list-393.png`). **The list is right.** The owner's screenshot shows another place (offshore
California, outlines drawn as at zoom 7 or more, no coast) with a list that fits it; how the phone got
there is not reproduced: the drift of ruling 13 only zooms out. Likely a reopened tab or a completed
address from an earlier visit; with the address now held, and the view line on a phone (under More),
the next phone screenshot with More open will say. Also seen and reproduced: on a 393 px screen the
area-kind switch (Countries | Provinces | Basins | Licences) lies over the base map's credit line when
the credit is unfolded (shop.js and shop.css: inbox note 8).
