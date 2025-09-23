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

# Repo of 100 follow-up questions (examples, expand as needed)
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

    # Scenario D: Hybrid (weights later adjusted via happiness score)
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
# NARRATIVES
# ============================================================

def generate_improved_narratives(results: List[ScenarioResult], inp: ScenarioInput):
    narratives = {}
    for r in results:
        if r.name == "Pay Debt":
            narratives[r.name] = f"🎯 Debt free in {r.time_to_debt_free_months} months, saving ${r.interest_saved:,.0f} interest."
        elif r.name == "Invest":
            narratives[r.name] = f"📈 Invest: Grow balance to ${r.investment_value:,.0f} in {inp.months} months."
        elif r.name == "Save":
            narratives[r.name] = f"💰 Save: Build EF to ${r.liquidity:,.0f} within {min(inp.months,12)} months."
        elif r.name == "Hybrid":
            narratives[r.name] = f"⚖️ Hybrid: $ to debt, investing, and savings split → ${r.interest_saved:,.0f} saved, ${r.investment_value:,.0f} invested, ${r.liquidity:,.0f} saved."
        elif r.name == "Debt+EF":
            narratives[r.name] = f"🔗 Debt+EF: Debt free in {r.time_to_debt_free_months} months, EF ${r.liquidity:,.0f}, ${r.interest_saved:,.0f} saved."
    return narratives

# ============================================================
# STREAMLIT APP
# ============================================================

st.title("💰 Financial Scenario Planner (Standalone)")

# Step 1: CFPB Initial Questions
st.header("Step 1: Financial Well-being Questions")
responses = []
for i, q in enumerate(initial_questions):
    responses.append(st.slider(q, 1, 5, 3, key=f"q{i}"))

if st.button("Submit Initial Questions"):
    score = sum(responses) * 4  # simple scale to 100
    st.session_state["wellbeing_score"] = score
    st.success(f"Your financial well-being score is {score}/100")

# Step 2: Cashflow + Debts
st.sidebar.header("Cash & Goals")
lump_sum = st.sidebar.number_input("Expected lump sum ($)", min_value=0, value=5000, step=500)
monthly_free_cash = st.sidebar.number_input("Monthly free cash ($)", min_value=0, value=500, step=50)
invest_return = st.sidebar.number_input("Expected investment return (%)", min_value=-100.0, max_value=100.0, value=7.0, step=0.5)
emergency_fund_goal = st.sidebar.number_input("Emergency fund goal ($)", min_value=0, value=15000, step=500)
months = st.sidebar.slider("Timeline (months)", 6, 120, 60)

st.sidebar.header("Debts")
num_debts = st.sidebar.number_input("How many debts do you have?", min_value=1, max_value=10, value=2)
debts = []
for i in range(num_debts):
    st.sidebar.subheader(f"Debt {i+1}")
    category = st.sidebar.selectbox(f"Category {i+1}", ["Credit Card", "Auto Loan", "Mortgage", "Student Loan", "Personal Loan"], key=f"cat_{i}")
    balance = st.sidebar.number_input(f"Balance {i+1} ($)", min_value=0, value=1000, step=100, key=f"bal_{i}")
    apr = st.sidebar.number_input(f"APR {i+1} (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.5, key=f"apr_{i}")
    min_payment = st.sidebar.number_input(f"Minimum Payment {i+1} ($)", min_value=0, value=50, step=10, key=f"min_{i}")
    revolving = st.sidebar.checkbox(f"Revolving? {i+1}", value=(category=="Credit Card"), key=f"rev_{i}")
    monthly_spend = st.sidebar.number_input(f"Monthly Spend {i+1} ($)", min_value=0, value=0, step=10, key=f"spend_{i}") if revolving else 0.0
    debts.append(Debt(category=category, balance=balance, apr=apr, min_payment=min_payment, revolving=revolving, monthly_spend=monthly_spend))

inp = ScenarioInput(
    lump_sum=lump_sum,
    monthly_free_cash=monthly_free_cash,
    debts=debts,
    invest_return=invest_return,
    emergency_fund_goal=emergency_fund_goal,
    months=months,
    assumed_happiness=st.session_state.get("wellbeing_score", 60)
)

if st.button("Run scenarios"):
    results = run_scenarios(inp)
    df = pd.DataFrame([r.dict() for r in results])
    st.subheader("📑 Scenario Results")
    st.dataframe(df)

    narratives = generate_improved_narratives(results, inp)
    st.subheader("📊 Narratives")
    for name, text in narratives.items():
        st.markdown(f"**{name}** → {text}")

# Step 3: Follow-up Questions
st.header("Step 3: Periodic Follow-up")
if st.button("Get Follow-up Questions"):
    followups = random.sample(followup_questions, 3)
    for q in followups:
        st.slider(q, 1, 5, 3)
