import logging
from pathlib import Path

import numpy as np

from app.core.config import (
    CUDNN_BENCHMARK,
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
    TTS_HOME_DIR,
    VOICES_DIR,
    XTTS_LANG_CODE,
    XTTS_MODEL_NAME,
)
from app.utils.audio import crossfade_chunks, post_process, trim_silence
from app.utils.text import chunk_text, preprocess_text_ptbr

logger = logging.getLogger(__name__)


class XTTSEngine:
    """Engine Coqui Evo XTTS V2 para pt-BR com clonagem de voz."""

    def __init__(self):
        self._model = None
        self._loaded = False
        self._voices_dir = Path(VOICES_DIR)
        self._voice_cache: dict[str, tuple] = {}

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
            torch.set_grad_enabled(False)

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

        self._loaded = True
        logger.info("[Evo XTTS V2] Modelo carregado com sucesso")

        self._preload_voices()

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
                logger.warning("[Evo XTTS V2] TorchCodec indisponivel; usando fallback com soundfile")
                return load_with_soundfile(*args, **kwargs)

        torchaudio.load = patched_load
        torchaudio._evo_soundfile_patch = True

    def _preload_voices(self) -> None:
        logger.info(f"[Evo XTTS V2] Procurando vozes em: {self._voices_dir}")
        if not self._voices_dir.exists():
            logger.warning(f"[Evo XTTS V2] Pasta '{self._voices_dir}' nao encontrada.")
            return

        wav_files = list(self._voices_dir.glob("*.wav"))
        if not wav_files:
            logger.warning(f"[Evo XTTS V2] Nenhum .wav em '{self._voices_dir}/'.")
            return

        for wav_file in wav_files:
            voice_id = wav_file.stem
            try:
                self._cache_voice(voice_id, str(wav_file))
                logger.info(f"[Evo XTTS V2] Voz '{voice_id}' cacheada")
            except Exception as exc:
                import traceback
                logger.error(f"[Evo XTTS V2] Erro ao carregar voz '{voice_id}': {exc}\n{traceback.format_exc()}")

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
                    f"Voz '{voice}' nao encontrada. "
                    f"Coloque '{voice}.wav' (6-30s) na pasta '{self._voices_dir}/'. "
                    f"Disponiveis: {available}"
                )
        return self._voice_cache[voice]

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_voices(self) -> list[dict]:
        voices = []
        for voice_id in self._voice_cache:
            voices.append(
                {
                    "id": voice_id,
                    "name": voice_id.replace("_", " ").replace("-", " ").title(),
                    "gender": "clonada",
                    "lang": "pt-br",
                    "description": f"Voz clonada '{voice_id}' (Evo XTTS V2)",
                }
            )
        return voices

    def get_default_voice(self) -> str:
        if self._voice_cache:
            if DEFAULT_VOICE in self._voice_cache:
                return DEFAULT_VOICE
            return next(iter(self._voice_cache))
        return DEFAULT_VOICE

    def validate_voice(self, voice: str) -> bool:
        if voice in self._voice_cache:
            return True
        return (self._voices_dir / f"{voice}.wav").exists()

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

    def _synth_chunk(self, text_chunk: str, voice: str, speed: float, emotion: str | None = None) -> np.ndarray:
        import torch

        gpt_cond_latent, speaker_embedding = self._get_voice(voice)
        emotion_params = self._get_emotion_params(emotion)

        with torch.inference_mode():
            out = self._model.inference(
                text_chunk,
                XTTS_LANG_CODE,
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

    def synthesize(self, text: str, voice: str, speed: float, emotion: str | None = None) -> np.ndarray:
        text = preprocess_text_ptbr(text)
        chunks = chunk_text(text)
        logger.debug(f"[Evo XTTS V2] {len(chunks)} chunks, emotion={emotion or 'neutro'}")

        audio_segments = []
        for chunk in chunks:
            audio = self._synth_chunk(chunk, voice, speed, emotion)
            if audio is not None and len(audio) > 0:
                audio_segments.append(audio)

        if not audio_segments:
            raise RuntimeError("Nenhum audio gerado")

        audio = crossfade_chunks(audio_segments)
        audio = trim_silence(audio)
        audio = post_process(audio)
        return audio

    def synthesize_chunks(self, text: str, voice: str, speed: float, emotion: str | None = None) -> list[np.ndarray]:
        text = preprocess_text_ptbr(text)
        chunks = chunk_text(text)
        result = []

        for chunk in chunks:
            audio = self._synth_chunk(chunk, voice, speed, emotion)
            if audio is not None and len(audio) > 0:
                result.append(post_process(audio))

        return result

    def synthesize_stream(self, text: str, voice: str, speed: float, emotion: str | None = None):
        import torch

        text = preprocess_text_ptbr(text)
        gpt_cond_latent, speaker_embedding = self._get_voice(voice)
        emotion_params = self._get_emotion_params(emotion)

        with torch.inference_mode():
            chunks_iter = self._model.inference_stream(
                text,
                XTTS_LANG_CODE,
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
