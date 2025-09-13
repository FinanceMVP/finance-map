from typing import List, Dict, Any

def format_currency(amount: float) -> str:
    return f"${amount:,.0f}"

def build_narratives(payload: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
    narratives: List[str] = []

    debts = payload.get("debts", [])
    if debts:
        narratives.append(f"📌 You entered {len(debts)} debt account(s):")
        for d in debts:
            cat = d.get("category", "unknown").replace("_", " ").title()
            narratives.append(
                f"• {cat}: {format_currency(d.get('balance',0))} at {d.get('apr',0):.2f}% APR (min {format_currency(d.get('min_payment',0))})"
                + (f"; adds {format_currency(d.get('monthly_spend',0))}/mo" if d.get('monthly_spend',0) else "")
            )
    else:
        narratives.append("📌 No debts entered.")

    if payload.get("months"):
        narratives.append(f"⏳ You provided a {payload['months']}-month planning horizon.")
    else:
        if results:
            narratives.append(f"🧭 No timeline provided — we estimated a {results[0].get('timeline_used')} month horizon.")

    for r in results:
        name = r.get("name")
        alloc = r.get("allocations", {})
        if name == "Pay Debt":
            narratives.append(
                f"🎯 Debt-first: Apply {format_currency(alloc.get('lump_to_debt',0))} lump and {format_currency(alloc.get('monthly_to_debt',0))}/mo to debt. "
                f"Estimated debt-free in {r.get('time_to_debt_free_months')} months and interest saved ≈ {format_currency(r.get('interest_saved',0))}."
            )
        elif name == "Invest":
            narratives.append(
                f"📈 Invest-first: Put {format_currency(alloc.get('lump_to_invest',0))} lump and {format_currency(alloc.get('monthly_to_invest',0))}/mo into investments. "
                f"Projected portfolio ≈ {format_currency(r.get('investment_value',0))}."
            )
        elif name == "Save":
            narratives.append(
                f"💰 Emergency-fund-first: Allocate {format_currency(alloc.get('lump_to_ef',0))} lump and {format_currency(alloc.get('monthly_to_ef',0))}/mo to emergency savings. "
                f"Projected EF balance ≈ {format_currency(r.get('liquidity',0))}."
            )
        elif name == "Hybrid":
            narratives.append(
                f"⚖️ Hybrid (weighted by your assessment): Lump — {format_currency(alloc.get('lump_debt',0))} to debt, {format_currency(alloc.get('lump_invest',0))} to invest, {format_currency(alloc.get('lump_ef',0))} to EF. "
                f"Monthly — {format_currency(alloc.get('monthly_to_debt',0))} to debt, {format_currency(alloc.get('monthly_to_invest',0))} to invest, {format_currency(alloc.get('monthly_to_ef',0))} to EF. "
                f"Debt-free in {r.get('time_to_debt_free_months')} months; investments ≈ {format_currency(r.get('investment_value',0))}; EF ≈ {format_currency(r.get('liquidity',0))}."
            )
        elif name == "Debt + EF Goal":
            narratives.append(
                f"🛡️ Debt + EF Goal: Lump — {format_currency(alloc.get('lump_debt',0))} to debt, {format_currency(alloc.get('lump_ef',0))} to EF. "
                f"Monthly — {format_currency(alloc.get('monthly_to_debt',0))} to debt, {format_currency(alloc.get('monthly_to_ef',0))} to EF. "
                f"Debt-free in {r.get('time_to_debt_free_months')} months; EF projected ≈ {format_currency(r.get('liquidity',0))}."
            )

    recommended = None
    for r in results:
        if r.get("name") == "Debt + EF Goal" and r.get("liquidity",0) >= payload.get("emergency_fund_goal",0):
            recommended = "Debt + EF Goal"
            break
    if not recommended:
        best_score = -1
        best_name = None
        for r in results:
            score = r.get("investment_value",0) + r.get("liquidity",0) + r.get("interest_saved",0)
            if score > best_score:
                best_score = score
                best_name = r.get("name")
        recommended = best_name or "Hybrid"
    narratives.append(f"💡 Recommended: {recommended} based on your inputs and priorities.")

    return narratives
