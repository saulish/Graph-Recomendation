-- Schema base (derivado de gr_schema.sql)
-- Nota: se omitieron owners/dumps/\restrict y secuencias del dump para mantenerlo portable.

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
    genre     text NOT NULL
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

-- Si quieres FK explícita (opcional):
-- ALTER TABLE public.songs_data
--   ADD CONSTRAINT songs_data_album_fk FOREIGN KEY (album_id) REFERENCES public.albums(album_id);
