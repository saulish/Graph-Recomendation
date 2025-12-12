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
    for i, (name1, song1) in enumerate(tracks.items()):
        graph.add_vertex(song1[0])
        for j, (name2, song2) in enumerate(tracks.items()):
            if name1 == name2:  # If the songs have the same name
                continue
            w = int(0)
            graph.add_vertex(name2)
            if song1[1] == song2[1]:  # Album type
                w += 3

            # If there´s x more songs
            if int(max(song1[2], song2[2])) - int(min(song1[2], song2[2])) < 5:
                w += 3
            if song1[3] == song2[3]:  # Album name
                w *= 2

            # Album release date
            w = compareYears(name1, name2, song1[4], song2[4], w)

            # Same artist on the album
            for artist in song1[5]:
                if artist in song2[5]: w += 3

            seconds_diff = int(max(song1[6], song2[6])) - int(min(song1[6], song2[6]))
            if seconds_diff < 30:  # Duration
                w *= 2
            if song1[7] == song2[7]:  # Is explicit?
                w += 2

            popularity_diff = int(max(song1[8], song2[8])) - int(min(song1[8], song2[8]))
            if popularity_diff < 10:  # Spotify's popularity (0-100)
                w += 3
            ranking_diff = int(max(song1[9], song2[9])) - int(min(song1[9], song2[9]))
            if ranking_diff < 1000:  # Dezzer ranking
                w += 3
            bpm_diff = float(max(song1[10], song2[10])) - float(min(song1[10], song2[10]))
            if bpm_diff < 20:  # BPM
                w += 5
            gain_diff = float(max(song1[11], song2[11])) - float(min(song1[11], song2[11]))
            if gain_diff < 20:  # Gain
                w += 5

            for genre in song1[12]:  # Genre
                if genre in song2[12]:
                    w *= 5

            graph.add_edge(name1, name2, w)

    # graph.read_graph()
