"""E40: the starter project contract (charter docs/program/charters/E40-starter-project-contract.md,
strategy E40-starter-project-contract-STRATEGY.md): custody/2, verification/7, starter/1, the nine
validity tests, the published projection and the pack manifest. Everything runs offline over the
fixtures in tests/fixtures/starters/ and the custody snapshot in tests/fixtures/custody/."""

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from osd import custody, paths

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
        "8e49a769973447b23e12a8f8beb4cac7ea9f99a3a5c40e8a36ffed5a06c87cee")
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
