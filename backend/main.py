from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Créer les tables si elles n'existent pas (dev only, prod use alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")
    yield
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered dropshipping company operating system",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}
