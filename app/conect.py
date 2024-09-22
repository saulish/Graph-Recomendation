from flask import session, redirect, url_for
import spotipy
import requests
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv() 

clientID = os.getenv('SPOTIFY_API_KEY')
secretID = os.getenv('SPOTIFY_API_SECRET')
redirect_url = os.getenv('REDIRECT')

playlist="https://open.spotify.com/playlist/4PsCeD3yIyiN3YhobkOv4R" #40 CANCIONES         2 segs       17 segs
#playlist="https://open.spotify.com/playlist/1pkkHHc9IFUbvxMP7Ae3tH" #75 CANCIONES        9 segs        32 segs
#playlist="https://open.spotify.com/playlist/2crl2EB6XAbpRgfbwKfCHa" #107 CANCIONES       14 seg         42 segs
#playlist="https://open.spotify.com/playlist/5lt9aNOMN1FAa3PLcJ01fy" #500+ CANCIONES     54 segs         168 segs
base_url = 'https://api.deezer.com/search'
track_Url='https://api.deezer.com/track/'
artist_url = 'https://api.deezer.com/artist'
album_url = 'https://api.deezer.com/album'



sp_oauth = SpotifyOAuth(client_id=clientID, client_secret=secretID, redirect_uri=redirect_url, scope='playlist-read-private')

def getSpotifyInstance():
    # Obtiene el token de acceso del usuario (abre automáticamente una ventana de inicio de sesión)
    token_info = sp_oauth.get_access_token()
    access_token = token_info['access_token']

    # Crea una instancia de Spotipy con el token de acceso
    return spotipy.Spotify(auth=access_token)

def getPlaylist(token_info):
    if not token_info:
        return redirect(url_for('index'))

    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlists = sp.current_user_playlists()
    return playlists


def login():
    auth_url = sp_oauth.get_authorize_url()
    return auth_url

def getToken(code):
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return token_info


def refrescarToken(token_info):
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    
