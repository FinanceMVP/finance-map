import streamlit as st
import pandas as pd
from typing import List, Literal
from pydantic import BaseModel, Field
import plotly.graph_objects as go
import random

# -----------------------------
# Embedded Question Repository
# -----------------------------
BASELINE_QUESTIONS = [
    "I could handle a major unexpected expense.",
    "I can enjoy life because of the way I'm managing my money.",
    "I am securing my financial future.",
    "Because of my money situation, I feel like I will never have the things I want in life.",
    "I can make ends meet without too much difficulty.",
    "Giving a gift for a wedding, birthday, or other occasion would put a strain on my finances for the month.",
    "I have money left over at the end of the month.",
    "My finances control my life.",
    "I could cover expenses for three months if I lost my income.",
    "I am confident I am on track with my long-term financial goals."
]

FOLLOW_UP_QUESTIONS = [
    "I pay my bills on time without reminders.",
    "I have a plan for how I will pay off my debt.",
    "I regularly save money for emergencies.",
    "I know how much money I need for retirement.",
    "I review my budget or spending plan regularly.",
    "I feel confident making financial decisions.",
    "I avoid using credit cards for daily expenses.",
    "I track my investments and retirement accounts.",
    "I have a clear understanding of my insurance needs.",
    "I regularly discuss finances with my partner or family."
] + [f"Follow-up Q{i}" for i in range(11, 101)]  # placeholders

# -----------------------------
# Session State Setup
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "score" not in st.session_state:
    st.session_state.score = None
if "inputs" not in st.session_state:
    st.session_state.inputs = {}

# -----------------------------
# Helper Functions
# -----------------------------
def calculate_score(responses):
    if not responses:
        return 50, "Moderate"
    avg = sum(responses.values()) / len(responses)
    score = int(round(avg * 20))  # 0–100 scale
    label = (
        "Excellent" if score >= 80 else
        "Good" if score >= 65 else
        "Moderate" if score >= 50 else
        "Low"
    )
    return score, label

def format_currency(val):
    return f"${val:,.0f}"

# -----------------------------
# Pages
# -----------------------------
def page_welcome():
    st.title("💸 Finance MVP")
    st.subheader("Your personal finance and scenario tool")
    st.write("Welcome! This app helps you evaluate your financial well-being and explore scenarios "
             "for debt payoff, saving, and investing.")
    if st.button("Continue ➡️"):
        st.session_state.page = "about_questions"

def page_about_questions():
    st.header("📋 About the Questions")
    st.write("We start with 10 baseline questions developed by the **Consumer Financial Protection Bureau (CFPB)** "
             "to measure financial well-being. These are answered on a **0–5 scale**, where 0 = least likely and "
             "5 = most likely. Every few months, you’ll see 2–3 follow-up questions to refine your score.")
    st.markdown("### Scale Guide")
    st.write("0 = Not at all likely\n\n5 = Completely likely")
    if st.button("Start Questions ➡️"):
        st.session_state.page = "questions"

def page_questions():
    st.header("📝 Baseline Financial Well-being Questions")
    st.write("Please answer all 10 questions on a scale from 0–5.")
    for i, q in enumerate(BASELINE_QUESTIONS):
        st.session_state.responses[q] = st.slider(q, 0, 5, st.session_state.responses.get(q, 0))
    if st.button("Submit Responses"):
        score, label = calculate_score(st.session_state.responses)
        st.session_state.score = (score, label)
        st.session_state.page = "score"

def page_score():
    score, label = st.session_state.score
    st.header("📊 Your Financial Well-being Score")
    st.success(f"Your score is {score} ({label})")
    st.write("This score reflects your overall financial well-being based on your answers.")
    if st.button("Continue to Instructions ➡️"):
        st.session_state.page = "instructions"

def page_instructions():
    st.header("📘 Instructions for Inputs")
    st.markdown("""
    Before running scenarios, here’s what you’ll need to provide:
    - **Lump sum cash**: Any one-time cash you can allocate now.
    - **Monthly free cash**: Amount available each month for debt, savings, or investing.
    - **Emergency fund goal**: Target cushion of cash for unexpected expenses.
    - **Expected return on investment (ROI)**: Annual growth rate you expect from investments.
    - **Debt details**: Balances, interest rates, and payments for each debt.
    """)
    if st.button("Enter Inputs ➡️"):
        st.session_state.page = "inputs"

def page_inputs():
    st.header("💵 Financial Inputs")
    # Lump sum and monthly
    lump_sum = st.selectbox("Lump sum available", ["None", 1000, 5000, 10000, 20000], index=2)
    monthly_cash = st.selectbox("Monthly free cash", ["None", 100, 250, 500, 1000], index=2)
    ef_goal = st.selectbox("Emergency Fund Goal", ["None", "1 month expenses", "3 months expenses",
                                                   "6 months expenses", "12 months expenses"], index=2)
    exp_return = st.selectbox("Expected ROI", ["None", "3% (conservative)", "5% (moderate)", "7% (aggressive)"], index=2)
    months = st.selectbox("Timeline (months)", ["None", 12, 24, 36, 60, 120], index=3)

    # Debt section
    st.subheader("Debts")
    debt_entries = []
    for i in range(3):  # allow up to 3 debts
        with st.expander(f"Debt {i+1}"):
            debt_type = st.selectbox("Debt type", ["Credit Card", "Auto Loan", "Student Loan", "Mortgage", "Other"], key=f"type{i}")
            balance = st.number_input("Balance", min_value=0, value=5000, key=f"bal{i}")
            apr = st.number_input("APR (%)", min_value=0.0, max_value=100.0, value=18.0, step=0.1, key=f"apr{i}")
            minpay = st.number_input("Minimum Payment", min_value=0, value=100, key=f"pay{i}")
            revolving = st.selectbox("Revolving (for credit cards)?", ["No", "Yes"], key=f"rev{i}")
            debt_entries.append({"type": debt_type, "balance": balance, "apr": apr, "minpay": minpay, "revolving": revolving})

    if st.button("Run Scenarios ➡️"):
        st.session_state.inputs = {
            "lump_sum": 0 if lump_sum == "None" else lump_sum,
            "monthly_cash": 0 if monthly_cash == "None" else monthly_cash,
            "ef_goal": ef_goal,
            "exp_return": exp_return,
            "months": 60 if months == "None" else months,
            "debts": debt_entries
        }
        st.session_state.page = "scenarios"

def page_scenarios():
    st.header("📊 Scenario Results & Recommendations")

    # Fake results for demo
    scenarios = {
        "Debt First": {"why": "You have high-interest debt, so paying it off first saves you the most.", "score": 90},
        "Invest First": {"why": "Investing early compounds wealth, but debt remains a burden.", "score": 70},
        "Emergency Fund First": {"why": "Building cash reserves ensures stability before tackling debt or investing.", "score": 80},
        "Hybrid": {"why": "Splitting funds balances risk and growth.", "score": 85}
    }

    # Best option
    best = max(scenarios, key=lambda x: scenarios[x]["score"])
    st.markdown(f"""
        <div style="background-color:#d4edda;padding:15px;border-radius:10px;margin-bottom:10px;">
        <h4>✅ Recommended: {best}</h4>
        <p>{scenarios[best]["why"]}</p>
        </div>
    """, unsafe_allow_html=True)

    # Others
    for k, v in scenarios.items():
        if k == best: continue
        st.markdown(f"""
            <div style="background-color:#f8f9fa;padding:15px;border-radius:10px;margin-bottom:10px;">
            <h4>{k}</h4>
            <p>{v["why"]}</p>
            </div>
        """, unsafe_allow_html=True)

    st.subheader("Allocation Comparison (Demo Data)")
    df = pd.DataFrame({
        "Scenario": ["Debt First", "Invest First", "Emergency Fund First", "Hybrid"],
        "Allocation": ["100% to debt", "100% to invest", "100% to EF", "Split across all"]
    })
    st.table(df)

# -----------------------------
# Page Router
# -----------------------------
if st.session_state.page == "welcome":
    page_welcome()
elif st.session_state.page == "about_questions":
    page_about_questions()
elif st.session_state.page == "questions":
    page_questions()
elif st.session_state.page == "score":
    page_score()
elif st.session_state.page == "instructions":
    page_instructions()
elif st.session_state.page == "inputs":
    page_inputs()
elif st.session_state.page == "scenarios":
    page_scenarios()
