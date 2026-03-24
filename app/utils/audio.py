import io
import struct
import numpy as np
from pydub import AudioSegment
from app.core.config import SAMPLE_RATE, MP3_BITRATE, MP3_BITRATE_STREAM, CROSSFADE_MS, SILENCE_BETWEEN_CHUNKS_MS


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


# ===================================================================
#  NORMALIZAÇÃO
# ===================================================================

def normalize_peak(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """Normaliza pelo pico máximo."""
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio * (target_peak / peak)
    return audio


def normalize_rms(audio: np.ndarray, target_rms_db: float = -18.0) -> np.ndarray:
    """Normaliza pelo volume médio (RMS) — mais consistente que pico.
    -18 dB é padrão para narração/podcast."""
    rms = np.sqrt(np.mean(audio ** 2))
    if rms == 0:
        return audio
    current_db = 20 * np.log10(rms)
    gain_db = target_rms_db - current_db
    gain = 10 ** (gain_db / 20)
    audio = audio * gain
    # Limitar para não clipar
    peak = np.max(np.abs(audio))
    if peak > 0.98:
        audio = audio * (0.98 / peak)
    return audio


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """Pipeline de normalização: RMS + limiter."""
    audio = normalize_rms(audio, target_rms_db=-18.0)
    return audio


# ===================================================================
#  REDUÇÃO DE RUÍDO
# ===================================================================

def de_noise(audio: np.ndarray, noise_floor: float = 0.003) -> np.ndarray:
    """Noise gate suave — atenua gradualmente sons abaixo do threshold."""
    abs_audio = np.abs(audio)
    gate = np.clip((abs_audio - noise_floor * 0.5) / (noise_floor * 0.5), 0.0, 1.0)
    return audio * gate


# ===================================================================
#  COMPRESSOR DINÂMICO
# ===================================================================

def compress_dynamics(audio: np.ndarray, threshold_db: float = -20.0,
                      ratio: float = 3.0, window_ms: float = 15.0) -> np.ndarray:
    """Compressor de dinâmica vetorizado (rápido, sem loop Python).
    Reduz diferença entre sons altos e baixos.
    Resultado: voz mais uniforme e presente, ideal para narração."""
    threshold = 10 ** (threshold_db / 20)
    window_samples = max(int(SAMPLE_RATE * window_ms / 1000), 1)

    # Envelope RMS por janela deslizante (vetorizado)
    squared = audio ** 2
    kernel = np.ones(window_samples) / window_samples
    envelope = np.sqrt(np.convolve(squared, kernel, mode='same'))

    # Aplicar compressão onde ultrapassa o threshold
    gain = np.ones_like(envelope)
    mask = envelope > threshold
    gain[mask] = (threshold / envelope[mask]) ** (1 - 1 / ratio)

    return audio * gain


# ===================================================================
#  DE-ESSER (reduz sibilância)
# ===================================================================

def de_ess(audio: np.ndarray, freq_low: int = 4000, freq_high: int = 9000,
           threshold: float = 0.15, reduction: float = 0.5) -> np.ndarray:
    """Reduz sibilância (sons de 's', 'z', 'ch') que ficam estridentes em TTS."""
    n = len(audio)
    fft = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)

    # Isolar banda de sibilância
    band_mask = (freqs >= freq_low) & (freqs <= freq_high)
    sibilance_energy = np.sqrt(np.mean(np.abs(fft[band_mask]) ** 2))

    if sibilance_energy > threshold:
        # Atenuar a banda de sibilância
        attenuation = np.ones_like(fft, dtype=np.float64)
        attenuation[band_mask] = reduction
        fft = fft * attenuation
        return np.fft.irfft(fft, n).astype(np.float32)

    return audio


# ===================================================================
#  HIGHPASS FILTER (remove rumble/graves indesejados)
# ===================================================================

def highpass_filter(audio: np.ndarray, cutoff_hz: int = 80) -> np.ndarray:
    """Remove frequências muito graves (rumble, ruído de fundo grave).
    Cutoff de 80Hz é padrão para voz."""
    n = len(audio)
    fft = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)

    # Rolloff suave (não corta bruscamente)
    gain = np.ones_like(freqs)
    below_cutoff = freqs < cutoff_hz
    if np.any(below_cutoff):
        gain[below_cutoff] = (freqs[below_cutoff] / cutoff_hz) ** 2

    # DC offset sempre zero
    gain[0] = 0

    fft = fft * gain
    return np.fft.irfft(fft, n).astype(np.float32)


# ===================================================================
#  CROSSFADE E TRIM
# ===================================================================

def crossfade_chunks(chunks: list[np.ndarray], crossfade_samples: int = None) -> np.ndarray:
    """Concatena chunks com crossfade suave."""
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
    result[:len(chunks[0])] = chunks[0]
    pos = len(chunks[0])

    for chunk in chunks[1:]:
        pos += silence_samples

        cf = min(crossfade_samples, pos, len(chunk))
        if cf > 10:
            fade_out = np.linspace(1.0, 0.0, cf, dtype=np.float32)
            fade_in = np.linspace(0.0, 1.0, cf, dtype=np.float32)

            result[pos - cf:pos] *= fade_out
            result[pos - cf:pos] += chunk[:cf] * fade_in
            result[pos:pos + len(chunk) - cf] = chunk[cf:]
            pos += len(chunk) - cf
        else:
            result[pos:pos + len(chunk)] = chunk
            pos += len(chunk)

    return result[:pos]


def trim_silence(audio: np.ndarray, threshold: float = 0.008, pad_samples: int = 1200) -> np.ndarray:
    """Remove silêncio excessivo do início e fim."""
    mask = np.abs(audio) > threshold
    if not mask.any():
        return audio
    indices = np.where(mask)[0]
    start = max(0, indices[0] - pad_samples)
    end = min(len(audio), indices[-1] + pad_samples)
    return audio[start:end]


# ===================================================================
#  PIPELINE COMPLETO DE PÓS-PROCESSAMENTO
# ===================================================================

def post_process(audio: np.ndarray) -> np.ndarray:
    """Pipeline completo de pós-processamento para qualidade profissional.
    Ordem importa — cada etapa prepara para a próxima."""

    # 1. Highpass: remove graves indesejados e DC offset
    audio = highpass_filter(audio, cutoff_hz=80)

    # 2. Noise gate: remove ruído de fundo
    audio = de_noise(audio, noise_floor=0.003)

    # 3. De-esser: reduz sibilância
    audio = de_ess(audio)

    # 4. Compressor: uniformiza volume (partes baixas sobem, altas descem)
    audio = compress_dynamics(audio, threshold_db=-20.0, ratio=3.0)

    # 5. Normalização RMS: volume consistente padrão narração (-18 dB)
    audio = normalize_audio(audio)

    return audio


# ===================================================================
#  CONVERSÃO PARA FORMATOS
# ===================================================================

def numpy_to_mp3_bytes(audio: np.ndarray, bitrate: str = None) -> bytes:
    if bitrate is None:
        bitrate = MP3_BITRATE
    wav_bytes = numpy_to_wav_bytes(audio)
    segment = AudioSegment.from_wav(io.BytesIO(wav_bytes))
    buf = io.BytesIO()
    # Parâmetros ffmpeg para máxima qualidade MP3
    segment.export(
        buf,
        format="mp3",
        bitrate=bitrate,
        parameters=["-q:a", "0"],  # Melhor qualidade VBR do LAME
    )
    return buf.getvalue()


def numpy_to_mp3_chunk(audio: np.ndarray) -> bytes:
    return numpy_to_mp3_bytes(audio, bitrate=MP3_BITRATE_STREAM)
