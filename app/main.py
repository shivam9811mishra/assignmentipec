import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.seed_data import seed_initial_data
from app.routers import cameras, analytics, watchlist, alerts, stats, ws

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        try:
            seed_initial_data(db)
        except Exception as e:
            print(f"Error seeding initial data: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(watchlist.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(stats.router, prefix=settings.API_V1_PREFIX)
app.include_router(ws.router)

if os.path.exists(settings.STATIC_DIR):
    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

    assets_dir = settings.STATIC_DIR / "assets"
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def index_view():
    index_file = settings.STATIC_DIR / "index.html"
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
