from fastapi import Request, HTTPException
from app.conect import get_token_info


async def get_current_user(request: Request) -> dict:
    token_info = get_token_info(request)
    if not token_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_info
