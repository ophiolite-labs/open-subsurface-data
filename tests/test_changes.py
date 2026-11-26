"""E54: the site says what changed. build.json (the stamp), changes.json (the entries), the daily note."""

import json
import os
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from osd import changes, cli, paths

FIX = Path(__file__).parent / "fixtures" / "changes"
ENTRIES = FIX / "entries"
SHA = "fccb4d02930c908ede102856b9152f61a98975d7"   # the fixture commit: empty tree, fixed names, 2026-11-26T14:03:00Z


@pytest.fixture
def fixture_repo(tmp_path):
    """A one-commit checkout whose commit is always SHA (git computes it from fixed inputs)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "osd", "GIT_AUTHOR_EMAIL": "osd@example.org",
           "GIT_COMMITTER_NAME": "osd", "GIT_COMMITTER_EMAIL": "osd@example.org",
           "GIT_AUTHOR_DATE": "2026-11-26T14:03:00Z", "GIT_COMMITTER_DATE": "2026-11-26T14:03:00Z"}
    for args in (["init", "-q"], ["-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "fixture"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, env=env)
    assert subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip() == SHA
    return repo


def fixture_build(tmp_path, monkeypatch, root, sha=None, git="git"):
    """osd build over the small fidelity records, with the changes folder and checkout of the test."""
    from test_build import _fixture_build

    monkeypatch.setattr(changes, "ROOT", root)
    monkeypatch.setattr(changes, "CHANGES_DIR", ENTRIES)
    monkeypatch.setattr(changes, "GIT", git)
    if sha:
        monkeypatch.setenv("GITHUB_SHA", sha)
    else:
        monkeypatch.delenv("GITHUB_SHA", raising=False)
    _fixture_build(tmp_path)
    return tmp_path / "catalog"


# ---- Acceptance 1: the stamp ------------------------------------------------------------------------

def test_build_with_github_sha_writes_the_golden_build_json(tmp_path, monkeypatch, fixture_repo):
    out = fixture_build(tmp_path, monkeypatch, fixture_repo, sha=SHA)
    assert json.loads((out / "build.json").read_text()) == json.loads((FIX / "build.json").read_text())
    assert (out / "build.json").read_text() == (FIX / "build.json").read_text()
    assert (out / "changes.json").read_text() == (FIX / "changes.json").read_text()


def test_the_stamp_is_the_commits_date_not_the_clock(fixture_repo):
    a = changes.stamp(fixture_repo, {"GITHUB_SHA": SHA})
    b = changes.stamp(fixture_repo, {})   # no variable: HEAD from git, the same commit
    assert a == b == {"commit": "fccb4d0", "date": "2026-11-26", "time": "14:03 UTC"}


def test_without_git_or_the_variable_no_build_json_and_the_build_succeeds(tmp_path, monkeypatch):
    out = tmp_path / "catalog"
    out.mkdir()
    (out / "build.json").write_text("{}\n")   # an older build's stamp is not left behind
    nowhere = tmp_path / "not-a-checkout"
    nowhere.mkdir()
    fixture_build(tmp_path, monkeypatch, nowhere, git=str(tmp_path / "no-git"))
    assert not (out / "build.json").exists()
    assert json.loads((out / "changes.json").read_text())["changes"]   # the rest of the build is there
    assert (out / "records.json").exists()
    assert changes.stamp(nowhere, {}) is None   # git present, but no checkout here either


# ---- Acceptance 3: a bad entry refuses the build with the file name -----------------------------------

GOOD = {"date": "2026-11-26", "title": "Find datasets in the shop.", "link": "/shop.html", "pr": 91}


def bad_dir(tmp_path, doc: dict) -> Path:
    d = tmp_path / "bad"
    d.mkdir()
    for p in ENTRIES.iterdir():
        (d / p.name).write_bytes(p.read_bytes())
    (d / "2026-11-26-bad-entry.yaml").write_text("".join(f"{k}: {json.dumps(v)}\n" for k, v in doc.items()))
    return d


@pytest.mark.parametrize("doc, says", [
    ({k: v for k, v in GOOD.items() if k != "link"}, "missing link"),
    ({**GOOD, "epic": "E54"}, "unknown key epic"),
    ({**GOOD, "link": "shop.html"}, "does not begin with /"),
    ({**GOOD, "title": "Find datasets " + "x" * 127}, "141 characters, over 140"),
], ids=["missing-key", "extra-key", "link-without-slash", "long-title"])
def test_a_bad_entry_refuses_the_build_naming_its_file(tmp_path, monkeypatch, doc, says):
    from test_build import _fixture_build

    monkeypatch.setattr(changes, "CHANGES_DIR", bad_dir(tmp_path, doc))
    with pytest.raises(changes.ChangeError) as e:
        _fixture_build(tmp_path)
    assert str(e.value).startswith("changes/2026-11-26-bad-entry.yaml: ")
    assert says in str(e.value)
    assert not (tmp_path / "catalog" / "changes.json").exists()


def test_the_good_entry_of_those_tests_passes(tmp_path):
    assert GOOD in changes.load(bad_dir(tmp_path, GOOD))


def test_a_title_of_exactly_140_characters_passes(tmp_path):
    t = "Find datasets " + "x" * 126
    assert len(t) == 140 and {**GOOD, "title": t} in changes.load(bad_dir(tmp_path, {**GOOD, "title": t}))


# ---- Acceptance 4: the committed entries ---------------------------------------------------------------

def test_the_fixture_entries_newest_first():
    assert [(e["date"], e["pr"]) for e in changes.load(ENTRIES)] == [("2026-11-26", 91), ("2026-11-25", 90),
                                                                    ("2026-11-24", 80)]


def test_the_committed_entries_load_and_every_link_answers_in_the_built_site(full_build):
    """Every `link` of changes/ is a page of site/ or a file of the build; an anchor is on that page."""
    entries = changes.load()
    assert len(entries) >= 10
    site = paths.ROOT / "site"
    for e in entries:
        u = urlsplit(e["link"])
        path = u.path + ("index.html" if u.path.endswith("/") else "")
        rel = path.lstrip("/")
        target = full_build / rel[len("data/"):] if rel.startswith("data/") else site / rel
        assert target.is_file(), f"{e['link']} ({e['title']}) does not answer: no {target}"
        if u.fragment and target.suffix == ".html":
            assert f'id="{u.fragment}"' in target.read_text(), f"{e['link']}: no id {u.fragment} on {rel}"
    assert json.loads((full_build / "changes.json").read_text()) == {"changes": entries}


# ---- Acceptance 5: the daily note ----------------------------------------------------------------------

def test_osd_changes_since_top_3_equals_the_golden_note(fixture_repo, monkeypatch, capsys):
    real = changes.stamp
    monkeypatch.setattr(changes, "stamp", lambda *a, **k: real(fixture_repo, {}))
    monkeypatch.setattr(changes, "utc_today", lambda: date(2026, 11, 26))
    assert cli.main(["changes", "--since", "2026-11-25", "--top", "3", "--dir", str(ENTRIES)]) == 0
    assert capsys.readouterr().out == (FIX / "note.txt").read_text()


def test_the_note_takes_one_entry_per_pull_request_and_stops_at_top():
    es = [{"date": "2026-11-26", "title": t, "link": "/", "pr": pr} for t, pr in (("a", 2), ("b", 2), ("c", 1))]
    n = changes.note(es, "2026-11-01", top=1, today=date(2026, 11, 26), build=None)
    assert "- a\n" in n and "- b" not in n and "- c" not in n
    n = changes.note(es, "2026-11-01", top=3, today=date(2026, 11, 26), build=None)
    assert "- a\n" in n and "- b" not in n and "- c\n" in n


def test_the_note_with_nothing_new_says_so():
    n = changes.note(changes.load(ENTRIES), "2026-12-01", today=date(2026, 12, 2), build=None)
    assert "Nothing new on the site since 2026-12-01." in n
