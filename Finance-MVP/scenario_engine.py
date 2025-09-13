from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
import math

DebtCategory = Literal["credit_card", "student_loan", "auto", "mortgage", "personal", "other"]

class Debt(BaseModel):
    category: DebtCategory
    balance: float = Field(..., ge=0)
    apr: float = Field(..., ge=0, le=200)
    min_payment: float = Field(..., ge=0)
    monthly_spend: float = Field(0.0, ge=0.0)

class ScenarioInput(BaseModel):
    lump_sum: float = Field(0.0, ge=0)
    monthly_free_cash: float = Field(0.0, ge=0)
    debts: List[Debt] = Field(default_factory=list)
    invest_return: float = Field(7.0, ge=-100, le=100)
    emergency_fund_goal: float = Field(0.0, ge=0)
    months: Optional[int] = Field(None, ge=1, le=360)
    assumed_happiness: int = Field(60, ge=0, le=100)
    weights: Optional[Dict[str, float]] = None

class ScenarioResult(BaseModel):
    name: Literal["Pay Debt", "Invest", "Save", "Hybrid", "Debt + EF Goal"]
    end_balance: float
    interest_saved: float
    investment_value: float
    liquidity: float
    time_to_debt_free_months: int
    timeline_used: int
    allocations: Dict[str, Any] = Field(default_factory=dict)

def _monthly_rate(apr_pct: float) -> float:
    return (apr_pct / 100.0) / 12.0

def _future_value(monthly_contrib: float, months: int, annual_return_pct: float) -> float:
    r = (annual_return_pct / 100.0) / 12.0
    fv = 0.0
    for _ in range(months):
        fv = fv * (1 + r) + monthly_contrib
    return fv

def _amortize_single(balance: float, apr_pct: float, monthly_payment: float, months: int, monthly_spend: float = 0.0):
    if balance <= 0:
        return 0.0, 0
    r = _monthly_rate(apr_pct)
    interest_paid = 0.0
    for m in range(1, months + 1):
        interest = balance * r
        interest_paid += interest
        principal_paid = max(0.0, monthly_payment - interest)
        balance = max(0.0, balance - principal_paid)
        if monthly_spend > 0:
            balance += monthly_spend
        if balance <= 0.01:
            return interest_paid, m
    return interest_paid, months

def _total_balance_and_min_payment(debts: List[Debt]):
    total_balance = sum(d.balance for d in debts)
    total_min = sum(d.min_payment for d in debts)
    return total_balance, total_min

def _estimate_timeline(inp: ScenarioInput) -> int:
    total_balance, total_min = _total_balance_and_min_payment(inp.debts)
    if total_balance > 0 and total_min > 0:
        avg_apr = sum(d.apr * d.balance for d in inp.debts) / total_balance if total_balance > 0 else 0.0
        interest_per_month = total_balance * _monthly_rate(avg_apr)
        principal_payment = max(1.0, total_min - interest_per_month)
        est_months = math.ceil(total_balance / principal_payment)
        est_months = min(max(est_months + 3, 6), 360)
        return est_months
    elif inp.emergency_fund_goal > 0 and inp.monthly_free_cash > 0:
        est_months = math.ceil(inp.emergency_fund_goal / inp.monthly_free_cash)
        return min(max(est_months, 6), 360)
    else:
        return 60

def run_scenarios(inp: ScenarioInput) -> List[Dict[str, Any]]:
    if not isinstance(inp, ScenarioInput):
        inp = ScenarioInput(**(inp if isinstance(inp, dict) else {}))

    horizon = inp.months if inp.months else _estimate_timeline(inp)

    baseline_interest = 0.0
    baseline_payoff_month = 0
    for d in inp.debts:
        i, m = _amortize_single(d.balance, d.apr, d.min_payment, horizon, monthly_spend=d.monthly_spend if d.category == "credit_card" else 0.0)
        baseline_interest += i
        baseline_payoff_month = max(baseline_payoff_month, m)

    scenarios = []

    debts_copy = [d.model_dump() for d in inp.debts]
    debts_sorted = sorted(debts_copy, key=lambda x: -x["apr"])
    lump_remaining = inp.lump_sum
    for d in debts_sorted:
        if lump_remaining <= 0:
            break
        apply = min(d["balance"], lump_remaining)
        d["balance"] = max(0.0, d["balance"] - apply)
        lump_remaining -= apply

    extra = inp.monthly_free_cash
    total_interest_pay_debt = 0.0
    payoff_months_debt = 0
    sim_debts = [dict(d) for d in debts_sorted]
    for month in range(1, horizon + 1):
        for d in sim_debts:
            if d["category"] == "credit_card" and d.get("monthly_spend", 0) > 0:
                d["balance"] += d["monthly_spend"]
        for d in sim_debts:
            if d["balance"] <= 0:
                continue
            interest = d["balance"] * _monthly_rate(d["apr"])
            d["balance"] += interest
            total_interest_pay_debt += interest
            pay = min(d["min_payment"], d["balance"])
            d["balance"] = max(0.0, d["balance"] - pay)
        rem_extra = extra
        for d in sorted(sim_debts, key=lambda x: -x["apr"]):
            if rem_extra <= 0:
                break
            if d["balance"] <= 0:
                continue
            apply = min(rem_extra, d["balance"])
            d["balance"] = max(0.0, d["balance"] - apply)
            rem_extra -= apply
        if all(d["balance"] <= 0.01 for d in sim_debts):
            payoff_months_debt = month
            break
    if payoff_months_debt == 0:
        payoff_months_debt = horizon
    alloc_pay_debt = {
        "lump_to_debt": inp.lump_sum,
        "monthly_to_debt": inp.monthly_free_cash
    }
    scenarios.append(ScenarioResult(
        name="Pay Debt",
        end_balance=0.0,
        interest_saved=max(0.0, baseline_interest - total_interest_pay_debt),
        investment_value=0.0,
        liquidity=0.0,
        time_to_debt_free_months=payoff_months_debt,
        timeline_used=horizon,
        allocations=alloc_pay_debt
    ).model_dump())

    invest_value = _future_value(inp.monthly_free_cash, horizon, inp.invest_return) + inp.lump_sum
    scenarios.append(ScenarioResult(
        name="Invest",
        end_balance=0.0,
        interest_saved=0.0,
        investment_value=invest_value,
        liquidity=0.0,
        time_to_debt_free_months=baseline_payoff_month,
        timeline_used=horizon,
        allocations={
            "lump_to_invest": inp.lump_sum,
            "monthly_to_invest": inp.monthly_free_cash
        }
    ).model_dump())

    ef_liquidity = min(inp.emergency_fund_goal, inp.lump_sum) + inp.monthly_free_cash * min(horizon, 12)
    scenarios.append(ScenarioResult(
        name="Save",
        end_balance=0.0,
        interest_saved=0.0,
        investment_value=0.0,
        liquidity=ef_liquidity,
        time_to_debt_free_months=baseline_payoff_month,
        timeline_used=horizon,
        allocations={
            "lump_to_ef": min(inp.lump_sum, inp.emergency_fund_goal),
            "monthly_to_ef": inp.monthly_free_cash
        }
    ).model_dump())

    if not inp.weights:
        return scenarios

    w = inp.weights
    total_w = max(1e-9, sum(w.get(k, 0.0) for k in ["debt", "ef", "invest"]))
    debt_share = w.get("debt", 0.0) / total_w
    ef_share = w.get("ef", 0.0) / total_w
    invest_share = w.get("invest", 0.0) / total_w

    lump_debt = inp.lump_sum * debt_share
    lump_ef = inp.lump_sum * ef_share
    lump_invest = inp.lump_sum * invest_share
    monthly_to_debt = inp.monthly_free_cash * debt_share
    monthly_to_ef = inp.monthly_free_cash * ef_share
    monthly_to_invest = inp.monthly_free_cash * invest_share

    sim_debts_h = [dict(d) for d in debts_sorted]
    rem = lump_debt
    for d in sim_debts_h:
        if rem <= 0:
            break
        apply = min(d["balance"], rem)
        d["balance"] = max(0.0, d["balance"] - apply)
        rem -= apply
    total_interest_h = 0.0
    payoff_h = 0
    for month in range(1, horizon + 1):
        for d in sim_debts_h:
            if d["category"] == "credit_card" and d.get("monthly_spend", 0) > 0:
                d["balance"] += d["monthly_spend"]
            if d["balance"] <= 0:
                continue
            interest = d["balance"] * _monthly_rate(d["apr"])
            total_interest_h += interest
            d["balance"] += interest
            pay = min(d["min_payment"], d["balance"])
            d["balance"] = max(0.0, d["balance"] - pay)
        rem_extra = monthly_to_debt
        for d in sorted(sim_debts_h, key=lambda x: -x["apr"]):
            if rem_extra <= 0:
                break
            if d["balance"] <= 0:
                continue
            apply = min(rem_extra, d["balance"])
            d["balance"] = max(0.0, d["balance"] - apply)
            rem_extra -= apply
        if all(d["balance"] <= 0.01 for d in sim_debts_h):
            payoff_h = month
            break
    if payoff_h == 0:
        payoff_h = horizon
    invest_val_h = _future_value(monthly_to_invest, horizon, inp.invest_return) + lump_invest
    liquidity_h = lump_ef + monthly_to_ef * min(horizon, 12)
    scenarios.append(ScenarioResult(
        name="Hybrid",
        end_balance=0.0,
        interest_saved=max(0.0, baseline_interest - total_interest_h),
        investment_value=invest_val_h,
        liquidity=liquidity_h,
        time_to_debt_free_months=payoff_h,
        timeline_used=horizon,
        allocations={
            "lump_debt": lump_debt,
            "lump_invest": lump_invest,
            "lump_ef": lump_ef,
            "monthly_to_debt": monthly_to_debt,
            "monthly_to_invest": monthly_to_invest,
            "monthly_to_ef": monthly_to_ef
        }
    ).model_dump())

    lump_debt_e = inp.lump_sum * debt_share
    lump_ef_e = inp.lump_sum * ef_share
    monthly_to_debt_e = inp.monthly_free_cash * debt_share
    monthly_to_ef_e = inp.monthly_free_cash * ef_share

    sim_debts_e = [dict(d) for d in debts_sorted]
    rem = lump_debt_e
    for d in sim_debts_e:
        if rem <= 0:
            break
        apply = min(d["balance"], rem)
        d["balance"] = max(0.0, d["balance"] - apply)
        rem -= apply

    total_interest_e = 0.0
    payoff_e = 0
    ef_balance = lump_ef_e
    ef_goal_month = horizon
    for month in range(1, horizon + 1):
        for d in sim_debts_e:
            if d["category"] == "credit_card" and d.get("monthly_spend", 0) > 0:
                d["balance"] += d["monthly_spend"]
        for d in sim_debts_e:
            if d["balance"] <= 0:
                continue
            interest = d["balance"] * _monthly_rate(d["apr"])
            d["balance"] += interest
            total_interest_e += interest
            pay = min(d["min_payment"], d["balance"])
            d["balance"] = max(0.0, d["balance"] - pay)
        rem_extra = monthly_to_debt_e
        for d in sorted(sim_debts_e, key=lambda x: -x["apr"]):
            if rem_extra <= 0:
                break
            if d["balance"] <= 0:
                continue
            apply = min(rem_extra, d["balance"])
            d["balance"] = max(0.0, d["balance"] - apply)
            rem_extra -= apply
        ef_balance += monthly_to_ef_e
        if ef_balance >= inp.emergency_fund_goal and ef_goal_month == horizon:
            ef_goal_month = month
        if all(d["balance"] <= 0.01 for d in sim_debts_e) and payoff_e == 0:
            payoff_e = month
        if ef_balance >= inp.emergency_fund_goal and payoff_e != 0:
            break
    if payoff_e == 0:
        payoff_e = horizon

    scenarios.append(ScenarioResult(
        name="Debt + EF Goal",
        end_balance=0.0,
        interest_saved=max(0.0, baseline_interest - total_interest_e),
        investment_value=0.0,
        liquidity=ef_balance,
        time_to_debt_free_months=payoff_e,
        timeline_used=horizon,
        allocations={
            "lump_debt": lump_debt_e,
            "lump_ef": lump_ef_e,
            "monthly_to_debt": monthly_to_debt_e,
            "monthly_to_ef": monthly_to_ef_e
        }
    ).model_dump())

    return scenarios
