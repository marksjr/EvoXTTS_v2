from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from app.models.schemas import TTSRequest, TTSStreamRequest, HealthResponse, VoiceInfo
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
            "Nenhuma voz encontrada. Coloque arquivos .wav (6-30s) na pasta 'voices/'.",
        )
    return [VoiceInfo(**v) for v in voices]


@router.get("/emotions")
async def list_emotions():
    """Lista todas as emoções disponíveis e seus efeitos."""
    from app.core.config import EMOTIONS
    result = []
    descriptions = {
        "neutro": "Voz padrão, equilibrada para narração",
        "animado": "Voz empolgada, mais variação e energia",
        "calmo": "Voz tranquila, ritmo lento e suave",
        "serio": "Voz firme, tom formal e estável",
        "triste": "Voz baixa, ritmo lento e melancólico",
        "raiva": "Voz intensa, mais variação e velocidade",
    }
    for name, params in EMOTIONS.items():
        result.append({
            "id": name,
            "description": descriptions.get(name, ""),
            "temperature": params["temperature"],
            "speed_modifier": params["speed_mod"],
        })
    return result


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    voice = req.voice or tts_service.get_default_voice()

    if not tts_service.validate_voice(voice):
        raise HTTPException(
            400,
            f"Voz '{voice}' não disponível. "
            f"Coloque '{voice}.wav' na pasta 'voices/' ou use GET /voices.",
        )

    try:
        audio_bytes = await tts_service.generate(
            text=req.text, voice=voice, speed=req.speed, fmt=req.format,
            emotion=req.emotion,
        )
    except Exception as e:
        raise HTTPException(500, f"Erro na geração: {str(e)}")

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
        raise HTTPException(400, f"Voz '{voice}' não disponível.")

    async def audio_generator():
        async for chunk in tts_service.generate_stream(
            text=req.text, voice=voice, speed=req.speed,
            emotion=req.emotion,
        ):
            yield chunk

    return StreamingResponse(
        audio_generator(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="tts_stream.mp3"'},
    )

