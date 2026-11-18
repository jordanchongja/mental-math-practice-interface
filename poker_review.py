"""Hand review log: write up hands you played, tag the mistake, see your patterns.

Most of a poker player's improvement comes from reviewing their own hands, the
way a trader reviews their trade journal. This keeps the write-ups in one
place and counts which mistakes keep coming back.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from storage import read_hands, save_hand

POSITIONS = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]
VERDICTS = ["❌ Mistake", "🤔 Unsure", "✅ Played well"]
TAGS = [
    "Preflop range", "C-bet too often", "C-bet too rarely", "Wrong bet size", "Over-folded",
    "Called too wide", "Missed value", "Bluffed bad spot", "Hero call", "Tilt / focus", "Other",
]


@st.cache_data(ttl=60)
def _hands() -> pd.DataFrame:
    return read_hands()


def hand_review() -> None:
    st.caption("Write up hands right after a session while they're fresh. Tag the mistake: the counts below "
               "show which leak to study next. Unsure hands are the best ones to check in the Flop Explorer.")

    with st.form("hand_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        game = c1.text_input("Game", placeholder="e.g. 1/2 live, NL10 online")
        position = c2.selectbox("Your position", POSITIONS, index=3)
        villain = c3.selectbox("Villain position", ["—"] + POSITIONS, index=6)
        c4, c5 = st.columns(2)
        hero_hand = c4.text_input("Your hand", placeholder="AhQd")
        board = c5.text_input("Board", placeholder="Ks 7d 2c | 5h | Jc")
        line = st.text_area("Action", placeholder="BTN open 2.5, BB call. Flop: BB check, I bet 2, BB raise to 7...", height=80)
        decision = st.text_input("The decision you're unsure about", placeholder="Call or fold to the check-raise?")
        c6, c7 = st.columns(2)
        verdict = c6.radio("Verdict", VERDICTS, horizontal=True)
        tag = c7.selectbox("Mistake tag", TAGS)
        notes = st.text_area("What you'd do next time / notes", height=70)
        if st.form_submit_button("Save hand"):
            if not (hero_hand or line):
                st.warning("Add at least your hand or the action.")
            else:
                save_hand({"game": game, "position": position, "hero_hand": hero_hand, "villain": villain,
                           "board": board, "line": line, "decision": decision, "verdict": verdict,
                           "tag": tag if verdict != VERDICTS[2] else "", "notes": notes})
                _hands.clear()
                st.success("Saved.")

    try:
        df = _hands()
    except Exception as e:
        st.warning(f"Couldn't load saved hands ({e}).")
        return
    if df.empty:
        st.info("No hands logged yet.")
        return

    mistakes = df[df["verdict"].astype(str).str.contains("Mistake|Unsure")]
    if not mistakes.empty:
        st.subheader("Your recurring leaks")
        counts = mistakes["tag"].replace("", "Untagged").value_counts()
        st.bar_chart(counts)

    st.subheader(f"Logged hands ({len(df)})")
    pick = st.selectbox("Show", ["All", *VERDICTS], key="hr_filter")
    view = df if pick == "All" else df[df["verdict"] == pick]
    st.dataframe(view.sort_values("timestamp", ascending=False), hide_index=True, width="stretch")
