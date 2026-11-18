"""Exact-enough all-in preflop equities for a set of classic matchups (Monte Carlo, 60k boards each)."""
import json
import random

import eval7

RANKS = "AKQJT98765432"
SUITS = "shdc"
TRIALS = 60_000

# Matchup families players are expected to know, as (hand class, hand class)
FAMILIES = {
    "Pair vs two overcards": [("QQ", "AKo"), ("JJ", "AKs"), ("TT", "AQo"), ("77", "AKo"), ("22", "AKs"), ("99", "KQs"), ("55", "JTs")],
    "Pair vs two undercards": [("AA", "KQs"), ("KK", "JTs"), ("QQ", "76s"), ("TT", "98s"), ("AA", "72o"), ("JJ", "T9o")],
    "Pair vs smaller pair": [("AA", "KK"), ("KK", "77"), ("QQ", "22"), ("88", "55")],
    "Pair vs one overcard": [("JJ", "AJo"), ("TT", "AKo"), ("88", "A7s"), ("66", "K2s"), ("QQ", "AQs"), ("99", "A9o")],
    "Domination (shared card)": [("AKo", "AQo"), ("AKo", "AJs"), ("KQo", "KJo"), ("AQs", "QJs"), ("AJo", "JTs"), ("A5s", "A2o")],
    "Overcards vs undercards": [("AKo", "QJs"), ("AQo", "T9s"), ("KQo", "65s"), ("AJs", "87s"), ("A2o", "KQs")],
    "Pair vs over and under": [("88", "A5s"), ("66", "K4o"), ("TT", "J7s")],
    "Suited vs offsuit twin": [("AKs", "AKo"), ("76s", "76o")],
}


def deal(hand_class: str, used: set) -> list[str]:
    a, b = hand_class[0], hand_class[1]
    for _ in range(200):
        if a == b:
            s1, s2 = random.sample(SUITS, 2)
        elif hand_class.endswith("s"):
            s1 = s2 = random.choice(SUITS)
        else:
            s1, s2 = random.sample(SUITS, 2)
        cards = [a + s1, b + s2]
        if not (set(cards) & used):
            return cards
    raise RuntimeError(hand_class)


def equity(h1: list[str], h2: list[str]) -> tuple[float, float]:
    c1 = [eval7.Card(c) for c in h1]
    c2 = [eval7.Card(c) for c in h2]
    deck = eval7.Deck()
    for c in c1 + c2:
        deck.cards.remove(c)
    w1 = ties = 0
    rest = deck.cards
    for _ in range(TRIALS):
        board = random.sample(rest, 5)
        v1, v2 = eval7.evaluate(c1 + board), eval7.evaluate(c2 + board)
        if v1 > v2:
            w1 += 1
        elif v1 == v2:
            ties += 1
    return (w1 + ties / 2) / TRIALS, ties / TRIALS


random.seed(7)
out = []
for fam, pairs in FAMILIES.items():
    for x, y in pairs:
        for _ in range(2):  # two suit layouts per matchup, since shared suits matter
            h1 = deal(x, set())
            h2 = deal(y, set(h1))
            e, t = equity(h1, h2)
            out.append({"family": fam, "a": h1, "b": h2, "a_class": x, "b_class": y, "eq_a": round(e, 3), "tie": round(t, 3)})
            print(fam, h1, h2, round(e * 100, 1), flush=True)
json.dump(out, open("/home/claude/solver/preflop_equity.json", "w"))
