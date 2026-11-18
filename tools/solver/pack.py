"""Pack the per-flop solver outputs into one compact gzipped JSON for the app."""
import glob
import gzip
import json
import os

OUT = "/home/claude/mental-math-practice-interface/data/poker_postflop.json.gz"


def compact(node):
    if not node:
        return None
    hands = node["hands"]
    wmax = max(v[0] for v in hands.values())
    return {
        "player": node["player"],
        "pot_bb": node["pot_bb"],
        "actions": node["actions"],
        "agg": [round(x, 3) for x in node["agg"]],
        "range_equity": node["range_equity"],
        # combo -> [relative weight, equity, freq per action]
        "hands": {k: [round(v[0] / wmax, 2), round(v[1], 3)] + [round(f, 2) for f in v[2:]]
                  for k, v in hands.items() if v[0] / wmax >= 0.005},
    }


flops = []
for path in sorted(glob.glob("/home/claude/solver/out/*.json")):
    who, _ = os.path.basename(path)[:-5].split("_")
    d = json.load(open(path))
    flops.append({
        "matchup": who,
        "flop": d["flop"],
        "exploitability_pct_pot": d["exploitability_pct_pot"],
        "nodes": {k: compact(v) for k, v in d["nodes"].items()},
        "turns": [{"card": t["card"], **{k: compact(t[k]) for k in ("oop_first", "ip_vs_check", "oop_vs_bet")}}
                  for t in d["turns"]],
    })

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with gzip.open(OUT, "wt") as f:
    json.dump({"flops": flops}, f, separators=(",", ":"))
print(len(flops), "flops,", os.path.getsize(OUT) // 1024, "KB")
