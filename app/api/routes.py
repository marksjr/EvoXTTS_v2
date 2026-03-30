from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

from app.models.schemas import HealthResponse, TTSRequest, TTSStreamRequest, VoiceInfo
from app.services.tts_service import tts_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    voices = tts_service.get_voices()
    return HealthResponse(
        status="ok" if tts_service.model_loaded else "loading",
        engine="Evo XTTS V2",
        device=tts_service.device,
        model_loaded=tts_service.model_loaded,
        voices_loaded=len(voices),
    )


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices():
    voices = tts_service.get_voices()
    if not voices:
        raise HTTPException(
            404,
            "No voices found. Place .wav files (6-30s) in the 'voices/' folder.",
        )
    return [VoiceInfo(**voice) for voice in voices]


@router.get("/languages")
async def list_languages():
    return tts_service.get_supported_languages()


@router.get("/emotions")
async def list_emotions():
    from app.core.config import EMOTIONS

    descriptions = {
        "neutro": "Default balanced voice for narration",
        "animado": "Excited voice with more variation and energy",
        "calmo": "Calm voice with slow and smooth rhythm",
        "serio": "Firm voice with formal and stable tone",
        "triste": "Low voice with slow and melancholic rhythm",
        "raiva": "Intense voice with more variation and speed",
    }
    return [
        {
            "id": name,
            "description": descriptions.get(name, ""),
            "temperature": params["temperature"],
            "speed_modifier": params["speed_mod"],
        }
        for name, params in EMOTIONS.items()
    ]


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    voice = req.voice or tts_service.get_default_voice()

    if not tts_service.validate_voice(voice):
        raise HTTPException(
            400,
            f"Voice '{voice}' not available. Place '{voice}.wav' in the 'voices/' folder or use GET /voices.",
        )

    if not tts_service.validate_language(req.language):
        raise HTTPException(400, f"Language '{req.language}' not supported.")

    try:
        audio_bytes = await tts_service.generate(
            text=req.text,
            voice=voice,
            language=req.language,
            speed=req.speed,
            fmt=req.format,
            emotion=req.emotion,
        )
    except Exception as exc:
        raise HTTPException(500, f"Generation error: {exc}") from exc

    media_type = "audio/mpeg" if req.format == "mp3" else "audio/wav"
    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="tts.{req.format}"'},
    )


@router.post("/tts/stream")
async def text_to_speech_stream(req: TTSStreamRequest):
    voice = req.voice or tts_service.get_default_voice()

    if not tts_service.validate_voice(voice):
        raise HTTPException(400, f"Voice '{voice}' not available.")

    if not tts_service.validate_language(req.language):
        raise HTTPException(400, f"Language '{req.language}' not supported.")

    async def audio_generator():
        async for chunk in tts_service.generate_stream(
            text=req.text,
            voice=voice,
            language=req.language,
            speed=req.speed,
            emotion=req.emotion,
        ):
            yield chunk

    return StreamingResponse(
        audio_generator(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="tts_stream.mp3"'},
    )
