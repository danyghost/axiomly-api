from pathlib import Path
from fastapi import FastAPI, Depends
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from web.api.routers import locations, predict, health
from core.services.city_region_mapper import CityRegionMapper
from core.services.model_registry import ModelRegistry

from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.db.session import engine, get_db

BASE_DIR = Path(__file__).resolve().parents[2]  # корень проекта (AxiomlyAPI)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - ничего не делаем пока
    yield
    # Shutdown - закрываем пул соединений
    await engine.dispose()
app = FastAPI(title="AxiomlyAPI", lifespan=lifespan)

@app.get("/test-db")
async def test_db(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(1))
    return {"status": "DB работает!", "result": result.scalar()}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup():
    print("\n=== Запуск AxiomlyAPI ===")
    app.state.city_mapper = CityRegionMapper(str(BASE_DIR / "config" / "regions.json"))
    print(f"Загружено регионов: {len(app.state.city_mapper.region_to_cities)}")
    app.state.models = ModelRegistry.load_from_disk(str(BASE_DIR / "models"))

app.include_router(locations.router, prefix="/api", tags=["Locations"])
app.include_router(predict.router, prefix="/api", tags=["Predict"])
app.include_router(health.router, prefix="/api", tags=["Health"])

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

@app.get("/")
def index():
    return FileResponse(str(BASE_DIR / "web" / "templates" / "index.html"))

if __name__ == "__main__":
    uvicorn.run(
        "web.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["web", "core"]
    )