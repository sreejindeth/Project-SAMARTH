from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import load_config
from .data_manager import DataManager
from .question_parser import parse_question
from .core import QueryEngine
from . import plugins  # Triggers plugin auto-registration


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    tables: list
    citations: list
    debug: dict | None = None


app = FastAPI(title="Project Samarth Prototype", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

config = load_config()
data_manager = DataManager(config)
engine = QueryEngine(data_manager)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    """
    Process a natural language question using the plugin architecture.

    The QueryEngine automatically routes to the appropriate plugin based on intent.
    """
    parsed = parse_question(payload.question)

    try:
        # Execute query using the plugin engine
        result = engine.execute_query(parsed.intent, parsed.params)
        return AskResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/refresh")
def refresh():
    """Refresh data from data.gov.in API."""
    data_manager.load_dataset("agriculture", force_refresh=True)
    data_manager.load_dataset("rainfall", force_refresh=True)
    return {"status": "reloaded"}
