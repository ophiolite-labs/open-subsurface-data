# Handoff

Repository: https://github.com/ophiolite-labs/open-subsurface-data (public, OSD-D1). Site: https://opensubsurfacedata.org (OSD-D4).

## Commands

```
uv sync                    # once
make check                 # lint, tests, validate, build  (the CI gate, offline, ~10 s locally)
make verify                # network: writes build/verification/*.json
uv run osd verify sodir/factpages equinor/volve     # some records only
uv run osd status          # one line per record with its level
make site                  # http://localhost:8765
```

Screenshot for a surface lane (Playwright from the Ophiolite web tree):

```
(python3 -m http.server --directory site 8765 &) && PLAYWRIGHT=<path>/node_modules/playwright node tools/shot.mjs out.png
```

## Known reds and baselines (23 Oct)

- SEG wiki answers HTTP 403 to this host for any user agent (Cloudflare). Not dead; see OSD-D9.
- NOPIMS page answers 403 from this host. Same class.
- Headless Chrome with virtual time budget hangs on MapLibre; use Playwright with swiftshader.
- `line-dasharray` takes no data expression in MapLibre 4: placeholder and derived outlines are
  separate line layers.

## Starting a lane (supervisor)

Brief by reference: the charter path, the branch name, the claim row, `make check` as the gate,
the known reds above. Nothing else; the charter is the authority.

## Starting as supervisor

Read `PROGRAM.md`, `CLAIMS.md`, `DECISIONS.md`, then this file. Confirm `make check` is green on
main. Take the first QUEUED epic whose dependencies are MERGED.
