"""Poker section: preflop chart drills, chart study view, and poker math.

Answers go into the app's existing log, so nothing new needs setting up:
  * preflop:  tab_name "Poker::PF::<spot>::<hand>"  e.g. "Poker::PF::BTN open::K9o"
  * math:     tab_name "Poker::Math::<question type>"
Keeping the hand in the name lets the Leaks view find the hands you keep
getting wrong, and lets missed hands come back in later sessions.
"""

from __future__ import annotations

import math
import random
import time
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st

from poker_ranges import ALL_HANDS, GRID_POS, RANKS, SPOTS, combos, grid_hand, range_pct, strategy
from storage import log_performance, read_logs

PF_PREFIX = "Poker::PF::"
MATH_PREFIX = "Poker::Math::"
XP_CORRECT = 10
MIX_OK = 0.2          # an action the chart takes at least this often counts as correct
RETEST_SHARE = 0.3    # chance the next preflop hand is one you got wrong before
BORDER_SHARE = 0.75   # with "focus on borderline hands" on, share of hands drawn from the range edges

ACTION_COLOURS = {"Raise": "#e4572e", "3-bet": "#e4572e", "Call": "#4c9f70", "Fold": "#d9dde3"}
SUITS = [("♠", "#1f2933"), ("♥", "#d64545"), ("♦", "#2f6fdb"), ("♣", "#2f9e44")]   # four-colour deck


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

@st.cache_data
def _strategies() -> dict[str, dict]:
    return {name: strategy(name) for name in SPOTS}


def _load_history() -> list[dict]:
    try:
        df = read_logs()
    except Exception as e:
        st.warning(f"Couldn't load past poker answers ({e}); tracking this session only.")
        return []
    df = df[df["tab_name"].astype(str).str.startswith("Poker::")]
    out = []
    for name, ok in zip(df["tab_name"].astype(str), df["is_correct"]):
        out.append({"name": name, "correct": bool(ok)})
    return out


def _log(name: str, ok: bool, elapsed: float) -> None:
    xp = XP_CORRECT if ok else 0
    log_performance(name, ok, elapsed, xp)
    st.session_state.poker_history.append({"name": name, "correct": ok})
    st.session_state.total_xp += xp
    st.session_state.streak = st.session_state.streak + 1 if ok else 0


def _fmt_mix(mix: dict[str, float]) -> str:
    parts = [f"{a} {f:.0%}" for a, f in sorted(mix.items(), key=lambda kv: -kv[1]) if f > 0.001]
    return " · ".join(parts)


def _main_action(mix: dict[str, float]) -> str:
    return max(mix, key=mix.get)


# --------------------------------------------------------------------------
# Range grid (HTML)
# --------------------------------------------------------------------------

def _cell_bg(mix: dict[str, float], actions: list[str]) -> str:
    """Solid colour for a pure hand, a split bar for a mixed one."""
    stops, pos = [], 0.0
    for a in actions:
        f = mix.get(a, 0)
        if f <= 0.001:
            continue
        c = ACTION_COLOURS[a]
        stops.append(f"{c} {pos * 100:.0f}% {(pos + f) * 100:.0f}%")
        pos += f
    if len(stops) == 1:
        return stops[0].split()[0]
    return f"linear-gradient(90deg, {', '.join(stops)})"


def range_grid_html(spot: str, highlight: str | None = None) -> str:
    strat = _strategies()[spot]
    actions = SPOTS[spot]["actions"]
    rows = []
    for i in range(13):
        cells = []
        for j in range(13):
            h = grid_hand(i, j)
            border = "outline:3px solid #111;outline-offset:-3px;font-weight:700;" if h == highlight else ""
            cells.append(f'<td title="{h}: {_fmt_mix(strat[h])}" style="background:{_cell_bg(strat[h], actions)};{border}">{h}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    legend = " ".join(
        f'<span style="display:inline-block;width:12px;height:12px;background:{ACTION_COLOURS[a]};'
        f'border-radius:2px;vertical-align:middle;margin:0 3px 0 10px"></span>{a}' for a in actions
    )
    return f"""
<style>
.pkgrid {{border-collapse:collapse;width:100%;max-width:560px;table-layout:fixed;font-family:ui-monospace,monospace}}
.pkgrid td {{border:1px solid #fff;text-align:center;font-size:clamp(7px,2.1vw,12px);padding:4px 0;color:#111}}
</style>
<table class="pkgrid">{''.join(rows)}</table>
<div style="font-size:12px;margin-top:6px">{legend}
<span style="margin-left:10px;color:#777">Split cells are mixed hands. Plays {range_pct(strat):.1%} of hands.</span></div>
"""


# --------------------------------------------------------------------------
# Preflop drill
# --------------------------------------------------------------------------

def _borderline(spot: str) -> list[str]:
    """Hands on the edge of the chart: mixed hands, plus pure hands next to a
    hand (one step across or down the grid) that is played differently."""
    strat = _strategies()[spot]
    out = []
    for h in ALL_HANDS:
        mix = strat[h]
        if max(mix.values()) < 0.999:
            out.append(h)
            continue
        i, j = GRID_POS[h]
        main = _main_action(mix)
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < 13 and 0 <= nj < 13 and _main_action(strat[grid_hand(ni, nj)]) != main:
                out.append(h)
                break
    return out


def _deal_cards(hand: str, rng: random.Random) -> list[tuple[str, int]]:
    if len(hand) == 2:
        s1, s2 = rng.sample(range(4), 2)
    elif hand[2] == "s":
        s1 = s2 = rng.randrange(4)
    else:
        s1, s2 = rng.sample(range(4), 2)
    return [(hand[0], s1), (hand[1], s2)]


def _cards_html(cards: list[tuple[str, int]]) -> str:
    out = []
    for r, s in cards:
        sym, col = SUITS[s]
        out.append(
            f'<span style="display:inline-block;min-width:58px;padding:10px 8px;margin-right:8px;'
            f'border:2px solid {col};border-radius:8px;font-size:34px;font-weight:700;color:{col};'
            f'text-align:center;background:#fff">{"10" if r == "T" else r}{sym}</span>'
        )
    return "".join(out)


def _pf_missed(spots: list[str]) -> list[tuple[str, str]]:
    """(spot, hand) pairs whose most recent attempt was wrong."""
    last: dict[tuple[str, str], bool] = {}
    for r in st.session_state.poker_history:
        if r["name"].startswith(PF_PREFIX):
            try:
                spot, hand = r["name"][len(PF_PREFIX):].rsplit("::", 1)
            except ValueError:
                continue
            last[(spot, hand)] = r["correct"]
    return [k for k, ok in last.items() if not ok and k[0] in spots and k[0] in SPOTS]


def _new_pf_hand(spots: list[str], focus_border: bool) -> None:
    rng = random.Random()
    missed = _pf_missed(spots)
    prev = st.session_state.get("poker_pf_q") or {}
    missed = [m for m in missed if (m[0], m[1]) != (prev.get("spot"), prev.get("hand"))]
    if missed and rng.random() < RETEST_SHARE:
        spot, hand = rng.choice(missed)
        why = "🔁 You missed this one before"
    else:
        spot = rng.choice(spots)
        if focus_border and rng.random() < BORDER_SHARE:
            hand = rng.choice(_borderline(spot))
        else:
            # Weighted by combos, so offsuit hands come up 3x as often as suited, like at the table.
            hand = rng.choices(ALL_HANDS, weights=[combos(h) for h in ALL_HANDS])[0]
        why = ""
    st.session_state.poker_pf_q = {
        "spot": spot, "hand": hand, "cards": _deal_cards(hand, rng), "why": why, "start": time.time(),
    }


def _preflop_drill() -> None:
    groups: dict[str, list[str]] = defaultdict(list)
    for name, sp in SPOTS.items():
        groups[sp["group"]].append(name)

    c1, c2 = st.columns([3, 1])
    spots = c1.multiselect("Spots to drill", list(SPOTS), default=groups["Open (folded to you)"], key="poker_spots")
    focus = c2.toggle("Borderline hands", value=True, key="poker_focus",
                      help="Mostly deal hands near the edge of each chart. AA and 72o teach you nothing.")
    if not spots:
        st.info("Pick at least one spot.")
        return

    q = st.session_state.get("poker_pf_q")
    if q is None or q["spot"] not in spots:
        _new_pf_hand(spots, focus)
        q = st.session_state.poker_pf_q

    last = st.session_state.get("poker_pf_last")
    if last:
        msg = f"**{last['hand']}** in *{last['spot']}*: you chose **{last['choice']}**. Chart: {_fmt_mix(last['mix'])}."
        if last["ok"] and last["mix"][last["choice"]] < 0.999:
            st.success("✅ " + msg + " Mixed hand, either works.")
        elif last["ok"]:
            st.success("✅ " + msg)
        else:
            st.error("❌ " + msg + " It'll come back.")
        with st.expander(f"Chart for {last['spot']}", expanded=not last["ok"]):
            st.markdown(range_grid_html(last["spot"], highlight=last["hand"]), unsafe_allow_html=True)

    st.markdown(f"##### {q['spot']} {q['why']}")
    st.markdown(SPOTS[q["spot"]]["story"])
    st.markdown(_cards_html(q["cards"]) + f'<span style="color:#888;font-size:14px">{q["hand"]}</span>',
                unsafe_allow_html=True)
    st.write("")

    actions = SPOTS[q["spot"]]["actions"]
    cols = st.columns(len(actions))
    for col, action in zip(cols, actions):
        if col.button(action, key=f"poker_act_{action}", use_container_width=True,
                      type="primary" if action != "Fold" else "secondary"):
            mix = _strategies()[q["spot"]][q["hand"]]
            ok = mix[action] >= MIX_OK
            _log(f"{PF_PREFIX}{q['spot']}::{q['hand']}", ok, time.time() - q["start"])
            st.session_state.poker_pf_last = {"spot": q["spot"], "hand": q["hand"], "choice": action, "mix": mix, "ok": ok}
            _new_pf_hand(spots, focus)
            st.rerun()

    pf = [r for r in st.session_state.poker_history if r["name"].startswith(PF_PREFIX)]
    if pf:
        recent = pf[-50:]
        st.caption(f"Last {len(recent)} preflop answers: {sum(r['correct'] for r in recent) / len(recent):.0%} correct · "
                   f"{len(_pf_missed(list(SPOTS)))} hands waiting for a retest")


# --------------------------------------------------------------------------
# Chart study view
# --------------------------------------------------------------------------

def _charts() -> None:
    st.caption("Study a chart, then drill it. Pairs run down the diagonal, suited hands sit above it, offsuit below.")
    spot = st.selectbox("Spot", list(SPOTS), key="poker_chart_spot")
    st.markdown(SPOTS[spot]["story"])
    st.markdown(range_grid_html(spot), unsafe_allow_html=True)
    st.info("These charts are approximations of typical solver strategy for 6-max cash, 100bb deep, 2.5bb opens. "
            "They're a solid baseline, not exact solver output. To use charts you trust more, edit `SPOTS` in "
            "`poker_ranges.py`.")


# --------------------------------------------------------------------------
# Poker math
# --------------------------------------------------------------------------

BET_FRACTIONS = [(0.25, "¼ pot"), (1 / 3, "⅓ pot"), (0.5, "½ pot"), (2 / 3, "⅔ pot"),
                 (0.75, "¾ pot"), (1.0, "pot"), (1.5, "1.5x pot"), (2.0, "2x pot")]


def _pot_and_bet(rng: random.Random) -> tuple[float, float, str]:
    pot = rng.choice([6, 8, 10, 12, 15, 20, 24, 30, 40, 60, 90, 120])
    frac, label = rng.choice(BET_FRACTIONS)
    bet = round(pot * frac, 1)
    return pot, bet, label


def _q_pot_odds(rng):
    p, b, lab = _pot_and_bet(rng)
    ans = b / (p + 2 * b) * 100
    return {
        "prompt": f"The pot is **{p:g}bb**. Villain bets **{b:g}bb** ({lab}). What equity do you need to call? (%)",
        "answer": ans, "unit": "%", "tol": 1.5,
        "solution": f"You call {b:g} to win the {p:g} pot plus their {b:g} bet plus your call: "
                    f"{b:g} / ({p:g} + {b:g} + {b:g}) = **{ans:.1f}%**.\n\n"
                    "Shortcut: half pot → 25%, ⅔ pot → 28.6%, pot → 33.3%, 2x pot → 40%.",
    }


def _q_mdf(rng):
    p, b, lab = _pot_and_bet(rng)
    ans = p / (p + b) * 100
    return {
        "prompt": f"The pot is **{p:g}bb** and villain bets **{b:g}bb** ({lab}). What is your **minimum defence "
                  f"frequency** (how often you must continue so their bluffs with any two cards don't auto-profit)? (%)",
        "answer": ans, "unit": "%", "tol": 1.5,
        "solution": f"MDF = pot / (pot + bet) = {p:g} / ({p:g} + {b:g}) = **{ans:.1f}%**.\n\n"
                    "Think of it as the bluffer's price: they risk the bet to win the pot, so you have to keep them "
                    "from winning more than bet / (pot + bet) of the time.",
    }


def _q_bluff_ratio(rng):
    p, b, lab = _pot_and_bet(rng)
    ans = b / (p + 2 * b) * 100
    return {
        "prompt": f"River. You bet **{b:g}bb** into **{p:g}bb** ({lab}) with a polarised range (nuts or air). "
                  f"What share of your betting range should be **bluffs** so villain is indifferent to calling? (%)",
        "answer": ans, "unit": "%", "tol": 1.5,
        "solution": f"Bluffs should equal the pot odds you're laying villain: {b:g} / ({p:g} + 2×{b:g}) = **{ans:.1f}%**. "
                    f"That's about {ans / (100 - ans):.2f} bluffs per value bet.\n\n"
                    "Same number as the pot-odds question from the other seat. Bigger bets allow more bluffs.",
    }


def _q_bluff_breakeven(rng):
    p, b, lab = _pot_and_bet(rng)
    ans = b / (p + b) * 100
    return {
        "prompt": f"You have pure air and bet **{b:g}bb** into **{p:g}bb** ({lab}). How often must villain fold "
                  f"for the bluff to break even? (%)",
        "answer": ans, "unit": "%", "tol": 1.5,
        "solution": f"Risk / (risk + reward) = {b:g} / ({b:g} + {p:g}) = **{ans:.1f}%**. "
                    "It's 100% minus the MDF: what the bluffer needs and what the defender must prevent.",
    }


def _q_call_ev(rng):
    p, b, lab = _pot_and_bet(rng)
    eq = rng.choice([20, 25, 30, 35, 40, 45, 55])
    ans = eq / 100 * (p + 2 * b) - b
    return {
        "prompt": f"Pot **{p:g}bb**, villain bets **{b:g}bb**, you have **{eq}%** equity and nobody bets after this. "
                  f"What's the EV of calling, in bb?",
        "answer": ans, "unit": "bb", "tol": max(0.3, abs(ans) * 0.03),
        "solution": f"EV = equity × final pot − cost to call = {eq / 100:.2f} × ({p:g} + 2×{b:g}) − {b:g} "
                    f"= **{ans:+.2f}bb**. You need {b / (p + 2 * b):.1%} to break even.",
    }


DRAWS = [
    ("J♥T♥", "9♥ 8♣ 2♥", 15, "flush draw (9) + open-ended straight draw (8 − 2 hearts already counted = 6)"),
    ("A♠5♠", "K♠ 9♠ 3♦", 9, "nut flush draw: 13 spades − 4 seen = 9"),
    ("9♦8♣", "7♠ 6♥ K♦", 8, "open-ender: four 10s and four 5s"),
    ("9♦8♣", "J♠ 7♥ 2♦", 4, "gutshot: only the four 10s"),
    ("A♣K♦", "8♠ 6♥ 2♣", 6, "two overcards: three aces + three kings (and they might not be good)"),
    ("Q♥J♥", "K♥ 9♣ 4♥", 12, "flush draw (9) + gutshot to the 10 (4 − the 10♥ already counted = 3)"),
    ("7♣7♦", "K♠ 9♥ 4♣", 2, "set draw: the two remaining sevens"),
    ("A♥Q♣", "J♦ T♠ 3♥", 7, "gutshot (four kings) + ace overcard (three aces)"),
    ("8♠7♠", "6♠ 5♦ 2♠", 15, "flush draw (9) + open-ender (8 − 2 spades counted = 6)"),
    ("K♣Q♣", "A♦ J♥ 5♠", 4, "gutshot: four tens make Broadway"),
]


def _q_outs(rng):
    hole, board, outs, why = rng.choice(DRAWS)
    return {
        "prompt": f"You hold **{hole}** on a flop of **{board}**. How many clean outs to improve to a likely best hand?",
        "answer": outs, "unit": "outs", "tol": 0,
        "solution": f"**{outs}** outs: {why}.",
    }


def _q_equity(rng):
    outs = rng.choice([4, 6, 8, 9, 12, 15])
    street = rng.choice(["flop", "turn"])
    if street == "flop":
        exact = (1 - math.comb(47 - outs, 2) / math.comb(47, 2)) * 100
        rule, how = outs * 4, f"rule of 4: {outs} × 4 = {outs * 4}%"
        prompt = f"On the **flop** with **{outs} outs**, all-in so you see the turn **and** river. Roughly what's your equity? (%)"
    else:
        exact = outs / 46 * 100
        rule, how = outs * 2, f"rule of 2: {outs} × 2 = {outs * 2}%"
        prompt = f"On the **turn** with **{outs} outs**, one card to come. Roughly what's your equity? (%)"
    note = " With lots of outs the rule of 4 overshoots, so shade it down." if street == "flop" and outs >= 12 else ""
    return {
        "prompt": prompt, "answer": exact, "unit": "%", "tol": 2.5, "alt": rule,
        "solution": f"Exact: **{exact:.1f}%**. Quick estimate, {how}.{note}",
    }


def _q_combos(rng):
    kind = rng.choice(["pair", "pair_block", "unpaired", "unpaired_block"])
    r1, r2 = sorted(rng.sample(range(13), 2))
    a, b = RANKS[r1], RANKS[r2]
    if kind == "pair":
        return {"prompt": f"How many combos of **{a}{a}** are there?", "answer": 6, "unit": "combos", "tol": 0,
                "solution": "4 cards choose 2 = **6**. Every pocket pair has 6 combos."}
    if kind == "pair_block":
        seen = rng.choice([1, 2])
        left = 4 - seen
        ans = left * (left - 1) // 2
        where = "one is on the board" if seen == 1 else "one is on the board and one is in your hand"
        return {"prompt": f"How many combos of **{a}{a}** can villain have if {where}?",
                "answer": ans, "unit": "combos", "tol": 0,
                "solution": f"{left} {a}s left, choose 2 = **{ans}**. One blocker cuts a set from 6 combos to 3."}
    if kind == "unpaired":
        sub = rng.choice(["total", "suited", "offsuit"])
        ans = {"total": 16, "suited": 4, "offsuit": 12}[sub]
        label = {"total": f"{a}{b} (suited and offsuit together)", "suited": f"{a}{b}s", "offsuit": f"{a}{b}o"}[sub]
        return {"prompt": f"How many combos of **{label}**?", "answer": ans, "unit": "combos", "tol": 0,
                "solution": f"4 × 4 = 16 in total: 4 suited (one per suit) and 12 offsuit. **{ans}**."}
    seen = rng.choice([1, 2])
    ans = (4 - seen) * 4
    return {"prompt": f"The board has {'one' if seen == 1 else 'two'} **{a}**. How many combos of **{a}{b}** "
                      f"(suited + offsuit) can villain have?",
            "answer": ans, "unit": "combos", "tol": 0,
            "solution": f"{4 - seen} {a}s left × 4 {b}s = **{ans}**. Blockers are why holding an ace makes "
                        "villain's AK less likely."}


MATH_TYPES = {
    "Pot odds": _q_pot_odds,
    "MDF": _q_mdf,
    "Bluff share": _q_bluff_ratio,
    "Bluff break-even": _q_bluff_breakeven,
    "Call EV": _q_call_ev,
    "Counting outs": _q_outs,
    "Outs → equity": _q_equity,
    "Combos": _q_combos,
}


def parse_num(text: str, unit: str) -> float | None:
    """'25', '25%', '0.25' and '1/4' all read as 25 for a percentage question."""
    t = text.strip().replace(",", "").replace(" ", "").replace("bb", "")
    if not t:
        return None
    try:
        if t.endswith("%"):
            return float(t[:-1])
        if "/" in t:
            n, d = t.split("/", 1)
            v = float(n) / float(d)
            return v * 100 if unit == "%" else v
        v = float(t)
        return v * 100 if unit == "%" and 0 < abs(v) < 1 else v
    except (ValueError, ZeroDivisionError):
        return None


def math_correct(val: float, q: dict) -> bool:
    if abs(val - q["answer"]) <= q["tol"] + 1e-9:
        return True
    return "alt" in q and abs(val - q["alt"]) <= 1.0


def _new_math_q(kinds: list[str]) -> None:
    kind = random.choice(kinds)
    st.session_state.poker_math_q = {"kind": kind, **MATH_TYPES[kind](random.Random()), "start": time.time()}


def _poker_math() -> None:
    kinds = st.multiselect("Question types", list(MATH_TYPES), default=list(MATH_TYPES), key="poker_math_kinds")
    if not kinds:
        st.info("Pick at least one question type.")
        return
    q = st.session_state.get("poker_math_q")
    if q is None or q["kind"] not in kinds:
        _new_math_q(kinds)
        q = st.session_state.poker_math_q

    last = st.session_state.get("poker_math_last")
    if last:
        (st.success if last["ok"] else st.error)(
            f"{'✅ Correct' if last['ok'] else '❌ Not quite'}: you said {last['given']}. {last['q']['solution']}")

    st.markdown(f"##### {q['kind']}")
    st.markdown(q["prompt"])
    with st.form("poker_math_form", clear_on_submit=True):
        raw = st.text_input("Answer", key="poker_math_ans", placeholder="e.g. 28.6, 2/7 or 15")
        sub = st.form_submit_button("Submit")
    if sub:
        val = parse_num(raw, q["unit"])
        if val is None:
            st.warning("Couldn't read that as a number.")
            return
        ok = math_correct(val, q)
        _log(MATH_PREFIX + q["kind"], ok, time.time() - q["start"])
        st.session_state.poker_math_last = {"ok": ok, "given": raw, "q": q}
        _new_math_q(kinds)
        st.rerun()
    if st.button("Skip (counts as a miss)", key="poker_math_skip"):
        _log(MATH_PREFIX + q["kind"], False, time.time() - q["start"])
        st.session_state.poker_math_last = {"ok": False, "given": "(skipped)", "q": q}
        _new_math_q(kinds)
        st.rerun()


# --------------------------------------------------------------------------
# Leaks
# --------------------------------------------------------------------------

def _leaks() -> None:
    hist = st.session_state.poker_history
    if not hist:
        st.info("No poker answers yet. Your weak spots show up here once you've drilled a bit.")
        return

    by_spot: dict[str, list[bool]] = defaultdict(list)
    by_hand: dict[tuple[str, str], list[bool]] = defaultdict(list)
    by_math: dict[str, list[bool]] = defaultdict(list)
    by_other: dict[str, list[bool]] = defaultdict(list)
    for r in hist:
        n = r["name"]
        if n.startswith(PF_PREFIX):
            try:
                spot, hand = n[len(PF_PREFIX):].rsplit("::", 1)
            except ValueError:
                continue
            by_spot[spot].append(r["correct"])
            by_hand[(spot, hand)].append(r["correct"])
        elif n.startswith(MATH_PREFIX):
            by_math[n[len(MATH_PREFIX):]].append(r["correct"])
        else:   # Poker::Post::..., Poker::Texture::..., Poker::Equity::...
            parts = n.split("::")
            if len(parts) >= 3:
                by_other[f"{parts[1]}: {parts[2]}"].append(r["correct"])

    if by_spot:
        st.subheader("Preflop accuracy by spot")
        st.dataframe(pd.DataFrame([
            {"Spot": s, "Answers": len(v), "Correct": f"{sum(v) / len(v):.0%}"}
            for s, v in sorted(by_spot.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        ]), hide_index=True, width="stretch")

        misses = Counter({k: v.count(False) for k, v in by_hand.items() if False in v})
        if misses:
            st.subheader("Hands you miss most")
            strat = _strategies()
            st.dataframe(pd.DataFrame([
                {"Spot": s, "Hand": h, "Missed": n, "Seen": len(by_hand[(s, h)]),
                 "Chart says": _fmt_mix(strat[s][h]) if s in strat else "?",
                 "Last try": "✅" if by_hand[(s, h)][-1] else "❌"}
                for (s, h), n in misses.most_common(20)
            ]), hide_index=True, width="stretch")

    if by_other:
        st.subheader("Postflop, board texture and equity accuracy")
        st.dataframe(pd.DataFrame([
            {"Drill": k, "Answers": len(v), "Correct": f"{sum(v) / len(v):.0%}"}
            for k, v in sorted(by_other.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        ]), hide_index=True, width="stretch")

    if by_math:
        st.subheader("Poker math accuracy")
        st.dataframe(pd.DataFrame([
            {"Type": k, "Answers": len(v), "Correct": f"{sum(v) / len(v):.0%}"}
            for k, v in sorted(by_math.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        ]), hide_index=True, width="stretch")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def render() -> None:
    st.title("Poker Trainer")
    if "poker_history" not in st.session_state:
        st.session_state.poker_history = _load_history()

    import poker_postflop as pp
    import poker_review

    tabs = st.tabs(["Preflop Drill", "Postflop Drill", "Board Textures", "Equity", "Poker Math",
                    "Range Charts", "Flop Explorer", "Hand Review", "Leaks"])
    with tabs[0]:
        _preflop_drill()
    with tabs[1]:
        pp.postflop_drill()
    with tabs[2]:
        pp.texture_quiz()
    with tabs[3]:
        pp.equity_trainer()
    with tabs[4]:
        _poker_math()
    with tabs[5]:
        _charts()
    with tabs[6]:
        pp.flop_explorer()
    with tabs[7]:
        poker_review.hand_review()
    with tabs[8]:
        _leaks()
