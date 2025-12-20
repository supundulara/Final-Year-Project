#!/usr/bin/env python3
# examples/load_dataset_example.py

"""
Example: How to load and use the generated GNN dataset
Demonstrates loading data, building graphs, and preparing for GNN training
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os


def load_dataset(dataset_dir="data/dataset"):
    """
    Load the generated dataset
    
    Returns:
        tuple: (nodes_df, edges_df, labels_df)
    """
    nodes = pd.read_csv(os.path.join(dataset_dir, "nodes.csv"))
    edges = pd.read_csv(os.path.join(dataset_dir, "edges.csv"))
    labels = pd.read_csv(os.path.join(dataset_dir, "labels.csv"))
    
    return nodes, edges, labels


def print_dataset_stats(nodes, edges, labels):
    """
    Print statistics about the dataset
    """
    print("="*70)
    print(" DATASET STATISTICS")
    print("="*70)
    
    print(f"\n📊 Dataset Size:")
    print(f"  Nodes: {len(nodes):,} samples")
    print(f"  Edges: {len(edges):,} samples")
    print(f"  Labels: {len(labels):,} samples")
    
    print(f"\n🌐 Scenarios:")
    num_scenarios = nodes['scenario_idx'].nunique()
    print(f"  Total scenarios: {num_scenarios}")
    print(f"  Scenario names: {nodes['scenario_name'].unique().tolist()}")
    
    print(f"\n🔷 Node Types:")
    node_type_counts = nodes['node_type'].value_counts()
    for node_type, count in node_type_counts.items():
        print(f"  {node_type}: {count}")
    
    print(f"\n🔗 Link Types:")
    link_type_counts = edges['link_type'].value_counts()
    for link_type, count in link_type_counts.items():
        print(f"  {link_type}: {count}")
    
    print(f"\n🎯 QoS Distribution:")
    qos_satisfied = labels['qos_satisfied'].sum()
    qos_total = len(labels)
    qos_rate = (qos_satisfied / qos_total * 100) if qos_total > 0 else 0
    print(f"  Satisfied: {qos_satisfied}/{qos_total} ({qos_rate:.1f}%)")
    print(f"  Not satisfied: {qos_total - qos_satisfied}/{qos_total} ({100-qos_rate:.1f}%)")
    
    print(f"\n📈 Performance Metrics:")
    print(f"  Latency range: {labels['e2e_latency_ms'].min():.2f} - {labels['e2e_latency_ms'].max():.2f} ms")
    print(f"  Throughput range: {labels['throughput_mbps'].min():.2f} - {labels['throughput_mbps'].max():.2f} Mbps")
    print(f"  Packet loss range: {labels['packet_loss_pct'].min():.2f}% - {labels['packet_loss_pct'].max():.2f}%")
    print(f"  GPU utilization range: {labels['gpu_utilization_pct'].min():.2f}% - {labels['gpu_utilization_pct'].max():.2f}%")


def build_graph_for_scenario(scenario_idx, nodes, edges, labels):
    """
    Build a NetworkX graph for a specific scenario
    
    Args:
        scenario_idx: Scenario index (0-15)
        nodes, edges, labels: DataFrames
    
    Returns:
        nx.DiGraph: Graph with node and edge attributes
    """
    # Filter data for this scenario
    s_nodes = nodes[nodes['scenario_idx'] == scenario_idx]
    s_edges = edges[edges['scenario_idx'] == scenario_idx]
    s_labels = labels[labels['scenario_idx'] == scenario_idx]
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes with features
    for _, row in s_nodes.iterrows():
        G.add_node(
            row['node_id'],
            node_type=row['node_type'],
            cpu_capacity=row['cpu_capacity'],
            gpu_capacity=row['gpu_capacity'],
            cv_model=row['cv_model'],
            fps=row['fps'],
            queue_occupancy=row['queue_occupancy_avg'],
            model_gflops=row['model_gflops'],
            model_params=row['model_params']
        )
    
    # Add edges with features
    for _, row in s_edges.iterrows():
        G.add_edge(
            row['src'],
            row['dst'],
            bandwidth_mbps=row['bandwidth_mbps'],
            delay_ms=row['delay_ms'],
            queue_size=row['queue_size'],
            queue_discipline=row['queue_discipline'],
            link_type=row['link_type']
        )
    
    # Add performance labels as graph attributes
    performance = {}
    for _, row in s_labels.iterrows():
        path = (row['src_node'], row['dst_node'])
        performance[path] = {
            'latency': row['e2e_latency_ms'],
            'throughput': row['throughput_mbps'],
            'packet_loss': row['packet_loss_pct'],
            'gpu_util': row['gpu_utilization_pct'],
            'qos_satisfied': row['qos_satisfied']
        }
    
    G.graph['performance'] = performance
    G.graph['scenario_name'] = s_nodes.iloc[0]['scenario_name']
    
    return G


def visualize_scenario(G, scenario_idx, save_path=None):
    """
    Visualize a scenario graph
    """
    plt.figure(figsize=(12, 8))
    
    # Color nodes by type
    node_colors = []
    for node in G.nodes():
        node_type = G.nodes[node]['node_type']
        if node_type == 'camera':
            node_colors.append('lightblue')
        elif node_type == 'edge':
            node_colors.append('orange')
        else:  # cloud
            node_colors.append('lightgreen')
    
    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Draw
    nx.draw(G, pos,
            node_color=node_colors,
            node_size=1000,
            with_labels=True,
            font_size=8,
            font_weight='bold',
            arrows=True,
            edge_color='gray',
            width=2)
    
    plt.title(f"Scenario {scenario_idx}: {G.graph['scenario_name']}", fontsize=16)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved visualization to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def prepare_for_gnn_training(nodes, edges, labels):
    """
    Example: Prepare data for GNN training
    
    This shows how to extract features and labels for PyTorch Geometric
    """
    print("\n" + "="*70)
    print(" PREPARING FOR GNN TRAINING")
    print("="*70)
    
    # Example: Prepare features for one scenario
    scenario_idx = 0
    s_nodes = nodes[nodes['scenario_idx'] == scenario_idx]
    s_edges = edges[edges['scenario_idx'] == scenario_idx]
    s_labels = labels[labels['scenario_idx'] == scenario_idx]
    
    print(f"\nScenario {scenario_idx}: {s_nodes.iloc[0]['scenario_name']}")
    
    # Node features
    node_features = s_nodes[[
        'cpu_capacity',
        'gpu_capacity',
        'fps',
        'queue_occupancy_avg',
        'model_gflops'
    ]].values
    
    print(f"\n📊 Node features shape: {node_features.shape}")
    print(f"   Features: cpu, gpu, fps, queue, gflops")
    
    # Edge features
    edge_features = s_edges[[
        'bandwidth_mbps',
        'delay_ms',
        'queue_size'
    ]].values
    
    print(f"📊 Edge features shape: {edge_features.shape}")
    print(f"   Features: bandwidth, delay, queue_size")
    
    # Labels (for classification)
    qos_labels = s_labels['qos_satisfied'].values
    print(f"📊 Labels shape: {qos_labels.shape}")
    print(f"   Task: QoS satisfaction prediction (binary classification)")
    
    # Labels (for regression)
    latency_labels = s_labels['e2e_latency_ms'].values
    print(f"📊 Regression labels shape: {latency_labels.shape}")
    print(f"   Task: Latency prediction (regression)")
    
    print("\n💡 Next steps:")
    print("   1. Convert to PyTorch tensors")
    print("   2. Build edge_index from edges dataframe")
    print("   3. Create PyG Data objects")
    print("   4. Split into train/val/test sets")
    print("   5. Train your GNN model!")


def main():
    """
    Main example function
    """
    print("\n" + "="*70)
    print(" GNN DATASET LOADING EXAMPLE")
    print("="*70 + "\n")
    
    # Check if dataset exists
    if not os.path.exists("data/dataset/nodes.csv"):
        print("❌ Dataset not found!")
        print("Please generate dataset first:")
        print("  sudo $(which python3) scripts/generate_dataset.py --quick")
        return
    
    # Load dataset
    print("📂 Loading dataset...")
    nodes, edges, labels = load_dataset()
    print("✓ Dataset loaded successfully\n")
    
    # Print statistics
    print_dataset_stats(nodes, edges, labels)
    
    # Build graph for first scenario
    print("\n" + "="*70)
    print(" BUILDING GRAPH FOR SCENARIO 0")
    print("="*70)
    scenario_idx = 0
    G = build_graph_for_scenario(scenario_idx, nodes, edges, labels)
    print(f"\n✓ Built graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"   Scenario: {G.graph['scenario_name']}")
    
    # Visualize (save to file since we're in WSL)
    print("\n🎨 Creating visualization...")
    visualize_scenario(G, scenario_idx, save_path="data/scenario_0_graph.png")
    
    # Show how to prepare for GNN training
    prepare_for_gnn_training(nodes, edges, labels)
    
    print("\n" + "="*70)
    print(" ✓ EXAMPLE COMPLETE")
    print("="*70)
    print("\nYou now know how to:")
    print("  ✓ Load the dataset")
    print("  ✓ Build NetworkX graphs")
    print("  ✓ Extract features and labels")
    print("  ✓ Prepare for GNN training")
    print("\nNext: Implement your GNN model! 🚀\n")


if __name__ == "__main__":
    main()
