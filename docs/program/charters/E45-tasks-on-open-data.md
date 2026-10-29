## E45 Tasks on open data: a graded exercise beside a starter pack, taken in Ophiolite, its result counted here — QUEUED (after E42 publishes the first real pack; the catalogue half of a cross-repo pair with Ophiolite E135; Kernel for `task/1` and the submission path, the site pages Surface; strategy at lane open, one Codex round for the kernel part)

Authority: owner direction 26 Oct 2026 (evening) and "go for it" 29 Oct, given to the Ophiolite planner
(ophiolite-1e) and chartered there as family "Learning from the record" (Ophiolite E132–E136, D79–D81):
the owner wants the software free and is interested in collecting, under consent, how experts work on
real data; graded tasks on open packs are the part that lives in the catalogue. Family "Ready for your
tools" R-T1 (generated, never hand-made), R-T3 (the decision log is part of the pack), R-T6 (free, no
account, no key); E40 (starter/1), E42 (the F3 pack), E43 (starter pages); OSD-D23 (free; the paid
question reopens on evidence) and OSD-D24; Ophiolite R-L4 (pseudonymous outside) and R-L5 (open data
only); AGENTS.md (site is one HTML, one JS, one CSS; network only where stated).

**Outcome.** Beside a starter pack, the site lists one or more tasks: a sentence a geoscientist would
recognise ("Compute shale volume for the three F3 wells and compare with dGB's published curve; accept
within 0.05"), the application it suits, the time it takes, and what counts as done. A person takes it
in Ophiolite (`ophiolite tasks take <url>`, Ophiolite E135) and, when they are done, sends the task
result back; the pack's page shows how many results have come in and how many were accepted, never who.
A maintainer writes a task as a YAML record next to the pack; a job validates it and publishes it.

**Context today (verified in code on `origin/main` `cd218cf`, 29 Oct).**

- `schema/starter.schema.json` (E40, merged 28 Oct) describes a pack: inputs by digest, decisions,
  targets, licence, oracle. `src/osd/starters.py` builds `starters.json`; `site/starters.html` lists
  packs (E43, merged on fixture packs, PR #84). No `task` schema, record or page exists (`ls schema`,
  `ls site`, `grep -ri task src site` → nothing but the word in prose).
- Submissions today: three issue forms in `.github/ISSUE_TEMPLATE` (`dataset.yml`,
  `starter-request.yml`, `takedown.yml`) and pull requests; nothing receives a file.
- `src/osd/verify.py` and the `verify` workflow are the only network paths (AGENTS.md); `make check`
  is the gate, offline.
- Ophiolite's half (E135, chartered 29 Oct, queued after its E134): `ophiolite tasks take` reads a
  `task/1` document, makes a project from the pack with the task's outcome declared, and the taker's
  first verdict assembles `ophiolite.task-result/1` {task id and digest, the version, the outcome
  state, the verdict with reason, the check outcome, a values-mode trajectory under the taker's
  consent or null, the taker's pseudonym}; `ophiolite tasks deliver` writes it to disk or posts it.

**The design the strategy must map to.**

1. *`task/1` (`schema/task.schema.json`), one YAML per task under `starters/<pack>/tasks/<id>.yaml`.*
   Fields: `id`, `pack` (id and `starter.json` digest), `title` (one sentence), `instruction` (plain
   words, at most 1200 characters), `kind` (the expected result kind, Ophiolite's canonical kinds as
   `starter/1` names them), `outcome` (an Ophiolite `outcome/1` body: rule name and settings, copied
   verbatim, validated here only as JSON with the three required keys), `reference` (optional: a file
   in the pack by digest, rules and tolerance in Ophiolite's check vocabulary), `applications` (which
   targets suit it), `time` (words: "an hour", "an afternoon"), `author` (maintainer handle). A task
   over a pack whose licence record says redistribution is not allowed fails validation (R-L5).
2. *Published projection.* The build writes `tasks.json` (every valid task whole, plus per task the
   counts from design 4) beside `starters.json`; records and packs gain a `tasks` key with ids only.
   The site holds no task text of its own.
3. *The pages (Surface).* On `site/starters.html`, each pack with tasks gets a "Tasks" list: title,
   application, time, what counts as done (the outcome in words), the counts, and the one command to
   take it (`ophiolite tasks take https://opensubsurfacedata.org/data/tasks/<id>.json`). The task
   document is served at that address as JSON, so Ophiolite reads it by URL or from a dropped file.
4. *Results come in by pull request or issue form, never by an endpoint (AGENTS.md: no server).*
   `osd task-result check <file>` validates an `ophiolite.task-result/1` file against the task (task
   digest, pack digest, kind, the pseudonym present, no person name or email anywhere in the file,
   trajectory either null or a `values` folder reference under 50 MB); a new issue form
   `task-result.yml` takes the file as an attachment and a job runs the check and, when it passes,
   commits the file under `results/<task>/<pseudonym>-<n>.json` and reopens the build. Counts in
   `tasks.json` are derived from `results/` (accepted = the file's outcome state and verdict both
   accepted). Nothing in a result file is shown on the site except the counts.
5. *Words.* "Task" everywhere; "exercise", "challenge", "benchmark" and "leaderboard" never appear.

**Acceptance.**

1. `make check` validates `starters/<fixture-pack>/tasks/shale-volume.yaml` and refuses, each with its
   own sentence, a task over a restricted-licence pack, a 1201-character instruction, an unknown
   kind, an `outcome` without its three keys, a `reference` naming a digest the pack does not hold
   (five mutations).
2. The build writes `tasks.json` with one task, counts `{received: 0, accepted: 0}`, and serves
   `site/data/tasks/shale-volume.json` byte-equal to the projection's entry.
3. `osd task-result check fixtures/task-result-accepted.json` passes; the same file with the task
   digest changed, with a person name inserted in any string field, with `trajectory` pointing
   outside the folder, and with a 51 MB folder are each refused with their own sentence (four
   mutations); after the file is placed under `results/`, the build's counts read `{received: 1,
   accepted: 1}`; a rejected-verdict file gives `{received: 2, accepted: 1}`.
4. Playwright: the F3 fixture pack's page shows the task with the counts and the take command;
   screenshot committed (R5).
5. The issue form exists, the job runs the check on a fixture attachment in CI (offline, the file in
   the repository), and a failing check comments the sentence and commits nothing.

**Out of scope.** Payment or credit (OSD-D23; Ophiolite D80); naming or ranking takers; tasks over
licensed packs (R-L5, never); a server endpoint (a later decision if issue-form volume demands it;
reopened by twenty results in a month); writing the Ophiolite side (E135); scores beyond accepted or
rejected.

**Stop rules.** The lane stops when: E42's real pack is not published (then fixture packs only, and the
counts stay zero in public: the task list is hidden until a pack is real, as E43 hides starters);
Ophiolite E135's `task-result/1` is not closed at lane open (then `task/1` and the check land against
E135's charter fields and the result path waits); the result check cannot prove "no person name" without
a list it does not have (then the check is limited to the fields Ophiolite declares pseudonymous and
says so).

**Ownership and dependencies.** Coding lane; paths `schema/task.schema.json` (new),
`src/osd/tasks.py` (new), `src/osd/build.py` (the projection), `src/osd/cli.py` (`task-result check`),
`site/starters.html`, `site/app.js`, `site/data/tasks/` (generated, not committed, R7),
`starters/**/tasks/`, `results/` (new), `.github/ISSUE_TEMPLATE/task-result.yml`,
`.github/workflows/task-result.yml`, `tests/test_tasks.py`, `tests/site/`. Depends on E40 and E43
(merged); E42 (queued) for the first real pack; Ophiolite E135 for the result files (queued there after
E134).

**Evidence to inspect.** `schema/starter.schema.json`, `src/osd/starters.py`, `src/osd/build.py`,
`site/starters.html`, `.github/ISSUE_TEMPLATE/starter-request.yml`; Ophiolite (read only):
`docs/program-2026-09-25/EPICS.md` sections E132–E136 at the Ophiolite commit the handoff names.
