import asyncio
import math
from .config import config
from .postgresConnection import conn
import aiohttp
import json
import time


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


async def process_batch(datos, all_tracks, songs, model):
    embeddings = []
    max_concurrent_requests = math.ceil(len(all_tracks) / 10)
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with (aiohttp.ClientSession() as session):
        tasks = []
        tasks_album = []
        tasks_track = []
        faileds = []  # List to identify the searches that failed
        for track in all_tracks:
            try:
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
            except Exception as e:
                print(f"Error while taking data: {e}")
                print(f"Probably song has not all the info")
                print(f"Deleting: {track['track']['name']}")
                del datos[track['track']['id']]
                songs.pop(songs.index(track['track']['name']))
                faileds.append(track)

        # Re-adding the tracks to remove those that failed
        all_tracks = [track for track in all_tracks if track not in faileds]
        # Search of each song
        results = await asyncio.gather(*tasks)
        faileds = []
        album_ids = []  # List to separate the logic of the search and the album tasks
        repeated_albums = {}  # List of those albums that will not be saved, (for already being cached or duplicated)
        for result, song in zip(results, all_tracks):  # Results of the search of search song
            try:
                spotify_id = song['track']['id']
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
        # Consult if there's albums to cache
        data, cached_albums = conn.consult_cached_albums([album[0] for album in album_ids])
        if data:
            # print(f"Cached albums: \n{cached_albums}\nRepeated albums: {repeated_albums}")
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
                # Create the embedding of the iteration track
                embedding = model.encode({spotify_id: datos[spotify_id]})
                if embedding is None:
                    raise "Embedding encoding error"
                # Transform into correct type
                embedding = embedding.squeeze().tolist()
                # Save it for the later 2D creation
                embeddings.append(embedding)
                # Save in the dict to put in the database
                datos[spotify_id]['embedding'] = embedding
                #conn.insert_song(datos[spotify_id])
                if album_id in repeated_albums and 'song' in repeated_albums[album_id] and spotify_id in \
                        repeated_albums[album_id]['song']:
                    # The albums that were duplicated or cached should not be saved
                    print(f"Commited song {song_name}, but avoiding repeated album {album_name}")
                    continue  # If the song has a repeated album, do not commit the album and genree
                print(f"Inserting {song_name} from the album {album_name} and the id {album_id}")
                #conn.insert_album(datos[spotify_id]['album'])
                #conn.insert_album_genres(datos[spotify_id]['album']['id'],
                #                         [genre['id'] for genre in datos[spotify_id]['album']['genres']])
                #conn.insert_genres(datos[spotify_id]['album']['genres'])
            except Exception as e:
                print(f"Error while inserting data: {e}")
                print(f"Commited song {song_name}, data:\n {datos[spotify_id]}\n{datos[spotify_id]['album']}\n")
                conn.rollback()
        conn.commit()
    return songs, datos, embeddings


async def cache_producer(embeddings, cached_data, model, queue, full_cache=False):
    # Create embeddings for cached songs
    try:
        # Here if are at least MIN_FIT_SONGS cached, to avoid retraining umap every time
        if (not model.umap_fitted and len(embeddings) >= config.MIN_FIT_SONGS) or full_cache:
            embeddings_2d = await asyncio.to_thread(model.reduct, embeddings, True)  # Shape (batch_size, 2)
        else:
            embeddings_2d = None
    except Exception as e:
        print(f"Error while calculating embeddings in the cache producer: {e}")
        embeddings_2d = None
    payload = create_payload(cached_data, embeddings_2d)
    await queue.put(payload)


async def api_producer(total_tracks, all_tracks, all_data, model, buffer_data, queue):
    songs_without_2d = 0
    for i in range(0, total_tracks, config.BATCH_SIZE):
        iteration = int(i / config.BATCH_SIZE) + 1
        batch_tracks = all_tracks[i:i + config.BATCH_SIZE]
        left_tracks = len(all_tracks[i + config.BATCH_SIZE:])
        songs, all_data, embeddings = await process_batch(all_data, batch_tracks, [], model)
        songs_without_2d += len(songs)
        # Create embeddings for cached songs
        try:
            # Save the data and embeddings
            buffer_data['embeddings'].extend(embeddings)
            buffer_data['data'].update(all_data)
            # It works by two main conditions
            # if the batch is multiple of MIN_UMAP_SIZE or there are at least MIN_UMAP_BATCH_SIZE songs without 2D
            # or, if it's the last iteration and at least are 1 song that has not been processed to 2D
            if ((iteration % config.MIN_UMAP_SIZE == 0 or songs_without_2d >= config.MIN_UMAP_BATCH_SIZE) or
                    (left_tracks == 0 and songs_without_2d > 0)):

                # fit is used to avoid training umap every time, if in cache are not enough songs to train
                # (MIN_FIT_SONGS), it waits until a batch is completed
                # Also, do not need here check if are MIN_FIT_SONGS songs, because already is over MIN_UMAP_BATCH_SIZE
                # ir it's the las iteration
                fit = not model.umap_fitted
                embeddings_2d = await asyncio.to_thread(model.reduct, buffer_data['embeddings'], fit)
                songs_without_2d = 0
            else:
                embeddings_2d = None
        except Exception as e:
            print(f"Error while calculating embeddings in the api producer: {e}")
            embeddings_2d = None
        # The payload it's created using all the data and the fresh creates 2D embeddings
        payload = create_payload(buffer_data['data'], embeddings_2d)
        # The payload must be put in the queue to be processed
        await queue.put(payload)


async def consumer_main(all_tracks, real_total, model):
    queue = asyncio.Queue(maxsize=config.MAX_QUEUE_SIZE)
    total_tracks = len(all_tracks)
    all_data = {}
    # This buffer it's necessary for the UMAP model, and also saving the data to send each iteration all the new songs
    buffer_data = {'embeddings': [], 'data': {}}
    start = time.time()
    # Directly take the cached songs with all data because of the nice optimized db
    cached_data, cached_names, invalid_songs, embeddings = (
        conn.consult_cached_song([track['track']['id'] for track in all_tracks]))
    if cached_data:
        # This way we separate how many songs are cached (in cached data) and the rest of them (all_tracks)
        all_tracks = [track for track in all_tracks if track['track']['name']
                      not in cached_names and track['track']['name'] not in invalid_songs]
        total_tracks = len(all_tracks)
        # Create the task of the cached songs
        try:
            # Here are the cached songs, so the ones with embedding
            # Saving the embeddings in a list, using extend to have it only in one list
            buffer_data['embeddings'].extend(embeddings)
            # The same with data, but with update to have all the data of each song
            buffer_data['data'].update(cached_data)
            fit = (real_total == len(cached_names)) or len(cached_names) >= config.MIN_FIT_SONGS
            cache_task = asyncio.create_task(cache_producer(embeddings, cached_data,
                                                            model, queue, fit))

        except Exception as e:
            print(f"Error while adding embedding to the buffer {e}")
            cache_task = None
    else:
        cache_task = None
    # Create the task of the api query
    api_task = asyncio.create_task(api_producer(total_tracks, all_tracks, all_data, model, buffer_data, queue))
    producers = 2 if cache_task is not None else 1

    # It's easier to move the logic into a small function, insted of duplicating code
    def check_producers():
        nonlocal cache_task, producers, api_task
        if cache_task and cache_task.done():
            # If are finished, we reduce a producer from the count
            producers -= 1
            # And mark it as None
            cache_task = None
        if api_task and api_task.done():
            producers -= 1
            api_task = None

    # The loop will run until both task finishes
    while producers > 0:
        try:
            # First takes the batch from the queue
            batch = await asyncio.wait_for(queue.get(), timeout=0.5)
            # Still using yield to send the batch
            yield (json.dumps(batch) + "\n").encode("utf-8")
            # Mark this as done
            queue.task_done()

            # Then must check if the tasks still running
            check_producers()
        except asyncio.TimeoutError:
            check_producers()
        except Exception as e:
            print(f"Error while producing: {e}")

    yield (json.dumps({"done": True}) + "\n").encode("utf-8")
    end = time.time()
    print(f"{real_total} songs processed in {end - start:.2f} seconds.")


def create_payload(data, embeddings_2d):
    payload = [
        {
            'id': song_id,
            'x': float(embeddings_2d[i][0]) if embeddings_2d is not None else None,
            'y': float(embeddings_2d[i][1]) if embeddings_2d is not None else None,
            'song_name': data[song_id]['name'],
            'artists': data[song_id]['album']['artists'],
            'album_name': data[song_id]['album']['name']
        }
        for i, song_id in enumerate(data)
    ]
    return payload
