"""What changed on the site, and from which build (E54, OSD-D42).

The site publishes on every merge to main; this module lets it say so.

  build.json    {"commit": "<7 hex>", "date": "<YYYY-MM-DD>", "time": "<HH:MM> UTC"}: the commit the site
                was built from (GITHUB_SHA in the Pages workflow, else `git rev-parse HEAD` in the checkout)
                with the commit's own committer date in UTC, never the clock, so one commit builds one
                file. Neither a variable nor git: no file, and site/foot.js shows no line.
  changes.json  {"changes": [...]}: every changes/<YYYY-MM-DD>-<slug>.yaml, newest first. Each entry
                has exactly `date`, `title` (one plain sentence of what a person can now do, at most
                140 characters), `link` (an address on the site, beginning with "/") and `pr` (the pull
                request number). A bad entry refuses the build, naming its file.

`osd changes --since <date>` prints the daily note from the committed entries only (no timer, no
sending: the supervisor runs it and places the text). No network anywhere here.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

from . import paths

ROOT = paths.ROOT   # the checkout the stamp is read from
CHANGES_DIR = ROOT / "changes"
GIT = "git"
SITE = "https://opensubsurfacedata.org"
KEYS = ("date", "title", "link", "pr")
TITLE_MAX = 140
FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9][a-z0-9-]*\.yaml$")
SHA = re.compile(r"^[0-9a-f]{7,40}$")


class ChangeError(ValueError):
    """An entry in changes/ that the build refuses; the message starts with the file name."""


# ---- The stamp ------------------------------------------------------------------------------------

def stamp(root: Path | None = None, env: Mapping[str, str] | None = None, git: str | None = None) -> dict | None:
    """build.json's content, or None when neither GITHUB_SHA nor git names a commit with a date."""
    root, env, git = root or ROOT, os.environ if env is None else env, git or GIT

    def run(*args: str) -> str | None:
        try:
            r = subprocess.run([git, "-C", str(root), *args], capture_output=True, text=True, check=False,
                               env={**os.environ, "GIT_CEILING_DIRECTORIES": str(Path(root).resolve().parent)})
        except OSError:
            return None
        return r.stdout.strip() if r.returncode == 0 else None

    sha = (env.get("GITHUB_SHA") or "").strip().lower() or run("rev-parse", "HEAD")
    if not sha or not SHA.match(sha):
        return None
    seconds = run("show", "-s", "--format=%ct", sha)
    if not seconds or not seconds.isdigit():
        return None
    when = datetime.fromtimestamp(int(seconds), UTC)
    return {"commit": sha[:7], "date": when.strftime("%Y-%m-%d"), "time": when.strftime("%H:%M") + " UTC"}


# ---- The entries ----------------------------------------------------------------------------------

def check(path: Path) -> dict:
    """One entry, as changes.json carries it, or ChangeError naming the file."""
    name = path.name

    def bad(why: str) -> ChangeError:
        return ChangeError(f"changes/{name}: {why}")

    if not FILE.match(name):
        raise bad("the file name is not <YYYY-MM-DD>-<slug>.yaml (lower-case slug)")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise bad(f"not YAML ({e})") from None
    if not isinstance(doc, dict):
        raise bad("not a mapping of date, title, link, pr")
    missing = [k for k in KEYS if k not in doc]
    if missing:
        raise bad("missing " + ", ".join(missing))
    extra = sorted(str(k) for k in doc if k not in KEYS)
    if extra:
        raise bad("unknown key " + ", ".join(extra) + " (only date, title, link, pr)")
    day = doc["date"]
    if isinstance(day, str):
        try:
            day = date.fromisoformat(day)
        except ValueError:
            raise bad(f"date {doc['date']!r} is not YYYY-MM-DD") from None
    if not isinstance(day, date) or isinstance(day, datetime):
        raise bad(f"date {doc['date']!r} is not YYYY-MM-DD")
    if day.isoformat() != FILE.match(name).group(1):
        raise bad(f"date {day.isoformat()} is not the date in the file name")
    title, link, pr = doc["title"], doc["link"], doc["pr"]
    if not isinstance(title, str) or not title.strip():
        raise bad("title is not a sentence")
    if len(title) > TITLE_MAX:
        raise bad(f"title is {len(title)} characters, over {TITLE_MAX}")
    if not isinstance(link, str) or not link.startswith("/") or link.startswith("//"):
        raise bad(f"link {link!r} does not begin with / (an address on the site)")
    if not isinstance(pr, int) or isinstance(pr, bool) or pr < 1:
        raise bad(f"pr {pr!r} is not a pull request number")
    return {"date": day.isoformat(), "title": title.strip(), "link": link, "pr": pr}


def load(changes_dir: Path | None = None) -> list[dict]:
    """Every entry, newest first (date, then pull request, then file name, all descending)."""
    changes_dir = changes_dir or CHANGES_DIR
    files = sorted(Path(changes_dir).glob("*.yaml")) if Path(changes_dir).is_dir() else []
    entries = [(check(p), p.name) for p in files]
    entries.sort(key=lambda e: (e[0]["date"], e[0]["pr"], e[1]), reverse=True)
    return [e for e, _ in entries]


def write(out_dir: Path, changes_dir: Path | None = None, root: Path | None = None,
          env: Mapping[str, str] | None = None, git: str | None = None) -> dict | None:
    """out_dir/changes.json always; out_dir/build.json when the build has a stamp (else removed)."""
    entries = load(changes_dir)
    (out_dir / "changes.json").write_text(json.dumps({"changes": entries}, indent=1, ensure_ascii=False) + "\n")
    s = stamp(root, env, git)
    target = out_dir / "build.json"
    if s:
        target.write_text(json.dumps(s) + "\n")
    else:
        target.unlink(missing_ok=True)
    return s


# ---- The daily note -------------------------------------------------------------------------------

def utc_today() -> date:
    return datetime.now(UTC).date()


def built_words(s: dict | None) -> str:
    if not s:
        return "no build stamp (no commit in this checkout)"
    d = date.fromisoformat(s["date"])
    return f"Built {d.day} {d.strftime('%b')} {d.year} from {s['commit']}"


def note(entries: list[dict], since: str, top: int = 3, today: date | None = None, build: dict | None = None) -> str:
    """The plain-text note: the date, up to `top` sentences (the newest, one per pull request) with
    their full addresses, and the foot line the live site should show."""
    today = today or utc_today()
    picked, prs = [], set()
    for e in entries:   # already newest first
        if e["date"] < since or e["pr"] in prs:
            continue
        prs.add(e["pr"])
        picked.append(e)
        if len(picked) == top:
            break
    lines = [f"Open Subsurface Data: worth opening today ({today.isoformat()})", ""]
    if picked:
        lines += [f"- {e['title']}\n  {SITE}{e['link']}" for e in picked]
    else:
        lines.append(f"Nothing new on the site since {since}.")
    lines += ["", f"The live site should say at its foot: {built_words(build)}"]
    return "\n".join(lines) + "\n"
