from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.conect import start_process
from app.core.dependencies import get_current_user
from app.embeddings.model_inference import model

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/playlist/{playlist_id}")
async def analyze_playlist(
        playlist_id: str,
        token_info: dict = Depends(get_current_user)):
    generator = start_process(token_info, playlist_id, model)
    return StreamingResponse(generator, media_type="application/x-ndjson")
