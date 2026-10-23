# Decisions

Open items are for the owner. A default is applied under the standing delegation (Ophiolite,
18 Oct 2026) and recorded; the owner can overturn it.

| # | Question | Default applied | Status |
|---|---|---|---|
| OSD-D1 | Repository home and name | `ophiolite-labs/open-subsurface-data`, public | DECIDED by the owner 23 Oct |
| OSD-D2 | Licences: Apache-2.0 for code, CC0 for records and outlines | Applied in `LICENSE`, `records/LICENSE` | DEFAULT |
| OSD-D3 | Basemap and theme: OpenFreeMap Positron (light) under a dark panel today; a dark basemap when one without a key is confirmed | Positron | DEFAULT |
| OSD-D4 | Domain | `opensubsurfacedata.org`, bought by the owner at Spaceship 23 Oct; apex to GitHub Pages, `www` CNAME | DECIDED by the owner 23 Oct; DNS records are an owner action |
| OSD-D5 | Where verification results live | A `verification-results` branch the verify workflow force-pushes; pages reads it. No bucket and no secret until mirrors (E07) need bytes; then a separate Hetzner project `open-subsurface-data` so its keys cannot reach Ophiolite's buckets | DEFAULT 23 Oct (replaces the bucket-first default) |
| OSD-D6 | Mirror policy: mirror only `redistribution: allowed`, under 20 GB, with a takedown contact; never `unknown` | As stated | DEFAULT |
| OSD-D7 | First twenty datasets: the SEG open-data list plus Sodir, NLOG, NDR, NOPIMS, NZP&M registers | As stated; E01 may swap entries with reasons | DEFAULT |
| OSD-D8 | Codex review: one round per kernel charter, none for surface and records | As stated | DEFAULT |
| OSD-D9 | Verification runner: the SEG wiki and NOPIMS refuse this VPS (403). Options: run `verify` on GitHub-hosted runners (different egress), or the MacBook, or treat a 403 from a challenge page as "blocked, not dead" | Treat as blocked-not-dead in E02 and run verify on GitHub-hosted runners first | DEFAULT |
| OSD-D10 | Name of the product on the site: "Open Subsurface Data" | As stated | DEFAULT |
