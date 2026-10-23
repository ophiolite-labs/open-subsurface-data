"""E07: mirror store and custody, slice 1 (charter docs/program/charters/E07-mirror-store-and-custody.md,
strategy E07-mirror-store-and-custody-STRATEGY.md). Local-directory transport only; the origin and the
mirror are fake openers keyed by URL, so nothing leaves the machine."""

import copy
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from osd import custody, mirror, paths, stac
from osd import get as get_mod
from osd import manifest as mf
from osd.build import build
from osd.records import load_record, load_records
from osd.verify import ByteBudget, Fetched, FetchError, load_samples, verify_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "mirror"
NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)
ORIGIN = "https://origin.test/"
MIRROR = "https://mirror.test/"
FILES = {"survey/a.sgy": b"alpha" * 1000, "survey/b.las": b"bravo" * 333, "survey/c.csv": b"x,y\n1,2\n" * 50}
RULE = ["survey/*"]
GB = 10**9


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Net:
    """Origin at ORIGIN (FILES, a JSON listing, a licence page) and the mirror at MIRROR (the store's
    directory). `requests` counts every URL; `dead` hosts answer nothing; `corrupt` flips a byte;
    `interrupt[url]` raises after the first chunk, once."""

    def __init__(self, store_root: Path | None = None, files=FILES):
        self.files, self.store_root = dict(files), store_root
        self.requests: Counter = Counter()
        self.dead: set[str] = set()
        self.corrupt: set[str] = set()
        self.interrupt: set[str] = set()

    def body(self, url: str) -> bytes:
        if url == ORIGIN + "index.json":
            return json.dumps({"files": [{"path": p, "href": p} for p in [*self.files, "README.txt"]]}).encode()
        if url == ORIGIN + "licence.html":
            return b"<html><body><p>Licence text.</p></body></html>"
        if url.startswith(ORIGIN) and url[len(ORIGIN):] in self.files:
            return self.files[url[len(ORIGIN):]]
        if url.startswith(MIRROR) and self.store_root is not None:
            p = self.store_root / url[len(MIRROR):]
            if p.is_file():
                return p.read_bytes()
        raise FetchError(url, 404)

    def __call__(self, url: str):
        self.requests[url] += 1
        if any(url.startswith(h) for h in self.dead):
            raise FetchError(url, 0, "connection")
        data = self.body(url)
        if url in self.corrupt:
            data = bytes([data[0] ^ 1]) + data[1:]
        chunks = [data[i:i + 1000] for i in range(0, len(data), 1000)] or [b""]
        if url in self.interrupt:
            self.interrupt.discard(url)

            def broken():
                yield chunks[0]
                raise ConnectionResetError("interrupted")
            return broken()
        return iter(chunks)

    def origin_requests(self) -> int:
        return sum(n for u, n in self.requests.items() if u.startswith(ORIGIN) and u[len(ORIGIN):] in self.files)


def record(rid="acme/demo", redistribution="allowed", size=None) -> dict:
    rec = {"id": rid, "title": f"Title of {rid}", "summary": "A dataset.",
           "publisher": {"name": "Acme", "url": "https://acme.example"},
           "origin": {"url": f"https://acme.example/{rid}", "access": "anonymous",
                      "manifest_url": ORIGIN + "index.json"},
           "licence": {"name": "CC BY 4.0", "spdx": "CC-BY-4.0", "url": ORIGIN + "licence.html",
                       "redistribution": redistribution, "attribution": "required",
                       "statement": "Contains Acme data"},
           "kinds": ["seismic-3d"], "region": {"country": "NL", "bbox": [4, 54, 5, 55]},
           "listed_by": ["community"], "added": "2026-10-23"}
    if size is not None:
        rec["size"] = {"bytes_estimate": size}
    return rec


def verification(rid="acme/demo", files=None, *, level="L2", reach="ok", rule=RULE, selected=None) -> dict:
    files = FILES if files is None else files
    out = [{"path": p, "url": ORIGIN + p, "bytes": len(b), "sha256": _sha(b)} for p, b in files.items()]
    return {"record_id": rid, "checked_at": "2026-10-23T11:00:00+00:00", "tool_version": "0.1.0",
            "level": level, "checks": [], "origin": {"reachability": reach},
            "licence_text_sha256": "cd" * 32, "files": out,
            "inventory": {"rule": list(rule), "listed": len(files) + 1,
                          "selected": list(files) if selected is None else selected, "coverage": "complete"}}


def store(tmp_path) -> mirror.LocalDirectory:
    return mirror.LocalDirectory(tmp_path / "store", MIRROR)


# --- the verifier writes the inventory (verification/3) -----------------------------------------

def test_verifier_writes_complete_inventory(tmp_path):
    net = Net()
    v = verify_record(record(), lambda u: Fetched(200, u, "text/html", 3), None, now=NOW, opener=net,
                      sample=["*.sgy"], mirror_rule=RULE)
    assert v["inventory"] == {"rule": RULE, "listed": 4, "selected": list(FILES), "coverage": "complete"}
    assert {f["path"]: f["sha256"] for f in v["files"]} == {p: _sha(b) for p, b in FILES.items()}
    assert net.requests[ORIGIN + "survey/a.sgy"] == 1   # the sampled file is not hashed twice
    Draft202012Validator(json.loads((paths.SCHEMA_DIR / "verification.schema.json").read_text())).validate(v)


def test_inventory_counts_against_the_run_budget():
    v = verify_record(record(), lambda u: Fetched(200, u, "text/html", 3), None, now=NOW, opener=Net(),
                      sample=["*.csv"], mirror_rule=RULE, budget=ByteBudget(len(FILES["survey/c.csv"]) + 6000))
    assert v["inventory"]["coverage"] == "partial"
    assert not mirror.eligibility(record(), v, RULE).eligible


def test_no_rule_no_inventory():
    v = verify_record(record(), lambda u: Fetched(200, u, "text/html", 3), None, now=NOW, opener=Net(),
                      sample=["*.sgy"])
    assert "inventory" not in v


def test_mirror_rules_name_real_records():
    recs, rules = load_records(), mirror.load_rules()
    assert set(rules) == {"opm/norne"}                      # ruled 23 Oct: Norne only in slice 1
    for rid, globs in rules.items():
        assert recs[rid]["origin"].get("manifest_url") and recs[rid]["licence"]["redistribution"] == "allowed"
        assert globs and all(isinstance(g, str) and g for g in globs)
    assert "mirror" not in load_samples()                   # the verifier's sample policy is untouched


# --- eligibility --------------------------------------------------------------------------------

NORNE_LISTING = {"norne/NORNE_ATW2013.DATA": b"d" * 12129, "norne/Norne_model_for_atw2013.pdf": b"p" * 1320,
                 "norne/README": b"r" * 687, "norne/plothelper.sh": b"s" * 5893, "norne/plotwells.sh": b"w" * 3270}


def test_eligible_norne_complete_inventory():
    rec = load_record(paths.RECORDS_DIR / "opm" / "norne.yaml")
    rule = mirror.load_rules()["opm/norne"]
    v = verification("opm/norne", NORNE_LISTING, rule=rule)
    e = mirror.eligibility(rec, v, rule)
    assert e.eligible, e.reasons
    assert len(e.files) == 5 and e.bytes == sum(len(b) for b in NORNE_LISTING.values())


@pytest.mark.parametrize("rights", ["unknown", "restricted", "forbidden"])
def test_not_eligible_rights(rights):
    e = mirror.eligibility(record(redistribution=rights), verification(), RULE)
    assert not e.eligible and any("redistribution" in r for r in e.reasons)


def test_not_eligible_volve_unknown():
    rec = load_record(paths.RECORDS_DIR / "equinor" / "volve.yaml")
    e = mirror.eligibility(rec, verification("equinor/volve"), RULE)
    assert not e.eligible and e.reasons == ("redistribution unknown, not allowed (OSD-D6)",)


@pytest.mark.parametrize("where", ["inventory", "declared"])
def test_not_eligible_over_cap(where):
    v = verification()
    rec = record()
    if where == "inventory":
        v["files"][0]["bytes"] = 25 * GB
    else:
        rec = record(size=25 * GB)
    e = mirror.eligibility(rec, v, RULE)
    assert not e.eligible and any("20 GB" in r for r in e.reasons), e.reasons


def test_not_eligible_one_unhashed_entry():
    v = verification()
    v["files"] = v["files"][:2]
    e = mirror.eligibility(record(), v, RULE)
    assert not e.eligible and e.reasons == ("survey/c.csv: selected by the rule, not hashed",)


def test_not_eligible_missing_size():
    v = verification()
    del v["files"][1]["bytes"]
    e = mirror.eligibility(record(), v, RULE)
    assert not e.eligible and e.reasons == ("survey/b.las: no bytes",)


def test_not_eligible_missing_checksum():
    v = verification()
    v["files"][1]["sha256"] = None
    e = mirror.eligibility(record(), v, RULE)
    assert not e.eligible and e.reasons == ("survey/b.las: no sha256",)


def test_not_eligible_blocked_origin():
    e = mirror.eligibility(record(), verification(reach="blocked"), RULE)
    assert not e.eligible and e.reasons == ("origin blocked",)


def test_not_eligible_below_l2():
    e = mirror.eligibility(record(), verification(level="L1"), RULE)
    assert not e.eligible and e.reasons == ("level L1, L2 required",)


def test_not_eligible_without_inventory_or_rule():
    v = verification()
    assert mirror.eligibility(record(), v, None).reasons == ("no mirror: rule in verifier/samples.yaml",)
    assert mirror.eligibility(record(), v, ["*.sgy"]).reasons == ("inventory made under another mirror rule",)
    del v["inventory"]
    assert mirror.eligibility(record(), v, RULE).reasons == ("no inventory in the latest verification",)
    assert mirror.eligibility(record(), None, RULE).reasons == (
        "level L0, L2 required", "no inventory in the latest verification")


# --- publication on the local transport ---------------------------------------------------------

def test_mirror_three_files(tmp_path):
    s, net = store(tmp_path), Net()
    out = mirror.put(record(), verification(), RULE, s, net, now=NOW)
    assert [c.outcome for c in out] == ["published"] * 3
    docs = [s.get_json(k) for k in s.keys("custody/")]
    assert {(d["path"], d["sha256"], d["bytes"]) for d in docs} == {(p, _sha(b), len(b)) for p, b in FILES.items()}
    for d in docs:
        assert custody.problems(d, d["sha256"] + ".json", s.size(d["key"])) == []
        assert (s.root / d["key"]).read_bytes() == FILES[d["path"]]
        assert d["href"] == MIRROR + d["key"] and d["origin_href"] == ORIGIN + d["path"]
    assert all(net.requests[ORIGIN + p] == 1 for p in FILES) and net.origin_requests() == 3
    assert s.keys("staging/") == []


def test_corrupted_stream_leaves_no_public_key(tmp_path):
    s, net = store(tmp_path), Net()
    net.corrupt.add(ORIGIN + "survey/b.las")
    out = {c.path: c.outcome for c in mirror.put(record(), verification(), RULE, s, net, now=NOW)}
    assert out["survey/b.las"] == "mismatch"
    sha = _sha(FILES["survey/b.las"])
    assert not [k for k in s.keys("") if sha in k]          # no staging, no public object, no custody


def test_rerun_after_interruption(tmp_path):
    s, net = store(tmp_path), Net()
    net.interrupt.add(ORIGIN + "survey/b.las")
    with pytest.raises(ConnectionResetError):
        mirror.put(record(), verification(), RULE, s, net, now=NOW)
    assert s.keys("mirror/") == [mirror.keys_for("acme/demo", _sha(FILES["survey/a.sgy"]), "survey/a.sgy").public]
    out = mirror.put(record(), verification(), RULE, s, net, now=NOW)
    assert [c.outcome for c in out] == ["present", "published", "published"]
    assert net.requests[ORIGIN + "survey/a.sgy"] == 1        # completed file not fetched again
    assert net.requests[ORIGIN + "survey/b.las"] == 2        # the interrupted one is
    assert len(s.keys("mirror/")) == 3 and s.keys("staging/") == []


def test_rerun_after_crash_before_move(tmp_path):
    s, net = store(tmp_path), Net()

    class Crash(Exception):
        pass

    real = s.move
    s.move = lambda a, b: (_ for _ in ()).throw(Crash())
    with pytest.raises(Crash):
        mirror.put(record(), verification(), RULE, s, net, now=NOW)
    assert s.keys("mirror/") == [] and len(s.keys("staging/")) == 1
    s.move = real
    out = mirror.put(record(), verification(), RULE, s, net, now=NOW)
    assert out[0].outcome == "published" and "staging" in out[0].detail
    assert net.requests[ORIGIN + "survey/a.sgy"] == 1        # finished from staging, no second fetch
    assert len(s.keys("mirror/")) == 3


def test_mirror_refuses_ineligible(tmp_path):
    s, net = store(tmp_path), Net()
    with pytest.raises(mirror.NotEligible, match="redistribution unknown"):
        mirror.put(record(redistribution="unknown"), verification(), RULE, s, net, now=NOW)
    assert net.requests == Counter() and s.keys("") == []


# --- catalogue, manifest and osd get ------------------------------------------------------------

def catalogue(tmp_path: Path, s: mirror.LocalDirectory, rec=None, v=None) -> Path:
    rec, v = rec or record(), v or verification()
    out, vdir, odir = tmp_path / "catalog", tmp_path / "verification", tmp_path / "outlines"
    for d in (out, vdir, odir):
        d.mkdir(exist_ok=True)
    (vdir / "acme__demo.json").write_text(json.dumps(v))
    joined = dict(rec, level=v["level"], checked_at=v["checked_at"], stale=False, blocked_since=None)
    stac.write_catalog(out, [joined], vdir, odir, mirror_index=mirror.public_index(s.root / "custody"))
    (out / "records.json").write_text(json.dumps({"count": 1, "records": [joined]}))
    return out


def mirrored(tmp_path):
    s = store(tmp_path)
    net = Net(s.root)
    mirror.put(record(), verification(), RULE, s, net, now=NOW)
    doc = mf.from_catalog(["acme/demo"], catalogue(tmp_path, s), now=NOW)
    m = mf.read(mf.write(doc, tmp_path / "manifest.json"))
    net.requests.clear()
    return s, net, doc, m


def test_stac_alternate_validates_offline(tmp_path, monkeypatch):
    s = store(tmp_path)
    mirror.put(record(), verification(), RULE, s, Net(), now=NOW)
    col_path = catalogue(tmp_path, s) / "stac" / "acme--demo" / "collection.json"
    col = json.loads(col_path.read_text())
    assert stac.ALTERNATE_EXTENSION in col["stac_extensions"]
    for k, a in col["assets"].items():
        assert a["alternate"]["mirror"]["href"] == MIRROR + mirror.keys_for("acme/demo", _sha(FILES[k]), k).public
        assert a["file:checksum"] == "1220" + _sha(FILES[k])       # one logical asset, one checksum
    monkeypatch.setattr("stac_validator.utilities.urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("net")))
    ok, msgs = stac.validate(col_path, recursive=False)
    assert ok, msgs


def test_manifest_v2_alternates(tmp_path):
    _, _, doc, m = mirrored(tmp_path)
    assert doc["format"] == "osd.manifest/2" and mf.problems(doc) == []
    a = m.entries[0].assets[0]
    assert a.alternates == (("mirror", MIRROR + mirror.keys_for("acme/demo", a.sha256, a.key).public),)


def test_manifest_v1_still_reads():
    m = mf.read(ROOT / "tests" / "fixtures" / "manifest" / "two-records.json")
    assert m.entries and all(a.alternates == () for e in m.entries for a in e.assets)


def test_manifest_without_alternates_stays_v1(tmp_path):
    doc = mf.from_catalog(["acme/demo"], catalogue(tmp_path, store(tmp_path)), now=NOW)
    assert doc["format"] == "osd.manifest/1" and mf.problems(doc) == []


def test_manifest_v1_refuses_alternates(tmp_path):
    _, _, doc, _ = mirrored(tmp_path)
    doc["format"] = "osd.manifest/1"
    assert mf.problems(doc)


def test_get_from_mirror(tmp_path):
    _, net, _, m = mirrored(tmp_path)
    out = get_mod.get(m, tmp_path / "dest", opener=net)
    assert [(r.outcome, r.source) for r in out] == [("verified", "mirror")] * 3
    assert net.origin_requests() == 0
    for p, b in FILES.items():
        assert (tmp_path / "dest" / "acme--demo" / p).read_bytes() == b
    assert all("from mirror" in line for line in get_mod.summary(m, out)[:3])


def test_get_falls_back_when_mirror_unreachable(tmp_path):
    _, net, _, m = mirrored(tmp_path)
    net.dead.add(MIRROR)
    out = get_mod.get(m, tmp_path / "dest", opener=net)
    assert [(r.outcome, r.source) for r in out] == [("verified", "origin")] * 3
    assert all(r.attempts[0][:2] == ("mirror", "unreachable") for r in out)
    assert net.origin_requests() == 3


def test_get_mirror_mismatch_then_origin(tmp_path):
    s, net, _, m = mirrored(tmp_path)
    a = next(x for x in m.entries[0].assets if x.key == "survey/b.las")
    bad = s.root / mirror.keys_for("acme/demo", a.sha256, a.key).public
    bad.write_bytes(b"X" + bad.read_bytes()[1:])
    seen = []
    real_replace = get_mod.os.replace

    def watch(src, dst):                                     # what reaches the target path
        seen.append(Path(src).read_bytes())
        real_replace(src, dst)
    get_mod.os.replace = watch
    try:
        out = {r.key: r for r in get_mod.get(m, tmp_path / "dest", opener=net)}
    finally:
        get_mod.os.replace = real_replace
    r = out["survey/b.las"]
    assert r.attempts[0][:2] == ("mirror", "mismatch") and (r.outcome, r.source) == ("verified", "origin")
    assert (tmp_path / "dest" / "acme--demo" / "survey/b.las").read_bytes() == FILES["survey/b.las"]
    assert all(_sha(b) in {_sha(x) for x in FILES.values()} for b in seen)   # bad bytes never placed
    assert out["survey/a.sgy"].source == "mirror"


# --- custody schema ------------------------------------------------------------------------------

def _custody_fixture(name):
    return json.loads((FIXTURES / "custody" / name).read_text())


def test_custody_fixture_valid():
    doc = _custody_fixture("held.json")
    assert custody.problems(doc, doc["sha256"] + ".json", doc["bytes"]) == []
    tomb = _custody_fixture("removed.json")
    assert custody.problems(tomb, tomb["sha256"] + ".removed.json") == []


@pytest.mark.parametrize("name", ["missing-origin", "missing-licence", "missing-contact", "malformed-hash",
                                  "inconsistent-size", "invalid-removal-state"])
def test_custody_rejects(name):
    doc = _custody_fixture(f"bad-{name}.json")
    assert custody.problems(doc, doc.get("sha256", "x") + ".json", 12129), name


def test_custody_rejects_size_unlike_the_object():
    doc = _custody_fixture("held.json")
    assert custody.problems(doc, doc["sha256"] + ".json", doc["bytes"] + 1)


def test_custody_rejects_held_state_in_a_tombstone_name():
    doc = _custody_fixture("held.json")
    assert custody.problems(doc, doc["sha256"] + ".removed.json")


def test_custody_licence_must_allow_redistribution():
    doc = copy.deepcopy(_custody_fixture("held.json"))
    doc["licence"]["redistribution"] = "unknown"
    assert custody.problems(doc, doc["sha256"] + ".json")


# --- takedown -------------------------------------------------------------------------------------

def test_takedown(tmp_path):
    s, net = store(tmp_path), Net()
    mirror.put(record(), verification(), RULE, s, net, now=NOW)
    sha = _sha(FILES["survey/a.sgy"])
    req = "https://github.com/ophiolite-labs/open-subsurface-data/issues/99"
    gone = mirror.remove(sha, s, request=req, approved_by="tuna-soup", now=NOW)
    assert gone and all(not s.exists(k) for k in gone)
    assert not [k for k in s.keys("") if sha in k and not k.endswith(".removed.json")]
    tomb = s.get_json(f"custody/{sha}.removed.json")
    assert custody.problems(tomb, f"{sha}.removed.json") == []
    assert tomb["removal"] == {"state": "removed", "removed_at": "2026-10-23T12:00:00Z", "request": req,
                               "approved_by": "tuna-soup"}
    col = json.loads((catalogue(tmp_path, s) / "stac" / "acme--demo" / "collection.json").read_text())
    assert "alternate" not in col["assets"]["survey/a.sgy"] and "alternate" in col["assets"]["survey/b.las"]
    net.requests.clear()
    out = {c.path: c.outcome for c in mirror.put(record(), verification(), RULE, s, net, now=NOW)}
    assert out == {"survey/a.sgy": "refused", "survey/b.las": "present", "survey/c.csv": "present"}
    assert net.requests == Counter() and not s.exists(mirror.keys_for("acme/demo", sha, "survey/a.sgy").public)


def test_remove_unknown_digest_refused(tmp_path):
    with pytest.raises(mirror.MirrorError):
        mirror.remove("ab" * 32, store(tmp_path), request="https://x.test/1", approved_by="tuna-soup", now=NOW)


# --- the build regenerates the public index ------------------------------------------------------

def test_build_writes_public_index_from_custody(tmp_path):
    rec = load_record(paths.RECORDS_DIR / "opm" / "norne.yaml")
    rule = mirror.load_rules()["opm/norne"]
    files = {"norne/README": b"r" * 687}
    s = mirror.LocalDirectory(tmp_path / "store", MIRROR)
    net = Net(files={})
    net.body = lambda url: files[url[len(ORIGIN):]]
    v = verification("opm/norne", files, rule=rule)
    mirror.put(rec, v, rule, s, net, now=NOW)
    vdir = tmp_path / "verification"
    vdir.mkdir()
    (vdir / "opm__norne.json").write_text(json.dumps(v))
    out = tmp_path / "catalog"
    build(out, vdir, mirror_dir=s.root)
    index = json.loads((out / "mirror.json").read_text())
    assert [(c["record_id"], c["path"]) for c in index["copies"]] == [("opm/norne", "norne/README")]
    col = json.loads((out / "stac" / "opm--norne" / "collection.json").read_text())
    assert col["assets"]["norne/README"]["alternate"]["mirror"]["href"] == index["copies"][0]["href"]


def test_no_public_copy_without_a_valid_custody_document(tmp_path):
    s = mirror.LocalDirectory(tmp_path / "store", (tmp_path / "store").as_uri())   # file:// is no public href
    with pytest.raises(mirror.MirrorError, match="custody document refused"):
        mirror.put(record(), verification(), RULE, s, Net(), now=NOW)
    assert s.keys("mirror/") == [] and s.keys("custody/") == []


def test_verification_2_still_validates():
    """A verification/2 record as the verify workflow wrote it on 23 Oct (Norne, before E07)."""
    doc = json.loads((FIXTURES / "verification-2-norne.json").read_text())
    Draft202012Validator(json.loads((paths.SCHEMA_DIR / "verification.schema.json").read_text())).validate(doc)
    e = mirror.eligibility(load_record(paths.RECORDS_DIR / "opm" / "norne.yaml"), doc, mirror.load_rules()["opm/norne"])
    assert e.reasons == ("no inventory in the latest verification",)


def test_cli_put_eligible_remove(tmp_path, capsys):
    from osd import cli
    rule = mirror.load_rules()["opm/norne"]
    vdir = tmp_path / "v"
    vdir.mkdir()
    (vdir / "opm__norne.json").write_text(json.dumps(verification("opm/norne", NORNE_LISTING, rule=rule)))
    net = Net(files={})
    net.body = lambda url: NORNE_LISTING[url[len(ORIGIN):]]
    assert cli.main(["mirror", "eligible", "opm/norne", "equinor/volve", "--vdir", str(vdir)]) == 0
    out = capsys.readouterr().out
    assert "eligible opm/norne" in out and "1 eligible" in out and "redistribution unknown" in out
    args = cli.argparse.Namespace(ids=["opm/norne"], vdir=str(vdir), store=str(tmp_path / "s"), public_url=MIRROR)
    assert cli.cmd_mirror_put(args, opener=net) == 0
    assert "5 objects, 5 custody documents, 0 tombstones" in capsys.readouterr().out
    sha = _sha(NORNE_LISTING["norne/README"])
    assert cli.main(["mirror", "remove", sha, "--store", str(tmp_path / "s"), "--public-url", MIRROR,
                     "--request", "https://github.com/ophiolite-labs/open-subsurface-data/issues/1",
                     "--approved-by", "tuna-soup"]) == 0
    assert cli.cmd_mirror_put(args, opener=net) == 0
    assert "refused     opm/norne norne/README" in capsys.readouterr().out


def test_interrupted_takedown_already_drops_the_copy_and_reruns(tmp_path):
    s, net = store(tmp_path), Net()
    mirror.put(record(), verification(), RULE, s, net, now=NOW)
    sha = _sha(FILES["survey/a.sgy"])
    real = s.delete
    s.delete = lambda key: (_ for _ in ()).throw(KeyboardInterrupt())          # dies after the tombstone
    with pytest.raises(KeyboardInterrupt):
        mirror.remove(sha, s, request="https://x.test/issues/1", approved_by="tuna-soup", now=NOW)
    assert s.exists(f"custody/{sha}.json") and s.exists(f"custody/{sha}.removed.json")
    assert sha not in {c["sha256"] for c in mirror.public_index(s.root / "custody")}
    assert mirror.put(record(), verification(), RULE, s, net, now=NOW)[0].outcome == "refused"
    s.delete = real
    mirror.remove(sha, s, request="https://x.test/issues/1", approved_by="tuna-soup", now=NOW)
    assert [k for k in s.keys("") if sha in k] == [f"custody/{sha}.removed.json"]
