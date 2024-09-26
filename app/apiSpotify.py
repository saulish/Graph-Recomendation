import asyncio
import time
import math
from app.conect import getSpotifyInstance, playlist, base_url, album_url, artist_url, track_Url
import aiohttp
import requests

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

async def main(playlist_id, sp, datos, all_tracks, playlist_info,album_Res, track_Res, songs):
    cantSongs=len(all_tracks)
    faltantes = 0
    correctas = 0
    album_c = 0
    album_f=0
    track_c=0
    track_f=0
    max_concurrent_requests = math.ceil(cantSongs / 10)
    #if(max_concurrent_requests > 50): max_concurrent_requests/=3
    espera = (max_concurrent_requests / 10) / 1.2
    if cantSongs > 500:
        espera += 0.6
    if cantSongs < 51:
        max_concurrent_requests = 50
        espera = 4.5
    #max_concurrent_requests = 50
    #espera=0.75
    print(f"Realizando {cantSongs} solicitudes en lotes de {max_concurrent_requests} con una pausa de {espera} segundos entre lotes...")
    semaphore = asyncio.Semaphore(max_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        print(f"Nombre de la Playlist: {playlist_info['name']}")
        print(f"Propietario: {playlist_info['owner']['display_name']}")
        print(f"Descripción: {playlist_info['description']}")
        print(f"Número de Canciones: {cantSongs}")

        tasks = []
        tasks_album = []
        tasks_track = []
        for i, track in enumerate(all_tracks):
            track_name = track['track']['name'] 
            songs.append(track_name)
            datos[track_name]=[track_name , track['track']['album']['album_type'],
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

            if (i + 1) % max_concurrent_requests == 0 or (i + 1) == len(all_tracks):
                # Ejecuta las peticiones en paralelo y espera resultados
                results = await asyncio.gather(*tasks)
                tasks = []

                # Procesa los resultados
                for result in results:
                    try:
                        track_id = result['data'][0]['id']
                        album_id = result['data'][0]['album']['id']

                        track_task = fecth_track(session, track_id, semaphore)
                        tasks_track.append(track_task)
                        album_task = fetch_album(session, album_id, semaphore)
                        tasks_album.append(album_task)

                        #songs.append(result['data'][0]['title'])

                        correctas += 1
                    except Exception as e:
                        print(f"Error: {e}")
                        faltantes += 1
                #print("---------------------------------------------")
                await asyncio.sleep(espera)               
                resA = await asyncio.gather(*tasks_album)               
                for album_result in resA:
                    try:
                        album_result['genres']
                        album_Res.append(album_result)
                        #print(album_result['genres'])
                        album_c += 1
                    except Exception as e:
                        print(f"Error: {e}")
                        album_f += 1

                tasks_album = []
                await asyncio.sleep(espera)

                resT = await asyncio.gather(*tasks_track)
                for track_result in resT:
                    try:
                        track_result['bpm']
                        track_Res.append(track_result)
                        #print(track_result['bpm']) 
                        track_c += 1
                    except Exception as e:
                        print(f"Error: {e}")
                        track_f += 1
                tasks_track = []
                await asyncio.sleep(espera)
        try:
            for i, song in enumerate(songs):
                datos[song].append(track_Res[i]['bpm'])
                datos[song].append(track_Res[i]['gain'])

                datos[song].append([genero['name'] for genero in album_Res[i]['genres']['data']])
        except Exception as e:
            print(f"Error: {e}")
            imprimir(songs,datos)
                            
                        

    print(f"Correctas fueron {correctas}")
    print(f"Faltantes fueron {faltantes}")
    print(f"Album Correctas fueron {album_c}")
    print(f"Album Faltantes fueron {album_f}")
    print(f"Track Correctas fueron {track_c}")
    print(f"Track Faltantes fueron {track_f}")


    return;


def getGrafo(playlist_id, sp, playlist_info):
    datos={}
    songs=[]
    album_Res=[]
    track_Res=[]

    all_tracks = get_all_tracks(playlist_id, sp)

    asyncio.run(main(playlist_id, sp, datos, all_tracks, playlist_info, album_Res, track_Res, songs))


    print("Fin del programa")
    imprimir(songs,datos)
    return songs,datos



