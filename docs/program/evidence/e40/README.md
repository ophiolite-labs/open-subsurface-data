# E40 evidence

- `starters.json`: the fixture build (`tests/fixtures/starters/`, custody snapshot `tests/fixtures/custody/`), written by `osd build`.
- records.json on that build: rmotc/teapot-dome starters ['rmotc/teapot-dome/python']; terranubis/f3-demo-2020 starters ['terranubis/f3-demo-2020/starter'].
- `osd-get.txt`: `osd get` on `osd manifest --starter terranubis/f3-demo-2020/starter` against a `LocalDirectory` store (test_pack_manifest_and_get).
- `mutations.md`: one line per refusal and guard.

Frozen schemas (sha256, pinned in tests/test_starters.py):

- `tests/fixtures/schema/starter-1.schema.json` f38b9bbce3adbeecc4aecacd1a1f367b6bdb2acaa157d68c200455becd766250
- `tests/fixtures/schema/custody-2.schema.json` c029a2033c310bfd048b4224603dcc01a5726958c8537792dc49d9ff3b822e11
- `tests/fixtures/schema/verification-7.schema.json` d87c42dd419ed1f6465b972c60464ecf8b9f1bc5a924b8a96ae86d65b4c2a49b
- `tests/fixtures/schema/custody-1.schema.json` 9711149e5d86a857c8210751267d7aaeb8c89ebed49cc6a3c2a37d6df1e791ff
- `tests/fixtures/schema/verification-6.schema.json` ec36887cd1aa205136a9501e5bf2bb8921e516a720b0885c2868a8511c20c7c9
