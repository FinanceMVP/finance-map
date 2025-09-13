# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Any
import questions_repo

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="Finance MVP", layout="wide")
st.title("Personal Finance Scenario Pilot")

# Sidebar general inputs
st.sidebar.header("General Inputs")
lump_sum = st.sidebar.number_input("Lump sum (one-time) $", min_value=0.0, step=100.0, value=5000.0)
monthly_free_cash = st.sidebar.number_input("Monthly free cash $", min_value=0.0, step=50.0, value=500.0)
invest_return = st.sidebar.number_input("Expected investment return (%)", min_value=-100.0, max_value=100.0, step=0.1, value=7.0)
emergency_fund_goal = st.sidebar.number_input("Emergency fund goal $", min_value=0.0, step=100.0, value=15000.0)

# Timeline option
set_timeline = st.sidebar.checkbox("Set my own timeline (months)", value=True)
months = None
if set_timeline:
    months = st.sidebar.slider("Horizon (months)", min_value=6, max_value=360, value=60, step=1)

st.sidebar.markdown("---")
st.sidebar.header("Debts (click + Add Debt to add more)")

# Session state for debts
if "debts" not in st.session_state:
    st.session_state["debts"] = []

def add_debt():
    st.session_state.debts.append({"category": "credit_card", "balance": 5000.0, "apr": 18.0, "min_payment": 150.0, "monthly_spend": 0.0})

def remove_last_debt():
    if st.session_state.debts:
        st.session_state.debts.pop()

st.sidebar.button("➕ Add Debt", on_click=add_debt)
st.sidebar.button("➖ Remove Debt", on_click=remove_last_debt)

# Input for each debt
for i, debt in enumerate(st.session_state.debts):
    st.sidebar.subheader(f"Debt {i+1}")
    cat = st.sidebar.selectbox(f"Category {i+1}", ["credit_card", "student_loan", "auto", "mortgage", "personal", "other"], key=f"cat{i}")
    bal = st.sidebar.number_input(f"Balance {i+1} $", min_value=0.0, step=100.0, value=debt.get("balance", 5000.0), key=f"bal{i}")
    apr = st.sidebar.number_input(f"APR {i+1} (%)", min_value=0.0, max_value=200.0, step=0.1, value=debt.get("apr", 18.0), key=f"apr{i}")
    minp = st.sidebar.number_input(f"Minimum payment {i+1} $", min_value=0.0, step=10.0, value=debt.get("min_payment", 150.0), key=f"minp{i}")
    ms = 0.0
    if cat == "credit_card":
        st.sidebar.info("Credit cards are revolving: add estimated new monthly charges.")
        ms = st.sidebar.number_input(f"New monthly charges {i+1} $", min_value=0.0, step=50.0, value=debt.get("monthly_spend", 0.0), key=f"ms{i}")
    st.session_state.debts[i] = {"category": cat, "balance": float(bal), "apr": float(apr), "min_payment": float(minp), "monthly_spend": float(ms)}

st.sidebar.markdown("---")
st.sidebar.header("Assessment (required for tailored recommendations)")
st.sidebar.write("Please answer these 10 CFPB-style questions (0–5).")

if "responses" not in st.session_state:
    st.session_state["responses"] = []

# 10 baseline CFPB questions
questions = [
    {"id": "q1", "text": "How often would you say you are behind on your finances?"},
    {"id": "q2", "text": "How confident are you that you could find $2,000 if an unexpected need arose within the next month?"},
    {"id": "q3", "text": "How often do you feel that your finances control your life?"},
    {"id": "q4", "text": "How confident are you that you are on track to meet your long-term goals?"},
    {"id": "q5", "text": "How often do you worry about not having enough money for basic needs?"},
    {"id": "q6", "text": "How often does your income cover your expenses without difficulty?"},
    {"id": "q7", "text": "How often do you have money left over at the end of the month?"},
    {"id": "q8", "text": "How confident are you that you could handle a major unexpected expense?"},
    {"id": "q9", "text": "How often do you feel anxious about your finances?"},
    {"id": "q10", "text": "How satisfied are you with your current financial situation?"}
]

for q in questions:
    score = st.sidebar.slider(q["text"], 0, 5, key=q["id"])

# Quick fallback option
st.sidebar.markdown("**Quick fallback** (one choice):")
quick_choice = st.sidebar.radio("If you prefer, pick your top priority:", ("debt", "ef", "invest"))

# Submit baseline assessment
if st.sidebar.button("Submit Assessment"):
    payload = [{"id": q["id"], "score": st.session_state.get(q["id"], 0)} for q in questions]
    r = requests.post(f"{API}/assess", json=payload)
    if r.status_code != 200:
        st.sidebar.error(r.text)
    else:
        st.session_state["weights"] = r.json().get("weights")
        st.session_state["initial_score"] = r.json().get("score")
        st.sidebar.success(f"Assessment saved. Score: {st.session_state['initial_score']}, Weights: {st.session_state['weights']}")

# Quick choice assessment
if st.sidebar.button("Submit Quick Choice"):
    r = requests.post(f"{API}/quick_assess", json={"choice": quick_choice})
    if r.status_code != 200:
        st.sidebar.error(r.text)
    else:
        st.session_state["weights"] = r.json().get("weights")
        st.sidebar.success(f"Quick weights applied: {st.session_state['weights']}")

# Follow-up questions (only after initial assessment)
if "initial_score" in st.session_state:
    st.sidebar.header("Follow-up Questions")
    followups = questions_repo.get_followup_questions(3)
    responses = []
    for fq in followups:
        score = st.sidebar.slider(fq["text"], 0, 5, key=fq["id"])
        responses.append({"id": fq["id"], "score": score})

    if st.sidebar.button("Submit Follow-up"):
        r = requests.post(f"{API}/assess", json=responses)
        if r.status_code == 200:
            st.sidebar.success("Your financial well-being score has been updated.")
            st.session_state["weights"] = r.json().get("weights")

# Main section
st.header("Run scenarios")
if st.button("Run scenarios"):
    if "weights" not in st.session_state:
        st.warning("You must complete the assessment or use the quick fallback before running tailored scenarios.")
    else:
        payload = {
            "lump_sum": float(lump_sum),
            "monthly_free_cash": float(monthly_free_cash),
            "debts": st.session_state.debts,
            "invest_return": float(invest_return),
            "emergency_fund_goal": float(emergency_fund_goal),
            "months": int(months) if months else None,
            "assumed_happiness": 60,
            "weights": st.session_state["weights"]
        }
        r = requests.post(f"{API}/scenarios", json=payload)
        if r.status_code != 200:
            st.error(r.text)
        else:
            data = r.json()

            # Clean allocations into readable sentences
            for r in data["results"]:
                alloc = r.get("allocations", {})
                if alloc:
                    parts = []
                    if "lump_to_debt" in alloc or "lump_debt" in alloc:
                        parts.append(f"Lump to debt: ${alloc.get('lump_to_debt', alloc.get('lump_debt', 0)):,}")
                    if "lump_invest" in alloc or "lump_to_invest" in alloc:
                        parts.append(f"Lump to invest: ${alloc.get('lump_invest', alloc.get('lump_to_invest', 0)):,}")
                    if "lump_ef" in alloc or "lump_to_ef" in alloc:
                        parts.append(f"Lump to EF: ${alloc.get('lump_ef', alloc.get('lump_to_ef', 0)):,}")
                    if "monthly_to_debt" in alloc:
                        parts.append(f"Monthly to debt: ${alloc['monthly_to_debt']:,}")
                    if "monthly_to_invest" in alloc:
                        parts.append(f"Monthly to invest: ${alloc['monthly_to_invest']:,}")
                    if "monthly_to_ef" in alloc:
                        parts.append(f"Monthly to EF: ${alloc['monthly_to_ef']:,}")
                    r["allocations"] = "; ".join(parts)
                else:
                    r["allocations"] = "—"

            # Display results
            df = pd.DataFrame(data["results"])
            st.dataframe(df, use_container_width=True)

            # Chart
            names = [x["name"] for x in data["results"]]
            invest_vals = [x["investment_value"] for x in data["results"]]
            liquid_vals = [x["liquidity"] for x in data["results"]]
            interest_vals = [x["interest_saved"] for x in data["results"]]

            fig = go.Figure()
            fig.add_bar(name="Investment Value", x=names, y=invest_vals)
            fig.add_bar(name="Liquidity", x=names, y=liquid_vals)
            fig.add_bar(name="Interest Saved", x=names, y=interest_vals)
            fig.update_layout(barmode="group", xaxis_title="Scenario", yaxis_title="Dollars")
            st.plotly_chart(fig, use_container_width=True)

            # Narratives
            st.subheader("Narratives")
            for n in data["narratives"]:
                st.info(n)
