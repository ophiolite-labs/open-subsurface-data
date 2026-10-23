# One target per station. CI runs exactly `make check`.
.PHONY: check check-full test lint validate build verify site serve clean site-deps site-test shot

check: lint test validate build          ## the required CI check (offline, < 2 min)

lint:
	uv run ruff check src tests

test:
	uv run pytest -q

validate:                                ## every record and outline against its schema
	uv run osd validate

build:                                   ## build/catalog/*.json, outlines.pmtiles (tippecanoe) + site/data/
	uv run osd build
	mkdir -p site/data && rm -rf site/data/stac site/data/*.pmtiles && cp -R build/catalog/. site/data/   # stac/ is a tree; tiles only when tippecanoe ran (E15)
	ls site/data | grep -vx files.txt > site/data/files.txt   # the map reads optional files from this list

check-full: build                        ## the whole STAC tree, every Item (OSD-D18; verify workflow on main, not the gate)
	uv run python -c "import sys; from pathlib import Path; from osd import stac; ok, m = stac.validate(Path('site/data/stac/catalog.json')); print(len(m), 'STAC objects', 'valid' if ok else 'INVALID'); sys.exit(not ok)"

verify:                                  ## network: reach origins, record levels (not part of `check`)
	uv run osd verify

site: build                              ## serve the map locally
	python3 -m http.server --directory site 8765

site-deps:                               ## Playwright and Chromium for the site test (not part of `check`)
	npm install --no-audit --no-fund
	npx playwright install chromium

site-test: build                         ## Playwright against the local site (not part of `check` yet)
	npm run --silent site-test

shot: build                              ## desktop and phone screenshots into build/shots/
	mkdir -p build/shots
	node tools/shot.mjs build/shots

clean:
	rm -rf build site/data
