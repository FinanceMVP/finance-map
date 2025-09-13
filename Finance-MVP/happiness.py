from pydantic import BaseModel, Field
from typing import List

class Question(BaseModel):
    id: str
    text: str
    weight: int = 1

class QuestionResponse(BaseModel):
    id: str
    score: int = Field(ge=1, le=5)

DEFAULT_QUESTIONS: List[Question] = [
    Question(id="emergency", text="Having an emergency fund matters more than faster debt payoff."),
    Question(id="flexibility", text="Financial flexibility (cash on hand) reduces my stress."),
]

def compute_happiness_score(responses: List[QuestionResponse]) -> int:
    if not responses:
        return 60
    avg = sum(r.score for r in responses) / len(responses)
    return int(round(avg * 20))
