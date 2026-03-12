"""SellScope API - Stock Contributor Intelligence Platform"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
import structlog

from app.core.config import settings
from app.core.database import init_db
from app.routers import (
    auth,
    keywords,
    opportunities,
    portfolios,
    scraper,
    briefs,
    webhooks,
    analytics,
    assets,
    insights,
)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SellScope API", version=settings.VERSION)
    await init_db()
    yield
    logger.info("Shutting down SellScope API")


app = FastAPI(
    title="SellScope API",
    description="Stock Contributor Intelligence Platform - The Bloomberg Terminal for Stock Contributors",
    version=settings.VERSION,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(keywords.router, prefix="/keywords", tags=["Keywords"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
app.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
app.include_router(scraper.router, prefix="/scraper", tags=["Scraper"])
app.include_router(briefs.router, prefix="/briefs", tags=["AI Briefs"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(assets.router, prefix="/assets", tags=["Assets"])
app.include_router(insights.router, prefix="/insights", tags=["Insights"])


@app.get("/")
async def root():
    return {
        "name": "SellScope API",
        "version": settings.VERSION,
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
