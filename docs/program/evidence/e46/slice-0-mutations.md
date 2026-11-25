# E46 slice 0: one mutation per guard

Each mutation applied alone to commit b716949, the named tests run, the file restored. Script: a
text replacement per row (strings in the PR body); all fifteen RED.

| Mutation | File | Result |
|---|---|---|
| hole ignored (outer ring only) | `src/osd/areas.py` | RED: 1 failed, 25 deselected in 4.81s |
| edge crossing skipped | `src/osd/areas.py` | RED: 1 failed, 25 deselected in 4.69s |
| area inside a feature polygon skipped | `src/osd/areas.py` | RED: 1 failed, 25 deselected in 0.04s |
| bbox middle used with outlines | `src/osd/areas.py` | RED: 1 failed, 25 deselected in 0.05s |
| national record uses its bbox | `src/osd/areas.py` | RED: 1 failed, 25 deselected in 0.05s |
| country fallback removed | `src/osd/areas.py` | RED: 1 failed, 26 deselected in 0.05s |
| antimeridian cut skipped | `src/osd/areas.py` | RED: 1 failed, 26 deselected in 0.04s |
| 180-degree area edge check removed | `src/osd/areas.py` | RED: 1 failed, 26 deselected in 0.08s |
| duplicate-id check removed | `src/osd/areas.py` | RED: 1 failed, 26 deselected in 0.07s |
| empty licence admitted (minLength dropped) | `schema/area.schema.json` | RED: 1 failed, 26 deselected in 0.07s |
| national without country admitted | `schema/record.schema.json` | RED: 1 failed, 72 deselected in 0.05s |
| national as a string admitted | `schema/record.schema.json` | RED: 1 failed, 72 deselected in 0.05s |
| province country not checked | `src/osd/areas.py` | RED: 1 failed, 26 deselected in 0.07s |
| empty areas/ still adds the key | `src/osd/areas.py` | RED: 1 failed, 26 deselected in 0.05s |
| index lists an area that holds nothing | `src/osd/areas.py` | RED: 1 failed, 25 deselected in 0.06s |
