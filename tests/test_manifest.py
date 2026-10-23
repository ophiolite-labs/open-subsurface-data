"""E06: retrieval by manifest (charter docs/program/charters/E06-retrieval-by-manifest.md, strategy
E06-retrieval-by-manifest-STRATEGY.md). Every download is served by a local HTTP server on
127.0.0.1; nothing leaves the machine."""

import copy
import hashlib
import json
import threading
from collections import Counter
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from osd import cli, stac
from osd import get as get_mod
from osd import manifest as mf

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "manifest"
NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)
BODIES = {"/a/one.bin": b"first asset\n" * 100, "/a/sub/two.bin": b"second\x00asset" * 50,
          "/b/three.dat": bytes(range(256)) * 4}


class Origin:
    """Serves BODIES; `status[path]` overrides the answer, `corrupt` flips one byte of a path."""

    def __init__(self):
        self.requests: Counter = Counter()
        self.status: dict[str, int] = {}
        self.corrupt: set[str] = set()
        origin = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                origin.requests[self.path] += 1
                code = origin.status.get(self.path, 200 if self.path in BODIES else 404)
                body = BODIES.get(self.path, b"")
                if self.path in origin.corrupt:
                    body = bytes([body[0] ^ 1]) + body[1:]
                self.send_response(code)
                self.send_header("Content-Length", str(len(body) if code == 200 else 0))
                self.end_headers()
                if code == 200:
                    self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()


@pytest.fixture
def origin():
    o = Origin()
    yield o
    o.server.shutdown()


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _record(rid, *, access="anonymous", licence=None, known_issues=None):
    rec = {"id": rid, "title": f"Title of {rid}", "summary": "A dataset.",
           "publisher": {"name": "Acme", "url": "https://acme.example"},
           "origin": {"url": f"https://acme.example/{rid}", "access": access},
           "licence": licence or {"name": "CC BY 4.0", "spdx": "CC-BY-4.0", "redistribution": "allowed",
                                  "attribution": "required"},
           "kinds": ["seismic-3d"], "region": {"country": "NL"}, "listed_by": ["publisher"],
           "added": "2026-10-23", "level": "L2", "checked_at": "2026-10-23T00:00:00Z", "stale": False,
           "blocked_since": None}
    if known_issues:
        rec["known_issues"] = known_issues
    return rec


def catalogue(tmp_path: Path, base: str, records=None, files=None) -> Path:
    """build/catalog/ as `osd build` writes it, through E04's own STAC writer."""
    out, vdir, odir = tmp_path / "catalog", tmp_path / "verification", tmp_path / "outlines"
    for d in (out, vdir, odir):
        d.mkdir(exist_ok=True)
    records = records or [
        _record("acme/alpha", licence={"name": "CC BY-SA 4.0", "spdx": "CC-BY-SA-4.0", "url":
                "https://creativecommons.org/licenses/by-sa/4.0/", "redistribution": "allowed",
                "attribution": "required", "share_alike": True,
                "statement": "Contains Alpha data © Acme 2019, CC BY-SA 4.0"}),
        _record("beta-co/beta", licence={"name": "Beta open licence", "spdx": None, "redistribution": "unknown",
                "attribution": "required", "statement": "Courtesy of Beta Co. and partners"},
                known_issues=["Terms page forbids resale of the data."]),
        _record("gamma/locked", access="registration"),
    ]
    files = files if files is not None else {
        "acme/alpha": [("one.bin", "/a/one.bin"), ("sub/two.bin", "/a/sub/two.bin")],
        "beta-co/beta": [("three.dat", "/b/three.dat")]}
    for rid, fl in files.items():
        (vdir / (rid.replace("/", "__") + ".json")).write_text(json.dumps({"record_id": rid, "files": [
            {"path": p, "url": base + u, "bytes": len(BODIES[u]), "sha256": _sha(BODIES[u])} for p, u in fl]}))
    features = []
    for rec, with_period in ((records[0], True), (records[1], False)):
        rid = rec["id"]
        fc = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {
            "record_id": rid, "kind": "wellbore", "name": "W-1", "approximate": False, "source": "publisher",
            "feature_id": f"{rid}#w-1"}, "geometry": {"type": "Point", "coordinates": [4.5, 54.5]}}]}
        (odir / (rid.replace("/", "__") + ".geojson")).write_text(json.dumps(fc))
        if with_period:
            rec["period"] = {"start": "2019", "end": "2019"}
        features.append({"type": "Feature", "id": f"{rid}#w-1", "properties": fc["features"][0]["properties"],
                         "geometry": fc["features"][0]["geometry"]})
    stac.write_catalog(out, records, vdir, odir)
    (out / "records.json").write_text(json.dumps({"count": len(records), "records": records}))
    (out / "outlines.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return out


def manifest_file(tmp_path, base, ids=("acme/alpha", "beta-co/beta"), **kw) -> Path:
    doc = mf.from_catalog(list(ids), catalogue(tmp_path, base, **kw), now=NOW)
    return mf.write(doc, tmp_path / "manifest.json")


# --- schema and reader ---------------------------------------------------------------------------

def test_manifest_for_two_records_validates(tmp_path):
    doc = mf.from_catalog(["acme/alpha", "beta-co--beta"], catalogue(tmp_path, "https://files.example"), now=NOW)
    assert mf.problems(doc) == []
    assert [e["record_id"] for e in doc["entries"]] == ["acme/alpha", "beta-co/beta"]
    assert doc["selection"] == "collections" and doc["format"] == "osd.manifest/1"
    a = doc["entries"][0]["assets"]["one.bin"]
    assert a["href"] == "https://files.example/a/one.bin"
    assert a["file:checksum"] == "1220" + _sha(BODIES["/a/one.bin"]) and a["file:size"] == 1200
    assert all(e["coverage"] == "sampled" for e in doc["entries"])


def test_v1_fixture_validates():
    """The committed osd.manifest/1 sample: a later schema version must keep it valid."""
    assert mf.problems(json.loads((FIXTURES / "two-records.json").read_text())) == []


def _mutations():
    def drop_licence(d):
        del d["entries"][0]["licence"]

    def bad_checksum(d):
        d["entries"][0]["assets"]["one.bin"]["file:checksum"] = "1220xyz"

    def format_2(d):
        d["format"] = "osd.manifest/2"

    def userinfo(d):
        d["entries"][0]["assets"]["one.bin"]["href"] = "https://me:secret@files.example/a/one.bin"

    def signed_query(d):
        d["entries"][0]["assets"]["one.bin"]["href"] += "?X-Amz-Signature=abc"

    def no_unresolved(d):
        d["entries"][0]["assets"] = {}

    def extra_field(d):
        d["entries"][0]["assets"]["one.bin"]["headers"] = {"Authorization": "Bearer x"}

    def bad_licence(d):
        d["entries"][0]["licence"]["redistribution"] = "maybe"

    def escaping_key(d):
        d["entries"][0]["assets"]["../../etc/x"] = d["entries"][0]["assets"].pop("one.bin")

    return [drop_licence, bad_checksum, format_2, userinfo, signed_query, no_unresolved, extra_field,
            bad_licence, escaping_key]


@pytest.mark.parametrize("mutate", _mutations(), ids=lambda f: f.__name__)
def test_schema_rejects(mutate):
    doc = json.loads((FIXTURES / "two-records.json").read_text())
    assert mf.problems(doc) == []
    bad = copy.deepcopy(doc)
    mutate(bad)
    assert mf.problems(bad)


def test_read_returns_typed_entries():
    m = mf.read(FIXTURES / "two-records.json")
    assert isinstance(m, mf.Manifest) and len(m.entries) == 2
    e = m.entries[0]
    assert isinstance(e.licence, mf.Licence) and e.licence.share_alike is True
    a = {x.key: x for x in e.assets}["one.bin"]
    assert a.sha256 == _sha(BODIES["/a/one.bin"]) and a.size == 1200
    assert m.entries[1].licence.share_alike is None          # not stated stays not stated


def test_read_refuses_invalid_and_non_sha256(tmp_path):
    doc = json.loads((FIXTURES / "two-records.json").read_text())
    doc["entries"][0]["assets"]["one.bin"]["file:checksum"] = "1340" + "ab" * 64   # sha2-512
    p = tmp_path / "m.json"
    p.write_text(json.dumps(doc))
    with pytest.raises(mf.ManifestError, match="not sha2-256"):
        mf.read(p)
    del doc["entries"][0]["licence"]
    p.write_text(json.dumps(doc))
    with pytest.raises(mf.ManifestError, match="licence"):
        mf.read(p)


# --- selection identity, rights ----------------------------------------------------------------

def test_item_selection_carries_no_assets(tmp_path):
    doc = mf.from_catalog(["acme/alpha#w-1"], catalogue(tmp_path, "https://f.example"), now=NOW)
    (e,) = doc["entries"]
    assert doc["selection"] == "items"
    assert e["item_id"] == "acme/alpha#w-1" and e["feature_id"] == "acme/alpha#w-1"
    assert e["assets"] == {} and "Collection acme--alpha" in e["unresolved"]
    assert mf.problems(doc) == []


def test_feature_without_item_is_unresolved(tmp_path):
    doc = mf.from_catalog(["beta-co/beta#w-1"], catalogue(tmp_path, "https://f.example"), now=NOW)
    (e,) = doc["entries"]
    assert e["item_id"] is None and e["collection_id"] == "beta-co--beta"
    assert "no STAC Item" in e["unresolved"] and e["assets"] == {}


def test_mixed_selection_refused(tmp_path):
    with pytest.raises(mf.ManifestError, match="never a mix"):
        mf.from_catalog(["acme/alpha", "acme/alpha#w-1"], catalogue(tmp_path, "https://f.example"))


def test_unknown_id_refused(tmp_path):
    cat = catalogue(tmp_path, "https://f.example")
    with pytest.raises(mf.ManifestError, match="nope/none"):
        mf.from_catalog(["nope/none"], cat)
    with pytest.raises(mf.ManifestError, match="acme/alpha#w-9"):
        mf.from_catalog(["acme/alpha#w-9"], cat)


def test_registration_record_is_a_to_do(tmp_path):
    doc = mf.from_catalog(["gamma/locked"], catalogue(tmp_path, "https://f.example"), now=NOW)
    (e,) = doc["entries"]
    assert e["assets"] == {} and "registration" in e["unresolved"] and "coverage" not in e
    assert e["origin_url"] == "https://acme.example/gamma/locked"


def test_licence_copied_whole(tmp_path):
    cat = catalogue(tmp_path, "https://f.example")
    recs = {r["id"]: r for r in json.loads((cat / "records.json").read_text())["records"]}
    doc = mf.from_catalog(["acme/alpha", "beta-co/beta", "gamma/locked"], cat, now=NOW)
    for e in doc["entries"]:
        assert e["licence"] == recs[e["record_id"]]["licence"]
    assert "share_alike" not in doc["entries"][1]["licence"]


def test_known_issues_and_redistribution_carried(tmp_path):
    doc = mf.from_catalog(["beta-co/beta"], catalogue(tmp_path, "https://f.example"), now=NOW)
    (e,) = doc["entries"]
    assert e["known_issues"] == ["Terms page forbids resale of the data."]
    assert e["licence"]["redistribution"] == "unknown"


def test_cli_manifest_writes_valid_file(tmp_path, capsys):
    cat = catalogue(tmp_path, "https://f.example")
    out = tmp_path / "m.json"
    assert cli.main(["manifest", "acme/alpha", "gamma/locked", "--catalog", str(cat), "-o", str(out)]) == 0
    assert "2 collections, 2 assets, 1 to-do" in capsys.readouterr().out
    assert len(mf.read(out).entries) == 2
    assert cli.main(["manifest", "acme/alpha", "acme/alpha#w-1", "--catalog", str(cat), "-o", str(out)]) == 1


# --- osd get ------------------------------------------------------------------------------------

def _by_key(outcomes):
    return {f"{r.collection_id}/{r.key}": r.outcome for r in outcomes}


def _files(dest):
    return {"acme--alpha/one.bin": BODIES["/a/one.bin"], "acme--alpha/sub/two.bin": BODIES["/a/sub/two.bin"],
            "beta-co--beta/three.dat": BODIES["/b/three.dat"]}


def test_get_three_assets_verified(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base))
    dest = tmp_path / "fresh"
    out = get_mod.get(m, dest)
    assert sorted(r.outcome for r in out) == ["verified"] * 3 and not get_mod.failed(out)
    for rel, body in _files(dest).items():
        assert (dest / rel).read_bytes() == body
    assert sum(origin.requests.values()) == 3
    assert not list(dest.rglob("*.partial"))


def test_get_corrupt_byte_is_mismatch(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base))
    dest = tmp_path / "fresh"
    origin.corrupt.add("/a/sub/two.bin")
    out = get_mod.get(m, dest)
    assert get_mod.failed(out)
    assert _by_key(out) == {"acme--alpha/one.bin": "verified", "acme--alpha/sub/two.bin": "mismatch",
                            "beta-co--beta/three.dat": "not-attempted"}
    assert (dest / "acme--alpha/one.bin").read_bytes() == BODIES["/a/one.bin"]
    assert not (dest / "acme--alpha/sub/two.bin").exists()          # bad bytes never land
    assert not (dest / "beta-co--beta/three.dat").exists() and origin.requests["/b/three.dat"] == 0
    assert not list(dest.rglob("*.partial"))


def test_mismatch_leaves_existing_file_untouched(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base))
    dest = tmp_path / "d"
    old = dest / "acme--alpha/sub/two.bin"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"something the person had")
    origin.corrupt.add("/a/sub/two.bin")
    out = get_mod.get(m, dest)
    assert _by_key(out)["acme--alpha/sub/two.bin"] == "mismatch"
    assert old.read_bytes() == b"something the person had"


def test_get_without_checksum_reports_fetched(tmp_path, origin):
    doc = json.loads(manifest_file(tmp_path, origin.base).read_text())
    for e in doc["entries"]:
        for a in e["assets"].values():
            del a["file:checksum"]
    p = mf.write(doc, tmp_path / "nochecksum.json")
    out = get_mod.get(mf.read(p), tmp_path / "d")
    assert sorted(r.outcome for r in out) == ["fetched"] * 3


def test_get_size_mismatch(tmp_path, origin):
    doc = json.loads(manifest_file(tmp_path, origin.base).read_text())
    a = doc["entries"][0]["assets"]["one.bin"]
    del a["file:checksum"]
    a["file:size"] += 1
    out = get_mod.get(mf.read(mf.write(doc, tmp_path / "m2.json")), tmp_path / "d")
    assert _by_key(out)["acme--alpha/one.bin"] == "mismatch"
    assert not (tmp_path / "d/acme--alpha/one.bin").exists()


def test_rerun_fetches_only_missing_asset(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base))
    dest = tmp_path / "d"
    origin.status["/a/sub/two.bin"] = 503
    first = get_mod.get(m, dest)
    assert _by_key(first)["acme--alpha/sub/two.bin"] == "origin-dead"
    assert _by_key(first)["beta-co--beta/three.dat"] == "verified"   # a dead origin does not stop the run
    assert get_mod.failed(first)
    origin.status.clear()
    origin.requests.clear()
    second = get_mod.get(m, dest)
    assert sorted(r.outcome for r in second) == ["verified"] * 3
    assert dict(origin.requests) == {"/a/sub/two.bin": 1}
    assert [r.requested for r in second] == [False, True, False]


def test_rerun_repairs_truncated_and_corrupt_files(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base))
    dest = tmp_path / "d"
    get_mod.get(m, dest)
    truncated, corrupt = dest / "acme--alpha/one.bin", dest / "beta-co--beta/three.dat"
    truncated.write_bytes(BODIES["/a/one.bin"][:-7])
    corrupt.write_bytes(b"X" + BODIES["/b/three.dat"][1:])
    origin.requests.clear()
    out = get_mod.get(m, dest)
    assert sorted(r.outcome for r in out) == ["verified"] * 3
    assert dict(origin.requests) == {"/a/one.bin": 1, "/b/three.dat": 1}
    assert truncated.read_bytes() == BODIES["/a/one.bin"] and corrupt.read_bytes() == BODIES["/b/three.dat"]


@pytest.mark.parametrize("key", ["../outside.bin", "sub/../../outside.bin", "/abs.bin"])
def test_get_refuses_escaping_paths(tmp_path, key):
    """The schema refuses these keys; the downloader refuses them again on its own."""
    m = mf.read(FIXTURES / "two-records.json")
    e = m.entries[0]
    bad = mf.Asset(key=key, href="https://files.example/x", size=None, sha256=None)
    m2 = mf.Manifest(m.created, m.catalog_url, m.selection,
                     (mf.Entry(**{**e.__dict__, "assets": (bad,)}),))
    with pytest.raises(mf.ManifestError, match="leaves"):
        get_mod.get(m2, tmp_path / "d", opener=lambda url: pytest.fail("requested before refusing"))
    assert not (tmp_path / "outside.bin").exists()


def test_get_refuses_duplicate_targets(tmp_path):
    m = mf.read(FIXTURES / "two-records.json")
    m2 = mf.Manifest(m.created, m.catalog_url, m.selection, (m.entries[0], m.entries[0]))
    with pytest.raises(mf.ManifestError, match="both be written"):
        get_mod.get(m2, tmp_path / "d", opener=lambda url: pytest.fail("requested before refusing"))


def test_get_401_needs_sign_in_404_origin_dead(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base))
    origin.status.update({"/a/one.bin": 401, "/a/sub/two.bin": 403, "/b/three.dat": 404})
    out = get_mod.get(m, tmp_path / "d")
    assert _by_key(out) == {"acme--alpha/one.bin": "needs-sign-in", "acme--alpha/sub/two.bin": "needs-sign-in",
                            "beta-co--beta/three.dat": "origin-dead"}
    assert get_mod.failed(out)


# --- rights -------------------------------------------------------------------------------------

def test_attribution_statements_verbatim(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base))
    get_mod.get(m, tmp_path / "d")
    text = (tmp_path / "d" / "ATTRIBUTION.md").read_text()
    assert "> Contains Alpha data © Acme 2019, CC BY-SA 4.0" in text
    assert "> Courtesy of Beta Co. and partners" in text
    assert "Share-alike: derived work must carry CC-BY-SA-4.0" in text
    assert "(no SPDX identifier)" in text and "Redistribution: unknown" in text
    assert "Known issue: Terms page forbids resale of the data." in text
    assert text.count("Share-alike: not stated") == 1


def test_attribution_missing_statement_invents_nothing(tmp_path, origin):
    m = mf.read(manifest_file(tmp_path, origin.base, ids=("gamma/locked",)))
    out = get_mod.get(m, tmp_path / "d")
    assert out == [] and not get_mod.failed(out)
    text = (tmp_path / "d" / "ATTRIBUTION.md").read_text()
    assert "Statement: none stated by the publisher in the record" in text
    assert ">" not in text.split("## ", 1)[1]                        # no quoted statement at all
    assert "Title of gamma/locked" in text and "(CC-BY-4.0)" in text


def test_cli_get_summary_names_share_alike(tmp_path, origin, capsys):
    p = manifest_file(tmp_path, origin.base, ids=("acme/alpha", "beta-co/beta", "gamma/locked"))
    assert cli.main(["get", str(p), "--dest", str(tmp_path / "d")]) == 0
    out = capsys.readouterr().out
    assert "1 item requires derived work to carry CC-BY-SA-4.0" in out
    assert "3 verified" in out and "to-do         gamma--locked" in out
    assert "the files the verifier sampled, not the whole dataset" in out
    origin.corrupt.add("/b/three.dat")
    (tmp_path / "d/beta-co--beta/three.dat").unlink()
    assert cli.main(["get", str(p), "--dest", str(tmp_path / "d")]) == 1
