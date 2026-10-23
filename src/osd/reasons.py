"""Why a record is at its level, in the verifier's own words: the one source of that sentence.

`osd status` prints it and `osd build` writes it into records.json as `reason`, so the terminal, the
map's detail panel and the status page read the same string (E27; the rules are E23's and H1's).

- never verified: "never verified".
- blocked (OSD-D9, OSD-D20): the origin check's detail, e.g. "origin-reachable: answers a browser, not
  the verifier (HTTP 404 to osd-verifier, HTTP 200 to a browser agent); blocked since 2026-10-23".
- below L2: the first check of the level above the record's that did not pass, as "<check>: <detail>";
  an L0 record names its origin check, an L1 record its first L2 check. The one rewording: a record
  that states no `origin.manifest_url` reads "no file address is published to us", with its access.
- L2 and above: the detail of the check that awarded the level (files hashed, outline derived,
  conversion), without the check name.
"""

from __future__ import annotations

from .verify import LEVELS

EVIDENCE = {"L2": "files-checksummed", "L3": "outline-derived", "L4": "canonical-conversion"}
NO_MANIFEST = "no origin.manifest_url"


def reason(v: dict | None, rec: dict | None = None) -> str:
    """The sentence for verification `v` of record `rec` (rec only words the no-listing case)."""
    if v is None:
        return "never verified"
    checks = v.get("checks", [])
    if v.get("origin", {}).get("reachability") == "blocked":
        for c in checks:
            if c["name"] == "origin-reachable":
                return f"{c['name']}: {c.get('detail') or c['outcome']}"
    level = LEVELS.index(v["level"])
    if level >= LEVELS.index("L2"):
        name = EVIDENCE.get(v["level"])
        return next((c.get("detail", "") for c in checks if c["name"] == name and c["outcome"] == "pass"), "")
    for above in LEVELS[level + 1:]:
        for c in checks:
            if c["level"] == above and c["outcome"] != "pass":
                detail = c.get("detail") or c["outcome"]
                if c["name"] == "files-checksummed" and detail == NO_MANIFEST:
                    access = f"; access {rec['origin']['access']}" if rec else ""
                    detail = f"no file address is published to us ({NO_MANIFEST}{access})"
                return f"{c['name']}: {detail}"
    return ""
