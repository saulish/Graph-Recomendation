import asyncio
import math
from .config import config
from .graph import Graph, compareSongs
import aiohttp
import json


def get_all_tracks(playlist_id, sp):
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=100)
    tracks.extend(results['items'])

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return tracks


async def fetch(session, track_name, semaphore):
    params = {
        'q': track_name,
        'limit': 1
    }
    async with semaphore:
        async with session.get(config.base_url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to search the track: {track_name}")
                return None


async def fetch_album(session, albumID, semaphore):
    async with semaphore:
        async with session.get(config.album_url + "/" + str(albumID)) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


async def fecth_track(session, trackID, semaphore):
    async with semaphore:
        async with session.get(config.track_Url + "/" + str(trackID)) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


async def main(datos, all_tracks, album_Res, track_Res, songs):
    max_concurrent_requests = math.ceil(len(all_tracks) / 10)
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with (aiohttp.ClientSession() as session):
        tasks = []
        tasks_album = []
        tasks_track = []

        for track in all_tracks:
            track_name = track['track']['name']
            songs.append(track_name)
            datos[track_name] = {}
            datos[track_name]['spotify_id'] = track['track']['id']
            datos[track_name]["name"] = track_name
            datos[track_name]['duration'] = track['track']['duration_ms']
            datos[track_name]['explicit'] = track['track']['explicit']
            datos[track_name]['popularity'] = track['track']['popularity']

            datos[track_name]['album'] = {}
            datos[track_name]['album']["type"] = track['track']['album']['album_type']
            datos[track_name]['album']["total_tracks"] = track['track']['album']['total_tracks']
            datos[track_name]['album']["name"] = track['track']['album']['name']
            datos[track_name]['album']["release_date"] = track['track']['album']['release_date']
            datos[track_name]['album']["artists"] = [artist['name'] for artist in track['track']['artists']]

            # Petición de búsqueda de la canción
            task = fetch(session, track_name, semaphore)
            tasks.append(task)

        # Procesa las canciones en este lote
        results = await asyncio.gather(*tasks)
        faileds = []
        for result, song in zip(results, all_tracks):
            try:
                track_name = song['track']['name']
                track_id = result['data'][0]['id']
                album_id = result['data'][0]['album']['id']
                artist_id = result['data'][0]['artist']['id']
                # For some reason, deezer just gives me only the id of the first artist
                datos[track_name]['deezer_id'] = track_id
                datos[track_name]['album_id'] = album_id
                datos[track_name]['album']['id'] = album_id
                datos[track_name]['artist_id'] = artist_id
                track_task = fecth_track(session, track_id, semaphore)
                tasks_track.append(track_task)
                album_task = fetch_album(session, album_id, semaphore)
                tasks_album.append(album_task)
            except Exception as e:
                print(f"Error in search: {e}")
                print(f"Deleting: {song['track']['name']}")
                del datos[song['track']['name']]
                songs.pop(songs.index(song['track']['name']))
                faileds.append(song)
        all_tracks = [track for track in all_tracks if track not in faileds]
        # Procesa los álbumes y pistas
        resA = await asyncio.gather(*tasks_album)
        for album_result, track in zip(resA, all_tracks):
            try:
                song_name = track['track']['name']
                datos[song_name]['album']['genres'] = [genero['name'] for genero in album_result['genres']['data']]
            except Exception as e:
                print(f"Error in album: {e}")

        resT = await asyncio.gather(*tasks_track)
        for track_result, track in zip(resT, all_tracks):
            try:
                song_name = track['track']['name']
                datos[song_name]['rank'] = track_result['rank']
                datos[song_name]['album']['bpm'] = track_result['bpm']
                datos[song_name]['album']['gain'] = track_result['gain']
            except Exception as e:
                print(f"Error in track: {e}")
    return datos, album_Res, track_Res


async def process_batch(datos, tmpTracks, album_Res, track_Res):
    songs = []
    await main(datos, tmpTracks, album_Res, track_Res, songs)
    return songs, datos


async def getGrafo(playlist_id, sp, playlist_info):
    n_playlist = playlist_info['tracks']['total']
    grafo = Graph(n_playlist)
    album_Res = []
    track_Res = []

    all_tracks = get_all_tracks(playlist_id, sp)
    total_tracks = len(all_tracks)
    batch_size = config.MAX_CONCURRENT_TRACKS
    datos = {}
    # Procesa las canciones en lotes de batch_size
    for i in range(0, total_tracks, batch_size):
        tmpTracks = all_tracks[i:i + batch_size]
        songs, datos = await process_batch(datos, tmpTracks, album_Res, track_Res)
        album_Res.clear()
        compareSongs(datos, grafo)
        payload = {"songs": songs, "datos": datos, "matrix": grafo.matrix, "batch_index": i // batch_size}

        yield (json.dumps(payload) + "\n").encode("utf-8")

    print("Fin del procesamiento de todas las canciones.")
    # grafo.read_graph()
    yield (json.dumps({"done": True}) + "\n").encode("utf-8")
