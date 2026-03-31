import io
import struct
from pathlib import Path

import numpy as np
from pydub import AudioSegment

from app.core.config import (
    CROSSFADE_MS,
    MP3_BITRATE,
    MP3_BITRATE_STREAM,
    SAMPLE_RATE,
    SILENCE_BETWEEN_CHUNKS_MS,
)


def _configure_local_ffmpeg() -> None:
    project_root = Path(__file__).resolve().parents[2]
    ffmpeg_bin = project_root / "ffmpeg" / "bin"
    ffmpeg_exe = ffmpeg_bin / "ffmpeg.exe"
    ffprobe_exe = ffmpeg_bin / "ffprobe.exe"

    if ffmpeg_exe.exists():
        AudioSegment.converter = str(ffmpeg_exe)
        AudioSegment.ffmpeg = str(ffmpeg_exe)
    if ffprobe_exe.exists():
        AudioSegment.ffprobe = str(ffprobe_exe)


_configure_local_ffmpeg()


def numpy_to_wav_bytes(audio: np.ndarray) -> bytes:
    buf = io.BytesIO()
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    num_samples = len(audio_int16)
    data_size = num_samples * 2

    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))
    buf.write(struct.pack("<H", 1))
    buf.write(struct.pack("<H", 1))
    buf.write(struct.pack("<I", SAMPLE_RATE))
    buf.write(struct.pack("<I", SAMPLE_RATE * 2))
    buf.write(struct.pack("<H", 2))
    buf.write(struct.pack("<H", 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(audio_int16.tobytes())
    return buf.getvalue()


def normalize_peak(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio * (target_peak / peak)
    return audio


def normalize_rms(audio: np.ndarray, target_rms_db: float = -18.0) -> np.ndarray:
    rms = np.sqrt(np.mean(audio ** 2))
    if rms == 0:
        return audio
    current_db = 20 * np.log10(rms)
    gain_db = target_rms_db - current_db
    gain = 10 ** (gain_db / 20)
    audio = audio * gain
    peak = np.max(np.abs(audio))
    if peak > 0.98:
        audio = audio * (0.98 / peak)
    return audio


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    return normalize_rms(audio, target_rms_db=-18.0)


def de_noise(audio: np.ndarray, noise_floor: float = 0.003) -> np.ndarray:
    abs_audio = np.abs(audio)
    gate = np.clip((abs_audio - noise_floor * 0.5) / (noise_floor * 0.5), 0.0, 1.0)
    return audio * gate


def highpass_filter(audio: np.ndarray, cutoff_hz: int = 80) -> np.ndarray:
    n = len(audio)
    fft = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)

    gain = np.ones_like(freqs)
    below_cutoff = freqs < cutoff_hz
    if np.any(below_cutoff):
        gain[below_cutoff] = (freqs[below_cutoff] / cutoff_hz) ** 2

    gain[0] = 0

    fft = fft * gain
    return np.fft.irfft(fft, n).astype(np.float32)


def crossfade_chunks(chunks: list[np.ndarray], crossfade_samples: int = None) -> np.ndarray:
    if not chunks:
        return np.array([], dtype=np.float32)
    if len(chunks) == 1:
        return chunks[0]

    if crossfade_samples is None:
        crossfade_samples = int(SAMPLE_RATE * CROSSFADE_MS / 1000)

    silence_samples = int(SAMPLE_RATE * SILENCE_BETWEEN_CHUNKS_MS / 1000)

    total_size = sum(len(c) for c in chunks) + silence_samples * (len(chunks) - 1)
    result = np.zeros(total_size, dtype=np.float32)

    pos = 0
    result[: len(chunks[0])] = chunks[0]
    pos = len(chunks[0])

    for chunk in chunks[1:]:
        pos += silence_samples

        cf = min(crossfade_samples, pos, len(chunk))
        if cf > 10:
            fade_out = np.linspace(1.0, 0.0, cf, dtype=np.float32)
            fade_in = np.linspace(0.0, 1.0, cf, dtype=np.float32)

            result[pos - cf : pos] *= fade_out
            result[pos - cf : pos] += chunk[:cf] * fade_in
            result[pos : pos + len(chunk) - cf] = chunk[cf:]
            pos += len(chunk) - cf
        else:
            result[pos : pos + len(chunk)] = chunk
            pos += len(chunk)

    return result[:pos]


def trim_silence(audio: np.ndarray, threshold: float = 0.008, pad_samples: int = 1200) -> np.ndarray:
    mask = np.abs(audio) > threshold
    if not mask.any():
        return audio
    indices = np.where(mask)[0]
    start = max(0, indices[0] - pad_samples)
    end = min(len(audio), indices[-1] + pad_samples)
    return audio[start:end]


def post_process(audio: np.ndarray) -> np.ndarray:
    audio = highpass_filter(audio, cutoff_hz=80)
    audio = normalize_audio(audio)
    return audio


def numpy_to_mp3_bytes(audio: np.ndarray, bitrate: str = None) -> bytes:
    if bitrate is None:
        bitrate = MP3_BITRATE
    wav_bytes = numpy_to_wav_bytes(audio)
    segment = AudioSegment.from_wav(io.BytesIO(wav_bytes))
    buf = io.BytesIO()
    segment.export(
        buf,
        format="mp3",
        bitrate=bitrate,
        parameters=["-q:a", "0"],
    )
    return buf.getvalue()


def numpy_to_mp3_chunk(audio: np.ndarray) -> bytes:
    return numpy_to_mp3_bytes(audio, bitrate=MP3_BITRATE_STREAM)
