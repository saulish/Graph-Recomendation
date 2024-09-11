import requests
from conect import getSpotifyInstance, playlist, base_url, album_url

sp = getSpotifyInstance()

playlist_id = playlist.split('/')[-1]

# Obtiene la información de la playlist
playlist_info = sp.playlist(playlist_id)

# Imprime la información de la playlist
songs=[]
print(f"Nombre de la Playlist: {playlist_info['name']}")
print(f"Propietario: {playlist_info['owner']['display_name']}")
print(f"Descripción: {playlist_info['description']}")
print(f"Número de Canciones: {playlist_info['tracks']['total']}")
print("Canciones:")
for track in playlist_info['tracks']['items']:
    params = {
    'q': track['track']['name'],   # Término de búsqueda (nombre de la canción)
    'limit': 1 }
    response = requests.get(base_url, params=params)
    if(response.status_code==200):
        data = response.json()
        songs.append(data)
    print(f"- {track['track']['name']}")
    print(f"  Artista: {track['track']['artists'][0]['name']}")
