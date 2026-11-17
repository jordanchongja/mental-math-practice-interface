"""More Quant Practice items: original new-number questions for chapters 3-7,
plus a pointer card for every named problem in the Green Book.

Pointers carry only the section and problem name, never the book's text.
"""

from __future__ import annotations

import math
from fractions import Fraction


def _frac(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator} ≈ {float(f):.4f}" if f.denominator != 1 else str(f.numerator)


def _N(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _bs(S, K, sigma, r, T):
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2, S * _N(d1) - K * math.exp(-r * T) * _N(d2)


# ==========================================================================
# Chapter 3 -- calculus and linear algebra
# ==========================================================================

def g_deriv(rng):
    n = rng.randint(2, 5)
    k = rng.choice([-2, -1, 1, 2, 3])
    ans = (n + k) * math.exp(k)
    return dict(
        prompt=f"Let f(x) = x^{n} · e^({k}x). What is **f′(1)**? (3 significant figures is fine.)",
        answer=ans,
        solution=(f"Product rule: f′(x) = {n}x^{n - 1}e^({k}x) + {k}x^{n}e^({k}x) = x^{n - 1}e^({k}x)({n} + {k}x).\n\n"
                  f"At x = 1 this is ({n} + {k})e^{k} = **{ans:.4f}**."),
    )


def g_lhopital(rng):
    a = rng.randint(2, 9)
    return dict(
        prompt=f"Evaluate **lim (x→0) [e^({a}x) − 1 − {a}x] / x²**.",
        answer=a * a / 2,
        solution=(f"This is 0/0, so apply L'Hôpital twice: [{a}e^({a}x) − {a}] / 2x, then {a}²e^({a}x) / 2, which goes to {a}²/2 = **{a * a / 2}**.\n\n"
                  f"(Or use Taylor: e^({a}x) = 1 + {a}x + ({a}x)²/2 + …)"),
    )


def g_int_xnlnx(rng):
    n = rng.randint(1, 6)
    f = Fraction(-1, (n + 1) ** 2)
    return dict(
        prompt=f"Evaluate **∫₀¹ x^{n} ln x dx**.",
        answer=float(f),
        solution=(f"Integrate by parts with u = ln x and dv = x^{n} dx: the boundary term [x^{n + 1} ln x /{n + 1}] from 0 to 1 is 0, "
                  f"leaving −∫₀¹ x^{n}/{n + 1} dx = −1/{n + 1}² = **{_frac(f)}**."),
        tol=0.0005,
    )


def g_mgf_normal(rng):
    a = rng.choice([0.5, 1, 1.5, 2, 3])
    ans = math.exp(a * a / 2)
    return dict(
        prompt=f"Z is standard normal. What is **E[e^({a}Z)]**?",
        answer=ans,
        solution=(f"Complete the square inside the integral: ∫ e^(az) φ(z) dz = e^(a²/2) ∫ φ(z − a) dz = e^(a²/2). "
                  f"With a = {a}: e^{a * a / 2} = **{ans:.4f}**."),
    )


def g_newton(rng):
    N = rng.choice([n for n in range(2, 120) if int(math.isqrt(n)) ** 2 != n])
    x0 = round(math.sqrt(N))
    x1 = (x0 + N / x0) / 2
    return dict(
        prompt=f"Use **one step of Newton's method** on f(x) = x² − {N}, starting from x₀ = {x0}. What is x₁? (It approximates √{N}.)",
        answer=x1,
        solution=(f"x₁ = x₀ − f(x₀)/f′(x₀) = x₀ − (x₀² − {N})/(2x₀) = (x₀ + {N}/x₀)/2 = ({x0} + {N / x0:.4f})/2 = **{x1:.4f}**. "
                  f"The true value is √{N} = {math.sqrt(N):.4f}."),
        tol=0.001,
    )


def g_lagrange(rng):
    a, b = rng.randint(1, 5), rng.randint(1, 5)
    c = rng.randint(10, 60)
    f = Fraction(c * c, 4 * a * b)
    return dict(
        prompt=f"Maximise **xy** subject to {a}x + {b}y = {c}, with x, y > 0. What is the maximum value?",
        answer=float(f),
        solution=(f"Lagrange: y = λ·{a} and x = λ·{b}, so {a}x = {b}y and the budget splits evenly: {a}x = {b}y = {c}/2.\n\n"
                  f"x = {Fraction(c, 2 * a)}, y = {Fraction(c, 2 * b)}, so xy = c²/(4ab) = **{_frac(f)}**."),
        tol=0.001,
    )


def g_ode_double(rng):
    k = rng.choice([0.02, 0.03, 0.04, 0.05, 0.07, 0.1])
    ans = math.log(2) / k
    return dict(
        prompt=f"y′ = {k}·y with y(0) = 5. At what time t does y first reach **10**?",
        answer=ans,
        solution=(f"Separate the variables: dy/y = {k} dt, so y = 5e^({k}t). Setting 2 = e^({k}t) gives t = ln 2/{k} = **{ans:.3f}**. "
                  f"(This is the 'rule of 70': about 70/{k * 100:.0f}.)"),
        tol=0.01,
    )


def g_eig2(rng):
    a, d = rng.randint(1, 9), rng.randint(1, 9)
    b = rng.randint(1, 6)
    ans = (a + d) / 2 + math.sqrt(((a - d) / 2) ** 2 + b * b)
    return dict(
        prompt=f"What is the **largest eigenvalue** of the matrix [[{a}, {b}], [{b}, {d}]]?",
        answer=ans,
        solution=(f"λ² − (trace)λ + det = 0, where trace = {a + d} and det = {a * d - b * b}.\n\n"
                  f"λ = {a + d}/2 ± √(({a}−{d})²/4 + {b}²), so the largest is **{ans:.4f}**."),
        tol=0.005,
    )


def g_det3(rng):
    m = [[rng.randint(-3, 5) for _ in range(3)] for _ in range(3)]
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    rows = "; ".join("[" + ", ".join(map(str, r)) + "]" for r in m)
    return dict(
        prompt=f"Find the **determinant** of the matrix with rows {rows}.",
        answer=det,
        solution=(f"Expand along the first row: {a}·({e}·{i} − {f}·{h}) − {b}·({d}·{i} − {f}·{g}) + {c}·({d}·{h} − {e}·{g})\n\n"
                  f"= {a}·{e * i - f * h} − {b}·{d * i - f * g} + {c}·{d * h - e * g} = **{det}**."),
    )


def g_equicorr(rng):
    n = rng.randint(3, 12)
    f = Fraction(-1, n - 1)
    return dict(
        prompt=(f"{n} assets all have the same pairwise correlation ρ. What is the **smallest** ρ for which this "
                f"is a valid correlation matrix (positive semidefinite)?"),
        answer=float(f),
        solution=(f"The matrix is (1−ρ)I + ρ·11ᵀ, with eigenvalues 1 + ({n}−1)ρ (once) and 1 − ρ ({n - 1} times). "
                  f"Requiring 1 + {n - 1}ρ ≥ 0 gives ρ ≥ −1/{n - 1} = **{_frac(f)}**.\n\nAnother way to see it: Var(sum of all {n}) = {n} + {n}({n}−1)ρ ≥ 0."),
        tol=0.0005,
    )


# ==========================================================================
# Chapter 4 -- probability
# ==========================================================================

def g_rabbit(rng):
    n = rng.randint(5, 20)
    a, b = 1, 2
    for _ in range(n - 2):
        a, b = b, a + b
    return dict(
        prompt=f"A staircase has **{n}** steps. You climb 1 or 2 steps at a time. How many different ways can you reach the top?",
        answer=b,
        solution=(f"Ways(n) = Ways(n−1) + Ways(n−2), because the last move was either a 1-step or a 2-step. "
                  f"Starting from Ways(1)=1 and Ways(2)=2 this is the Fibonacci sequence, so Ways({n}) = **{b:,}**."),
    )


def g_all_boys(rng):
    n = rng.randint(2, 5)
    f = Fraction(1, 2 ** n - 1)
    return dict(
        prompt=(f"A family has **{n}** children (each a boy or girl with probability ½, independently). You learn that "
                f"**at least one** is a boy. What is the probability they are **all** boys?"),
        answer=float(f),
        solution=(f"Of the 2^{n} = {2 ** n} equally likely combinations, only 'all girls' is ruled out, which leaves {2 ** n - 1}. "
                  f"Exactly one of them is all boys, so P = **{_frac(f)}**."),
        tol=0.001,
    )


def g_dice_increasing(rng):
    n = rng.choice([4, 6, 8, 10, 12, 20])
    f = Fraction(math.comb(n, 3), n ** 3)
    return dict(
        prompt=f"Roll a fair **{n}-sided** die three times. What is the probability the results are **strictly increasing**?",
        answer=float(f),
        solution=(f"A strictly increasing triple is just a choice of 3 distinct faces, which can only be arranged in one increasing order: C({n},3) = {math.comb(n, 3)} ways, "
                  f"out of {n}³ = {n ** 3}. P = **{_frac(f)}**.\n\nCheck: P(all distinct) × 1/3! gives the same answer."),
        tol=0.001,
    )


def g_extinction(rng):
    while True:
        a = rng.choice([0.1, 0.15, 0.2, 0.25, 0.3])
        c = rng.choice([0.3, 0.4, 0.5, 0.6])
        if a < c and a + c <= 1:
            break
    b = round(1 - a - c, 2)
    ans = a / c
    return dict(
        prompt=(f"A cell either dies (prob {a}), stays as one cell (prob {b}), or splits into two (prob {c}). Every cell then "
                f"behaves independently in the same way. Starting from one cell, what is the probability the population **eventually dies out**?"),
        answer=ans,
        solution=(f"Condition on the first step. The extinction probability x satisfies x = {a} + {b}x + {c}x², i.e. {c}x² − {a + c:.2f}x + {a} = 0, "
                  f"which factors as ({c}x − {a})(x − 1) = 0. The extinction probability is the smaller root: x = {a}/{c} = **{ans:.4f}**."),
        tol=0.002,
    )


def g_poisson(rng):
    lam = rng.randint(2, 12)
    m = rng.choice([5, 10, 15, 20, 30])
    ans = math.exp(-lam * m / 60)
    return dict(
        prompt=(f"Trades arrive as a Poisson process at **{lam} per hour**. What is the probability of **no** trade "
                f"in the next **{m} minutes**?"),
        answer=ans,
        solution=f"In a Poisson process the waiting time is exponential: P(no arrival in t) = e^(−λt) = e^(−{lam}×{m}/60) = **{ans:.4f}**.",
        tol=0.002,
    )


def g_normal_moment(rng):
    mu = rng.randint(1, 4)
    s = rng.randint(1, 3)
    ans = mu ** 3 + 3 * mu * s * s
    return dict(
        prompt=f"X ~ Normal(mean {mu}, variance {s * s}). What is **E[X³]**?",
        answer=ans,
        solution=(f"Write X = μ + σZ. Then E[X³] = μ³ + 3μ²σE[Z] + 3μσ²E[Z²] + σ³E[Z³] = μ³ + 3μσ², since the odd moments of Z are 0.\n\n"
                  f"= {mu}³ + 3·{mu}·{s * s} = **{ans}**."),
    )


def g_hedge(rng):
    ss = rng.choice([0.15, 0.2, 0.25, 0.3])
    sf = rng.choice([0.18, 0.22, 0.25, 0.35])
    rho = rng.choice([0.6, 0.7, 0.8, 0.9, 0.95])
    h = rho * ss / sf
    return dict(
        prompt=(f"You hold a commodity with volatility {ss:.0%} and hedge it with a future with volatility {sf:.0%}; their correlation is {rho}. "
                f"What hedge ratio (futures per unit of commodity) **minimises the variance** of the hedged position?"),
        answer=h,
        solution=(f"Var(S − hF) = σ_S² − 2hρσ_Sσ_F + h²σ_F². Setting the derivative to 0 gives h* = ρσ_S/σ_F = {rho}×{ss}/{sf} = **{h:.4f}**. "
                  f"It's the regression beta of S on F."),
        tol=0.005,
    )


def g_sum_uniform(rng):
    x = rng.choice([0.3, 0.5, 0.8, 1.2, 1.5, 1.7])
    ans = x * x / 2 if x <= 1 else 1 - (2 - x) ** 2 / 2
    return dict(
        prompt=f"U₁ and U₂ are independent Uniform(0,1). What is **P(U₁ + U₂ ≤ {x})**?",
        answer=ans,
        solution=("Draw the unit square; the region below the line u₁ + u₂ = x is "
                  + (f"a triangle with area x²/2 = **{ans:.4f}**." if x <= 1 else
                     f"everything except the top-right triangle, whose area is (2−x)²/2. P = 1 − {(2 - x) ** 2 / 2:.4f} = **{ans:.4f}**.")),
        tol=0.002,
    )


def g_joint_default(rng):
    a = rng.choice([0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    b = rng.choice([0.4, 0.5, 0.6, 0.7, 0.8])
    want_min = rng.random() < 0.6
    ans = max(0.0, a + b - 1) if want_min else min(a, b)
    word = "smallest" if want_min else "largest"
    return dict(
        prompt=(f"Bond A defaults with probability {a} and bond B with probability {b}; you know nothing about how they're related. "
                f"What is the **{word}** possible probability that **both** default?"),
        answer=ans,
        solution=(f"P(A∩B) = P(A) + P(B) − P(A∪B), and P(A∪B) ≤ 1, so the minimum is max(0, {a}+{b}−1) = {max(0, a + b - 1):.2f}. "
                  f"The maximum is min({a},{b}) = {min(a, b)}, reached when one default always comes with the other.\n\nAnswer: **{ans:.2f}**."),
        tol=0.001,
    )


def g_order_stats(rng):
    n = rng.randint(2, 9)
    want_max = rng.random() < 0.5
    f = Fraction(n, n + 1) if want_max else Fraction(1, n + 1)
    return dict(
        prompt=f"Draw **{n}** independent Uniform(0,1) numbers. What is the expected value of the **{'largest' if want_max else 'smallest'}**?",
        answer=float(f),
        solution=(f"{n} random points split [0,1] into {n + 1} pieces, and by symmetry each has expected length 1/{n + 1}. "
                  f"So E[min] = 1/{n + 1} and E[max] = {n}/{n + 1}. Answer: **{_frac(f)}**.\n\n(Formally: P(max ≤ x) = xⁿ, so E[max] = ∫ x·n·x^(n−1) dx = n/(n+1).)"),
        tol=0.001,
    )


# ==========================================================================
# Chapter 5 -- stochastic processes
# ==========================================================================

def g_coin_pattern(rng):
    L = rng.choice([3, 3, 4])
    p = "".join(rng.choice("HT") for _ in range(L))
    overlaps = [k for k in range(1, L + 1) if p[:k] == p[-k:]]
    ans = sum(2 ** k for k in overlaps)
    return dict(
        prompt=f"Flip a fair coin until the pattern **{p}** first appears. What is the expected number of flips?",
        answer=ans,
        solution=(f"Use overlaps (the 'gambling team' martingale argument): add up 2^k for every k where the first k letters of {p} equal the last k letters. "
                  f"That happens for k = {', '.join(map(str, overlaps))}, so E = {' + '.join(f'2^{k}' for k in overlaps)} = **{ans}**.\n\n"
                  f"Patterns that overlap themselves (like HH…) take longer to appear."),
    )


def g_walk_exit(rng):
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    ask_time = rng.random() < 0.5
    if ask_time:
        ans, txt = a * b, "the expected number of steps until it stops"
    else:
        ans, txt = float(Fraction(b, a + b)), f"the probability it stops at **+{a}**"
    return dict(
        prompt=f"A symmetric ±1 random walk starts at 0 and stops when it hits **+{a}** or **−{b}**. What is {txt}?",
        answer=ans,
        solution=(f"S_n is a martingale, so E[S_τ] = 0: p·{a} − (1−p)·{b} = 0 → p = {b}/({a}+{b}) = {b / (a + b):.4f}.\n\n"
                  f"S_n² − n is also a martingale, so E[τ] = E[S_τ²] = p·{a}² + (1−p)·{b}² = {a}×{b} = {a * b}.\n\nAnswer: **{ans if ask_time else round(ans, 4)}**."),
        tol=0.001,
    )


def g_bm_both_pos(rng):
    s, t = rng.choice([(1, 2), (1, 4), (1, 3), (2, 3), (1, 9)])
    ans = 0.25 + math.asin(math.sqrt(s / t)) / (2 * math.pi)
    return dict(
        prompt=f"W is a standard Brownian motion. What is **P(W_{s} > 0 and W_{t} > 0)**?",
        answer=ans,
        solution=(f"(W_{s}, W_{t}) is bivariate normal with correlation ρ = √({s}/{t}) = {math.sqrt(s / t):.4f}. For a centred bivariate normal, "
                  f"P(both > 0) = 1/4 + arcsin(ρ)/(2π) = **{ans:.4f}**."),
        tol=0.002,
    )


def g_bm_var(rng):
    s, t = sorted(rng.sample(range(1, 10), 2))
    a, b = rng.choice([1, 2, 3, -1]), rng.choice([1, 2, -2, 3])
    ans = a * a * s + b * b * t + 2 * a * b * s
    return dict(
        prompt=f"W is a standard Brownian motion. What is **Var({a}·W_{s} + {b}·W_{t})**?",
        answer=ans,
        solution=(f"Var(W_s) = s, Var(W_t) = t and Cov(W_s, W_t) = min(s,t) = {s}.\n\n"
                  f"Var = {a}²·{s} + {b}²·{t} + 2·{a}·{b}·{s} = **{ans}**."),
    )


def g_ito_moment(rng):
    t = rng.randint(1, 6)
    if rng.random() < 0.5:
        return dict(
            prompt=f"W is a standard Brownian motion. What is **E[W_{t}⁴]**?",
            answer=3 * t * t,
            solution=(f"Itô: d(W⁴) = 4W³dW + 6W²dt, so E[W_t⁴] = ∫₀ᵗ 6E[W_u²]du = ∫₀ᵗ 6u du = 3t² = **{3 * t * t}**. "
                      f"(Equivalently, a normal's 4th moment is 3σ⁴.)"),
        )
    sig = rng.choice([0.5, 1, 2])
    ans = math.exp(sig * sig * t / 2)
    return dict(
        prompt=f"W is a standard Brownian motion. What is **E[e^({sig}·W_{t})]**?",
        answer=ans,
        solution=f"W_{t} ~ N(0, {t}), so this is the normal MGF: e^(σ²t/2) = e^({sig * sig * t / 2}) = **{ans:.4f}**.",
    )


def g_world_series(rng):
    p = rng.choice([0.55, 0.6, 0.65])
    n = rng.choice([3, 4])
    q = 1 - p
    ans = sum(math.comb(n - 1 + k, k) * p ** n * q ** k for k in range(n))
    return dict(
        prompt=(f"Team A wins each game against Team B with probability {p}, independently. They play a **best-of-{2 * n - 1}** series. "
                f"What is the probability Team A wins the series?"),
        answer=ans,
        solution=(f"A wins the series in game {n}+k by winning that game and {n - 1} of the previous {n - 1}+k games:\n\n"
                  f"P = Σ_(k=0..{n - 1}) C({n - 1}+k, k)·p^{n}·q^k = **{ans:.4f}**.\n\nA small per-game edge gets amplified by the longer series."),
        tol=0.002,
    )


# ==========================================================================
# Chapter 6 -- finance
# ==========================================================================

def g_pcp(rng):
    S = rng.choice([80, 95, 100, 110, 120])
    K = rng.choice([90, 100, 105, 110])
    r = rng.choice([0.0, 0.02, 0.04, 0.05])
    T = rng.choice([0.25, 0.5, 1.0])
    C = round(max(S - K * math.exp(-r * T), 0) + rng.uniform(2, 8), 2)
    P = C - S + K * math.exp(-r * T)
    return dict(
        prompt=(f"A non-dividend stock trades at {S}. A European call with strike {K} and expiry {T}y costs {C}; the rate is {r:.0%} "
                f"(continuous). What should the matching European **put** cost?"),
        answer=P,
        solution=(f"Put-call parity: C − P = S − K·e^(−rT). P = C − S + K·e^(−rT) = {C} − {S} + {K}×{math.exp(-r * T):.4f} = **{P:.3f}**."),
        tol=0.01,
    )


def _bs_inputs(rng):
    return (100, rng.choice([90, 95, 100, 105, 110]), rng.choice([0.2, 0.25, 0.3, 0.4]),
            rng.choice([0.0, 0.02, 0.05]), rng.choice([0.25, 0.5, 1.0]))


def g_bs_call(rng):
    S, K, s, r, T = _bs_inputs(rng)
    d1, d2, c = _bs(S, K, s, r, T)
    return dict(
        prompt=f"Black-Scholes: S = {S}, K = {K}, σ = {s:.0%}, r = {r:.0%}, T = {T}y, no dividends. What is the **call price**? (Calculator allowed; within 1%.)",
        answer=c,
        solution=(f"d1 = [ln(S/K) + (r + σ²/2)T]/(σ√T) = {d1:.4f}, d2 = d1 − σ√T = {d2:.4f}.\n\n"
                  f"C = S·N(d1) − K·e^(−rT)·N(d2) = {S}×{_N(d1):.4f} − {K * math.exp(-r * T):.3f}×{_N(d2):.4f} = **{c:.3f}**."),
        rel=0.01,
    )


def g_atm_approx(rng):
    S = rng.choice([50, 80, 100, 200, 400])
    s = rng.choice([0.16, 0.2, 0.25, 0.3, 0.4])
    T = rng.choice([0.25, 0.5, 1.0])
    _, _, c = _bs(S, S, s, 0.0, T)
    return dict(
        prompt=(f"Estimate in your head: an **at-the-money** call, S = K = {S}, σ = {s:.0%}, T = {T}y, r = 0. "
                f"What does it roughly cost? (Within 3% counts.)"),
        answer=c,
        solution=(f"Rule of thumb: ATM call ≈ 0.4·S·σ·√T (since 1/√(2π) ≈ 0.4) = 0.4×{S}×{s}×{math.sqrt(T):.3f} = {0.4 * S * s * math.sqrt(T):.3f}. "
                  f"The exact Black-Scholes price is **{c:.3f}**."),
        rel=0.03,
    )


def g_delta(rng):
    S, K, s, r, T = _bs_inputs(rng)
    d1, _, _ = _bs(S, K, s, r, T)
    return dict(
        prompt=f"Black-Scholes: S = {S}, K = {K}, σ = {s:.0%}, r = {r:.0%}, T = {T}y. What is the **delta** of the call?",
        answer=_N(d1),
        solution=f"Call delta = N(d1), where d1 = {d1:.4f}. Δ = **{_N(d1):.4f}**. (The put delta is N(d1) − 1 = {_N(d1) - 1:.4f}.)",
        tol=0.005,
    )


def g_binary(rng):
    S, K, s, r, T = _bs_inputs(rng)
    _, d2, _ = _bs(S, K, s, r, T)
    ans = math.exp(-r * T) * _N(d2)
    return dict(
        prompt=(f"A cash-or-nothing call pays **$1** if S_T > K. With S = {S}, K = {K}, σ = {s:.0%}, r = {r:.0%}, T = {T}y "
                f"(Black-Scholes), what is it worth?"),
        answer=ans,
        solution=(f"Value = e^(−rT)·P_Q(S_T > K) = e^(−rT)·N(d2), where d2 = {d2:.4f}. Value = {math.exp(-r * T):.4f}×{_N(d2):.4f} = **{ans:.4f}**.\n\n"
                  f"It's also the limit of a tight call spread: −∂C/∂K."),
        tol=0.005,
    )


def g_bull_spread(rng):
    K1 = rng.choice([90, 95, 100])
    K2 = K1 + rng.choice([5, 10, 15])
    cost = round(rng.uniform(1, (K2 - K1) * 0.7), 1)
    ask_be = rng.random() < 0.5
    ans = K1 + cost if ask_be else K2 - K1 - cost
    return dict(
        prompt=(f"You buy a {K1} call and sell a {K2} call (same expiry), paying **{cost}** net. What is your "
                f"{'**breakeven** stock price at expiry' if ask_be else '**maximum profit**'}?"),
        answer=ans,
        solution=(f"The payoff runs from 0 below {K1} up to {K2 - K1} above {K2}. Max profit = {K2 - K1} − {cost} = {K2 - K1 - cost:.1f}. "
                  f"Breakeven = {K1} + {cost} = {K1 + cost:.1f}.\n\nAnswer: **{ans:.1f}**."),
        tol=0.01,
    )


def g_var(rng):
    V = rng.choice([1, 5, 10, 50])
    sd = rng.choice([0.8, 1.0, 1.2, 1.5, 2.0])
    conf, z = rng.choice([(95, 1.645), (99, 2.326)])
    h = rng.choice([1, 5, 10])
    ans = z * sd / 100 * math.sqrt(h) * V
    return dict(
        prompt=(f"A ${V}M portfolio has daily return volatility {sd}% (normal, zero mean, i.i.d.). What is its **{h}-day {conf}% VaR** in $M?"),
        answer=ans,
        solution=(f"VaR = z·σ_daily·√h·V = {z}×{sd}%×√{h}×{V} = **{ans:.4f}** $M.\n\nScaling by √h assumes independent daily returns."),
        rel=0.01,
    )


def g_duration(rng):
    P = 100
    D = rng.choice([3, 5, 7, 10])
    C = rng.choice([20, 40, 60, 100])
    bp = rng.choice([-100, -50, 25, 50, 100, 150])
    dy = bp / 10000
    dP = P * (-D * dy + 0.5 * C * dy * dy)
    return dict(
        prompt=(f"A bond priced at {P} has modified duration {D} and convexity {C}. Yields move **{bp:+d} bp**. "
                f"Estimate the **price change**, using duration and convexity."),
        answer=dP,
        solution=(f"ΔP ≈ P[−D·Δy + ½·C·Δy²] = {P}[−{D}×{dy} + ½×{C}×{dy}²] = {P * -D * dy:.4f} + {P * 0.5 * C * dy * dy:.4f} = **{dP:.4f}**.\n\n"
                  f"Convexity always adds to the price, whichever way yields move."),
        tol=0.01,
    )


def g_forward(rng):
    S = rng.choice([50, 100, 250, 3000])
    r = rng.choice([0.02, 0.04, 0.05])
    q = rng.choice([0.0, 0.01, 0.03])
    T = rng.choice([0.25, 0.5, 1, 2])
    F = S * math.exp((r - q) * T)
    return dict(
        prompt=f"Spot {S}, continuous rate {r:.0%}, dividend/convenience yield {q:.0%}, maturity {T}y. What is the **fair forward price**?",
        answer=F,
        solution=f"Cost of carry: F = S·e^((r−q)T) = {S}×e^({(r - q) * T:.4f}) = **{F:.3f}**. Any other price lets you buy one leg, sell the other and lock in a profit.",
        rel=0.0005,
    )


def g_minvar(rng):
    s1 = rng.choice([0.1, 0.15, 0.2])
    s2 = rng.choice([0.2, 0.25, 0.3])
    rho = rng.choice([-0.3, 0.0, 0.2, 0.5])
    w = (s2 ** 2 - rho * s1 * s2) / (s1 ** 2 + s2 ** 2 - 2 * rho * s1 * s2)
    return dict(
        prompt=(f"Asset 1 has volatility {s1:.0%} and asset 2 has {s2:.0%}, with correlation {rho}. What weight in **asset 1** gives the "
                f"**minimum-variance** fully invested portfolio?"),
        answer=w,
        solution=(f"Minimise w²σ₁² + (1−w)²σ₂² + 2w(1−w)ρσ₁σ₂ over w:\n\n"
                  f"w* = (σ₂² − ρσ₁σ₂)/(σ₁² + σ₂² − 2ρσ₁σ₂) = **{w:.4f}**."),
        tol=0.005,
    )


# ==========================================================================
# Chapter 7 -- algorithms
# ==========================================================================

def g_max_subarray(rng):
    arr = [rng.randint(-9, 9) for _ in range(9)]
    best, bi, bj = arr[0], 0, 0
    cur, ci = 0, 0
    for j, x in enumerate(arr):
        if cur <= 0:
            cur, ci = x, j
        else:
            cur += x
        if cur > best:
            best, bi, bj = cur, ci, j
    return dict(
        prompt=f"What is the largest sum of a **contiguous** (non-empty) run in: {arr}?",
        answer=best,
        solution=(f"Kadane's algorithm: keep a running sum and restart it whenever it drops to 0 or below; track the best seen. "
                  f"Best run = {arr[bi:bj + 1]} (positions {bi + 1}–{bj + 1}), sum **{best}**. It runs in O(n)."),
    )


def g_poison(rng):
    n = rng.choice([100, 500, 1000, 2000, 5000, 10000])
    ans = math.ceil(math.log2(n))
    return dict(
        prompt=(f"One of **{n:,}** bottles is poisoned. A taster shows symptoms a day later, so there's only time for **one round** of tasting. "
                f"What is the minimum number of tasters needed to identify the bottle?"),
        answer=ans,
        solution=(f"Number the bottles in binary. Taster i drinks from every bottle whose i-th bit is 1, and the pattern of sick tasters spells out the bad bottle's number. "
                  f"You need 2^k ≥ {n:,}, so k = ⌈log₂ {n:,}⌉ = **{ans}**."),
    )


def g_popcount(rng):
    n = rng.randint(100, 2000)
    return dict(
        prompt=f"How many **1 bits** are in the binary representation of **{n}**?",
        answer=bin(n).count("1"),
        solution=(f"{n} = {bin(n)[2:]} in binary, which has **{bin(n).count('1')}** ones.\n\nBit trick: n & (n−1) clears the lowest set bit, "
                  f"so you can count the ones by repeating it until n = 0. A power of 2 is a positive n with n & (n−1) = 0."),
    )


# id, title, section pointer, level, generator, extra tolerance kwargs
NUMERIC = [
    ("rabbit", "Staircase hops", "§4.2 Combinatorial analysis: Hopping rabbit", 2, g_rabbit, {}),
    ("all_boys", "At least one boy", "§4.3 Conditional probability: Boys and girls", 2, g_all_boys, {"abs_tol": 0.001}),
    ("dice_increasing", "Increasing dice", "§4.3 Conditional probability: Dice order", 2, g_dice_increasing, {"abs_tol": 0.001}),
    ("poisson", "Quiet minutes", "§4.4 Distributions: Poisson process", 2, g_poisson, {"abs_tol": 0.002}),
    ("order_stats", "Max and min of uniforms", "§4.6 Order statistics: Expected max and min", 2, g_order_stats, {"abs_tol": 0.001}),
    ("joint_default", "Both default", "§4.5 Expected value: Joint default probability", 2, g_joint_default, {"abs_tol": 0.001}),
    ("poison", "Poisoned bottle", "§7.2 The power of two: Poisonous wine", 2, g_poison, {}),
    ("popcount", "Count the bits", "§7.2 The power of two", 2, g_popcount, {}),
    ("pcp", "Put-call parity", "§6.1 Option pricing: Put-call parity", 3, g_pcp, {"abs_tol": 0.01}),
    ("forward", "Fair forward", "§6.4 Other finance: Forward and futures", 3, g_forward, {"rel_tol": 0.0005}),
    ("bull_spread", "Bull call spread", "§6.3 Option portfolios: Bull spread", 3, g_bull_spread, {"abs_tol": 0.01}),
    ("sum_uniform", "Sum of two uniforms", "§4.5 Expected value: Sum of random variables", 3, g_sum_uniform, {"abs_tol": 0.002}),
    ("normal_moment", "Third moment of a normal", "§4.4 Distributions: Moments of normal", 3, g_normal_moment, {}),
    ("hedge", "Minimum-variance hedge", "§4.5 Expected value: Optimal hedge ratio", 3, g_hedge, {"abs_tol": 0.005}),
    ("extinction", "Cell population dies out", "§4.3 Conditional probability: Amoeba population", 3, g_extinction, {"abs_tol": 0.002}),
    ("deriv", "Product-rule derivative", "§3.1 Limits and derivatives", 3, g_deriv, {"rel_tol": 0.002}),
    ("lhopital", "0/0 limit", "§3.1 L'Hospital's rule", 3, g_lhopital, {"abs_tol": 0.001}),
    ("int_xnlnx", "x^n ln x integral", "§3.2 Integration", 3, g_int_xnlnx, {"abs_tol": 0.0005}),
    ("mgf_normal", "Normal MGF", "§3.2 Expected value using integration", 3, g_mgf_normal, {"rel_tol": 0.002}),
    ("newton", "Newton step", "§3.4 Newton's method", 3, g_newton, {"abs_tol": 0.001}),
    ("lagrange", "Constrained max", "§3.4 Lagrange multipliers", 3, g_lagrange, {"abs_tol": 0.001}),
    ("ode_double", "Doubling time", "§3.5 Separable differential equations", 3, g_ode_double, {"abs_tol": 0.01}),
    ("eig2", "2×2 eigenvalue", "§3.6 Determinant, eigenvalue and eigenvector", 3, g_eig2, {"abs_tol": 0.005}),
    ("det3", "3×3 determinant", "§3.6 Determinant", 3, g_det3, {}),
    ("equicorr", "Equicorrelation bound", "§3.6 Positive semidefinite matrix", 3, g_equicorr, {"abs_tol": 0.0005}),
    ("max_subarray", "Best contiguous run", "§7.1 Algorithms: Maximum contiguous subarray", 3, g_max_subarray, {}),
    ("coin_pattern", "Waiting for a pattern", "§5.1 Markov chain: Coin triplets", 4, g_coin_pattern, {}),
    ("walk_exit", "Random walk exit", "§5.2 Martingale and random walk", 4, g_walk_exit, {"abs_tol": 0.001}),
    ("world_series", "Best-of-n series", "§5.3 Dynamic programming: World series", 4, g_world_series, {"abs_tol": 0.002}),
    ("bm_var", "Brownian covariance", "§5.4 Brownian motion", 4, g_bm_var, {}),
    ("bm_both_pos", "Brownian motion positive twice", "§5.4 Brownian motion", 4, g_bm_both_pos, {"abs_tol": 0.002}),
    ("ito_moment", "Itô moments", "§5.4 Itô's lemma", 4, g_ito_moment, {"rel_tol": 0.002}),
    ("atm_approx", "ATM call in your head", "§6.1 Option pricing: Black-Scholes formula", 4, g_atm_approx, {"rel_tol": 0.03}),
    ("bs_call", "Black-Scholes call", "§6.1 Option pricing: Black-Scholes formula", 4, g_bs_call, {"rel_tol": 0.01}),
    ("delta", "Call delta", "§6.2 The Greeks: Delta", 4, g_delta, {"abs_tol": 0.005}),
    ("binary", "Digital call", "§6.3 Exotic options: Binary options", 4, g_binary, {"abs_tol": 0.005}),
    ("var", "Value at risk", "§6.4 Other finance: Value at risk", 4, g_var, {"rel_tol": 0.01}),
    ("duration", "Duration + convexity", "§6.4 Other finance: Duration and convexity", 4, g_duration, {"abs_tol": 0.01}),
    ("minvar", "Two-asset min variance", "§6.4 Other finance: Portfolio optimization", 4, g_minvar, {"abs_tol": 0.005}),
]


# ==========================================================================
# Pointer cards: every named problem in the book (1st-edition numbering).
# (section, name, level, is_topic). Topic cards cover a block of unnamed problems.
# ==========================================================================

POINTERS = [
    ("2.2", "River crossing", 2, False), ("2.2", "Birthday problem", 2, False), ("2.2", "Card game", 2, False),
    ("2.2", "Trailing zeros", 2, False), ("2.2", "Horse race", 2, False), ("2.2", "Infinite sequence", 2, False),
    ("2.3", "Box packing", 2, False), ("2.3", "Calendar cubes", 2, False), ("2.3", "Door to offer", 2, False),
    ("2.3", "Message delivery", 2, False), ("2.3", "Last ball", 2, False), ("2.3", "Quant salary", 2, False),
    ("2.4", "Coin piles", 2, False), ("2.4", "Mislabeled bags", 2, False), ("2.4", "Wise men", 2, False),
    ("2.5", "Clock pieces", 2, False), ("2.5", "Missing integers", 2, False), ("2.5", "Counterfeit coins I", 2, False),
    ("2.6", "Matching socks", 2, False), ("2.6", "Handshakes", 2, False), ("2.6", "Have we met before?", 2, False),
    ("2.6", "Ants on a square", 2, False), ("2.6", "Counterfeit coins II", 3, False),
    ("2.7", "Prisoner problem", 3, False), ("2.7", "Division by 9", 2, False),
    ("2.8", "Coin split problem", 2, False), ("2.8", "Chocolate bar problem", 2, False), ("2.8", "Race track", 3, False),
    ("2.9", "Irrational number", 2, False), ("2.9", "Rainbow hats", 3, False),
    ("3.1", "Basics of derivatives", 3, True), ("3.1", "Maximum and minimum", 3, True), ("3.1", "L'Hospital's rule", 3, True),
    ("3.2", "Basics of integration", 3, True), ("3.2", "Applications of integration", 3, True),
    ("3.2", "Expected value using integration", 3, True), ("3.3", "Partial derivatives and multiple integrals", 3, True),
    ("3.4", "Taylor's series", 3, True), ("3.4", "Newton's method", 3, True), ("3.4", "Lagrange multipliers", 3, True),
    ("3.5", "Separable differential equations", 3, True), ("3.5", "First-order linear differential equations", 3, True),
    ("3.5", "Homogeneous linear equations", 3, True), ("3.5", "Nonhomogeneous linear equations", 3, True),
    ("3.6", "Vectors", 3, True), ("3.6", "QR decomposition", 3, True), ("3.6", "Determinant, eigenvalue and eigenvector", 3, True),
    ("3.6", "Positive semidefinite/definite matrix", 3, True), ("3.6", "LU decomposition and Cholesky decomposition", 3, True),
    ("4.1", "Coin toss game", 2, False), ("4.1", "Card game", 2, False), ("4.1", "N points on a circle", 3, False),
    ("4.2", "Poker hands", 2, False), ("4.2", "Hopping rabbit", 2, False), ("4.2", "Screwy pirates 2", 3, False),
    ("4.2", "Chess tournament", 3, False), ("4.2", "Application letters", 3, False), ("4.2", "Birthday problem", 2, False),
    ("4.2", "100th digit", 3, False), ("4.2", "Cubic of integer", 3, False),
    ("4.3", "Boys and girls", 2, False), ("4.3", "All-girl world?", 2, False), ("4.3", "Unfair coin", 2, False),
    ("4.3", "Fair probability from an unfair coin", 2, False), ("4.3", "Dart game", 3, False), ("4.3", "Birthday line", 3, False),
    ("4.3", "Dice order", 2, False), ("4.3", "Monty Hall problem", 2, False), ("4.3", "Amoeba population", 3, False),
    ("4.3", "Candies in a jar", 3, False), ("4.3", "Coin toss game", 3, False), ("4.3", "Russian roulette series", 3, False),
    ("4.3", "Aces", 3, False), ("4.3", "Gambler's ruin problem", 3, False), ("4.3", "Basketball scores", 3, False),
    ("4.3", "Cars on road", 3, False),
    ("4.4", "Meeting probability", 3, False), ("4.4", "Probability of triangle", 3, False),
    ("4.4", "Property of Poisson process", 3, False), ("4.4", "Moments of normal distribution", 3, False),
    ("4.5", "Connecting noodles", 3, False), ("4.5", "Optimal hedge ratio", 3, False), ("4.5", "Dice game", 3, False),
    ("4.5", "Card game", 3, False), ("4.5", "Sum of random variables", 3, False), ("4.5", "Coupon collection", 3, False),
    ("4.5", "Joint default probability", 3, False),
    ("4.6", "Expected value of max and min", 3, False), ("4.6", "Correlation of max and min", 4, False),
    ("4.6", "Random ant", 4, False),
    ("5.1", "Gambler's ruin problem", 4, False), ("5.1", "Dice question", 4, False), ("5.1", "Coin triplets", 4, False),
    ("5.1", "Color balls", 4, False),
    ("5.2", "Dice game", 4, False), ("5.2", "Ticket line", 4, False), ("5.2", "Coin sequence", 4, False),
    ("5.3", "Dynamic programming algorithm", 4, True), ("5.3", "Dice game", 4, False), ("5.3", "World series", 4, False),
    ("5.3", "Dynamic dice game", 4, False), ("5.3", "Dynamic card game", 4, False),
    ("5.4", "Brownian motion", 4, True), ("5.4", "Stopping time / first passage time", 4, True), ("5.4", "Itô's lemma", 4, True),
    ("6.1", "Price direction of options", 4, False), ("6.1", "Put-call parity", 4, False),
    ("6.1", "American vs. European options", 4, False), ("6.1", "Black-Scholes-Merton differential equation", 4, True),
    ("6.1", "Black-Scholes formula", 4, True),
    ("6.2", "Delta", 4, True), ("6.2", "Gamma", 4, True), ("6.2", "Theta", 4, True), ("6.2", "Vega", 4, True),
    ("6.3", "Bull spread", 4, False), ("6.3", "Straddle", 4, False), ("6.3", "Binary options", 4, False),
    ("6.3", "Exchange options", 4, False),
    ("6.4", "Portfolio optimization", 4, False), ("6.4", "Value at risk", 4, False),
    ("6.4", "Duration and convexity", 4, False), ("6.4", "Forward and futures", 4, False),
    ("6.4", "Interest rate models", 4, True),
    ("7.1", "Number swap", 3, False), ("7.1", "Unique element", 3, False), ("7.1", "Horner's algorithm", 3, False),
    ("7.1", "Moving average", 3, False), ("7.1", "Sorting algorithm", 3, False), ("7.1", "Random permutation", 3, False),
    ("7.1", "Search algorithm", 3, False), ("7.1", "Fibonacci numbers", 3, False),
    ("7.1", "Maximum contiguous subarray", 3, False),
    ("7.2", "Power of 2?", 3, False), ("7.2", "Multiplication by 7", 3, False), ("7.2", "Probability simulation", 3, False),
    ("7.2", "Poisonous wine", 3, False),
    ("7.3", "Monte Carlo simulation", 4, True), ("7.3", "Finite difference method", 4, True),
]
