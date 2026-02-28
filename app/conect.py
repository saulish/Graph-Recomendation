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
    playlist_keys = ('name', 'description', 'public', 'collaborative', 'images', 'tracks', 'id')
    playlists = [{k: d[k] for k in playlist_keys}
                 for d in sp.current_user_playlists()['items']
                 ]
    return playlists


def get_all_tracks(token_info, playlist_id):
    if not token_info:
        return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    tracks = []
    results = sp.playlist_items(playlist_id, limit=100)
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return tracks


def start_process(token_info, playlist_id, model):
    all_tracks = get_all_tracks(token_info, playlist_id)
    # To remove if those songs are not valid
    dup_tracks = set()
    all_tracks = [t for t in all_tracks if t.get('track') is not None and t['track']['type'] != 'episode'
                  and t['track']['id'] not in dup_tracks and not dup_tracks.add(t['track']['id'])]
    real_total = len(all_tracks)
    from .apiSpotify import consumer_main
    return consumer_main(all_tracks, real_total, model)


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
