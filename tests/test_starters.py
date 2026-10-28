"""E40: the starter project contract (charter docs/program/charters/E40-starter-project-contract.md,
strategy E40-starter-project-contract-STRATEGY.md): custody/2, verification/7, starter/1, the nine
validity tests, the published projection and the pack manifest. Everything runs offline over the
fixtures in tests/fixtures/starters/ and the custody snapshot in tests/fixtures/custody/."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

from osd import cli, custody, paths, starters
from osd.records import load_records

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "tests" / "fixtures" / "schema"
MIRROR_CUSTODY = ROOT / "tests" / "fixtures" / "mirror" / "custody"


def _v(path: Path) -> Draft202012Validator:
    return Draft202012Validator(json.loads(path.read_text()), format_checker=FormatChecker())


CUSTODY = _v(paths.SCHEMA_DIR / "custody.schema.json")
CUSTODY_1 = _v(FROZEN / "custody-1.schema.json")
CUSTODY_2 = _v(FROZEN / "custody-2.schema.json")
VERIFICATION = _v(paths.SCHEMA_DIR / "verification.schema.json")
VERIFICATION_6 = _v(FROZEN / "verification-6.schema.json")
VERIFICATION_7 = _v(FROZEN / "verification-7.schema.json")


def _errors(v: Draft202012Validator, doc: dict) -> list[str]:
    return [e.message for e in v.iter_errors(doc)]


# --- custody/2 (design 2) --------------------------------------------------------------------------

HELD_1 = json.loads((MIRROR_CUSTODY / "held.json").read_text())
DEPOSIT = {"obtained_at": "2026-10-29T10:00:00Z", "by": "maintainer",
           "publisher_page_url": "https://terranubis.com/datainfo/F3-Demo-2020",
           "publisher_page_sha256": "1" * 64, "licence_text_sha256": "2" * 64}
DERIVED = {"pack_id": "opm/norne/python", "recipe_id": "norne-python", "from": ["3" * 64]}


def _v2(**provenance) -> dict:
    doc = {k: v for k, v in HELD_1.items() if k not in ("origin_href", "verifier_run")}
    return dict(doc, format="osd.custody/2", **provenance)


def test_frozen_custody_pins():
    """custody/1 is main dbd5650's schema byte for byte; custody/2 is this lane's, pinned for Ophiolite E129."""
    assert hashlib.sha256((FROZEN / "custody-1.schema.json").read_bytes()).hexdigest() == (
        "9711149e5d86a857c8210751267d7aaeb8c89ebed49cc6a3c2a37d6df1e791ff")
    assert hashlib.sha256((FROZEN / "custody-2.schema.json").read_bytes()).hexdigest() == (
        "c029a2033c310bfd048b4224603dcc01a5726958c8537792dc49d9ff3b822e11")
    assert CUSTODY.schema["$id"] == "https://open-subsurface-data.org/schema/custody/2"
    assert CUSTODY_1.schema["$id"].endswith("/custody/1") and CUSTODY_2.schema["$id"].endswith("/custody/2")


def test_custody_1_documents_still_validate():
    for name in ("held.json", "removed.json"):
        doc = json.loads((MIRROR_CUSTODY / name).read_text())
        assert _errors(CUSTODY_1, doc) == [] and _errors(CUSTODY, doc) == [] and _errors(CUSTODY_2, doc) == []
        assert custody.problems(doc) == []


def test_custody_2_three_provenances():
    verified = dict(HELD_1, format="osd.custody/2")
    for doc in (verified, _v2(origin_href=None, deposit=DEPOSIT), _v2(origin_href=None, derived=DERIVED)):
        assert _errors(CUSTODY, doc) == [] and _errors(CUSTODY_2, doc) == []
        assert custody.problems(doc) == []
    assert _errors(CUSTODY_1, _v2(origin_href=None, deposit=DEPOSIT))   # /1 never admitted a deposit


@pytest.mark.parametrize("doc", [
    _v2(origin_href=None),                                                  # null origin, no provenance
    _v2(origin_href=None, deposit=DEPOSIT, derived=DERIVED),                # two provenances
    _v2(origin_href=None, deposit=DEPOSIT, verifier_run=HELD_1["verifier_run"]),
    _v2(origin_href=HELD_1["origin_href"], deposit=DEPOSIT),                # an origin with a deposit
    _v2(origin_href=HELD_1["origin_href"]),                                 # an origin without its run
    dict(_v2(origin_href=None, deposit=DEPOSIT), format="osd.custody/1"),   # a /1 deposit
    _v2(origin_href=None, deposit=dict(DEPOSIT, by="Jane Doe")),            # a person, not a role
    _v2(origin_href=None, derived=dict(DERIVED, **{"from": []})),           # derived from nothing
], ids=["null-origin-alone", "deposit-and-derived", "deposit-and-run", "origin-and-deposit", "origin-without-run",
        "v1-deposit", "by-a-name", "derived-from-nothing"])
def test_custody_2_exactly_one_provenance(doc):
    assert _errors(CUSTODY, doc) and _errors(CUSTODY_2, doc)
    assert custody.problems(doc)


# --- verification/7 (design 3) ---------------------------------------------------------------------

V_BASE = {"record_id": "terranubis/f3-demo-2020", "checked_at": "2026-10-29T10:05:00+00:00", "tool_version": "t",
          "level": "L2"}
DEPOSIT_CHECK = {"name": "deposit", "level": "L2", "outcome": "pass",
                 "detail": "deposited by a maintainer from the publisher's download, 2026-10-29",
                 "files": [{"path": "F3_Demo_2023_seismic.zip", "sha256": "4" * 64, "bytes": 10,
                            "key": "mirror/terranubis/f3-demo-2020/" + "4" * 64 + "/F3_Demo_2023_seismic.zip"}],
                 "obtained_at": "2026-10-29T10:00:00Z", "by": "maintainer",
                 "publisher_page_sha256": "1" * 64, "licence_text_sha256": "2" * 64}


def test_frozen_verification_pins():
    assert hashlib.sha256((FROZEN / "verification-6.schema.json").read_bytes()).hexdigest() == (
        "ec36887cd1aa205136a9501e5bf2bb8921e516a720b0885c2868a8511c20c7c9")
    assert hashlib.sha256((FROZEN / "verification-7.schema.json").read_bytes()).hexdigest() == (
        "d87c42dd419ed1f6465b972c60464ecf8b9f1bc5a924b8a96ae86d65b4c2a49b")
    assert VERIFICATION.schema["$id"] == "https://open-subsurface-data.org/schema/verification/7"


def test_deposit_check_shape():
    doc = dict(V_BASE, checks=[DEPOSIT_CHECK])
    assert _errors(VERIFICATION, doc) == [] and _errors(VERIFICATION_7, doc) == []
    assert _errors(VERIFICATION_6, doc)   # /6 has no deposit payload


@pytest.mark.parametrize("bad", [
    {"detail": "deposited, 29 October"}, {"level": "L1"}, {"files": []}, {"by": "Jane Doe"},
    {"files": [{k: v for k, v in DEPOSIT_CHECK["files"][0].items() if k != "key"}]},
    {"publisher_page_sha256": None}, {"extra": 1},
], ids=["reason-sentence", "level", "no-files", "by-a-name", "file-without-key", "page-hash", "extra-key"])
def test_deposit_check_refuses(bad):
    check = {k: v for k, v in dict(DEPOSIT_CHECK, **bad).items() if v is not None}
    assert _errors(VERIFICATION, dict(V_BASE, checks=[check]))


def test_other_checks_keep_the_v6_shape():
    plain = {"name": "files-checksummed", "level": "L2", "outcome": "pass", "detail": "3 files"}
    assert _errors(VERIFICATION, dict(V_BASE, checks=[plain])) == []
    assert _errors(VERIFICATION, dict(V_BASE, checks=[dict(plain, files=DEPOSIT_CHECK["files"])]))


def test_verification_6_documents_still_validate():
    found = 0
    for p in sorted((ROOT / "tests" / "fixtures").rglob("*.json")):
        try:
            d = json.loads(p.read_text())
        except ValueError:
            continue
        if isinstance(d, dict) and {"record_id", "checked_at", "level", "checks"} <= set(d) and VERIFICATION_6.is_valid(d):
            assert _errors(VERIFICATION, d) == [], p
            found += 1
    assert found >= 15


# --- starter/1 and the fixtures (design 1, 7; acceptance 8) ------------------------------------------

FIXTURES = ROOT / "tests" / "fixtures" / "starters"
PACKS = FIXTURES / "packs"
SNAPSHOT = ROOT / "tests" / "fixtures" / "custody"
F3 = "terranubis__f3-demo-2020__starter.json"
TEAPOT = "rmotc__teapot-dome__python.json"
STARTER = _v(paths.SCHEMA_DIR / "starter.schema.json")
STARTER_1 = _v(FROZEN / "starter-1.schema.json")


def pack(name: str = F3) -> dict:
    return json.loads((PACKS / name).read_text())


def test_frozen_starter_pin():
    assert hashlib.sha256((FROZEN / "starter-1.schema.json").read_bytes()).hexdigest() == (
        "f38b9bbce3adbeecc4aecacd1a1f367b6bdb2acaa157d68c200455becd766250")
    assert STARTER.schema["$id"] == STARTER_1.schema["$id"] == "https://open-subsurface-data.org/schema/starter/1"


def test_frozen_schemas_validate_the_fixtures():
    for name in (F3, TEAPOT):
        assert _errors(STARTER, pack(name)) == [] and _errors(STARTER_1, pack(name)) == []
    docs = [json.loads(p.read_text()) for p in sorted(SNAPSHOT.glob("*.json"))]
    assert {d["format"] for d in docs} == {"osd.custody/1", "osd.custody/2"}
    assert sum(p.name.endswith(".removed.json") for p in SNAPSHOT.glob("*.json")) == 1
    assert {("deposit" in d, "derived" in d) for d in docs} == {(False, False), (True, False), (False, True)}
    for d in docs:
        assert _errors(CUSTODY_2, d) == []
    f3v = json.loads((FIXTURES / "verification" / "terranubis__f3-demo-2020.json").read_text())
    assert [c["name"] for c in f3v["checks"]] == ["origin-reachable", "deposit"]
    assert _errors(VERIFICATION_7, f3v) == [] and _errors(VERIFICATION_6, f3v)


def test_fixture_shapes():
    """The F3-shaped pack: one cube, four wells, two horizons, three targets, deposited inputs, derived SEG-Y
    and LAS; the Teapot-shaped pack: one target over verified inputs."""
    f3, teapot = pack(F3), pack(TEAPOT)
    assert [(c["kind"], c["count"]) for c in f3["contents"]] == [("seismic-3d", 1), ("wellbore-logs", 4), ("horizons", 2)]
    assert [t["application"] for t in f3["targets"]] == ["opendtect", "resinsight", "python"]
    assert {i["held"]["as"] for i in f3["inputs"]} == {"deposited"}
    assert {Path(d["path"]).suffix for d in f3["derived"]} >= {".sgy", ".las"}
    assert [t["application"] for t in teapot["targets"]] == ["python"]
    assert {i["held"]["as"] for i in teapot["inputs"]} == {"verified"}


def _artefact(doc: dict) -> dict:
    return doc["targets"][0]["artefacts"][0]


@pytest.mark.parametrize("mutate", [
    lambda d: d["decisions"][0].update(topic="colour"),
    lambda d: d["decisions"][0].pop("subject"),
    lambda d: _artefact(d).pop("key"),
], ids=["unknown-topic", "missing-subject", "artefact-without-key"])
def test_starter_schema_is_not_permissive(mutate):
    doc = pack(F3)
    mutate(doc)
    assert _errors(STARTER, doc)


# --- custody/2 readers (design 2) ------------------------------------------------------------------

def test_mixed_custody_set_through_index_sync_and_build(tmp_path):
    """The snapshot (/1 verified, /2 deposit and derived, one tombstone) through the store's sync, the
    public index and the build: every held document is indexed once, the tombstoned digest never."""
    from osd import mirror
    from osd.build import build

    store = mirror.LocalDirectory(tmp_path / "store", "https://mirror.example")
    for p in SNAPSHOT.glob("*.json"):
        store.put_json(f"custody/{p.name}", json.loads(p.read_text()))
    synced = tmp_path / "mirror" / "custody"
    names = mirror.sync_custody(store, synced)
    assert names == sorted(p.name for p in SNAPSHOT.glob("*.json"))
    index = mirror.public_index(synced)
    held = [json.loads(p.read_text()) for p in sorted(SNAPSHOT.glob("*.json")) if not p.name.endswith(".removed.json")]
    assert [c["sha256"] for c in index] == [d["sha256"] for d in held]
    assert sorted(custody.provenance(d) for d in held) == ["deposit"] * 2 + ["derived"] * 13 + ["verified"]
    tomb = next(SNAPSHOT.glob("*.removed.json")).name.removesuffix(".removed.json")
    assert tomb not in {c["sha256"] for c in index}
    out = tmp_path / "catalog"
    build(out, FIXTURES / "verification", mirror_dir=tmp_path / "mirror", records_dir=FIXTURES / "records")
    assert json.loads((out / "mirror.json").read_text())["copies"] == index


def test_takedown_of_a_derived_artefact(tmp_path):
    from osd import mirror

    store = mirror.LocalDirectory(tmp_path / "store", "https://mirror.example")
    art = _artefact(pack(F3))
    doc = json.loads((SNAPSHOT / f"{art['sha256']}.json").read_text())
    store.put_json(f"custody/{art['sha256']}.json", doc)
    store.upload(art["key"], [b"x"])
    gone = mirror.remove(art["sha256"], store, request="https://github.com/o/r/issues/1", approved_by="tuna-soup")
    assert art["key"] in gone
    tombstone = store.get_json(f"custody/{art['sha256']}.removed.json")
    assert tombstone["derived"] == doc["derived"] and custody.problems(tombstone, f"{art['sha256']}.removed.json") == []


def test_keys_come_later_while_unpublished():
    """Ophiolite E129 writes a pack before its upload with `unpublished: true` and no keys, then fills each
    key from the held derived custody document; a published pack without a key stays refused."""
    doc = pack(F3)
    for t in doc["targets"]:
        for a in t["artefacts"]:
            a.pop("key")
    assert _errors(STARTER, doc)
    doc["unpublished"] = True
    assert _errors(STARTER, doc) == [] and _errors(STARTER_1, doc) == []
    doc["unpublished"] = False
    assert _errors(STARTER, doc)


# --- the nine validity tests (design 4; acceptance 1 to 5) -------------------------------------------

VDIR = FIXTURES / "verification"


def evidence(records_dir: Path = FIXTURES / "records", custody_dir: Path | None = SNAPSHOT,
             vdir: Path | None = VDIR) -> starters.Evidence:
    return starters.Evidence(load_records(records_dir), vdir, custody_dir)


def problems(doc: dict, ev: starters.Evidence | None = None, starters_dir: Path = PACKS) -> list[str]:
    return starters.check(doc, ev or evidence(), starters_dir).problems


def refused(doc: dict, expected: str, ev: starters.Evidence | None = None, starters_dir: Path = PACKS) -> list[str]:
    out = problems(doc, ev, starters_dir)
    assert any(expected in p for p in out), out
    return out


def test_the_fixture_packs_are_valid():
    for name in (F3, TEAPOT):
        r = starters.check(pack(name), evidence(), PACKS, name)
        assert (r.problems, r.unchecked) == ([], [])


def test_without_evidence_nothing_is_passed_that_needs_it():
    """make check has no verifications and no custody: (b) and (f) are unchecked there, never passed."""
    ev = starters.Evidence(load_records(FIXTURES / "records"), None, Path("/nonexistent"))
    r = starters.check(pack(F3), ev, PACKS)
    assert r.problems == []
    assert {u.split(":")[0] for u in r.unchecked} == (
        {f"input {i['name']}" for i in pack(F3)["inputs"]}
        | {f"artefact {a['path']}" for t in pack(F3)["targets"] for a in t["artefacts"]})
    r = starters.check(pack(TEAPOT), ev, PACKS)
    assert r.problems == [] and all(u.startswith(("input ", "artefact ")) for u in r.unchecked)


def _custody_doc(key: str) -> dict:
    return next(json.loads(p.read_text()) for p in SNAPSHOT.glob("*.json") if json.loads(p.read_text())["key"] == key)


# acceptance 2: inputs

def test_input_of_another_record():
    doc = pack(F3)
    norne = json.loads((MIRROR_CUSTODY / "held.json").read_text())
    doc["inputs"][0]["held"]["key"] = norne["key"]
    refused(doc, "input F3_Demo_2023_seismic.zip: custody key mirror/opm/norne/")
    refused(doc, "holds a file of record opm/norne, not terranubis/f3-demo-2020")


def test_input_of_another_record_verified(tmp_path):
    vdir = tmp_path / "v"
    shutil.copytree(VDIR, vdir)
    other = json.loads((VDIR / "rmotc__teapot-dome.json").read_text())
    (vdir / "acme__other.json").write_text(json.dumps(dict(other, record_id="acme/other")))
    doc = pack(TEAPOT)
    v = json.loads((VDIR / "rmotc__teapot-dome.json").read_text())
    v["files"] = v["files"][1:]
    (vdir / "rmotc__teapot-dome.json").write_text(json.dumps(v))
    refused(doc, "input filt_mig.sgy: " + doc["inputs"][0]["sha256"][:12] + "… is a file of record acme/other, "
            "not rmotc/teapot-dome", evidence(vdir=vdir))


def test_input_wrong_verifier_run():
    doc = pack(TEAPOT)
    doc["inputs"][0]["held"]["verifier_run"]["checked_at"] = "2026-10-01T09:30:00+00:00"
    assert problems(doc) == [("input filt_mig.sgy: verifier_run 2026-10-01T09:30:00+00:00 0.1.0 is not the latest "
                             "verification of rmotc/teapot-dome (2026-10-29T09:30:00+00:00 0.1.0)")]


def test_input_wrong_size():
    doc = pack(TEAPOT)
    doc["inputs"][1]["bytes"] += 1
    assert problems(doc) == [(f"input 490251051400.las: bytes {doc['inputs'][1]['bytes']}, the verification states "
                             f"{doc['inputs'][1]['bytes'] - 1}")]


def test_input_wrong_name():
    doc = pack(TEAPOT)
    doc["inputs"][0]["name"] = doc["licence"]["sources"][0]["input"] = "cube.sgy"
    assert problems(doc) == ["input cube.sgy: name cube.sgy is not filt_mig.sgy, the file the verification names"]


def test_input_tombstoned_custody_key():
    doc = pack(F3)
    tomb = json.loads(next(SNAPSHOT.glob("*.removed.json")).read_text())
    doc["inputs"][0].update(sha256=tomb["sha256"], bytes=tomb["bytes"], held={"as": "deposited", "key": tomb["key"]})
    refused(doc, f"input F3_Demo_2023_seismic.zip: custody key {tomb['key']} is removed (2026-10-28, "
                 "https://github.com/ophiolite-labs/open-subsurface-data/issues/101): never in a pack")


def test_input_deposit_must_be_a_deposit():
    doc = pack(F3)
    doc["inputs"][0]["held"]["key"] = _artefact(doc)["key"]
    refused(doc, "is a derived copy, not a deposit")


# acceptance 3: licence

def _teapot_licence(tmp_path: Path, **change) -> tuple[dict, starters.Evidence]:
    """Teapot with its record's licence changed and the pack's sources following it: only the rule speaks."""
    records = tmp_path / "records"
    shutil.copytree(FIXTURES / "records", records)
    p = records / "rmotc" / "teapot-dome.yaml"
    rec = yaml.safe_load(p.read_text())
    rec["licence"].update(change)
    p.write_text(yaml.safe_dump(rec, sort_keys=False))
    doc = pack(TEAPOT)
    for s in doc["licence"]["sources"]:
        s["licence"].update(change)
    return doc, evidence(records_dir=records)


@pytest.mark.parametrize("value", ["restricted", "unknown"])
def test_licence_not_allowed(tmp_path, value):
    doc, ev = _teapot_licence(tmp_path, redistribution=value)
    assert problems(doc, ev) == [f"input filt_mig.sgy: redistribution {value}: never in a pack",
                                 f"input 490251051400.las: redistribution {value}: never in a pack"]


def test_licence_value_outside_the_enum():
    doc = pack(TEAPOT)
    doc["licence"]["sources"][0]["licence"]["redistribution"] = "maybe"
    assert problems(doc) == [("licence/sources/0/licence/redistribution: 'maybe' is not one of "
                             "['allowed', 'restricted', 'forbidden', 'unknown']")]


def _f3_second_input_licence(tmp_path: Path, **change) -> tuple[dict, starters.Evidence]:
    doc = pack(F3)
    custody_dir = tmp_path / "custody"
    shutil.copytree(SNAPSHOT, custody_dir)
    sha = doc["inputs"][1]["sha256"]
    d = json.loads((custody_dir / f"{sha}.json").read_text())
    d["licence"].update(change)
    (custody_dir / f"{sha}.json").write_text(json.dumps(d))
    doc["licence"]["sources"][1]["licence"].update(change)
    return doc, evidence(custody_dir=custody_dir)


def test_licence_mixed_spdx(tmp_path):
    doc, ev = _f3_second_input_licence(tmp_path, spdx="CC-BY-SA-4.0")
    assert problems(doc, ev) == [('unsupported combination: the inputs\' licence spdx differs ("CC-BY-SA-3.0", '
                                 '"CC-BY-SA-4.0")')]


def test_licence_dropped_required_attribution():
    doc = pack(F3)
    doc["licence"]["attribution"] = "not-required"
    assert problems(doc) == ['licence attribution is "not-required", computed "required" from the inputs']


def test_licence_share_alike_over_a_share_alike_input():
    doc = pack(F3)
    doc["licence"]["share_alike"] = False
    assert problems(doc) == ["licence share_alike is false, computed true from the inputs"]


def test_licence_sources_entry_edited():
    doc = pack(F3)
    doc["licence"]["sources"][0]["licence"]["url"] = "https://creativecommons.org/licenses/by/4.0/"
    out = refused(doc, "licence sources F3_Demo_2023_seismic.zip: not its evidence's licence (url differ)")
    assert all("url" in p for p in out)


def test_licence_attribution_computed_across_inputs():
    lic = {"name": "n", "redistribution": "allowed"}
    for values, expected in ((["required", "unknown"], "required"), (["not-required", "unknown"], "unknown"),
                             (["not-required", "not-required"], "not-required")):
        got, why = starters.computed_licence([{"input": str(i), "licence": dict(lic, attribution=a)}
                                              for i, a in enumerate(values)])
        assert why == [] and got["attribution"] == expected and "share_alike" not in got


# acceptance 4: decisions

def test_decision_missing_for_one_well():
    doc = pack(F3)
    doc["decisions"] = [d for d in doc["decisions"] if (d["topic"], d["subject"]) != ("depth-reference", "F03-2")]
    assert problems(doc) == ["decision depth-reference for F03-2 (wellbore-logs) is missing"]


def test_decision_contradicting_duplicate():
    doc = pack(F3)
    doc["decisions"].append({"topic": "crs", "subject": "F3", "value": "EPSG:25831", "source": "chosen", "note": "n"})
    assert problems(doc) == ["decision crs for F3 has two values: EPSG:23031 (ED50 / UTM zone 31N) | EPSG:25831"]
    doc["decisions"][-1]["value"] = doc["decisions"][0]["value"]   # the same value twice is one decision
    assert problems(doc) == []


def test_decision_depth_cube_needs_velocity():
    doc = pack(F3)
    next(d for d in doc["decisions"] if (d["topic"], d["subject"]) == ("domain", "F3"))["value"] = "depth"
    assert problems(doc) == ["decision velocity for F3 (seismic-3d) is missing"]
    doc["decisions"].append({"topic": "velocity", "subject": "F3", "value": "dGB's interval model", "source": "publisher"})
    assert problems(doc) == []


def test_decision_subject_and_count():
    doc = pack(F3)
    doc["decisions"][0]["subject"] = "F9"
    doc["contents"][1]["count"] = 5
    assert set(problems(doc)) == {"contents wellbore-logs: count 5, ids name 4",
                                  "decision crs names subject F9, not an object of contents",
                                  "decision crs for F3 (seismic-3d) is missing"}


def test_a_pack_line_satisfies_no_object():
    doc = pack(TEAPOT)
    doc["decisions"] = [d for d in doc["decisions"] if (d["topic"], d["subject"]) != ("crs", "Teapot 3D")]
    assert problems(doc) == ["decision crs for Teapot 3D (seismic-3d) is missing"]


# acceptance 5: artefacts and fidelity

def _custody_copy(tmp_path: Path) -> Path:
    shutil.copytree(SNAPSHOT, tmp_path / "custody")
    return tmp_path / "custody"


def test_artefact_missing_custody_object(tmp_path):
    custody_dir, a = _custody_copy(tmp_path), _artefact(pack(F3))
    (custody_dir / f"{a['sha256']}.json").unlink()
    assert problems(pack(F3), evidence(custody_dir=custody_dir)) == [
        f"artefact standard/F3.sgy: no held custody document has key {a['key']}"]


def test_artefact_tombstone(tmp_path):
    custody_dir, a = _custody_copy(tmp_path), _artefact(pack(F3))
    d = json.loads((custody_dir / f"{a['sha256']}.json").read_text())
    d["removal"] = {"state": "removed", "removed_at": "2026-10-30T08:00:00Z",
                    "request": "https://github.com/ophiolite-labs/open-subsurface-data/issues/102", "approved_by": "tuna-soup"}
    (custody_dir / f"{a['sha256']}.removed.json").write_text(json.dumps(d))   # takedown writes the tombstone first
    expected = problems(pack(F3), evidence(custody_dir=custody_dir))
    (custody_dir / f"{a['sha256']}.json").unlink()                           # then deletes the live document
    assert problems(pack(F3), evidence(custody_dir=custody_dir)) == expected == [
        (f"artefact standard/F3.sgy: custody key {a['key']} is removed (2026-10-30, "
        "https://github.com/ophiolite-labs/open-subsurface-data/issues/102): never in a pack")]


def test_artefact_size_mismatch():
    doc = pack(TEAPOT)
    a = doc["targets"][0]["artefacts"][2]
    a["bytes"] += 1
    assert problems(doc) == [(f"artefact python/teapot_starter.ipynb: bytes {a['bytes']}, its custody document states "
                             f"{a['bytes'] - 1}")]


def test_artefact_of_another_pack():
    doc = pack(TEAPOT)
    other = _artefact(pack(F3))
    doc["targets"][0]["artefacts"][2] = dict(other, path="python/teapot_starter.ipynb")
    refused(doc, "is not an artefact of rmotc/teapot-dome/python (terranubis/f3-demo-2020/starter)")


def test_import_names_no_artefact():
    doc = pack(F3)
    doc["targets"][1]["import"] = "resinsight/missing.py"
    assert problems(doc) == ["target resinsight: import resinsight/missing.py is not one of its artefacts"]


def test_one_path_one_digest():
    doc = pack(F3)
    doc["derived"][0]["sha256"] = "0" * 64
    assert problems(doc) == ["artefact standard/F3.sgy: two digests for one path in the pack"]


def _fidelity(tmp_path: Path, mutate) -> Path:
    shutil.copytree(PACKS, tmp_path / "packs")
    p = tmp_path / "packs" / "fidelity" / F3
    fd = json.loads(p.read_text())
    mutate(fd)
    p.write_text(json.dumps(fd))
    return tmp_path / "packs"


def _extra(fd: dict) -> None:
    fd["inputs"].append(dict(fd["inputs"][0], sha256="e" * 64, name="extra.zip"))


def _failed(fd: dict) -> None:
    fd["inputs"][1].update(result="failed", reason="unreadable")
    fd["inputs"][1].pop("output")


@pytest.mark.parametrize("mutate,expected", [
    (lambda fd: fd["inputs"].pop(), ("fidelity fidelity/terranubis__f3-demo-2020__starter.json: no result for input "
                                    "F3_Demo_2023_wells.zip (cca8d65df640…)")),
    (_extra, ("fidelity fidelity/terranubis__f3-demo-2020__starter.json: input extra.zip (eeeeeeeeeeee…) is not a pack "
             "input")),
    (_failed, "fidelity fidelity/terranubis__f3-demo-2020__starter.json: input F3_Demo_2023_wells.zip is failed"),
    (lambda fd: fd.update(record="opm/norne"), ("fidelity fidelity/terranubis__f3-demo-2020__starter.json: record "
                                               "opm/norne, the pack is of terranubis/f3-demo-2020")),
    (lambda fd: fd["inputs"][0]["output"].update(kind="faults"), ("fidelity fidelity/terranubis__f3-demo-2020__starter.json: input "
                                                                 "F3_Demo_2023_seismic.zip became faults, not a contents kind")),
    (lambda fd: fd.pop("catalog"), ("fidelity fidelity/terranubis__f3-demo-2020__starter.json: (root): 'catalog' is a "
                                   "required property")),
], ids=["input-missing", "input-extra", "failed", "wrong-record", "kind", "schema"])
def test_fidelity_refusals(tmp_path, mutate, expected):
    assert problems(pack(F3), starters_dir=_fidelity(tmp_path, mutate)) == [expected]


def test_fidelity_path_stays_in_starters(tmp_path):
    doc = pack(F3)
    doc["fidelity"] = "fidelity/absent.json"
    assert problems(doc) == [f"fidelity fidelity/absent.json: not found under {PACKS}"]
    d = tmp_path / "starters"
    shutil.copytree(PACKS, d)
    (d / "fidelity" / F3).unlink()
    (d / "fidelity" / F3).symlink_to(PACKS / "fidelity" / F3)   # a valid record, but outside this starters/
    assert problems(pack(F3), starters_dir=d) == [f"fidelity fidelity/{F3}: not found under {d}"]


def test_derived_from_an_input():
    doc = pack(F3)
    doc["derived"][2]["from"] = "0" * 64
    assert problems(doc) == ["derived standard/F02-1.las: from 000000000000… is not an input digest"]


def test_oracle():
    doc = pack(F3)
    doc["targets"][2]["oracle"].update(differences=3)
    doc["targets"][0]["oracle"].update(values=0)
    assert problems(doc) == ["target opendtect: the oracle compared no values",
                             "target python: the oracle found 3 differences; such a pack says unpublished: true"]
    doc["unpublished"] = True
    assert problems(doc) == []


def test_file_name_and_record():
    r = starters.check(pack(F3), evidence(), PACKS, "f3.json")
    assert r.problems == [("file name f3.json is not terranubis__f3-demo-2020__starter.json, the name of pack "
                          "terranubis/f3-demo-2020/starter")]
    doc = pack(F3)
    doc["record_id"] = "acme/f3"
    assert "id terranubis/f3-demo-2020/starter is not a pack of record acme/f3" in problems(doc)


# acceptance 1: discovery (the function `osd validate` runs is `starters.check`)

def _starters_dir(tmp_path: Path, broken: bool = True) -> Path:
    d = tmp_path / "starters"
    shutil.copytree(PACKS, d)
    if broken:
        doc = pack(F3)
        doc["decisions"] = [x for x in doc["decisions"] if (x["topic"], x["subject"]) != ("nulls", "MFS4")]
        (d / F3).write_text(json.dumps(doc))
    return d


def _validate(*args: str) -> int:
    return cli.main(["validate", *args, "--records", str(FIXTURES / "records"), "--vdir", str(VDIR),
                     "--custody", str(SNAPSHOT), "--outlines", str(FIXTURES / "no-outlines")])


def test_osd_validate_names_the_invalid_pack(tmp_path, capsys, monkeypatch):
    calls = []
    real = starters.check
    monkeypatch.setattr(starters, "check", lambda *a, **k: calls.append(a[0]["id"]) or real(*a, **k))
    assert _validate("--starters", str(_starters_dir(tmp_path))) == 1
    out = capsys.readouterr().out
    bad = [line for line in out.splitlines() if line.startswith("  ")]
    assert bad == [(f"  {tmp_path / 'starters' / F3}: decision nulls for MFS4 "
                   "(horizons) is missing")]
    assert out.splitlines()[-1] == "2 records, 2 starter packs, 1 problems"
    assert sorted(calls) == ["rmotc/teapot-dome/python", "terranubis/f3-demo-2020/starter"]
    assert _validate("--starters", str(_starters_dir(tmp_path / "ok", broken=False))) == 0


def test_osd_validate_one_document_by_path(tmp_path, capsys):
    """Ophiolite E129's subprocess: `osd validate <pack>.json` anywhere on disk, exit 0 or 1."""
    work = tmp_path / "e129-run"
    shutil.copytree(PACKS, work)
    p = work / "pack.json"   # outside starters/: no file-name rule
    doc = pack(F3)
    for t in doc["targets"]:
        for a in t["artefacts"]:
            a.pop("key")
    p.write_text(json.dumps(dict(doc, unpublished=True)))
    assert _validate(str(p)) == 0
    out = capsys.readouterr().out
    assert "unchecked here: artefact standard/F3.sgy: no custody key yet (unpublished)" in out
    assert out.splitlines()[-1] == "1 starter documents, 0 problems"
    p.write_text(json.dumps(pack(F3)))
    assert _validate(str(p)) == 0
    doc = pack(F3)
    doc["licence"]["share_alike"] = False
    p.write_text(json.dumps(doc))
    assert _validate(str(p)) == 1
    assert "licence share_alike is false" in capsys.readouterr().out


# --- the published projection (design 5; acceptance 1, 6) -------------------------------------------

def fixture_build(tmp_path: Path, starters_dir: Path = PACKS, custody_dir: Path | None = SNAPSHOT) -> Path:
    from osd.build import build

    mirror_dir = tmp_path / "mirror"
    if custody_dir is not None:
        shutil.copytree(custody_dir, mirror_dir / "custody")
    out = tmp_path / "catalog"
    build(out, VDIR, mirror_dir=mirror_dir, records_dir=FIXTURES / "records", starters_dir=starters_dir,
          source_commit="1" * 40, verification_commit="2" * 40)
    return out


def test_projection_holds_the_packs_whole(tmp_path):
    out = fixture_build(tmp_path)
    published = json.loads((out / "starters.json").read_text())["starters"]
    assert [p["id"] for p in published] == ["rmotc/teapot-dome/python", "terranubis/f3-demo-2020/starter"]
    held = {json.loads(p.read_text())["key"]: json.loads(p.read_text()) for p in SNAPSHOT.glob("*.json")}
    for p in published:
        name = starters.file_name(p["id"])
        assert p["record"] == {"title": {"rmotc/teapot-dome": "Teapot Dome 3D survey and wells",
                                         "terranubis/f3-demo-2020": "F3 Demo 2020 (Dutch North Sea)"}[p["record_id"]],
                               "level": "L2"}
        for t in p["targets"]:
            for a in t["artefacts"]:
                assert a.pop("href") == held[a["key"]]["href"]
        assert {k: v for k, v in p.items() if k != "record"} == pack(name)   # whole, nothing else added
        assert (out / "starters" / name).read_bytes() == (PACKS / name).read_bytes()
        assert (out / "starters" / p["fidelity"]).read_bytes() == (PACKS / p["fidelity"]).read_bytes()
    recs = json.loads((out / "records.json").read_text())["records"]
    assert {r["id"]: r["starters"] for r in recs if "starters" in r} == {
        "rmotc/teapot-dome": ["rmotc/teapot-dome/python"], "terranubis/f3-demo-2020": ["terranubis/f3-demo-2020/starter"]}


def test_build_refuses_the_invalid_pack_and_publishes_the_rest(tmp_path, capsys):
    out = fixture_build(tmp_path, starters_dir=_starters_dir(tmp_path))
    assert [p["id"] for p in json.loads((out / "starters.json").read_text())["starters"]] == ["rmotc/teapot-dome/python"]
    assert f"starters: {F3} not published: decision nulls for MFS4 (horizons) is missing" in capsys.readouterr().err
    recs = json.loads((out / "records.json").read_text())["records"]
    assert [r["id"] for r in recs if "starters" in r] == ["rmotc/teapot-dome"]
    assert not (out / "starters" / F3).exists()


def test_an_unpublished_pack_is_absent(tmp_path):
    d = _starters_dir(tmp_path, broken=False)
    doc = pack(F3)
    doc["unpublished"] = True
    doc["targets"][0]["oracle"]["differences"] = 2
    (d / F3).write_text(json.dumps(doc))
    assert starters.check(doc, evidence(), d, F3).problems == []
    out = fixture_build(tmp_path, starters_dir=d)
    assert [p["id"] for p in json.loads((out / "starters.json").read_text())["starters"]] == ["rmotc/teapot-dome/python"]
    assert "terranubis/f3-demo-2020/starter" not in (out / "records.json").read_text()


def test_nothing_unchecked_is_published(tmp_path, capsys):
    """make check's build has no custody: the packs stay out, the records carry no starters key."""
    out = fixture_build(tmp_path, custody_dir=None)
    assert json.loads((out / "starters.json").read_text()) == {"starters": []}
    assert "not published: unchecked here: artefact standard/F3.sgy: no custody documents here" in capsys.readouterr().err
    assert all("starters" not in r for r in json.loads((out / "records.json").read_text())["records"])
