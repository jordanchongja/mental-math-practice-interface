"""Answer log storage: Google Sheets when configured, local SQLite otherwise.

Streamlit Community Cloud wipes the app's local files whenever it restarts,
so a hosted copy needs somewhere durable to keep stats. With
`[gcp_service_account]` and `[gsheet]` in st.secrets, every answer goes to a
Google Sheet tab instead (laptop and hosted app then share the same history).
Without them -- a fresh local checkout -- it falls back to math_stats.db.

Sheet writes happen on a background thread: an API round trip takes ~0.5s,
and this is a speed drill, so the next question shouldn't wait for it.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

DB_NAME = "math_stats.db"
COLUMNS = ["timestamp", "tab_name", "is_correct", "time_sec", "xp_earned"]
_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _sheets_configured() -> bool:
    # st.secrets raises (not just returns falsy) when no secrets.toml exists.
    try:
        return "gcp_service_account" in st.secrets and "gsheet" in st.secrets
    except Exception:
        return False


@st.cache_resource
def _worksheet():
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=_SCOPES)
    sheet = gspread.authorize(creds).open_by_key(st.secrets["gsheet"]["spreadsheet_id"])
    name = st.secrets["gsheet"].get("worksheet", "mental_math_logs")
    try:
        return sheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=name, rows=1000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)
        return ws


@st.cache_resource
def _writer() -> ThreadPoolExecutor:
    # One worker keeps appends in answer order.
    return ThreadPoolExecutor(max_workers=1)


def init_db() -> None:
    if _sheets_configured():
        return
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS logs
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                     tab_name TEXT,
                     is_correct INTEGER,
                     time_sec REAL,
                     xp_earned INTEGER)''')
    conn.commit()
    conn.close()


def log_performance(tab_name, is_correct, time_sec, xp_earned) -> None:
    if _sheets_configured():
        # UTC, matching the SQLite CURRENT_TIMESTAMP rows migrated from before.
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        row = [stamp, tab_name, int(is_correct), round(float(time_sec), 3), int(xp_earned)]
        ws = _worksheet()
        _writer().submit(ws.append_row, row, value_input_option="RAW")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "INSERT INTO logs (tab_name, is_correct, time_sec, xp_earned) VALUES (?, ?, ?, ?)",
        (tab_name, int(is_correct), time_sec, xp_earned),
    )
    conn.commit()
    df = pd.read_sql_query("SELECT * FROM logs", conn)
    df.to_csv("performance_log.csv", index=False)
    conn.close()


def read_logs() -> pd.DataFrame:
    """Every logged answer, oldest first, with numeric columns typed."""
    if _sheets_configured():
        df = pd.DataFrame(_worksheet().get_all_records(), columns=COLUMNS)
    else:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT timestamp, tab_name, is_correct, time_sec, xp_earned FROM logs", conn)
        conn.close()
    for col in ("is_correct", "time_sec", "xp_earned"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["is_correct"] = df["is_correct"].astype(int)
    return df


# --- Poker hand reviews --------------------------------------------------
# Same backend choice as the answer log: a "poker_hands" tab in the Google
# Sheet when configured, otherwise a table in math_stats.db.

HAND_COLUMNS = ["timestamp", "game", "position", "hero_hand", "villain", "board", "line",
                "decision", "verdict", "tag", "notes"]


@st.cache_resource
def _hands_worksheet():
    import gspread
    ws_name = st.secrets["gsheet"].get("hands_worksheet", "poker_hands")
    sheet = _worksheet().spreadsheet
    try:
        return sheet.worksheet(ws_name)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=ws_name, rows=500, cols=len(HAND_COLUMNS))
        ws.append_row(HAND_COLUMNS)
        return ws


def _hands_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("CREATE TABLE IF NOT EXISTS poker_hands (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                 + ", ".join(f"{c} TEXT" for c in HAND_COLUMNS) + ")")
    return conn


def save_hand(row: dict) -> None:
    row = {c: str(row.get(c, "")) for c in HAND_COLUMNS}
    row["timestamp"] = row["timestamp"] or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if _sheets_configured():
        _writer().submit(_hands_worksheet().append_row, [row[c] for c in HAND_COLUMNS], value_input_option="RAW")
        return
    conn = _hands_db()
    conn.execute(f"INSERT INTO poker_hands ({', '.join(HAND_COLUMNS)}) VALUES ({', '.join('?' * len(HAND_COLUMNS))})",
                 [row[c] for c in HAND_COLUMNS])
    conn.commit()
    conn.close()


def read_hands() -> pd.DataFrame:
    if _sheets_configured():
        return pd.DataFrame(_hands_worksheet().get_all_records(), columns=HAND_COLUMNS)
    conn = _hands_db()
    df = pd.read_sql_query(f"SELECT {', '.join(HAND_COLUMNS)} FROM poker_hands", conn)
    conn.close()
    return df
