from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from app.conect import getTokenInfo, start_process
from app.embeddings.model_inference import model

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/playlist/{playlist_id}")
async def analizePlaylist(
        request: Request, playlist_id: str,
        token_info: dict = Depends(getTokenInfo)):
    generator = start_process(token_info, playlist_id, model)
    return StreamingResponse(generator, media_type="application/x-ndjson")
