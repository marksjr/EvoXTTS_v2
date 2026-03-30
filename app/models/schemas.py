from pydantic import BaseModel, Field
from typing import Literal, Optional


EMOTION_TYPE = Literal["neutro", "animado", "calmo", "serio", "triste", "raiva"]


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to synthesize")
    voice: str = Field(default="", description="Voice ID (.wav filename without extension)")
    language: str = Field(default="pt", description="Text language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    format: Literal["mp3", "wav"] = Field(default="wav", description="Output format")
    emotion: Optional[EMOTION_TYPE] = Field(
        default=None,
        description="Voice emotion: neutro, animado, calmo, serio, triste, raiva",
    )


class TTSStreamRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to synthesize")
    voice: str = Field(default="", description="Voice ID")
    language: str = Field(default="pt", description="Text language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    emotion: Optional[EMOTION_TYPE] = Field(default=None, description="Voice emotion")


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
    languages: list[str] = Field(default_factory=list)
