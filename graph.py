class Graph:
    def __init__(self):
        self.vertices = {}
        self.edges = []
        self.edge_indices = {}

    def add_vertex(self, key, vertex):
        self.vertices[key] = vertex

    def add_edge(self, edge):
        self.edges.append(edge)
        self.edge_indices[(edge.start, edge.end)] = len(self.edges) - 1

    def get_edge(self, start, end):
        return self.edges[self.edge_indices[(start, end)]]

    def get_vertex(self, key):
        return self.vertices[key]

    def get_vertices(self):
        return self.vertices.keys()

    def get_edges(self):
        return self.edges


class Node:
    def __init__(self, val):
        self.value = val
        self.vecinos = {}

    def add_neighbor(self, vecino, peso):
        self.vecinos[vecino] = peso

    def get_connections(self):
        return self.vecinos.keys()

    def get_Value(self):
        return self.value

    def get_Peso(self, vecino):
        return self.vecinos[vecino]


def aStar(graph, start, end):
    print("A*")



