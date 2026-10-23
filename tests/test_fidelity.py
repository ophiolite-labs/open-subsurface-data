"""E09: fidelity/1 and the L4 rule (charter docs/program/charters/E09-ophiolite-reads-the-catalogue.md,
strategy E09-ophiolite-reads-the-catalogue-STRATEGY.md). The fixture is two synthetic LAS files, a
record, its verification at L3 and the fidelity record a workspace would write for them; nothing
leaves the machine."""

import copy
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from osd import cli, verify
from osd.build import build

ROOT = Path(__file__).resolve().parents[1]
FIDELITY = ROOT / "tests" / "fixtures" / "fidelity"
RID = "acme/two-wells"
NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)


def snapshot(tmp_path: Path, vdir: Path = FIDELITY / "verification") -> Path:
    """The fixture catalogue as `osd build` writes it, at a fixed time and fixed commits."""
    out = tmp_path / "catalog"
    build(out, vdir, now=NOW, mirror_dir=tmp_path / "no-mirror", records_dir=FIDELITY / "records",
          source_commit="1" * 40, verification_commit="2" * 40)
    return out


def catalog_of(cat_dir: Path) -> dict:
    return json.loads((cat_dir / "records.json").read_text())["catalog"]


def fixture() -> dict:
    return json.loads((FIDELITY / "fidelity.json").read_text())


def verification() -> dict:
    return json.loads((FIDELITY / "verification" / "acme__two-wells.json").read_text())


def apply(tmp_path, doc, v=None, rid=RID):
    return verify.apply_fidelity(rid, doc, verification() if v is None else v)


def conversion(v: dict) -> dict:
    (c,) = [c for c in v["checks"] if c["name"] == "canonical-conversion"]
    return c


def assert_rejected(tmp_path, doc, fragment, v=None):
    out, reasons = apply(tmp_path, doc, v)
    assert any(fragment in r for r in reasons), reasons
    assert out["level"] == "L3"
    c = conversion(out)
    assert c["outcome"] == "fail" and fragment in c["detail"]
    return reasons


# --- the fixture -----------------------------------------------------------------------------------

def test_fixture_is_valid_and_names_the_fixture_snapshot(tmp_path):
    doc = fixture()
    assert verify.fidelity_problems(doc) == []
    assert doc["catalog"] == catalog_of(snapshot(tmp_path))
    hashed = {f["path"]: f["sha256"] for f in verification()["files"]}
    assert hashed == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FIDELITY.glob("*.las"))}


def test_fixture_fidelity_awards_l4_two_of_two(tmp_path):
    before = verification()
    out, reasons = apply(tmp_path, fixture(), before)
    assert reasons == []
    assert out["level"] == "L4"
    c = conversion(out)
    assert c["outcome"] == "pass" and c["detail"].startswith("2 of 2 inputs converted")
    assert verify.conversion_coverage(out) == "2 of 2 converted"
    assert [x for x in out["checks"] if x["name"] != "canonical-conversion"] == \
        [x for x in before["checks"] if x["name"] != "canonical-conversion"]
    assert {k: v for k, v in out.items() if k not in ("checks", "level")} == \
        {k: v for k, v in before.items() if k not in ("checks", "level")}
    verify._validator().validate(out)


def test_partial_coverage_one_of_two_awards_l4(tmp_path):
    doc = fixture()
    doc["inputs"][1].update(result="failed", reason="curve RHOB unit G/CC not in the unit registry")
    doc["inputs"][1].pop("output")
    out, reasons = apply(tmp_path, doc)
    assert reasons == [] and out["level"] == "L4"
    assert verify.conversion_coverage(out) == "1 of 2 converted"


# --- each of these alone yields no L4 and names the reason -----------------------------------------

def test_rejects_mismatched_input_hash(tmp_path):
    doc = fixture()
    doc["inputs"].append({"sha256": "ab" * 32, "name": "well-c.las", "result": "skipped"})
    assert_rejected(tmp_path, doc, "is not a file of the latest verification")


def test_rejects_mismatched_record_id(tmp_path):
    doc = fixture()
    doc["record"] = "acme/other-wells"
    assert_rejected(tmp_path, doc, "names record acme/other-wells")


def test_snapshot_is_identity_not_a_criterion(tmp_path):
    """Amended 23 Oct: another records_digest or an older built_at is recorded, never refused."""
    doc = fixture()
    doc["catalog"].update(records_digest="f" * 64, built_at="2026-10-23T08:59:59Z")   # verification: 09:00
    out, reasons = apply(tmp_path, doc)
    assert reasons == [] and out["level"] == "L4"
    assert "snapshot ffffffffffff… built 2026-10-23T08:59:59Z" in conversion(out)["detail"]


def test_rejects_failed_input_without_reason(tmp_path):
    doc = fixture()
    doc["inputs"][1] = {"sha256": doc["inputs"][1]["sha256"], "name": "well-b.las", "result": "failed"}
    assert_rejected(tmp_path, doc, "is failed without a reason")


def test_rejects_partial_input_without_reason(tmp_path):
    doc = fixture()
    doc["inputs"][1]["result"] = "partial"
    assert_rejected(tmp_path, doc, "is partial without a reason")


def test_rejects_empty_inputs(tmp_path):
    doc = fixture()
    doc["inputs"] = []
    assert assert_rejected(tmp_path, doc, "lists no inputs") == ["the fidelity record lists no inputs"]


def test_rejects_inventory_file_without_result(tmp_path):
    doc = fixture()
    doc["inputs"].pop()
    assert_rejected(tmp_path, doc, "1 of 2 files of the latest verification have no result: well-b.las")


def test_rejects_no_input_converted(tmp_path):
    doc = fixture()
    for i in doc["inputs"]:
        i.update(result="failed", reason="no reader for LAS 2.0 wrapped files")
        i.pop("output")
    assert_rejected(tmp_path, doc, "no input converted")


def test_rejects_without_a_verification(tmp_path):
    out, reasons = verify.apply_fidelity(RID, fixture(), None)
    assert out is None and reasons == [f"no verification for {RID}: run osd verify {RID} first"]


def test_rejects_schema_problems_by_path(tmp_path):
    doc = fixture()
    doc["level"] = "L4"   # a file cannot carry a level
    reasons = assert_rejected(tmp_path, doc, "not an osd.fidelity/1 record")
    assert any("'level' was unexpected" in r for r in reasons)


def test_no_l4_when_own_l3_absent(tmp_path):
    """The catalogue's own L1-L3 stand: a valid fidelity never lifts a record past a gap."""
    v = verification()
    for c in v["checks"]:
        if c["name"] == "outline-derived":
            c.update(outcome="fail", detail="no outline rule")
    v["level"] = "L2"
    out, reasons = apply(tmp_path, fixture(), v)
    assert out["level"] == "L2"
    assert reasons == ["L4 needs the catalogue's own L1-L3: its own checks reach L2"]
    assert conversion(out)["outcome"] == "pass"
    assert [x for x in out["checks"] if x["level"] != "L4"] == [x for x in v["checks"] if x["level"] != "L4"]
    assert verify.conversion_coverage(out) is None


# --- schema negatives --------------------------------------------------------------------------------

def _negatives():
    def missing_catalog(d):
        del d["catalog"]

    def unknown_result(d):
        d["inputs"][0]["result"] = "maybe"

    def output_without_kind(d):
        del d["inputs"][0]["output"]["kind"]

    def input_without_sha256(d):
        del d["inputs"][0]["sha256"]

    return [missing_catalog, unknown_result, output_without_kind, input_without_sha256]


@pytest.mark.parametrize("mutate", _negatives(), ids=lambda f: f.__name__)
def test_fidelity_schema_rejects(mutate):
    doc = fixture()
    mutate(doc)
    assert verify.fidelity_problems(doc) != []


def test_catalog_object_is_one_contract_in_both_schemas():
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k != "description"}
        return x
    schema = lambda n: json.loads((ROOT / "schema" / f"{n}.schema.json").read_text())
    assert strip(schema("fidelity")["$defs"]["catalog"]) == strip(schema("manifest")["$defs"]["catalog"])


# --- the command and the status line ---------------------------------------------------------------

def _vdir(tmp_path) -> Path:
    vdir = tmp_path / "verification"
    vdir.mkdir()
    (vdir / "acme__two-wells.json").write_text((FIDELITY / "verification" / "acme__two-wells.json").read_text())
    return vdir


def test_status_shows_coverage_beside_l4(tmp_path):
    vdir = _vdir(tmp_path)
    assert cli.main(["verify", RID, "--fidelity-from", str(FIDELITY / "fidelity.json"), "--vdir", str(vdir)]) == 0
    lines = cli.status_lines(vdir, now=NOW, records_dir=FIDELITY / "records")
    rows = {next(t for t in line.split() if "/" in t): line for line in lines[1:]}
    assert rows[RID].startswith("L4 (2 of 2 converted) ")
    assert rows["acme/no-statement"].split()[0] == "L0"
    assert {line.index("acme/") for line in lines[1:]} == {lines[0].index(" id ") + 1}   # columns stay aligned


def test_cli_fidelity_from_prints_reasons(tmp_path, capsys):
    vdir = _vdir(tmp_path)
    assert cli.main(["verify", RID, "--fidelity-from", str(FIDELITY / "fidelity.json"), "--vdir", str(vdir)]) == 0
    out = capsys.readouterr().out
    assert f"L4  {RID}  canonical-conversion: pass (2 of 2 inputs converted" in out
    assert json.loads((vdir / "acme__two-wells.json").read_text())["level"] == "L4"
    bad = copy.deepcopy(fixture())
    bad["record"] = "acme/other-wells"
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    assert cli.main(["verify", RID, "--fidelity-from", str(tmp_path / "bad.json"), "--vdir", str(vdir)]) == 1
    out = capsys.readouterr().out
    assert f"L3  {RID}  fidelity rejected: the fidelity record names record acme/other-wells" in out
    assert json.loads((vdir / "acme__two-wells.json").read_text())["level"] == "L3"
    assert cli.main(["verify", "--fidelity-from", str(FIDELITY / "fidelity.json")]) == 2


def test_unrelated_record_edit_keeps_l4(tmp_path):
    """Amended 23 Oct: the fidelity names a snapshot; an edit to another record moves the digest
    and the same file still awards L4, and the rebuilt catalogue publishes it."""
    recs = tmp_path / "records"
    shutil.copytree(FIDELITY / "records", recs)
    other = recs / "acme" / "no-statement.yaml"
    other.write_text(other.read_text().replace("Licence without a statement", "Licence without a statement, edited"))
    vdir = _vdir(tmp_path)
    kw = {"now": NOW, "mirror_dir": tmp_path / "no-mirror", "records_dir": recs,
          "source_commit": "1" * 40, "verification_commit": "2" * 40}
    build(tmp_path / "before", vdir, **kw)
    assert catalog_of(tmp_path / "before")["records_digest"] != fixture()["catalog"]["records_digest"]
    assert cli.main(["verify", RID, "--fidelity-from", str(FIDELITY / "fidelity.json"), "--vdir", str(vdir)]) == 0
    build(tmp_path / "after", vdir, **kw)
    published = {r["id"]: r["level"] for r in json.loads((tmp_path / "after" / "records.json").read_text())["records"]}
    assert published[RID] == "L4"


def _network_run(previous: dict, bodies: dict[str, bytes]) -> dict:
    """A verify_record run against fakes: the listing names the two wells, bodies serves them."""
    rec = yaml.safe_load((FIDELITY / "records" / "acme" / "two-wells.yaml").read_text())
    rec["added"] = str(rec["added"])
    base = "https://acme.example/two-wells/"

    def opener(url):
        if url.endswith("/robots.txt"):
            raise verify.FetchError(url, 404)
        if url == rec["origin"]["manifest_url"]:
            return iter([json.dumps(sorted(bodies)).encode()])
        if url == rec["licence"]["url"]:
            return iter([b"Acme Two Wells Licence 1.0: share alike, attribute Acme."])
        return iter([bodies[url.removeprefix(base)]])

    fetch = lambda u: verify.Fetched(200, u, "text/html", 1)
    return verify.verify_record(rec, fetch, None, opener=opener, previous=previous, sample=["*.las"])


def test_verification_run_with_unchanged_files_keeps_the_conversion(tmp_path):
    accepted, _ = apply(tmp_path, fixture())
    las = {p.name: p.read_bytes() for p in FIDELITY.glob("*.las")}
    again = _network_run(accepted, las)
    assert conversion(again) == conversion(accepted)
    changed = _network_run(accepted, dict(las, **{"well-b.las": las["well-b.las"] + b" 1502.0 70.00 2.450\n"}))
    assert conversion(changed)["outcome"] == "skip" and "changed since the fidelity" in conversion(changed)["detail"]
    fresh = _network_run(verification(), las)
    assert conversion(fresh)["detail"] == verify.NO_FIDELITY


def test_plain_verify_declares_conversion_skip():
    rec = {"id": RID, "origin": {"url": "https://acme.example/x", "access": "anonymous"}, "licence": {}}
    v = verify.verify_record(rec, lambda u: verify.Fetched(200, u, "text/html", 1), None)
    assert conversion(v) == {"name": "canonical-conversion", "level": "L4", "outcome": "skip",
                             "detail": "no fidelity record (osd verify <id> --fidelity-from)"}
