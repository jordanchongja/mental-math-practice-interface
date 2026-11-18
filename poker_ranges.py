"""Preflop strategy charts for the Poker tab.

Setting: 6-max cash, 100bb effective, opens to 2.5bb (SB opens to 3bb), no limping.

IMPORTANT: these are hand-written approximations of the shape typical solver
charts take for this setting, not output exported from a solver. They are a
sensible baseline to drill, not ground truth. To swap in your own charts
(free charts you trust, or ranges you exported from TexasSolver), edit the
SPOTS table below. Nothing else in the app needs to change.

Range syntax (the usual shorthand):
    "77"        one pair            "22+"     22 up to AA     "99-66"   99, 88, 77, 66
    "AKs"/"AKo" suited / offsuit    "A2s+"    A2s..AKs        "K9o+"    K9o..KQo
    "A5s-A2s"   A5s, A4s, A3s, A2s

Each spot is a list of (action, range, frequency). Frequencies for the same
hand add up; whatever is left over is a fold. A hand listed under two actions
at 0.5 each is a 50/50 mix, the way a solver plays many borderline hands.
"""

from __future__ import annotations

RANKS = "AKQJT98765432"            # high to low; index 0 = Ace
RANK_VAL = {r: 14 - i for i, r in enumerate(RANKS)}


# --------------------------------------------------------------------------
# Range-string parsing
# --------------------------------------------------------------------------

def _hand(hi: str, lo: str, kind: str = "") -> str:
    """Canonical name: 'AA', 'AKs', 'AKo' with the higher rank first."""
    if RANK_VAL[lo] > RANK_VAL[hi]:
        hi, lo = lo, hi
    return hi + lo if hi == lo else hi + lo + kind


def _expand_token(tok: str) -> list[str]:
    tok = tok.strip()
    if not tok:
        return []
    plus = tok.endswith("+")
    if plus:
        tok = tok[:-1]

    if "-" in tok:                                   # "99-66" or "A5s-A2s"
        a, b = tok.split("-")
        if a[0] == a[1]:                             # pairs
            hi, lo = sorted((RANK_VAL[a[0]], RANK_VAL[b[0]]), reverse=True)
            return [r + r for r in RANKS if lo <= RANK_VAL[r] <= hi]
        top, kind = a[0], a[2] if len(a) > 2 else ""
        hi, lo = sorted((RANK_VAL[a[1]], RANK_VAL[b[1]]), reverse=True)
        return [_hand(top, r, kind) for r in RANKS if lo <= RANK_VAL[r] <= hi]

    if tok[0] == tok[1]:                             # "77" or "22+"
        if not plus:
            return [tok]
        return [r + r for r in RANKS if RANK_VAL[r] >= RANK_VAL[tok[0]]]

    top, kick, kind = tok[0], tok[1], tok[2] if len(tok) > 2 else ""
    if not plus:
        return [_hand(top, kick, kind)] if kind else [_hand(top, kick, "s"), _hand(top, kick, "o")]
    # "K9s+" = K9s up to KQs (kicker climbs, stops below the top card)
    kinds = [kind] if kind else ["s", "o"]
    return [_hand(top, r, k) for k in kinds for r in RANKS
            if RANK_VAL[kick] <= RANK_VAL[r] < RANK_VAL[top]]


def expand(rng: str) -> list[str]:
    out: list[str] = []
    for tok in rng.split(","):
        out.extend(_expand_token(tok))
    return out


# --------------------------------------------------------------------------
# The 169 starting hands and the 13x13 grid
# --------------------------------------------------------------------------

def grid_hand(i: int, j: int) -> str:
    """Row i, column j of the standard chart: pairs on the diagonal,
    suited above it (top right), offsuit below it (bottom left)."""
    a, b = RANKS[i], RANKS[j]
    if i == j:
        return a + a
    return a + b + "s" if i < j else b + a + "o"


ALL_HANDS = [grid_hand(i, j) for i in range(13) for j in range(13)]
GRID_POS = {grid_hand(i, j): (i, j) for i in range(13) for j in range(13)}


def combos(hand: str) -> int:
    if len(hand) == 2:
        return 6
    return 4 if hand[2] == "s" else 12


# --------------------------------------------------------------------------
# Spots
# --------------------------------------------------------------------------

SPOTS: dict[str, dict] = {
    # ---- Raise first in (folded to you) ----
    "UTG open": {
        "group": "Open (folded to you)",
        "story": "Folded to you **under the gun**. Open or fold?",
        "actions": ["Raise", "Fold"],
        "chart": [
            ("Raise", "77+, A9s+, A5s-A4s, KTs+, QTs+, JTs, T9s, AJo+, KQo", 1.0),
            ("Raise", "66-22, A8s-A6s, A3s-A2s, K9s, Q9s, J9s, 98s, 87s, 76s, ATo, KJo", 0.5),
        ],
    },
    "HJ open": {
        "group": "Open (folded to you)",
        "story": "Folded to you in the **hijack**. Open or fold?",
        "actions": ["Raise", "Fold"],
        "chart": [
            ("Raise", "55+, A2s+, K9s+, Q9s+, J9s+, T9s, 98s, 87s, ATo+, KJo+, QJo", 1.0),
            ("Raise", "44-22, K8s-K7s, Q8s, J8s, T8s, 97s, 76s, 65s, A9o, KTo, QTo, JTo", 0.5),
        ],
    },
    "CO open": {
        "group": "Open (folded to you)",
        "story": "Folded to you in the **cutoff**. Open or fold?",
        "actions": ["Raise", "Fold"],
        "chart": [
            ("Raise", "22+, A2s+, K6s+, Q8s+, J8s+, T8s+, 97s+, 87s, 76s, 65s, A8o+, KTo+, QTo+, JTo", 1.0),
            ("Raise", "K5s-K4s, Q7s-Q6s, J7s, T7s, 96s, 86s, 75s, 54s, A7o-A5o, K9o, Q9o, J9o, T9o", 0.5),
        ],
    },
    "BTN open": {
        "group": "Open (folded to you)",
        "story": "Folded to you on the **button**. Open or fold?",
        "actions": ["Raise", "Fold"],
        "chart": [
            ("Raise", "22+, A2s+, K2s+, Q5s+, J7s+, T7s+, 96s+, 86s+, 75s+, 65s, 54s, "
                      "A2o+, K9o+, Q9o+, J9o+, T9o", 1.0),
            ("Raise", "Q4s-Q2s, J6s-J5s, T6s, 95s, 85s, 74s, 64s, 53s, 43s, K8o-K7o, Q8o, J8o, T8o, 98o", 0.5),
        ],
    },
    "SB open": {
        "group": "Open (folded to you)",
        "story": "Folded to you in the **small blind**, only the big blind left. Raise or fold? "
                 "(Raise-or-fold version; real solvers also limp some hands here.)",
        "actions": ["Raise", "Fold"],
        "chart": [
            ("Raise", "22+, A2s+, K4s+, Q7s+, J7s+, T7s+, 97s+, 86s+, 76s, 65s, A2o+, K9o+, QTo+, JTo", 1.0),
            ("Raise", "K3s-K2s, Q6s-Q4s, J6s, T6s, 96s, 85s, 75s, 64s, 54s, K8o-K6o, Q9o, J9o, T9o, 98o", 0.5),
        ],
    },

    # ---- Facing an open ----
    "BB vs BTN open": {
        "group": "Facing an open",
        "story": "The **button** opens to 2.5bb, the small blind folds. You're in the **big blind**.",
        "actions": ["3-bet", "Call", "Fold"],
        "chart": [
            ("3-bet", "TT+, AQs+, AKo, A5s-A4s", 1.0),
            ("3-bet", "99-88, AJs, KQs, K9s, Q9s, J9s, T8s, 97s, 86s, 75s, 65s, AQo, A3s-A2s", 0.5),
            ("Call",  "99-88, AJs, KQs, K9s, Q9s, J9s, T8s, 97s, 86s, 75s, 65s, AQo, A3s-A2s", 0.5),
            ("Call",  "77-22, ATs-A6s, KJs-KTs, K8s-K2s, QJs-QTs, Q8s-Q2s, JTs, J8s-J4s, T9s, T7s-T6s, "
                      "98s, 96s, 87s, 85s, 76s, 74s, 64s, 63s, 54s, 53s, 43s, "
                      "AJo-A2o, KQo-K7o, QJo-Q8o, JTo-J8o, T9o-T8o, 98o, 97o, 87o, 76o", 1.0),
        ],
    },
    "SB vs BTN open": {
        "group": "Facing an open",
        "story": "The **button** opens to 2.5bb. You're in the **small blind** (3-bet or fold: "
                 "calling out of position with the BB still to act is rarely good).",
        "actions": ["3-bet", "Fold"],
        "chart": [
            ("3-bet", "88+, A9s+, A5s-A4s, KTs+, QTs+, JTs, AJo+, KQo", 1.0),
            ("3-bet", "77-55, A8s-A6s, A3s, K9s, Q9s, J9s, T9s, 98s, 87s, 76s, ATo, KJo", 0.5),
        ],
    },
    "BB vs UTG open": {
        "group": "Facing an open",
        "story": "**Under the gun** opens to 2.5bb, everyone else folds. You're in the **big blind**.",
        "actions": ["3-bet", "Call", "Fold"],
        "chart": [
            ("3-bet", "QQ+, AKs, AKo, A5s", 1.0),
            ("3-bet", "JJ, AQs, A4s, KJs", 0.5),
            ("Call",  "JJ, AQs, A4s, KJs", 0.5),
            ("Call",  "TT-22, AJs-A6s, A3s-A2s, KQs, KTs-K6s, QJs-Q8s, JTs-J8s, T9s-T8s, 98s-97s, "
                      "87s-86s, 76s-75s, 65s, 54s, AQo-ATo, KQo-KJo, QJo", 1.0),
        ],
    },
    "BTN vs CO open": {
        "group": "Facing an open",
        "story": "The **cutoff** opens to 2.5bb. You're on the **button**.",
        "actions": ["3-bet", "Call", "Fold"],
        "chart": [
            ("3-bet", "JJ+, AQs+, AKo, A5s-A4s, KQs", 1.0),
            ("3-bet", "TT, AJs, ATs, KJs, AQo, K9s, Q9s, J9s, T8s, 76s", 0.5),
            ("Call",  "TT, AJs, ATs, KJs, AQo, K9s, Q9s, J9s, T8s, 76s", 0.5),
            ("Call",  "99-22, A9s-A6s, KTs, QJs-QTs, JTs, T9s, 98s, 87s, 65s, AJo, KQo", 1.0),
        ],
    },
}


def strategy(spot: str) -> dict[str, dict[str, float]]:
    """hand -> {action: frequency}, every action present, summing to 1."""
    sp = SPOTS[spot]
    out = {h: {a: 0.0 for a in sp["actions"]} for h in ALL_HANDS}
    for action, rng, freq in sp["chart"]:
        for h in expand(rng):
            out[h][action] += freq
    for h, s in out.items():
        played = sum(v for a, v in s.items() if a != "Fold")
        if played > 1 + 1e-9:
            raise ValueError(f"{spot}: {h} adds up to {played:.0%}")
        s["Fold"] = round(1 - played, 6) if "Fold" in s else 0.0
    return out


def range_pct(strat: dict[str, dict[str, float]]) -> float:
    """Share of all 1326 combos that don't fold."""
    played = sum(combos(h) * (1 - s.get("Fold", 0)) for h, s in strat.items())
    return played / 1326
