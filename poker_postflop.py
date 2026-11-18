"""Postflop drills, board texture quiz, flop explorer and equity trainer.

Postflop data comes from real solver runs (postflop-solver, an open-source
GTO solver), packed into data/poker_postflop.json.gz. Setting for every flop:
single-raised pot, opener (BTN or UTG) vs big blind caller, 100bb deep,
5.5bb pot. The opener's and BB's preflop ranges are the charts in
poker_ranges.py. Simplified bet sizes (as most trainers use):
  flop:  BB checks; opener checks, bets 33% or bets 75%; BB can check-raise 3x
  turn:  either player bets 66%      river: either player bets 75%
Solved to under ~1% of the pot in exploitability.

data/preflop_equity.json holds all-in preflop matchups (Monte Carlo, 60k boards).
"""

from __future__ import annotations

import gzip
import json
import os
import random
import time
from collections import defaultdict

import streamlit as st

from poker_ranges import RANKS, grid_hand

HERE = os.path.dirname(os.path.abspath(__file__))
XP_CORRECT = 10
MIX_OK = 0.2

ACTION_COLOURS = {
    "Check": "#4c9f70", "Call": "#4c9f70", "Fold": "#d9dde3",
    "Bet 33%": "#f2a541", "Bet 66%": "#e4572e", "Bet 75%": "#c0392b",
    "Raise": "#7b2cbf", "All-in": "#3c096c",
}
SUIT_SYM = {"s": ("♠", "#1f2933"), "h": ("♥", "#d64545"), "d": ("♦", "#2f6fdb"), "c": ("♣", "#2f9e44")}
WHO = {"BTN": "the button", "UTG": "under the gun"}


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

@st.cache_data
def load_postflop() -> list[dict]:
    path = os.path.join(HERE, "data", "poker_postflop.json.gz")
    if not os.path.exists(path):
        return []
    with gzip.open(path, "rt") as f:
        flops = json.load(f)["flops"]
    for fl in flops:
        fl["texture"] = texture(fl["flop"])
    return flops


@st.cache_data
def load_preflop_equity() -> list[dict]:
    path = os.path.join(HERE, "data", "preflop_equity.json")
    return json.load(open(path)) if os.path.exists(path) else []


def cards_of(board: str) -> list[str]:
    return [board[i:i + 2] for i in range(0, len(board), 2)]


def texture(flop: str) -> dict:
    cs = cards_of(flop)
    vals = sorted((14 - RANKS.index(c[0]) for c in cs), reverse=True)
    suits = {c[1] for c in cs}
    paired = len(set(vals)) < 3
    span = max(vals) - min(vals)
    if 14 in vals:   # the ace also plays low (A-4-3 is connected)
        low = [1 if v == 14 else v for v in vals]
        span = min(span, max(low) - min(low))
    connected = not paired and span <= 4
    suit_tag = {1: "monotone", 2: "two-tone", 3: "rainbow"}[len(suits)]
    high = {14: "ace-high", 13: "king-high", 12: "queen-high", 11: "jack-high", 10: "ten-high"}.get(vals[0], "low board")
    bits = [high, suit_tag]
    if paired:
        bits.append("paired")
    if connected:
        bits.append("connected")
    elif not paired and span <= 6 and vals[0] <= 11:
        bits.append("semi-connected")
    elif not paired:
        bits.append("disconnected")
    return {"high": vals[0], "suits": suit_tag, "paired": paired, "connected": connected, "label": ", ".join(bits)}


# --------------------------------------------------------------------------
# Display helpers
# --------------------------------------------------------------------------

def card_html(c: str, size: int = 28) -> str:
    sym, col = SUIT_SYM[c[1]]
    r = "10" if c[0] == "T" else c[0]
    return (f'<span style="display:inline-block;min-width:{size * 1.6:.0f}px;padding:{size // 4}px {size // 5}px;'
            f'margin-right:6px;border:2px solid {col};border-radius:7px;font-size:{size}px;font-weight:700;'
            f'color:{col};text-align:center;background:#fff">{r}{sym}</span>')


def board_html(cards: list[str], hole: list[str] | None = None) -> str:
    out = '<div style="margin:4px 0 8px 0">'
    out += "".join(card_html(c) for c in cards)
    if hole:
        out += '<span style="display:inline-block;width:18px"></span>'
        out += '<span style="font-size:13px;color:#777;margin-right:6px">You:</span>'
        out += "".join(card_html(c, 32) for c in hole)
    return out + "</div>"


def fmt_mix(actions: list[str], freqs: list[float]) -> str:
    return " · ".join(f"{a} {f:.0%}" for a, f in sorted(zip(actions, freqs), key=lambda x: -x[1]) if f > 0.004)


def mix_bar(actions: list[str], freqs: list[float], height: int = 18) -> str:
    segs = "".join(
        f'<div title="{a} {f:.0%}" style="width:{f * 100:.1f}%;background:{ACTION_COLOURS.get(a, "#999")};'
        f'height:{height}px;display:flex;align-items:center;justify-content:center;font-size:11px;color:#fff;'
        f'overflow:hidden;white-space:nowrap">{a if f > 0.12 else ""}</div>'
        for a, f in zip(actions, freqs) if f > 0.004)
    return f'<div style="display:flex;width:100%;max-width:520px;border-radius:4px;overflow:hidden;margin:4px 0">{segs}</div>'


def hand_class(combo: str) -> str:
    a, b = combo[0], combo[2]
    if a == b:
        return a + a
    if RANKS.index(a) > RANKS.index(b):
        a, b = b, a
    return a + b + ("s" if combo[1] == combo[3] else "o")


def class_grid_html(node: dict) -> str:
    """13x13 chart of a postflop node: each cell averages that hand's combos."""
    acts = node["actions"]
    sums: dict[str, list[float]] = defaultdict(lambda: [0.0] * len(acts))
    wts: dict[str, float] = defaultdict(float)
    for combo, v in node["hands"].items():
        h, w = hand_class(combo), v[0]
        wts[h] += w
        for i, f in enumerate(v[2:]):
            sums[h][i] += w * f
    rows = []
    for i in range(13):
        cells = []
        for j in range(13):
            h = grid_hand(i, j)
            if wts.get(h, 0) <= 0:
                cells.append(f'<td style="background:#fff;color:#ccc">{h}</td>')
                continue
            fr = [x / wts[h] for x in sums[h]]
            stops, pos = [], 0.0
            for a, f in zip(acts, fr):
                if f > 0.004:
                    stops.append(f"{ACTION_COLOURS.get(a, '#999')} {pos * 100:.0f}% {(pos + f) * 100:.0f}%")
                    pos += f
            bg = stops[0].split()[0] if len(stops) == 1 else f"linear-gradient(90deg,{','.join(stops)})"
            cells.append(f'<td title="{h}: {fmt_mix(acts, fr)}" style="background:{bg}">{h}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    legend = " ".join(
        f'<span style="display:inline-block;width:12px;height:12px;background:{ACTION_COLOURS.get(a, "#999")};'
        f'border-radius:2px;vertical-align:middle;margin:0 3px 0 10px"></span>{a}' for a in acts)
    return f"""
<style>.pfgrid{{border-collapse:collapse;width:100%;max-width:560px;table-layout:fixed;font-family:ui-monospace,monospace}}
.pfgrid td{{border:1px solid #fff;text-align:center;font-size:clamp(7px,2.1vw,12px);padding:4px 0;color:#111}}</style>
<table class="pfgrid">{''.join(rows)}</table><div style="font-size:12px;margin-top:6px">{legend}
<span style="margin-left:10px;color:#777">Blank cells aren't in this player's range here.</span></div>"""


def _log(name: str, ok: bool, elapsed: float) -> None:
    from storage import log_performance
    xp = XP_CORRECT if ok else 0
    log_performance(name, ok, elapsed, xp)
    st.session_state.poker_history.append({"name": name, "correct": ok})
    st.session_state.total_xp += xp
    st.session_state.streak = st.session_state.streak + 1 if ok else 0


# --------------------------------------------------------------------------
# Postflop drill
# --------------------------------------------------------------------------

# kind -> (where the node lives, who you are, how to describe it)
SPOT_KINDS = {
    "Flop: checked to you (c-bet?)": "flop_ip",
    "Flop: BB facing a ⅓-pot c-bet": "flop_vs33",
    "Flop: BB facing a ¾-pot c-bet": "flop_vs75",
    "Turn: BB acts first after calling": "turn_oop",
    "Turn: checked to you": "turn_ip",
    "Turn: BB facing a ⅔-pot bet": "turn_vs",
}


def _node_for(fl: dict, kind: str, rng: random.Random):
    """(node, board cards, story) for a spot kind on a flop, or None."""
    opener = WHO[fl["matchup"]]
    pos = fl["matchup"]
    flop = cards_of(fl["flop"])
    if kind == "flop_ip":
        return fl["nodes"]["ip_vs_check"], flop, (
            f"You opened from **{pos}**, the big blind called. Pot **5.5bb**. BB checks to you.")
    if kind in ("flop_vs33", "flop_vs75"):
        key = "oop_vs_bet33" if kind == "flop_vs33" else "oop_vs_bet75"
        node = fl["nodes"].get(key)
        size = "⅓ pot (1.8bb)" if kind == "flop_vs33" else "¾ pot (4.1bb)"
        return node, flop, (
            f"You're in the **big blind** and called a 2.5bb open from {opener}. Pot **5.5bb**. "
            f"You check, they bet **{size}**.")
    if not fl["turns"]:
        return None
    t = rng.choice(fl["turns"])
    board = flop + [t["card"]]
    pot = t["oop_first"]["pot_bb"] if t["oop_first"] else 9.1
    line = f"Flop went: BB checks, {pos} bets ⅓ pot, BB calls. Turn pot **{pot:g}bb**."
    if kind == "turn_oop":
        return t["oop_first"], board, f"You're the **big blind**. {line} You act first."
    if kind == "turn_ip":
        return t["ip_vs_check"], board, f"You opened from **{pos}**. {line} BB checks to you."
    return t["oop_vs_bet"], board, f"You're the **big blind**. {line} You check, {pos} bets **⅔ pot**."


def _pick_combo(node: dict, rng: random.Random, focus_mixed: bool) -> str:
    hands = node["hands"]
    names = list(hands)
    if focus_mixed and rng.random() < 0.65:
        tricky = [h for h in names if max(hands[h][2:]) < 0.85]
        if tricky:
            return rng.choices(tricky, weights=[hands[h][0] for h in tricky])[0]
    return rng.choices(names, weights=[hands[h][0] for h in names])[0]


def _new_postflop(flops: list[dict], kinds: list[str], matchups: list[str], focus: bool) -> None:
    rng = random.Random()
    pool = [f for f in flops if f["matchup"] in matchups]
    for _ in range(50):
        fl = rng.choice(pool)
        kind = SPOT_KINDS[rng.choice(kinds)]
        got = _node_for(fl, kind, rng)
        if got and got[0] and got[0]["hands"]:
            node, board, story = got
            combo = _pick_combo(node, rng, focus)
            st.session_state.pp_q = {"flop": fl["flop"], "matchup": fl["matchup"], "kind": kind, "board": board,
                                     "story": story, "node": node, "combo": combo, "start": time.time()}
            return
    st.session_state.pp_q = None


def postflop_drill() -> None:
    flops = load_postflop()
    if not flops:
        st.warning("Postflop solver data is missing (data/poker_postflop.json.gz).")
        return
    c1, c2 = st.columns([3, 1])
    kinds = c1.multiselect("Spots", list(SPOT_KINDS), default=list(SPOT_KINDS)[:3], key="pp_kinds")
    matchups = c2.multiselect("Opener", ["BTN", "UTG"], default=["BTN", "UTG"], key="pp_matchups")
    focus = st.toggle("Focus on mixed hands", value=True, key="pp_focus",
                      help="Mostly deal hands the solver plays more than one way. Those are where the learning is.")
    if not kinds or not matchups:
        st.info("Pick at least one spot and one opener.")
        return
    q = st.session_state.get("pp_q")
    if q is None or q["matchup"] not in matchups or q["kind"] not in [SPOT_KINDS[k] for k in kinds]:
        _new_postflop(flops, kinds, matchups, focus)
        q = st.session_state.pp_q

    last = st.session_state.get("pp_last")
    if last:
        n, acts = last["node"], last["node"]["actions"]
        fr = n["hands"][last["combo"]][2:]
        eq = n["hands"][last["combo"]][1]
        head = (f"**{last['combo']}** on **{' '.join(last['board'])}**: you chose **{last['choice']}**. "
                f"Solver: {fmt_mix(acts, fr)}.")
        if last["ok"]:
            st.success("✅ " + head + (" Mixed, so either is fine." if max(fr) < 0.8 else ""))
        else:
            st.error("❌ " + head)
        with st.expander("Why? Hand equity, and how the whole range plays it", expanded=not last["ok"]):
            st.markdown(f"Your equity against the range you're facing here: **{eq:.0%}**. "
                        f"Your whole range's equity: **{n['range_equity']:.0%}**.")
            st.markdown("**This hand:**" + mix_bar(acts, fr), unsafe_allow_html=True)
            st.markdown("**Whole range:**" + mix_bar(acts, n["agg"]), unsafe_allow_html=True)
            st.markdown(class_grid_html(n), unsafe_allow_html=True)
            st.caption(f"Board: {texture(last['flop'])['label']}.")

    if q is None:
        st.warning("Couldn't find a spot for that filter.")
        return
    hole = [q["combo"][:2], q["combo"][2:]]
    st.markdown(q["story"])
    st.markdown(board_html(q["board"], hole), unsafe_allow_html=True)
    acts = q["node"]["actions"]
    cols = st.columns(len(acts))
    for col, a in zip(cols, acts):
        if col.button(a, key=f"pp_act_{a}", use_container_width=True):
            fr = q["node"]["hands"][q["combo"]][2:]
            ok = fr[acts.index(a)] >= MIX_OK
            _log(f"Poker::Post::{q['matchup']} {q['kind']}", ok, time.time() - q["start"])
            st.session_state.pp_last = {**q, "choice": a, "ok": ok}
            _new_postflop(flops, kinds, matchups, focus)
            st.rerun()
    st.caption("Graded against solver frequencies: any action the solver takes at least 20% of the time counts.")


# --------------------------------------------------------------------------
# Board texture quiz + flop explorer
# --------------------------------------------------------------------------

def _bucket(x: float, edges: list[float], labels: list[str]) -> str:
    for e, l in zip(edges, labels):
        if x < e:
            return l
    return labels[-1]


CBET_EDGES, CBET_LABELS = [0.35, 0.55, 0.75], ["Under 35%", "35–55%", "55–75%", "Over 75%"]
FOLD_EDGES, FOLD_LABELS = [0.3, 0.45, 0.6], ["Under 30%", "30–45%", "45–60%", "Over 60%"]


def _tex_question(flops: list[dict], rng: random.Random) -> dict:
    kind = rng.choice(["cbet", "size", "compare", "fold", "equity"])
    fl = rng.choice(flops)
    n = fl["nodes"]["ip_vs_check"]
    acts, agg = n["actions"], n["agg"]
    pos = fl["matchup"]
    board = cards_of(fl["flop"])
    cbet = 1 - agg[acts.index("Check")]
    small, big = agg[acts.index("Bet 33%")], agg[acts.index("Bet 75%")]
    tex = fl["texture"]["label"]
    if kind == "cbet":
        ans = _bucket(cbet, CBET_EDGES, CBET_LABELS)
        return {"kind": "C-bet frequency", "board": board,
                "prompt": f"{pos} opened, BB called and checks. How often does **{pos}** c-bet this flop (any size)?",
                "options": CBET_LABELS, "answer": ans,
                "why": f"Solver c-bets **{cbet:.0%}** ({small:.0%} small, {big:.0%} big). {pos}'s range equity: "
                       f"**{n['range_equity']:.0%}**. Board: {tex}.", "node": n}
    if kind == "size":
        opts = ["Mostly small (⅓ pot)", "Mostly big (¾ pot)", "Mostly check"]
        top = max([("Mostly small (⅓ pot)", small), ("Mostly big (¾ pot)", big), ("Mostly check", 1 - cbet)], key=lambda x: x[1])[0]
        return {"kind": "Sizing", "board": board,
                "prompt": f"{pos} vs BB, checked to {pos}. What's {pos}'s most common action here?",
                "options": opts, "answer": top,
                "why": f"Check {1 - cbet:.0%} · small {small:.0%} · big {big:.0%}. Board: {tex}. Rule of thumb: "
                       "dry boards that favour the opener → small and often; wet, dynamic boards → bet big or check.",
                "node": n}
    if kind == "fold":
        node = fl["nodes"].get("oop_vs_bet33")
        fold = node["agg"][node["actions"].index("Fold")]
        ans = _bucket(fold, FOLD_EDGES, FOLD_LABELS)
        return {"kind": "BB defence", "board": board,
                "prompt": f"{pos} c-bets ⅓ pot into the big blind. How often does BB **fold**?",
                "options": FOLD_LABELS, "answer": ans,
                "why": f"BB folds **{fold:.0%}**, calls {node['agg'][node['actions'].index('Call')]:.0%}, "
                       f"raises {node['agg'][node['actions'].index('Raise')]:.0%}. MDF vs ⅓ pot is 75%, "
                       f"so BB folds about 25% or less on boards where it isn't crushed. Board: {tex}.", "node": node}
    if kind == "equity":
        opts = [f"{pos} has a big edge (58%+)", f"{pos} slightly ahead (52–58%)", "About even or BB ahead (under 52%)"]
        e = n["range_equity"]
        ans = opts[0] if e >= 0.58 else opts[1] if e >= 0.52 else opts[2]
        return {"kind": "Range advantage", "board": board,
                "prompt": f"{pos} opened, BB called. Whose range hits this flop better? ({pos}'s equity vs BB's range)",
                "options": opts, "answer": ans,
                "why": f"{pos} range equity: **{e:.0%}**. Board: {tex}. High cards favour the opener's range; "
                       "low connected boards favour the big blind's wide calling range.", "node": n}
    # compare two flops of the same matchup
    same = [f for f in flops if f["matchup"] == fl["matchup"] and f["flop"] != fl["flop"]]
    other = rng.choice(same)
    def cb(f):
        nn = f["nodes"]["ip_vs_check"]
        return 1 - nn["agg"][nn["actions"].index("Check")]
    a_, b_ = cb(fl), cb(other)
    if abs(a_ - b_) < 0.08:
        return _tex_question(flops, rng)
    lab_a = " ".join(cards_of(fl["flop"]))
    lab_b = " ".join(cards_of(other["flop"]))
    return {"kind": "Compare boards", "board": None, "boards": [cards_of(fl["flop"]), cards_of(other["flop"])],
            "prompt": f"{pos} vs BB, checked to {pos}. On which flop does {pos} c-bet **more often**?",
            "options": [lab_a, lab_b], "answer": lab_a if a_ > b_ else lab_b,
            "why": f"{lab_a}: c-bet {a_:.0%} ({fl['texture']['label']}). "
                   f"{lab_b}: c-bet {b_:.0%} ({other['texture']['label']}).", "node": None}


def texture_quiz() -> None:
    flops = load_postflop()
    if not flops:
        st.warning("Postflop solver data is missing.")
        return
    if st.session_state.get("tex_q") is None:
        st.session_state.tex_q = {**_tex_question(flops, random.Random()), "start": time.time()}
    q = st.session_state.tex_q

    last = st.session_state.get("tex_last")
    if last:
        (st.success if last["ok"] else st.error)(
            f"{'✅' if last['ok'] else '❌'} You said *{last['given']}*, answer: **{last['answer']}**. {last['why']}")
        if last.get("node"):
            with st.expander("See the full strategy"):
                st.markdown(mix_bar(last["node"]["actions"], last["node"]["agg"]), unsafe_allow_html=True)
                st.markdown(class_grid_html(last["node"]), unsafe_allow_html=True)

    st.markdown(f"##### {q['kind']}")
    if q.get("board"):
        st.markdown(board_html(q["board"]), unsafe_allow_html=True)
    st.markdown(q["prompt"])
    if q.get("boards"):
        cols = st.columns(2)
        for col, b in zip(cols, q["boards"]):
            col.markdown(board_html(b), unsafe_allow_html=True)
    cols = st.columns(len(q["options"]))
    for i, (col, opt) in enumerate(zip(cols, q["options"])):
        if col.button(opt, key=f"tex_opt_{i}", use_container_width=True):
            ok = opt == q["answer"]
            _log(f"Poker::Texture::{q['kind']}", ok, time.time() - q["start"])
            st.session_state.tex_last = {**q, "given": opt, "ok": ok}
            st.session_state.tex_q = None
            st.rerun()


def flop_explorer() -> None:
    flops = load_postflop()
    if not flops:
        return
    st.caption("Browse the solved flops. Pick a board and a decision point to see how the whole range plays it.")
    c1, c2 = st.columns(2)
    matchup = c1.radio("Opener", ["BTN", "UTG"], horizontal=True, key="fx_m")
    pool = [f for f in flops if f["matchup"] == matchup]
    labels = {f"{' '.join(cards_of(f['flop']))}  ·  {f['texture']['label']}": f for f in pool}
    fl = labels[c2.selectbox("Flop", list(labels), key="fx_f")]
    views = {"Opener, checked to": fl["nodes"]["ip_vs_check"],
             "BB vs ⅓-pot c-bet": fl["nodes"].get("oop_vs_bet33"),
             "BB vs ¾-pot c-bet": fl["nodes"].get("oop_vs_bet75")}
    view = st.radio("Decision", list(views), horizontal=True, key="fx_v")
    n = views[view]
    st.markdown(board_html(cards_of(fl["flop"])), unsafe_allow_html=True)
    st.markdown(f"Range equity: **{n['range_equity']:.0%}** · Overall: {fmt_mix(n['actions'], n['agg'])}")
    st.markdown(mix_bar(n["actions"], n["agg"]), unsafe_allow_html=True)
    st.markdown(class_grid_html(n), unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Equity trainer
# --------------------------------------------------------------------------

def _new_eq_q(mode: str) -> None:
    rng = random.Random()
    if mode == "Preflop all-in" or not load_postflop():
        m = rng.choice(load_preflop_equity())
        if rng.random() < 0.5:
            hero, vil, eq = m["a"], m["b"], m["eq_a"]
        else:
            hero, vil, eq = m["b"], m["a"], 1 - m["eq_a"]
        st.session_state.eq_q = {"mode": "pre", "hero": hero, "vil": vil, "answer": eq * 100, "tol": 4,
                                 "family": m["family"], "start": time.time()}
        return
    fl = rng.choice(load_postflop())
    key = rng.choice(["ip_vs_check", "oop_vs_bet33"])
    node = fl["nodes"][key]
    combo = rng.choices(list(node["hands"]), weights=[v[0] for v in node["hands"].values()])[0]
    eq = node["hands"][combo][1]
    who = (f"You opened {fl['matchup']}, BB called and checked. Your equity vs **BB's checking range**?"
           if key == "ip_vs_check" else
           f"You're BB vs a {fl['matchup']} open, facing a ⅓-pot c-bet. Your equity vs **their betting range**?")
    st.session_state.eq_q = {"mode": "flop", "hero": [combo[:2], combo[2:]], "board": cards_of(fl["flop"]),
                             "prompt": who, "answer": eq * 100, "tol": 8, "start": time.time(),
                             "range_eq": node["range_equity"]}


RULES = {
    "Pair vs two overcards": "a pair is a small favourite over two overcards, about 55/45 (the classic coinflip)",
    "Pair vs two undercards": "a pair dominates two undercards, about 80–85%",
    "Pair vs smaller pair": "a bigger pair is about 80/20",
    "Pair vs one overcard": "a pair vs one overcard is about 70/30",
    "Domination (shared card)": "sharing a card with a better kicker is about 70–75%",
    "Overcards vs undercards": "two overcards vs two unpaired undercards is about 60–65%",
    "Pair vs over and under": "a pair vs one over and one under is about 70/30",
    "Suited vs offsuit twin": "suitedness is worth only about 2–3%",
}


def equity_trainer() -> None:
    mode = st.radio("Mode", ["Preflop all-in", "Flop: hand vs range"], horizontal=True, key="eq_mode")
    q = st.session_state.get("eq_q")
    if q is None or (q["mode"] == "pre") != (mode == "Preflop all-in"):
        _new_eq_q(mode)
        q = st.session_state.eq_q

    last = st.session_state.get("eq_last")
    if last:
        msg = f"You said {last['given']}%, actual **{last['answer']:.1f}%**."
        if last["mode"] == "pre":
            msg += f" Rule of thumb: {RULES.get(last['family'], '')}."
        else:
            msg += f" Your whole range has {last['range_eq']:.0%} here."
        (st.success if last["ok"] else st.error)(("✅ " if last["ok"] else "❌ ") + msg)

    if q["mode"] == "pre":
        st.markdown("All-in preflop. What's **your** equity?")
        st.markdown(f'<div style="font-size:13px;color:#777">You</div>' + board_html(q["hero"])
                    + f'<div style="font-size:13px;color:#777">Villain</div>' + board_html(q["vil"]),
                    unsafe_allow_html=True)
        st.caption(f"Within ±{q['tol']} points counts.")
    else:
        st.markdown(q["prompt"])
        st.markdown(board_html(q["board"], q["hero"]), unsafe_allow_html=True)
        st.caption(f"Within ±{q['tol']} points counts.")
    with st.form("eq_form", clear_on_submit=True):
        raw = st.text_input("Your equity (%)", key="eq_ans")
        sub = st.form_submit_button("Submit")
    if sub:
        try:
            val = float(raw.strip().rstrip("%"))
            val = val * 100 if 0 < val < 1 else val
        except ValueError:
            st.warning("Type a number like 55.")
            return
        ok = abs(val - q["answer"]) <= q["tol"]
        _log(f"Poker::Equity::{'Preflop' if q['mode'] == 'pre' else 'Flop'}", ok, time.time() - q["start"])
        st.session_state.eq_last = {**q, "given": raw, "ok": ok}
        _new_eq_q(mode)
        st.rerun()
