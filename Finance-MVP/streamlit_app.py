import streamlit as st
import pandas as pd
from typing import List, Literal
from pydantic import BaseModel, Field
import random

# ============================================================
# DATA MODELS
# ============================================================

class Debt(BaseModel):
    category: Literal["Credit Card", "Auto Loan", "Mortgage", "Student Loan", "Personal Loan"]
    balance: float
    apr: float
    min_payment: float
    revolving: bool = False
    monthly_spend: float = 0.0

class ScenarioInput(BaseModel):
    lump_sum: float = Field(..., ge=0)
    monthly_free_cash: float = Field(0, ge=0)
    debts: List[Debt] = []
    invest_return: float = Field(7.0, ge=-100, le=100)
    emergency_fund_goal: float = Field(0, ge=0)
    months: int = Field(60, ge=1, le=360)
    assumed_happiness: int = Field(60, ge=0, le=100)

class ScenarioResult(BaseModel):
    name: Literal["Pay Debt", "Invest", "Save", "Hybrid", "Debt+EF"]
    interest_saved: float
    investment_value: float
    liquidity: float
    time_to_debt_free_months: int

# ============================================================
# QUESTIONS REPOSITORY
# ============================================================

initial_questions = [
    "How confident are you that you could handle a major unexpected expense?",
    "How often do you run out of money before the end of the month?",
    "How secure do you feel about your financial future?",
    "How often do you worry about paying for basic needs?",
    "Do you feel you are on track to meet your long-term goals?",
    "If faced with an emergency expense, how easily could you cover it?",
    "How often do you delay medical or other essential expenses due to money?",
    "Do you feel your debt is manageable?",
    "How often do you feel stress because of your finances?",
    "How satisfied are you with your current financial situation?"
]

followup_questions = [
    f"Follow-up financial question {i+1}: (Likert scale 1-5)" for i in range(100)
]

# ============================================================
# SCENARIO ENGINE
# ============================================================

def _monthly_rate(apr_pct: float) -> float:
    return (apr_pct / 100.0) / 12.0

def _future_value(monthly_contrib: float, months: int, annual_return_pct: float) -> float:
    r = (annual_return_pct / 100.0) / 12.0
    fv = 0.0
    for _ in range(months):
        fv = fv * (1 + r) + monthly_contrib
    return fv

def _amortize(balance: float, apr_pct: float, monthly_payment: float, months: int, revolving: bool = False, monthly_spend: float = 0.0):
    r = _monthly_rate(apr_pct)
    interest_paid = 0.0
    for m in range(1, months + 1):
        interest = balance * r
        principal = max(0.0, monthly_payment - interest)
        interest_paid += interest
        balance = max(0.0, balance - principal)
        if revolving:
            balance += monthly_spend
        if balance <= 0.01:
            return interest_paid, m
    return interest_paid, months

def run_scenarios(inp: ScenarioInput) -> List[ScenarioResult]:
    results: List[ScenarioResult] = []

    total_debt = sum(d.balance for d in inp.debts)
    avg_apr = (sum(d.apr * d.balance for d in inp.debts) / total_debt) if total_debt > 0 else 0
    min_payment = sum(d.min_payment for d in inp.debts)

    # Scenario A: Pay Debt
    interest_no_extra, months_no_extra = _amortize(total_debt, avg_apr, min_payment, inp.months)
    interest_with_extra, months_with_extra = _amortize(total_debt, avg_apr, min_payment + inp.monthly_free_cash, inp.months)
    results.append(ScenarioResult(
        name="Pay Debt",
        interest_saved=max(0.0, interest_no_extra - interest_with_extra),
        investment_value=0.0,
        liquidity=0.0,
        time_to_debt_free_months=months_with_extra
    ))

    # Scenario B: Invest
    fv_b = _future_value(inp.monthly_free_cash, inp.months, inp.invest_return) + inp.lump_sum
    results.append(ScenarioResult(
        name="Invest",
        interest_saved=0.0,
        investment_value=fv_b,
        liquidity=0.0,
        time_to_debt_free_months=months_no_extra
    ))

    # Scenario C: Save
    liquidity_c = min(inp.emergency_fund_goal, inp.lump_sum) + inp.monthly_free_cash * min(inp.months, 12)
    results.append(ScenarioResult(
        name="Save",
        interest_saved=0.0,
        investment_value=0.0,
        liquidity=liquidity_c,
        time_to_debt_free_months=months_no_extra
    ))

    # Scenario D: Hybrid (50/25/25 split)
    debt_allocation = 0.5 * inp.monthly_free_cash
    invest_allocation = 0.25 * inp.monthly_free_cash
    save_allocation = 0.25 * inp.monthly_free_cash
    interest_paid_d, months_d = _amortize(total_debt, avg_apr, min_payment + debt_allocation, inp.months)
    fv_d = _future_value(invest_allocation, inp.months, inp.invest_return)
    liquidity_d = save_allocation * min(inp.months, 12)
    results.append(ScenarioResult(
        name="Hybrid",
        interest_saved=max(0.0, interest_no_extra - interest_paid_d),
        investment_value=fv_d,
        liquidity=liquidity_d,
        time_to_debt_free_months=months_d
    ))

    # Scenario E: Debt + EF Goal (70/30 split)
    debt_allocation = 0.7 * inp.monthly_free_cash
    save_allocation = 0.3 * inp.monthly_free_cash
    interest_paid_e, months_e = _amortize(total_debt, avg_apr, min_payment + debt_allocation, inp.months)
    ef_accumulated = save_allocation * min(inp.months, 24)
    results.append(ScenarioResult(
        name="Debt+EF",
        interest_saved=max(0.0, interest_no_extra - interest_paid_e),
        investment_value=0.0,
        liquidity=ef_accumulated,
        time_to_debt_free_months=months_e
    ))

    return results

# ============================================================
# NARRATIVES + RECOMMENDATION
# ============================================================

def generate_improved_narratives(results: List[ScenarioResult], inp: ScenarioInput):
    narratives = {}
    for r in results:
        if r.name == "Pay Debt":
            narratives[r.name] = f"🎯 Debt free in {r.time_to_debt_free_months} months, saving ${r.interest_saved:,.0f} interest."
        elif r.name == "Invest":
            narratives[r.name] = f"📈 Invest: Grow balance to ${r.investment_value:,.0f} in {inp.months} months."
        elif r.name == "Save":
            narratives[r.name] = f"💰 Save: Build Emergency Fund to ${r.liquidity:,.0f} within {min(inp.months,12)} months."
        elif r.name == "Hybrid":
            narratives[r.name] = f"⚖️ Hybrid: Save ${r.interest_saved:,.0f}, invest ${r.investment_value:,.0f}, build EF ${r.liquidity:,.0f}."
        elif r.name == "Debt+EF":
            narratives[r.name] = f"🔗 Debt+EF: Debt free in {r.time_to_debt_free_months} months, EF ${r.liquidity:,.0f}, saving ${r.interest_saved:,.0f}."
    return narratives

def recommend_strategy(score: int, results: List[ScenarioResult]):
    if score >= 75:
        rec = "Hybrid or Invest"
        why = "Your score is strong. You can afford to balance debt reduction with investing for growth."
    elif 50 <= score < 75:
        rec = "Hybrid or Debt+EF"
        why = "Your score is moderate. A balanced approach with an emergency fund provides stability."
    else:
        rec = "Pay Debt or Save"
        why = "Your score is lower. Reducing debt or building savings will reduce financial stress first."
    return rec, why

# ============================================================
# STREAMLIT APP (LINEAR FLOW)
# ============================================================

if "step" not in st.session_state:
    st.session_state["step"] = 1
if "initial_responses" not in st.session_state:
    st.session_state["initial_responses"] = []
if "happiness_score" not in st.session_state:
    st.session_state["happiness_score"] = None
if "followups" not in st.session_state:
    st.session_state["followups"] = []

step = st.session_state["step"]

# ---------------- Step 1: Landing ----------------
if step == 1:
    st.title("💰 Welcome to Finance MVP")
    st.write("""
    Your personal finance and scenario tool.

    This app helps you explore how different choices—paying debt, investing, or saving—affect your financial future.
    We begin with **10 questions from the CFPB financial well-being survey**. These questions measure your confidence and stress
    about money on a **0–5 scale** (0 = least likely, 5 = most likely).

    After your score is calculated, you’ll enter your personal inputs and see tailored scenarios.
    Every few months, we’ll ask additional follow-up questions to refine your profile.
    """)
    if st.button("Continue →"):
        st.session_state["step"] = 2
        st.rerun()

# ---------------- Step 2: Questions ----------------
elif step == 2:
    st.header("Step 2: Financial Well-being Questions")
    responses = []
    for i, q in enumerate(initial_questions):
        val = st.slider(q, 0, 5, 3, key=f"q{i}")
        responses.append(val)
    if st.button("Submit Responses"):
        st.session_state["initial_responses"] = responses
        score = sum(responses) * 2  # Scale to ~100
        st.session_state["happiness_score"] = score
        st.session_state["step"] = 3
        st.rerun()
    if st.button("← Back"):
        st.session_state["step"] = 1
        st.rerun()

# ---------------- Step 3: Score + Inputs ----------------
elif step == 3:
    st.header("Step 3: Your Happiness Score & Inputs")
    score = st.session_state["happiness_score"]
    st.success(f"Your financial well-being score is {score}/100")

    st.write("Now enter your financial details:")

    lump_sum = st.number_input("Expected lump sum (bonus, refund, etc.)", min_value=0, value=5000, step=500)
    monthly_free_cash = st.number_input("Monthly free cash (after bills)", min_value=0, value=500, step=50)
    invest_return = st.number_input("Expected investment return (%)", min_value=-100.0, max_value=100.0, value=7.0, step=0.5)
    emergency_fund_goal = st.number_input("Emergency Fund goal ($)", min_value=0, value=15000, step=500)

    st.write("### Timeline")
    months_slider = st.slider("Timeline (months)", 6, 120, 60)
    months_input = st.number_input("Or enter timeline manually (months)", min_value=1, max_value=360, value=months_slider)
    months = months_input

    st.write("### Debts")
    num_debts = st.number_input("How many debts do you have?", min_value=1, max_value=10, value=2)
    debts = []
    for i in range(num_debts):
        category = st.selectbox(f"Debt {i+1} Category", ["Credit Card", "Auto Loan", "Mortgage", "Student Loan", "Personal Loan"], key=f"cat_{i}")
        st.caption({
            "Credit Card": "Revolving debt with variable payments.",
            "Auto Loan": "Fixed-term loan for a vehicle.",
            "Mortgage": "Long-term home loan with collateral.",
            "Student Loan": "Loan for education expenses.",
            "Personal Loan": "Unsecured loan for personal use."
        }[category])
        balance = st.number_input(f"Debt {i+1} Balance ($)", min_value=0, value=1000, step=100, key=f"bal_{i}")
        apr = st.number_input(f"Debt {i+1} APR (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.5, key=f"apr_{i}")
        min_payment = st.number_input(f"Debt {i+1} Minimum Payment ($)", min_value=0, value=50, step=10, key=f"min_{i}")
        revolving = st.checkbox(f"Debt {i+1} Revolving?", value=(category=="Credit Card"), key=f"rev_{i}")
        monthly_spend = st.number_input(f"Debt {i+1} Monthly Spend ($)", min_value=0, value=0, step=10, key=f"spend_{i}") if revolving else 0.0
        debts.append(Debt(category=category, balance=balance, apr=apr, min_payment=min_payment, revolving=revolving, monthly_spend=monthly_spend))

    st.session_state["scenario_input"] = ScenarioInput(
        lump_sum=lump_sum,
        monthly_free_cash=monthly_free_cash,
        debts=debts,
        invest_return=invest_return,
        emergency_fund_goal=emergency_fund_goal,
        months=months,
        assumed_happiness=score
    )

    if st.button("Continue →"):
        st.session_state["step"] = 4
        st.rerun()
    if st.button("← Back"):
        st.session_state["step"] = 2
        st.rerun()

# ---------------- Step 4: Results ----------------
elif step == 4:
    st.header("Step 4: Scenario Results")
    inp = st.session_state["scenario_input"]
    results = run_scenarios(inp)
    st.session_state["results"] = results

    # Recommendation
    rec, why = recommend_strategy(st.session_state["happiness_score"], results)
    st.markdown(f"### 🌟 Recommended Next Step\n**Strategy:** {rec}\n\n**Why:** {why}")

    # Table
    df = pd.DataFrame([r.dict() for r in results])
    st.dataframe(df)

    # Narratives
    st.write("### Other Scenarios")
    narratives = generate_improved_narratives(results, inp)
    for name, text in narratives.items():
        st.markdown(f"**{name}** → {text}")

    if st.button("Continue →"):
        st.session_state["step"] = 5
        st.rerun()
    if st.button("← Back"):
        st.session_state["step"] = 3
        st.rerun()

# ---------------- Step 5: Follow-ups ----------------
elif step == 5:
    st.header("Step 5: Follow-up Questions")
    st.write("Every few months, answer a few more questions to refine your score.")
    followups = random.sample(followup_questions, 3)
    answers = []
    for i, q in enumerate(followups):
        val = st.slider(q, 0, 5, 3, key=f"fup{i}{len(st.session_state['followups'])}")
        answers.append(val)
    if st.button("Finish"):
        st.session_state["followups"].append(answers)
        st.success("Follow-up responses saved.")
    if st.button("Restart"):
        st.session_state.clear()
        st.session_state["step"] = 1
        st.rerun()
    if st.button("← Back"):
        st.session_state["step"] = 4
        st.rerun()
