import requests
from bs4 import BeautifulSoup
import base64
from urllib.parse import urlencode
from conect import clientID as CLIENT_ID, secretID as CLIENT_SECRET, redirect as REDIRECT_URI
class Grafo:
    def __init__(self):
        self.nodos= []
        self.aristas =[]
    def agregar_nodo(self,nodo):
        if((nodo not in self.nodos )):
            self.nodos.append(nodo)
            return


    def get_arista(self):
        return self.aristas
    
    def get_peso_arista(self, origen, destino):
        for arista in self.aristas:
            if arista[0] == origen and arista[1] == destino:
                return arista[2]
          
        return None
    def agregar_arista(self, origen, destino, peso):
        if (not (self.get_peso_arista(origen,destino)))and origen != destino :
            self.aristas.append((origen,destino,peso))
            self.aristas.append((destino,origen,peso))
            return
   

listas={}



# Paso 1: Redirigir al usuario a la página de autorización de Spotify
auth_url = 'https://accounts.spotify.com/authorize'
params = {
    'client_id': CLIENT_ID,
    'response_type': 'code',
    'redirect_uri': REDIRECT_URI,
    'scope': 'user-read-private user-read-email',  # Especifica los alcances necesarios
}
authorization_url = f"{auth_url}?{urlencode(params)}"

print("Abre la siguiente URL en tu navegador para autorizar la aplicación:")
print(authorization_url)
# Paso 2: Manejar la redirección de vuelta desde Spotify






authorization_code = input("Pega el código de autorización aquí: ")




# Paso 3: Intercambiar el código de autorización por un token de acceso
token_url = 'https://accounts.spotify.com/api/token'
token_data = {
    'grant_type': 'authorization_code',
    'code': authorization_code,
    'redirect_uri': REDIRECT_URI,
}
token_headers = {
    'Authorization': f'Basic {base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()}',
}
token_response = requests.post(token_url, data=token_data, headers=token_headers)

if token_response.status_code == 200:
    token_info = token_response.json()
    access_token = token_info['access_token']
    #print("Token de acceso obtenido con éxito:", access_token)
else:
    print("Error al obtener el token de acceso.")

# A partir de este punto, puedes usar 'access_token' para hacer solicitudes a la API de Spotify.




def peticion_album(album_id):
    # URL de la API de Spotify para obtener información del álbum
    url = f'https://api.spotify.com/v1/albums/{album_id}'

    # Headers con el token de acceso
    headers = {
        'Authorization': 'Bearer ' + access_token,
    }

    # Realiza la solicitud GET
    response = requests.get(url, headers=headers)
    data = response.json()
    generos=data['genres']
    if response.status_code != 200:
        raise Exception(f"Error al obtener el álbum: {response.status_code}")

    # Devuelve los géneros del álbum.
    return generos


def comparacion(matriz, tamanio, tracks,grafo):
    
  
    i =int(0)
    j= int(0)
    for rola1 in tracks:
        grafo.agregar_nodo(rola1['track']['name'])
        cont=int(0)
        for rola2 in tracks:


            if rola1['track']['album']['release_date'][:4]==rola2['track']['album']['release_date'][:4]: 
                cont+=1#AÑO
            if (rola1['track']['duration_ms']-30 < rola2['track']['duration_ms'] and rola1['track']['duration_ms']+30 > rola2['track']['duration_ms']):
                cont+=1#DURACION 
            if rola1['track']['explicit'] == rola2['track']['explicit'] :
                cont+=1#EXPLICITA     
            if (rola1['track']['popularity']-20 < rola2['track']['popularity'] and rola1['track']['popularity']+20 > rola2['track']['popularity']):
                cont+=1#POPULARIDAD 
            if(matriz[i][j]==0 or i != j):
                matriz[i][j]=5-cont
                matriz[j][i]=5-cont
                if((5-cont)<=5):
                    grafo.agregar_nodo(rola2['track']['name'])
                    grafo.agregar_arista(rola1['track']['name'],rola2['track']['name'],5-cont)

            cont=0;
            j+=1;
        i+=1;
        j=0;
    print("EL GRAFO ES ",grafo.get_arista())
def ver_playlist():

    grafo = Grafo()
    # URL de la API de Spotify para obtener las playlists del usuario
    url = 'https://api.spotify.com/v1/me/playlists'

# Headers con el token de acceso del usuario
    headers = {
        'Authorization': 'Bearer ' + access_token,  # Reemplaza 'access_token' con el token de acceso del usuario
    }

# Realiza la solicitud GET para obtener las playlists del usuario
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        playlists_data = response.json()
        # Itera a través de las playlists y muestra sus nombres
        for playlist in playlists_data['items']:
            playlist_name = playlist['name']
            playlist_id = playlist['id']
            listas[playlist_name]=playlist_id
            print(f'Nombre de la playlist: {playlist_name}')
        select=input("Dame el nomnbre de la plalist que buscas")
        url = f'https://api.spotify.com/v1/playlists/{listas[select]}/tracks'
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        response = requests.get(url, headers=headers)
        tamanio_playlist=int()
        if response.status_code == 200:
            data = response.json()
            tamanio_playlist=data['total']
            matriz__playlist=[[0 for _ in range(tamanio_playlist)] for _ in range(tamanio_playlist)]
            tracks = data['items']
            comparacion(matriz__playlist,tamanio_playlist,tracks,grafo)

            print("HAY ",tamanio_playlist)
            for rola in tracks:
                #AÑADIR CONFIRMACION
                nombre = rola['track']['name']
                artistas = rola['track']['artists']  # Esta es una lista de artistas
                album = rola['track']['album']['name']
                album_id = rola['track']['album']['id']  # Obtén el ID del álbum
                anio = rola['track']['album']['release_date'][:4]
                duracion_ms = rola['track']['duration_ms'] 
                explicit = rola['track']['explicit'] 
                popularidad = rola['track']['popularity']
                nombres_artistas = [artista['name'] for artista in artistas]  # Extraer los nombres de los artistas

                #generos=peticion_album(album_id)
                

                print("Nombre de la canción:", nombre)
                print("Artistas:", ", ".join(nombres_artistas))  # Imprimir una lista de artistas separados por comas
                print("Álbum:", album)
                print("Año de lanzamiento:", anio)
                print("Duración en segundos:", (duracion_ms/1000))
                print("Popularidad:", popularidad)
                if(explicit):
                    print("Explicita")
                else:
                    print("No es explicita")
                
                print("")
                print("")
            for i in range(tamanio_playlist):
                for j in range(tamanio_playlist):
                    print(matriz__playlist[i][j], end=" ")  # Imprime el elemento y un espacio en lugar de un salto de línea
                print()  # Salto de línea al final de cada fila


    else:
        print(f'Error al obtener las playlists del usuario: Código de estado {response.status_code}')









def solo_una():
    url = 'https://api.spotify.com/v1/search'


# URL de la API de búsqueda de Spotify

    cancion = ""
    artista = ""

    cancion = input("Dame el nombre de la canción: ")
    artista = input("Ahora su artista: ")

    # Parámetros de búsqueda
    query = cancion + ' artist:' + artista  # Corregido el formato de la consulta
    params = {
        'q': query,
        'type': 'track',
    }

    # URL de la API de búsqueda de Spotify
    url = 'https://api.spotify.com/v1/search'  # Definir la URL antes de hacer la solicitud

    # Headers con el token de acceso (asegúrate de que access_token esté definido previamente)
    headers = {
        'Authorization': 'Bearer ' + access_token,
    }

    # Realiza la solicitud GET
    response = requests.get(url, params=params, headers=headers)

    # Procesa la respuesta JSON y obtén el ID de la canción
    if response.status_code == 200:
        data = response.json()
        if data['tracks']['items']:
            track_id = data['tracks']['items'][0]['id']  # Obtiene el ID de la primera canción en los resultados
        else:
            print('Canción no encontrada en Spotify.')
    else:
        print(f'Error al realizar la búsqueda: {response.status_code}')

    # ID de la canción que deseas obtener

    # URL de la API de Spotify para obtener información de una canción
    url = f'https://api.spotify.com/v1/tracks/{track_id}'

    # Headers con el token de acceso
    headers = {
        'Authorization': 'Bearer ' + access_token,
    }

    # Realiza la solicitud GET
    response = requests.get(url, headers=headers)

    # Procesa la respuesta JSON
    if response.status_code == 200:
        data = response.json()

        # Aquí puedes acceder a diferentes propiedades de la canción
        nombre_canción = data['name']
        artistas = [artista['name'] for artista in data['artists']]
        #artist_genres= data['genres']se puede obtener con el id del cantante
        album = data['album']['name']
        popularidad = data['popularity']

        # Imprime la información de la canción
        print(f'Nombre de la canción: {nombre_canción}')
        print(f'Artistas: {", ".join(artistas)}')
        print(f'Álbum: {album}')
        print(f'Popularidad: {popularidad}')


    else:
        print(f'Error al obtener información de la canción: {response.status_code}')

def main():
    while (True):
        print("Que deseas hacer?")
        print("[1] Ver y buscar en playlist")
        print("[2] Buscar una sola cancion")
        print("[3] salir")
        opcion=int(input())

        if(opcion==1):
            ver_playlist()
        elif(opcion==2):
            solo_una()
        else:
            break

main()