import networkx as nx
from pyvis.network import Network
import random

# Load the GraphML file
# G = nx.read_graphml("./outputs/local_excalidraw/graph_chunk_entity_relation.graphml")
G = nx.read_graphml("./outputs/local_excalidraw_split_by_file/graph_chunk_entity_relation.graphml")

# Create a Pyvis network
net = Network(height="100vh", notebook=True)

# Convert NetworkX graph to Pyvis network
net.from_nx(G)


# Add colors and title to nodes
for node in net.nodes:
    node["color"] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    if "description" in node:
        node["title"] = node["description"]

# Add title to edges
for edge in net.edges:
    if "description" in edge:
        edge["title"] = edge["description"]

# Save and display the network
net.show("./outputs/local_excalidraw_split_by_file/knowledge_graph_sinppet.html")
