import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from app.config import config


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
            duration, explicit, album_id, artists_id, embedding, embedding_ver
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            json.dumps(song['artist_id']),
            song['embedding'],
            config.get_embedding_version()
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
        SELECT s.name, s.embedding, s.spotify_id, a.artists, a.name
        FROM songs_data s 
        JOIN albums a ON s.album_id =a.album_id
        WHERE s.spotify_id = ANY(%s)        
        AND s.embedding IS NOT NULL;
                 """)
        self.cur.execute(query, (songs,))
        self.commit()
        cached = {}
        songs = []
        embeddings = []
        invalid_songs = []
        for track in self.cur.fetchall():
            try:
                name = track[0]
                embedding_str = track[1]
                spotify_id = track[2]

                if embedding_str is None:
                    if name in cached:
                        del cached[name]
                    invalid_songs.append(name)
                    print(f"No embedding found for song {name}, removing song.")
                    continue
                else:
                    embedding = list(map(float, embedding_str.strip('[]').split(',')))
                    embeddings.append(embedding)
                cached[spotify_id] = {'name': name, 'album': {
                    'artists': track[3], 'name': track[4]}}
                songs.append(name)

            except Exception as e:
                print(f"Error consulting the database: {e}")
                invalid_songs.append(track[0])
                if track[0] in cached:
                    del cached[track[0]]
                continue
        return cached, songs, invalid_songs, embeddings

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

    def consult_cosine_similarity(self, album_id_1, album_id_2):
        if album_id_1 == album_id_2:
            return 1.0
        query = ("""
        WITH album_embeddings AS (
            SELECT
                ag.album_id,
                avg(g.embedding) AS embedding
            FROM album_genres ag
            JOIN genres g ON g.deezer_id = ag.genre_id
            WHERE ag.album_id IN (%s, %s)
              AND g.embedding IS NOT NULL
            GROUP BY ag.album_id
        )
        SELECT
            a.album_id AS album_a,
            b.album_id AS album_b,
            1 - (a.embedding <=> b.embedding) AS cosine_similarity
        FROM album_embeddings a
        JOIN album_embeddings b
            ON a.album_id <> b.album_id;
        """)
        self.cur.execute(query, (album_id_1, album_id_2))
        self.commit()
        if self.cur.rowcount == 0:
            return None
        return self.cur.fetchone()[-1]

    # ------------------ TRANSACTION CONTROL ------------------

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.cur.close()
        self.conn.close()


conn = Connection()
