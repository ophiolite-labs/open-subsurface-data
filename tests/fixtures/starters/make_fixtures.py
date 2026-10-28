"""Writes the E40 fixtures (design 7); run `uv run python tests/fixtures/starters/make_fixtures.py`.

Two packs a recipe could have written, with everything they are judged against:

  packs/                      a starters/ directory: the two pack documents and fidelity/ (one per pack)
    terranubis__f3-demo-2020__starter.json   F3-shaped: one cube, four wells, two horizons, three
                                              targets, deposited inputs, derived SEG-Y and LAS
    rmotc__teapot-dome__python.json           Teapot-shaped: one target over verified inputs
  artefacts/<pack>/<path>     the artefact bytes (a few lines each), as the mirror would hold them
  records/                    copies of the two records, as committed on main dbd5650
  verification/               the latest verification per record: F3 a verification/7 with the
                              deposit check (frozen here, E41 writes it), Teapot a /6-shaped one
  ../custody/                 the captured custody snapshot: the Norne /1 copy, the F3 deposits
                              (custody/2 `deposit`), every artefact (custody/2 `derived`) and one
                              tombstone (an earlier F3 deposit, removed)

Input files are never fetched, so their bytes are stand-ins: the digest of a fixed string. The
licence and attribution lines are computed here the way the validator computes them; the tests
prove the two agree. Rewrites every file above; nothing else.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import yaml

from osd import custody
from osd.get import entry_attribution
from osd.manifest import LICENCE_FIELDS, Entry, Licence
from osd.stac import collection_id

HERE = Path(__file__).resolve().parent
CUSTODY_DIR = HERE.parent / "custody"
MIRROR = "https://mirror.example"
NORNE = HERE.parent / "mirror" / "custody" / "held.json"
CATALOG = {"source_commit": "1" * 40, "verification_commit": "2" * 40, "built_at": "2026-10-29T09:00:00Z",
           "records_digest": "3" * 64}
RECIPE_REPO = "https://github.com/ophiolite-labs/ophiolite"
RECIPE_COMMIT = "4" * 40


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dump(p: Path, doc: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def record(rid: str) -> dict:
    return yaml.safe_load((HERE / "records" / f"{rid}.yaml").read_text())


def licence_of(rec: dict) -> dict:
    return {k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]}


def attribution(rec: dict, lic: dict) -> list[str]:
    e = Entry(collection_id=collection_id(rec["id"]), record_id=rec["id"], title=rec["title"],
              origin_url=rec["origin"]["url"], access=rec["origin"]["access"], licence=Licence(**lic), assets=(),
              known_issues=tuple(rec.get("known_issues", [])))
    return entry_attribution(e)


def computed(sources: list[dict]) -> dict:
    """The pack licence of one-record packs: every field agrees, attribution and share_alike as stated."""
    lic = dict(sources[0]["licence"])
    return {**lic, "sources": sources}


def custody_doc(rec: dict, path: str, digest: str, n: int, lic: dict, copied_at: str, **provenance) -> dict:
    return {"format": "osd.custody/2", "record_id": rec["id"], "path": path, "origin_href": None,
            "key": custody.object_key(rec["id"], digest, path),
            "href": f"{MIRROR}/{custody.object_key(rec['id'], digest, path)}", "sha256": digest, "bytes": n,
            "copied_at": copied_at, **provenance, "licence": lic,
            "licence_text_sha256": provenance.get("deposit", {}).get("licence_text_sha256"),
            "attribution": attribution(rec, lic), "takedown": custody.TAKEDOWN_URL, "removal": {"state": "held"}}


def artefact_files(pack: str, files: dict[str, str]) -> dict[str, bytes]:
    out = {}
    for path, text in files.items():
        p = HERE / "artefacts" / pack / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        out[path] = p.read_bytes()
    return out


def decision(topic: str, subject: str, value: str, source: str, note: str | None = None) -> dict:
    return {"topic": topic, "subject": subject, "value": value, "source": source, **({"note": note} if note else {})}


def well_decisions(well: str, kb: str) -> list[dict]:
    return [decision("crs", well, "EPSG:23031 (ED50 / UTM zone 31N)", "publisher"),
            decision("vertical-datum", well, "MSL", "publisher"),
            decision("depth-reference", well, f"KB {kb} m above MSL", "data"),
            decision("depth-kind", well, "MD", "data"),
            decision("units", well, "depth m; GR API; DT us/ft; RHOB g/cm3", "data"),
            decision("nulls", well, "-999.25", "data"),
            decision("names", well, "GR, DT, RHOB, PHIE kept as the LAS names them", "chosen",
                     "the four curves every target reads; no renaming keeps the LAS and the targets aligned")]


def write_pack(rec: dict, pack: str, title: str, summary: str, tools: dict, contents: list, inputs: list,
               derived: list, decisions: list, targets: list, artefacts: dict[str, bytes], copied_at: str,
               docs: dict[str, dict], fidelity_outputs: dict[str, dict]) -> None:
    pid = f"{rec['id']}/{pack}"
    name = f"{rec['id'].replace('/', '__')}__{pack}.json"
    sources = [{"input": i["name"], "licence": licence_of(rec)} for i in inputs]
    lic = computed(sources)
    pack_lic = {k: v for k, v in lic.items() if k != "sources"}
    for path, b in artefacts.items():
        d = custody_doc(rec, path, sha(b), len(b), pack_lic, copied_at,
                        derived={"pack_id": pid, "recipe_id": f"{rec['id'].split('/')[1]}-{pack}",
                                 "from": [i["sha256"] for i in inputs]})
        docs[d["sha256"]] = d

    def art(path: str) -> dict:
        b = artefacts[path]
        return {"path": path, "sha256": sha(b), "bytes": len(b), "key": custody.object_key(rec["id"], sha(b), path)}

    doc = {"format": "osd.starter/1", "id": pid, "record_id": rec["id"], "title": title, "summary": summary,
           "recipe": {"id": f"{rec['id'].split('/')[1]}-{pack}", "repository": RECIPE_REPO, "commit": RECIPE_COMMIT,
                      "tools": tools},
           "contents": contents, "inputs": inputs,
           "derived": [dict(path=p, sha256=sha(artefacts[p]), bytes=len(artefacts[p]), **{"from": f, "how": h})
                       for p, f, h in derived],
           "decisions": decisions,
           "targets": [dict(t, artefacts=[art(p) for p in t["artefacts"]]) for t in targets],
           "licence": lic, "fidelity": f"fidelity/{name}", "built_at": copied_at}
    dump(HERE / "packs" / name, doc)
    dump(HERE / "packs" / "fidelity" / name, {
        "format": "osd.fidelity/1", "catalog": CATALOG, "record": rec["id"],
        "inputs": [{"sha256": i["sha256"], "name": i["name"], "result": "converted", "output": fidelity_outputs[i["name"]]}
                   for i in inputs]})


def f3(docs: dict[str, dict]) -> None:
    rec = record("terranubis/f3-demo-2020")
    lic = licence_of(rec)
    deposit = {"obtained_at": "2026-10-29T10:00:00Z", "by": "maintainer",
               "publisher_page_url": "https://terranubis.com/datainfo/F3-Demo-2023",
               "publisher_page_sha256": sha(b"F3 Demo 2023 page as captured"),
               "licence_text_sha256": sha(b"CC BY-SA 3.0 deed as captured")}
    inputs, files = [], []
    for path, stand_in in (("F3_Demo_2023_seismic.zip", b"F3 seismic zip stand-in" * 40),
                           ("F3_Demo_2023_wells.zip", b"F3 wells zip stand-in" * 20)):
        d = custody_doc(rec, path, sha(stand_in), len(stand_in), lic, "2026-10-29T10:01:00Z", deposit=deposit)
        docs[d["sha256"]] = d
        inputs.append({"name": custody.object_name(path), "sha256": d["sha256"], "bytes": d["bytes"],
                       "held": {"as": "deposited", "key": d["key"]}})
        files.append({"path": path, "sha256": d["sha256"], "bytes": d["bytes"], "key": d["key"]})
    old = b"F3 seismic zip stand-in, the deposit of 2026-10-01"
    gone = custody_doc(rec, "F3_Demo_2023_seismic.zip", sha(old), len(old), lic, "2026-10-01T10:01:00Z", deposit=deposit)
    gone["removal"] = {"state": "removed", "removed_at": "2026-10-28T08:00:00Z",
                       "request": "https://github.com/ophiolite-labs/open-subsurface-data/issues/101",
                       "approved_by": "tuna-soup"}
    docs[gone["sha256"] + ".removed"] = gone
    dump(HERE / "verification" / "terranubis__f3-demo-2020.json", {
        "record_id": rec["id"], "checked_at": "2026-10-29T10:05:00+00:00", "tool_version": "0.1.0", "level": "L2",
        "checks": [{"name": "origin-reachable", "level": "L1", "outcome": "pass", "detail": "HTTP 200"},
                   {"name": "deposit", "level": "L2", "outcome": "pass",
                    "detail": "deposited by a maintainer from the publisher's download, 2026-10-29", "files": files,
                    "obtained_at": deposit["obtained_at"], "by": "maintainer",
                    "publisher_page_sha256": deposit["publisher_page_sha256"],
                    "licence_text_sha256": deposit["licence_text_sha256"]}],
        "origin": {"http_status": 200, "final_url": rec["origin"]["url"], "reachability": "ok"},
        "licence_text_sha256": deposit["licence_text_sha256"]})
    seismic, wells_zip = inputs[0]["sha256"], inputs[1]["sha256"]
    wells = {"F02-1": "30.0", "F03-2": "30.0", "F03-4": "30.0", "F06-1": "30.0"}
    files_text = {"standard/F3.sgy": "SEG-Y rev 1 stand-in: F3 inlines 100-750, crosslines 300-1250, 4 ms\n",
                  "standard/horizons.xyz": "# Truncation, MFS4 in TWT ms, ED50 UTM 31N\n"}
    files_text.update({f"standard/{w}.las": f"~Version 2.0 stand-in for {w}\n" for w in wells})
    files_text.update({"opendtect/import_f3.py": "# imports standard/ through odbind and OpendTect's own importers\n",
                       "resinsight/import_f3.py": "# imports standard/ through rips\n",
                       "python/f3_starter.ipynb": '{"cells": [], "metadata": {"name": "f3"}, "nbformat": 4, "nbformat_minor": 5}\n',
                       "python/requirements.txt": "segyio==1.9.12\nlasio==0.31\n"})
    art = artefact_files("terranubis__f3-demo-2020__starter", files_text)
    standard = ["standard/F3.sgy", "standard/horizons.xyz", *[f"standard/{w}.las" for w in wells]]
    oracle = {"compared": ["trace samples at 64 seeded positions against dGB's survey read through odbind",
                           "log samples at 32 seeded depths per well against lasio"],
              "values": 192, "differences": 0, "seed": 40}
    decisions = [decision("crs", "F3", "EPSG:23031 (ED50 / UTM zone 31N)", "publisher"),
                 decision("domain", "F3", "time", "data"),
                 decision("units", "F3", "TWT ms; amplitude unscaled", "data"),
                 decision("nulls", "F3", "none: every trace is live", "data")]
    for w, kb in wells.items():
        decisions += well_decisions(w, kb)
    for h in ("Truncation", "MFS4"):
        decisions += [decision("crs", h, "EPSG:23031 (ED50 / UTM zone 31N)", "publisher"),
                      decision("domain", h, "time", "data"),
                      decision("units", h, "TWT ms", "data"),
                      decision("nulls", h, "1e30 written as missing", "chosen", "OpendTect's undefined value maps to an empty xyz row")]
    write_pack(
        rec, "starter", "F3 starter project", "The F3 block cube, four wells and two horizons, ready for OpendTect, "
        "ResInsight and Python, with every decision written down.",
        {"ophiolite": "0.9.0", "odbind": "7.0.10", "segyio": "1.9.12", "lasio": "0.31"},
        [{"kind": "seismic-3d", "ids": ["F3"], "count": 1},
         {"kind": "wellbore-logs", "ids": list(wells), "count": 4},
         {"kind": "horizons", "ids": ["Truncation", "MFS4"], "count": 2}],
        inputs,
        [("standard/F3.sgy", seismic, "SEG-Y rev 1 written from the deposited survey"),
         ("standard/horizons.xyz", seismic, "both horizons as xyz from the deposited survey")]
        + [(f"standard/{w}.las", wells_zip, f"LAS 2.0 of {w} from the deposited well files") for w in wells],
        decisions,
        [{"application": "opendtect", "version": "7.0.10", "artefacts": [*standard, "opendtect/import_f3.py"],
          "import": "opendtect/import_f3.py", "oracle": oracle},
         {"application": "resinsight", "version": "2025.04", "artefacts": [*standard, "resinsight/import_f3.py"],
          "import": "resinsight/import_f3.py", "oracle": oracle},
         {"application": "python", "version": "3.12", "artefacts": [*standard, "python/f3_starter.ipynb",
                                                                    "python/requirements.txt"],
          "import": "python/f3_starter.ipynb", "oracle": oracle}],
        art, "2026-10-29T11:00:00Z", docs,
        {"F3_Demo_2023_seismic.zip": {"kind": "seismic-3d", "id": "F3", "converter": "ophiolite.segy", "version": "0.9.0"},
         "F3_Demo_2023_wells.zip": {"kind": "wellbore-logs", "id": "F3 wells", "converter": "ophiolite.las", "version": "0.9.0"}})


def teapot(docs: dict[str, dict]) -> None:
    rec = record("rmotc/teapot-dome")
    files = []
    for path, stand_in in (("teapot/3D_Seismic/filt_mig.sgy", b"Teapot migrated cube stand-in" * 30),
                           ("teapot/Well_logs/490251051400.las", b"Teapot 48-X-28 LAS stand-in" * 10)):
        files.append({"path": path, "url": f"https://edx.netl.doe.gov/storage/{path}", "bytes": len(stand_in),
                      "sha256": sha(stand_in)})
    v = {"record_id": rec["id"], "checked_at": "2026-10-29T09:30:00+00:00", "tool_version": "0.1.0", "level": "L2",
         "checks": [{"name": "origin-reachable", "level": "L1", "outcome": "pass", "detail": "HTTP 200"},
                    {"name": "files-checksummed", "level": "L2", "outcome": "pass", "detail": "2 files"},
                    {"name": "licence-text-captured", "level": "L2", "outcome": "pass", "detail": "captured"}],
         "origin": {"http_status": 200, "final_url": rec["origin"]["url"], "reachability": "ok"},
         "files": files, "licence_text_sha256": sha(b"US Government works statement as captured")}
    dump(HERE / "verification" / "rmotc__teapot-dome.json", v)
    run = {"checked_at": v["checked_at"], "tool_version": v["tool_version"]}
    inputs = [{"name": custody.object_name(f["path"]), "sha256": f["sha256"], "bytes": f["bytes"],
               "held": {"as": "verified", "verifier_run": run, "path": f["path"]}} for f in files]
    art = artefact_files("rmotc__teapot-dome__python", {
        "standard/teapot.sgy": "SEG-Y rev 1 stand-in: Teapot migrated cube\n",
        "standard/48-X-28.las": "~Version 2.0 stand-in for 48-X-28\n",
        "python/teapot_starter.ipynb": '{"cells": [], "metadata": {"name": "teapot"}, "nbformat": 4, "nbformat_minor": 5}\n'})
    crs = "EPSG:32056 (NAD27 / Wyoming East Central)"
    write_pack(
        rec, "python", "Teapot Dome for Python", "The Teapot Dome cube and well 48-X-28 for segyio and lasio.",
        {"ophiolite": "0.9.0", "segyio": "1.9.12", "lasio": "0.31"},
        [{"kind": "seismic-3d", "ids": ["Teapot 3D"], "count": 1}, {"kind": "wellbore-logs", "ids": ["48-X-28"], "count": 1}],
        inputs,
        [("standard/teapot.sgy", inputs[0]["sha256"], "SEG-Y rev 1 with the textual header rewritten"),
         ("standard/48-X-28.las", inputs[1]["sha256"], "LAS 2.0 with the well name in the header")],
        [decision("crs", "pack", crs, "publisher"),
         decision("crs", "Teapot 3D", crs, "publisher"), decision("domain", "Teapot 3D", "time", "data"),
         decision("units", "Teapot 3D", "TWT ms; ft", "data"), decision("nulls", "Teapot 3D", "none", "data"),
         decision("crs", "48-X-28", crs, "publisher"), decision("vertical-datum", "48-X-28", "NGVD29", "publisher"),
         decision("depth-reference", "48-X-28", "KB 5,207 ft", "data"), decision("depth-kind", "48-X-28", "MD", "data"),
         decision("units", "48-X-28", "depth ft; GR API", "data"), decision("nulls", "48-X-28", "-999.25", "data"),
         decision("names", "48-X-28", "curve names as the LAS states them", "data")],
        [{"application": "python", "version": "3.12",
          "artefacts": ["standard/teapot.sgy", "standard/48-X-28.las", "python/teapot_starter.ipynb"],
          "import": "python/teapot_starter.ipynb",
          "oracle": {"compared": ["trace samples at 32 seeded positions against segyio"], "values": 32,
                     "differences": 0, "seed": 7}}],
        art, "2026-10-29T11:30:00Z", docs,
        {"filt_mig.sgy": {"kind": "seismic-3d", "id": "Teapot 3D", "converter": "ophiolite.segy", "version": "0.9.0"},
         "490251051400.las": {"kind": "wellbore-logs", "id": "48-X-28", "converter": "ophiolite.las", "version": "0.9.0"}})


def main() -> None:
    for d in (HERE / "packs", HERE / "artefacts", HERE / "verification", CUSTODY_DIR):
        shutil.rmtree(d, ignore_errors=True)
    docs: dict[str, dict] = {}
    f3(docs)
    teapot(docs)
    CUSTODY_DIR.mkdir(parents=True)
    shutil.copyfile(NORNE, CUSTODY_DIR / (json.loads(NORNE.read_text())["sha256"] + ".json"))
    for name, d in docs.items():
        dump(CUSTODY_DIR / (name + ".json"), d)


if __name__ == "__main__":
    main()
