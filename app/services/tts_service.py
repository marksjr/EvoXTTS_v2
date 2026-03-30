import asyncio
import logging
import os
import threading
from typing import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from app.engines.xtts_engine import XTTSEngine
from app.core.config import DEVICE
from app.utils.audio import numpy_to_mp3_bytes, numpy_to_wav_bytes, numpy_to_mp3_chunk

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1 if DEVICE == "cuda" else max(2, (os.cpu_count() or 2) // 2))


class TTSService:
    """Evo XTTS V2 TTS service."""

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
        self._gpu_lock = threading.Lock()
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

    def preload_voices_background(self):
        self._engine.preload_voices_background()

    def get_supported_languages(self) -> list[dict]:
        return self._engine.get_supported_languages()

    def get_default_voice(self) -> str:
        return self._engine.get_default_voice()

    def validate_voice(self, voice: str) -> bool:
        return self._engine.validate_voice(voice)

    def validate_language(self, language: str) -> bool:
        return self._engine.validate_language(language)

    async def generate(self, text: str, voice: str, language: str, speed: float, fmt: str,
                       emotion: str | None = None) -> bytes:
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            _executor,
            lambda: self._synthesize_locked(text, voice, language, speed, emotion),
        )
        if fmt == "wav":
            return numpy_to_wav_bytes(audio)
        return numpy_to_mp3_bytes(audio)

    async def generate_stream(self, text: str, voice: str, language: str, speed: float,
                              emotion: str | None = None) -> AsyncGenerator[bytes, None]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        error_holder: list[Exception] = []

        def worker():
            try:
                for chunk in self._synthesize_stream_locked(text, voice, language, speed, emotion):
                    mp3_chunk = numpy_to_mp3_chunk(chunk)
                    loop.call_soon_threadsafe(queue.put_nowait, mp3_chunk)
            except Exception as exc:
                error_holder.append(exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        loop.run_in_executor(_executor, worker)

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

        if error_holder:
            raise error_holder[0]

    def _synthesize_locked(self, text: str, voice: str, language: str, speed: float, emotion: str | None = None):
        if DEVICE != "cuda":
            return self._engine.synthesize(text, voice, language, speed, emotion)
        with self._gpu_lock:
            return self._engine.synthesize(text, voice, language, speed, emotion)

    def _synthesize_stream_locked(self, text: str, voice: str, language: str, speed: float, emotion: str | None = None):
        if DEVICE != "cuda":
            yield from self._engine.synthesize_stream(text, voice, language, speed, emotion)
            return
        with self._gpu_lock:
            yield from self._engine.synthesize_stream(text, voice, language, speed, emotion)


tts_service = TTSService()
