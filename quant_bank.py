"""Question bank for the Quant Practice tab.

Two kinds of item:

* "numeric" -- an original question written in the style of a Green Book
  topic. `gen(rng)` draws fresh numbers every time it's served, so a retest
  is the same idea with different inputs (no memorising the answer).
* "review" -- a pointer to a specific Green Book problem that doesn't
  survive a number swap (logic puzzles, proofs). You solve it on paper from
  your own copy of the book and mark yourself.

Book text is deliberately NOT reproduced here (this repo is public); the
`gb` field just names the section and problem so you can find it.

The bank is served in list order (easy first), so add new items roughly
where their difficulty belongs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable


@dataclass
class Item:
    id: str
    title: str
    gb: str                    # Green Book section / problem pointer
    level: int                 # 1 = warm-up ... 3 = harder
    kind: str = "numeric"      # "numeric" or "review"
    gen: Callable | None = None
    prompt: str = ""           # review items only
    abs_tol: float = 1e-9      # numeric answers within this are correct...
    rel_tol: float = 0.0       # ...or within this fraction of the answer
    tags: list[str] = field(default_factory=list)


def _frac(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator} ≈ {float(f):.4f}" if f.denominator != 1 else str(f.numerator)


# --------------------------------------------------------------------------
# Level 1 -- warm-ups
# --------------------------------------------------------------------------

def g_trailing_zeros(rng):
    n = rng.randint(30, 600)
    terms, k, total = [], 5, 0
    while k <= n:
        terms.append(f"⌊{n}/{k}⌋ = {n // k}")
        total += n // k
        k *= 5
    return dict(
        prompt=f"How many trailing zeros does **{n}!** have?",
        answer=total,
        solution=("Each trailing zero needs a factor 10 = 2×5, and 2s are plentiful, so count the 5s. "
                  "Multiples of 25 give an extra 5, multiples of 125 another, and so on:\n\n"
                  + "  \n".join(terms) + f"\n\nTotal = **{total}**."),
    )


def g_missing_number(rng):
    n = rng.randint(20, 120)
    m = rng.randint(1, n)
    s = n * (n + 1) // 2 - m
    return dict(
        prompt=(f"The integers 1 to {n} are written down, but one of them is missing. "
                f"The ones that remain add up to **{s:,}**. Which number is missing?"),
        answer=m,
        solution=f"Full sum = n(n+1)/2 = {n}×{n + 1}/2 = {n * (n + 1) // 2:,}. Missing = {n * (n + 1) // 2:,} − {s:,} = **{m}**.",
    )


def g_pigeonhole(rng):
    c = rng.randint(3, 8)
    k = rng.randint(2, 5)
    ans = c * (k - 1) + 1
    return dict(
        prompt=(f"A dark drawer has plenty of socks in **{c} colours**. What is the minimum number you must "
                f"pull out to be **certain** of having **{k} socks of the same colour**?"),
        answer=ans,
        solution=(f"Worst case: you draw {k - 1} of every colour without hitting {k} of any, which is "
                  f"{c}×{k - 1} = {c * (k - 1)} socks. One more forces a colour up to {k}: **{ans}**."),
    )


def g_dice_sum(rng):
    s = rng.choice([3, 4, 5, 6, 7, 8, 9, 10, 11])
    ways = 6 - abs(7 - s)
    f = Fraction(ways, 36)
    return dict(
        prompt=f"Roll two fair six-sided dice. What is the probability their sum is **{s}**?",
        answer=float(f),
        solution=(f"Count the ordered pairs: the number of ways to make s is 6 − |7 − s| = {ways}, "
                  f"out of 36 equally likely pairs. P = {ways}/36 = **{_frac(f)}**."),
    )


def g_at_least_one(rng):
    k = rng.randint(2, 8)
    sides = rng.choice([6, 6, 8, 10])
    p = 1 - ((sides - 1) / sides) ** k
    return dict(
        prompt=(f"You roll a fair **{sides}-sided** die **{k} times**. What is the probability that at least one "
                f"roll shows a {sides}? (3 decimal places is fine.)"),
        answer=p,
        solution=(f"Use the complement. P(no {sides} in one roll) = {sides - 1}/{sides}, so "
                  f"P(none in {k}) = ({sides - 1}/{sides})^{k} = {((sides - 1) / sides) ** k:.4f}. "
                  f"P(at least one) = 1 − that = **{p:.4f}**."),
    )


def g_committee(rng):
    n = rng.randint(6, 14)
    k = rng.randint(3, min(6, n - 1))
    ans = math.comb(n, k) * k
    return dict(
        prompt=(f"From a team of **{n}** people you form a committee of **{k}**, and one committee member "
                f"is named chair. How many different (committee, chair) setups are there?"),
        answer=ans,
        solution=(f"Choose the members, then the chair: C({n},{k}) × {k} = {math.comb(n, k)} × {k} = **{ans:,}**. "
                  f"(Or choose the chair first: {n} × C({n - 1},{k - 1}) = {n * math.comb(n - 1, k - 1):,}, which gives the same count.)"),
    )


# --------------------------------------------------------------------------
# Level 2
# --------------------------------------------------------------------------

def g_birthday(rng):
    m = rng.randint(10, 45)
    p_distinct = 1.0
    for i in range(m):
        p_distinct *= (365 - i) / 365
    p = 1 - p_distinct
    return dict(
        prompt=(f"There are **{m}** people in a room (365-day year, all birthdays equally likely). "
                f"What is the probability that at least two of them share a birthday? (Within 0.01.)"),
        answer=p,
        solution=(f"P(all different) = (365/365)(364/365)…({365 - m + 1}/365) = {p_distinct:.4f}, "
                  f"so P(at least one shared birthday) = **{p:.4f}**.\n\nShortcut: P(all different) ≈ exp(−m(m−1)/730) = "
                  f"{math.exp(-m * (m - 1) / 730):.4f}."),
    )


def g_bayes_test(rng):
    prev = rng.choice([0.005, 0.01, 0.02, 0.05])
    sens = rng.choice([0.90, 0.95, 0.98, 0.99])
    fpr = rng.choice([0.02, 0.05, 0.10])
    post = prev * sens / (prev * sens + (1 - prev) * fpr)
    return dict(
        prompt=(f"A condition affects **{prev:.1%}** of people. A test catches **{sens:.0%}** of true cases, "
                f"and gives a false positive for **{fpr:.0%}** of healthy people. Someone tests positive. "
                f"What is the probability they actually have the condition? (Within 0.005.)"),
        answer=post,
        solution=(f"Bayes: P(C|+) = P(+|C)P(C) / [P(+|C)P(C) + P(+|¬C)P(¬C)]\n\n"
                  f"= {sens}×{prev} / ({sens}×{prev} + {fpr}×{1 - prev:.3f}) = {prev * sens:.5f} / {prev * sens + (1 - prev) * fpr:.5f} "
                  f"= **{post:.4f}**.\n\nAn easier way to picture it: out of 10,000 people, {prev * 10000:.0f} are sick and {prev * sens * 10000:.0f} of them test positive, "
                  f"while {(1 - prev) * fpr * 10000:.0f} healthy people also test positive."),
    )


def g_double_headed(rng):
    n = rng.choice([10, 20, 50, 100, 1000])
    k = rng.randint(3, 10)
    f = Fraction(2 ** k, 2 ** k + n - 1)
    return dict(
        prompt=(f"A jar has **{n}** coins: {n - 1} fair and 1 with heads on both sides. You pick one at random "
                f"and flip it **{k}** times, getting **{k} heads**. What is the probability you picked the two-headed coin?"),
        answer=float(f),
        solution=(f"Prior odds two-headed : fair = 1 : {n - 1}. Likelihood ratio = 1 / (1/2)^{k} = {2 ** k}. "
                  f"Posterior odds = {2 ** k} : {n - 1}, so P = {2 ** k}/({2 ** k}+{n - 1}) = **{_frac(f)}**."),
    )


def g_monty_n(rng):
    n = rng.randint(3, 10)
    m = rng.randint(1, n - 2)
    f = Fraction(n - 1, n * (n - m - 1))
    return dict(
        prompt=(f"A game show has **{n}** doors: one hides a car and the rest hide goats. You pick a door. The host, who "
                f"knows where the car is, opens **{m}** of the other doors, all goats. You then switch to one of the "
                f"remaining unopened doors, chosen at random. What is the probability you win the car?"),
        answer=float(f),
        solution=(f"Your first pick is wrong with probability ({n}−1)/{n}. If it was wrong, the car is behind one of the "
                  f"{n - m - 1} other unopened doors, and you pick it with probability 1/{n - m - 1}.\n\n"
                  f"P = ({n - 1}/{n}) × 1/{n - m - 1} = **{_frac(f)}** (compare with staying: 1/{n} = {1 / n:.4f})."),
    )


def g_meeting(rng):
    T = 60
    w = rng.choice([5, 10, 12, 15, 20, 30])
    p = 1 - (1 - w / T) ** 2
    return dict(
        prompt=(f"Two friends each arrive at a café at a uniformly random time between 12:00 and 1:00, independently. "
                f"Whoever arrives first waits **{w} minutes** and then leaves. What is the probability they meet?"),
        answer=p,
        solution=(f"Plot the two arrival times on a 60×60 square. They meet when |x − y| ≤ {w}. "
                  f"The two corner triangles where they miss each other have area (60−{w})², so "
                  f"P = 1 − ({T - w}/60)² = **{p:.4f}**."),
        tol=0.002,
    )


def g_mod_power(rng):
    a = rng.randint(2, 9)
    b = rng.randint(20, 300)
    m = rng.choice([7, 9, 10, 11, 13])
    r = pow(a, b, m)
    cycle, x = [], 1
    for _ in range(m):
        x = x * a % m
        if x in cycle:
            break
        cycle.append(x)
    return dict(
        prompt=f"What is the remainder when **{a}^{b}** is divided by **{m}**?",
        answer=r,
        solution=(f"Powers of {a} mod {m} repeat in a cycle: {', '.join(map(str, cycle))} (length {len(cycle)}). "
                  f"Find where {b} falls in that cycle: {a}^{b} ≡ **{r}** (mod {m})."),
    )


def g_reroll_die(rng):
    n = rng.choice([6, 8, 10, 12, 20])
    e2 = Fraction(n + 1, 2)
    keep = [x for x in range(1, n + 1) if x > e2]
    ev = (Fraction(sum(keep)) + (n - len(keep)) * e2) / n
    return dict(
        prompt=(f"You roll a fair **{n}-sided** die and are paid its face value in dollars. After seeing the roll you may "
                f"roll once more, but then you must take the second result. With the best strategy, what is your expected payout?"),
        answer=float(ev),
        solution=(f"A reroll is worth E = ({n}+1)/2 = {float(e2)}. Keep a first roll only if it beats that, i.e. {keep[0]}…{n}.\n\n"
                  f"EV = [sum of kept faces + (rolls you reroll) × {float(e2)}] / {n} = "
                  f"[{sum(keep)} + {n - len(keep)}×{float(e2)}] / {n} = **{_frac(ev)}**."),
        tol=0.01,
    )


# --------------------------------------------------------------------------
# Level 3
# --------------------------------------------------------------------------

def g_consecutive_heads(rng):
    k = rng.randint(2, 6)
    ans = 2 ** (k + 1) - 2
    return dict(
        prompt=f"You flip a fair coin until you get **{k} heads in a row**. What is the expected number of flips?",
        answer=ans,
        solution=(f"Let E_k be the expected flips to reach k heads in a row. From k−1 in a row, one more flip either finishes (½) "
                  f"or sends you back to zero (½): E_k = E_(k−1) + 1 + ½·E_k, so E_k = 2E_(k−1) + 2. "
                  f"With E_0 = 0 this gives E_k = 2^(k+1) − 2 = **{ans}**."),
    )


def g_gamblers_ruin(rng):
    p = rng.choice([0.4, 0.45, 0.55, 0.6])
    N = rng.choice([5, 8, 10, 12])
    i = rng.randint(2, N - 2)
    r = (1 - p) / p
    ans = (1 - r ** i) / (1 - r ** N)
    return dict(
        prompt=(f"You start with **${i}** and bet $1 at a time. Each bet wins with probability **{p}**. You stop when you "
                f"reach **${N}** or go broke. What is the probability you reach ${N}? (Within 0.005.)"),
        answer=ans,
        solution=(f"Let r = q/p = {1 - p}/{p} = {r:.4f}. For biased steps, P(reach N from i) = (1 − r^i)/(1 − r^N) "
                  f"= (1 − {r ** i:.4f})/(1 − {r ** N:.4f}) = **{ans:.4f}**.\n\n(For a fair game this becomes i/N = {i / N:.3f}.)"),
        tol=0.005,
    )


def g_coupon(rng):
    n = rng.randint(4, 12)
    h = sum(Fraction(1, k) for k in range(1, n + 1))
    ans = n * h
    return dict(
        prompt=f"How many rolls of a fair **{n}-sided** die do you expect to need before every face has appeared at least once?",
        answer=float(ans),
        solution=(f"Once you have seen j faces, a new face turns up with probability ({n}−j)/{n}, so that stage takes {n}/({n}−j) rolls on average. "
                  f"Sum the stages: {n}(1 + 1/2 + … + 1/{n}) = {n} × H_{n} = **{float(ans):.3f}**."),
        tol=0.01,
    )


def g_distinct_faces(rng):
    n = rng.choice([6, 8, 10, 12, 20])
    k = rng.randint(3, 15)
    ans = n * (1 - (1 - 1 / n) ** k)
    return dict(
        prompt=f"You roll a fair **{n}-sided** die **{k}** times. What is the expected number of **different** faces you see?",
        answer=ans,
        solution=(f"Linearity of expectation with indicator variables: each face is missed in all {k} rolls with probability (1 − 1/{n})^{k}. "
                  f"E = {n} × [1 − ({n - 1}/{n})^{k}] = **{ans:.4f}**."),
        tol=0.005,
    )


def g_first_ace(rng):
    N = rng.choice([20, 32, 40, 52, 60])
    a = rng.randint(2, 6)
    f = Fraction(N + 1, a + 1)
    return dict(
        prompt=(f"A shuffled deck has **{N}** cards, **{a}** of them aces. You turn cards over one at a time. "
                f"What is the expected position of the **first ace**? (Count the ace itself.)"),
        answer=float(f),
        solution=(f"The {a} aces split the {N - a} non-aces into {a + 1} gaps, and by symmetry each gap has {N - a}/{a + 1} non-aces on average. "
                  f"First-ace position = 1 + ({N - a})/({a + 1}) = ({N}+1)/({a}+1) = **{_frac(f)}**."),
        tol=0.01,
    )


# --------------------------------------------------------------------------
# The bank, in serving order
# --------------------------------------------------------------------------

def _num(id, title, gb, level, gen, **kw):
    return Item(id=id, title=title, gb=gb, level=level, kind="numeric", gen=gen, **kw)


def _rev(id, title, gb, level, prompt):
    return Item(id=id, title=title, gb=gb, level=level, kind="review", prompt=prompt)


BANK: list[Item] = [
    # Level 1
    _num("dice_sum", "Two-dice sum", "§4.1 Basic probability", 1, g_dice_sum, abs_tol=0.001),
    _num("trailing_zeros", "Trailing zeros", "§2.2 Logic reasoning: Trailing zeros", 1, g_trailing_zeros),
    _num("missing_number", "Missing integer", "§2.5 Series summation: Missing integers", 1, g_missing_number),
    _num("at_least_one", "At least one", "§4.1 Basic probability", 1, g_at_least_one, abs_tol=0.0015),
    _num("pigeonhole", "Socks in the dark", "§2.6 Pigeon hole principle", 1, g_pigeonhole),
    _num("committee", "Committee with a chair", "§4.2 Combinatorial analysis", 1, g_committee),
    # Level 2
    _rev("rv_screwy_pirates", "Screwy pirates", "§2.1 Problem simplification: Screwy pirates", 2,
         "Work the **Screwy pirates** problem (§2.1) from scratch: start with the smallest case and build up. Then check the book's solution."),
    _num("double_headed", "Two-headed coin", "§4.3 Conditional probability: Unfair coin", 2, g_double_headed, abs_tol=0.002),
    _num("monty_n", "Monty Hall, n doors", "§4.3 Conditional probability: Monty Hall", 2, g_monty_n, abs_tol=0.002),
    _num("bayes_test", "Positive test", "§4.3 Bayes' formula", 2, g_bayes_test, abs_tol=0.005),
    _rev("rv_burning_ropes", "Burning ropes", "§2.2 Logic reasoning: Burning ropes", 2,
         "Do **Burning ropes** (§2.2). Before checking the book, also ask yourself: which other time intervals could you measure with two ropes?"),
    _num("mod_power", "Big power, small remainder", "§2.7 Modular arithmetic", 2, g_mod_power),
    _num("birthday", "Birthday clash", "§4.2 Combinatorial analysis: Birthday problem", 2, g_birthday, abs_tol=0.01),
    _num("meeting", "Café meeting", "§4.4 Distributions: Meeting probability", 2, g_meeting, abs_tol=0.002),
    _rev("rv_tiger_sheep", "Tiger and sheep", "§2.1 Problem simplification: Tiger and sheep", 2,
         "Do **Tiger and sheep** (§2.1). Write out the 1-, 2- and 3-tiger cases before you generalise."),
    _num("reroll_die", "One reroll", "§4.5 Expected value", 2, g_reroll_die, abs_tol=0.01),
    _rev("rv_defective_ball", "Defective ball", "§2.2 Logic reasoning: Defective ball", 2,
         "Do **Defective ball** (§2.2). Draw the full weighing tree, covering every outcome of every weighing."),
    _rev("rv_drunk_passenger", "Drunk passenger", "§4.1 Basic probability: Drunk passenger", 2,
         "Do **Drunk passenger** (§4.1). Look for the symmetry argument rather than a recursion."),
    # Level 3
    _num("consecutive_heads", "Heads in a row", "§4.5 Expected value / §5.1 Markov chains", 3, g_consecutive_heads),
    _num("first_ace", "First ace", "§4.5 Expected value: Aces", 3, g_first_ace, abs_tol=0.01),
    _num("distinct_faces", "Distinct faces", "§4.5 Expected value (indicator variables)", 3, g_distinct_faces, abs_tol=0.005),
    _rev("rv_chameleon", "Chameleon colors", "§2.7 Modular arithmetic: Chameleon colors", 3,
         "Do **Chameleon colors** (§2.7). Find the invariant first."),
    _num("coupon", "Collect every face", "§4.5 Expected value: Coupon collection", 3, g_coupon, rel_tol=0.005),
    _num("gamblers_ruin", "Biased gambler's ruin", "§4.3 Gambler's ruin problem", 3, g_gamblers_ruin, abs_tol=0.005),
    _rev("rv_light_switches", "Light switches", "§2.3 Thinking out of the box: Light switches", 3,
         "Do **Light switches** (§2.3). It's an out-of-the-box puzzle, so time-box it to 10 minutes before you read the solution."),
]

BY_ID = {it.id: it for it in BANK}


def make_instance(item: Item, rng) -> dict:
    """A concrete, servable question. Numeric items get fresh numbers."""
    if item.kind == "review":
        return {"prompt": item.prompt}
    inst = item.gen(rng)
    # A generator can tighten/loosen tolerance for its own draw.
    if "tol" in inst:
        inst["abs_tol"] = max(item.abs_tol, inst.pop("tol"))
    else:
        inst["abs_tol"] = item.abs_tol
    inst["rel_tol"] = item.rel_tol
    return inst


def parse_answer(text: str) -> float | None:
    """Accepts 0.375, 3/8, 37.5%, 1,234 and similar."""
    t = text.strip().replace(",", "").replace(" ", "")
    if not t:
        return None
    try:
        if t.endswith("%"):
            return float(t[:-1]) / 100
        if "/" in t:
            a, b = t.split("/", 1)
            return float(a) / float(b)
        return float(t)
    except (ValueError, ZeroDivisionError):
        return None


def is_correct(user: float, inst: dict) -> bool:
    ans = float(inst["answer"])
    return abs(user - ans) <= max(inst["abs_tol"], inst["rel_tol"] * abs(ans)) + 1e-12
