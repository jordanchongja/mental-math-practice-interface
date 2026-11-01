# Mental RAM & Case Math Engine

### Purpose of this Interface
I built this interface because I realized that I was struggling with mental math speed and visualizing market sizing structures during case prep. I wanted to build a tool that would help me target my specific weak points and was fully customizable to my own issues. 

I built this in Streamlit and decided to host it locally for the time being. The major advantage of local hosting is the ability to write to a local SQLite database and CSV file, allowing you to persistently track your metrics and visualize your improvement over time. (Hosting it online works as well, but the persistent database would need to be swapped for session-state tracking, meaning your stats would reset every time you refresh the page). 

If you are grinding for case interviews in management consulting (MBB, Tier 2) or high-finance roles, I hope this helps you build the muscle memory required to clear the math hurdles effortlessly.

---

## 🚀 Getting Started

To run this interface, you will need Python installed on your machine. The app runs on **Streamlit**, a fast and powerful open-source Python framework for building machine learning and data science web apps.

### 1. Clone the Repository
Open your terminal or command prompt and clone this repository to your local machine:
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
```

### 2. Install Dependencies
It is highly recommended to use a virtual environment. Once inside the project folder, install the required packages:
```bash
pip install -r requirements.txt
```
The primary dependencies are Streamlit and Pandas. Matplotlib is used for the payoff diagram in the Trading Drills tab — if it isn't installed, that one chart falls back to a simpler view and the rest of the app is unaffected.


### 3. Run the Engine
To launch the app, simply execute the following command in your terminal:
```bash
streamlit run app.py
```
A local web server will spin up, and the interface will automatically open in your default web browser (usually at `http://localhost:8501`). 

*Note: The first time you run the app or submit an answer, it will automatically generate a local `math_stats.db` (SQLite Database) and a `performance_log.csv` in the same folder to track your metrics.*

---

## 🧠 The Training Modules

This app is designed like a high-performance typing test, but for case math. The cursor auto-focuses after every submission so you never have to touch your mouse.

### Tab 1: Rapid Arithmetic (Mental RAM)
This is your bread and butter. It tests your raw speed in addition, subtraction, multiplication, and clean division. You can toggle specific operations on or off to target your weakest links.

### Tab 2: Rote Memory Bank
In case math, you often see a number like 225 and need to immediately recognize it as 15². This tab drills your perfect squares (up to 20) and fraction-to-percentage conversions (e.g., 1/7 = 14.286%). Turn on **Mixed Mode** to train your brain to calculate in reverse (e.g., square roots and finding the denominator from a percentage).

### Tab 3: Zero Gravity Engine (Magnitudes)
Consulting math is notorious for tripping candidates up with zeros. This module forces you to separate the "Mantissa Math" (e.g., 1.5 / 3 = 0.5) from the "Zero Math" (e.g., Billions / Thousands = Millions) so you never drop a zero under pressure again.

### Tab 4: Fraction & Bounding Simulator
Calculators aren't allowed in case interviews. This tab generates ugly fractions (e.g., 87 / 643) and forces you to estimate the percentage within a 1% variance. The feedback breaks down the denominator into 10%, 5%, and 1% building blocks to show you how to quickly bound the exact answer.

### Tab 5: Case Interview Scenarios
This is the ultimate context-switching drill. It randomly generates five of the most common sequential math frameworks seen in case interviews:
1. **Standard TAM:** Bottom-up market sizing.
2. **Market Share Target:** Reverse-engineering the market share needed to hit a revenue goal.
3. **Profitability:** Calculating net profit given volume, price, variable costs, and fixed costs.
4. **Breakeven Volume:** Calculating exact units required to cover fixed costs.
5. **Compounding Growth:** Calculating Year 2 revenues based on a starting base and YoY growth rate.

### Tab 6: Trading Drills
Built for trading intuition rather than case interviews, sized to dairy/milk futures price ranges. Pick a module from the radio selector:
- **Basis & Futures Curve** — three drills: compute the exact (signed) basis from a spot/futures pair, judge whether a basis move over time is strengthening or weakening, and read a 4-point futures curve to call contango vs. backwardation.
- **Milk Price Arithmetic** — mixed-format speed drill that randomly asks you to compute basis, solve for effective price from futures + basis, judge basis direction, or work a full hedge P&L (futures P&L per MT, total P&L, and net effective price).
- **Options Breakeven** — mixed-format drill covering call/put breakeven, ITM/OTM/ATM judgment with intrinsic value, and net effective price for a protective put.
- **Payoff Diagram Explorer** — not scored. Pick option type, position (long/short), strike, and premium, then drag a spot-price slider to watch the P&L payoff diagram update live — built for memorizing the shape of each payoff curve.

### Tab 7: Performance Dashboard
If you can maintain 120 WPM on a keyboard, you can train your Calculations Per Minute (CPM) just as rigorously. This dashboard reads your answer history (see *Saving your stats* below) to display your overall accuracy, CPM, and a rolling 10-question moving average chart (filterable by module) to track your progression over time.

### Saving your stats
With no setup, answers go to a local SQLite file (`math_stats.db`). That's fine on your own machine, but Streamlit Community Cloud wipes local files whenever the app restarts, so a hosted copy saves to a Google Sheet instead. Add this to `.streamlit/secrets.toml` locally, or to the app's **Settings → Secrets** on Streamlit Cloud:

```toml
[gsheet]
spreadsheet_id = "the-id-from-the-sheet-url"
worksheet = "mental_math_logs"   # tab name; created automatically if missing

[gcp_service_account]
# paste the service account JSON key here, as a TOML table
```

Share the sheet with the service account's `client_email` as an Editor. Sheet writes run in the background, so answering stays instant.

---

## 🏁 Conclusion
Case math is not about innate genius; it is about pattern recognition and mechanical repetition. Treat this tool like a daily warm-up workbench before you dive into live casing or technical assessments. 

Feel free to fork this repository, add your own custom case scenarios to Tab 5, and adjust the logic to fit your specific prep needs. Happy casing!