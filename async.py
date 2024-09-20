import asyncio
import time
import math
from conect import getSpotifyInstance, playlist, base_url, album_url, artist_url, track_Url
import aiohttp
import requests
start_time = time.time()
sp = getSpotifyInstance()
datos={}
playlist_id = playlist.split('/')[-1]
# Obtiene la información de la playlist

# Obtiene la información de la playlist
def get_all_tracks(playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=100)
    tracks.extend(results['items'])
    
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    
    return tracks

playlist_info = sp.playlist(playlist_id)
# Obtiene todas las pistas de la playlist
all_tracks = get_all_tracks(playlist_id)
print(all_tracks[0])
#print(all_tracks[0]['track'])
cantSongs=len(all_tracks)


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
songs=[]
album_Res=[]
track_Res=[]
async def main():
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
        print("Canciones:")

        tasks = []
        tasks_album = []
        tasks_track = []
        for i, track in enumerate(all_tracks):
            track_name = track['track']['name']

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

                        # Realiza las peticiones a Deezer para la canción y el álbum
                        
                        track_task = fecth_track(session, track_id, semaphore)
                        tasks_track.append(track_task)
                        album_task = fetch_album(session, album_id, semaphore)
                        tasks_album.append(album_task)

                        
                        
                        
                        # Espera ambas peticiones
                        #track_result, album_result = await asyncio.gather(track_task, album_task)
                        '''
                        # Aquí puedes hacer algo con los resultados de la canción y el álbum
                        #print(f"Track ID: {track_result['id']}, Album ID: {album_result['id']}")
                        #print("track_result") 
                        try:
                            track_result['bpm']
                            #print(track_result['bpm']) 
                            track_c += 1
                        except Exception as e:
                            print(f"Error: {e}")
                            track_f += 1


                        #print("album_result")
                        try:
                            album_result['genres']
                            #print(album_result['genres'])
                            album_c += 1
                        except Exception as e:
                            print(f"Error: {e}")
                            album_f += 1
                        '''
                        songs.append(result)

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

    print(f"Correctas fueron {correctas}")
    print(f"Faltantes fueron {faltantes}")
    print(f"Album Correctas fueron {album_c}")
    print(f"Album Faltantes fueron {album_f}")
    print(f"Track Correctas fueron {track_c}")
    print(f"Track Faltantes fueron {track_f}")



    '''
    response = requests.get(album_url+"/"+str(albumID))
    if(response.status_code==200):
        data = response.json()
        #print(data)
    '''
    print("El tamaño final fue de "+str(len(songs)))
    #print(songs[0])
    end_time = time.time()
    print(f"El tiempo de ejecución del bloque de código fue de {end_time - start_time} segundos")
    print(songs[0])
    return;
    for rola in songs:
        params = {
        'q': rola['title'],
        'limit': 1 }
        print(f"La cancion es {rola['title']} y la respuesta es:")
        response = requests.get(base_url, params=params)
        
        if(response.status_code==200):
            print("response.json() Esta es la peticion del titulo de las rolas")
        else:
            print("Error")
        







asyncio.run(main())


print("Fin del programa")

#res=requests.get(base_url, params=params)
#print(res.json()['data'])
#eun-j2p-m52