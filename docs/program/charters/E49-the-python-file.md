## E49 The Python file: `import osd; osd.get("opm/norne")`, and the file the bag writes — CHARTERED 25 Nov 2026 (Kernel; strategy at lane open; one Codex round)

Authority: family `MAP-AS-A-SHOP-family.md` (journey J12; R-S6, R-S8); OSD-D30, OSD-D32; board
Shop 04 (`b6.py`): the file shown to the owner reads

```python
# open-subsurface-data, made 25 Nov 2026 for 2 datasets
import osd

norne = osd.get("opm/norne")        # 5 files from our server, checked
nlog  = osd.get("nlog/nlog", area="F03") # from the publisher

logs = nlog.well_logs()    # a table per well
print(logs["F03-04"].head())
```

and the board says: "It downloads the files to the own computer of the person, checks each file
against the fingerprint we recorded, and opens them. The data then sits locally. Nothing of theirs
is on our server. A dataset with a sign-in is left out with a line that says where to sign in."
Builds on E06 (`osd get`, manifest/4), E07 (mirror), E23/E30 (listings and checksums), E40 (the
Python target of a starter pack).

**Outcome.** A person with Python installs the package from the repository, runs the file the bag
gave them, and has the files of the chosen datasets on their own disk, each checked against the
recorded sha256, with a handle that says what arrived and opens the common kinds. The file is
short enough to read and is the same whether the site or the command line wrote it.

**Context today (verified on `origin/main` `fd69de4`).** `src/osd/get.py` has `get(m: Manifest,
dest, opener)` returning outcomes per entry, `attribution`, `summary`; `src/osd/manifest.py` has
`from_catalog(ids, catalog_dir, catalog_url)` which builds a manifest from a built catalogue on
disk. `src/osd/__init__.py` exports only `__version__`. There is no call that takes a dataset id
and reads the published catalogue, no reader, and the package name `osd` is installed from the
repository (`uv sync`); it is not on PyPI (OSD-D32). The lane's first act is to write down, in the
strategy, exactly what E06 gives and what is missing; this charter's design is corrected there if
the code disagrees.

**The design the charter fixes.**

1. *`osd.get(id, dest=None, area=None, catalog=None) -> Dataset`.* Reads the published catalogue
   (`https://opensubsurfacedata.org/data/…`, or `catalog=` a local build directory or another URL),
   builds the same manifest entry `osd manifest` would, and fetches through the E06 path: mirror
   copy first when one is held, else the publisher; sha256 checked where one is recorded; resumable
   and idempotent (a file already present with the right digest is not fetched again). `dest`
   defaults to `./osd-data/<publisher>/<dataset>/`. This is the intentional retrieval AGENTS.md
   already names for `osd get`; the network line gains "`osd.get(...)`, the same retrieval called
   from Python" and nothing else.
2. *What cannot be fetched is said, not raised.* A dataset whose access is registration, request
   or purchase returns a `Dataset` with no files and `todo` holding the sentence and the address
   where to sign in or ask; printing the dataset shows it. A checksum mismatch raises.
3. *`Dataset`.* `id`, `title`, `licence`, `attribution` (the E06 text), `files` (path, size,
   sha256, source: mirror or publisher, checked: yes/no/no checksum recorded), `path`, `todo`,
   and readers that exist only where the files support them: `well_logs()` (LAS files → a dict of
   tables by well name), `segy()` (a list of opened SEG-Y handles or their paths with headers),
   `tables()` (CSV and similar). Readers import their library when called (`lasio`, `segyio`,
   `pandas`) and say in one line what to install when it is missing; they are an optional extra
   `osd[readers]`, never a dependency of the catalogue tools.
4. *`area=`.* Honoured only where the catalogue can honour it without guessing: the dataset has a
   listing whose entries carry a name, block or position that matches (for a register with
   committed outlines: the wells whose name starts with, or that lie in, the named block or area
   id from E46 when that has merged). Where it cannot, `osd.get` refuses with the sentence "this
   dataset cannot be narrowed by area yet" rather than fetching everything. Slice 3; the first two
   slices accept only `area=None`.
5. *The file.* `osd script <id> [<id> …] [-o file.py]` writes the Python file: a comment line with
   the date and count, the install line (`pip install "osd[readers] @ git+https://github.com/
   ophiolite-labs/open-subsurface-data"`), `import osd`, one `osd.get` line per dataset with a
   trailing comment that states where the files come from and how many ("5 files from our mirror,
   checked" / "from the publisher" / "sign-in needed: left out"), and for the first dataset that
   has a reader, two lines that use it. The text is a pure function of the catalogue and the ids:
   `osd.script.render(catalog, ids, today)`. The site writes the same text: the rule is specified
   in the charter's strategy as a table, the CLI's output for the fixture catalogue is committed as
   golden files, and the page's output is tested equal to them (as E06 does for manifests).
6. *Slices.* 1: `osd.get` and `Dataset` without readers, `osd script`, golden files. 2: readers
   and the extra. 3: `area=`. 4 (after E47 merges; surface, small): the bag's "Get a Python file"
   button in `site/shop.js`, lighting J12.

**Acceptance.** Offline; tests inject the opener and a fixture catalogue.

1. `osd.get("fx/mirrored")` against the fixture catalogue fetches from the mirror transport,
   verifies sha256 and returns files marked checked; a second call fetches nothing (opener call
   count 0).
2. `osd.get` of a registration fixture returns no files and a `todo` with the publisher's address;
   nothing is requested from the origin.
3. A corrupted byte raises with the file name and both digests (mutation: the check removed makes
   the test fail).
4. `osd.get(id)` and `osd get <manifest for id>` leave byte-identical trees and report the same
   outcomes (one code path, asserted).
5. `osd script` for three fixture ids equals the committed golden file; dates and counts come from
   arguments, so the golden file is stable.
6. The golden file, executed by the test in a subprocess against the fixture catalogue with an
   injected transport, exits 0 and prints the first rows of a well log (slice 2).
7. `well_logs()` without `lasio` installed raises one sentence naming the extra; `import osd` and
   every existing command work without the extra installed (test in an environment without it).
8. `area="F03"` on a fixture register with named wells returns only those wells' files; on a
   dataset without a matching listing it refuses with the sentence and requests nothing (slice 3).
9. Slice 4: the page's file for the same three ids equals the golden file; J12 in
   `shop.test.mjs` is lit; a sign-in dataset in the bag appears as the comment line.
10. A real run, recorded in the PR (not in the gate): the file for `opm/norne` run on the
    controller fetches the mirror's files and reports them checked.

**Out of scope.** Publishing to PyPI (OSD-D32, an owner item if wanted); readers for kinds beyond
LAS, SEG-Y and tables; reading into Ophiolite types; any server-side subsetting.

**Stop rules.** If `import osd` cannot stay free of the reader libraries, stop. If the published
catalogue lacks what `from_catalog` needs over HTTP (it reads a directory today), write the
smallest list of files to fetch to the inbox and continue on the default "fetch `records.json`,
`collections.json`, `mirror.json`, cached per session".

**Ownership and dependencies.** Coding lane (kernel). Paths: `src/osd/__init__.py`,
`src/osd/api.py`, `src/osd/script.py`, `src/osd/readers.py` (new), `src/osd/get.py`,
`src/osd/manifest.py` (only what `from_catalog` over a URL needs), `src/osd/cli.py` (`script`
subcommand only; E46 holds the `areas` subcommand in the same file: one function each, rebase on
the other's merge), `pyproject.toml`, `uv.lock`, `tests/test_api.py`, `tests/test_script.py`
(new), `tests/fixtures/api/**` (new), `AGENTS.md` and `CLAUDE.md` (the one network sentence,
announced in the PR title), `README.md` (a "From Python" section), `docs/program/charters/E49-*`,
`docs/program/evidence/e49/**`; slice 4 only: `site/shop.js` (bag button), `tests/site/shop.test.mjs`
(J12), after E47 has merged and released them. Depends on nothing for slices 1–2; slice 3 reads
E46's area ids if merged; slice 4 on E47.

**Evidence to inspect.** The golden file; the real Norne run; the mutation list.
