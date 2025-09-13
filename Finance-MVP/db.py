from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine, Session
import json

_engine = create_engine("sqlite:///finance_mvp.db")

class ScenarioRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    inputs_json: str
    results_json: str
    narratives_json: str

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "inputs": json.loads(self.inputs_json),
            "results": json.loads(self.results_json),
            "narratives": json.loads(self.narratives_json),
        }

def get_session():
    with Session(_engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(_engine)
