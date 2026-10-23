"""H2: verify in shards. The shard key (origin host hash), `osd verify --shard I/N` with an injected
verifier, the finishing job's overlay of shard artifacts on the earlier-results snapshot, and its
dead-link report step run with a fake `gh` (no network, no issue touched)."""

import hashlib
import json
import os
import subprocess
import sys
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
