import os
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

load_dotenv()
BACKEND_PORT = os.getenv('BACK_PORT')
FRONTEND_PORT = os.getenv('FRONT_PORT')

def configApp(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http://127.0.0.1:{FRONTEND_PORT}"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key="miau",
        session_cookie="session",
        same_site="lax",  # only dev
        https_only=False  # only dev
    )


class Config:
    clientID = os.getenv('SPOTIFY_API_KEY')
    secretID = os.getenv('SPOTIFY_API_SECRET')
    BACKEND_PORT = BACKEND_PORT
    FRONTEND_PORT = FRONTEND_PORT
    redirect_url = f'http://127.0.0.1:{str(BACKEND_PORT)}/callback'
    scope = 'playlist-read-private'
    base_url = 'https://api.deezer.com/search'
    backend_url = f'http://127.0.0.1:{str(BACKEND_PORT)}/'
    track_Url = 'https://api.deezer.com/track/'
    artist_url = 'https://api.deezer.com/artist'
    album_url = 'https://api.deezer.com/album'


config = Config()
