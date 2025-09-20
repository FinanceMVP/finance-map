import streamlit as st
import pandas as pd
from typing import List, Literal
from pydantic import BaseModel, Field

# ============================================================
# SCENARIO ENGINE (merged from scenario_engine.py)
# ============================================================

class ScenarioInput(BaseModel):
    lump_sum: float = Field(..., ge=0)
    monthly_free_cash: float = Field(0, ge=0)
    debt_balance: float = Field(0, ge=0)
    apr: float = Field(0, ge=0, le=100)
    min_payment: float = Field(0, ge=0)
    invest_return: float = Field(7.0, ge=-100, le=100)
    emergency_fund_goal: float = Field(0, ge=0)
    months: int = Field(60, ge=1, le=360)
    assumed_happiness: int = Field(60, ge=0, le=100)

class ScenarioResult(BaseModel):
    name: Literal["Pay Debt", "Invest", "Save", "Hybrid", "Debt+EF"]
    end_balance: float
    interest_saved: float
    investment_value: float
    liquidity: float
    time_to_debt_free_months: int

def _monthly_rate(apr_pct: float) -> float:
    return (apr_pct / 100.0) / 12.0

def _future_value(monthly_contrib: float, months: int, annual_return_pct: float) -> float:
    r = (annual_return_pct / 100.0) / 12.0
    fv = 0.0
    for _ in range(months):
        fv = fv * (1 + r) + monthly_contrib
    return fv

def _amortize(balance: float, apr_pct: float, monthly_payment: float, months: int):
    r = _monthly_rate(apr_pct)
    interest_paid = 0.0
    for m in range(1, months + 1):
        interest = balance * r
        principal = max(0.0, monthly_payment - interest)
        interest_paid += interest
        balance = max(0.0, balance - principal)
        if balance <= 0.01:
            return interest_paid, m
    return interest_paid, months

def run_scenarios(inp: ScenarioInput) -> List[ScenarioResult]:
    res: List[ScenarioResult] = []

    # Scenario A: Pay Debt
    lump_to_debt = min(inp.lump_sum, inp.debt_balance)
    new_balance = max(0.0, inp.debt_balance - lump_to_debt)
    extra = inp.monthly_free_cash
    interest_paid_a, months_a = _amortize(new_balance, inp.apr, inp.min_payment + extra, inp.months)
    res.append(ScenarioResult(
        name="Pay Debt",
        end_balance=0.0,
        interest_saved=max(0.0, _amortize(inp.debt_balance, inp.apr, inp.min_payment, inp.months)[0] - interest_paid_a),
        investment_value=0.0,
        liquidity=max(0.0, inp.emergency_fund_goal),
        time_to_debt_free_months=months_a
    ))

    # Scenario B: Invest
    fv_b = _future_value(inp.monthly_free_cash, inp.months, inp.invest_return) + inp.lump_sum
    interest_paid_b, months_b = _amortize(inp.debt_balance, inp.apr, inp.min_payment, inp.months)
    res.append(ScenarioResult(
        name="Invest",
        end_balance=0.0,
        interest_saved=0.0,
        investment_value=fv_b,
        liquidity=max(0.0, inp.emergency_fund_goal),
        time_to_debt_free_months=months_b
    ))

    # Scenario C: Save
    liquidity_c = min(inp.emergency_fund_goal, inp.lump_sum) + inp.monthly_free_cash * min(inp.months, 12)
    interest_paid_c, months_c = _amortize(inp.debt_balance, inp.apr, inp.min_payment, inp.months)
    res.append(ScenarioResult(
        name="Save",
        end_balance=0.0,
        interest_saved=0.0,
        investment_value=0.0,
        liquidity=liquidity_c,
        time_to_debt_free_months=months_c
    ))

    # Scenario D: Hybrid
    lump_debt = 0.5 * inp.lump_sum
    lump_invest = 0.25 * inp.lump_sum
    lump_save = 0.25 * inp.lump_sum
    bal_d = max(0.0, inp.debt_balance - min(lump_debt, inp.debt_balance))
    interest_paid_d, months_d = _amortize(bal_d, inp.apr, inp.min_payment + 0.5 * inp.monthly_free_cash, inp.months)
    fv_d = _future_value(0.25 * inp.monthly_free_cash, inp.months, inp.invest_return) + lump_invest
    liquidity_d = lump_save + 0.25 * inp.monthly_free_cash * min(inp.months, 12)

    res.append(ScenarioResult(
        name="Hybrid",
        end_balance=0.0,
        interest_saved=max(0.0, _amortize(inp.debt_balance, inp.apr, inp.min_payment, inp.months)[0] - interest_paid_d),
        investment_value=fv_d,
        liquidity=liquidity_d,
        time_to_debt_free_months=months_d
    ))

    # Scenario E: Debt + EF Goal
    lump_to_debt = 0.7 * inp.lump_sum
    lump_to_ef = 0.3 * inp.lump_sum
    bal_e = max(0.0, inp.debt_balance - lump_to_debt)
    interest_paid_e, months_e = _amortize(bal_e, inp.apr, inp.min_payment + 0.7 * inp.monthly_free_cash, inp.months)
    ef_accumulated = lump_to_ef + (0.3 * inp.monthly_free_cash * min(inp.months, 24))

    res.append(ScenarioResult(
        name="Debt+EF",
        end_balance=0.0,
        interest_saved=max(0.0, _amortize(inp.debt_balance, inp.apr, inp.min_payment, inp.months)[0] - interest_paid_e),
        investment_value=0.0,
        liquidity=ef_accumulated,
        time_to_debt_free_months=months_e
    ))

    return res

# ============================================================
# NARRATIVES (merged)
# ============================================================

def generate_improved_narratives(results: List[ScenarioResult], inp: ScenarioInput):
    narratives = {}
    for r in results:
        if r.name == "Pay Debt":
            narratives[r.name] = f"""
            ### 🎯 Pay Debt
            You aggressively pay off your debt. Debt free in **{r.time_to_debt_free_months} months**, saving **${r.interest_saved:,.0f}** in interest.
            """
        elif r.name == "Invest":
            narratives[r.name] = f"""
            ### 📈 Invest
            By investing all funds, you could build **${r.investment_value:,.0f}** in {inp.months} months. Debt remains on minimum payment schedule.
            """
        elif r.name == "Save":
            narratives[r.name] = f"""
            ### 💰 Save
            You build an emergency fund of **${r.liquidity:,.0f}** within {min(inp.months,12)} months. Debt payoff is delayed.
            """
        elif r.name == "Hybrid":
            narratives[r.name] = f"""
            ### ⚖️ Hybrid
            Split approach:  
            • Save **${r.liquidity:,.0f}**  
            • Invest **${r.investment_value:,.0f}**  
            • Save **${r.interest_saved:,.0f}** in interest by paying debt faster.
            """
        elif r.name == "Debt+EF":
            narratives[r.name] = f"""
            ### 🔗 Debt + Emergency Fund
            Prioritize debt with {70}% of funds and build EF with {30}%.  
            • EF grows to **${r.liquidity:,.0f}**  
            • Debt free in **{r.time_to_debt_free_months} months**, saving **${r.interest_saved:,.0f}** interest.
            """
    return narratives

# ============================================================
# STREAMLIT APP UI
# ============================================================

st.title("💰 Financial Scenario Planner (Standalone)")

st.sidebar.header("Inputs")

inp = ScenarioInput(
    lump_sum=st.sidebar.number_input("Expected lump sum ($)", min_value=0, value=5000, step=500),
    monthly_free_cash=st.sidebar.number_input("Monthly free cash ($)", min_value=0, value=500, step=50),
    debt_balance=st.sidebar.number_input("Debt balance ($)", min_value=0, value=5000, step=500),
    apr=st.sidebar.number_input("Debt APR (%)", min_value=0.0, max_value=100.0, value=24.0, step=0.5),
    min_payment=st.sidebar.number_input("Minimum debt payment ($)", min_value=0, value=120, step=10),
    invest_return=st.sidebar.number_input("Expected investment return (%)", min_value=-100.0, max_value=100.0, value=7.0, step=0.5),
    emergency_fund_goal=st.sidebar.number_input("Emergency fund goal ($)", min_value=0, value=15000, step=500),
    months=st.sidebar.slider("Timeline (months)", 6, 120, 60),
    assumed_happiness=st.sidebar.slider("Happiness threshold (0-100)", 0, 100, 60)
)

if st.button("Run scenarios"):
    results = run_scenarios(inp)
    df = pd.DataFrame([r.dict() for r in results])
    st.subheader("📑 Scenario Results")
    st.dataframe(df)

    narratives = generate_improved_narratives(results, inp)
    st.subheader("📊 Narratives")
    for name, text in narratives.items():
        st.markdown(text)
