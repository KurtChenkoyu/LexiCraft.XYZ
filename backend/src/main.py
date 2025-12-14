"""
FastAPI Main Application Entry Point

LexiCraft API V8.1 - Survey Engine Backend with FSRS A/B Testing
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from src.api import survey_router
from src.api.deposits import router as deposits_router
from src.api import onboarding
from src.api import users as users_router
from src.api import testimonials as testimonials_router
from src.api import verification as verification_router
from src.api import analytics as analytics_router
from src.api import mcq as mcq_router
from src.api import dashboard as dashboard_router
from src.api import learner_profile as learner_profile_router
from src.api import coach_profile as coach_profile_router
from src.api import goals as goals_router
from src.api import leaderboards as leaderboards_router
from src.api import notifications as notifications_router
from src.api import words as words_router
from src.api import mine as mine_router
from src.api import sync as sync_router
from src.api import pipeline as pipeline_router
from src.api import currencies as currencies_router
from src.api import items as items_router

app = FastAPI(
    title="LexiCraft API V8.1",
    description="LexiCraft Survey Engine with Progressive Survey Model (PSM) and FSRS A/B Testing",
    version="8.1"
)

# Request logging middleware (for debugging batch endpoint)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if "/api/v1/mcq/submit-batch" in str(request.url.path):
        print(f"🔍 [MIDDLEWARE] {request.method} {request.url.path} - Received batch request")
    try:
        response = await call_next(request)
        if "/api/v1/mcq/submit-batch" in str(request.url.path):
            print(f"🔍 [MIDDLEWARE] {request.method} {request.url.path} - Response status: {response.status_code}")
        return response
    except Exception as e:
        if "/api/v1/mcq/submit-batch" in str(request.url.path):
            print(f"🔍 [MIDDLEWARE] ERROR in batch endpoint: {e}")
        raise

# CORS (Allow frontend access)
# For development: allow all origins without credentials (CORS spec requirement)
# For production: specify exact origins: ["http://localhost:3000", "https://yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=False,  # Can't use True with "*" origins per CORS spec
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request validation error handler (catches Pydantic validation errors)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with CORS headers."""
    error_detail = exc.errors()
    print(f"VALIDATION ERROR: {error_detail}")
    print(f"Request path: {request.url.path}")
    print(f"Request method: {request.method}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
)

# Global exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions and ensure CORS headers are present."""
    error_detail = str(exc)
    traceback_str = traceback.format_exc()
    
    # Log the full error for debugging
    print(f"ERROR: {error_detail}")
    print(f"TRACEBACK: {traceback_str}")
    print(f"Request path: {request.url.path}")
    print(f"Request method: {request.method}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_detail,
            "type": type(exc).__name__,
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Register Routers
app.include_router(survey_router)  # Mount the survey endpoints
app.include_router(deposits_router)  # Mount the deposits endpoints
app.include_router(onboarding.router)  # Mount the onboarding endpoints
app.include_router(users_router.router)  # Mount the users endpoints
app.include_router(testimonials_router.router)  # Mount the testimonials endpoints (PSM)
app.include_router(verification_router.router)  # Mount the verification/spaced repetition endpoints
app.include_router(analytics_router.router)  # Mount the analytics endpoints (algorithm A/B testing)
app.include_router(mcq_router.router)  # Mount the MCQ adaptive selection endpoints
app.include_router(dashboard_router.router)  # Mount the dashboard endpoints
app.include_router(learner_profile_router.router)  # Mount the learner profile endpoints (gamified)
app.include_router(coach_profile_router.router)  # Mount the coach/parent profile endpoints (analytics)
app.include_router(goals_router.router)  # Mount the goals endpoints
app.include_router(leaderboards_router.router)  # Mount the leaderboard endpoints
app.include_router(notifications_router.router)  # Mount the notification endpoints
app.include_router(words_router.router)  # Mount the words endpoints
app.include_router(mine_router.router)  # Mount the mine endpoints
app.include_router(sync_router.router)  # Mount the sync endpoints (offline-first)
app.include_router(pipeline_router.router)  # Mount the pipeline status/control endpoints
app.include_router(currencies_router.router)  # Mount the currencies endpoints (three-currency economy)
app.include_router(items_router.router)  # Mount the items/building endpoints


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "8.1"}


@app.get("/health")
def health():
    """Detailed health check endpoint."""
    return {
        "status": "ok",
        "version": "8.1",
        "service": "LexiCraft Survey API",
        "features": [
            "Progressive Survey Model",
            "Warm-Start",
            "Testimonials",
            "FSRS A/B Testing",
            "SM-2+ Algorithm",
            "Spaced Repetition",
            "MCQ Adaptive Selection",
            "MCQ Quality Tracking",
            "Gamification System",
            "Achievements & Levels",
            "Goals & Leaderboards",
            "Notifications",
            "Offline-First Sync",
            "VocabularyStore (In-Memory)",
            "Pipeline Management (Auto-restart)",
        ]
    }

