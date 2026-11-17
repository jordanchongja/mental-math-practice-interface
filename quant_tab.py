"""Quant Practice tab: one Green Book-style question a day, with spaced retests.

Scheduling (a simple Leitner box):
  * a new question is served once nothing is due for review
  * a wrong answer comes back the next day, with new numbers
  * each correct answer pushes the next review further out: 3, 7, 14, 30, 60 days

History lives in the app's existing answer log (Google Sheet or SQLite).
Each answer is logged with tab_name "Quant::<question id>", so it needs no
new storage. The log is read once per browser session and then kept up to
date in memory. Every tab's code runs on every Streamlit rerun, so reading
the Sheet on each rerun would slow down the speed drills.
"""

from __future__ import annotations

import random
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from quant_bank import BANK, BY_ID, is_correct, make_instance, parse_answer
from storage import log_performance, read_logs

PREFIX = "Quant::"
SGT = timezone(timedelta(hours=8))   # Singapore has no DST
INTERVALS = [3, 7, 14, 30, 60]        # days until the next review after 1, 2, 3... correct in a row
XP_CORRECT = 25


def today() -> date:
    return datetime.now(SGT).date()


def _load_history() -> list[dict]:
    try:
        df = read_logs()
    except Exception as e:
        st.warning(f"Couldn't load past quant answers ({e}); scheduling from this session only.")
        return []
    df = df[df["tab_name"].astype(str).str.startswith(PREFIX)]
    if df.empty:
        return []
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce").dt.tz_convert(SGT)
    out = [
        {"qid": name[len(PREFIX):], "date": t.date(), "correct": bool(c)}
        for name, t, c in zip(df["tab_name"], ts, df["is_correct"])
        if pd.notna(t)
    ]
    out.sort(key=lambda r: r["date"])
    return out


def _schedule(history: list[dict]) -> dict:
    """qid -> {box, last, due, last_correct, attempts}."""
    state: dict[str, dict] = {}
    for r in history:
        s = state.setdefault(r["qid"], {"box": 0, "attempts": 0})
        s["attempts"] += 1
        s["box"] = s["box"] + 1 if r["correct"] else 0
        s["last"] = r["date"]
        s["last_correct"] = r["correct"]
    for s in state.values():
        gap = INTERVALS[min(s["box"], len(INTERVALS)) - 1] if s["box"] > 0 else 1
        s["due"] = s["last"] + timedelta(days=gap)
    return state


def _pick_next(sched: dict, exclude: set[str]) -> tuple[str, str]:
    """(qid, reason). Due reviews come first (most overdue first), then the next new question in bank order."""
    t = today()
    due = sorted(
        (s["due"], qid) for qid, s in sched.items()
        if qid in BY_ID and s["due"] <= t and qid not in exclude
    )
    if due:
        qid = due[0][1]
        s = sched[qid]
        why = "missed last time" if not s["last_correct"] else f"review, {s['box']} correct in a row"
        return qid, f"🔁 Retest ({why}, last seen {s['last']:%d %b})"
    for it in BANK:
        if it.id not in sched and it.id not in exclude:
            return it.id, "🆕 New question"
    # Everything seen and nothing due: practise the one due soonest.
    pool = [q for q in sched if q in BY_ID and q not in exclude] or [it.id for it in BANK]
    qid = min(pool, key=lambda q: sched.get(q, {}).get("due", t))
    return qid, "➕ Extra practice (nothing due)"


def _serve(qid: str, reason: str) -> None:
    st.session_state.quant_q = {
        "qid": qid,
        "reason": reason,
        "inst": make_instance(BY_ID[qid], random.Random()),
        "start": time.time(),
        "result": None,
    }


def _record(qid: str, correct: bool, elapsed: float) -> None:
    xp = XP_CORRECT if correct else 0
    log_performance(PREFIX + qid, correct, elapsed, xp)
    st.session_state.total_xp += xp
    st.session_state.quant_history.append({"qid": qid, "date": today(), "correct": correct})


def render() -> None:
    st.header("Quant Practice")
    st.caption("One Green Book-style question a day, easiest first. Questions you miss come back the next day with new numbers.")

    if "quant_history" not in st.session_state:
        st.session_state.quant_history = _load_history()
        st.session_state.quant_q = None

    history = st.session_state.quant_history
    sched = _schedule(history)
    done_today = [r for r in history if r["date"] == today()]

    t = today()
    n_due = sum(1 for q, s in sched.items() if q in BY_ID and s["due"] <= t)
    n_new = sum(1 for it in BANK if it.id not in sched)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Done today", len(done_today))
    c2.metric("Due for retest", n_due)
    c3.metric("New left", n_new)
    c4.metric("Day streak", _day_streak(history))

    if done_today and st.session_state.quant_q is None:
        st.success("✅ Today's question is done. Come back tomorrow, or keep going if you want more.")
        if not st.button("Give me another one", key="quant_more"):
            _progress_table(sched)
            return

    if st.session_state.quant_q is None:
        _serve(*_pick_next(sched, exclude={r["qid"] for r in done_today}))

    q = st.session_state.quant_q
    item = BY_ID[q["qid"]]
    inst = q["inst"]

    st.markdown(f"#### {item.title}  \n{'⭐' * item.level} · Green Book {item.gb} · {q['reason']}")
    st.markdown(inst["prompt"])

    if item.kind == "numeric":
        _numeric(q, item, inst)
    else:
        _review(q)

    _progress_table(sched)


def _numeric(q, item, inst) -> None:
    if q["result"] is None:
        with st.form("quant_form", clear_on_submit=False):
            raw = st.text_input("Your answer (fractions like 3/8 and percentages like 37.5% are fine):", key="quant_ans")
            submitted = st.form_submit_button("Submit")
        if submitted:
            val = parse_answer(raw)
            if val is None:
                st.warning("Couldn't read that as a number. Try 0.375, 3/8 or 37.5%.")
                return
            ok = is_correct(val, inst)
            _record(q["qid"], ok, time.time() - q["start"])
            q["result"] = {"ok": ok, "given": raw}
            st.rerun()
        if st.button("Skip / show solution (counts as a miss)", key="quant_skip"):
            _record(q["qid"], False, time.time() - q["start"])
            q["result"] = {"ok": False, "given": "(skipped)"}
            st.rerun()
        return

    r = q["result"]
    if r["ok"]:
        st.success(f"Correct. You answered {r['given']}. +{XP_CORRECT} XP")
    else:
        st.error(f"Not quite. You answered {r['given']}. This one will come back tomorrow with new numbers.")
    with st.expander("Solution", expanded=True):
        st.markdown(inst["solution"])
    _next_button()


def _review(q) -> None:
    st.info("This one doesn't work with swapped numbers. Solve it on paper from your copy of the book, then mark yourself honestly.")
    if q["result"] is None:
        a, b = st.columns(2)
        if a.button("✅ Got it", key="quant_got"):
            _record(q["qid"], True, time.time() - q["start"])
            q["result"] = {"ok": True}
            st.rerun()
        if b.button("❌ Missed / needed the solution", key="quant_miss"):
            _record(q["qid"], False, time.time() - q["start"])
            q["result"] = {"ok": False}
            st.rerun()
        return
    st.success("Logged.") if q["result"]["ok"] else st.warning("Logged. It'll come back tomorrow.")
    _next_button()


def _next_button() -> None:
    if st.button("Next question", key="quant_next"):
        st.session_state.quant_q = None
        st.session_state.pop("quant_ans", None)
        st.rerun()


def _day_streak(history: list[dict]) -> int:
    days = {r["date"] for r in history}
    d = today() if today() in days else today() - timedelta(days=1)
    n = 0
    while d in days:
        n += 1
        d -= timedelta(days=1)
    return n


def _progress_table(sched: dict) -> None:
    with st.expander("Question bank & schedule"):
        rows = []
        for it in BANK:
            s = sched.get(it.id)
            rows.append({
                "Question": it.title,
                "Level": "⭐" * it.level,
                "Green Book": it.gb,
                "Type": "new numbers" if it.kind == "numeric" else "book problem",
                "Attempts": s["attempts"] if s else 0,
                "In a row": s["box"] if s else 0,
                "Next due": s["due"].strftime("%d %b") if s else "new",
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
