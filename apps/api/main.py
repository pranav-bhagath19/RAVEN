"""
RAVEN FastAPI Gateway Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import get_settings
from apps.api.exceptions import register_exception_handlers
from apps.api.middleware import RequestCorrelationMiddleware
from apps.api.routes import health, intelligence, operations, policies, webhooks

settings = get_settings()

app = FastAPI(
    title="RAVEN — Revenue-aware Autonomous Verification & ENgine API",
    description="Production-shaped API gateway for Razorpay webhook ingestion, autonomous revenue recovery, and control plane operational telemetry.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach request correlation middleware
app.add_middleware(RequestCorrelationMiddleware)

# Attach CORS middleware with production settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register production exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(operations.router)
app.include_router(policies.router)
app.include_router(intelligence.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
