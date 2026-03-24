from pydantic import BaseModel, Field
from typing import Literal, Optional


EMOTION_TYPE = Literal["neutro", "animado", "calmo", "serio", "triste", "raiva"]


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Texto para sintetizar")
    voice: str = Field(default="", description="ID da voz (nome do arquivo .wav sem extensao)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Velocidade da fala")
    format: Literal["mp3", "wav"] = Field(default="wav", description="Formato de saida")
    emotion: Optional[EMOTION_TYPE] = Field(
        default=None,
        description="Emocao da voz: neutro, animado, calmo, serio, triste, raiva",
    )


class TTSStreamRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Texto para sintetizar")
    voice: str = Field(default="", description="ID da voz")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Velocidade da fala")
    emotion: Optional[EMOTION_TYPE] = Field(default=None, description="Emocao da voz")


class HealthResponse(BaseModel):
    status: str
    engine: str
    device: str
    model_loaded: bool
    voices_loaded: int


class VoiceInfo(BaseModel):
    id: str
    name: str
    gender: str
    lang: str
    description: str
