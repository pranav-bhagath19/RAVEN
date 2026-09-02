"""
RAVEN FastAPI Gateway Application Entry Point
"""

from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from apps.api.config import get_settings  # noqa: E402
from apps.api.exceptions import register_exception_handlers  # noqa: E402
from apps.api.middleware import RequestCorrelationMiddleware  # noqa: E402
from apps.api.routes import health, intelligence, operations, policies, regions, replication, webhooks  # noqa: E402



settings = get_settings()

@asynccontextmanager

async def lifespan(app: FastAPI):
    from persistence.database import init_db
    try:
        init_db()
    except Exception as e:
        import logging
        logging.getLogger("raven.api").warning(f"Startup DB init warning: {e}")
    yield

app = FastAPI(
    title="RAVEN — Revenue-aware Autonomous Verification & ENgine API",
    description="Production-shaped API gateway for Razorpay webhook ingestion, autonomous revenue recovery, and control plane operational telemetry.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
app.include_router(regions.router)
app.include_router(replication.router)


@app.get("/metrics", tags=["Observability"])
def prometheus_metrics():
    """Prometheus Scrape Endpoint for Application Metrics."""
    from fastapi.responses import PlainTextResponse
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)
