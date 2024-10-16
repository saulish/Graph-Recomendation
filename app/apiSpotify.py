import asyncio
import time
import math
from app.conect import getSpotifyInstance, playlist, base_url, album_url, artist_url, track_Url
import aiohttp
import requests
import json
def get_all_tracks(playlist_id, sp):
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=100)
    tracks.extend(results['items'])
    
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    return tracks





async def imprimir(songs):
    for song in songs:
        print(song['title'])

async def fetch(session, track_name, semaphore):
    params = {
        'q': track_name,
        'limit': 1
    }
    async with semaphore:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None
async def fetch_album(session, albumID, semaphore):
    async with semaphore:
        async with session.get(album_url+"/"+str(albumID)) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None
             
async def fecth_track(session, trackID, semaphore):
    async with semaphore:
        async with session.get(track_Url+"/"+str(trackID)) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None
def imprimir(songs,datos):
    for song in songs:
        print(datos[song])

async def main(playlist_id, sp, datos, all_tracks, playlist_info, album_Res, track_Res, songs):
    faltantes = 0
    correctas = 0
    album_c = 0
    album_f = 0
    track_c = 0
    track_f = 0
    max_concurrent_requests = math.ceil(len(all_tracks) / 10)
    espera = (max_concurrent_requests / 10) / 1.2
    espera = 4  # tiempo de espera fijo para simplificar

    semaphore = asyncio.Semaphore(max_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        tasks = []
        tasks_album = []
        tasks_track = []

        for track in all_tracks:
            track_name = track['track']['name']
            songs.append(track_name)
            datos[track_name] = [track_name, track['track']['album']['album_type'],
                                 track['track']['album']['total_tracks'],
                                 track['track']['album']['name'],
                                 track['track']['album']['release_date'],
                                 [artist['name'] for artist in track['track']['artists']],
                                 track['track']['duration_ms'],
                                 track['track']['explicit'],
                                 track['track']['popularity']]
            
            # Petición de búsqueda de la canción
            task = fetch(session, track_name, semaphore)
            tasks.append(task)

        # Procesa las canciones en este lote
        results = await asyncio.gather(*tasks)

        for result in results:
            try:
                track_id = result['data'][0]['id']
                album_id = result['data'][0]['album']['id']

                track_task = fecth_track(session, track_id, semaphore)
                tasks_track.append(track_task)
                album_task = fetch_album(session, album_id, semaphore)
                tasks_album.append(album_task)

                correctas += 1
            except Exception as e:
                print(f"Error: {e}")
                faltantes += 1

        # Procesa los álbumes y pistas
        resA = await asyncio.gather(*tasks_album)
        for album_result in resA:
            try:
                album_result['genres']
                album_Res.append(album_result)
                album_c += 1
            except Exception as e:
                print(f"Error: {e}")
                album_f += 1

        resT = await asyncio.gather(*tasks_track)
        for track_result in resT:
            try:
                track_result['bpm']
                track_Res.append(track_result)
                track_c += 1
            except Exception as e:
                print(f"Error: {e}")
                track_f += 1
        try:
            for i, song in enumerate(songs):
                datos[song].append(track_Res[i]['rank'])
                datos[song].append(track_Res[i]['bpm'])
                datos[song].append(track_Res[i]['gain'])
                datos[song].append([genero['name'] for genero in album_Res[i]['genres']['data']])
        except Exception as e:
            print(f"Error: {e}")
    return datos, album_Res, track_Res


def getGrafo(playlist_id, sp, playlist_info):
    datos = {}
    songs = []
    album_Res = []
    track_Res = []

    all_tracks = get_all_tracks(playlist_id, sp)
    total_tracks = len(all_tracks)

    # Procesa las canciones en lotes de 15
    for i in range(0, total_tracks, 15):
        tmpTracks = all_tracks[i:i+15]
        asyncio.run(main(playlist_id, sp, datos, tmpTracks, playlist_info, album_Res, track_Res, songs))
        yield json.dumps(
            {
                'songs': songs,
                'datos': datos
            }
        ) + "\n"  # Realiza el yield tras cada lote de 15 canciones
    
    print("Fin del procesamiento de todas las canciones.")



