# E03 evidence

- `mutations.txt`: one mutation per guard, the named test fails, the source is restored
  (`/tmp` runner; each line is `outcome | mutation | file | test`).
- `factpages_ids.txt`: the 9869 `NPDID_wellbore` of the FactPages table "Wellbore – All – long list"
  (`https://factpages.sodir.no/en/wellbore/tableview/wellbore_all_long`, CSV, 23 Oct 2026), the
  publisher's second statement of its count. It equals the WFS `numberMatched` (9869) and the
  wellbore ids in `outlines/sodir__factpages.geojson` drawn plus listed unplaced (9805 + 64): the
  symmetric difference is empty.
- `norway.png`: the site after `make build`, Sodir selected, solid derived outlines.
- `status.txt`: `uv run osd status` after the `osd verify --outlines` run of 23 Oct 2026.
