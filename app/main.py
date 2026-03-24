import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.api.routes import router
from app.services.tts_service import tts_service
from app.core.config import HOST, PORT, DEVICE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
PROJECT_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando Evo XTTS V2 API (device: {DEVICE})")
    tts_service.load_model()
    voices = tts_service.get_voices()
    logger.info(f"API pronta — {len(voices)} voz(es) carregada(s)")
    yield
    logger.info("Encerrando API TTS")


app = FastAPI(
    title="Evo XTTS V2 API",
    description="API local de Text-to-Speech pt-BR usando Evo XTTS V2 com clonagem de voz",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(PROJECT_DIR / "ui" / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False, workers=1)

