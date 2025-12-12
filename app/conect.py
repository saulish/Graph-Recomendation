import time
import spotipy
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from spotipy.oauth2 import SpotifyOAuth
from .config import config


def getPlaylist(token_info):
    if not token_info:
        return RedirectResponse(config.backend_url + "")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    return playlists


def getData(token_info, playlist_id):
    if not token_info:
        return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)
    sp = spotipy.Spotify(auth=token_info['access_token'])

    from .apiSpotify import getGrafo
    playlist_info = sp.playlist(playlist_id)
    return getGrafo(playlist_id, sp, playlist_info)


def login():
    sp_oauth = getOauth()
    auth_url = sp_oauth.get_authorize_url()
    return auth_url


def getTokenInfo(request: Request):
    try:
        token_info = request.session["token_info"]
    except KeyError as e:
        print(f"Token not existent")
        return None
    if not token_info:
        return None

    if token_info["expires_at"] - int(time.time()) < 60:
        print("Experied token → refreshing...")
        sp_oauth = getOauth()
        refreshed = sp_oauth.refresh_access_token(token_info["refresh_token"])
        token_info = refreshed

        request.session["token_info"] = token_info

    return token_info


def createAccesToken(code):
    sp_oauth = getOauth()
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info.get("access_token")
    if not access_token:
        return JSONResponse({"error": "Access code failed"}, status_code=500)

    return token_info


def getOauth():
    return SpotifyOAuth(client_id=config.clientID, client_secret=config.secretID, redirect_uri=config.redirect_url,
                        show_dialog=True, scope=config.scope, cache_path=None)
