import json
import numpy as np
from app.config import config


class GenreEmbeddingHelper:
    def __init__(self,
                 embeddings_path=f"{config.GENRES_EMBEDDINGS_PATH}genres_v{config.GENRES_EMBEDDINGS_VERSION}.json"):
        with open(embeddings_path, 'r', encoding='utf-8') as f:
            self.embeddings = json.load(f)
        print(f"Loaded: {len(self.embeddings)} genres")

    def get_embedding(self, genre_id):
        # Separte method to obtain a embedding from an id
        genre_id_str = str(genre_id)
        if genre_id_str in self.embeddings:
            return np.array(self.embeddings[genre_id_str]['embedding'])
        return None

    def similarity(self, genre_id1, genre_id2):
        # Separate method to compare a pair of genres
        emb1 = self.get_embedding(genre_id1)
        emb2 = self.get_embedding(genre_id2)

        if emb1 is not None and emb2 is not None:
            return cosine_sim(emb1, emb2)
        return 0.0

    def get_album_embedding(self, genre_ids):
        # Method     to obtain an embedding mean from an album
        embeddings_list = []
        for gid in genre_ids:
            emb = self.get_embedding(gid)
            if emb is not None:
                embeddings_list.append(emb)

        if embeddings_list:
            return np.mean(embeddings_list, axis=0)
        return None

    def album_similarity(self, genres_1, genres_2):
        # Method to fully compare 2 albums
        emb1 = self.get_album_embedding(genres_1)
        emb2 = self.get_album_embedding(genres_2)

        if emb1 is not None and emb2 is not None:
            return cosine_sim(emb1, emb2)
        return 0.0


def cosine_sim(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)


helper = GenreEmbeddingHelper()
