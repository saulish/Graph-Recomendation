-- Schema base (derivado de gr_schema.sql)
-- Nota: se omitieron owners/dumps/\restrict y secuencias del dump para mantenerlo portable.

-- Enable pgvector extension (PostgreSQL 16.11+)
-- Requires pgvector compiled/installed: https://github.com/pgvector/pgvector
CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;

CREATE TABLE IF NOT EXISTS public.albums (
    album_id  text PRIMARY KEY,
    name      text NOT NULL,
    bpm       double precision NOT NULL,
    gain      double precision NOT NULL,
    release_date date NOT NULL,
    artists   jsonb NOT NULL,
    album_type integer NOT NULL,
    number_songs integer NOT NULL,
    genres_id jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS public.artists (
    deezer_id integer PRIMARY KEY,
    name      text NOT NULL
);

CREATE TABLE IF NOT EXISTS public.genres (
    deezer_id integer PRIMARY KEY,
    genre     text NOT NULL,
    embedding vector(128)  -- 128-dimensional genre embeddings (pgvector)
);

-- Many-to-many relationship: albums <-> genres (optimized for joins with embeddings)
CREATE TABLE IF NOT EXISTS public.album_genres (
    album_id  text NOT NULL,
    genre_id  integer NOT NULL,
    PRIMARY KEY (album_id, genre_id),
    FOREIGN KEY (album_id) REFERENCES public.albums(album_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES public.genres(deezer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.songs_data (
    deezer_id   text NOT NULL,
    name        text NOT NULL,
    rank        integer NOT NULL,
    popularity  integer NOT NULL,
    duration    double precision NOT NULL,
    explicit    boolean NOT NULL,
    album_id    text NOT NULL,
    artists_id  jsonb NOT NULL,
    spotify_id  text PRIMARY KEY
);

-- Optional indexes for performance
CREATE INDEX IF NOT EXISTS idx_album_genres_album ON public.album_genres(album_id);
CREATE INDEX IF NOT EXISTS idx_album_genres_genre ON public.album_genres(genre_id);
CREATE INDEX IF NOT EXISTS idx_genres_embedding ON public.genres USING ivfflat (embedding vector_cosine_ops);

