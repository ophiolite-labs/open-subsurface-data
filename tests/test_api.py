"""E49 slice 1: `osd.get(id)` from Python (charter docs/program/charters/E49-the-python-file.md,
strategy E49-the-python-file-STRATEGY.md). Offline: an injected opener serves the fixture catalogue
(tests/fixtures/api/catalog/) and the asset bodies (transport.json); acceptance 4 uses a server on
127.0.0.1 so `osd get` and `osd.get` both go through `http_open`."""

import json
import shutil
import subprocess
import sys
import threading
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import osd
from osd import api, cli
from osd import get as get_mod
from osd.verify import FetchError

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "tests" / "fixtures" / "api"
CATALOG = "https://catalog.fixture.invalid/data/"


class Transport:
    """url -> bytes from the fixture; counts every request; `corrupt` flips the first byte of a URL."""

    def __init__(self):
        self.bodies = {u: t.encode() for u, t in json.loads((FX / "transport.json").read_text()).items()}
        for p in (FX / "catalog").rglob("*.json"):
            self.bodies[CATALOG + p.relative_to(FX / "catalog").as_posix()] = p.read_bytes()
        self.requests: Counter = Counter()
        self.corrupt: set[str] = set()

    def __call__(self, url: str):
        self.requests[url] += 1
        if url not in self.bodies:
            raise FetchError(url, 404)
        b = self.bodies[url]
        return [bytes([b[0] ^ 1]) + b[1:] if url in self.corrupt else b]

    def assets(self) -> int:
        return sum(n for u, n in self.requests.items() if not u.startswith(CATALOG))


@pytest.fixture
def t(monkeypatch):
    monkeypatch.setattr(api, "_cache", {})
    return Transport()


def test_get_from_mirror_checked_then_idempotent(tmp_path, t):
    """Acceptance 1."""
    d = osd.get("fx/mirrored", dest=tmp_path, catalog=CATALOG, opener=t)
    assert [(f.key, f.source, f.checked) for f in d.files] == [
        ("well/A-1.las", "mirror", "verified"), ("README", "mirror", "verified")]
    assert all(u.startswith(("https://mirror.", CATALOG)) for u in t.requests), "mirror first, origin untouched"
    assert (tmp_path / "fx--mirrored" / "README").read_text() == "fixture readme\n"
    assert d.files[1].path == tmp_path / "fx--mirrored" / "README" and d.files[1].size == 15
    assert d.todo == () and d.licence.spdx == "CC-BY-4.0" and "Contains fixture data." in d.attribution
    t.requests.clear()
    again = osd.get("fx/mirrored", dest=tmp_path, catalog=CATALOG, opener=t)
    assert sum(t.requests.values()) == 0, "second call: catalogue from memory, files rehashed on disk"
    assert {f.source for f in again.files} == {"disk"} and {f.checked for f in again.files} == {"verified"}


def test_registration_is_todo_and_requests_nothing(tmp_path, t):
    """Acceptance 2: no files, the to-do names the address; only the catalogue was read."""
    d = osd.get("fx/signin", dest=tmp_path, catalog=CATALOG, opener=t)
    assert d.files == () and t.assets() == 0
    assert d.todo == (("access registration: sign in or ask at the origin page; no file address is published "
                      "to us -> https://origin.fixture.invalid/signin/"),)
    assert "to-do" in str(d) and "https://origin.fixture.invalid/signin/" in str(d)


def test_mismatch_raises_with_both_digests(tmp_path, t):
    """Acceptance 3: a corrupted byte on mirror and origin raises; nothing of the file is left."""
    for u in t.bodies:
        if u.endswith("README"):
            t.corrupt.add(u)
    with pytest.raises(api.ChecksumMismatch) as e:
        osd.get("fx/mirrored", dest=tmp_path, catalog=CATALOG, opener=t)
    assert e.value.key == "fx--mirrored/README"
    got, want = e.value.detail.split(", the catalogue states ")
    assert len(got.removeprefix("sha256 ")) == 64 and len(want) == 64 and got[7:] != want
    assert not (tmp_path / "fx--mirrored" / "README").exists()
    assert not list(tmp_path.rglob("*.partial"))


def test_mirror_mismatch_falls_back_to_publisher(tmp_path, t):
    t.corrupt.update(u for u in t.bodies if u.startswith("https://mirror.") and u.endswith("README"))
    d = osd.get("fx/mirrored", dest=tmp_path, catalog=CATALOG, opener=t)
    assert {f.key: f.source for f in d.files} == {"well/A-1.las": "mirror", "README": "publisher"}


def test_unreachable_file_is_todo_not_raised(tmp_path, t):
    del t.bodies["https://origin.fixture.invalid/publisher/grid.csv"]
    d = osd.get("fx/publisher", dest=tmp_path, catalog=CATALOG, opener=t)
    assert d.files == () and d.todo[0].startswith("grid.csv: origin-dead: ")


@pytest.mark.parametrize("bad", ["fx/none", "../fx/mirrored", "fx/mirrored#1", "stac/catalog.json", ""])
def test_unknown_or_feature_id_refused_before_request(tmp_path, t, bad):
    """F13: caller text never reaches a URL; only records.json is read."""
    with pytest.raises(api.DatasetError):
        osd.get(bad, dest=tmp_path, catalog=CATALOG, opener=t)
    assert set(t.requests) <= {CATALOG + "records.json"} and not list(tmp_path.iterdir())


def test_catalogue_url_built_from_records_only(tmp_path, t):
    """F4: exactly the two catalogue files, the collection addressed by its computed id; a collection id works."""
    osd.get("fx--publisher", dest=tmp_path, catalog=CATALOG.rstrip("/"), opener=t)
    assert sorted(u for u in t.requests if u.startswith(CATALOG)) == [
        CATALOG + "records.json", CATALOG + "stac/fx--publisher/collection.json"]


def test_catalogue_unreachable_names_the_url(tmp_path, t):
    with pytest.raises(api.DatasetError, match="https://nowhere.invalid/data/records.json"):
        osd.get("fx/mirrored", dest=tmp_path, catalog="https://nowhere.invalid/data", opener=t)


def test_local_catalogue_directory(tmp_path, t):
    d = osd.get("fx/publisher", dest=tmp_path, catalog=FX / "catalog", opener=t)
    assert [f.checked for f in d.files] == ["verified"] and not any(u.startswith(CATALOG) for u in t.requests)


@pytest.mark.parametrize("area", ["F03", ""])
def test_area_refused_before_request(tmp_path, t, area):
    """F8 (OSD-D36): any area is refused with the sentence, nothing requested."""
    with pytest.raises(ValueError, match="^this dataset cannot be narrowed by area yet$"):
        osd.get("fx/mirrored", dest=tmp_path, area=area, catalog=CATALOG, opener=t)
    assert not t.requests


def test_default_dest_is_per_dataset(tmp_path, t, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = osd.get("fx/publisher", catalog=CATALOG, opener=t)
    assert d.path == Path("osd-data/fx/publisher")
    assert (tmp_path / "osd-data/fx/publisher/fx--publisher/grid.csv").is_file()
    assert (tmp_path / "osd-data/fx/publisher/ATTRIBUTION.md").is_file()


def test_osd_get_module_still_importable():
    """`osd.get` is callable and is still the E06 module for every existing import."""
    from osd import get as m
    assert m is get_mod and callable(osd.get) and m.summary and cli.get_mod is m


def test_import_osd_is_offline_and_reader_free():
    """F16, F17: importing osd opens no socket and loads no reader library."""
    code = ("import socket, sys\n"
            "def no(*a, **k): raise SystemExit('network at import')\n"
            "socket.socket.connect = no; socket.create_connection = no\n"
            "import osd, osd.cli, osd.script\n"
            "bad = [m for m in ('lasio', 'segyio', 'pandas') if m in sys.modules]\n"
            "sys.exit(f'loaded {bad}' if bad else 0)\n")
    r = subprocess.run([sys.executable, "-c", code], check=False, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout


# --- acceptance 4: one code path with `osd get <manifest>` ---------------------------------------------

def _serve(root: Path):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Quiet, directory=str(root)))
    threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _tree(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


def test_api_and_cli_leave_identical_trees(tmp_path, monkeypatch, capsys):
    """Acceptance 4 (F11): byte-identical trees, the same summary, and both through `get.get`."""
    site = tmp_path / "site"
    shutil.copytree(FX / "catalog", site / "data")
    for u, body in json.loads((FX / "transport.json").read_text()).items():
        p = site / u.split("://", 1)[1]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    srv, base = _serve(site)
    try:
        for p in (site / "data" / "stac").rglob("collection.json"):
            p.write_text(p.read_text().replace("https://", base))
        monkeypatch.setattr(api, "_cache", {})
        seen, real = [], get_mod.get

        def spy(m, dest, *a, **k):
            seen.append(m.entries)
            return real(m, dest, *a, **k)

        monkeypatch.setattr(get_mod, "get", spy)
        ds = osd.get("fx/mirrored", dest=tmp_path / "api", catalog=base + "data/")
        man = tmp_path / "m.json"
        assert cli.main(["manifest", "fx/mirrored", "--catalog", str(site / "data"), "-o", str(man)]) == 0
        capsys.readouterr()
        assert cli.main(["get", str(man), "--dest", str(tmp_path / "cli")]) == 0
        printed = capsys.readouterr().out.splitlines()
    finally:
        srv.shutdown()
    assert len(seen) == 2 and seen[0] == seen[1], "both paths hand the same manifest entries to get.get"
    assert _tree(tmp_path / "api") == _tree(tmp_path / "cli") and len(_tree(tmp_path / "api")) == 3
    assert str(ds).splitlines()[1:] == printed[:-1] and printed[-1].startswith("attribution -> ")
