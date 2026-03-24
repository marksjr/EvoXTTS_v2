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

CROSSFADE_MS = 40
SILENCE_BETWEEN_CHUNKS_MS = 60

CHUNK_TARGET_MIN_CHARS = 80
CHUNK_TARGET_MAX_CHARS = 200
CHUNK_ABSOLUTE_MAX_CHARS = 350

XTTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
XTTS_LANG_CODE = "pt"
DEFAULT_VOICE = "default"
VOICES_DIR = str(PROJECT_DIR / "voices")
TTS_HOME_DIR = str(PROJECT_DIR / ".tts")

TEMPERATURE = 0.60
TOP_K = 40
TOP_P = 0.90
REPETITION_PENALTY = 4.0
LENGTH_PENALTY = 1.0

GPT_COND_LEN = 30
GPT_COND_CHUNK_LEN = 3

STREAM_CHUNK_SIZE = 20

EMOTIONS = {
    "neutro":  {"temperature": 0.60, "top_p": 0.90, "speed_mod": 1.0, "repetition_penalty": 4.0},
    "animado": {"temperature": 0.85, "top_p": 0.92, "speed_mod": 1.1, "repetition_penalty": 4.0},
    "calmo":   {"temperature": 0.45, "top_p": 0.78, "speed_mod": 0.9, "repetition_penalty": 6.0},
    "serio":   {"temperature": 0.50, "top_p": 0.80, "speed_mod": 0.95, "repetition_penalty": 6.0},
    "triste":  {"temperature": 0.40, "top_p": 0.75, "speed_mod": 0.85, "repetition_penalty": 6.0},
    "raiva":   {"temperature": 0.90, "top_p": 0.95, "speed_mod": 1.15, "repetition_penalty": 3.5},
}
