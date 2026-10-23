# Site fixture: one verification per reason class (E27)

`verification/` holds one verification/4 document per reason class the map and the status page show:
no listing published (open, and registration), a listing that names no file, robots.txt disallowing the
listing, blocked by OSD-D20 (answers a browser, not the verifier) and by OSD-D9 (challenge page), a dead
origin, L2 and L3. Every other record stays "never verified". Modelled on the stored results of run
39964480446 and the H1 branch run; hand-written, validated by `tests/test_build.py`.
`tests/site/site.test.mjs` builds records.json from these with `osd.build` and serves it in place of the
built one.
