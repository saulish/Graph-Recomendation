from fastapi import Request, HTTPException
from app.conect import getTokenInfo


async def get_current_user(request: Request) -> dict:
    token_info = getTokenInfo(request)
    if not token_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_info
