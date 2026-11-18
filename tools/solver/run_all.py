"""Solve every flop in the list, one at a time, skipping ones already done."""
import os
import random
import subprocess
import sys

GEN = "/home/claude/solver/gen/target/release/gen"
OUT = "/home/claude/solver/out"
ranges = open("/home/claude/solver/ranges.txt").read().split("\n")
MATCHUPS = {
    "BTN": (ranges[1], ranges[0]),   # (OOP = BB calling range, IP = opener)
    "UTG": (ranges[3], ranges[2]),
}

BTN_FLOPS = """As7d2c Ah8c3d Ks7d2c Qs6d2c Kc9h4d AsKd4c AhQc5d KhQd3s KsKd5c 7s7d2c QsQh8d 3c3d9h
AsAc6d As9s4s Kh8h3h 9c7c3c QdJd5d Jh9h8c Ts9s7d 8d7d5c 6h5h4c QsJhTd Td9c6d 7h4d2c 8s5d2c
9c5h2d Jc7d3h Th6c2d 9s8d2h KsQdTc AhKcQd KhJd9c Ah9h5c AsTs7c 5s4d3c JsTd4c""".split()
UTG_FLOPS = """As7d2c Ks7d2c Qs6d2c 7h4d2c 8d7d5c 6h5h4c Jh9h8c Ts9s7d KhQd3s 9c5h2d KsKd5c 7s7d2c
As9s4s 8s5d2c AhKcQd Th6c2d""".split()

RANKS = "23456789TJQKA"
SUITS = "cdhs"


def turns_for(flop: str) -> str:
    rng = random.Random(flop)
    board = {flop[i:i + 2] for i in (0, 2, 4)}
    deck = [r + s for r in RANKS for s in SUITS if r + s not in board]
    return ",".join(rng.sample(deck, 2))


jobs = [("BTN", f) for f in BTN_FLOPS] + [("UTG", f) for f in UTG_FLOPS]
if len(sys.argv) > 1:
    jobs = jobs[: int(sys.argv[1])]
for who, flop in jobs:
    path = f"{OUT}/{who}_{flop}.json"
    if os.path.exists(path):
        continue
    oop, ip = MATCHUPS[who]
    subprocess.run([GEN, oop, ip, flop, turns_for(flop), path + ".tmp", "0.01", "300"], check=True)
    os.rename(path + ".tmp", path)
    print(f"done {who} {flop}", flush=True)
print("ALL DONE", flush=True)
