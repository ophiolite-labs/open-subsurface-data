import copy
import gzip
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime, timedelta

import pytest
from jsonschema import Draft202012Validator, ValidationError

from osd import paths
from osd.build import build
from osd.cli import status_lines
from osd.records import load_record, load_records
from osd.verifier.listings import ListingError, read_listing, stated_checksum
from osd.verify import (
    USER_AGENT,
    ByteBudget,
    Fetched,
    FetchError,
    Pacer,
    is_stale,
    level_from_checks,
    load_samples,
    verify_all,
    verify_record,
)

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)
REC = load_record(paths.RECORDS_DIR / "terranubis" / "f3-demo-2020.yaml")
BASE = "https://fixture.test/"
CHALLENGE = b"<html><head><title>Just a moment...</title></head><body>cf-chl</body></html>"


def fetch_ok(url):
    return Fetched(200, url, "text/html", 12)


def fetch_dead(url):
    return Fetched(404, url, "", 12)


class Counting:
    """A fake fetcher answering from a list, one answer per call; the last answer repeats."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), 0

    def __call__(self, url):
        a = self.answers[min(self.calls, len(self.answers) - 1)]
        self.calls += 1
        return a if isinstance(a, Fetched) else a(url)


def timeout(url):
    return Fetched(0, url, "", 20000, error="timeout")


def dir_opener(root, calls=None):
    """Serve https://fixture.test/<path> from a local directory, in small chunks."""

    def open_(url):
        if calls is not None:
            calls.append(url)
        p = root / url[len(BASE):].split("?")[0] if url.startswith(BASE) else None
        if p is None or not p.is_file():
            raise FetchError(url, 404)
        data = p.read_bytes()
        return iter([data[i:i + 7] for i in range(0, len(data), 7)])

    return open_


def l2_fixture(tmp_path, files=None, licence="Licence text, version one."):
    files = files or {"a.sgy": b"alpha" * 100, "b.las": b"bravo" * 33, "c.csv": b"x,y\n1,2\n"}
    for name, data in files.items():
        (tmp_path / "data" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / name).write_bytes(data)
    (tmp_path / "data" / "README.txt").write_text("not in the sample")
    listing = [{"path": f"data/{n}", "href": f"data/{n}"} for n in [*files, "README.txt"]]
    (tmp_path / "index.json").write_text(json.dumps({"files": listing}))
    (tmp_path / "licence.html").write_text(
        f"<html><head><script>var t={datetime.now().timestamp()}</script></head><body><p>{licence}</p></body></html>")
    rec = copy.deepcopy(REC)
    rec["origin"]["manifest_url"] = BASE + "index.json"
    rec["licence"]["url"] = BASE + "licence.html"
    return rec


SAMPLE = ["*.sgy", "*.las", "*.csv"]


def outcome(v, name):
    return next(c for c in v["checks"] if c["name"] == name)


# --- L1: reachability classes ------------------------------------------------------------

@pytest.mark.parametrize("answer,level,origin_outcome,needle", [
    (Fetched(200, "https://terranubis.com/x", "text/html", 5), "L1", "pass", "HTTP 200"),
    (Fetched(403, "https://terranubis.com/x", "text/html", 5, body=CHALLENGE), "L0", "skip",
     "blocked from this runner"),
    (Fetched(404, "https://terranubis.com/x", "", 5), "L0", "fail", "HTTP 404"),
    (Fetched(0, "https://terranubis.com/x", "", 20000, error="timeout"), "L0", "fail", "timeout"),
], ids=["ok", "blocked", "dead", "timeout"])
def test_classification_four_fetchers(answer, level, origin_outcome, needle):
    v = verify_record(REC, Counting(answer), None, now=NOW)
    c = outcome(v, "origin-reachable")
    assert (v["level"], c["outcome"]) == (level, origin_outcome)
    assert needle in c["detail"]


def test_timeout_is_retried_once():
    f = Counting(timeout)
    v = verify_record(REC, f, None, now=NOW)
    assert f.calls == 2
    assert v["origin"]["reachability"] == "dead"


def test_timeout_then_ok_is_L1():
    v = verify_record(REC, Counting(timeout, fetch_ok), None, now=NOW)
    assert v["level"] == "L1"


def test_dns_failure_is_dead_without_retry():
    f = Counting(Fetched(0, REC["origin"]["url"], "", 3, error="dns"))
    v = verify_record(REC, f, None, now=NOW)
    assert (f.calls, v["level"], v["origin"]["reachability"]) == (1, "L0", "dead")


@pytest.mark.parametrize("status", [200, 503])
def test_challenge_body_is_blocked_at_any_status(status):
    v = verify_record(REC, Counting(Fetched(status, REC["origin"]["url"], "text/html", 5, body=CHALLENGE)),
                      None, now=NOW)
    assert (v["origin"]["reachability"], v["level"]) == ("blocked", "L0")


def test_blocked_since_keeps_the_first_date():
    blocked = Counting(Fetched(403, REC["origin"]["url"], "text/html", 5))
    first = verify_record(REC, blocked, None, now=NOW - timedelta(days=9))
    second = verify_record(REC, blocked, None, now=NOW, previous=first)
    assert second["origin"]["blocked_since"] == first["checked_at"]
    assert "blocked since 2026-10-14" in outcome(second, "origin-reachable")["detail"]
    healed = verify_record(REC, fetch_ok, None, now=NOW, previous=second)
    again = verify_record(REC, blocked, None, now=NOW + timedelta(days=1), previous=healed)
    assert again["origin"]["blocked_since"] == again["checked_at"]


@pytest.mark.parametrize("status", [401, 410, 500])
def test_every_other_status_is_dead(status):
    v = verify_record(REC, Counting(Fetched(status, REC["origin"]["url"], "", 5)), None, now=NOW)
    assert (v["origin"]["reachability"], v["level"]) == ("dead", "L0")


def test_moved_host_passes_with_hint():
    v = verify_record(REC, Counting(Fetched(200, "https://elsewhere.example/x", "text/html", 5)), None, now=NOW)
    c = outcome(v, "origin-reachable")
    assert (v["origin"]["reachability"], c["outcome"]) == ("moved", "pass")
    assert "elsewhere.example" in c["detail"] and "known_issues" in c["detail"]


def test_reachable_origin_with_placeholder_outline_is_L1():
    outline = json.loads(paths.outline_path(REC["id"]).read_text())
    v = verify_record(REC, fetch_ok, outline, now=NOW)
    assert v["level"] == "L1"
    names = {c["name"]: c["outcome"] for c in v["checks"]}
    assert names["origin-reachable"] == "pass"
    assert names["outline-derived"] == "fail"  # approximate: true


def test_dead_origin_is_L0():
    v = verify_record(REC, fetch_dead, None, now=NOW)
    assert v["level"] == "L0"


# --- L2: files and licence ---------------------------------------------------------------

def test_l2_checksums_match_sha256sum(tmp_path):
    rec = l2_fixture(tmp_path)
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert len(v["files"]) == 3
    for f in v["files"]:
        local = tmp_path / f["path"]
        expected = subprocess.run(["sha256sum", str(local)], capture_output=True, text=True,
                                  check=True).stdout.split()[0]
        assert f["sha256"] == expected
        assert f["bytes"] == local.stat().st_size
    assert outcome(v, "files-checksummed")["outcome"] == "pass"
    assert outcome(v, "licence-text-captured")["outcome"] == "pass"
    assert v["level"] == "L2"


def test_only_allow_listed_files_are_hashed(tmp_path):
    rec = l2_fixture(tmp_path)
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=["*.las"])
    assert [f["path"] for f in v["files"]] == ["data/b.las"]


def test_no_sample_stays_L1(tmp_path):
    rec = l2_fixture(tmp_path)
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=None)
    c = outcome(v, "files-checksummed")
    assert (c["outcome"], v["level"]) == ("skip", "L1")
    assert "samples.yaml" in c["detail"]


def test_sample_cut_at_byte_budget(tmp_path):
    rec = l2_fixture(tmp_path)
    budget = ByteBudget(600)  # a.sgy is 500 bytes, b.las 165: the second cannot fit
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE,
                      budget=budget)
    assert [f["path"] for f in v["files"]] == ["data/a.sgy"]
    assert "sample cut" in outcome(v, "files-checksummed")["detail"]
    assert budget.used <= 600


def test_robots_disallow_skips_l2(tmp_path):
    rec = l2_fixture(tmp_path)
    (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /index.json\n")
    calls = []
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path, calls), sample=SAMPLE)
    c = outcome(v, "files-checksummed")
    assert c["outcome"] == "skip" and "robots.txt" in c["detail"]
    assert BASE + "index.json" not in calls


def test_empty_selection_fails(tmp_path):
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=["*.zip"])
    assert (outcome(v, "files-checksummed")["outcome"], v["level"]) == ("fail", "L1")
    assert "files" not in v


def test_failed_file_fetch_prevents_L2(tmp_path):
    rec = l2_fixture(tmp_path)
    (tmp_path / "data" / "b.las").unlink()
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    c = outcome(v, "files-checksummed")
    assert (c["outcome"], v["level"]) == ("fail", "L1")
    assert "data/b.las" in c["detail"]


def test_failed_or_absent_licence_prevents_L2(tmp_path):
    rec = l2_fixture(tmp_path)
    (tmp_path / "licence.html").unlink()
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert (outcome(v, "licence-text-captured")["outcome"], v["level"]) == ("fail", "L1")
    del rec["licence"]["url"]
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert (outcome(v, "licence-text-captured")["outcome"], v["level"]) == ("skip", "L1")
    (tmp_path / "licence.html").write_bytes(CHALLENGE)
    rec["licence"]["url"] = BASE + "licence.html"
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert (outcome(v, "licence-text-captured")["outcome"], v["level"]) == ("fail", "L1")


def test_licence_text_change_is_a_finding(tmp_path):
    rec = l2_fixture(tmp_path, licence="Licence text, version one.")
    first = verify_record(rec, fetch_ok, None, now=NOW - timedelta(days=3), opener=dir_opener(tmp_path), sample=SAMPLE)
    assert outcome(first, "licence-text-captured")["detail"].startswith("26 characters captured")
    assert first["licence_text"] == "Licence text, version one."
    l2_fixture(tmp_path, licence="Licence text, version one.")  # new script timestamp, same text
    same = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE, previous=first)
    assert "changed" not in outcome(same, "licence-text-captured")["detail"]  # script churn ignored
    l2_fixture(tmp_path, licence="Licence text, version two.")
    second = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE, previous=first)
    c = outcome(second, "licence-text-captured")
    assert c["outcome"] == "pass"
    assert c["detail"] == "licence text changed since 2026-10-20"
    assert second["licence_text_sha256"] != first["licence_text_sha256"]


def test_verify_all_compares_with_the_previous_run(tmp_path, monkeypatch):
    rec = l2_fixture(tmp_path)
    monkeypatch.setattr("osd.verify.load_records", lambda: {rec["id"]: rec})
    monkeypatch.setattr("osd.verify.load_samples", lambda: {rec["id"]: SAMPLE})
    out = tmp_path / "verification"
    verify_all(fetch=fetch_ok, opener=dir_opener(tmp_path), out_dir=out)
    l2_fixture(tmp_path, licence="Rewritten terms.")
    (v,) = verify_all(fetch=fetch_ok, opener=dir_opener(tmp_path), out_dir=out)
    assert outcome(v, "licence-text-captured")["detail"].startswith("licence text changed since")


# --- rate and identity -------------------------------------------------------------------

def test_pacer_waits_two_seconds_per_host():
    t, slept = [100.0], []
    p = Pacer(clock=lambda: t[0], sleep=lambda s: (slept.append(s), t.__setitem__(0, t[0] + s)))
    p.wait("https://a.example/1")
    p.done("https://a.example/1")
    t[0] += 0.5
    p.wait("https://b.example/1")  # another host: no pause
    p.done("https://b.example/1")
    p.wait("https://a.example/2")
    assert slept == [pytest.approx(1.5)]


def test_user_agent_names_the_repository():
    assert "github.com/ophiolite-labs/open-subsurface-data" in USER_AGENT


# --- schema, build, status ---------------------------------------------------------------

def schema(name):
    return Draft202012Validator(json.loads((paths.SCHEMA_DIR / name).read_text()))


def test_verification_record_matches_schema(tmp_path):
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert v["level"] == "L2"
    schema("verification.schema.json").validate(v)
    for f in (timeout, Fetched(403, "https://x", "", 1, body=CHALLENGE)):
        schema("verification.schema.json").validate(verify_record(REC, Counting(f), None, now=NOW))
    cut = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path),
                        sample=SAMPLE, budget=ByteBudget(600))
    schema("verification.schema.json").validate(cut)


def test_v1_verification_record_still_validates():
    v1 = {"record_id": "equinor/volve", "checked_at": "2026-10-23T12:00:00+00:00", "tool_version": "0.1.0",
          "level": "L1", "checks": [{"name": "origin-reachable", "level": "L1", "outcome": "pass",
                                     "detail": "HTTP 200"}],
          "origin": {"http_status": 200, "final_url": "https://x", "content_type": "text/html", "elapsed_ms": 3}}
    schema("verification.schema.json").validate(v1)


def test_samples_name_records_with_a_listing():
    recs = load_records()
    samples = load_samples()
    assert len(samples) >= 3
    for rid, globs in samples.items():
        assert recs[rid]["origin"].get("manifest_url"), rid
        if isinstance(globs, str):   # E23: a sentence saying why nothing is sampled
            assert globs.strip(), rid
        else:
            assert globs and all(isinstance(g, str) and g for g in globs), rid


def test_record_schema_has_no_tool_policy():
    assert "verification" not in schema("record.schema.json").schema["properties"]  # OSD-D11


def test_stale_after_30_days():
    assert not is_stale("2026-09-24T12:00:00+00:00", NOW)
    assert is_stale("2026-09-22T12:00:00+00:00", NOW)
    assert is_stale(None, NOW)


def test_records_json_levels_equal_status_levels(tmp_path):
    vdir = tmp_path / "verification"
    vdir.mkdir()
    levels = {"equinor/volve": "L1", "sodir/factpages": "L2", "seg/open-data-wiki": "L0"}
    for rid, lv in levels.items():
        origin = {"reachability": "blocked", "blocked_since": "2026-10-20T00:00:00+00:00"} if lv == "L0" else {}
        (vdir / (rid.replace("/", "__") + ".json")).write_text(json.dumps(
            {"record_id": rid, "checked_at": "2026-08-01T00:00:00+00:00", "tool_version": "t",
             "level": lv, "checks": [], "origin": origin}))
    out = tmp_path / "catalog"
    build(out, vdir, now=NOW)
    published = {r["id"]: (r["level"], r["stale"], (r["blocked_since"] or "")[:10])
                 for r in json.loads((out / "records.json").read_text())["records"]}
    printed = {}
    for line in status_lines(vdir, now=NOW)[1:]:
        lv, rid, *_ = line.split()
        m = re.search(r"blocked since (\S+)", line)
        printed[rid] = (lv, "stale" in line, m.group(1) if m else "")
    assert published == printed
    assert published["sodir/factpages"] == ("L2", True, "")
    assert published["seg/open-data-wiki"] == ("L0", True, "2026-10-20")
    assert published["terranubis/f3-demo-2020"] == ("L0", True, "")


def test_level_ladder_has_no_gaps():
    # L2 passing cannot lift the level over a failed L1
    checks = [{"name": "a", "level": "L1", "outcome": "fail"},
              {"name": "b", "level": "L2", "outcome": "pass"}]
    assert level_from_checks(checks) == "L0"
    checks[0]["outcome"] = "pass"
    assert level_from_checks(checks) == "L2"
    # a skipped check at a level stops the ladder there
    checks.append({"name": "c", "level": "L3", "outcome": "skip"})
    assert level_from_checks(checks) == "L2"


def test_fetch_error_message_names_the_status():
    assert "HTTP 403" in str(FetchError("https://x", 403))


def test_verify_all_never_writes_an_invalid_record(tmp_path, monkeypatch):
    monkeypatch.setattr("osd.verify.load_records", lambda: {REC["id"]: REC})
    monkeypatch.setattr("osd.verify.verify_record", lambda *a, **k: {"record_id": REC["id"], "level": "L9"})
    with pytest.raises(ValidationError):
        verify_all(fetch=fetch_ok, out_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []



# --- E23: listing readers by shape ---------------------------------------------------------------

LISTINGS = paths.ROOT / "tests" / "fixtures" / "listings"


def listing(name, base):
    return read_listing((LISTINGS / name).read_bytes(), base)


def rows(lst):
    return [(e.name, e.url, e.size) for e in lst.entries]


AR = "https://datos.gob.ar/api/3/action/package_show?id=datos-de-fractura-de-pozos-adjunto-iv"
AR_ASSETS = [
    ("Datos de fractura de pozos de hidrocarburos (Adjunto IV) - Actualización diaria",
     ("http://datos.energia.gob.ar/dataset/71fa2e84-0316-4a1b-af68-7f35e41f58d7/resource/2280ad92-6ed3-403e-a095-"
      "50139863ab0d/download/datos-de-fractura-de-pozos-de-hidrocarburos-adjunto-iv-actualizacin-diaria.csv"), None),
    ("Infografía Hidrocarburos No Convencionales",
     "http://www.energia.gob.ar/contenidos/archivos/Reorganizacion/planeamiento/infografias/lamina_dneype_C_01.pdf",
     None)]
BCER = "https://geoweb-ags.bc-er.ca/arcgis/rest/services/PASR/PASR_WELL_SURFACE_STATE_PT/MapServer/0?f=json"
SGC = ("https://services1.arcgis.com/Og2nrTKe5bptW02d/arcgis/rest/services/"
       "Banco_de_Informaci%C3%B3n_Petrolera_Pozos/FeatureServer/0")
UT = "https://services.arcgis.com/ZzrwjTRez6FJiOq4/arcgis/rest/services/viewAGRC_WellData_Surf/FeatureServer/0"
EXPORT = "/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=2000"
EXPORT_NAME = "query export (geojson, at most 2000 features)"


@pytest.mark.parametrize("name,base,shape,assets,listed,excluded", [
    ("ckan-ar-energia-fractura.json", AR, "ckan", AR_ASSETS, None,
     ["https://datos.gob.ar/dataset/energia-datos-fractura-pozos-hidrocarburos-adjunto-iv"]),
    ("ckan-wa-demirs.json", "https://catalogue.data.wa.gov.au/api/3/action/package_show?id=x", "ckan",
     [("Other spatial formats", "https://dasc.dmirs.wa.gov.au/home?productAlias=WAPetroleumWells", None)], None,
     ["https://public-services.slip.wa.gov.au/public/services/SLIP_Public_Services/Industry_and_Mining_WFS/MapServer/WFSServer",
      "https://public-services.slip.wa.gov.au/public/services/SLIP_Public_Services/Industry_and_Mining/MapServer/WMSServer",
      "https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Industry_and_Mining/MapServer/13"]),
    ("socrata-anh.json", "https://www.datos.gov.co/api/views/fdvb-hsrf.json", "socrata",
     [("rows.csv", "https://www.datos.gov.co/api/views/fdvb-hsrf/rows.csv?accessType=DOWNLOAD", None)], "2026-06-02",
     ["https://www.datos.gov.co/api/views/fdvb-hsrf.json"]),
    ("datagovtw-cpc.json", "https://data.gov.tw/api/v2/rest/dataset/62919", "data.gov.tw",
     [("探採研究所台灣陸域鑽井位置.csv", "https://www3.cpc.com.tw/opendata_f00/探採研究所台灣陸域鑽井位置.csv", None)], None,
     ["https://data.gov.tw/license"]),
    ("arcgis-mapserver-bcer.json", BCER, "arcgis-layer",
     [(EXPORT_NAME, BCER.split("?")[0] + EXPORT, None)], None, [BCER]),
    ("arcgis-featureserver-sgc.html", SGC, "arcgis-layer", [(EXPORT_NAME, SGC + EXPORT, None)], "2022-10-20",
     ["http://resources.arcgis.com/en/help/arcgis-rest-api/"]),
    ("arcgis-featureserver-ut.html", UT, "arcgis-layer", [(EXPORT_NAME, UT + EXPORT, None)], "2026-10-23",
     ["http://resources.arcgis.com/en/help/arcgis-rest-api/"]),
    ("zenodo-record.json", "https://zenodo.org/api/records/14534965", "zenodo",
     [("Kietavainen_etal_VOC_data.xlsx",
       "https://zenodo.org/api/records/14534965/files/Kietavainen_etal_VOC_data.xlsx/content", 27237),
      ("Kietavainen_etal_VOC_supplementary_table_1.xlsx",
       "https://zenodo.org/api/records/14534965/files/Kietavainen_etal_VOC_supplementary_table_1.xlsx/content", 24059)],
     None, ["https://zenodo.org/records/14534965"]),
    ("figshare-article.json", "https://api.figshare.com/v2/articles/1000001", "figshare",
     [("well_logs.las", "https://ndownloader.figshare.com/files/2000001", 51234),
      ("survey.sgy", "https://ndownloader.figshare.com/files/2000002", 7340032)], None,
     ["https://example.org/landing", "https://figshare.com/articles/dataset/example/1000001"]),
    ("dataverse-geus.json", "https://dataverse.geus.dk/api/datasets/:persistentId/?persistentId=doi:10.22008/FK2/44TKZR",
     "dataverse", [("Havnsø_2020_publ_Petrel.zip", "https://dataverse.geus.dk/api/access/datafile/51691", 133117652)],
     None, ["https://doi.org/10.22008/FK2/44TKZR"]),
    ("github-release-cli.json", "https://api.github.com/repos/cli/cli/releases/latest", "github-release", None, None,
     ["https://api.github.com/repos/cli/cli/zipball/v2.103.0", "https://api.github.com/repos/cli/cli/tarball/v2.103.0",
      "https://github.com/cli/cli/releases/tag/v2.103.0"]),
    ("ak-dggs.html", "https://dggs.alaska.gov/webpubs/dggs/gmc/well_data/", "directory-index", None, None,
     ["https://dggs.alaska.gov/webpubs/dggs/gmc/"]),
], ids=lambda x: x if isinstance(x, str) and x.endswith((".json", ".html")) else "")
def test_reader_selects_assets_only(name, base, shape, assets, listed, excluded):
    lst = listing(name, base)
    assert lst.shape == shape
    if assets is not None:
        assert rows(lst) == assets
    assert lst.listed_at == listed
    urls = {e.url for e in lst.entries}
    assert not urls & set(excluded)


def test_reader_release_and_index_counts():
    gh = listing("github-release-cli.json", "https://api.github.com/repos/cli/cli/releases/latest")
    assert len(gh.entries) == 22
    assert (gh.entries[0].name, gh.entries[0].size, gh.entries[0].checksum) == (
        "gh_2.103.0_checksums.txt", 1971,
        {"algorithm": "sha256", "digest": "075bb954e2b113d0d2ac788d318b516280cb87103e601e788c34f3557acb15df"})
    ak = listing("ak-dggs.html", "https://dggs.alaska.gov/webpubs/dggs/gmc/well_data/")
    assert len(ak.entries) == 105 and all(e.name.endswith(".zip") for e in ak.entries)
    assert ("BadamiUnitB1-11A[5002922829].zip",
            "https://dggs.alaska.gov/webpubs/dggs/gmc/well_data/BadamiUnitB1-11A%5B5002922829%5D.zip", None) in rows(ak)


@pytest.mark.parametrize("name,base,shape", [
    ("ckan-gsq.json", "https://www.data.qld.gov.au/api/3/action/package_show?id=ds000005", "ckan"),
    ("danegovpl-cbdg.json", "https://api.dane.gov.pl/1.4/datasets/677/resources", "json:api"),
    ("datacite-egg.json", "https://api.datacite.org/dois/10.4121/uuid:916c86cd-3558-4672-829a-105c62985ab2", "datacite"),
    ("jamstec-cruises.json", "https://www.jamstec.go.jp/obsmcs_db/e/survey/db/list_cruise.json", "json"),
])
def test_reader_names_no_files(name, base, shape):
    lst = listing(name, base)
    assert (lst.shape, lst.entries) == (shape, [])


def test_reader_is_chosen_by_shape_not_host():
    for name, base in [("ckan-ar-energia-fractura.json", AR), ("socrata-anh.json", "https://www.datos.gov.co/x"),
                       ("arcgis-featureserver-ut.html", UT), ("zenodo-record.json", "https://zenodo.org/api/x")]:
        mine, other = listing(name, base), listing(name, "https://another.test/listing")
        assert mine.shape == other.shape != "json"
    assert rows(listing("ckan-ar-energia-fractura.json", "https://another.test/l")) == AR_ASSETS


@pytest.mark.parametrize("body,needle", [
    (b'{"help": "x", "success": false, "error": {"message": "Not found", "__type": "Not Found Error"}}', "Not found"),
    (b'{"error": {"code": 400, "message": "Invalid URL", "details": []}}', "Invalid URL"),
])
def test_error_bodies_are_not_listings(body, needle):
    with pytest.raises(ListingError, match=f"error response: {needle}"):
        read_listing(body, BASE)


def test_unrecognised_listing_names_content_type_and_first_bytes():
    with pytest.raises(ListingError) as e:
        read_listing(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", BASE, "image/png")
    assert str(e.value).startswith("listing format not recognised (content type image/png, first bytes '\\x89PNG")
    assert read_listing(b"a.csv\n# note\nb.csv\n", BASE, "text/plain").shape == "text"  # text lines still read


# --- E23: publisher checksums -------------------------------------------------------------------

class MapOpener:
    """Serve URLs from a dict (bytes, in 7-byte chunks); every URL asked for is recorded."""

    def __init__(self, files, content_type=""):
        self.files, self.calls, self.content_type = files, [], content_type

    def __call__(self, url):
        self.calls.append(url)
        if url not in self.files:
            raise FetchError(url, 404)
        data = self.files[url]
        return iter([data[i:i + 7] for i in range(0, len(data), 7)])


DATA = b"well,x,y\nA-1,1,2\n" * 40
LICENCE = b"<html><body><p>Free to use with attribution.</p></body></html>"


def ckan(resources):
    return json.dumps({"success": True, "result": {"resources": resources}}).encode()


def checked(hash_value, data=DATA, sample=("*.csv",)):
    rec = copy.deepcopy(REC)
    rec["origin"]["manifest_url"] = BASE + "package"
    rec["licence"]["url"] = BASE + "licence.html"
    files = {BASE + "package": ckan([{"name": "wells.csv", "url": BASE + "wells.csv", "format": "CSV",
                                      "hash": hash_value}]),
             BASE + "wells.csv": data, BASE + "licence.html": LICENCE}
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=MapOpener(files), sample=list(sample))
    schema("verification.schema.json").validate(v)
    return v


MD5 = hashlib.md5(DATA).hexdigest()
SHA256 = hashlib.sha256(DATA).hexdigest()


@pytest.mark.parametrize("stated,outcome_,level,expect", [
    (f"md5:{MD5}", "pass", "L2", {"publisher_checksum": {"algorithm": "md5", "digest": MD5}, "compared": True}),
    ("md5:" + "0" * 32, "fail", "L1", {"publisher_checksum": {"algorithm": "md5", "digest": "0" * 32}, "compared": True}),
    ("", "pass", "L2", {}),
    ("md5:not-a-digest", "pass", "L2", {"publisher_checksum": {"algorithm": "md5", "digest": "not-a-digest"},
                                        "compared": False}),
    (f"crc32:{MD5[:8]}", "pass", "L2", {"publisher_checksum": {"algorithm": "crc32", "digest": MD5[:8]},
                                        "compared": False}),
], ids=["match", "mismatch", "absent", "malformed", "unsupported"])
def test_publisher_checksum(stated, outcome_, level, expect):
    v = checked(stated)
    c = outcome(v, "files-checksummed")
    (f,) = v["files"]
    assert f == {"path": "wells.csv", "url": BASE + "wells.csv", "bytes": len(DATA), "sha256": SHA256, **expect}
    assert (c["outcome"], v["level"]) == (outcome_, level)
    if outcome_ == "fail":
        assert c["detail"] == f"publisher checksum mismatch: wells.csv: publisher md5 {'0' * 32}, computed {MD5}"
    elif expect.get("compared"):
        assert "publisher checksums match for 1 of 1" in c["detail"]
    else:
        assert "publisher checksums" not in c["detail"]


@pytest.mark.parametrize("stated", [
    hashlib.sha1(DATA).hexdigest(),                       # bare hex, 40 digits: sha1
    {"type": "SHA-256", "value": SHA256.upper()},          # Dataverse form, upper case
    "sha256:" + SHA256,                                    # GitHub release digest form
    {"algorithm": "MD5", "digest": MD5},
])
def test_publisher_checksum_algorithms(stated):
    v = checked(stated)
    assert (v["files"][0]["compared"], v["level"]) == (True, "L2")
    bad = checked(stated, data=DATA + b"tampered")
    assert (outcome(bad, "files-checksummed")["outcome"], bad["level"]) == ("fail", "L1")


def test_stated_checksum_forms():
    assert stated_checksum("md5:ABC") == {"algorithm": "md5", "digest": "ABC"}
    assert stated_checksum({"type": "MD5", "value": "x"}) == {"algorithm": "MD5", "digest": "x"}
    assert stated_checksum("a" * 32) == {"algorithm": "md5", "digest": "a" * 32}
    assert stated_checksum("a" * 64) == {"algorithm": "sha256", "digest": "a" * 64}
    assert stated_checksum("zz-top") == {"algorithm": "unstated", "digest": "zz-top"}
    assert stated_checksum("") is None and stated_checksum(None) is None


# --- E23: generated exports ----------------------------------------------------------------------

LAYER = json.dumps({"type": "Feature Layer", "maxRecordCount": 2000, "fields": [],
                    "editingInfo": {"lastEditDate": 1761213703000}}).encode()


def exported(body, max_records=2000):
    rec = copy.deepcopy(REC)
    rec["origin"]["manifest_url"] = BASE + "svc/0?f=json"
    rec["licence"]["url"] = BASE + "licence.html"
    layer = LAYER.replace(b"2000", str(max_records).encode())
    url = BASE + f"svc/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount={max_records}"
    op = MapOpener({BASE + "svc/0?f=json": layer, url: body, BASE + "licence.html": LICENCE})
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=op, sample=["*"])
    schema("verification.schema.json").validate(v)
    return v, op


GEOJSON = b'{"type":"FeatureCollection","features":[{"type":"Feature","geometry":null,"properties":{"a":1}}]'


def test_truncated_export_is_partial_never_a_file():
    v, _ = exported(GEOJSON + b',"properties":{"exceededTransferLimit" : true}}')
    assert "files" not in v
    (p,) = v["partial_exports"]
    assert (p["partial"], p["path"]) == (True, "query export (geojson, at most 2000 features)")
    c = outcome(v, "files-checksummed")
    assert (c["outcome"], v["level"]) == ("skip", "L1")
    assert "export truncated by the server (exceededTransferLimit)" in c["detail"]


def test_complete_export_is_a_file():
    v, _ = exported(GEOJSON + b',"properties":{"exceededTransferLimit":false}}')
    assert "partial_exports" not in v and v["level"] == "L2"
    assert v["files"][0]["sha256"] == hashlib.sha256(GEOJSON + b',"properties":{"exceededTransferLimit":false}}').hexdigest()


def test_arcgis_export_is_bounded_by_max_record_count():
    v, op = exported(GEOJSON + b"}", max_records=750)
    assert BASE + "svc/0/query?where=1%3D1&outFields=*&f=geojson&resultRecordCount=750" in op.calls
    assert v["level"] == "L2"


def test_listing_date_in_coverage():
    v, _ = exported(GEOJSON + b"}")
    assert outcome(v, "files-checksummed")["detail"].endswith("; listing dated 2025-10-23")


# --- E23: policy coverage and reasons ------------------------------------------------------------

def test_every_manifest_url_record_has_a_sample_policy():
    samples = load_samples()
    missing = sorted(rid for rid, r in load_records().items() if r["origin"].get("manifest_url") and rid not in samples)
    assert missing == []
    assert len(samples) >= 23


def test_unsampled_sentence_is_the_reason(tmp_path):
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path),
                      sample="the listing is a search result with no file addresses")
    c = outcome(v, "files-checksummed")
    assert (c["outcome"], c["detail"]) == ("skip", ("nothing to sample (verifier/samples.yaml): the listing is a "
                                                    "search result with no file addresses"))


def cause(tmp_path, kind):
    rec = l2_fixture(tmp_path)
    opener, sample = dir_opener(tmp_path), SAMPLE
    if kind == "no-manifest":
        del rec["origin"]["manifest_url"]
    elif kind == "unrecognised":
        (tmp_path / "index.json").write_bytes(b"PK\x03\x04\x00\x00binary zip")
    elif kind == "robots":
        (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /index.json\n")
    elif kind == "budget":
        (tmp_path / "index.json").write_text(json.dumps([{"name": "big.sgy", "url": "data/a.sgy", "size": 10**12}]))
    elif kind == "no-sample":
        sample = None
    elif kind == "no-match":
        sample = ["*.zip"]
    elif kind == "licence-404":
        (tmp_path / "licence.html").unlink()
    return verify_record(rec, fetch_ok, None, now=NOW, opener=opener, sample=sample)


REASONS = {
    "no-manifest": ("files-checksummed", "no origin.manifest_url"),
    "unrecognised": ("files-checksummed", "listing format not recognised (content type not stated, first bytes 'PK\\x03\\x04"),
    "robots": ("files-checksummed", "robots.txt disallows the listing https://fixture.test/index.json"),
    "budget": ("files-checksummed", "sample would exceed the run budget (1000000000000 bytes listed for big.sgy"),
    "no-sample": ("files-checksummed", "no sample for this record in verifier/samples.yaml"),
    "no-match": ("files-checksummed", "no entry of the listing (4 entries, json) matches the sample"),
    "licence-404": ("licence-text-captured", "licence page https://fixture.test/licence.html answered HTTP 404"),
}


@pytest.mark.parametrize("kind", list(REASONS))
def test_l2_reason_texts(tmp_path, kind):
    v = cause(tmp_path, kind)
    name, text = REASONS[kind]
    assert v["level"] == "L1"
    assert outcome(v, name)["detail"].startswith(text)


def test_status_prints_each_records_own_reason(tmp_path):
    vdir = tmp_path / "verification"
    vdir.mkdir()
    picks = {"equinor/volve": "no-match", "sodir/factpages": "licence-404", "opm/norne": "unrecognised",
             "nlog/nlog": None}
    for i, (rid, kind) in enumerate(picks.items()):
        d = tmp_path / f"r{i}"
        d.mkdir()
        v = cause(d, kind) if kind else verify_record(l2_fixture(d), fetch_ok, None, now=NOW,
                                                      opener=dir_opener(d), sample=SAMPLE)
        v["record_id"] = rid
        (vdir / (rid.replace("/", "__") + ".json")).write_text(json.dumps(v))
    lines = {line.split()[1]: line for line in status_lines(vdir, now=NOW)[1:]}
    assert status_lines(vdir, now=NOW)[0].endswith(" reason")
    for rid, kind in picks.items():
        if kind is None:
            assert lines[rid].split()[0] == "L2" and "files-checksummed" not in lines[rid]
            continue
        name, text = REASONS[kind]
        assert f"{name}: {text}" in lines[rid], rid
        for other in set(picks.values()) - {kind, None}:
            assert REASONS[other][1] not in lines[rid]
    assert lines["seg/open-data-wiki"].endswith(" never verified")


# --- E23: guards ---------------------------------------------------------------------------------

def test_cut_sample_leaves_no_partial_file(tmp_path):
    budget = ByteBudget(600)  # a.sgy is 500 bytes; b.las crosses the budget mid-stream
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE,
                      budget=budget)
    assert [f["path"] for f in v["files"]] == ["data/a.sgy"] and "partial_exports" not in v
    assert "data/b.las abandoned mid-stream and not recorded; 1 of 3 files hashed" in outcome(v, "files-checksummed")["detail"]


def test_record_share_of_the_run_budget(tmp_path, monkeypatch):
    monkeypatch.setattr("osd.verify.RECORD_SAMPLE_BYTES", 600)
    run = ByteBudget()
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE,
                      budget=run)
    assert [f["path"] for f in v["files"]] == ["data/a.sgy"]
    assert run.used <= 600 and run.remaining > 10**9   # the next record still has the rest of the run


def test_sample_and_inventory_share_one_budget(tmp_path, monkeypatch):
    monkeypatch.setattr("osd.verify.RECORD_SAMPLE_BYTES", 600)
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=["*.sgy"],
                      budget=ByteBudget(), mirror_rule=["data/*"])
    assert [f["path"] for f in v["files"]] == ["data/a.sgy"]
    assert v["inventory"]["coverage"] == "partial"


def test_unreadable_robots_is_not_called_a_disallow(tmp_path):
    rec = l2_fixture(tmp_path)
    inner = dir_opener(tmp_path)

    def opener(url):
        if url.endswith("/robots.txt"):
            raise FetchError(url, 503)
        return inner(url)

    c = outcome(verify_record(rec, fetch_ok, None, now=NOW, opener=opener, sample=SAMPLE), "files-checksummed")
    assert (c["outcome"], c["detail"]) == ("skip", ("robots.txt could not be read (HTTP 503 from "
                                                    "https://fixture.test/robots.txt), so the listing is not fetched (RFC 9309)"))


def test_robots_disallow_never_fetches_the_listing(tmp_path):
    rec = l2_fixture(tmp_path)
    (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /index.json\n")
    calls = []
    verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path, calls), sample=SAMPLE,
                  mirror_rule=["data/*"])
    assert BASE + "robots.txt" in calls and BASE + "index.json" not in calls


# --- E23: verification/4 compatibility -----------------------------------------------------------

FROZEN_3 = paths.ROOT / "tests" / "fixtures" / "schema" / "verification-3.schema.json"


def test_verification_4_identity():
    assert schema("verification.schema.json").schema["$id"] == "https://open-subsurface-data.org/schema/verification/4"


def test_frozen_3_is_main_085a7de():
    assert hashlib.sha256(FROZEN_3.read_bytes()).hexdigest() == (
        "61a18c30a92a78fc816f0615db12e75e5a92480ef8c80a8cce6286caae1562d9")
    assert json.loads(FROZEN_3.read_text())["$id"].endswith("/verification/3")


def test_stored_3_results_validate_against_4():
    with gzip.open(paths.ROOT / "tests" / "fixtures" / "verification" / "stored-3.jsonl.gz", "rt") as fh:
        docs = [json.loads(line) for line in fh]
    v3 = Draft202012Validator(json.loads(FROZEN_3.read_text()))
    v4 = schema("verification.schema.json")
    assert len(docs) == 96
    for d in docs:
        v3.validate(d)
        v4.validate(d)


def test_fixture_verifications_validate_against_4():
    fx = paths.ROOT / "tests" / "fixtures"   # E127's fidelity input and E07's Norne verification
    for p in (fx / "fidelity" / "verification" / "acme__two-wells.json", fx / "mirror" / "verification-2-norne.json"):
        schema("verification.schema.json").validate(json.loads(p.read_text()))


def test_inventory_keeps_e07_meaning():
    assert (schema("verification.schema.json").schema["properties"]["inventory"]
            == json.loads(FROZEN_3.read_text())["properties"]["inventory"])


def test_partial_exports_stay_out_of_files():
    base = {"record_id": "a/b", "checked_at": "2026-10-23T12:00:00+00:00", "tool_version": "t", "level": "L1",
            "checks": []}
    f = {"path": "x", "bytes": 1, "sha256": "0" * 64}
    s = schema("verification.schema.json")
    s.validate({**base, "partial_exports": [{**f, "partial": True}]})
    with pytest.raises(ValidationError):
        s.validate({**base, "files": [{**f, "partial": True}]})
    with pytest.raises(ValidationError):
        s.validate({**base, "partial_exports": [f]})
