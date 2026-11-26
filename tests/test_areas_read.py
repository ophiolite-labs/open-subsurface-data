"""E51 slice 1: licences read per country from the regulator (charter E51-licences-per-country.md, strategy
-STRATEGY.md). Norway (Sodir) against a small served copy of its three layers (fixtures/areas/licence/sodir.json),
the guards that keep the committed file, the count and records[].blocks, the workflow. No network."""

import copy
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest
import yaml

from osd import areas, cli, paths
from osd.build import build

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures" / "areas"
LIC = FIX / "licence"
SERVICE = "https://factmaps.sodir.no/api/rest/services/Factmaps/FactMapsWGS84/FeatureServer"
TODAY = "2026-11-25"


def serve(layers: dict, fail: str | None = None, service: str = SERVICE):
    """`get` answering ArcGIS FeatureServer requests from {layer: {description, features}}; `fail`: a URL part
    whose request answers HTTP 503."""
    from osd.verifier.layers import Incomplete

    calls = []

    def get(url: str) -> bytes:
        calls.append(url)
        if fail and fail in url:
            raise Incomplete(f"HTTP 503 for {url}")
        u = urlsplit(url)
        assert url.startswith(service + "/"), url
        layer, _, op = u.path.removeprefix(urlsplit(service).path + "/").partition("/")
        lay, q = layers[layer], dict(parse_qsl(u.query))
        feats = sorted(lay["features"], key=lambda f: f["attributes"]["OBJECTID"])
        if not op:
            return json.dumps(lay["description"]).encode()
        if q.get("returnCountOnly") == "true":
            return json.dumps({"count": len(feats)}).encode()
        if q.get("returnIdsOnly") == "true":
            return json.dumps({"objectIdFieldName": "OBJECTID",
                               "objectIds": [f["attributes"]["OBJECTID"] for f in feats]}).encode()
        off, n = int(q["resultOffset"]), int(q["resultRecordCount"])
        d = lay["description"]
        return json.dumps({"geometryType": d["geometryType"], "spatialReference": d["spatialReference"],
                           "features": feats[off:off + n]}).encode()
    get.calls = calls
    return get


def sodir() -> dict:
    return json.loads((LIC / "sodir.json").read_text())


@pytest.fixture
def adir(tmp_path) -> Path:
    """An areas dir holding the real areas/licence/no.yaml and nothing read yet."""
    (tmp_path / "licence").mkdir()
    shutil.copy(paths.AREAS_DIR / "licence" / "no.yaml", tmp_path / "licence" / "no.yaml")
    return tmp_path


def read(adir: Path, layers: dict | None = None, **kw) -> dict:
    return areas.read_to_file("no", serve(layers or sodir(), **kw), TODAY, adir)


# --- acceptance 2: the golden file, pages, the current filter, the join ---------------------------------

def test_read_writes_the_golden_file_across_pages(adir):
    get = serve(sodir())
    s = areas.read_to_file("no", get, TODAY, adir)
    assert s["status"] == "written" and (s["before"], s["after"]) == (0, 4)
    assert (adir / "licence" / "no.geojson").read_bytes() == (LIC / "no.geojson").read_bytes()
    assert sum("/616/query" in u and "resultOffset" in u for u in get.calls) == 3   # 5 rows, 2 a page
    doc = json.loads((LIC / "no.geojson").read_text())
    props = {f["properties"]["name"]: f["properties"] for f in doc["features"]}
    assert props["PL 001"] == {"area_id": "NO:101", "name": "PL 001", "country": "NO", "blocks": ["1/2", "1/12"]}
    assert json.loads((LIC / "no.geojson").read_text())["features"][1]["geometry"]["type"] == "MultiPolygon"


def test_relinquished_licence_is_not_read(adir):
    read(adir)
    names = [f["properties"]["name"] for f in json.loads((adir / "licence" / "no.geojson").read_text())["features"]]
    assert names == ["PL 001", "PL 002 B", "PL 015", "PL 004"] and "PL 003" not in names


def test_unchanged_read_leaves_the_file(adir):
    read(adir)
    before = (adir / "licence" / "no.geojson").read_bytes()
    s = areas.read_to_file("no", serve(sodir()), "2026-12-02", adir)
    assert s["status"] == "unchanged" and (adir / "licence" / "no.geojson").read_bytes() == before


# --- acceptance 3: empty, failed and shrunken reads leave the committed file -----------------------------

def _committed(adir: Path, n_extra: int = 0) -> bytes:
    """Commit the fixture read, with n_extra more licences (copies of 001 under other ids) when asked."""
    layers = sodir()
    for k in range(n_extra):
        f = copy.deepcopy(layers["616"]["features"][0])
        f["attributes"].update(OBJECTID=100 + k, prlNpdidLicence=900 + k, prlName=f"9{k:02d}")
        layers["616"]["features"].append(f)
        layers["615"]["features"].append({"attributes": {"OBJECTID": 100 + k, "prlName": f"9{k:02d}",
                                                         "blcNpdidBlock": 5}, "geometry": None})
    assert read(adir, layers)["status"] == "written"
    return (adir / "licence" / "no.geojson").read_bytes()


def _refused(adir: Path, before: bytes, s: dict, says: str) -> None:
    assert s["status"] == "refused" and says in s["finding"], s
    assert (adir / "licence" / "no.geojson").read_bytes() == before


def test_empty_read_leaves_the_file(adir):
    before = _committed(adir)
    layers = sodir()
    layers["616"]["features"] = []
    _refused(adir, before, read(adir, layers), "counts 0 features")


def test_http_error_leaves_the_file(adir):
    before = _committed(adir)
    _refused(adir, before, read(adir, fail="resultOffset=2"), "HTTP 503")


def test_a_fifth_missing_is_read(adir):
    _committed(adir, n_extra=1)   # 5 committed; 1 missing is exactly a fifth
    s = read(adir)
    assert s["status"] == "written" and (s["before"], s["after"], s["removed"]) == (5, 4, 1)


def test_more_than_a_fifth_missing_is_refused(adir):
    before = _committed(adir, n_extra=2)   # 6 committed; 2 missing is a third
    _refused(adir, before, read(adir), "2 of the 6 committed licences are missing")


def test_same_count_other_ids_is_refused(adir):
    before = _committed(adir)
    layers = sodir()
    for f in layers["616"]["features"]:
        f["attributes"]["prlNpdidLicence"] += 1000
    _refused(adir, before, read(adir, layers), "4 of the 4 committed licences are missing")


def _break(case: str, layers: dict) -> None:
    f616, f615, f802 = (layers[k]["features"] for k in ("616", "615", "802"))
    if case == "repeated id":
        f616[3]["attributes"]["prlNpdidLicence"] = 101
    elif case == "no name":
        f616[0]["attributes"]["prlName"] = ""
    elif case == "filter field gone":
        for f in f616:
            del f["attributes"]["prlStatus"]
    elif case == "licence without blocks":
        layers["615"]["features"] = [f for f in f615 if f["attributes"]["prlName"] != "015"]
    elif case == "block row of no current licence":
        f615[0]["attributes"]["prlName"] = "003"
    elif case == "block not in the block layer":
        layers["802"]["features"] = [f for f in f802 if f["attributes"]["blcNpdidBlock"] != 4]
    elif case == "block named twice":
        f802.append({"attributes": {"OBJECTID": 99, "blcNpdidBlock": 1, "blcName": "1/2 X"}, "geometry": None})
    elif case == "not WGS84":
        layers["616"]["description"]["spatialReference"] = {"wkid": 23031}
    elif case == "no polygon":
        f616[0]["geometry"] = {"rings": [[[2, 58], [3, 59], [2, 58]]]}
    elif case == "positions outside WGS84":   # metres served under a WGS84 label
        f616[0]["geometry"] = {"rings": [[[500000, 6400000], [500000, 6410000], [510000, 6410000],
                                          [510000, 6400000], [500000, 6400000]]]}


GUARDS = [("repeated id", "read twice"), ("no name", "without"), ("filter field gone", "field 'prlStatus'"),
          ("licence without blocks", "have no block rows"), ("block row of no current licence", "not a current"),
          ("block not in the block layer", "is not in block layer 802"), ("block named twice", "named"),
          ("not WGS84", "not in WGS84"), ("no polygon", "licence 001"),
          ("positions outside WGS84", "licence 001: ")]


@pytest.mark.parametrize(("case", "says"), GUARDS)
def test_refused_reads_leave_the_file(adir, case, says):
    before = _committed(adir)
    layers = sodir()
    _break(case, layers)
    _refused(adir, before, read(adir, layers), says)


def test_config_without_the_current_filter_is_refused(adir):
    p = adir / "licence" / "no.yaml"
    cfg = yaml.safe_load(p.read_text())
    del cfg["licences"]["current"]
    p.write_text(yaml.safe_dump(cfg))
    s = read(adir)
    assert s["status"] == "refused" and "licences.current" in s["finding"]
    assert not (adir / "licence" / "no.geojson").exists()


def licence_only(tmp_path: Path) -> Path:
    """The real licence file and areas/SOURCES.md, without the 21 MB of other kinds."""
    d = tmp_path / "areas"
    (d / "licence").mkdir(parents=True)
    shutil.copy(paths.AREAS_DIR / "SOURCES.md", d / "SOURCES.md")
    shutil.copy(REAL, d / "licence" / "no.geojson")
    return d


def test_validate_refuses_a_licence_file_not_in_sources_md(tmp_path):
    d = licence_only(tmp_path)
    assert areas.validate_areas(d) == []
    f = d / "licence" / "no.geojson"
    doc = json.loads(f.read_text())
    doc["source"]["credit"] = "Data from Sodir"
    f.write_text(json.dumps(doc))
    found = areas.validate_areas(d)
    assert [p.message[:40] for p in found] == ["source/credit is not written in areas/SO"]


# --- acceptance 4: the count and the row -----------------------------------------------------------------

@pytest.fixture(scope="module")
def built_licences(tmp_path_factory) -> Path:
    tmp = tmp_path_factory.mktemp("lic")
    shutil.copytree(FIX / "areas", tmp / "areas")
    (tmp / "areas" / "licence").mkdir()
    shutil.copy(LIC / "xa.geojson", tmp / "areas" / "licence" / "xa.geojson")
    out = tmp / "catalog"
    (tmp / "noverif").mkdir()
    build(out, tmp / "noverif", now=datetime(2026, 11, 25, tzinfo=UTC), mirror_dir=tmp / "nomirror",
          records_dir=FIX / "records", source_commit=None, verification_commit=None,
          starters_dir=tmp / "nostarters", areas_dir=tmp / "areas", outlines_dir=FIX / "outlines")
    return out


def test_licence_holding_a_well_is_written_and_the_other_not(built_licences):
    index = json.loads((built_licences / "areas.json").read_text())
    assert not list(areas.validator("index").iter_errors(index))
    lic = index["kinds"]["licence"]
    assert [(a["area_id"], a["ids"]) for a in lic["areas"]] == [("XA:P1", ["fixture/register"])]
    assert lic["sources"][0]["file"] == "licence/xa.geojson" and lic["sources"][0]["retrieved"] == "2026-11-25"
    drawn = json.loads((built_licences / "areas-licence.geojson").read_text())
    assert [f["properties"]["area_id"] for f in drawn["features"]] == ["XA:P1"]


def test_each_kind_has_its_own_index_file_equal_to_areas_json(built_licences):
    index = json.loads((built_licences / "areas.json").read_text())
    for k, entry in index["kinds"].items():   # J13: the shop's first load reads areas-country.json only
        got = json.loads((built_licences / f"areas-{k}.json").read_text())
        assert got == {"version": "areas/1", "kind": k, **entry}
    assert sorted(p.name for p in built_licences.glob("areas-*.json")) == sorted(f"areas-{k}.json" for k in index["kinds"])


def test_record_blocks_are_its_licences_blocks(built_licences):
    recs = {r["id"]: r for r in json.loads((built_licences / "records.json").read_text())["records"]}
    assert recs["fixture/register"]["areas"]["licence"] == ["XA:P1"]
    assert recs["fixture/register"]["blocks"] == ["7/9", "7/12"]
    assert all("blocks" not in r for rid, r in recs.items() if rid != "fixture/register")


def test_26_licences_give_no_block_list():
    held = {f"NO:{i}": [f"{i}/1"] for i in range(30)}
    assert areas.record_blocks([f"NO:{i}" for i in range(25)], held)[:3] == ["0/1", "1/1", "2/1"]
    assert areas.record_blocks([f"NO:{i}" for i in range(26)], held) == []
    assert areas.record_blocks([], held) == []


# --- acceptance 5 and 8: the real file, the real catalogue, offline --------------------------------------

REAL = paths.AREAS_DIR / "licence" / "no.geojson"


def test_real_licence_file_under_5_mb_and_valid(tmp_path):
    assert REAL.stat().st_size < 5_000_000
    assert areas.validate_areas(licence_only(tmp_path)) == []
    doc = json.loads(REAL.read_text())
    assert doc["source"]["url"].endswith("/FeatureServer/616") and len(doc["features"]) > 400


def test_real_norway_licences_hold_datasets(full_build):
    index = json.loads((full_build / "areas.json").read_text())
    held = index["kinds"]["licence"]["areas"]
    assert held and all(a["area_id"].startswith("NO:") for a in held)
    recs = json.loads((full_build / "records.json").read_text())["records"]
    assert any(r.get("blocks") for r in recs)


def test_check_never_reads_regulators(monkeypatch, tmp_path):
    assert "areas read" not in (ROOT / "Makefile").read_text()
    assert "areas read" not in (ROOT / ".github" / "workflows" / "ci.yml").read_text()

    def no_network(*a, **k):
        raise AssertionError("network reached")
    import socket
    import urllib.request
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    d = licence_only(tmp_path)
    assert areas.validate_areas(d) == [] and areas.AreaSet.load(d).features("licence")
    shutil.copytree(FIX / "areas", tmp_path / "fx")
    shutil.copytree(d / "licence", tmp_path / "fx" / "licence")
    out = tmp_path / "catalog"
    build(out, tmp_path / "noverif", now=datetime(2026, 11, 25, tzinfo=UTC), mirror_dir=tmp_path / "nomirror",
          records_dir=FIX / "records", source_commit=None, verification_commit=None,
          starters_dir=tmp_path / "nostarters", areas_dir=tmp_path / "fx", outlines_dir=FIX / "outlines")
    assert "licence" in json.loads((out / "areas.json").read_text())["kinds"]


# --- acceptance 7: the workflow and its texts ------------------------------------------------------------

def test_workflow_never_pushes_main_and_states_its_permissions():
    text = (ROOT / ".github" / "workflows" / "areas.yml").read_text()
    wf = yaml.safe_load(text)
    on = wf.get("on", wf.get(True))
    assert set(on) == {"schedule", "workflow_dispatch", "pull_request"}
    assert on["schedule"][0]["cron"].split()[2:] == ["*", "*", "1"]   # weekly
    assert wf["permissions"] == {"contents": "write", "pull-requests": "write", "issues": "write"}
    assert "push origin main" not in text and "git push" in text and "HEAD:refs/heads/areas-read" in text
    assert "uv run osd areas read no" in text


def test_pr_and_issue_texts(adir):
    s = read(adir)
    title, body = areas.pr_text([s], TODAY)
    assert title == "Licences read 2026-11-25" and body.startswith("What a user can do after this merges:")
    assert "| NO | written | 0 | 4 | +4 -0 | 2026-11-25 |" in body
    r = read(adir, fail="/615/")
    t, comment = areas.issue_text(r, TODAY)
    assert t == "Licences: NO read refused" and "stays as read on 2026-11-25" in comment and "HTTP 503" in comment


def test_cli_writes_the_summary_and_exits_1_on_a_refusal(adir, tmp_path):
    import argparse
    a = argparse.Namespace(country=["no"], areas=str(adir), summary=str(tmp_path / "sum"))
    assert cli.cmd_areas_read(a, get=serve(sodir()), today=TODAY) == 0
    assert cli.cmd_areas_read(a, get=serve(sodir(), fail="/802"), today=TODAY) == 1
    assert (tmp_path / "sum" / "issue-no.md").read_text().startswith("Licences: NO read refused\n")
    assert json.loads((tmp_path / "sum" / "no.json").read_text())["status"] == "refused"


def test_http_get_tries_a_dropped_page_again_and_stops_at_a_4xx():
    import urllib.error

    from osd.verifier.layers import Incomplete
    tries = []

    def opener(url):
        tries.append(url)
        if url.endswith("/robots.txt"):
            return b""
        if "dropped" in url and tries.count(url) < 3:
            raise urllib.error.URLError("Remote end closed connection without response")
        if "gone" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return b"ok"
    get = areas.http_get(opener=opener, sleep=lambda s: None)
    assert get("https://x.example/dropped") == b"ok" and tries.count("https://x.example/dropped") == 3
    with pytest.raises(Incomplete, match="HTTP 404"):
        get("https://x.example/gone")
    assert tries.count("https://x.example/gone") == 1


# --- slice 3: the United States offshore (BOEM): blocks on the lease row, NAD83 -----------------------

BOEM = "https://gis.boem.gov/arcgis/rest/services/BOEM_BSEE/MMC_Layers/MapServer"


def boem() -> dict:
    return json.loads((LIC / "boem.json").read_text())


@pytest.fixture
def usdir(tmp_path) -> Path:
    (tmp_path / "licence").mkdir()
    shutil.copy(paths.AREAS_DIR / "licence" / "us.yaml", tmp_path / "licence" / "us.yaml")
    return tmp_path


def read_us(usdir: Path, layers: dict | None = None) -> dict:
    return areas.read_to_file("us", serve(layers or boem(), service=BOEM), TODAY, usdir)


def test_boem_read_writes_the_golden_file(usdir):
    s = read_us(usdir)
    assert s["status"] == "written" and (s["before"], s["after"]) == (0, 3)
    assert (usdir / "licence" / "us.geojson").read_bytes() == (LIC / "us.geojson").read_bytes()
    props = [f["properties"] for f in json.loads((LIC / "us.geojson").read_text())["features"]]
    assert props == [
        {"area_id": "US:00016", "name": "OCS-00016", "country": "US", "blocks": ["WD31"]},
        {"area_id": "US:G02883", "name": "OCS-G02883", "country": "US", "blocks": ["SM127"]},
        {"area_id": "US:G35001", "name": "OCS-G35001", "country": "US", "blocks": ["HIA 384"]}]


def test_boem_renewable_lease_is_not_read(usdir):
    read_us(usdir)
    assert "A0501" not in (usdir / "licence" / "us.geojson").read_text()


@pytest.mark.parametrize(("case", "says"), [("no block", "have no block field ACLABS"),
                                            ("served in WGS84", "is not in NAD83")])
def test_boem_refused_reads_leave_the_file(usdir, case, says):
    assert read_us(usdir)["status"] == "written"
    before = (usdir / "licence" / "us.geojson").read_bytes()
    layers = boem()
    if case == "no block":
        layers["15"]["features"][0]["attributes"]["ACLABS"] = " "
    else:
        layers["15"]["description"]["spatialReference"] = {"wkid": 4326}
    s = read_us(usdir, layers)
    assert s["status"] == "refused" and says in s["finding"], s
    assert (usdir / "licence" / "us.geojson").read_bytes() == before


def test_config_refuses_a_projected_wkid(usdir):
    p = usdir / "licence" / "us.yaml"
    p.write_text(p.read_text().replace("wkid: 4269", "wkid: 3857"))
    assert "wkid 3857 is not one of the geographic" in read_us(usdir)["finding"]


def test_real_us_file_under_5_mb_and_valid(tmp_path):
    us = paths.AREAS_DIR / "licence" / "us.geojson"
    assert us.stat().st_size < 5_000_000
    d = licence_only(tmp_path)
    shutil.copy(us, d / "licence" / "us.geojson")
    assert areas.validate_areas(d) == []
    doc = json.loads(us.read_text())
    assert doc["source"]["url"].endswith("/MapServer/15") and len(doc["features"]) > 1500
    total = sum(p.stat().st_size for p in (paths.AREAS_DIR / "licence").glob("*.geojson"))
    assert total < 10_000_000   # acceptance 8: the licence files of all countries together
