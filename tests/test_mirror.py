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

def test_build_writes_public_index_from_custody(tmp_path, records_subset):
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
    build(out, vdir, mirror_dir=s.root, records_dir=records_subset(["opm/norne"]))
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


# --- E23: the mirror's selection through the listing readers --------------------------------------

def _contents(path, size):
    """One entry of the GitHub contents API, as api.github.com answers for OPM/opm-data/contents/norne."""
    name = path.rsplit("/", 1)[-1]
    raw = f"https://raw.githubusercontent.com/OPM/opm-data/master/{path}" if size is not None else None
    api = f"https://api.github.com/repos/OPM/opm-data/contents/{path}?ref=master"
    html = f"https://github.com/OPM/opm-data/{'blob' if raw else 'tree'}/master/{path}"
    return {"name": name, "path": path, "sha": "0" * 40, "size": size or 0, "url": api, "html_url": html,
            "git_url": "https://api.github.com/repos/OPM/opm-data/git/blobs/" + "0" * 40, "download_url": raw,
            "type": "file" if raw else "dir", "_links": {"self": api, "git": api, "html": html}}


def test_mirror_selection_unchanged_through_readers():
    from osd.verify import parse_listing
    body = json.dumps([_contents("norne/INCLUDE", None)]
                      + [_contents(p, len(b)) for p, b in NORNE_LISTING.items()]).encode()
    entries = parse_listing(body, "https://api.github.com/repos/OPM/opm-data/contents/norne")
    assert [(e.name, e.url, e.size) for e in entries] == [
        (p, f"https://raw.githubusercontent.com/OPM/opm-data/master/{p}", len(b)) for p, b in NORNE_LISTING.items()]
    rule = mirror.load_rules()["opm/norne"]
    rec = load_record(paths.RECORDS_DIR / "opm" / "norne.yaml")
    files = {rec["origin"]["manifest_url"]: body,
             **{f"https://raw.githubusercontent.com/OPM/opm-data/master/{p}": b for p, b in NORNE_LISTING.items()}}

    def opener(url):
        if url not in files:
            raise FetchError(url, 404)
        return iter([files[url]])

    got, inv = mirror.inventory(rec, rule, opener, ByteBudget())
    assert inv == {"rule": rule, "listed": 5, "selected": list(NORNE_LISTING), "coverage": "complete"}
    assert {f["path"]: f["sha256"] for f in got} == {p: _sha(b) for p, b in NORNE_LISTING.items()}


def test_mirror_inventory_reads_ckan_assets_only():
    rec = record()
    package = json.dumps({"success": True, "result": {"url": "https://acme.example/landing", "resources": [
        {"name": "survey/a.sgy", "url": ORIGIN + "survey/a.sgy", "format": "SEG-Y", "size": len(FILES["survey/a.sgy"])},
        {"name": "Web Map Service", "url": ORIGIN + "wms", "format": "WMS"},
        {"name": "Project page", "url": "https://acme.example/landing", "format": "HTML"}]}}).encode()
    net = Net()
    net.body = lambda url, orig=net.body: package if url == ORIGIN + "index.json" else orig(url)
    files, inv = mirror.inventory(rec, ["*"], net, ByteBudget())
    assert inv == {"rule": ["*"], "listed": 1, "selected": ["survey/a.sgy"], "coverage": "complete"}
    assert [f["path"] for f in files] == ["survey/a.sgy"]


# --- slice 2: the S3 transport against an in-memory S3 that checks every signature ---------------

S3_ENDPOINT = "https://fsn1.objects.test"
S3_ACCESS, S3_SECRET = "TESTACCESSKEY", "test/secret/key"     # fakes: the real keys live only in GitHub


class FakeS3:
    """S3 over `send(method, url, headers, body)`: one bucket, objects with their ACL, multipart
    uploads, server-side copy, ListObjectsV2 in pages of `page`. Every request's SigV4 signature and
    payload hash are checked; `fail` maps (method, key, query-substring) to a status to answer once;
    `copy_error` answers the next copy with 200 and an <Error> body."""

    def __init__(self, bucket="osd-mirror", page=1000):
        self.bucket, self.page = bucket, page
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.uploads: dict[str, dict] = {}
        self.requests: list[tuple[str, str, str]] = []
        self.fail: dict[tuple[str, str, str], int] = {}
        self.copy_error = False

    def _reply(self, status, body=b"", headers=None):
        stream = __import__("io").BytesIO(body)
        return mirror.Reply(status, {k.lower(): v for k, v in (headers or {}).items()},
                            lambda n=-1: stream.read(n))

    def __call__(self, method, url, headers, body):
        from urllib.parse import parse_qs, unquote, urlsplit
        u = urlsplit(url)
        assert u.scheme + "://" + u.netloc == S3_ENDPOINT
        _, bucket, *rest = u.path.split("/", 2)
        key = unquote(rest[0]) if rest else ""
        q = {k: v[0] for k, v in parse_qs(u.query, keep_blank_values=True).items()}
        self.requests.append((method, key, u.query))
        # the signature: recomputed from what arrived
        assert headers["x-amz-content-sha256"] == hashlib.sha256(body).hexdigest(), "payload hash not signed"
        when = datetime.strptime(headers["x-amz-date"], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        plain = {k: v for k, v in headers.items() if k not in ("Authorization", "x-amz-date", "x-amz-content-sha256")}
        want = mirror.sigv4(method, url, plain, headers["x-amz-content-sha256"], S3_ACCESS, S3_SECRET, "fsn1", when)
        if bucket != self.bucket or headers["Authorization"] != want["Authorization"]:
            return self._reply(403, b"<Error><Code>SignatureDoesNotMatch</Code></Error>")
        for (m, k, part), status in list(self.fail.items()):
            if m == method and k == key and part in u.query:
                del self.fail[(m, k, part)]
                return self._reply(status, b"<Error><Code>InternalError</Code></Error>")
        acl = headers.get("x-amz-acl", "private")
        if method == "HEAD":
            if not key:
                return self._reply(200)
            if key in self.objects:
                return self._reply(200, headers={"Content-Length": str(len(self.objects[key][0]))})
            return self._reply(404)
        if method == "GET" and not key:
            names = sorted(k for k in self.objects if k.startswith(q.get("prefix", "")))
            start = int(q.get("continuation-token", "0"))
            batch, more = names[start:start + self.page], start + self.page < len(names)
            xml = ("<ListBucketResult xmlns='http://s3.amazonaws.com/doc/2006-03-01/'>"
                   + "".join(f"<Contents><Key>{k}</Key></Contents>" for k in batch)
                   + f"<IsTruncated>{'true' if more else 'false'}</IsTruncated>"
                   + (f"<NextContinuationToken>{start + self.page}</NextContinuationToken>" if more else "")
                   + "</ListBucketResult>")
            return self._reply(200, xml.encode())
        if method == "GET":
            return self._reply(200, self.objects[key][0]) if key in self.objects else self._reply(404)
        if method == "DELETE":
            if "uploadId" in q:
                self.uploads.pop(q["uploadId"], None)
            else:
                self.objects.pop(key, None)
            return self._reply(204)
        if method == "POST" and "uploads" in q:
            uid = f"u{len(self.requests)}"
            self.uploads[uid] = {"key": key, "acl": acl, "parts": {}}
            return self._reply(200, f"<InitiateMultipartUploadResult><UploadId>{uid}</UploadId>"
                                    f"</InitiateMultipartUploadResult>".encode())
        if method == "POST":
            up = self.uploads.pop(q["uploadId"])
            numbers = [int(n) for n in __import__("re").findall(r"<PartNumber>(\d+)</PartNumber>", body.decode())]
            self.objects[key] = (b"".join(up["parts"][n] for n in numbers), up["acl"])
            return self._reply(200, b"<CompleteMultipartUploadResult/>")
        if method == "PUT":
            source = headers.get("x-amz-copy-source")
            if source:
                if self.copy_error:
                    self.copy_error = False
                    return self._reply(200, b"<Error><Code>InternalError</Code></Error>")
                data = self.objects[unquote(source).split("/", 2)[2]][0]
                if "x-amz-copy-source-range" in headers:
                    a, b = map(int, headers["x-amz-copy-source-range"].removeprefix("bytes=").split("-"))
                    data = data[a:b + 1]
            else:
                data = body
            if "uploadId" in q:
                self.uploads[q["uploadId"]]["parts"][int(q["partNumber"])] = data
                etag = f'"{hashlib.md5(data).hexdigest()}"'
                return self._reply(200, f"<CopyPartResult><ETag>{etag}</ETag></CopyPartResult>".encode()
                                   if source else b"", {"ETag": etag})
            self.objects[key] = (data, acl)
            return self._reply(200, b"<CopyObjectResult><ETag>x</ETag></CopyObjectResult>" if source else b"")
        return self._reply(405)


def s3_store(fake=None, **kw) -> tuple[mirror.S3, FakeS3]:
    fake = fake or FakeS3()
    return mirror.S3("osd-mirror", S3_ENDPOINT, S3_ACCESS, S3_SECRET, MIRROR, send=fake, **kw), fake


def test_sigv4_matches_aws_example():
    """AWS's published SigV4 examples for S3 (GET Object with a range; ListObjects)."""
    when = datetime(2013, 5, 24, tzinfo=UTC)
    key, secret = "AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    got = mirror.sigv4("GET", "https://examplebucket.s3.amazonaws.com/test.txt", {"Range": "bytes=0-9"},
                       mirror.EMPTY_SHA256, key, secret, "us-east-1", when)
    assert got["Authorization"] == (
        "AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/20130524/us-east-1/s3/aws4_request, "
        "SignedHeaders=host;range;x-amz-content-sha256;x-amz-date, "
        "Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41")
    got = mirror.sigv4("GET", "https://examplebucket.s3.amazonaws.com/?max-keys=2&prefix=J", {},
                       mirror.EMPTY_SHA256, key, secret, "us-east-1", when)
    assert got["Authorization"].endswith(
        "Signature=34b48302e7b5fa45bde8084f4b7868a86f0a534bc59db6670ed5711ef69dc6f7")


def test_s3_region_from_endpoint_and_keys_never_shown():
    s, _ = s3_store()
    assert s.region == "fsn1" and s.root == "s3://osd-mirror"
    assert S3_SECRET not in repr(s) and S3_ACCESS not in repr(s)
    with pytest.raises(mirror.MirrorError, match="OSD_S3_SECRET_KEY") as e:
        mirror.open_store("s3://osd-mirror", None, {"OSD_S3_ENDPOINT": S3_ENDPOINT, "OSD_S3_ACCESS_KEY": S3_ACCESS})
    assert S3_ACCESS not in str(e.value)
    s = mirror.open_store("s3://osd-mirror", None, {"OSD_S3_ENDPOINT": "https://fsn1.your-objectstorage.com",
                                                     "OSD_S3_ACCESS_KEY": "a", "OSD_S3_SECRET_KEY": "b"})
    assert s.public_url("mirror/x") == "https://osd-mirror.fsn1.your-objectstorage.com/mirror/x"


def test_s3_mirror_three_files():
    s, _ = s3_store()
    net = Net()
    out = mirror.put(record(), verification(), RULE, s, net, now=NOW)
    assert [c.outcome for c in out] == ["published"] * 3
    docs = [s.get_json(k) for k in s.keys("custody/")]
    assert {(d["path"], d["sha256"], d["bytes"]) for d in docs} == {(p, _sha(b), len(b)) for p, b in FILES.items()}
    for d in docs:
        assert custody.problems(d, d["sha256"] + ".json", s.size(d["key"])) == []
        assert b"".join(s.open(d["key"])) == FILES[d["path"]]
    assert net.origin_requests() == 3 and s.keys("staging/") == []


def test_s3_acl_on_public_keys_only():
    s, fake = s3_store()
    mirror.put(record(), verification(), RULE, s, Net(), now=NOW)
    assert {k.split("/")[0]: acl for k, (_, acl) in fake.objects.items()} == {
        "mirror": "public-read", "custody": "public-read"}
    staged = [(m, k, q) for m, k, q in fake.requests if m == "PUT" and k.startswith("staging/")]
    assert staged and all(fake.objects.get(k) is None for _, k, _ in staged)     # staging gone after the move
    s.upload("staging/x/y", [b"z"])
    assert fake.objects["staging/x/y"][1] == "private"


def test_s3_corrupted_stream_leaves_no_public_key():
    s, fake = s3_store()
    net = Net()
    net.corrupt.add(ORIGIN + "survey/b.las")
    out = {c.path: c.outcome for c in mirror.put(record(), verification(), RULE, s, net, now=NOW)}
    assert out["survey/b.las"] == "mismatch"
    assert not [k for k in fake.objects if _sha(FILES["survey/b.las"]) in k]


def test_s3_rerun_after_interruption_and_crash_before_move():
    s, fake = s3_store()
    net = Net()
    net.interrupt.add(ORIGIN + "survey/b.las")
    with pytest.raises(ConnectionResetError):
        mirror.put(record(), verification(), RULE, s, net, now=NOW)
    sha_c = _sha(FILES["survey/c.csv"])
    fake.fail[("PUT", mirror.keys_for("acme/demo", sha_c, "survey/c.csv").public, "")] = 500   # copy fails
    out = {c.path: c.outcome for c in _put_until_error(s, net)}
    assert out == {"survey/a.sgy": "present", "survey/b.las": "published"}
    assert [k for k in fake.objects if k.startswith("staging/")] == [f"staging/{sha_c}/c.csv"]
    out = mirror.put(record(), verification(), RULE, s, net, now=NOW)
    assert [c.outcome for c in out] == ["present", "present", "published"] and "staging" in out[2].detail
    assert net.requests[ORIGIN + "survey/a.sgy"] == 1 and net.requests[ORIGIN + "survey/c.csv"] == 1
    assert len(s.keys("mirror/")) == 3 and s.keys("staging/") == []


def _put_until_error(s, net):
    done = []
    for f in mirror.eligibility(record(), verification(), RULE).files:
        try:
            done.append(mirror._put_one(record(), verification(), f, s, net, NOW))
        except mirror.MirrorError:
            break
    return done


def test_s3_multipart_upload(monkeypatch):
    monkeypatch.setattr(mirror, "PART", 1024)
    s, fake = s3_store()
    net = Net()
    mirror.put(record(), verification(), RULE, s, net, now=NOW)
    big = mirror.keys_for("acme/demo", _sha(FILES["survey/a.sgy"]), "survey/a.sgy").public
    assert fake.objects[big] == (FILES["survey/a.sgy"], "public-read")
    parts = [q for m, k, q in fake.requests if m == "PUT" and k.startswith("staging/") and "partNumber" in q]
    assert len(parts) == 5 + 2       # a.sgy 5000 bytes: 5 parts of 1024 (last 904); b.las 1665: 2
    assert not fake.uploads


def test_s3_origin_failure_aborts_multipart(monkeypatch):
    monkeypatch.setattr(mirror, "PART", 1000)
    s, fake = s3_store()
    net = Net()
    net.dead.add(ORIGIN + "survey/b")
    big = Net().files["survey/a.sgy"]

    def failing():
        yield big[:2500]
        raise FetchError(ORIGIN + "survey/a.sgy", 0, "connection reset")
    with pytest.raises(FetchError):
        s.upload("staging/x/a.sgy", failing())
    assert fake.uploads == {} and "staging/x/a.sgy" not in fake.objects
    assert any(m == "DELETE" and "uploadId" in q for m, _, q in fake.requests)
    out = {c.path: c.outcome for c in mirror.put(record(), verification(), RULE, s, net, now=NOW)}
    assert out["survey/b.las"] == "origin-dead" and not s.keys("staging/")


def test_s3_copy_error_in_200():
    s, fake = s3_store()
    s.upload("staging/x/y", [b"bytes"])
    fake.copy_error = True
    with pytest.raises(mirror.MirrorError, match="InternalError"):
        s.move("staging/x/y", "mirror/r/x/y")
    assert "mirror/r/x/y" not in fake.objects and "staging/x/y" in fake.objects


def test_s3_large_copy_in_ranges(monkeypatch):
    monkeypatch.setattr(mirror, "COPY_LIMIT", 10)
    monkeypatch.setattr(mirror, "COPY_PART", 4)
    s, fake = s3_store()
    s.upload("staging/x/y", [b"0123456789abc"])
    s.move("staging/x/y", "mirror/r/x/y")
    assert fake.objects["mirror/r/x/y"] == (b"0123456789abc", "public-read") and "staging/x/y" not in fake.objects
    assert [q.split("&")[0] for m, k, q in fake.requests if "partNumber" in q] == [
        f"partNumber={i}" for i in range(1, 5)]       # 13 bytes in ranges of 4


def test_s3_wrong_key_is_refused_without_showing_it():
    fake = FakeS3()
    s = mirror.S3("osd-mirror", S3_ENDPOINT, S3_ACCESS, "not-the-secret", MIRROR, send=fake)
    with pytest.raises(mirror.MirrorError, match="HTTP 403 SignatureDoesNotMatch") as e:
        s.put_json("custody/x.json", {})
    assert "not-the-secret" not in str(e.value) and fake.objects == {}


def test_s3_keys_paginate():
    s, fake = s3_store(FakeS3(page=2))
    for i in range(5):
        s.put_json(f"custody/{i}.json", {})
    assert s.keys("custody/") == [f"custody/{i}.json" for i in range(5)]
    assert sum(1 for m, k, q in fake.requests if m == "GET" and not k) == 3


def test_s3_takedown():
    s, fake = s3_store()
    mirror.put(record(), verification(), RULE, s, Net(), now=NOW)
    sha = _sha(FILES["survey/a.sgy"])
    gone = mirror.remove(sha, s, request="https://github.com/ophiolite-labs/open-subsurface-data/issues/9",
                         approved_by="tuna-soup", now=NOW)
    assert gone and [k for k in fake.objects if sha in k] == [f"custody/{sha}.removed.json"]
    assert mirror.put(record(), verification(), RULE, s, Net(), now=NOW)[0].outcome == "refused"
