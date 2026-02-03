import torch
from .model_architecture import SongAutoencoder
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd


class SongEncoderInference:

    def __init__(self, model_path='app/models/song_encoder.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        checkpoint = torch.load(model_path, map_location=self.device)

        # Recreate model
        self.model = SongAutoencoder(
            input_dim=checkpoint['input_dim'],
            embedding_dim=checkpoint['embedding_dim'],
            hidden_dim=checkpoint['hidden_dim']
        ).to(self.device)

        self.model.load_state_dict(checkpoint['full_model_state_dict'])
        self.model.eval()

        self.numeric_features = checkpoint['numeric_features']
        self.scaler_center = checkpoint['scaler_center']
        self.scaler_scale = checkpoint['scaler_scale']
        self.imputer_statistics = checkpoint['imputer_statistics']

        print(f"Model loaded from: {model_path}")
        print(f"Embedding dim: {checkpoint['embedding_dim']}")

    def preprocess_songs(self, data):
        # Takes the raw data dict and preprocesses it into model input format
        album_type_map = {'single': 1, 'album': 2, 'compilation': 3}
        processed_songs = []
        
        for name in data:
            song = data[name]
            
            # Process year
            release_date = song['album']['release_date']
            if isinstance(release_date, str):
                try:
                    release_year = float(release_date.split('-')[0])
                except (ValueError, AttributeError):
                    release_year = 2000.0
            else:
                release_year = float(release_date) if release_date else 2000.0
            
            # Explicit song to 0/1
            explicit_val = 1.0 if song['explicit'] else 0.0
            
            # Album type mapping
            album_type_val = song['album']['type']
            if isinstance(album_type_val, str):
                album_type_num = float(album_type_map.get(album_type_val, 2))
            else:
                album_type_num = float(album_type_val)
            
            # BPM extraction and cleaning
            bpm_val = song['album'].get('bpm', 0)
            if pd.isna(bpm_val) or bpm_val is None:
                bpm_val = 0.0
            else:
                bpm_val = float(bpm_val)
            
            # Extract numeric features in the EXACT ORDER of the checkpoint
            # ['rank', 'popularity', 'duration', 'bpm', 'gain', 'album_type', 'number_songs', 'explicit', 'release_year']
            numeric_values = np.array([
                float(song['rank']),
                float(song['popularity']),
                float(song['duration']),
                bpm_val,
                float(song['album']['gain']),
                album_type_num,
                float(song['album']['total_tracks']),
                explicit_val,
                release_year
            ], dtype=np.float32)
            
            # Impute BPM if necessary (index 3)
            if numeric_values[3] == 0.0 or np.isnan(numeric_values[3]):
                numeric_values[3] = self.imputer_statistics[3]
            
            # Normalize with StandardScaler
            numeric_scaled = (numeric_values - self.scaler_center) / self.scaler_scale
            
            # Process genre embedding
            genre_embedding = song['album'].get('embedding', None)      
            if genre_embedding is None:
                genre_embedding = np.zeros(128, dtype=np.float32)
        
            # Concat numeric and genre embeddings
            combined = np.concatenate([numeric_scaled, genre_embedding])
            
            if combined.shape[0] != 137:
                raise ValueError(f"Input has {combined.shape[0]} dims, expected 137")
            
            processed_songs.append(combined)
        
        return np.array(processed_songs, dtype=np.float32)

    def encode(self, data):
        # The starting point, uses the dict data to produce embeddings of songs
        if not data:
            raise ValueError("No data to process")
        
        # Preprocess the songs, using the correct order of features
        X = self.preprocess_songs(data)
        
        # Convert to tensor
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        # Generate embeddings (N, 128)
        with torch.no_grad():
            embeddings = self.model.encode(X_tensor).cpu().numpy()
        
        return embeddings

    def similarity(self, embedding1, embedding2):
        return cosine_similarity(embedding1, embedding2)


model = SongEncoderInference()
