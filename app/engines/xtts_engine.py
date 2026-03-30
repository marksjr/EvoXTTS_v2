import logging
from pathlib import Path
from contextlib import nullcontext

import numpy as np

from app.core.config import (
    CUDNN_BENCHMARK,
    DEFAULT_LANGUAGE,
    DEFAULT_VOICE,
    DEVICE,
    EMOTIONS,
    GPT_COND_CHUNK_LEN,
    GPT_COND_LEN,
    LENGTH_PENALTY,
    REPETITION_PENALTY,
    STREAM_CHUNK_SIZE,
    TEMPERATURE,
    TOP_K,
    TOP_P,
    SUPPORTED_LANGUAGES,
    TTS_HOME_DIR,
    USE_FLOAT16,
    USE_TF32,
    USE_TORCH_COMPILE,
    VOICES_DIR,
    XTTS_MODEL_NAME,
)
from app.utils.audio import crossfade_chunks, post_process, trim_silence
from app.utils.text import chunk_text, preprocess_text

logger = logging.getLogger(__name__)


class XTTSEngine:
    """Coqui Evo XTTS V2 engine with multi-language voice cloning."""

    def __init__(self):
        self._model = None
        self._loaded = False
        self._voices_dir = Path(VOICES_DIR)
        self._voice_cache: dict[str, tuple] = {}
        self._available_voices: set[str] = set()
        self._autocast_dtype = None
        self._preloading = False

    def load(self) -> None:
        if self._loaded:
            return

        import os
        import torch

        os.environ["COQUI_TOS_AGREED"] = "1"
        os.environ.setdefault("TTS_HOME", TTS_HOME_DIR)
        Path(TTS_HOME_DIR).mkdir(parents=True, exist_ok=True)

        original_load = torch.load

        def patched_load(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return original_load(*args, **kwargs)

        torch.load = patched_load

        self._install_audio_fallbacks()

        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from TTS.utils.manage import ModelManager

        if DEVICE == "cuda":
            if CUDNN_BENCHMARK:
                torch.backends.cudnn.benchmark = True
                torch.backends.cudnn.enabled = True
            if USE_TF32:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
            torch.set_grad_enabled(False)
            if USE_FLOAT16:
                self._autocast_dtype = torch.float16

        logger.info(f"[Evo XTTS V2] Carregando modelo (device={DEVICE})")

        manager = ModelManager()
        model_path, config_path, _ = manager.download_model(XTTS_MODEL_NAME)

        if config_path is None:
            config_path = os.path.join(model_path, "config.json")

        config = XttsConfig()
        config.load_json(config_path)
        self._model = Xtts.init_from_config(config)
        self._model.load_checkpoint(config, checkpoint_dir=model_path, eval=True)

        if DEVICE == "cuda":
            self._model.cuda()
            if USE_TORCH_COMPILE and hasattr(torch, "compile"):
                try:
                    self._model.gpt = torch.compile(self._model.gpt, mode="reduce-overhead", fullgraph=False)
                    logger.info("[Evo XTTS V2] torch.compile ativado para GPT")
                except Exception as exc:
                    logger.warning(f"[Evo XTTS V2] torch.compile unavailable: {exc}")

        self._loaded = True
        logger.info("[Evo XTTS V2] Model loaded successfully")

        self._scan_available_voices()

    def _install_audio_fallbacks(self) -> None:
        import soundfile as sf
        import torch
        import torchaudio

        if getattr(torchaudio, "_evo_soundfile_patch", False):
            return

        original_load = torchaudio.load

        def load_with_soundfile(
            uri,
            frame_offset=0,
            num_frames=-1,
            normalize=True,
            channels_first=True,
            format=None,
            buffer_size=4096,
            backend=None,
        ):
            del format, buffer_size, backend
            frames = -1 if num_frames is None or num_frames < 0 else num_frames
            audio, sample_rate = sf.read(
                uri,
                start=max(0, int(frame_offset or 0)),
                frames=frames,
                dtype="float32",
                always_2d=True,
            )
            tensor = torch.from_numpy(audio.T if channels_first else audio)
            if not normalize:
                return tensor, sample_rate
            return tensor.float(), sample_rate

        def patched_load(*args, **kwargs):
            try:
                return original_load(*args, **kwargs)
            except (ImportError, ModuleNotFoundError) as exc:
                if "torchcodec" not in str(exc).lower():
                    raise
                if not getattr(torchaudio, "_evo_soundfile_warning_logged", False):
                    logger.warning("[Evo XTTS V2] TorchCodec unavailable; using soundfile fallback")
                    torchaudio._evo_soundfile_warning_logged = True
                return load_with_soundfile(*args, **kwargs)

        torchaudio.load = patched_load
        torchaudio._evo_soundfile_patch = True

    def _scan_available_voices(self) -> None:
        logger.info(f"[Evo XTTS V2] Scanning voices in: {self._voices_dir}")
        if not self._voices_dir.exists():
            logger.warning(f"[Evo XTTS V2] Folder '{self._voices_dir}' not found.")
            return

        wav_files = list(self._voices_dir.glob("*.wav"))
        if not wav_files:
            logger.warning(f"[Evo XTTS V2] No .wav files in '{self._voices_dir}/'.")
            return

        for wav_file in wav_files:
            self._available_voices.add(wav_file.stem)
        logger.info(f"[Evo XTTS V2] {len(self._available_voices)} voice(s) found")

    def preload_voices_background(self) -> None:
        import threading
        threading.Thread(target=self._preload_voices_sync, daemon=True).start()

    def _preload_voices_sync(self) -> None:
        self._preloading = True
        total = len(self._available_voices)
        cached = 0
        for voice_id in sorted(self._available_voices):
            if voice_id in self._voice_cache:
                cached += 1
                continue
            wav_path = self._voices_dir / f"{voice_id}.wav"
            try:
                self._cache_voice(voice_id, str(wav_path))
                cached += 1
                logger.info(f"[Evo XTTS V2] Voice '{voice_id}' cached ({cached}/{total})")
            except Exception as exc:
                import traceback
                logger.error(f"[Evo XTTS V2] Error loading voice '{voice_id}': {exc}\n{traceback.format_exc()}")
        self._preloading = False
        logger.info(f"[Evo XTTS V2] Preload complete: {cached}/{total} voices")

    def _cache_voice(self, voice_id: str, wav_path: str) -> None:
        gpt_cond_latent, speaker_embedding = self._model.get_conditioning_latents(
            audio_path=[wav_path],
            gpt_cond_len=GPT_COND_LEN,
            gpt_cond_chunk_len=GPT_COND_CHUNK_LEN,
        )
        if DEVICE == "cuda":
            gpt_cond_latent = gpt_cond_latent.cuda()
            speaker_embedding = speaker_embedding.cuda()
        self._voice_cache[voice_id] = (gpt_cond_latent, speaker_embedding)

    def _get_voice(self, voice: str) -> tuple:
        if voice not in self._voice_cache:
            wav_path = self._voices_dir / f"{voice}.wav"
            if wav_path.exists():
                self._cache_voice(voice, str(wav_path))
            else:
                available = list(self._voice_cache.keys())
                raise ValueError(
                    f"Voice '{voice}' not found. "
                    f"Place '{voice}.wav' (6-30s) in '{self._voices_dir}/'. "
                    f"Available: {available}"
                )
        return self._voice_cache[voice]

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_supported_languages(self) -> list[dict]:
        return [{"id": lang_id, "name": data["label"]} for lang_id, data in SUPPORTED_LANGUAGES.items()]

    def validate_language(self, language: str) -> bool:
        return language in SUPPORTED_LANGUAGES

    def _normalize_language(self, language: str | None) -> str:
        normalized = (language or DEFAULT_LANGUAGE).strip().lower()
        if normalized not in SUPPORTED_LANGUAGES:
            available = ", ".join(SUPPORTED_LANGUAGES.keys())
            raise ValueError(f"Language '{language}' not supported. Available: {available}")
        return normalized

    _VOICE_PREFIX_TO_LANG = {
        "Arabic": "ar",
        "Danish": "da",
        "Dutch": "nl",
        "English": "en",
        "French": "fr",
        "German": "de",
        "Japanese": "ja",
        "Norwegian": "no",
        "Portuguese_Brazilian": "pt",
        "Portuguese": "pt",
        "Spanish": "es",
        "Swedish": "sv",
    }
    _VOICE_PREFIX_SORTED = sorted(_VOICE_PREFIX_TO_LANG.items(), key=lambda x: -len(x[0]))

    def _detect_voice_language(self, voice_id: str) -> str:
        for prefix, lang_code in self._VOICE_PREFIX_SORTED:
            if voice_id.startswith(prefix):
                return lang_code
        return DEFAULT_LANGUAGE

    def get_voices(self) -> list[dict]:
        all_voices = self._available_voices | set(self._voice_cache.keys())
        voices = []
        for voice_id in sorted(all_voices):
            cached = voice_id in self._voice_cache
            lang = self._detect_voice_language(voice_id)
            voices.append(
                {
                    "id": voice_id,
                    "name": voice_id.replace("_", " ").replace("-", " ").title(),
                    "gender": "clonada",
                    "lang": lang,
                    "description": f"Cloned voice '{voice_id}'" + ("" if cached else " (loading...)"),
                    "languages": list(SUPPORTED_LANGUAGES.keys()),
                }
            )
        return voices

    def get_default_voice(self) -> str:
        all_voices = self._available_voices | set(self._voice_cache.keys())
        if DEFAULT_VOICE in all_voices:
            return DEFAULT_VOICE
        if all_voices:
            return sorted(all_voices)[0]
        return DEFAULT_VOICE

    def validate_voice(self, voice: str) -> bool:
        return voice in self._voice_cache or voice in self._available_voices or (self._voices_dir / f"{voice}.wav").exists()

    def _get_emotion_params(self, emotion: str | None) -> dict:
        if emotion and emotion in EMOTIONS:
            params = EMOTIONS[emotion]
            return {
                "temperature": params["temperature"],
                "top_p": params["top_p"],
                "speed_mod": params["speed_mod"],
                "repetition_penalty": params["repetition_penalty"],
            }
        return {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "speed_mod": 1.0,
            "repetition_penalty": REPETITION_PENALTY,
        }

    def _autocast_context(self):
        import torch

        if DEVICE != "cuda" or self._autocast_dtype is None:
            return nullcontext()
        return torch.autocast(device_type="cuda", dtype=self._autocast_dtype)

    def _synth_chunk(self, text_chunk: str, voice: str, language: str, speed: float, emotion: str | None = None) -> np.ndarray:
        import torch

        gpt_cond_latent, speaker_embedding = self._get_voice(voice)
        emotion_params = self._get_emotion_params(emotion)
        lang_code = SUPPORTED_LANGUAGES[self._normalize_language(language)]["tts_code"]

        with torch.inference_mode(), self._autocast_context():
            out = self._model.inference(
                text_chunk,
                lang_code,
                gpt_cond_latent,
                speaker_embedding,
                temperature=emotion_params["temperature"],
                top_k=TOP_K,
                top_p=emotion_params["top_p"],
                repetition_penalty=emotion_params["repetition_penalty"],
                length_penalty=LENGTH_PENALTY,
                speed=speed * emotion_params["speed_mod"],
                enable_text_splitting=True,
            )
        return out["wav"]

    def synthesize(self, text: str, voice: str, language: str, speed: float, emotion: str | None = None) -> np.ndarray:
        language = self._normalize_language(language)
        text = preprocess_text(text, language)
        chunks = chunk_text(text)
        logger.debug(f"[Evo XTTS V2] {len(chunks)} chunks, emotion={emotion or 'neutro'}")

        audio_segments = []
        for chunk in chunks:
            audio = self._synth_chunk(chunk, voice, language, speed, emotion)
            if audio is not None and len(audio) > 0:
                audio_segments.append(audio)

        if not audio_segments:
            raise RuntimeError("No audio generated")

        audio = crossfade_chunks(audio_segments)
        audio = trim_silence(audio)
        audio = post_process(audio)
        return audio

    def synthesize_chunks(self, text: str, voice: str, language: str, speed: float, emotion: str | None = None) -> list[np.ndarray]:
        language = self._normalize_language(language)
        text = preprocess_text(text, language)
        chunks = chunk_text(text)
        result = []

        for chunk in chunks:
            audio = self._synth_chunk(chunk, voice, language, speed, emotion)
            if audio is not None and len(audio) > 0:
                result.append(post_process(audio))

        return result

    def synthesize_stream(self, text: str, voice: str, language: str, speed: float, emotion: str | None = None):
        import torch

        language = self._normalize_language(language)
        original_text = text
        text = preprocess_text(text, language)
        gpt_cond_latent, speaker_embedding = self._get_voice(voice)
        emotion_params = self._get_emotion_params(emotion)
        lang_code = SUPPORTED_LANGUAGES[language]["tts_code"]

        try:
            with torch.inference_mode(), self._autocast_context():
                chunks_iter = self._model.inference_stream(
                    text,
                    lang_code,
                    gpt_cond_latent,
                    speaker_embedding,
                    stream_chunk_size=STREAM_CHUNK_SIZE,
                    temperature=emotion_params["temperature"],
                    top_k=TOP_K,
                    top_p=emotion_params["top_p"],
                    repetition_penalty=emotion_params["repetition_penalty"],
                    length_penalty=LENGTH_PENALTY,
                    speed=speed * emotion_params["speed_mod"],
                    enable_text_splitting=True,
                )
                for chunk_tensor in chunks_iter:
                    yield chunk_tensor.cpu().float().numpy()
        except AttributeError as exc:
            logger.warning(f"[Evo XTTS V2] Native streaming unavailable; using chunk fallback: {exc}")
            for chunk in self.synthesize_chunks(original_text, voice, language, speed, emotion):
                yield chunk
