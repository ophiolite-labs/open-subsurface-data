# One target per station. CI runs exactly `make check`.
.PHONY: check test lint validate build verify site serve clean

check: lint test validate build          ## the required CI check (offline, < 2 min)

lint:
	uv run ruff check src tests

test:
	uv run pytest -q

validate:                                ## every record and outline against its schema
	uv run osd validate

build:                                   ## build/catalog/*.json + site/data/ from records + outlines
	uv run osd build
	mkdir -p site/data && cp build/catalog/*.json build/catalog/*.geojson site/data/

verify:                                  ## network: reach origins, record levels (not part of `check`)
	uv run osd verify

site: build                              ## serve the map locally
	python3 -m http.server --directory site 8765

clean:
	rm -rf build site/data
