"""E49 slice 1: the Python file (`python -m osd.script`), rule table T1-T8 of
docs/program/charters/E49-the-python-file-STRATEGY.md. The golden file is the contract the page
(slice 4) is held equal to."""

import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from osd import script

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "tests" / "fixtures" / "api"
IDS = ["fx/mirrored", "fx/publisher", "fx/signin"]


def test_script_equals_golden(tmp_path):
    """Acceptance 5: three ids (one repeated, T1), date from the argument."""
    out = tmp_path / "osd_fixture.py"
    r = subprocess.run([sys.executable, "-m", "osd.script", *IDS, "fx/mirrored", "--catalog", str(FX / "catalog"),
                        "--today", "2026-11-25", "-o", str(out)], check=False, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert out.read_text() == (FX / "golden.py").read_text()


def test_golden_is_python():
    compile((FX / "golden.py").read_text(), "golden.py", "exec")


def test_unknown_or_feature_id_writes_nothing(tmp_path, capsys):
    for bad in (["fx/none"], ["fx/mirrored#1"]):
        assert script.main([*bad, "--catalog", str(FX / "catalog"), "-o", str(tmp_path / "x.py")]) == 2
    assert not (tmp_path / "x.py").exists()
    assert "fx/none" in capsys.readouterr().err


def _entry(rid, access="anonymous", assets=None):
    return {"record_id": rid, "access": access, "origin_url": f"https://o.invalid/{rid}", "assets": assets or {}}


SUM = {"file:checksum": "1220" + "0" * 64}


@pytest.mark.parametrize("assets,want", [
    ({"a": {**SUM, "alternates": {"mirror": {}}}}, "1 file from our mirror, checked"),
    ({"a": {}, "b": {}}, "2 files from the publisher, no checksum recorded"),
    ({"a": {**SUM, "alternates": {"m": {}}}, "b": SUM, "c": {}}, "3 files: 1 from our mirror and 2 from the publisher, 2 checked"),
    ({"a": {"alternates": {"m": {}}}}, "1 file from the publisher, no checksum recorded"),   # no sha256: mirror not trusted
])
def test_comment_counts_and_sources(assets, want):
    assert script.comment(_entry("p/d", assets=assets)) == want


@pytest.mark.parametrize("access,want", [
    ("registration", "sign-in needed: left out, sign in at https://o.invalid/p/d"),
    ("request", "request needed: left out, ask at https://o.invalid/p/d"),
    ("purchase", "for sale: left out, see https://o.invalid/p/d"),
    ("anonymous", "no file address known: left out, see https://o.invalid/p/d"),
])
def test_comment_left_out(access, want):
    assert script.comment(_entry("p/d", access)) == want


def test_variable_names():
    taken = set()
    got = [script.variable(r, taken) for r in ("a/norne", "b/norne", "c/3d-survey", "d/class", "e/osd", "f/F3.Demo")]
    assert got == ["norne", "norne_2", "d_3d_survey", "class_", "osd_", "f3_demo"]


def test_first_line_and_alignment():
    text = script.render([_entry("p/one"), _entry("p/longer-name")], date(2026, 1, 5))
    lines = text.splitlines()
    assert lines[0] == "# open-subsurface-data, made 5 Jan 2026 for 2 datasets"
    assert lines[5].index("#") == lines[6].index("#") == len('longer_name = osd.get("p/longer-name")') + 2
    assert text.endswith("print(longer_name)\n")
    assert script.render([_entry("p/one")], date(2026, 1, 5)).startswith("# open-subsurface-data, made 5 Jan 2026 for 1 dataset\n")
