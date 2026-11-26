Fixtures for E54 (`tests/test_changes.py`, `tests/site/foot.test.mjs`).

- `entries/`: three entries on three days, the folder `osd build` reads as `changes/`.
- `changes.json`, `build.json`: what `osd build` writes from them, with `GITHUB_SHA` naming the
  fixture commit (`tests/test_changes.py` makes it: an empty tree, fixed names and the date
  2026-11-26T14:03:00Z). The site test serves both as `data/`.
- `note.txt`: `osd changes --since 2026-11-25 --top 3` over `entries/`, today 2026-11-26.
