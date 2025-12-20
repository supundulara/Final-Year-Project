# scripts/run_experiments.py

from mininet.log import setLogLevel
from mininet.clean import cleanup
from topology import create_topology
from metrics import run_ping
from graph_builder import build_graph
import networkx as nx
import matplotlib.pyplot as plt

def main():
    setLogLevel('info')
    
    # Clean up any previous Mininet state
    cleanup()

    # 1️⃣ Create topology
    net, cameras, edge, cloud = create_topology()
    net.start()

    # 2️⃣ Run metrics
    run_ping(net, cameras)

    # 3️⃣ Build NetworkX graph
    G = build_graph(cameras, edge, cloud)

    # 4️⃣ Draw graph for visualization
    nx.draw(G, with_labels=True, node_size=1500)
    plt.savefig('network_graph.png')
    print("Graph saved to network_graph.png")

    # 5️⃣ Stop Mininet
    net.stop()

if __name__ == "__main__":
    main()