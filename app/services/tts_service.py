import asyncio
import logging
from typing import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from app.engines.xtts_engine import XTTSEngine
from app.core.config import DEVICE
from app.utils.audio import numpy_to_mp3_bytes, numpy_to_wav_bytes, numpy_to_mp3_chunk

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


class TTSService:
    """Serviço de TTS Evo XTTS V2."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._engine = XTTSEngine()
        self._initialized = True

    def load_model(self):
        self._engine.load()

    @property
    def model_loaded(self) -> bool:
        return self._engine.is_loaded

    @property
    def device(self) -> str:
        return DEVICE

    def get_voices(self) -> list[dict]:
        return self._engine.get_voices()

    def get_default_voice(self) -> str:
        return self._engine.get_default_voice()

    def validate_voice(self, voice: str) -> bool:
        return self._engine.validate_voice(voice)

    async def generate(self, text: str, voice: str, speed: float, fmt: str,
                       emotion: str | None = None) -> bytes:
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            _executor,
            lambda: self._engine.synthesize(text, voice, speed, emotion),
        )
        if fmt == "wav":
            return numpy_to_wav_bytes(audio)
        return numpy_to_mp3_bytes(audio)

    async def generate_stream(self, text: str, voice: str, speed: float,
                              emotion: str | None = None) -> AsyncGenerator[bytes, None]:
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            _executor,
            lambda: list(self._engine.synthesize_stream(text, voice, speed, emotion)),
        )
        for chunk in chunks:
            yield numpy_to_mp3_chunk(chunk)


tts_service = TTSService()
