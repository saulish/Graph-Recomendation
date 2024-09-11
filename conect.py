
import spotipy
import requests
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv() 

clientID = os.getenv('SPOTIFY_API_KEY')
secretID = os.getenv('SPOTIFY_API_SECRET')
redirect = os.getenv('REDIRECT')

playlist="https://open.spotify.com/playlist/4PsCeD3yIyiN3YhobkOv4R" #40 CANCIONES         2 segs
#playlist="https://open.spotify.com/playlist/1pkkHHc9IFUbvxMP7Ae3tH" #75 CANCIONES        9 segs
#playlist="https://open.spotify.com/playlist/2crl2EB6XAbpRgfbwKfCHa" #107 CANCIONES       14 seg
#playlist="https://open.spotify.com/playlist/5lt9aNOMN1FAa3PLcJ01fy" #500+ CANCIONES     54 segs
base_url = 'https://api.deezer.com/search'
album_url = 'https://api.deezer.com/album'




def getSpotifyInstance():
    sp_oauth = SpotifyOAuth(client_id=clientID, client_secret=secretID, redirect_uri=redirect, scope='playlist-read-private')

    # Obtiene el token de acceso del usuario (abre automáticamente una ventana de inicio de sesión)
    token_info = sp_oauth.get_access_token()
    access_token = token_info['access_token']

    # Crea una instancia de Spotipy con el token de acceso
    return spotipy.Spotify(auth=access_token)
