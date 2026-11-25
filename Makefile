# One target per station. CI runs exactly `make check`.
.PHONY: check check-full test test-real-build test-rest lint validate build verify site serve clean site-deps site-test shot

check:                                   ## the required CI check (offline, < 2 min)
	$(MAKE) lint
	$(MAKE) -j4 --output-sync=target test validate build   # side by side (E36): the build's tiling is the long one

lint:
	uv run ruff check src tests

# The test files that read the session's one real build (conftest `full_build`, found by name) and the rest,
# side by side: one real build in the first process, none in the second (E46 slice 2).
REAL_BUILD_TESTS = $(shell grep -rl --include='test_*.py' full_build tests | sort)

test: test-real-build test-rest

test-real-build:
	uv run pytest -q --durations=10 $(REAL_BUILD_TESTS)   # slowest ten printed: the gate's time is measured (E46 slice 2)

test-rest:
	uv run pytest -q --durations=10 $(addprefix --ignore=,$(REAL_BUILD_TESTS))   # slowest ten printed: the gate's time is measured (E46 slice 2)

validate:                                ## every record and outline against its schema
	uv run osd validate

build:                                   ## build/catalog/*.json, outlines.pmtiles (tippecanoe) + site/data/
	uv run osd build
	mkdir -p site/data && rm -rf site/data/stac site/data/*.pmtiles && cp -R build/catalog/. site/data/   # stac/ is a tree; tiles only when tippecanoe ran (E15)
	ls site/data | grep -vx files.txt > site/data/files.txt   # the map reads optional files from this list

check-full: build                        ## the whole STAC tree, every Item (OSD-D18), the full tile comparison (E36); verify workflow on main, not the gate
	uv run pytest -q -m full
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

shot: build                              ## desktop and phone screenshots into build/shots/ (the shop's into build/shots/shop/)
	mkdir -p build/shots
	node tools/shot.mjs build/shots
	node tools/shot.mjs build/shots/shop shop

clean:
	rm -rf build site/data
