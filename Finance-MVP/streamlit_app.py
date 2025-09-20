import streamlit as st
import pandas as pd

from scenario_engine import run_scenarios, ScenarioInput
from narratives import generate_improved_narratives, display_narratives_streamlit
from questions_repo import INITIAL_QUESTIONS, ADDITIONAL_QUESTIONS

# -----------------------------
# App Configuration
# -----------------------------
st.set_page_config(page_title="Finance MVP", layout="wide")

st.title("💸 Personal Finance Scenario Planner")
st.markdown("Answer a few questions, enter your financial info, and compare strategies for debt payoff, investing, and saving.")

# -----------------------------
# Section 1: Financial Well-Being Questions
# -----------------------------
st.header("Step 1: Financial Well-Being Checkup")

responses = {}
for i, q in enumerate(INITIAL_QUESTIONS, start=1):
    responses[i] = st.slider(q, 0, 5, 3)

# Calculate score (simple sum for now)
happiness_score = sum(responses.values()) * 4  # CFPB scale is 0–100
st.metric("Your Financial Well-Being Score", happiness_score)

# -----------------------------
# Section 2: Debt Information
# -----------------------------
st.header("Step 2: Enter Your Debts")

num_debts = st.number_input("How many debts do you have?", min_value=0, max_value=10, value=1, step=1)

debts = []
for i in range(num_debts):
    st.subheader(f"Debt {i+1}")
    debt_type = st.selectbox("Type of Debt", ["Credit Card", "Student Loan", "Auto Loan", "Mortgage", "Personal Loan"], key=f"type_{i}")
    balance = st.number_input("Balance ($)", min_value=0.0, step=100.0, key=f"balance_{i}")
    apr = st.number_input("APR (%)", min_value=0.0, step=0.1, key=f"apr_{i}")
    min_payment = st.number_input("Minimum Payment ($)", min_value=0.0, step=10.0, key=f"minpay_{i}")
    revolving = False
    monthly_new_charges = 0.0
    if debt_type == "Credit Card":
        revolving = st.checkbox("Is this revolving debt?", key=f"rev_{i}")
        if revolving:
            monthly_new_charges = st.number_input("Monthly new charges ($)", min_value=0.0, step=10.0, key=f"charges_{i}")

    debts.append({
        "type": debt_type,
        "balance": balance,
        "apr": apr,
        "min_payment": min_payment,
        "revolving": revolving,
        "monthly_new_charges": monthly_new_charges
    })

# -----------------------------
# Section 3: Cash & Goals
# -----------------------------
st.header("Step 3: Cash Flow & Goals")

lump_sum = st.number_input("Expected Lump Sum ($)", min_value=0.0, step=100.0)
monthly_free_cash = st.number_input("Monthly Free Cash ($)", min_value=0.0, step=50.0)
emergency_fund_goal = st.number_input("Emergency Fund Goal ($)", min_value=0.0, step=500.0)

timeline_option = st.radio("Do you want to provide your own time horizon (months)?", ["Yes", "No"])
if timeline_option == "Yes":
    months = st.slider("Horizon (months)", 6, 360, 60)
else:
    months = None  # Tool will calculate later if needed

# -----------------------------
# Section 4: Run Scenarios
# -----------------------------
st.header("Step 4: Run Scenarios")

if st.button("Run scenarios"):
    try:
        # Build ScenarioInput for engine
        total_debt = sum(d["balance"] for d in debts)
        avg_apr = sum(d["apr"] for d in debts) / len(debts) if debts else 0
        avg_min_payment = sum(d["min_payment"] for d in debts) / len(debts) if debts else 0

        inp = ScenarioInput(
            lump_sum=lump_sum,
            monthly_free_cash=monthly_free_cash,
            debt_balance=total_debt,
            apr=avg_apr,
            min_payment=avg_min_payment,
            invest_return=7.0,  # default 7% annual return
            emergency_fund_goal=emergency_fund_goal,
            months=months if months else 60,
            assumed_happiness=happiness_score
        )

        results = run_scenarios(inp)

        # Convert results to dict for narrative
        scenarios_dict = {r.name: r.dict() for r in results}
        allocation_data = {
            "initial_amount": lump_sum,
            "monthly_amount": monthly_free_cash,
            "duration_months": months if months else 60,
            "debt_apr": avg_apr / 100,
            "investment_return": 0.07,
            "emergency_fund_goal": emergency_fund_goal,
            "scenarios": scenarios_dict
        }

        narratives = generate_improved_narratives(allocation_data)

        # Show narratives
        display_narratives_streamlit(narratives)

        # Results Table
        st.subheader("📊 Scenario Results")
        df = pd.DataFrame([r.dict() for r in results])
        df.rename(columns={
            "name": "Scenario",
            "end_balance": "Ending Balance ($)",
            "interest_saved": "Interest Saved ($)",
            "investment_value": "Investment Value ($)",
            "liquidity": "Liquidity ($)",
            "time_to_debt_free_months": "Debt-Free Timeline (months)"
        }, inplace=True)
        st.dataframe(df)

        # Export to Excel
        st.download_button(
            label="Download Results as Excel",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="scenario_results.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")

# -----------------------------
# Section 5: Follow-up Questions (long-term scoring)
# -----------------------------
st.header("Step 5: Ongoing Financial Well-Being")

st.markdown("Every 3 months, answer a few more questions to refine your score:")

for i, q in enumerate(ADDITIONAL_QUESTIONS[:3], start=1):
    st.slider(q, 0, 5, 3, key=f"followup_{i}")
