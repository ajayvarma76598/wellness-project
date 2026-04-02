from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import health_router
from app.routes.feedback_history import router
from app.routes.analyze_suggest import analyse_suggest_router
from app.db.db_connection import create_tables
load_dotenv()
create_tables()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise HTTPException(
            status_code=401,
            detail={
                "error": "API key not configured",
                "message": "The required GEMINI_API_KEY is not set in environment variables.",
                "type": "api_key_missing_error",
            },
        )
base_url = os.getenv("GEMINI_BASE_URL")
model = os.getenv("GEMINI_MODEL_NAME")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Wellbeing Coach: Personalized Mental Booster API",
    description="A Python-based AI coach that analyzes emotional cues and suggests personalized 5-minute micro-activities to reduce stress and burnout.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=api_key, base_url=base_url)

# Health check endpoint
app.include_router(health_router)

# analyse-suggest endpoint
analyse_router = analyse_suggest_router(client, model)
app.include_router(analyse_router)

#feedback and history endpoint
app.include_router(router)

