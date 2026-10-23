## E11 Hosting and domain — IN PROGRESS · Ops · no strategy

Authority: `DECISIONS.md` OSD-D1 (public repository), OSD-D4 (opensubsurfacedata.org, bought at
Spaceship 23 Oct), OSD-D5 (results on a branch, bucket only for mirrors).

**Outcome.** The site answers at https://opensubsurfacedata.org with real verification levels,
and nothing about hosting needs a secret.

**Context today (23 Oct).** Repository public at `ophiolite-labs/open-subsurface-data`; `pages.yml`
publishes `site/` on every merge and reads the `verification-results` branch that a dispatched
`verify` run force-pushes. GitHub Pages serves from the github.io address until DNS points at it.

**The design the lane must map to.**
1. Apex `opensubsurfacedata.org` on GitHub Pages: four A and four AAAA records at Spaceship, a
   `www` CNAME to `ophiolite-labs.github.io`, the custom domain set on the repository's Pages
   settings, HTTPS enforced once the certificate is issued.
2. Domain verified for the ophiolite-labs organisation (a TXT record) so no other account can
   claim the name on Pages.
3. Verification results: the `verification-results` branch; no bucket, no key.
4. No analytics, no cookies; a plain `robots.txt` that allows indexing.
5. Mirrors (E07) get a bucket in a separate Hetzner project when that lane opens; nothing here.

**Acceptance.**
- `curl -sI https://opensubsurfacedata.org/` returns 200; `http://` redirects to `https://`.
- `www.opensubsurfacedata.org` redirects to the apex.
- After a dispatched verify run, the published `data/records.json` shows `L1` for
  `sodir/factpages` with that run's date.
- `dig TXT _github-pages-challenge-ophiolite-labs.opensubsurfacedata.org` returns the value the
  organisation settings show.

**Out of scope.** CDN beyond Pages, mirrors, uptime monitoring.

**Stop rules.** DNS not yet entered: everything else is done; the domain lines wait on the owner.

**Ownership and dependencies.** Supervisor; paths `.github/workflows/**`, `site/robots.txt`,
`docs/program/**`. Owner actions: the DNS records and the TXT record.

**Evidence to inspect.** The curl and dig outputs; the published `records.json`.
