# questions_repo.py
"""
Repository of financial well-being questions.
Based on CFPB framework: Control, Capacity, Resilience, Goals.
Used for periodic follow-up assessments.
"""

import random

FOLLOWUP_QUESTIONS = [
    # --- CONTROL (1–25) ---
    {"id": "q1", "text": "How often do you feel in control of your day-to-day finances?"},
    {"id": "q2", "text": "Do you track your expenses regularly?"},
    {"id": "q3", "text": "How confident are you in paying bills on time?"},
    {"id": "q4", "text": "Do you know your total monthly expenses?"},
    {"id": "q5", "text": "How often do you stick to a budget?"},
    {"id": "q6", "text": "Do you feel anxious when thinking about your finances?"},
    {"id": "q7", "text": "Do you know your current credit score?"},
    {"id": "q8", "text": "How often do you review your credit report?"},
    {"id": "q9", "text": "Do you pay more than the minimum on credit cards?"},
    {"id": "q10", "text": "Do you feel you have too much debt?"},
    {"id": "q11", "text": "Do you know the interest rates on your debts?"},
    {"id": "q12", "text": "How often do you avoid late fees?"},
    {"id": "q13", "text": "Do you regularly check your bank balances?"},
    {"id": "q14", "text": "Do you monitor your spending on subscriptions?"},
    {"id": "q15", "text": "Do you automate bill payments?"},
    {"id": "q16", "text": "Do you feel confident about managing multiple debts?"},
    {"id": "q17", "text": "Do you avoid overdrawing your accounts?"},
    {"id": "q18", "text": "How often do you compare financial products before choosing one?"},
    {"id": "q19", "text": "Do you feel organized in managing your finances?"},
    {"id": "q20", "text": "Do you use financial apps or tools to manage money?"},
    {"id": "q21", "text": "Do you regularly update financial goals?"},
    {"id": "q22", "text": "How often do you review monthly statements?"},
    {"id": "q23", "text": "Do you keep financial documents organized?"},
    {"id": "q24", "text": "Do you track net worth over time?"},
    {"id": "q25", "text": "Do you regularly evaluate spending priorities?"},

    # --- CAPACITY (26–50) ---
    {"id": "q26", "text": "Do you feel you have enough income to cover basic expenses?"},
    {"id": "q27", "text": "Do you have money left at the end of the month?"},
    {"id": "q28", "text": "How often do you adjust spending when income changes?"},
    {"id": "q29", "text": "Do you feel your job provides stable income?"},
    {"id": "q30", "text": "Do you earn enough to cover desired lifestyle?"},
    {"id": "q31", "text": "Do you regularly negotiate bills or expenses?"},
    {"id": "q32", "text": "Do you track side income sources?"},
    {"id": "q33", "text": "Do you save a portion of every paycheck?"},
    {"id": "q34", "text": "Do you have financial flexibility to handle extra expenses?"},
    {"id": "q35", "text": "Do you set aside money for taxes if self-employed?"},
    {"id": "q36", "text": "Do you plan for irregular expenses (like insurance or holidays)?"},
    {"id": "q37", "text": "Do you have predictable monthly cash flow?"},
    {"id": "q38", "text": "Do you feel confident about increasing your income in the future?"},
    {"id": "q39", "text": "Do you manage variable income effectively?"},
    {"id": "q40", "text": "Do you save at least 10% of income?"},
    {"id": "q41", "text": "Do you invest regularly for the long term?"},
    {"id": "q42", "text": "Do you avoid relying on credit for daily expenses?"},
    {"id": "q43", "text": "Do you track discretionary vs. non-discretionary expenses?"},
    {"id": "q44", "text": "Do you balance short-term wants with long-term needs?"},
    {"id": "q45", "text": "Do you compare income against rising living costs?"},
    {"id": "q46", "text": "Do you have access to affordable healthcare?"},
    {"id": "q47", "text": "Do you use employer benefits effectively?"},
    {"id": "q48", "text": "Do you understand your tax situation well?"},
    {"id": "q49", "text": "Do you feel you are building wealth over time?"},
    {"id": "q50", "text": "Do you anticipate income growth in your field?"},

    # --- RESILIENCE (51–75) ---
    {"id": "q51", "text": "Do you have an emergency fund?"},
    {"id": "q52", "text": "How many months of expenses can you cover with savings?"},
    {"id": "q53", "text": "Do you have insurance for major risks (health, auto, home)?"},
    {"id": "q54", "text": "Do you have disability insurance?"},
    {"id": "q55", "text": "Do you have life insurance for dependents?"},
    {"id": "q56", "text": "Do you have a plan for unexpected income loss?"},
    {"id": "q57", "text": "Do you keep some savings liquid for emergencies?"},
    {"id": "q58", "text": "Do you rely on credit during emergencies?"},
    {"id": "q59", "text": "Do you diversify income sources?"},
    {"id": "q60", "text": "Do you have access to low-interest borrowing options?"},
    {"id": "q61", "text": "Do you avoid cashing out retirement for emergencies?"},
    {"id": "q62", "text": "Do you have a financial safety net from family or friends?"},
    {"id": "q63", "text": "Do you update emergency savings goals regularly?"},
    {"id": "q64", "text": "Do you adjust savings when expenses rise?"},
    {"id": "q65", "text": "Do you use credit responsibly during unexpected events?"},
    {"id": "q66", "text": "Do you have backup childcare or support networks?"},
    {"id": "q67", "text": "Do you have a will or estate plan?"},
    {"id": "q68", "text": "Do you avoid borrowing against your home for emergencies?"},
    {"id": "q69", "text": "Do you keep at least one credit card unused for emergencies?"},
    {"id": "q70", "text": "Do you know where to reduce expenses quickly if needed?"},
    {"id": "q71", "text": "Do you feel resilient in the face of financial shocks?"},
    {"id": "q72", "text": "Do you monitor economic risks to your household?"},
    {"id": "q73", "text": "Do you have a plan for large medical bills?"},
    {"id": "q74", "text": "Do you have savings for home or car repairs?"},
    {"id": "q75", "text": "Do you avoid relying solely on high-interest credit in crises?"},

    # --- GOALS (76–100) ---
    {"id": "q76", "text": "Do you set short-term financial goals?"},
    {"id": "q77", "text": "Do you set long-term financial goals?"},
    {"id": "q78", "text": "Do you track progress toward financial goals?"},
    {"id": "q79", "text": "Do you regularly save for retirement?"},
    {"id": "q80", "text": "Do you know how much you need for retirement?"},
    {"id": "q81", "text": "Do you have education savings goals (for self or dependents)?"},
    {"id": "q82", "text": "Do you plan for homeownership?"},
    {"id": "q83", "text": "Do you plan for travel or leisure spending responsibly?"},
    {"id": "q84", "text": "Do you save for children’s expenses?"},
    {"id": "q85", "text": "Do you feel on track with retirement planning?"},
    {"id": "q86", "text": "Do you adjust goals when income changes?"},
    {"id": "q87", "text": "Do you feel motivated by financial goals?"},
    {"id": "q88", "text": "Do you prioritize saving over spending?"},
    {"id": "q89", "text": "Do you save for large planned purchases?"},
    {"id": "q90", "text": "Do you balance debt repayment with long-term goals?"},
    {"id": "q91", "text": "Do you review goals annually?"},
    {"id": "q92", "text": "Do you use milestones to measure goal progress?"},
    {"id": "q93", "text": "Do you celebrate financial achievements?"},
    {"id": "q94", "text": "Do you create action plans for goals?"},
    {"id": "q95", "text": "Do you regularly re-prioritize goals?"},
    {"id": "q96", "text": "Do you use automatic transfers toward goals?"},
    {"id": "q97", "text": "Do you avoid sacrificing long-term goals for short-term wants?"},
    {"id": "q98", "text": "Do you review investments to align with goals?"},
    {"id": "q99", "text": "Do you feel confident about achieving your financial goals?"},
    {"id": "q100", "text": "Do you share financial goals with your household?"}
]

def get_followup_questions(n: int = 3):
    """Return n random follow-up questions from the repository."""
    return random.sample(FOLLOWUP_QUESTIONS, min(n, len(FOLLOWUP_QUESTIONS)))

