from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limiter import InMemoryRateLimitMiddleware

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Secure enterprise multi-source RAG platform with RBAC, explainability, and grounded generation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(InMemoryRateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

app.include_router(router, prefix=settings.api_prefix)
