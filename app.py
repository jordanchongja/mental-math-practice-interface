import streamlit as st
import sqlite3
import pandas as pd
import random
import time
import math
from datetime import datetime
import streamlit.components.v1 as components

# --- Database & State Initialization ---
DB_NAME = "math_stats.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  tab_name TEXT,
                  is_correct INTEGER,
                  time_sec REAL,
                  xp_earned INTEGER)''')
    conn.commit()
    conn.close()

def log_performance(tab_name, is_correct, time_sec, xp_earned):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO logs (tab_name, is_correct, time_sec, xp_earned) VALUES (?, ?, ?, ?)",
              (tab_name, int(is_correct), time_sec, xp_earned))
    conn.commit()
    
    # Export to CSV automatically
    df = pd.read_sql_query("SELECT * FROM logs", conn)
    df.to_csv("performance_log.csv", index=False)
    conn.close()

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

def autofocus_active_input():
    """Forces the cursor back into the visible text input field."""
    components.html(
        """
        <script>
        // Find all text inputs in the parent Streamlit window
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        for (let input of inputs) {
            // Check if the input is currently visible on the screen (active tab)
            if (input.offsetParent !== null) {
                // Slight delay to ensure Streamlit has finished rendering before grabbing focus
                setTimeout(() => { input.focus(); }, 50); 
                break;
            }
        }
        </script>
        """,
        height=0
    )

# --- UI Setup ---
st.set_page_config(page_title="Case Math Engine", layout="wide")
st.title("Mental RAM & Case Math Engine")

st.sidebar.header("Current Session")
st.sidebar.metric("Total XP", st.session_state.total_xp)
st.sidebar.metric("Current Streak", st.session_state.streak)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Rapid Math", "Rote Memory", "Zero Gravity", 
    "Fraction Simulator", "Market Sizing", "Dashboard"
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

    # 2. State Key Fix
    if st.session_state.q_data.get("Zero Gravity") is None:
        mags = {"Thousand": 3, "Million": 6, "Billion": 9}
        op = random.choice(["Multiply", "Divide"])
        
        if op == "Divide":
            mantissa_ans = random.choice([0.5, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0])
            n2 = random.randint(2, 9)
            n1 = mantissa_ans * n2
            mag1, mag2 = random.sample(list(mags.items()), 2)
            if mag1[1] < mag2[1]: mag1, mag2 = mag2, mag1 
            correct_val = (n1 * (10**mag1[1])) / (n2 * (10**mag2[1]))
        else:
            n1 = random.randint(2, 15)
            n2 = random.randint(2, 15)
            mag1, mag2 = random.sample(list(mags.items()), 2)
            correct_val = (n1 * (10**mag1[1])) * (n2 * (10**mag2[1]))
            
        st.session_state.q_data["Zero Gravity"] = (n1, mag1, op, n2, mag2, correct_val)

    n1, mag1, op, n2, mag2, correct_val = st.session_state.q_data["Zero Gravity"]
    st.subheader(f"{n1} {mag1[0]} {op.lower()} by {n2} {mag2[0]}")
    
    with st.form("t3_form", clear_on_submit=True):
        # 3. Text Input Fix
        user_input = st.text_input("Raw Number Answer (e.g., 500000):")

        autofocus_active_input()
        
        if st.form_submit_button("Submit"):
            if user_input.strip() != "":
                try:
                    user_ans = float(user_input)
                    is_correct = math.isclose(user_ans, correct_val, rel_tol=1e-5)
                    process_answer("Zero Gravity", is_correct)
                    
                    # Append the breakdown to the feedback message so it survives the reload
                    if op == "Divide":
                        breakdown = f"\n\n**Breakdown:** Mantissa: {n1} / {n2} = {n1/n2}. Zeros: 10^{mag1[1]} / 10^{mag2[1]} = 10^{mag1[1]-mag2[1]}."
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

    # 2. State Key Fix
    if st.session_state.q_data.get("Fraction Bounding") is None:
        num = random.randint(15, 95)
        den = random.randint(110, 850)
        actual_pct = (num / den) * 100
        st.session_state.q_data["Fraction Bounding"] = (num, den, actual_pct)

    num, den, actual_pct = st.session_state.q_data["Fraction Bounding"]
    st.subheader(f"Estimate: {num} / {den} as a percentage")
    
    with st.form("t4_form", clear_on_submit=True):
        # 3. Text Input Fix
        user_input = st.text_input("Your Estimate (%):")

        autofocus_active_input()
        
        if st.form_submit_button("Submit"):
            if user_input.strip() != "":
                try:
                    user_guess = float(user_input)
                    variance = abs(user_guess - actual_pct)
                    is_correct = variance <= 1.0 # Pass if within 1%
                    process_answer("Fraction Bounding", is_correct)
                    
                    # Append the bounding blocks to the feedback message
                    building_blocks = (
                        f"\n\n**Actual:** {actual_pct:.2f}% (Variance: {variance:.2f}%)\n"
                        f"**Building Blocks of {den}:**\n"
                        f"- 10% = {den * 0.1:.1f}\n"
                        f"- 5% = {den * 0.05:.1f}\n"
                        f"- 1% = {den * 0.01:.1f}"
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

# --- TAB 6: Performance Dashboard ---
with tab6:
    st.header("Performance Dashboard")
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM logs", conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
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