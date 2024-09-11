import asyncio
import time
import math
from conect import getSpotifyInstance, playlist, base_url, album_url
import aiohttp
import requests
start_time = time.time()
sp = getSpotifyInstance()

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
     

songs=[]
async def main():
    faltantes = 0
    correctas = 0
    max_concurrent_requests = math.ceil(cantSongs / 10)
    espera=(max_concurrent_requests/10) / 1.3
    if(cantSongs)>500:
        espera+=1

    if(cantSongs<51):
        max_concurrent_requests=50
        espera=0
    print(f"Realizando {cantSongs} solicitudes en lotes de {max_concurrent_requests} con una pausa de {espera} segundos entre lotes...")
    semaphore = asyncio.Semaphore(max_concurrent_requests)


    async with aiohttp.ClientSession() as session:
        print(f"Nombre de la Playlist: {playlist_info['name']}")
        print(f"Propietario: {playlist_info['owner']['display_name']}")
        print(f"Descripción: {playlist_info['description']}")
        print(f"Número de Canciones: {cantSongs}")
        print("Canciones:")
        
        tasks = []
        for i, track in enumerate(all_tracks):
            track_name = track['track']['name']
            tasks.append(fetch(session, track_name, semaphore))
            
            # Ejecuta en lotes de `max_concurrent_requests`
            if (i + 1) % max_concurrent_requests == 0 or (i + 1) == len(all_tracks):
                results = await asyncio.gather(*tasks)

                tasks = []
                await asyncio.sleep(espera) 
                for j, result in enumerate(results):
                    try:
                        #print(i + 1 - len(results) + j + 1, result['data'][0]['title'])
                        songs.append(result['data'][0])
                        correctas += 1
                    except:
                        print(result)
                        faltantes += 1
    print("Correctas fueron " + str(correctas))
    print("Faltantes fueron " + str(faltantes))  
    #await imprimir(songs)
    albumID=songs[0]['album']['id']
    print(albumID)


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