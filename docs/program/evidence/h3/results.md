# H3 branch run against main's stored results (24 Oct 2026)

Branch run: verify workflow dispatched on `h3-robots-rfc-9309` at 8ec36b3 (design 3 head), all 196 records,
12 shards, run [40055355682](https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/40055355682),
success. Compared with main's stored results `verification-results` faa1aa8 (run 40052118575, the
snapshot the branch run read) by `compare.py` (this directory):
`gh run download 40055355682 -n verification -D run/` then `python compare.py run/ faa1aa8`.

## Level changes: five, none from robots.txt

No changed record has a robots.txt line on either side; each change is an origin or file answer
that differed between the two runs (minutes apart), not the matcher.

| Record | main → branch | Explaining line (main ⇒ branch) | robots line |
|---|---|---|---|
| geus/formation-tops-denmark | L0 → L1 | origin-reachable: timeout at dataverse.geus.dk ⇒ HTTP 200 | none either side |
| geus/havnso-reservoir-model | L0 → L1 | origin-reachable: timeout at dataverse.geus.dk ⇒ HTTP 200 | none either side |
| orogo/geoscience-programs | L0 → L1 | origin-reachable: timeout at www.orogo.gov.nt.ca ⇒ HTTP 206 | none either side |
| orogo/well-data | L1 → L0 | origin-reachable: HTTP 206 ⇒ timeout at www.orogo.gov.nt.ca | none either side |
| ns-energy/onshore-2d-seismic-navigation | L1 → L2 | files-checksummed: timeout on the Cumberland zip at novascotia.ca ⇒ 1 of 1 selected files hashed | none either side |

## robots.txt lines

Every robots.txt line on main is the same on the branch except one, at an unchanged level:

| Record | Level | main | branch |
|---|---|---|---|
| pgi/cbdg-boreholes | L1 both | robots.txt unreadable (HTTP 503), treated as disallow | robots.txt read; the layer is above the 50,000-feature whole-layer cap, kept as a partial export |

Unchanged on both sides (same words): ak-dggs/tax-credit-well-data (robots.txt disallows the listing,
dggs.alaska.gov), ar-energia ×3 and cpc/onshore-well-locations (robots.txt unreadable, timeout),
va-energy/gas-oil-wells (outline derivation refused: robots.txt disallows the layer).

No record lost a level because its publisher disallows the verifier under the RFC 9309 reading:
on the URLs this run asked for, no robots.txt outcome differs from main's apart from pgi's 503,
which is the host's answer, not the reading. data.qld.gov.au (the finding) has no record on main
yet; E37 meets it with this reading once H3 merges.
