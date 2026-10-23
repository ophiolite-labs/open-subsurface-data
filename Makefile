# One target per station. CI runs exactly `make check`.
.PHONY: check test lint validate build verify site serve clean site-deps site-test shot

check: lint test validate build          ## the required CI check (offline, < 2 min)

lint:
	uv run ruff check src tests

test:
	uv run pytest -q

validate:                                ## every record and outline against its schema
	uv run osd validate

build:                                   ## build/catalog/*.json + site/data/ from records + outlines
	uv run osd build
	mkdir -p site/data && rm -rf site/data/stac && cp -R build/catalog/. site/data/   # stac/ is a tree
	cp build/catalog/*.pmtiles site/data/ 2>/dev/null || true
	ls site/data | grep -vx files.txt > site/data/files.txt   # the map reads optional files from this list

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
