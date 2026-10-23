#!/usr/bin/env bash
# One Codex round on a kernel charter (ENGINEERING.md, "proof bar by class"). Read-only.
# Usage: tools/review-charter.sh docs/program/charters/E02-verifier-to-L2.md
# Writes <charter-stem>-CODEX-REVIEW.md next to the charter; the lane records dispositions in the charter.
set -euo pipefail
charter="$(readlink -f "$1")"
out="${charter%.md}-CODEX-REVIEW.md"
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
prompt="You are a fresh, independent senior reviewer of one epic charter in the Open Subsurface Data project (a verified catalogue of open subsurface datasets: YAML records -> verifier levels L0-L4 -> outlines -> STAC/GeoJSON catalogue -> static MapLibre map; Python package src/osd, tests in tests/, schemas in schema/). Read docs/ARCHITECTURE.md, docs/ENGINEERING.md, docs/program/PROGRAM.md, then the charter at ${charter}. VERIFY every 'exists' claim in its Context section against the code at HEAD (open the files; do not trust the document) and state the commit you verified against (git rev-parse HEAD). Report in Markdown: (1) Verdict: APPROVE / APPROVE WITH CHANGES / REWORK, one sentence why. (2) Factual errors about current code, with file:line evidence. (3) Design objections: an owner, boundary, format or contract choice that is unsafe or misplaced, each with a concrete alternative that stays within docs/ENGINEERING.md (no new CI stations, no server, standards over bespoke). (4) Acceptance lines that can pass vacuously or whose proposed test would stay green under the mutation it should catch. (5) Scope creep into another charter in docs/program/charters/. Be specific and terse; no praise; at most 60 lines. Do not modify any files."
codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort=medium --skip-git-repo-check --ephemeral -o "$out" "$prompt" </dev/null >"${out%.md}.log" 2>&1 || true
echo "review written to $out"
