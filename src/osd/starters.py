"""Starter packs, osd.starter/1 (E40): the validity of one pack document, as nine tests.

A pack is committed as starters/<record id with / as __>__<pack>.json by the recipe run it names, with
its fidelity record under starters/fidelity/. `check()` is the one function `osd validate`, `osd build`
and the tests call; it returns the refusals, each naming what it refuses, and what it could not check
here:

  (a) the live schema (nothing else is judged when it fails), the file name and the record;
  (b) each input is a held file of the record: one file of its latest verification with that
      `verifier_run`, or one held custody/2 `deposit` document with that key; name, size and digest
      agree; a tombstone or another record's file refuses;
  (c) each derived entry comes `from` an input digest;
  (d) the licence is computed from the inputs (every input `allowed`; name, spdx, url, statement and
      terms agree across inputs or the combination is unsupported; attribution required if any input
      requires it, else unknown if any is unknown; share-alike if any input is) and `sources[]` is
      each input's evidence licence, whole;
  (e) every (topic, object) its contents need is decided, once;
  (f) each artefact is a held custody/2 `derived` document of this pack, size and digest agreeing
      (an unpublished pack may carry no key yet: unchecked, never passed);
  (g) each target's `import` is one of its artefacts, and a path has one digest in the pack;
  (h) the fidelity record covers exactly the inputs, converted or partial, into contents kinds;
  (i) each oracle compared values and found no difference, unless the pack is `unpublished`.

(b) and (f) read the latest verifications and the custody documents, which `make check` does not
have (they arrive in the Pages build from `verification-results`). Where a directory is absent the
rule is reported as unchecked, never passed; `osd build` publishes no pack with anything unchecked.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cache, cached_property
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from . import custody, mirror, paths
from .manifest import LICENCE_FIELDS
from .verify import fidelity_problems

FORMAT = "osd.starter/1"
STARTERS_DIR = paths.ROOT / "starters"
CUSTODY_DIR = mirror.MIRROR_DIR / "custody"
AGREE = ("name", "spdx", "url", "statement", "terms")     # equal across inputs, or unsupported
WELL_KINDS = {"wellbore-headers", "wellbore-logs", "wellbore-paths", "tops"}
WELL_TOPICS = ("crs", "vertical-datum", "depth-reference", "depth-kind", "units", "nulls", "names")
VOLUME_TOPICS = ("crs", "domain", "units", "nulls")       # seismic-3d (+ velocity in depth) and horizons
ABSENT = "(absent)"


@cache
def _validator() -> Draft202012Validator:
    schema = json.loads((paths.SCHEMA_DIR / "starter.schema.json").read_text())
    return Draft202012Validator(schema, format_checker=FormatChecker())


def file_name(pack_id: str) -> str:
    return pack_id.replace("/", "__") + ".json"


def pack_files(starters_dir: Path = STARTERS_DIR) -> list[Path]:
    return sorted(starters_dir.glob("*.json")) if starters_dir.is_dir() else []


def record_licence(rec: dict) -> dict:
    return {k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]}


@dataclass
class Evidence:
    """What a pack is judged against: the records, and where present the latest verifications and the
    custody documents (None or a missing directory: not here)."""
    records: dict[str, dict]
    vdir: Path | None = None
    custody_dir: Path | None = None

    @property
    def has_verifications(self) -> bool:
        return self.vdir is not None and self.vdir.is_dir()

    @property
    def has_custody(self) -> bool:
        return self.custody_dir is not None and self.custody_dir.is_dir()

    @cached_property
    def custody(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """(held, removed) custody documents by key; a digest with a tombstone is removed, never held."""
        held, removed = {}, {}
        for p in sorted(self.custody_dir.glob("*.json")):
            doc = json.loads(p.read_text())
            if p.name.endswith(".removed.json"):
                removed[doc["key"]] = doc
            elif not (self.custody_dir / (p.stem + ".removed.json")).exists():
                held[doc["key"]] = doc
        return held, removed

    def verification(self, rid: str) -> dict | None:
        p = self.vdir / (rid.replace("/", "__") + ".json")   # as build.latest_verification reads it
        return json.loads(p.read_text()) if p.exists() else None

    @cached_property
    def by_digest(self) -> dict[str, str]:
        """sha256 to the record whose latest verification names it (another record's file)."""
        out = {}
        for p in sorted(self.vdir.glob("*.json")):
            v = json.loads(p.read_text())
            for f in v.get("files", []):
                out.setdefault(f["sha256"], v["record_id"])
        return out


@dataclass
class Result:
    problems: list[str] = field(default_factory=list)
    unchecked: list[str] = field(default_factory=list)


def _short(sha: str) -> str:
    return f"{sha[:12]}…"


def _held_in_custody(what: str, key: str, ev: Evidence, out: list[str]) -> dict | None:
    held, removed = ev.custody
    if key in removed:
        t = removed[key]["removal"]
        out.append(f"{what}: custody key {key} is removed ({t['removed_at'][:10]}, {t['request']}): never in a pack")
        return None
    if key not in held:
        out.append(f"{what}: no held custody document has key {key}")
        return None
    return held[key]


def _agrees(what: str, item: dict, evidence_name: str, evidence: dict, source: str, out: list[str]) -> None:
    if item["bytes"] != evidence["bytes"]:
        out.append(f"{what}: bytes {item['bytes']}, {source} states {evidence['bytes']}")
    if item["sha256"] != evidence["sha256"]:
        out.append(f"{what}: sha256 {_short(item['sha256'])}, {source} states {_short(evidence['sha256'])}")
    if evidence_name is not None and item.get("name", evidence_name) != evidence_name:
        out.append(f"{what}: name {item['name']} is not {evidence_name}, the file {source} names")


def _inputs(doc: dict, ev: Evidence, res: Result) -> dict[str, dict]:
    """(b). Returns each input's evidence licence by input name, where the evidence is here."""
    rid, out, licences = doc["record_id"], res.problems, {}
    for i in doc["inputs"]:
        what, held = f"input {i['name']}", i["held"]
        if held["as"] == "verified":
            licences[i["name"]] = record_licence(ev.records[rid])
            if not ev.has_verifications:
                res.unchecked.append(f"{what}: no verification results here")
                continue
            v = ev.verification(rid)
            if v is None:
                out.append(f"{what}: no verification of {rid}")
                continue
            run = held["verifier_run"]
            if (run["checked_at"], run["tool_version"]) != (v["checked_at"], v["tool_version"]):
                out.append(f"{what}: verifier_run {run['checked_at']} {run['tool_version']} is not the latest "
                           f"verification of {rid} ({v['checked_at']} {v['tool_version']})")
                continue
            f = next((f for f in v.get("files", []) if f["path"] == held["path"]), None)
            if f is None:
                other = ev.by_digest.get(i["sha256"])
                out.append(f"{what}: {_short(i['sha256'])} is a file of record {other}, not {rid}" if other and other != rid
                           else f"{what}: path {held['path']} is not a file of the latest verification of {rid}")
                continue
            _agrees(what, i, custody.object_name(f["path"]), f, "the verification", out)
        else:
            if not ev.has_custody:
                res.unchecked.append(f"{what}: no custody documents here")
                continue
            d = _held_in_custody(what, held["key"], ev, out)
            if d is None:
                continue
            if d["record_id"] != rid:
                out.append(f"{what}: custody key {held['key']} holds a file of record {d['record_id']}, not {rid}")
                continue
            if custody.provenance(d) != "deposit":
                out.append(f"{what}: custody key {held['key']} is a {custody.provenance(d)} copy, not a deposit")
                continue
            licences[i["name"]] = d["licence"]
            _agrees(what, i, custody.object_name(d["path"]), d, "its custody document", out)
    return licences


def computed_licence(sources: list[dict]) -> tuple[dict | None, list[str]]:
    """(d) The pack licence from its inputs' licences, or None with the reasons it is not computable."""
    out = []
    for s in sources:
        if s["licence"]["redistribution"] != "allowed":
            out.append(f"input {s['input']}: redistribution {s['licence']['redistribution']}: never in a pack")
    lics = [s["licence"] for s in sources]
    common = {}
    for f in AGREE:
        values = list(dict.fromkeys(json.dumps(lic.get(f, ABSENT), sort_keys=True) for lic in lics))
        if len(values) > 1:
            out.append(f"unsupported combination: the inputs' licence {f} differs ({', '.join(values)})")
        elif f in lics[0]:
            common[f] = lics[0][f]
    if out:
        return None, out
    attribution = ("required" if any(lic["attribution"] == "required" for lic in lics) else
                   "unknown" if any(lic["attribution"] == "unknown" for lic in lics) else "not-required")
    lic = {**common, "redistribution": "allowed", "attribution": attribution}
    if any("share_alike" in x for x in lics):
        lic["share_alike"] = any(x.get("share_alike") is True for x in lics)
    return {k: lic[k] for k in LICENCE_FIELDS if k in lic}, []


def _licence(doc: dict, evidence_licences: dict[str, dict], out: list[str]) -> None:
    sources = doc["licence"]["sources"]
    names = [i["name"] for i in doc["inputs"]]
    if [s["input"] for s in sources] != names:
        out.append(f"licence sources name {[s['input'] for s in sources]}, the inputs are {names}")
    for s in sources:
        lic = evidence_licences.get(s["input"])
        if lic is not None and s["licence"] != lic:
            fields = sorted(k for k in set(lic) | set(s["licence"]) if lic.get(k, ABSENT) != s["licence"].get(k, ABSENT))
            out.append(f"licence sources {s['input']}: not its evidence's licence ({', '.join(fields)} differ)")
    lic, why = computed_licence(sources)
    out += why
    if lic is None:
        return
    stated = {k: v for k, v in doc["licence"].items() if k != "sources"}
    for k in [k for k in LICENCE_FIELDS if k in stated or k in lic]:
        if stated.get(k, ABSENT) != lic.get(k, ABSENT):
            out.append(f"licence {k} is {json.dumps(stated.get(k, ABSENT))}, computed "
                       f"{json.dumps(lic.get(k, ABSENT))} from the inputs")


def _decisions(doc: dict, out: list[str]) -> None:
    subjects = {"pack"}
    for c in doc["contents"]:
        subjects.update(c["ids"])
        if c["count"] != len(c["ids"]):
            out.append(f"contents {c['kind']}: count {c['count']}, ids name {len(c['ids'])}")
    values: dict[tuple[str, str], list[str]] = {}
    for d in doc["decisions"]:
        if d["subject"] not in subjects:
            out.append(f"decision {d['topic']} names subject {d['subject']}, not an object of contents")
        values.setdefault((d["topic"], d["subject"]), [])
        if d["value"] not in values[(d["topic"], d["subject"])]:
            values[(d["topic"], d["subject"])].append(d["value"])
    for (topic, subject), vs in values.items():
        if len(vs) > 1:
            out.append(f"decision {topic} for {subject} has two values: {' | '.join(vs)}")
    for c in doc["contents"]:
        for oid in c["ids"]:
            if c["kind"] in WELL_KINDS:
                need = WELL_TOPICS
            elif c["kind"] == "seismic-3d":
                need = VOLUME_TOPICS + (("velocity",) if "depth" in values.get(("domain", oid), []) else ())
            elif c["kind"] == "horizons":
                need = VOLUME_TOPICS
            else:
                need = ()
            for topic in need:
                if (topic, oid) not in values:
                    out.append(f"decision {topic} for {oid} ({c['kind']}) is missing")


def _artefacts(doc: dict, ev: Evidence, res: Result) -> None:
    """(f) and (g)."""
    out = res.problems
    digests: dict[str, str] = {d["path"]: d["sha256"] for d in doc["derived"]}
    seen, clashes = set(), set()
    for t in doc["targets"]:
        paths_ = [a["path"] for a in t["artefacts"]]
        if t["import"] not in paths_:
            out.append(f"target {t['application']}: import {t['import']} is not one of its artefacts")
        for a in t["artefacts"]:
            if digests.setdefault(a["path"], a["sha256"]) != a["sha256"] and a["path"] not in clashes:
                clashes.add(a["path"])
                out.append(f"artefact {a['path']}: two digests for one path in the pack")
            what = f"artefact {a['path']}"
            if "key" not in a:   # admitted by the schema only while unpublished (E129 fills it at finalise)
                res.unchecked.append(f"{what}: no custody key yet (unpublished)")
                continue
            if a["key"] in seen:
                continue
            seen.add(a["key"])
            if not ev.has_custody:
                res.unchecked.append(f"{what}: no custody documents here")
                continue
            d = _held_in_custody(what, a["key"], ev, out)
            if d is None:
                continue
            if custody.provenance(d) != "derived" or d["derived"]["pack_id"] != doc["id"]:
                owner = d["derived"]["pack_id"] if "derived" in d else f"a {custody.provenance(d)} copy of {d['record_id']}"
                out.append(f"{what}: custody key {a['key']} is not an artefact of {doc['id']} ({owner})")
                continue
            _agrees(what, a, None, d, "its custody document", out)


def _fidelity(doc: dict, starters_dir: Path, out: list[str]) -> None:
    what = f"fidelity {doc['fidelity']}"
    p = (starters_dir / doc["fidelity"]).resolve()
    if not p.is_relative_to(starters_dir.resolve()) or not p.is_file():
        out.append(f"{what}: not found under {starters_dir}")
        return
    try:
        fd = json.loads(p.read_text())
    except ValueError as e:
        out.append(f"{what}: {e}")
        return
    bad = fidelity_problems(fd) if isinstance(fd, dict) else ["(root): not an object"]
    if bad:
        out += [f"{what}: {b}" for b in bad]
        return
    if fd["record"] != doc["record_id"]:
        out.append(f"{what}: record {fd['record']}, the pack is of {doc['record_id']}")
    pack_inputs = {i["sha256"]: i["name"] for i in doc["inputs"]}
    results = {i["sha256"]: i for i in fd["inputs"]}
    for sha, name in pack_inputs.items():
        if sha not in results:
            out.append(f"{what}: no result for input {name} ({_short(sha)})")
    kinds = {c["kind"] for c in doc["contents"]}
    for sha, i in results.items():
        if sha not in pack_inputs:
            out.append(f"{what}: input {i['name']} ({_short(sha)}) is not a pack input")
        if i["result"] not in ("converted", "partial"):
            out.append(f"{what}: input {i['name']} is {i['result']}")
        elif i["output"]["kind"] not in kinds:
            out.append(f"{what}: input {i['name']} became {i['output']['kind']}, not a contents kind")


def _oracle(doc: dict, out: list[str]) -> None:
    if doc.get("unpublished") is True:
        return
    for t in doc["targets"]:
        o = t["oracle"]
        if o["values"] == 0:
            out.append(f"target {t['application']}: the oracle compared no values")
        if o["differences"] != 0:
            out.append(f"target {t['application']}: the oracle found {o['differences']} differences; "
                       "such a pack says unpublished: true")


def check(doc: dict, ev: Evidence, starters_dir: Path = STARTERS_DIR, name: str | None = None) -> Result:
    res = Result()
    res.problems = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
                    for e in sorted(_validator().iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))]
    if res.problems:
        return res
    out = res.problems
    if name is not None and name != file_name(doc["id"]):
        out.append(f"file name {name} is not {file_name(doc['id'])}, the name of pack {doc['id']}")
    if not doc["id"].startswith(doc["record_id"] + "/"):
        out.append(f"id {doc['id']} is not a pack of record {doc['record_id']}")
    if doc["record_id"] not in ev.records:
        out.append(f"record {doc['record_id']} is not in the catalogue")
        return res
    licences = _inputs(doc, ev, res)
    digests = {i["sha256"] for i in doc["inputs"]}
    for d in doc["derived"]:
        if d["from"] not in digests:
            out.append(f"derived {d['path']}: from {_short(d['from'])} is not an input digest")
    _licence(doc, licences, out)
    _decisions(doc, out)
    _artefacts(doc, ev, res)
    _fidelity(doc, starters_dir, out)
    _oracle(doc, out)
    return res


def check_dir(starters_dir: Path, ev: Evidence) -> list[tuple[Path, dict | None, Result]]:
    """Every pack document in starters_dir, read and checked."""
    out = []
    for p in pack_files(starters_dir):
        try:
            doc = json.loads(p.read_text())
        except ValueError as e:
            out.append((p, None, Result(problems=[f"not JSON: {e}"])))
            continue
        if not isinstance(doc, dict):
            out.append((p, None, Result(problems=["(root): not an object"])))
            continue
        out.append((p, doc, check(doc, ev, starters_dir, p.name)))
    return out
