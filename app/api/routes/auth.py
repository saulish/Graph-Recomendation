from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from app.config import config
from app.conect import login, create_access_token, get_token_info
from app.schemas.response import LoginResponse, StandardResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get('/login')
async def start(request: Request):
    # Check if already logged in (optional validation, no auth required)
    token_info = get_token_info(request)
    if token_info:
        return LoginResponse(ok=True, logged=True)
    else:
        url = login()
        return LoginResponse(ok=True, logged=False, auth_url=url)


@router.get('/callback')
async def callback(request: Request):

    params = dict(request.query_params)
    code = params.get("code")
    error = params.get("error")
    if error:
        print(f"Error in callback: {error}")
        raise HTTPException(status_code=500, detail="Failed callback")

    token_info = create_access_token(code)
    if not token_info:
        print(f"Not token info available")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    request.session["token_info"] = token_info
    return RedirectResponse(f"http://127.0.0.1:{config.FRONTEND_PORT}/menu.html")


@router.delete('/logout')
async def logout(request: Request, ):
    request.session.clear()
    return StandardResponse(ok=True)
