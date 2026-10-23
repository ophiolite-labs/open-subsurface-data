## E12 Catalogue into a workspace — DEFERRED · Kernel, cross-repo · strategy at lane open · one Codex round

Authority: owner direction 23 Oct ("pull references of that data into their private workspace …
read-only access … derive products … push back"); Ophiolite E72a (source bindings), E73/E65
(fixed address per version), E69 (versions), E36/E79/E80 (where a person's workspace runs).

**Outcome.** A person binds a catalogue collection to their Ophiolite project as a read-only
source, works on a curve or a slice without copying the dataset, derives a new asset and keeps it
in their own project with provenance pointing at the catalogue item and version. The read is
intentional (check, get), nothing updates itself.

**Context today (23 Oct, from program memory; verify at lane open).** Ophiolite source bindings
exist for connected databases (E39–E42) and remote sources (E100a's Workspace remote source);
E36 public tenancy is deferred; E79 gives a local instance, E80 an own instance. Cross-instance
binding does not exist and is out of scope here: the catalogue is static HTTP, so any instance
can read it.

**The design the lane must map to.**
1. A catalogue collection is a source kind in Ophiolite ("Open Subsurface Data"), bound by the
   STAC collection address; items are read on demand through E06's manifest reader and, for
   curves, E100's ranged reads over mirrored files.
2. Derived assets are ordinary E69 versions whose E122 provenance names catalogue item id and
   `catalog_version`; "check" compares `catalog_version` and shows what changed, applies nothing.
3. Rights follow E09's mapping; a derived asset from a share-alike item inherits the licence in
   its rights-basis.
4. Where it runs: the E79 try-it instance first (no hosted sign-up needed), E80 second, hosted
   when E36 lands.

**Acceptance (frozen at lane open from the Ophiolite journey fixtures, by hand).**
- Bind F3, open one well's gamma-ray curve through a ranged read (request count below the
  file's chunk count), run a notebook cell that derives a smoothed curve, save it: the new
  version's provenance names the F3 item id and the catalogue commit.
- Change the catalogue fixture's commit: "check" lists F3 as changed; nothing in the project moves.
- A derived asset from F3 shows CC-BY-SA-4.0 in its rights-basis; one from Teapot Dome shows
  public domain with no attribution requirement.

**Out of scope.** Cross-instance bindings, hosted compute next to the data, seismic beyond E10.

**Stop rules.** Ophiolite E36 and E79 both unavailable to the lane: stop, the epic stays
deferred.

**Ownership and dependencies.** One Ophiolite lane (chartered in the Ophiolite program) and a small
lane here for whatever the reader needs. Depends on E09, E10 for slices, and Ophiolite E36 or E79.

**Evidence to inspect.** The Ophiolite journey test; the provenance record; the rights-basis views.
