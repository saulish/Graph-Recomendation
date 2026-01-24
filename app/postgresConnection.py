import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv


class Connection:
    def __init__(self):
        load_dotenv()
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        self.cur = self.conn.cursor()

    # ------------------ INSERTS ------------------

    def insert_song(self, song):
        query = """
        INSERT INTO songs_data (
            spotify_id, deezer_id, name, rank, popularity,
            duration, explicit, album_id, artists_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            song['spotify_id'],
            song['deezer_id'],
            song['name'],
            song['rank'],
            song['popularity'],
            song['duration'],
            song['explicit'],
            song['album_id'],
            json.dumps(song['artist_id'])
        )
        self.cur.execute(query, values)

    def insert_album(self, album):
        album_types = {
            'single': 1,
            'album': 2,
            'compilation': 3
        }
        query = """
        INSERT INTO albums (
            album_id, name, bpm, gain, release_date,
            artists, album_type, number_songs, genres_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            album['id'],
            album['name'],
            album['bpm'],
            album['gain'],
            album['release_date'],
            json.dumps(album['artists']),
            album_types[album['type']],
            album['total_tracks'],
            json.dumps([g['id'] for g in album['genres']])
        )
        self.cur.execute(query, values)

    def insert_genres(self, genres):
        query = """
        INSERT INTO genres (
            deezer_id, genre
        )
        VALUES %s
        ON CONFLICT (deezer_id) DO NOTHING
        """
        values = [
            (g['id'], g['name']) for g in genres
        ]
        execute_values(self.cur, query, values)

    def insert_album_genres(self, album_id, genres):
        query = """
        INSERT INTO album_genres (album_id, genre_id) 
        VALUES %s        
        """
        try:
            values = [(album_id, genre) for genre in genres]
            execute_values(self.cur, query, values)
        except Exception as e:
            print(f"Error inserting in album_genres table: {e}")
            print(f"Album id: {album_id}, genres: {genres}")

    # ------------------ QUERIES ------------------

    def consult_cached_song(self, songs):
        query = ("""
SELECT
    s.spotify_id, s.name AS track_name, s.rank, s.popularity,
    s.duration, s.explicit,s.artists_id,

    a.album_id, a.name AS album_name, a.bpm, a.gain,
    a.release_date, a.artists, a.album_type, a.number_songs, a.genres_id,
    COALESCE(array_agg(g.genre) FILTER (WHERE g.genre IS NOT NULL),'{}') AS genres
FROM songs_data s
JOIN albums a
    ON s.album_id = a.album_id
LEFT JOIN album_genres ag
    ON ag.album_id = a.album_id
LEFT JOIN genres g
    ON g.deezer_id = ag.genre_id
WHERE s.spotify_id = ANY(%s)
GROUP BY
    s.spotify_id, s.name, s.rank, s.popularity,
    s.duration, s.explicit, s.artists_id,
    a.album_id, a.name, a.bpm, a.gain,
    a.release_date, a.artists, a.album_type, a.number_songs;
                 """)
        self.cur.execute(query, (songs,))
        self.commit()
        cached = {}
        songs = []
        for track in self.cur.fetchall():
            try:
                name = track[1]
                cached[name] = {}
                cached[name]['spotify_id'] = track[0]
                cached[name]['name'] = name
                cached[name]['rank'] = track[2]
                cached[name]['popularity'] = track[3]
                cached[name]['duration'] = track[4]
                cached[name]['explicit'] = track[5]
                cached[name]['artist_id'] = str(track[6])
                cached[name]['album_id'] = str(track[7])

                cached[name]['album'] = {}
                cached[name]['album']['name'] = track[8]
                cached[name]['album']['id'] = str(track[7])
                cached[name]['album']['bpm'] = track[9]
                cached[name]['album']['gain'] = track[10]
                cached[name]['album']['release_date'] = str(track[11].isoformat())
                cached[name]['album']['artists'] = track[12]
                cached[name]['album']['type'] = track[13]
                cached[name]['album']['total_tracks'] = track[14]
                cached[name]['album']['genres'] = {}
                cached[name]['album']['genres'] = [{'id': id, 'name': genre} for id, genre in zip(track[15], track[16])]

                songs.append(name)

            except Exception as e:
                print(f"Error consulting the database: {e}")
                del cached[track[1]]
                continue
        return cached, songs

    def consult_cached_albums(self, albums):
        query = ("""
SELECT a.album_id, a.genres_id,
    COALESCE(array_agg(g.genre) FILTER (WHERE g.genre IS NOT NULL), '{}') AS genres
FROM albums a
LEFT JOIN album_genres ag
    ON ag.album_id = a.album_id
LEFT JOIN genres g
    ON g.deezer_id = ag.genre_id
WHERE a.album_id = ANY(%s)
GROUP BY a.album_id, a.name;
                 """)
        self.cur.execute(query, (albums,))
        self.commit()
        albums = []
        data = {}
        for album in self.cur.fetchall():
            album_id = album[0]
            albums.append(album_id)
            data[album_id] = [{'id': id, 'name': genre} for id, genre in zip(album[1], album[2])]
        return data, albums

    # ------------------ TRANSACTION CONTROL ------------------

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.cur.close()
        self.conn.close()


conn = Connection()
