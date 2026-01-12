import asyncio
import math
from .config import config
from .graph import Graph, compareSongs
from .postgresConnection import conn
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
                print(f"Error consulting album: {albumID}")
                return None


async def fecth_track(session, trackID, semaphore):
    async with semaphore:
        async with session.get(config.track_Url + "/" + str(trackID)) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


def fix_release_date(date):
    if not date:
        return "1999-01-01"
    if len(date.split("-")) == 2:
        date += "-01"
    elif len(date.split("-")) == 1:
        date += "-01" * 2
    return date


async def main(datos, all_tracks, album_Res, track_Res, songs):
    max_concurrent_requests = math.ceil(len(all_tracks) / 10)
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with (aiohttp.ClientSession() as session):
        tasks = []
        tasks_album = []
        tasks_track = []

        for track in all_tracks:
            track_name = track['track']['name']
            track_id = track['track']['id']
            songs.append(track_name)  # Maybe use {'id','name'} or something
            datos[track_id] = {}
            datos[track_id]['spotify_id'] = track_id
            datos[track_id]["name"] = track_name
            datos[track_id]['duration'] = track['track']['duration_ms']
            datos[track_id]['explicit'] = track['track']['explicit']
            datos[track_id]['popularity'] = track['track']['popularity']

            datos[track_id]['album'] = {}
            datos[track_id]['album']["type"] = track['track']['album']['album_type']
            datos[track_id]['album']["total_tracks"] = track['track']['album']['total_tracks']
            datos[track_id]['album']["name"] = track['track']['album']['name']
            datos[track_id]['album']["release_date"] = fix_release_date(track['track']['album']['release_date'])
            datos[track_id]['album']["artists"] = [artist['name'] for artist in track['track']['artists']]
            search = f"{track_name} {", ".join(datos[track_id]['album']["artists"])}"
            # Petición de búsqueda de la canción
            task = fetch(session, search, semaphore)
            tasks.append(task)

        # Search of each song
        results = await asyncio.gather(*tasks)
        faileds = []  # List to identify the searchs that failed
        album_ids = []  # List to separate the logic of the search and the album tasks
        repeated_albums = {}  # List of those albums that will not be saved, (for already being cached or duplicated)
        for result, song in zip(results, all_tracks):  # Results of the search of search song
            try:
                spotify_id = song['track']['id']
                track_name = song['track']['name']
                track_id = str(result['data'][0]['id'])
                album_id = str(result['data'][0]['album']['id'])
                artist_id = str(result['data'][0]['artist']['id'])
                # For some reason, deezer just gives me only the id of the first artist
                datos[spotify_id]['deezer_id'] = track_id
                datos[spotify_id]['album_id'] = album_id
                datos[spotify_id]['album']['id'] = album_id
                datos[spotify_id]['artist_id'] = artist_id

                # Creation of the tasks of the track petition
                track_task = fecth_track(session, track_id, semaphore)
                tasks_track.append(track_task)
                # If the current id is in the list, means it's repeated
                if album_id in [album[0] for album in album_ids]:
                    # If album_id is not in the list, means it's a new one in the repeated
                    if album_id not in repeated_albums:
                        # Save the names in a list is the best option because there can be many songs of the same album
                        repeated_albums[album_id] = {'song': []}
                    repeated_albums[album_id]['song'].append(spotify_id)
                else:  # If id is not in the list, is a new one
                    album_ids.append((album_id, spotify_id))
            except Exception as e:
                print(f"Error in search: {e}")
                # If a search had no results, means the song does not exist, so it must be ignored
                print(f"Deleting: {song['track']['name']}")
                del datos[song['track']['id']]
                songs.pop(songs.index(song['track']['name']))
                faileds.append(song)
        # Re-adding the tracks to remove those that failed
        all_tracks = [track for track in all_tracks if track not in faileds]
        # Consult if there´s albums to cache
        data, cached_albums = conn.consult_cached_albums([album[0] for album in album_ids])
        if data:
            print(f"Cached albums: \n{cached_albums}\nRepeated albums: {repeated_albums}")
            # Save the track names of those cached and duplicated songs
            track_id_cached = [track['track']['id'] for track in all_tracks if
                               (datos[track['track']['id']]['album']['id'] in repeated_albums
                                and track['track']['id']
                                in repeated_albums[datos[track['track']['id']]['album']['id']]['song'])
                               or
                               (track['track']['name'] for track in all_tracks if
                                datos[track['track']['id']]['album']['id'] in cached_albums)
                               ]
            for spotify_id in track_id_cached:  # Iterate through the cached tracks
                name = datos[spotify_id]['name']
                album_id = datos[spotify_id]['album']['id']
                if album_id in data:
                    # Means it's cached
                    # Save the cached where it belongs
                    datos[spotify_id]['album']['genres'] = data[album_id]
                    if album_id in repeated_albums:
                        # Means it's repeated and cached!!
                        # This parts checks if there's a repeated album with the same id just get cached
                        # Remember: repeated={'album id': 'song':['names'}, data={'id': [], 'genres' : []}
                        repeated_track_name = repeated_albums[album_id]['song']
                        for repeated in repeated_track_name:
                            datos[repeated]['album']['genres'] = data[album_id]
                    else:
                        # else it's here to initialize the list, it's repeated or not, needs to be in repeated_albums to
                        # be ignored later
                        repeated_albums[album_id] = {'song': []}
                    # At any case, we need to add the song to the repeated list
                    repeated_albums[album_id]['song'].append(spotify_id)

                if album_id in repeated_albums and album_id in data:
                    # Means it's repeated
                    # If it's repeated, it means it's on the album id
                    if (album_id, spotify_id) in album_ids:
                        # Erase the id of the list of album ids to avoid been consulted
                        album_ids.pop(album_ids.index((album_id, spotify_id)))

        # Create the tasks of the albums that were not cached
        for album_id in album_ids:
            album_task = fetch_album(session, album_id[0], semaphore)
            tasks_album.append(album_task)

        # Fetching albums petitions
        resA = await asyncio.gather(*tasks_album)
        for album_result, track in zip(resA, album_ids):
            try:
                # Here are fetched albums
                # Iterating over the results and the tracks to save the genres on each album song
                spotify_id = track[1]

                album_id = track[0]
                datos[spotify_id]['album']['genres'] = [{'name': genero['name'], 'id': genero['id']}
                                                       for genero in album_result['genres']['data']]
                if album_id in repeated_albums:
                    # Here are fetched and duplicated albums
                    for dup_id in repeated_albums[album_id]['song']:
                        datos[dup_id]['album']['genres'] = [{'name': genero['name'], 'id': genero['id']}
                                                              for genero in album_result['genres']['data']]
            except Exception as e:
                print(f"Error in album: {e}")
        # Fetching tracks petitions
        resT = await asyncio.gather(*tasks_track)
        for track_result, track in zip(resT, all_tracks):
            try:
                # Saving the track taken from the api
                spotify_id = track['track']['id']
                song_name = datos[spotify_id]['name']
                album_name = datos[spotify_id]['album']['name']
                album_id = datos[spotify_id]['album']['id']
                datos[spotify_id]['rank'] = track_result['rank']
                datos[spotify_id]['album']['bpm'] = track_result['bpm']
                datos[spotify_id]['album']['gain'] = track_result['gain']
            except Exception as e:
                print(f"Error in track: {e}")
                continue
            try:
                conn.insert_song(datos[spotify_id])
                if album_id in repeated_albums and 'song' in repeated_albums[album_id] and spotify_id in \
                        repeated_albums[album_id]['song']:
                    # The albums that were duplicated or cached should not be saved
                    print(f"Commited song {song_name}, but avoiding repeated album {album_name}")
                    continue  # If the song has a repeated album, do not commit the album and genree
                print(f"Inserting {song_name} from the album {album_name} and the id {album_id}")
                conn.insert_album(datos[spotify_id]['album'])
                conn.insert_genres(datos[spotify_id]['album']['genres'])
            except Exception as e:
                print(f"Error while inserting data: {e}")
                print(f"Commited song {song_name}, data:\n {datos[spotify_id]}\n{datos[spotify_id]['album']}\n")
                conn.rollback()
        conn.commit()
    return datos, album_Res, track_Res


async def process_batch(datos, tmp_tracks, album_res, track_res):
    songs = []
    await main(datos, tmp_tracks, album_res, track_res, songs)
    return songs, datos


temporal_db = {}


async def getGrafo(playlist_id, sp, playlist_info):
    n_playlist = playlist_info['tracks']['total']
    grafo = Graph(n_playlist)
    album_Res = []
    track_Res = []

    all_tracks = get_all_tracks(playlist_id, sp)
    # To remove if those songs are not valid
    dup_tracks = set()
    all_tracks = [t for t in all_tracks if t.get('track') is not None and t['track']['type'] != 'episode'
                  and t['track']['id'] not in dup_tracks and not dup_tracks.add(t['track']['id'])]
    total_tracks = len(all_tracks)
    batch_size = config.MAX_CONCURRENT_TRACKS
    datos = {}
    data, cahed_names = conn.consult_cached_song([track['track']['id'] for track in all_tracks])
    if data:
        all_tracks = [track for track in all_tracks if track['track']['name'] not in cahed_names]
        total_tracks = len(all_tracks)
        compareSongs(data, grafo)
        payload = {"songs": cahed_names, "datos": data, "matrix": grafo.matrix, "batch_index": 0}
        yield (json.dumps(payload) + "\n").encode("utf-8")
        print(f"Cached songs: {cahed_names}")
    # Procesa las canciones en lotes de batch_size
    import time
    start = time.time()
    for i in range(0, total_tracks, batch_size):
        tmpTracks = all_tracks[i:i + batch_size]
        songs, datos = await process_batch(datos, tmpTracks, album_Res, track_Res)
        album_Res.clear()
        compareSongs(datos, grafo)
        payload = {"songs": songs, "datos": datos, "matrix": grafo.matrix, "batch_index": i // batch_size}

        yield (json.dumps(payload) + "\n").encode("utf-8")
    end = time.time()
    print("Fin del procesamiento de todas las canciones.")
    print(f"Se procesaron {total_tracks} in {end - start:.4f} segundos.")
    # grafo.read_graph()
    yield (json.dumps({"done": True}) + "\n").encode("utf-8")
