# Graph Recommendation - Análisis de Playlists de Spotify

**API Backend para analizar playlists de Spotify con embeddings de canciones y visualización de similitud**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)

## Características

- **Integración OAuth con Spotify** - Autenticación segura con Spotipy
- **Embeddings de Canciones** - Vectores 128D vía autoencoder PyTorch (audio + género)
- **Visualización 2D** - Reducción dimensional UMAP para frontend interactivo
- **Caché Inteligente** - PostgreSQL con pgvector para búsquedas rápidas
- **Procesamiento Paralelo** - Arquitectura productor-consumidor con asyncio.Queue
- **Respuestas Streaming** - Batches NDJSON para renderizado progresivo
- **Enriquecimiento Deezer** - Datos de BPM, gain, rank y géneros

---

## Inicio Rápido

### Requisitos Previos

- Python 3.10+ (3.11 recomendado)
- PostgreSQL 16+ con [extensión pgvector](https://github.com/pgvector/pgvector)
- Credenciales Spotify Developer ([Consíguelas aquí](https://developer.spotify.com/dashboard))

### Instalación

1. **Clonar repositorio**:
```bash
git clone https://github.com/saulish/GR_back.git
cd GR_back
```

2. **Instalar dependencias**:
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

3. **Configurar base de datos**:
```bash
# Crear base de datos
createdb graph_recomendation

# Ejecutar schema
psql graph_recomendation < db/schema.sql
```

4. **Configurar entorno** (`app/.env`):
```env
SPOTIFY_API_KEY=tu_client_id
SPOTIFY_API_SECRET=tu_client_secret

FRONT_PORT=5500
BACK_PORT=8000

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=graph_recomendation
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_contraseña
```

5. **Ejecutar servidor**:
```bash
python run.py
```

6. **Probar**:
```bash
curl http://127.0.0.1:8000/
# Respuesta: {"message":"Alive and running"}
```

---

## Endpoints del API

### Autenticación
- `GET /auth/login` - Iniciar OAuth o verificar sesión
- `GET /auth/callback` - Callback OAuth (redirige al frontend)
- `DELETE /auth/logout` - Limpiar sesión

### Playlists
- `GET /playlists` - Listar playlists de Spotify del usuario (requiere auth)

### Análisis
- `GET /analysis/playlist/{id}` - Analizar playlist con embeddings (streaming NDJSON)

### Salud
- `GET /` - Estado del servidor

> **Documentación completa del API**: Ver [docs/api-reference.md](docs/api-reference.md) para schemas y ejemplos detallados

---

## ¿Cómo Funciona?

1. **Usuario se autentica** con OAuth de Spotify
2. **Backend obtiene** tracks de la playlist desde API de Spotify
3. **Verificación de caché**: Consulta PostgreSQL para embeddings existentes
4. **Enriquecimiento** (tracks no cacheados): Llamadas concurrentes a API de Deezer para BPM, gain, géneros
5. **Generación de embeddings**: Autoencoder PyTorch crea vectores 128D
6. **Reducción dimensional**: UMAP reduce a 2D para visualización
7. **Streaming**: Batches NDJSON progresivos enviados al frontend

### Flujo de Procesamiento

```
Petición Usuario → cache_producer (DB) ─┐
                                        ├─→ Queue → consumer_main → Frontend
                   api_producer (APIs) ─┘
               
- cache_producer: Resultados instantáneos de canciones cacheadas
- api_producer: Llamadas paralelas Spotify/Deezer para canciones no cacheadas
- Ambos alimentan una cola compartida para respuesta streaming
```

> **Detalles de arquitectura**: Ver [docs/architecture.md](docs/architecture.md)

---

## Embeddings de Canciones

Cada canción se representa como un **vector de 128 dimensiones** combinando:

| Tipo de Feature | Dimensiones | Fuente |
|-----------------|-------------|--------|
| Features de audio | 9 | BPM, gain, duración, popularidad, etc. |
| Embeddings de género | 128 | Vectores de género pre-entrenados (promedio ponderado) |

**Arquitectura del autoencoder**:
- Input: 137D (9 audio + 128 género)
- Encoder: Capas densas → **Cuello de botella 128D**
- Decoder: Reconstrucción simétrica

**Reducción UMAP** (128D → 2D):
- Permite visualización interactiva
- Preserva estructura local/global
- Optimizado: Entrenar una vez, transformar muchas (~10-50x más rápido)

> **Detalles técnicos**: Ver [docs/embeddings.md](docs/embeddings.md)

---

## Frontend

Este backend está diseñado para visualización interactiva. Repositorio del frontend:

**https://github.com/saulish/Graph-Recomendation-Frontend**

**Formato de respuesta** (NDJSON):
```json
[
  {
    "id": "spotify_track_id",
    "x": 0.25,
    "y": -0.83,
    "song_name": "Nombre de Track",
    "artists": ["Artista 1"],
    "album_name": "Nombre de Álbum"
  }
]
{"done": true}
```

---

## Configuración

### Ajuste de Rendimiento

Edita `app/config.py` para ajustar el procesamiento por batches:

```python
BATCH_SIZE = 20              # Canciones por batch de API
MIN_UMAP_SIZE = 3            # Frecuencia de ejecución UMAP
MIN_UMAP_BATCH_SIZE = 60     # Mínimo de canciones para UMAP
MIN_FIT_SONGS = 40           # Mínimo de canciones cacheadas para entrenar UMAP
MAX_QUEUE_SIZE = 5           # Tamaño del buffer de la cola
```

**Recomendaciones**:
- Aumentar `BATCH_SIZE` para procesamiento más rápido (cuidado con rate limits)
- Disminuir `MIN_UMAP_SIZE` para actualizaciones más frecuentes en frontend
- Ajustar `MIN_FIT_SONGS` según tasa típica de cache hits

---

## Base de Datos

El sistema usa PostgreSQL con **extensión pgvector** para almacenamiento de embeddings y consultas de similitud.

### Tablas Principales

| Tabla | Propósito |
|-------|-----------|
| `songs_data` | Canciones cacheadas con embeddings 128D |
| `albums` | Metadata de álbumes (BPM, gain, géneros) |
| `genres` | Catálogo de géneros con embeddings 128D |
| `album_genres` | Relación muchos-a-muchos álbum ↔ géneros |

### Uso de pgvector

```sql
-- Encontrar canciones similares vía similitud coseno
SELECT name, 1 - (embedding <=> target_embedding) AS similarity
FROM songs_data
ORDER BY embedding <=> target_embedding
LIMIT 10;
```

> **Detalles de base de datos**: Ver [docs/database.md](docs/database.md) para schema y optimización

---

## Estructura del Proyecto

```
app/
├── api/
│   └── routes/
│       ├── auth.py          # Endpoints de autenticación
│       ├── playlist.py      # Gestión de playlists
│       └── analysis.py      # Análisis de canciones
├── core/
│   └── dependencies.py      # Inyección de dependencias (auth)
├── schemas/
│   └── response.py          # Modelos de respuesta Pydantic
├── embeddings/
│   ├── model_architecture.py
│   └── model_inference.py   # Autoencoder PyTorch + UMAP
├── models/
│   └── song_encoder.pth     # Pesos del modelo entrenado
├── app.py                   # Aplicación principal FastAPI
├── config.py                # Configuración & middleware
├── conect.py                # Lógica de APIs Spotify/Deezer
├── apiSpotify.py            # Implementación productor-consumidor
└── postgresConnection.py    # Conexión a base de datos

db/
└── schema.sql               # Schema PostgreSQL con pgvector

docs/
├── architecture.md          # Productor-consumidor & optimización UMAP
├── embeddings.md            # Detalles técnicos de embeddings
├── api-reference.md         # Documentación completa del API
└── database.md              # Schema PostgreSQL & uso de pgvector
```

---

## Desarrollo

### Docs Interactivas del API

FastAPI proporciona documentación auto-generada:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Ejecutar Tests

```bash
# TODO: Agregar suite de tests (roadmap Fase 1)
pytest tests/
```

### Calidad de Código

Mejoras recientes de refactorización:
- Endpoints modulares con APIRouter (auth, playlists, analysis)
- Schemas Pydantic para validación y manejo de errores
- Inyección de dependencias para autenticación
- Respuestas de error estandarizadas

---

## Roadmap

### Completado

- OAuth de Spotify con gestión de sesiones
- Embeddings de canciones (autoencoder PyTorch + UMAP)
- Embeddings de géneros con pgvector
- Procesamiento paralelo productor-consumidor
- Caché PostgreSQL con versionado de modelo
- Refactorización de endpoints (estructura modular)
- Schemas Pydantic & inyección de dependencias

### En Progreso

**Fase 1: Testing & Logging**
- [ ] Logging estructurado (logs JSON con trazabilidad de requests)
- [ ] Suite de tests (pruebas unitarias, integración, endpoints)

**Fase 2: Escalabilidad**
- [ ] Redis para almacenamiento de sesiones (soporte multi-instancia)
- [ ] Optimización de connection pooling
- [ ] Rate limiting para endpoints del API

**Fase 3: Recomendaciones**
- [ ] Sistema de recomendación de canciones (similitud coseno)
- [ ] Endpoint de canciones similares
- [ ] Generación de playlists basada en canciones semilla

**Fase 4: Infraestructura**
- [ ] Containerización con Docker
- [ ] Pipeline CI/CD (testing y deployment automatizado)
- [ ] Configuración lista para producción

---

## Troubleshooting

### Problemas Comunes

**"Invalid or expired token"**
- Verificar cookies del navegador
- Asegurar que el origen del frontend coincida con CORS en `config.py`
- Re-autenticar vía `/auth/login`

**Errores de conexión a base de datos**
- Verificar que PostgreSQL esté corriendo
- Revisar credenciales en `app/.env`
- Asegurar que la base de datos existe: `createdb graph_recomendation`

**Extensión pgvector no encontrada**
- Instalar extensión: `CREATE EXTENSION IF NOT EXISTS vector;`
- Verificar versión de PostgreSQL (16+ recomendado)

**Resultados vacíos de API Deezer**
- Algunos tracks pueden no existir en el catálogo de Deezer
- El sistema automáticamente omite y continúa procesando

---

## Rendimiento

**Tiempos típicos de análisis** (playlist de 100 canciones):

| Escenario | Tiempo | Tasa de Cache Hits |
|-----------|--------|--------------------|
| 100% cacheado | ~1-2s | 100% |
| 50% cacheado | ~15-20s | 50% |
| 0% cacheado | ~30-40s | 0% |

**Optimizaciones**:
- Productor-consumidor: ~2-3x más rápido primer batch
- UMAP fit-once: ~90% reducción en overhead
- Caché PostgreSQL: ~100ms para 100+ embeddings

---

## Contribuciones

¡Contribuciones bienvenidas! Por favor:

1. Hacer fork del repositorio
2. Crear rama de feature (`git checkout -b feature/caracteristica-increible`)
3. Hacer commit de cambios (`git commit -m 'Agregar característica increíble'`)
4. Push a la rama (`git push origin feature/caracteristica-increible`)
5. Abrir un Pull Request

---

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para detalles.

---

## Proyectos Relacionados

- **Frontend**: https://github.com/saulish/Graph-Recomendation-Frontend
- **Documentación**: https://github.com/saulish/GR_back/tree/main/docs
- **pgvector**: https://github.com/pgvector/pgvector

---

## Soporte

Para documentación detallada, ver la carpeta `docs/`:

- [Documentación de Arquitectura](docs/architecture.md)
- [Detalles Técnicos de Embeddings](docs/embeddings.md)
- [Referencia del API](docs/api-reference.md)
- [Schema de Base de Datos](docs/database.md)

¿Preguntas? ¡Abre un issue en GitHub!

---

*Construido con FastAPI, PyTorch, PostgreSQL*
