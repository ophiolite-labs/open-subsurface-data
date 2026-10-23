## E10 Seismic slices — DEFERRED · Kernel · strategy at lane open · one Codex round

Authority: owner direction 23 Oct ("only a slice from a 3D cube rather than the entire dataset");
Ophiolite E100 (ranged reads at a resolution).

**Outcome.** In a notebook, a person reads one inline, crossline or time slice of a mirrored
seismic volume through an HTTP byte-range read, without downloading the cube and without a
server of ours running.

**Context today (verified 23 Oct).** Nothing. E07 would hold mirrored SEG-Y, which cannot be
sliced without a full read. The analogue is Zarr over object storage (Pangeo); the subsurface
form is MDIO (Zarr-based) or OpenVDS (OSDU). Ophiolite reads ZGY (E123).

**The design the lane must map to.**
1. One chunked store format for mirrored volumes, Zarr-based, chosen at lane open with a
   measured comparison on F3 (file count, bytes, slice latency from the bucket): MDIO is the
   default candidate.
2. Conversion is an E07 mirror step with a fidelity check: 100 random traces compared sample by
   sample to the SEG-Y original, zero differences.
3. Reader: `osd.seismic.open(item_id)` returns an xarray-like object; a slice reads only the
   chunks it needs (asserted by counting HTTP requests in the test).
4. Cost line: bytes stored per volume and egress per slice, by hand, in the PR.

**Acceptance.**
- A time slice of F3 from the bucket completes in under 3 s on the VPS and issues fewer than
  (volume chunks / 10) range requests.
- The fidelity check passes on F3 and fails on a fixture with one altered sample (mutation).
- The notebook in `examples/` runs top to bottom in CI against a local store.

**Out of scope.** Hosted compute, interpretation, anything beyond slicing.

**Stop rules.** F3's licence (CC BY-SA) requires the converted store to carry the same licence:
record it in custody; if any candidate volume is `redistribution: unknown`, it is not converted.

**Ownership and dependencies.** Coding lane; paths `src/osd/seismic/**`, `examples/**`, tests.
Depends on E07 and OSD-D6. Deferred until E07 is merged and a second volume with `allowed` exists.

**Evidence to inspect.** The comparison table at lane open; the request count; the cost line.
