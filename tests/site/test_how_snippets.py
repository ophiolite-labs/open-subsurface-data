"""how.html's three cards run as written, against a local server instead of the live site.

Offline: the catalogue is built into a temporary directory and served on 127.0.0.1.
"""

import html
import json
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIVE = "https://opensubsurfacedata.org/"


def snippets():
    page = (ROOT / "site" / "how.html").read_text()
    found = re.findall(r'<pre data-snippet="(\w+)">(.*?)</pre>', page, re.DOTALL)
    return [(kind, html.unescape(body)) for kind, body in found]


@pytest.fixture(scope="module")
def site(full_build):
    root = full_build.parent   # the session's real build is <root>/data, as `make build` stages it (E32)
    for f in ("index.html", "how.html", "app.js", "style.css"):
        shutil.copy(ROOT / "site" / f, root / f)
    handler = partial(type("Quiet", (SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}),
                      directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()


def test_how_page_has_the_three_cards():
    kinds = [k for k, _ in snippets()]
    assert kinds == ["url", "python", "python"]
    assert all(LIVE in body for _, body in snippets())


@pytest.mark.parametrize("i", range(3))
def test_snippet_runs_as_written(site, i):
    kind, body = snippets()[i]
    body = body.replace(LIVE, site)
    if kind == "url":
        fc = json.load(urllib.request.urlopen(body.strip()))
        assert fc["type"] == "FeatureCollection" and fc["features"]
        assert all("record_id" in f["properties"] for f in fc["features"])
    else:
        run = subprocess.run([sys.executable, "-c", body], check=False, capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, run.stderr
        assert run.stdout.strip() and not run.stdout.startswith("0 ")
