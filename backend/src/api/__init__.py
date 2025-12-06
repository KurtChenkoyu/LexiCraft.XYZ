"""
API package for LexiCraft backend.

Contains FastAPI routers and endpoints.
"""

from .survey import router as survey_router
from .deposits import router as deposits_router

__all__ = ["survey_router", "deposits_router"]

