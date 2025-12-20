# scripts/graph_builder.py

import networkx as nx
import pandas as pd

def build_graph(cameras, edge, cloud, ping_csv="data/ping_results.csv"):
    """
    Creates a NetworkX graph with node and edge features
    """

    G = nx.DiGraph()

    # Add camera nodes
    for cam in cameras:
        G.add_node(cam.name, type="camera", cpu=0.1, gpu=0.0)

    # Add edge node
    G.add_node(edge.name, type="edge", cpu=0.8, gpu=1.0)

    # Add cloud node
    G.add_node(cloud.name, type="cloud", cpu=1.0, gpu=4.0)

    # Add edges from CSV
    df = pd.read_csv(ping_csv)
    for idx, row in df.iterrows():
        G.add_edge(row["src"], row["dst"], latency_ms=row["latency_ms"])

    return G
