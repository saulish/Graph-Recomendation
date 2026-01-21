from .embedding_implementation.genres_helper import helper


class Graph:
    def __init__(self, size: int):
        self.nodes = []
        self.matrix = [[0 for i in range(size)] for j in range(size)]

    def add_vertex(self, value: any):
        if value in self.nodes: return

        self.nodes.append(value)

    def get_weigth(self, origen, destino):
        i = self.nodes.index(origen)
        j = self.nodes.index(destino)
        return self.matrix[i][j]

    def add_edge(self, origen, destino, w: int):
        self.add_vertex(origen)
        self.add_vertex(destino)
        i = self.nodes.index(origen)
        j = self.nodes.index(destino)
        self.matrix[i][j] = w
        self.matrix[j][i] = w

    def read_graph(self):
        for node in self.nodes:
            i = self.nodes.index(node)
            print(f"Node: {node}")
            for j in range(len(self.matrix[i])):
                if self.matrix[i][j] > 0:
                    print(f"{node} -> {self.nodes[j]}       w={self.matrix[i][j]}")


def compareYears(name1: str, name2: str, year1: str, year2: str, w: int) -> int:
    # It's necessary because the year might be in 'YYYY' format or 'YYYY-MM-DD'
    # try:

    if (len(year1.split('-'))) == 1 or len(year2.split('-')) == 1:
        if len(year1.split('-')) > 0:
            year1 = year1.split('-')[0]
        if len(year2.split('-')) > 0:
            year2 = year2.split('-')[0]

        year_diff = int(max(year1, year2)) - int(min(year1, year2))
        if year_diff < 2:
            w *= 2
        elif year_diff < 5:
            w += year_diff
    else:

        year_diff = int(max(year1.split('-')[0], year2.split('-')[0])) - int(min(year1.split('-')[0],
                                                                                 year2.split('-')[0]))
        month_diff = int(max(year1.split('-')[1], year2.split('-')[1])) - int(min(year1.split('-')[1],
                                                                                  year2.split('-')[1]))
        if year_diff < 2:
            if year_diff == 0:
                w *= 2
            else:
                w += month_diff

    return w


def compareSongs(tracks: dict, graph):
    for i, (id_1, song1) in enumerate(tracks.items()):
        name1 = song1['name']
        graph.add_vertex(name1)
        for j, (id_2, song2) in enumerate(tracks.items()):
            name2 = song2['name']
            if name1 == name2:  # If the songs have the same name
                continue
            w = int(0)
            graph.add_vertex(name2)
            if song1['album']['type'] == song2['album']['type']:  # Album type
                w += 3

            # If there´s x more songs
            if (int(max(song1['album']['total_tracks'], song2['album']['total_tracks'])) -
                    int(min(song1['album']['total_tracks'], song2['album']['total_tracks'])) < 5):
                w += 3
            if song1['album']['name'] == song2['album']['name']:  # Album name
                w *= 2

            # Album release date
            w = compareYears(name1, name2, song1['album']['release_date'],
                             song2['album']['release_date'], w)

            # Same artist on the album
            for artist in song1['album']['artists']:
                if artist in song2['album']['artists']: w += 3

            seconds_diff = (int(max(song1['duration'], song2['duration'])) -
                            int(min(song1['duration'], song2['duration'])))
            if seconds_diff < 30:  # Duration
                w *= 2
            if song1['explicit'] == song2['explicit']:  # Is explicit?
                w += 2

            popularity_diff = (int(max(song1['popularity'], song2['popularity']))
                               - int(min(song1['popularity'], song2['popularity'])))
            if popularity_diff < 10:  # Spotify's popularity (0-100)
                w += 3
            ranking_diff = (int(max(song1['rank'], song2['rank']))
                            - int(min(song1['rank'], song2['rank'])))
            if ranking_diff < 1000:  # Dezzer ranking
                w += 3
            bpm_diff = (float(max(song1['album']['bpm'], song2['album']['bpm']))
                        - float(min(song1['album']['bpm'], song2['album']['bpm'])))
            if bpm_diff < 20:  # BPM
                w += 5
            gain_diff = (float(max(song1['album']['gain'], song2['album']['gain']))
                         - float(min(song1['album']['gain'], song2['album']['gain'])))
            if gain_diff < 20:  # Gain
                w += 5
            genres_1 = [genre['name'] for genre in song1['album']['genres']]  # Genres
            genres_2 = [genre['name'] for genre in song2['album']['genres']]
            for g in genres_1:
                if g in genres_2:
                    w *= 5

            genres_id_1 = [g_id['id'] for g_id in song1['album']['genres']]
            genres_id_2 = [g_id['id'] for g_id in song2['album']['genres']]

            embeddings_diff = helper.album_similarity(genres_id_1, genres_id_2)
            w += int((embeddings_diff+0.5)*w)

    # graph.read_graph()
