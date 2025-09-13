from fastapi import FastAPI, HTTPException, Body
from typing import List, Dict, Any
from scenario_engine import ScenarioInput, run_scenarios
from narratives import build_narratives

app = FastAPI(title="Finance Scenario API", version="0.4.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/assess")
def assess(responses: List[dict]):
    if not responses:
        raise HTTPException(status_code=400, detail="You must complete the assessment.")

    # Average all answers into happiness score
    avg = sum(r["score"] for r in responses) / len(responses)
    score = int(round(avg * 20))  # CFPB scale is 0–100

    label = (
        "Excellent" if score >= 80 else
        "Good" if score >= 65 else
        "Moderate" if score >= 50 else
        "Low"
    )

    # Derive weights: simple example using 3 proxies
    weights = {"debt":0.33,"ef":0.33,"invest":0.34}
    for r in responses:
        qid = r["id"]
        s = r["score"]
        if qid in ["q1","q3","q5","q9"]:  # worry/stress questions → more debt aversion
            weights["debt"] += s * 0.05
        elif qid in ["q2","q6","q7","q8"]:  # liquidity/security → EF
            weights["ef"] += s * 0.05
        elif qid in ["q4","q10"]:  # long-term confidence/satisfaction → investing
            weights["invest"] += s * 0.05

    total = sum(weights.values()) or 1.0
    normalized = {k: round(v/total, 3) for k,v in weights.items()}

    return {"score": score, "label": label, "weights": normalized}


@app.post("/quick_assess")
def quick_assess(body: Dict[str, Any]):
    choice = body.get("choice")
    if choice not in ["debt","ef","invest"]:
        raise HTTPException(status_code=400, detail="choice must be debt, ef, or invest")
    weights = {"debt":0.33,"ef":0.33,"invest":0.33}
    weights[choice] = 0.6
    return {"score":60, "label":"Quick", "weights":weights}

@app.post("/scenarios")
def scenarios(payload: Dict[str, Any] = Body(...)):
    try:
        inp = ScenarioInput(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    results = run_scenarios(inp)
    narratives = build_narratives(inp.model_dump(), results)
    return {"inputs": inp.model_dump(), "results": results, "narratives": narratives}
