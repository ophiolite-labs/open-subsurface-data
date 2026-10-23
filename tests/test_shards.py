"""H2: verify in shards. The shard key (origin host hash), `osd verify --shard I/N` with an injected
verifier, the finishing job's overlay of shard artifacts on the earlier-results snapshot, and its
dead-link report step run with a fake `gh` (no network, no issue touched)."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import yaml

from osd import cli, paths, shards
from osd.records import load_records

FIX = paths.ROOT / "tests" / "fixtures" / "shards"
CATALOGUE = load_records()  # read once: the gate's time is unchanged (charter)


def expected(recs: dict, i: int, n: int) -> list[str]:
    """The charter's rule written out again: SHA-256 of the lowercased origin host, first 8 bytes
    big-endian, modulo N, plus one; catalogue order."""
    def key(rec):
        host = urlsplit(rec["origin"]["url"]).hostname.lower().encode("utf-8")
        return int.from_bytes(hashlib.sha256(host).digest()[:8], "big") % n + 1
    return [rid for rid, rec in recs.items() if key(rec) == i]


# --- the shard key -------------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 9))
def test_every_record_of_the_catalogue_is_in_exactly_one_shard(n):
    recs = CATALOGUE
    got = [rid for i in range(1, n + 1) for rid in shards.select(recs, i, n)]
    assert sorted(got) == sorted(recs) and len(got) == len(set(got))


def test_one_origin_host_is_one_shard():
    recs = CATALOGUE
    for n in (2, shards.SHARDS):
        by_host: dict[str, set[int]] = {}
        for i in range(1, n + 1):
            for rid in shards.select(recs, i, n):
                by_host.setdefault(shards.origin_host(recs[rid]), set()).add(i)
        assert all(len(s) == 1 for s in by_host.values())


def test_a_record_that_sorts_first_moves_no_other_record():
    # mutation: shard by list position (index % N) -> every record after the insert moves
    first = yaml.safe_load((FIX / "first" / "first.yaml").read_text())
    after = {first["id"]: first, **CATALOGUE}  # load_records order: by path, and 0000/ sorts first
    assert first["id"] < min(CATALOGUE)
    for n in (2, 5, shards.SHARDS):
        old = {rid: i for i in range(1, n + 1) for rid in shards.select(CATALOGUE, i, n)}
        new = {rid: i for i in range(1, n + 1) for rid in shards.select(after, i, n)}
        assert {rid: new[rid] for rid in old} == old


def test_selection_matches_the_rule_and_is_the_same_in_another_process():
    recs = CATALOGUE
    for i in range(1, shards.SHARDS + 1):
        assert shards.select(recs, i, shards.SHARDS) == expected(recs, i, shards.SHARDS)
    code = ("import json; from osd import shards; from osd.records import load_records; r = load_records(); "
            f"print(json.dumps([shards.select(r, i, {shards.SHARDS}) for i in range(1, {shards.SHARDS} + 1)]))")
    env = {**os.environ, "PYTHONHASHSEED": "12345", "PYTHONPATH": str(paths.ROOT / "src")}
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True).stdout
    assert json.loads(out) == [shards.select(recs, i, shards.SHARDS) for i in range(1, shards.SHARDS + 1)]


# --- osd verify --shard ----------------------------------------------------------------------------

@pytest.fixture
def verifier(monkeypatch):
    """The verifier `osd verify` calls, replaced: records each call's ids, verifies nothing."""
    calls = []
    monkeypatch.setattr(cli, "load_records", lambda: CATALOGUE)

    def fake(ids=None, **kw):
        calls.append(ids)
        return [{"record_id": rid, "level": "L1", "origin": {}, "checks": []} for rid in ids or []]
    monkeypatch.setattr(cli, "verify_all", fake)
    return calls


@pytest.mark.parametrize("spec", ["1/12", "7/12", "12/12", "2/3"])
def test_shard_calls_the_verifier_with_exactly_its_ids(verifier, tmp_path, spec):
    # mutation: cmd_verify ignores --shard -> the verifier is called with None (every record)
    i, n = map(int, spec.split("/"))
    out = tmp_path / "ids.txt"
    assert cli.main(["verify", "--shard", spec, "--ids-out", str(out)]) == 0
    assert verifier == [expected(CATALOGUE, i, n)]
    assert out.read_text().split() == expected(CATALOGUE, i, n)


def test_an_empty_shard_calls_nothing(verifier, monkeypatch, tmp_path, capsys):
    recs = load_records(FIX / "records")
    assert expected(recs, 1, 4) == []
    monkeypatch.setattr(cli, "load_records", lambda: recs)
    out = tmp_path / "ids.txt"
    assert cli.main(["verify", "--shard", "1/4", "--ids-out", str(out)]) == 0
    assert verifier == [] and out.read_text() == ""
    assert "shard 1/4: 0 records" in capsys.readouterr().out


@pytest.mark.parametrize("argv", [["--shard", "0/4"], ["--shard", "5/4"], ["--shard", "1/17"], ["--shard", "1/0"],
                                  ["--shard", "3"], ["--shard", "a/b"], ["--shard", "1/2/3"], ["--shard=-1/4"],
                                  ["--shard", ""], ["--shard", "1/2", "acme/demo"]])
def test_malformed_shards_and_ids_with_a_shard_are_refused(verifier, capsys, argv):
    assert cli.main(["verify", *argv]) == 2
    assert verifier == [] and "refused" in capsys.readouterr().out


def test_parse_bounds():
    assert shards.parse("1/1") == (1, 1) and shards.parse("16/16") == (16, 16)
    with pytest.raises(ValueError):
        shards.parse("17/17")


# --- the finishing job: overlay -------------------------------------------------------------------
# Fixture records, N = 3: alpha/one in shard 1, beta/two and delta/four in shard 2, gamma/three in 3.

RECS = load_records(FIX / "records")


def fresh(rid: str, level: str = "L1", when: str = "2026-10-23T07:00:00+00:00") -> dict:
    v = json.loads((FIX / "snapshot" / (rid.replace("/", "__") + ".json")).read_text())
    host = rid.split("/")[0]
    return {**v, "checked_at": when, "level": level,
            "checks": [{"name": "origin-reachable", "level": "L1", "outcome": "pass",
                        "detail": f"HTTP 200 at https://{host}.example/data"}],
            "origin": {**v["origin"], "http_status": 200, "reachability": "ok"},
            "files": [{"path": "a.csv", "url": f"https://{host}.example/a.csv", "bytes": 1000, "sha256": "0" * 64}]}


def artifact(shards_dir: Path, i: int, results: list[dict], n: int = 3, ids: list[str] | None = None) -> Path:
    """A shard's upload as the workflow writes it (ids.txt, verification/, shard.json)."""
    d = shards_dir / f"shard-{i}"
    (d / "verification").mkdir(parents=True)
    for v in results:
        (d / "verification" / (v["record_id"].replace("/", "__") + ".json")).write_text(json.dumps(v))
    ids = [v["record_id"] for v in results] if ids is None else ids
    (d / "ids.txt").write_text("".join(r + "\n" for r in ids))
    (d / "shard.json").write_text(json.dumps({"shard": i, "of": n, "started": 1761202800, "finished": 1761203100}))
    return d


def result(out: Path, rid: str) -> dict:
    return json.loads((out / (rid.replace("/", "__") + ".json")).read_text())


def snapshot_of(rid: str) -> dict:
    return json.loads((FIX / "snapshot" / (rid.replace("/", "__") + ".json")).read_text())


def test_fixture_shards():
    assert [shards.select(RECS, i, 3) for i in (1, 2, 3)] == [["alpha/one"], ["beta/two", "delta/four"], ["gamma/three"]]


def test_a_fresh_file_replaces_the_earlier_one(tmp_path):
    # mutation: overwrite suppressed (copy only when the destination is absent) -> red
    sd, out = tmp_path / "shards", tmp_path / "out"
    artifact(sd, 1, [fresh("alpha/one")])
    artifact(sd, 3, [fresh("gamma/three", "L2")])
    r = shards.overlay(FIX / "snapshot", sd, out, 3, RECS)
    assert result(out, "alpha/one") == fresh("alpha/one") and result(out, "gamma/three")["level"] == "L2"
    assert r["fresh"] == ["alpha/one", "gamma/three"] and sorted(r["accepted"]) == [1, 3]


def test_a_failed_shards_records_keep_their_earlier_files(tmp_path):
    # mutation: destination deleted before the overlay (only fresh files survive) -> red
    sd, out = tmp_path / "shards", tmp_path / "out"
    artifact(sd, 1, [fresh("alpha/one")])
    artifact(sd, 3, [fresh("gamma/three")])
    r = shards.overlay(FIX / "snapshot", sd, out, 3, RECS)    # shard 2 uploaded nothing
    assert result(out, "beta/two") == snapshot_of("beta/two") and result(out, "delta/four") == snapshot_of("delta/four")
    assert r["discarded"] == {2: "no id list (the shard failed, was cancelled or uploaded nothing)"}
    assert r["kept"] == ["beta/two", "delta/four"]
    text = "\n".join(shards.summary_lines(r, 3, RECS, shards.timings(sd, r["accepted"])))
    assert "| 2/3 | 2 | **failed**: no id list" in text
    assert "Shard 2/3 failed (no id list (the shard failed, was cancelled or uploaded nothing)); its records keep" in text
    assert "- beta/two\n- delta/four" in text
    assert "2 of 4 records verified in this run; 2 keep their earlier result." in text
    assert "Records without a fresh result: beta/two delta/four" in text
    assert "| 1/3 | 1 | 5.0 min | 1,000 | alpha/one" in text


@pytest.mark.parametrize("case", ["foreign id", "foreign file", "missing file", "wrong shard.json", "wrong record_id",
                                  "unknown id"])
def test_a_shard_artifact_outside_its_shard_is_discarded(tmp_path, case):
    sd, out = tmp_path / "shards", tmp_path / "out"
    if case == "foreign id":           # shard 3 claims alpha/one, a record of shard 1
        artifact(sd, 3, [fresh("gamma/three"), fresh("alpha/one")])
    elif case == "foreign file":       # a file its id list does not name
        artifact(sd, 3, [fresh("gamma/three"), fresh("alpha/one")], ids=["gamma/three"])
    elif case == "missing file":
        artifact(sd, 2, [fresh("beta/two")], ids=["beta/two", "delta/four"])
    elif case == "wrong shard.json":
        artifact(sd, 3, [fresh("gamma/three")], n=4)
    elif case == "wrong record_id":
        d = artifact(sd, 3, [fresh("gamma/three")])
        (d / "verification" / "gamma__three.json").write_text(json.dumps(fresh("alpha/one")))
    else:
        d = artifact(sd, 3, [fresh("gamma/three")], ids=["gamma/three", "zeta/none"])
    r = shards.overlay(FIX / "snapshot", sd, out, 3, RECS)
    assert r["fresh"] == [] and r["accepted"] == {}
    for rid in RECS:
        assert result(out, rid) == snapshot_of(rid)
    i = 2 if case == "missing file" else 3
    assert "no id list" not in r["discarded"][i]
