from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import analytics, attendances, health
from app.database.base import Base
from app.database.connection import engine
from app.models import Attendance, Classification, Routing  # noqa: F401

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AtendeAI API",
    description="API de classificação e encaminhamento de atendimentos.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(health.router)
app.include_router(attendances.router)
app.include_router(analytics.router)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets", check_dir=False), name="assets")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
