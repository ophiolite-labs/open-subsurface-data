"""Compare branch-run results (dir) with main's stored results (git ref): level changes and robots lines."""
import json, pathlib, subprocess, sys
branch, ref = pathlib.Path(sys.argv[1]), sys.argv[2]
names = subprocess.run(["git", "ls-tree", "--name-only", ref], capture_output=True, text=True).stdout.split()
rows, robots_diff = [], []
for n in sorted(set(names) | {p.name for p in branch.glob("*.json")}):
    a = json.loads(subprocess.run(["git", "show", f"{ref}:{n}"], capture_output=True, text=True).stdout or "null")
    p = branch / n
    b = json.loads(p.read_text()) if p.exists() else None
    la, lb = a and a["level"], b and b["level"]
    ra = {c["name"]: c["detail"] for c in (a or {}).get("checks", []) if "robots" in c["detail"]}
    rb = {c["name"]: c["detail"] for c in (b or {}).get("checks", []) if "robots" in c["detail"]}
    if la != lb:
        rows.append((n[:-5].replace("__", "/"), la, lb, ra, rb, a, b))
    elif ra != rb:
        robots_diff.append((n[:-5].replace("__", "/"), la, ra, rb))
print("LEVEL CHANGES", len(rows))
for r in rows:
    print(r[0], r[1], "->", r[2]); print("  main:", r[3]); print("  branch:", r[4])
    fa = {c["name"]: (c["outcome"], c["detail"][:160]) for c in (r[5] or {}).get("checks", [])}
    fb = {c["name"]: (c["outcome"], c["detail"][:160]) for c in (r[6] or {}).get("checks", [])}
    for k in fa:
        if fa[k] != fb.get(k): print("   ", k, fa[k], "=>", fb.get(k))
print("ROBOTS LINE CHANGES (same level)", len(robots_diff))
for r in robots_diff:
    print(r[0], r[1]); print("  main:", r[2]); print("  branch:", r[3])
