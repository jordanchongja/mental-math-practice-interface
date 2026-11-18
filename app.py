import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import math
from datetime import datetime
import streamlit.components.v1 as components

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# --- Database & State Initialization ---
from storage import init_db, log_performance, read_logs

if 'initialized' not in st.session_state:
    init_db()
    st.session_state.initialized = True
    st.session_state.streak = 0
    st.session_state.total_xp = 0
    st.session_state.start_time = time.time()
    st.session_state.q_data = {}
    st.session_state.feedback = None # NEW: State to hold feedback between reloads

def reset_question(tab_key):
    st.session_state.q_data[tab_key] = None
    st.session_state.start_time = time.time()

def process_answer(tab_name, is_correct):
    elapsed = time.time() - st.session_state.start_time
    xp = 0
    if is_correct:
        st.session_state.streak += 1
        xp = 10 + (st.session_state.streak * 2) 
        st.session_state.total_xp += xp
        # NEW: Added "tab": tab_name to the dictionary
        st.session_state.feedback = {"tab": tab_name, "type": "success", "msg": f"Correct! Time: {elapsed:.2f}s | XP: {xp} | Streak: {st.session_state.streak}"}
    else:
        st.session_state.streak = 0
        st.session_state.feedback = {"tab": tab_name, "type": "error", "msg": f"Incorrect. Streak reset. Time: {elapsed:.2f}s"}
    
    log_performance(tab_name, is_correct, elapsed, xp)
    reset_question(tab_name)

# --- Trading Drill Helpers ---

def normalize_direction(text):
    """Maps free-typed text to 'strengthen' / 'weaken', or None if unrecognized."""
    t = text.strip().lower()
    if not t:
        return None
    if t.startswith("strength") or t in ("s", "stronger", "strong", "up", "widen", "widening"):
        return "strengthen"
    if t.startswith("weak") or t in ("w", "weaker", "down", "narrow", "narrowing"):
        return "weaken"
    return None

def normalize_curve_shape(text):
    """Maps free-typed text to 'contango' / 'backwardation', or None if unrecognized."""
    t = text.strip().lower()
    if not t:
        return None
    if t.startswith("cont") or t == "c":
        return "contango"
    if t.startswith("back") or t == "b":
        return "backwardation"
    return None

def normalize_moneyness(text):
    """Maps free-typed text to 'itm' / 'otm' / 'atm', or None if unrecognized."""
    t = text.strip().lower().replace("-", " ").replace("_", "")
    if not t:
        return None
    if t in ("itm",) or "in the money" in t or t.startswith("in"):
        return "itm"
    if t in ("otm",) or "out of the money" in t or t.startswith("out") or t.startswith("o"):
        return "otm"
    if t in ("atm",) or "at the money" in t or t.startswith("at"):
        return "atm"
    return None

def fmt_signed(x, decimals=0):
    return f"{x:+,.{decimals}f}"

def autofocus_active_input():
    """Forces the cursor back into the visible text input field.

    A single delayed focus() call races against Streamlit's own re-render
    (the form widget is often torn down and remounted after a submit, e.g.
    because of clear_on_submit), so a one-shot attempt frequently loses that
    race and leaves the cursor nowhere - the bug where you have to click back
    into the box after every Enter. Instead, retry on an interval until an
    input is actually focused (or we give up after a few seconds).
    """
    components.html(
        """
        <script>
        (function() {
            function focusVisibleInput() {
                const doc = window.parent.document;
                const inputs = doc.querySelectorAll('input[type="text"]');
                for (const input of inputs) {
                    // Only the input on the active tab has a layout box
                    if (input.offsetParent !== null) {
                        if (doc.activeElement !== input) {
                            input.focus();
                            const len = input.value.length;
                            input.setSelectionRange(len, len);
                        }
                        return true;
                    }
                }
                return false;
            }

            let attempts = 0;
            const maxAttempts = 40; // ~4 seconds at 100ms, covers slow reruns
            const timer = setInterval(() => {
                attempts += 1;
                if (focusVisibleInput() || attempts >= maxAttempts) {
                    clearInterval(timer);
                }
            }, 100);
        })();
        </script>
        """,
        height=0
    )

# --- UI Setup ---
st.set_page_config(page_title="Case Math Engine", layout="wide")

st.sidebar.header("Current Session")
xp_slot, streak_slot = st.sidebar.empty(), st.sidebar.empty()

def _sidebar_metrics():
    xp_slot.metric("Total XP", st.session_state.total_xp)
    streak_slot.metric("Current Streak", st.session_state.streak)

# Two major sections. Only the chosen one runs, so the poker drills don't wait
# on every math tab re-rendering (and vice versa).
SECTIONS = ["🧮 Math", "🃏 Poker"]
if hasattr(st, "segmented_control"):
    section = st.segmented_control("Section", SECTIONS, default=SECTIONS[0], key="section",
                                   label_visibility="collapsed") or SECTIONS[0]
else:
    section = st.radio("Section", SECTIONS, horizontal=True, key="section", label_visibility="collapsed")

if section == SECTIONS[1]:
    import poker_tab
    poker_tab.render()
    _sidebar_metrics()
    st.stop()

st.title("Mental RAM & Case Math Engine")
_sidebar_metrics()

tab1, tab2, tab3, tab4, tab5, tab6, tab_quant, tab7 = st.tabs([
    "Rapid Math", "Rote Memory", "Zero Gravity",
    "Fraction Simulator", "Market Sizing", "Trading Drills", "Quant Practice", "Dashboard"
])

# --- TAB 1: Rapid Arithmetic ---
with tab1:
    st.header("Rapid Arithmetic")
    
    # NEW: Display feedback from the previous submission, then clear it
    if st.session_state.feedback and st.session_state.feedback.get("tab") == "Rapid Math":
        if st.session_state.feedback["type"] == "success":
            st.success(st.session_state.feedback["msg"])
        else:
            st.error(st.session_state.feedback["msg"])
        st.session_state.feedback = None 
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: add_on = st.checkbox("Addition (+)", value=True)
    with col2: sub_on = st.checkbox("Subtraction (-)", value=True)
    with col3: mul_on = st.checkbox("Multiplication (*)", value=True)
    with col4: div_on = st.checkbox("Division (/)", value=True)
    
    active_ops = []
    if add_on: active_ops.append('+')
    if sub_on: active_ops.append('-')
    if mul_on: active_ops.append('*')
    if div_on: active_ops.append('/')
    
    if not active_ops:
        st.warning("Please select at least one operation to continue.")
    else:
        current_q = st.session_state.q_data.get("Rapid Math")
        
        if current_q is None or current_q[1] not in active_ops:
            op = random.choice(active_ops)
            if op == '/':
                ans = random.randint(2, 15)
                div = random.randint(2, 12)
                num1 = ans * div
                num2 = div
                correct_ans = ans
            elif op == '*':
                num1 = random.randint(12, 99)
                num2 = random.randint(2, 9)
                correct_ans = num1 * num2
            else:
                num1 = random.randint(100, 999)
                num2 = random.randint(10, 999)
                correct_ans = num1 + num2 if op == '+' else num1 - num2
                
            st.session_state.q_data["Rapid Math"] = (num1, op, num2, correct_ans)

        num1, op, num2, correct_ans = st.session_state.q_data["Rapid Math"]
        st.subheader(f"What is: {num1} {op} {num2} ?")
        
        with st.form("t1_form", clear_on_submit=True):
            user_input = st.text_input("Answer:")

            autofocus_active_input()
            
            if st.form_submit_button("Submit"):
                if user_input.strip() != "":
                    try:
                        user_ans = int(user_input)
                        process_answer("Rapid Math", user_ans == correct_ans)
                        st.rerun()
                    except ValueError:
                        st.error("Please enter a valid whole number.")
                else:
                    st.error("Please enter an answer before submitting.")

# --- TAB 2: Rote Memory Bank ---
with tab2:
    st.header("Rote Memory Bank")
    
    # 1. FIXED: Only display and clear feedback if it belongs to this specific tab
    if st.session_state.feedback and st.session_state.feedback.get("tab") == "Rote Memory":
        if st.session_state.feedback["type"] == "success":
            st.success(st.session_state.feedback["msg"])
        else:
            st.error(st.session_state.feedback["msg"])
        st.session_state.feedback = None 

    mixed_mode = st.checkbox("Mixed Mode (Randomly include reverse questions)")
    
    if st.session_state.q_data.get("Rote Memory") is None:
        mode = random.choice(["square", "fraction"])
        num = random.randint(2, 20)
        is_reverse = random.choice([True, False]) if mixed_mode else False
        
        if mode == "square":
            ans = num ** 2
            st.session_state.q_data["Rote Memory"] = ("square", num, ans, is_reverse)
        else:
            ans_raw = (1 / num) * 100
            ans = round(ans_raw, 3)
            # 2. NEW: If it's a clean percentage (e.g., 20.0), convert it to an integer
            if ans.is_integer():
                ans = int(ans)
            st.session_state.q_data["Rote Memory"] = ("fraction", num, ans, is_reverse)

    mode, num, ans, is_reverse = st.session_state.q_data["Rote Memory"]
    
    with st.form("t2_form", clear_on_submit=True):
        if mode == "square":
            if is_reverse:
                st.subheader(f"What is the square root of {ans}?")
                target = num
            else:
                st.subheader(f"What is {num} squared?")
                target = ans
        else:
            if is_reverse:
                st.subheader(f"Which fraction (1/x) is approximately {ans}%?")
                target = num
            else:
                # 3. NEW: Dynamically change the question text based on if it's an integer
                if isinstance(ans, int):
                    st.subheader(f"What is 1/{num} as a percentage?")
                else:
                    st.subheader(f"What is 1/{num} as a percentage (to 3 decimal places)?")
                target = ans
                
        user_input = st.text_input("Answer:")

        autofocus_active_input()
        
        if st.form_submit_button("Submit"):
            if user_input.strip() != "":
                try:
                    if mode == "square":
                        user_ans = int(user_input)
                        is_correct = (user_ans == target)
                    else:
                        if is_reverse:
                            user_ans = int(user_input)
                            is_correct = (user_ans == target)
                        else:
                            user_ans = float(user_input)
                            is_correct = math.isclose(user_ans, target, abs_tol=0.01)
                            
                    process_answer("Rote Memory", is_correct)
                    st.rerun()
                except ValueError:
                    st.error("Please enter a valid number.")
            else:
                st.error("Please enter an answer before submitting.")

# --- TAB 3: Zero Gravity Engine ---
with tab3:
    st.header("Zero Gravity Engine")
    
    # 1. Feedback Block
    if st.session_state.feedback and st.session_state.feedback.get("tab") == "Zero Gravity":
        if st.session_state.feedback["type"] == "success":
            st.success(st.session_state.feedback["msg"])
        else:
            st.error(st.session_state.feedback["msg"])
        st.session_state.feedback = None 

    # 2. State Key Fix & Dictionary Upgrade
    current_q = st.session_state.q_data.get("Zero Gravity")
    if current_q is None or not isinstance(current_q, dict):
        mags = {"": 0, "Thousand": 3, "Million": 6, "Billion": 9}
        
        # 30% chance to generate a 2-step chained question
        steps = random.choices([1, 2], weights=[0.7, 0.3])[0]
        
        if steps == 1:
            op = random.choice(["Add", "Subtract", "Multiply", "Divide"])
            
            if op == "Divide":
                mantissa_ans = random.choice([0.5, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 10.0, 20.0])
                n2_base = random.randint(2, 12)
                n2_mult = random.choice([1, 10, 100])
                n2 = n2_base * n2_mult
                n1 = mantissa_ans * n2
                
                mag1_name, mag1_val = random.choice(list(mags.items()))
                mag2_name, mag2_val = random.choice(list(mags.items()))
                if mag1_val < mag2_val: 
                    mag1_name, mag1_val, mag2_name, mag2_val = mag2_name, mag2_val, mag1_name, mag1_val
                
                val1 = n1 * (10**mag1_val)
                val2 = n2 * (10**mag2_val)
                correct_val = val1 / val2
                
            elif op == "Multiply":
                n1 = random.randint(2, 15) * random.choice([1, 10, 100])
                n2 = random.randint(2, 15) * random.choice([1, 10, 100])
                mag1_name, mag1_val = random.choice(list(mags.items()))
                mag2_name, mag2_val = random.choice(list(mags.items()))
                
                while mag1_val + mag2_val > 12:
                    mag1_name, mag1_val = random.choice(list(mags.items()))
                    mag2_name, mag2_val = random.choice(list(mags.items()))
                    
                val1 = n1 * (10**mag1_val)
                val2 = n2 * (10**mag2_val)
                correct_val = val1 * val2

            else: # Add or Subtract
                n1 = random.randint(2, 99) * random.choice([1, 10, 100])
                n2 = random.randint(2, 99) * random.choice([1, 10, 100])
                mag1_name, mag1_val = random.choice(list(mags.items()))
                mag2_name, mag2_val = random.choice(list(mags.items()))
                
                val1 = n1 * (10**mag1_val)
                val2 = n2 * (10**mag2_val)
                
                if op == "Subtract" and val2 > val1:
                    val1, val2 = val2, val1
                    n1, n2 = n2, n1
                    mag1_name, mag2_name = mag2_name, mag1_name
                    mag1_val, mag2_val = mag2_val, mag1_val
                    
                correct_val = val1 + val2 if op == "Add" else val1 - val2

            st.session_state.q_data["Zero Gravity"] = {
                "steps": 1,
                "op1": op,
                "n1": n1, "mag1_name": mag1_name, "mag1_val": mag1_val, "val1": val1,
                "n2": n2, "mag2_name": mag2_name, "mag2_val": mag2_val, "val2": val2,
                "correct_val": correct_val
            }
            
        else: # 2-Step Logic
            op1 = random.choice(["Multiply", "Divide"])
            op2 = "Divide" if op1 == "Multiply" else "Multiply"
            
            # Generate backwards to ensure clean math
            factor1 = random.randint(2, 12)
            factor2 = random.randint(2, 12)
            factor3 = random.randint(2, 12)
            
            if op1 == "Multiply": # A * B / C
                n3 = factor1
                n1 = n3 * factor2
                n2 = factor3
            else: # A / B * C
                n2 = factor1
                n1 = n2 * factor2
                n3 = factor3
                
            n1 *= random.choice([1, 10, 10])
            n2 *= random.choice([1, 10, 10])
            n3 *= random.choice([1, 10, 10])
            
            mag1_name, mag1_val = random.choice(list(mags.items()))
            mag2_name, mag2_val = random.choice(list(mags.items()))
            mag3_name, mag3_val = random.choice(list(mags.items()))
            
            # Prevent microscopic decimals by enforcing magnitude hierarchies
            if op1 == "Multiply":
                while mag1_val + mag2_val < mag3_val:
                    mag3_name, mag3_val = random.choice(list(mags.items()))
            else:
                while mag1_val + mag3_val < mag2_val:
                    mag2_name, mag2_val = random.choice(list(mags.items()))
                    
            val1 = n1 * (10**mag1_val)
            val2 = n2 * (10**mag2_val)
            val3 = n3 * (10**mag3_val)
            
            if op1 == "Multiply":
                correct_val = (val1 * val2) / val3
            else:
                correct_val = (val1 / val2) * val3
                
            st.session_state.q_data["Zero Gravity"] = {
                "steps": 2,
                "op1": op1, "op2": op2,
                "n1": n1, "mag1_name": mag1_name, "mag1_val": mag1_val, "val1": val1,
                "n2": n2, "mag2_name": mag2_name, "mag2_val": mag2_val, "val2": val2,
                "n3": n3, "mag3_name": mag3_name, "mag3_val": mag3_val, "val3": val3,
                "correct_val": correct_val
            }

    # Unpack the current question
    q = st.session_state.q_data["Zero Gravity"]
    
    op_text_map = {"Add": "plus", "Subtract": "minus", "Multiply": "multiplied by", "Divide": "divided by"}
    
    # Format the terms cleanly (removes trailing spaces if magnitude is blank)
    term1 = f"{q['n1']:g} {q['mag1_name']}".strip()
    term2 = f"{q['n2']:g} {q['mag2_name']}".strip()
    
    if q["steps"] == 1:
        op_str = op_text_map[q["op1"]]
        st.subheader(f"{term1} {op_str} {term2}")
    else:
        term3 = f"{q['n3']:g} {q['mag3_name']}".strip()
        op1_str = op_text_map[q["op1"]]
        op2_str = op_text_map[q["op2"]]
        st.subheader(f"{term1} {op1_str} {term2} {op2_str} {term3}")
    
    with st.form("t3_form", clear_on_submit=True):
        user_input = st.text_input("Raw Number Answer (e.g., 500000):")

        autofocus_active_input()
        
        if st.form_submit_button("Submit"):
            if user_input.strip() != "":
                try:
                    user_ans = float(user_input)
                    is_correct = math.isclose(user_ans, q["correct_val"], rel_tol=1e-5)
                    process_answer("Zero Gravity", is_correct)
                    
                    # Custom breakdown based on 1-step vs 2-step
                    if q["steps"] == 1:
                        if q["op1"] == "Divide":
                            breakdown = f"\n\n**Breakdown:** Mantissa: {q['n1']:g} / {q['n2']:g} = {q['n1']/q['n2']:g}. Zeros: 10^{q['mag1_val']} / 10^{q['mag2_val']} = 10^{q['mag1_val']-q['mag2_val']}."
                        elif q["op1"] in ["Add", "Subtract"]:
                            symbol = "+" if q["op1"] == "Add" else "-"
                            breakdown = f"\n\n**Expanded:** {q['val1']:,.0f} {symbol} {q['val2']:,.0f} = {q['correct_val']:,.0f}"
                        else:
                            breakdown = f"\n\n**Exact Answer:** {q['correct_val']:,.0f}"
                    else:
                        symbol1 = "*" if q["op1"] == "Multiply" else "/"
                        symbol2 = "*" if q["op2"] == "Multiply" else "/"
                        breakdown = f"\n\n**Expanded:** ({q['val1']:,.0f} {symbol1} {q['val2']:,.0f}) {symbol2} {q['val3']:,.0f} = {q['correct_val']:,.0f}"
                        
                    st.session_state.feedback["msg"] += breakdown
                    
                    st.rerun()
                except ValueError:
                    st.error("Please enter a valid number.")
            else:
                st.error("Please enter an answer before submitting.")

# --- TAB 4: Fraction & Bounding Simulator ---
with tab4:
    st.header("Fraction & Bounding Simulator")
    
    # 1. Feedback Block
    if st.session_state.feedback and st.session_state.feedback.get("tab") == "Fraction Bounding":
        if st.session_state.feedback["type"] == "success":
            st.success(st.session_state.feedback["msg"])
        else:
            st.error(st.session_state.feedback["msg"])
        st.session_state.feedback = None 

    # 2. State Key Fix & Dictionary Upgrade
    current_q = st.session_state.q_data.get("Fraction Bounding")
    if current_q is None or not isinstance(current_q, dict):
        q_type = random.choice(["fraction", "pct_of_base"])
        q_data = {"type": q_type}
        
        if q_type == "fraction":
            q_data["num"] = random.randint(15, 95)
            q_data["den"] = random.randint(110, 850)
            q_data["actual_ans"] = (q_data["num"] / q_data["den"]) * 100
        else:
            q_data["pct"] = random.randint(15, 95)
            q_data["base"] = random.randint(1100, 9900)
            q_data["actual_ans"] = (q_data["pct"] / 100.0) * q_data["base"]
            
        st.session_state.q_data["Fraction Bounding"] = q_data

    # Unpack the current question
    q = st.session_state.q_data["Fraction Bounding"]
    
    # Set UI based on question type
    if q["type"] == "fraction":
        st.subheader(f"Estimate: {q['num']} / {q['den']} as a percentage")
        input_label = "Your Estimate (%):"
    else:
        st.subheader(f"Estimate: {q['pct']}% of {q['base']}")
        input_label = "Your Estimate (Absolute Value):"
    
    with st.form("t4_form", clear_on_submit=True):
        user_input = st.text_input(input_label)

        autofocus_active_input()
        
        if st.form_submit_button("Submit"):
            if user_input.strip() != "":
                try:
                    user_guess = float(user_input)
                    
                    if q["type"] == "fraction":
                        variance = abs(user_guess - q["actual_ans"])
                        is_correct = variance <= 1.0 # Pass if within 1% absolute
                        actual_text = f"{q['actual_ans']:.2f}%"
                        var_text = f"{variance:.2f}%"
                        base_val = q["den"]
                    else:
                        variance = abs(user_guess - q["actual_ans"])
                        allowed_variance = q["base"] * 0.01 # Pass if within 1% of the base
                        is_correct = variance <= allowed_variance
                        actual_text = f"{q['actual_ans']:.1f}"
                        var_text = f"{variance:.1f} (Allowed: ±{allowed_variance:.1f})"
                        base_val = q["base"]

                    process_answer("Fraction Bounding", is_correct)
                    
                    # Append the bounding blocks to the feedback message
                    building_blocks = (
                        f"\n\n**Actual:** {actual_text} (Variance: {var_text})\n"
                        f"**Building Blocks of {base_val}:**\n"
                        f"- 10% = {base_val * 0.1:.1f}\n"
                        f"- 5% = {base_val * 0.05:.1f}\n"
                        f"- 1% = {base_val * 0.01:.1f}"
                    )
                    st.session_state.feedback["msg"] += building_blocks
                    
                    st.rerun()
                except ValueError:
                    st.error("Please enter a valid number.")
            else:
                st.error("Please enter an answer before submitting.")

# --- TAB 5: Market Sizing Quick-Fire ---
with tab5:
    st.header("Case Interview Scenarios")
    
    # 1. Feedback Block
    if st.session_state.feedback and st.session_state.feedback.get("tab") == "Market Sizing":
        if st.session_state.feedback["type"] == "success":
            st.success(st.session_state.feedback["msg"])
        else:
            st.error(st.session_state.feedback["msg"])
        st.session_state.feedback = None 

    # 2. BUG FIX: Unified the key back to "Market Sizing" and added a safeguard to clear old tuple data
    current_q = st.session_state.q_data.get("Market Sizing")
    if current_q is None or not isinstance(current_q, dict):
        scenarios = ["TAM", "Market_Share", "Profitability", "Breakeven", "Growth"]
        q_type = random.choice(scenarios)
        q_data = {"type": q_type}
        
        if q_type in ["TAM", "Market_Share"]:
            q_data["pop"] = random.choice([10, 50, 100, 300]) # Millions
            q_data["seg"] = random.choice([10, 20, 25, 50]) # Percentage
            q_data["freq"] = random.randint(2, 12)
            q_data["price"] = random.choice([5, 10, 15, 20, 50, 100])
            total_market_m = q_data["pop"] * (q_data["seg"] / 100.0) * q_data["freq"] * q_data["price"]
            
            if q_type == "Market_Share":
                q_data["target_share"] = random.choice([1, 2, 5, 10, 15, 20, 25])
                q_data["target_rev"] = total_market_m * (q_data["target_share"] / 100.0)
                q_data["answer"] = q_data["target_share"]
                q_data["total_market_m"] = total_market_m
            else:
                q_data["answer"] = total_market_m
                
        elif q_type == "Profitability":
            q_data["vol_m"] = random.choice([1, 2, 5, 10]) # Millions
            q_data["price"] = random.choice([20, 50, 100, 200])
            # Ensure clean unit margins
            margin_pct = random.choice([0.2, 0.4, 0.5])
            q_data["vc"] = int(q_data["price"] * (1 - margin_pct))
            unit_margin = q_data["price"] - q_data["vc"]
            gross_profit_m = q_data["vol_m"] * unit_margin
            # Ensure fixed costs leave a positive net profit
            q_data["fc_m"] = int(gross_profit_m * random.choice([0.2, 0.4, 0.5])) 
            q_data["answer"] = gross_profit_m - q_data["fc_m"] # Net profit in Millions
            
        elif q_type == "Breakeven":
            # Generate backwards for clean math
            unit_margin = random.choice([5, 10, 20, 25, 50])
            q_data["price"] = unit_margin * random.choice([2, 3, 4, 5])
            q_data["vc"] = q_data["price"] - unit_margin
            q_data["fc_m"] = random.choice([5, 10, 20, 50]) # Millions
            # Answer is exact units, not millions
            q_data["answer"] = (q_data["fc_m"] * 1000000) / unit_margin
            
        elif q_type == "Growth":
            q_data["base_rev"] = random.choice([10, 50, 100, 200]) # Millions
            q_data["growth_pct"] = random.choice([10, 20, 25, 50])
            # Calculate Year 2 (compound 2 years)
            multiplier = 1 + (q_data["growth_pct"] / 100.0)
            q_data["answer"] = q_data["base_rev"] * (multiplier ** 2)

        st.session_state.q_data["Market Sizing"] = q_data

    # Unpack the current question
    q = st.session_state.q_data["Market Sizing"]
    q_type = q["type"]
    
    # Render UI Based on Scenario
    if q_type == "TAM":
        st.subheader("Calculate the Total Addressable Market (in Millions):")
        st.write(f"- **Population:** {q['pop']}M")
        st.write(f"- **Target Segment:** {q['seg']}%")
        st.write(f"- **Frequency:** {q['freq']}x / year")
        st.write(f"- **Price:** ${q['price']}")
        input_label = "Total Market ($ Millions):"
        
    elif q_type == "Market_Share":
        st.subheader(f"To capture **${q['target_rev']:,.1f}M** in revenue, what market share (%) do you need?")
        st.write(f"- **Population:** {q['pop']}M")
        st.write(f"- **Target Segment:** {q['seg']}%")
        st.write(f"- **Frequency:** {q['freq']}x / year")
        st.write(f"- **Price:** ${q['price']}")
        input_label = "Required Market Share (%):"
        
    elif q_type == "Profitability":
        st.subheader("Calculate the Net Profit (in Millions):")
        st.write(f"- **Annual Volume:** {q['vol_m']}M units")
        st.write(f"- **Price per Unit:** ${q['price']}")
        st.write(f"- **Variable Cost per Unit:** ${q['vc']}")
        st.write(f"- **Fixed Costs:** ${q['fc_m']}M")
        input_label = "Net Profit ($ Millions):"
        
    elif q_type == "Breakeven":
        st.subheader("Calculate the Breakeven Volume (Exact Units):")
        st.write(f"- **Fixed Costs:** ${q['fc_m']}M")
        st.write(f"- **Price per Unit:** ${q['price']}")
        st.write(f"- **Variable Cost per Unit:** ${q['vc']}")
        input_label = "Breakeven Units (e.g. 500000):"
        
    elif q_type == "Growth":
        st.subheader("Calculate Year 2 Revenue (in Millions):")
        st.write(f"- **Year 0 Revenue:** ${q['base_rev']}M")
        st.write(f"- **Year-over-Year Growth:** {q['growth_pct']}%")
        st.write(f"- *(Calculate the compounded revenue at the end of Year 2)*")
        input_label = "Year 2 Revenue ($ Millions):"

    with st.form("t5_form", clear_on_submit=True):
        user_input = st.text_input(input_label)

        autofocus_active_input()
        
        if st.form_submit_button("Submit"):
            if user_input.strip() != "":
                try:
                    user_ans = float(user_input)
                    is_correct = math.isclose(user_ans, q["answer"], abs_tol=0.1)
                    process_answer("Market Sizing", is_correct) 
                    
                    # Custom Breakdown Generation
                    if q_type == "TAM":
                        breakdown = f"\n\n**Exact Answer:** ${q['answer']:,.1f}M"
                    elif q_type == "Market_Share":
                        breakdown = f"\n\n**Breakdown:** TAM is ${q['total_market_m']:,.1f}M. ${q['target_rev']:,.1f}M / ${q['total_market_m']:,.1f}M = {q['answer']}%."
                    elif q_type == "Profitability":
                        unit_margin = q['price'] - q['vc']
                        breakdown = f"\n\n**Breakdown:** Unit Margin = ${unit_margin}. Gross Profit = ${unit_margin} * {q['vol_m']}M = ${unit_margin * q['vol_m']}M. Net = ${q['answer']}M."
                    elif q_type == "Breakeven":
                        unit_margin = q['price'] - q['vc']
                        breakdown = f"\n\n**Breakdown:** Unit Margin = ${unit_margin}. BE = ${q['fc_m']}M / ${unit_margin} = {q['answer']:,.0f} units."
                    elif q_type == "Growth":
                        yr1 = q['base_rev'] * (1 + (q['growth_pct'] / 100.0))
                        breakdown = f"\n\n**Breakdown:** Year 1 = ${yr1:,.1f}M. Year 2 = ${q['answer']:,.1f}M."
                        
                    st.session_state.feedback["msg"] += breakdown
                    st.rerun()
                    
                except ValueError:
                    st.error("Please enter a valid number.")
            else:
                st.error("Please enter an answer before submitting.")

# --- TAB 6: Trading Intuition Drills ---
with tab6:
    st.header("Trading Intuition Drills")
    st.caption("Speed drills for basis, futures curves, and options — sized for dairy/milk futures ranges.")

    module = st.radio(
        "Choose a module:",
        ["Basis & Futures Curve", "Milk Price Arithmetic", "Options Breakeven", "Payoff Diagram Explorer"],
        horizontal=True,
        key="trading_module_choice"
    )

    st.divider()

    # ===================== MODULE 1: BASIS & FUTURES CURVE =====================
    if module == "Basis & Futures Curve":
        drill = st.radio(
            "Drill type:",
            ["Basis Calculation", "Basis Direction (Strengthen/Weaken)", "Curve Shape (Contango/Backwardation)"],
            key="basis_drill_choice"
        )

        if drill == "Basis Calculation":
            tab_name = "Basis Calc"
            if st.session_state.feedback and st.session_state.feedback.get("tab") == tab_name:
                if st.session_state.feedback["type"] == "success":
                    st.success(st.session_state.feedback["msg"])
                else:
                    st.error(st.session_state.feedback["msg"])
                st.session_state.feedback = None

            if st.session_state.q_data.get(tab_name) is None:
                spot = random.randint(30, 48) * 100
                basis = random.choice([x for x in range(-300, 301, 10) if x != 0])
                futures = spot - basis
                st.session_state.q_data[tab_name] = {"spot": spot, "futures": futures, "basis": basis}

            q = st.session_state.q_data[tab_name]
            st.subheader(f"Spot: ${q['spot']:,}  |  Futures: ${q['futures']:,}")
            st.write("What is the basis? (Spot − Futures, include the sign)")

            with st.form("basis_calc_form", clear_on_submit=True):
                user_input = st.text_input("Basis:", key="basis_calc_input")
                autofocus_active_input()
                if st.form_submit_button("Submit", key="basis_calc_submit"):
                    if user_input.strip() != "":
                        try:
                            user_ans = float(user_input)
                            is_correct = math.isclose(user_ans, q["basis"], abs_tol=0.5)
                            process_answer(tab_name, is_correct)
                            shape = "Contango" if q["futures"] > q["spot"] else "Backwardation"
                            breakdown = (
                                f"\n\n**Basis = Spot − Futures = {q['spot']:,} − {q['futures']:,} = {fmt_signed(q['basis'])}**\n"
                                f"Futures {'>' if q['futures'] > q['spot'] else '<'} Spot → market is in **{shape}**."
                            )
                            st.session_state.feedback["msg"] += breakdown
                            st.rerun()
                        except ValueError:
                            st.error("Please enter a valid number.")
                    else:
                        st.error("Please enter an answer before submitting.")

        elif drill == "Basis Direction (Strengthen/Weaken)":
            tab_name = "Basis Direction"
            if st.session_state.feedback and st.session_state.feedback.get("tab") == tab_name:
                if st.session_state.feedback["type"] == "success":
                    st.success(st.session_state.feedback["msg"])
                else:
                    st.error(st.session_state.feedback["msg"])
                st.session_state.feedback = None

            if st.session_state.q_data.get(tab_name) is None:
                basis_old = random.choice([x for x in range(-300, 301, 10) if x != 0])
                delta = random.choice([x for x in range(-150, 151, 10) if x != 0])
                basis_new = basis_old + delta
                direction = "strengthen" if basis_new > basis_old else "weaken"
                st.session_state.q_data[tab_name] = {"basis_old": basis_old, "basis_new": basis_new, "direction": direction}

            q = st.session_state.q_data[tab_name]
            st.subheader(f"Basis 3 months ago: {fmt_signed(q['basis_old'])}   →   Basis today: {fmt_signed(q['basis_new'])}")
            st.write("Did the basis **strengthen** or **weaken**?")

            with st.form("basis_dir_form", clear_on_submit=True):
                user_input = st.text_input("Strengthen or Weaken:", key="basis_dir_input")
                autofocus_active_input()
                if st.form_submit_button("Submit", key="basis_dir_submit"):
                    if user_input.strip() == "":
                        st.error("Please enter an answer before submitting.")
                    else:
                        guess = normalize_direction(user_input)
                        if guess is None:
                            st.error("Please type 'strengthen' or 'weaken'.")
                        else:
                            is_correct = (guess == q["direction"])
                            process_answer(tab_name, is_correct)
                            beneficiary = "sellers / short hedgers (long the basis)" if q["direction"] == "strengthen" else "buyers / long hedgers (short the basis)"
                            breakdown = (
                                f"\n\n**Basis moved from {fmt_signed(q['basis_old'])} to {fmt_signed(q['basis_new'])} → it {q['direction'].upper()}ED.**\n"
                                f"This benefits: {beneficiary}."
                            )
                            st.session_state.feedback["msg"] += breakdown
                            st.rerun()

        else:  # Curve Shape
            tab_name = "Curve Shape"
            if st.session_state.feedback and st.session_state.feedback.get("tab") == tab_name:
                if st.session_state.feedback["type"] == "success":
                    st.success(st.session_state.feedback["msg"])
                else:
                    st.error(st.session_state.feedback["msg"])
                st.session_state.feedback = None

            if st.session_state.q_data.get(tab_name) is None:
                shape = random.choice(["contango", "backwardation"])
                start = random.randint(3000, 4500)
                prices = [start]
                for _ in range(3):
                    step = random.randint(10, 40)
                    if shape == "backwardation":
                        step = -step
                    prices.append(prices[-1] + step)
                st.session_state.q_data[tab_name] = {"shape": shape, "prices": prices}

            q = st.session_state.q_data[tab_name]
            months = ["Front Month", "+1 Month", "+2 Month", "+3 Month"]
            curve_df = pd.DataFrame({"Price": q["prices"]}, index=months)
            st.subheader("Futures Curve")
            st.line_chart(curve_df)
            cols = st.columns(4)
            for c, m, p in zip(cols, months, q["prices"]):
                c.metric(m, f"${p:,}")
            st.write("Is this curve in **contango** or **backwardation**?")

            with st.form("curve_shape_form", clear_on_submit=True):
                user_input = st.text_input("Contango or Backwardation:", key="curve_shape_input")
                autofocus_active_input()
                if st.form_submit_button("Submit", key="curve_shape_submit"):
                    if user_input.strip() == "":
                        st.error("Please enter an answer before submitting.")
                    else:
                        guess = normalize_curve_shape(user_input)
                        if guess is None:
                            st.error("Please type 'contango' or 'backwardation'.")
                        else:
                            is_correct = (guess == q["shape"])
                            process_answer(tab_name, is_correct)
                            breakdown = (
                                f"\n\n**Prices {'rise' if q['shape']=='contango' else 'fall'} across the curve → {q['shape'].capitalize()}.**\n"
                                f"Contango = futures > spot / rising with maturity (normal carry market). "
                                f"Backwardation = futures < spot / falling with maturity (tight/scarce supply)."
                            )
                            st.session_state.feedback["msg"] += breakdown
                            st.rerun()

    # ===================== MODULE 2: MILK PRICE ARITHMETIC =====================
    elif module == "Milk Price Arithmetic":
        tab_name = "Milk Arithmetic"
        if st.session_state.feedback and st.session_state.feedback.get("tab") == tab_name:
            if st.session_state.feedback["type"] == "success":
                st.success(st.session_state.feedback["msg"])
            else:
                st.error(st.session_state.feedback["msg"])
            st.session_state.feedback = None

        current_q = st.session_state.q_data.get(tab_name)
        if current_q is None or not isinstance(current_q, dict):
            q_type = random.choice(["calc_basis", "calc_effective_price", "basis_direction", "hedge_pnl"])
            q_data = {"type": q_type}

            if q_type == "calc_basis":
                q_data["spot"] = random.randint(30, 48) * 100
                q_data["basis"] = random.choice([x for x in range(-300, 301, 10) if x != 0])
                q_data["futures"] = q_data["spot"] - q_data["basis"]
                q_data["answer"] = q_data["basis"]

            elif q_type == "calc_effective_price":
                q_data["futures_sold"] = random.randint(30, 48) * 100
                q_data["basis"] = random.choice([x for x in range(-300, 301, 10) if x != 0])
                q_data["answer"] = q_data["futures_sold"] + q_data["basis"]

            elif q_type == "basis_direction":
                q_data["basis_old"] = random.choice([x for x in range(-300, 301, 10) if x != 0])
                delta = random.choice([x for x in range(-150, 151, 10) if x != 0])
                q_data["basis_new"] = q_data["basis_old"] + delta
                q_data["direction"] = "strengthen" if q_data["basis_new"] > q_data["basis_old"] else "weaken"

            else:  # hedge_pnl
                q_data["volume"] = random.choice([100, 200, 250, 500, 1000, 1500, 2000])
                q_data["entry_price"] = random.randint(38, 46) * 100
                move = random.choice([x for x in range(-500, 501, 25) if x != 0])
                q_data["settlement"] = q_data["entry_price"] + move
                q_data["answer"] = q_data["entry_price"] - q_data["settlement"]

            st.session_state.q_data[tab_name] = q_data

        q = st.session_state.q_data[tab_name]

        if q["type"] == "calc_basis":
            st.subheader(f"Spot is ${q['spot']:,}. You sold futures at ${q['futures']:,}.")
            input_label = "What is your basis?"
        elif q["type"] == "calc_effective_price":
            st.subheader(f"You sold futures at ${q['futures_sold']:,}. Basis is {fmt_signed(q['basis'])}.")
            input_label = "What is your effective price?"
        elif q["type"] == "basis_direction":
            st.subheader(f"Basis was {fmt_signed(q['basis_old'])}. Now it's {fmt_signed(q['basis_new'])}.")
            input_label = "Did basis strengthen or weaken?"
        else:
            st.subheader(f"You hedge {q['volume']:,} MT by selling futures at ${q['entry_price']:,}. At settlement, spot/futures is ${q['settlement']:,}.")
            input_label = "Futures P&L per MT? (use a negative sign for a loss)"

        with st.form("milk_arith_form", clear_on_submit=True):
            user_input = st.text_input(input_label, key="milk_arith_input")
            autofocus_active_input()
            if st.form_submit_button("Submit", key="milk_arith_submit"):
                if user_input.strip() == "":
                    st.error("Please enter an answer before submitting.")
                elif q["type"] == "basis_direction":
                    guess = normalize_direction(user_input)
                    if guess is None:
                        st.error("Please type 'strengthen' or 'weaken'.")
                    else:
                        is_correct = (guess == q["direction"])
                        process_answer(tab_name, is_correct)
                        beneficiary = "sellers / short hedgers" if q["direction"] == "strengthen" else "buyers / long hedgers"
                        st.session_state.feedback["msg"] += f"\n\n**Basis {q['direction']}ed. This benefits: {beneficiary}.**"
                        st.rerun()
                else:
                    try:
                        user_ans = float(user_input)
                        is_correct = math.isclose(user_ans, q["answer"], abs_tol=0.5)
                        process_answer(tab_name, is_correct)

                        if q["type"] == "calc_basis":
                            breakdown = f"\n\n**Basis = Spot − Futures = {q['spot']:,} − {q['futures']:,} = {fmt_signed(q['answer'])}**"
                        elif q["type"] == "calc_effective_price":
                            breakdown = f"\n\n**Effective Price = Futures + Basis = {q['futures_sold']:,} + {fmt_signed(q['basis'])} = {q['answer']:,.0f}**"
                        else:
                            total_pnl = q["answer"] * q["volume"]
                            net_effective = q["settlement"] + q["answer"]
                            breakdown = (
                                f"\n\n**Futures P&L/MT = Entry − Settlement = {q['entry_price']:,} − {q['settlement']:,} = {fmt_signed(q['answer'])}**\n"
                                f"Total P&L = {fmt_signed(q['answer'])} × {q['volume']:,} MT = ${total_pnl:+,.0f}\n"
                                f"Net Effective Price = Settlement + P&L/MT = {q['settlement']:,} + ({fmt_signed(q['answer'])}) = ${net_effective:,.0f} "
                                f"— the hedge locks in your entry price regardless of where spot ends up."
                            )
                        st.session_state.feedback["msg"] += breakdown
                        st.rerun()
                    except ValueError:
                        st.error("Please enter a valid number.")

    # ===================== MODULE 3: OPTIONS BREAKEVEN =====================
    elif module == "Options Breakeven":
        tab_name = "Options Breakeven"
        if st.session_state.feedback and st.session_state.feedback.get("tab") == tab_name:
            if st.session_state.feedback["type"] == "success":
                st.success(st.session_state.feedback["msg"])
            else:
                st.error(st.session_state.feedback["msg"])
            st.session_state.feedback = None

        current_q = st.session_state.q_data.get(tab_name)
        if current_q is None or not isinstance(current_q, dict):
            q_type = random.choice(["call_breakeven", "put_breakeven", "moneyness", "intrinsic_value", "net_effective_price"])
            q_data = {"type": q_type}

            if q_type in ("call_breakeven", "put_breakeven"):
                q_data["strike"] = random.randint(35, 48) * 100
                q_data["premium"] = random.randint(50, 200)
                if q_type == "call_breakeven":
                    q_data["answer"] = q_data["strike"] + q_data["premium"]
                else:
                    q_data["answer"] = q_data["strike"] - q_data["premium"]

            elif q_type in ("moneyness", "intrinsic_value"):
                q_data["opt_type"] = random.choice(["call", "put"])
                q_data["strike"] = random.randint(35, 48) * 100
                q_data["spot_exp"] = q_data["strike"] + random.choice(list(range(-300, 301, 10)))
                if q_data["opt_type"] == "call":
                    q_data["intrinsic"] = max(q_data["spot_exp"] - q_data["strike"], 0)
                else:
                    q_data["intrinsic"] = max(q_data["strike"] - q_data["spot_exp"], 0)
                if q_data["spot_exp"] == q_data["strike"]:
                    q_data["moneyness"] = "atm"
                elif q_data["intrinsic"] > 0:
                    q_data["moneyness"] = "itm"
                else:
                    q_data["moneyness"] = "otm"

            else:  # net_effective_price (protective put)
                q_data["strike"] = random.randint(35, 48) * 100
                q_data["premium"] = random.randint(50, 200)
                q_data["spot_exp"] = random.randint(30, 50) * 100
                q_data["answer"] = max(q_data["strike"], q_data["spot_exp"]) - q_data["premium"]

            st.session_state.q_data[tab_name] = q_data

        q = st.session_state.q_data[tab_name]

        if q["type"] == "call_breakeven":
            st.subheader(f"Call Option — Strike: ${q['strike']:,}, Premium: ${q['premium']:,}")
            input_label = "Breakeven price at expiry?"
        elif q["type"] == "put_breakeven":
            st.subheader(f"Put Option — Strike: ${q['strike']:,}, Premium: ${q['premium']:,}")
            input_label = "Breakeven price at expiry?"
        elif q["type"] == "moneyness":
            st.subheader(f"{q['strike']:,} {q['opt_type'].upper()} option. At expiry, spot is ${q['spot_exp']:,}.")
            input_label = "ITM, OTM, or ATM?"
        elif q["type"] == "intrinsic_value":
            st.subheader(f"{q['strike']:,} {q['opt_type'].upper()} option. At expiry, spot is ${q['spot_exp']:,}.")
            input_label = "What is the intrinsic value?"
        else:
            st.subheader(f"You bought a {q['strike']:,} put for ${q['premium']:,} to protect a milk sale. At expiry, spot is ${q['spot_exp']:,}.")
            input_label = "What is your net effective price?"

        with st.form("options_be_form", clear_on_submit=True):
            user_input = st.text_input(input_label, key="options_be_input")
            autofocus_active_input()
            if st.form_submit_button("Submit", key="options_be_submit"):
                if user_input.strip() == "":
                    st.error("Please enter an answer before submitting.")
                elif q["type"] == "moneyness":
                    guess = normalize_moneyness(user_input)
                    if guess is None:
                        st.error("Please type ITM, OTM, or ATM.")
                    else:
                        is_correct = (guess == q["moneyness"])
                        process_answer(tab_name, is_correct)
                        st.session_state.feedback["msg"] += f"\n\n**Intrinsic Value = ${q['intrinsic']:,} → {q['moneyness'].upper()}.**"
                        st.rerun()
                else:
                    try:
                        user_ans = float(user_input)
                        target = q["intrinsic"] if q["type"] == "intrinsic_value" else q["answer"]
                        is_correct = math.isclose(user_ans, target, abs_tol=0.5)
                        process_answer(tab_name, is_correct)

                        if q["type"] == "call_breakeven":
                            breakdown = f"\n\n**Breakeven = Strike + Premium = {q['strike']:,} + {q['premium']:,} = {q['answer']:,}**"
                        elif q["type"] == "put_breakeven":
                            breakdown = f"\n\n**Breakeven = Strike − Premium = {q['strike']:,} − {q['premium']:,} = {q['answer']:,}**"
                        elif q["type"] == "intrinsic_value":
                            breakdown = f"\n\n**Intrinsic Value = ${q['intrinsic']:,} → {q['moneyness'].upper()}.**"
                        else:
                            side = "strike (exercised the put)" if q['spot_exp'] < q['strike'] else "spot (let the put expire)"
                            breakdown = (
                                f"\n\n**Net Effective Price = max(Strike, Spot) − Premium = "
                                f"max({q['strike']:,}, {q['spot_exp']:,}) − {q['premium']:,} = {q['answer']:,}**\n"
                                f"You effectively sold at {side}."
                            )
                        st.session_state.feedback["msg"] += breakdown
                        st.rerun()
                    except ValueError:
                        st.error("Please enter a valid number.")

    # ===================== PAYOFF DIAGRAM EXPLORER (not scored) =====================
    else:
        st.subheader("Options Payoff Explorer")
        st.caption("Not scored — drag the slider to build intuition for how P&L moves with spot.")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            opt_type = st.selectbox("Option Type", ["Call", "Put"], key="pd_opt_type")
        with c2:
            position = st.selectbox("Position", ["Long", "Short"], key="pd_position")
        with c3:
            strike = st.number_input("Strike ($)", value=4200, step=50, key="pd_strike")
        with c4:
            premium = st.number_input("Premium ($/MT)", value=120, step=10, key="pd_premium")

        spot_lo = int(strike - 600)
        spot_hi = int(strike + 600)
        spot = st.slider("Spot Price at Expiry ($)", min_value=spot_lo, max_value=spot_hi, value=int(strike), step=10, key="pd_spot")

        spots = np.linspace(spot_lo, spot_hi, 200)
        if opt_type == "Call":
            intrinsic_curve = np.maximum(spots - strike, 0)
            current_intrinsic = max(spot - strike, 0)
        else:
            intrinsic_curve = np.maximum(strike - spots, 0)
            current_intrinsic = max(strike - spot, 0)

        if position == "Long":
            payoff_curve = intrinsic_curve - premium
            current_payoff = current_intrinsic - premium
        else:
            payoff_curve = premium - intrinsic_curve
            current_payoff = premium - current_intrinsic

        breakeven = strike + premium if opt_type == "Call" else strike - premium

        if MATPLOTLIB_AVAILABLE:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(spots, payoff_curve, color="#1f77b4", linewidth=2)
            ax.axhline(0, color="gray", linewidth=1, linestyle="--")
            ax.axvline(strike, color="orange", linewidth=1, linestyle=":", label=f"Strike ${strike:,.0f}")
            ax.fill_between(spots, payoff_curve, 0, where=(payoff_curve >= 0), color="green", alpha=0.15)
            ax.fill_between(spots, payoff_curve, 0, where=(payoff_curve < 0), color="red", alpha=0.15)
            ax.scatter([spot], [current_payoff], color="black", zorder=5)
            ax.annotate(f"P&L: {current_payoff:+,.0f}/MT", (spot, current_payoff),
                        textcoords="offset points", xytext=(10, 10))
            ax.set_xlabel("Spot Price at Expiry ($)")
            ax.set_ylabel("P&L per MT ($)")
            ax.set_title(f"{position} {strike:,.0f} {opt_type} @ ${premium:,.0f} premium")
            ax.legend(loc="upper left")
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.warning("Install matplotlib for the visual payoff diagram: `pip install matplotlib`. Showing raw data instead.")
            st.line_chart(pd.DataFrame({"P&L": payoff_curve}, index=spots))

        m1, m2, m3 = st.columns(3)
        m1.metric("Current P&L / MT", f"${current_payoff:+,.0f}")
        m2.metric("Current P&L (25 MT contract)", f"${current_payoff * 25:+,.0f}")
        m3.metric("Breakeven", f"${breakeven:,.0f}")

# --- Quant Practice (Green Book daily question; see quant_tab.py) ---
with tab_quant:
    import quant_tab
    quant_tab.render()

# --- TAB 7: Performance Dashboard ---
with tab7:
    st.header("Performance Dashboard")
    try:
        df = read_logs()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Quant answers are logged per question ("Quant::<id>"); group them as one module here.
            df['tab_name'] = df['tab_name'].astype(str).where(~df['tab_name'].astype(str).str.startswith("Quant::"), "Quant Practice")
            # Poker answers are logged per spot/hand or question type; group them too.
            df['tab_name'] = df['tab_name'].where(~df['tab_name'].str.startswith("Poker::PF::"), "Poker Preflop")
            df['tab_name'] = df['tab_name'].where(~df['tab_name'].str.startswith("Poker::Math::"), "Poker Math")
            df['tab_name'] = df['tab_name'].where(~df['tab_name'].str.startswith("Poker::Post::"), "Poker Postflop")
            df['tab_name'] = df['tab_name'].where(~df['tab_name'].str.startswith("Poker::Texture::"), "Poker Board Textures")
            df['tab_name'] = df['tab_name'].where(~df['tab_name'].str.startswith("Poker::Equity::"), "Poker Equity")
            
            # NEW: Filter by Exercise Module
            tabs_available = df['tab_name'].unique().tolist()
            selected_tab = st.selectbox("Select Exercise Module:", ["All Modules"] + tabs_available)
            
            if selected_tab != "All Modules":
                df = df[df['tab_name'] == selected_tab]
            
            total_correct = df['is_correct'].sum()
            total_time_min = df['time_sec'].sum() / 60.0
            
            cpm = total_correct / total_time_min if total_time_min > 0 else 0
            accuracy = (total_correct / len(df)) * 100 if len(df) > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("CPM (Calculations/Min)", f"{cpm:.2f}")
            col2.metric("Accuracy", f"{accuracy:.1f}%")
            col3.metric("Exercises Completed", len(df))
            
            st.subheader(f"Rolling 10-Question Time ({selected_tab})")
            if len(df) >= 10:
                # Sort by time so the rolling average plots chronologically 
                df_sorted = df.sort_values('timestamp')
                df_sorted['rolling_time'] = df_sorted['time_sec'].rolling(10).mean()
                st.line_chart(df_sorted.set_index('timestamp')['rolling_time'])
            else:
                st.info("Complete at least 10 questions in this module to generate the moving average chart.")
            
            st.subheader("Raw Session Data")
            st.dataframe(df.sort_values(by="timestamp", ascending=False).head(50))
        else:
            st.write("No data logged yet. Complete some exercises!")
    except Exception as e:
        st.write(f"Error loading dashboard data: {e}")