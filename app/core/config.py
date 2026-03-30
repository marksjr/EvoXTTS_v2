import torch
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

SAMPLE_RATE = 24000
MP3_BITRATE = "320k"
MP3_BITRATE_STREAM = "192k"

HOST = "0.0.0.0"
PORT = 8881

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

USE_FLOAT16 = False
CUDNN_BENCHMARK = True
USE_TORCH_COMPILE = False
USE_TF32 = False

CROSSFADE_MS = 40
SILENCE_BETWEEN_CHUNKS_MS = 60

CHUNK_TARGET_MIN_CHARS = 80
CHUNK_TARGET_MAX_CHARS = 180
CHUNK_ABSOLUTE_MAX_CHARS = 320

XTTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
DEFAULT_LANGUAGE = "pt"
DEFAULT_VOICE = "default"
VOICES_DIR = str(PROJECT_DIR / "voices")
TTS_HOME_DIR = str(PROJECT_DIR / ".tts")

SUPPORTED_LANGUAGES = {
    "ar": {"label": "Arabic", "tts_code": "ar"},
    "da": {"label": "Danish", "tts_code": "en"},
    "de": {"label": "German", "tts_code": "de"},
    "en": {"label": "English", "tts_code": "en"},
    "es": {"label": "Spanish", "tts_code": "es"},
    "fr": {"label": "French", "tts_code": "fr"},
    "ja": {"label": "Japanese", "tts_code": "ja"},
    "nl": {"label": "Dutch", "tts_code": "nl"},
    "no": {"label": "Norwegian", "tts_code": "en"},
    "pt": {"label": "Portuguese", "tts_code": "pt"},
    "sv": {"label": "Swedish", "tts_code": "en"},
}

TEMPERATURE = 0.65
TOP_K = 50
TOP_P = 0.90
REPETITION_PENALTY = 4.0
LENGTH_PENALTY = 1.0

GPT_COND_LEN = 30
GPT_COND_CHUNK_LEN = 6

STREAM_CHUNK_SIZE = 20

EMOTIONS = {
    "neutral":  {"temperature": 0.65, "top_p": 0.90, "speed_mod": 1.0, "repetition_penalty": 4.0},
    "excited":  {"temperature": 0.85, "top_p": 0.92, "speed_mod": 1.08, "repetition_penalty": 4.0},
    "calm":     {"temperature": 0.48, "top_p": 0.82, "speed_mod": 0.92, "repetition_penalty": 5.5},
    "serious":  {"temperature": 0.52, "top_p": 0.84, "speed_mod": 0.97, "repetition_penalty": 5.5},
    "sad":      {"temperature": 0.44, "top_p": 0.80, "speed_mod": 0.88, "repetition_penalty": 5.5},
    "angry":    {"temperature": 0.92, "top_p": 0.95, "speed_mod": 1.12, "repetition_penalty": 3.5},
}
