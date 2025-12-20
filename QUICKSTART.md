# 🚀 Quick Start Guide

## What Was Just Implemented?

A complete **GNN Dataset Generation System** for your Final Year Project that collects all the parameters you need to train a Graph Neural Network for network optimization.

## 📦 Files Created

```
✅ scripts/topology_config.py          # 16 diverse network scenarios
✅ scripts/data_collector.py           # Comprehensive metrics collection
✅ scripts/traffic_generator.py        # Video streaming simulation
✅ scripts/queue_monitor.py            # Queue monitoring
✅ scripts/generate_dataset.py         # Main orchestrator (CLI tool)
✅ scripts/test_dataset_generation.py  # Quick test script
✅ scripts/quick_start.sh              # Interactive menu script
✅ DATASET_README.md                   # Full documentation
✅ IMPLEMENTATION_SUMMARY.md           # Implementation details
```

## 🎯 What Data Gets Collected?

### Node Features (11 columns)
- Node ID, type (camera/edge/cloud)
- CPU/GPU capacity
- CV model and FPS
- Queue occupancy
- Model complexity (GFLOPs, parameters)

### Edge Features (9 columns)
- Source and destination nodes
- Bandwidth, delay
- Queue size, discipline
- Link type

### Performance Labels (9 columns)
- End-to-end latency
- Throughput
- Packet loss
- GPU utilization
- **QoS satisfied (target label for GNN)**

## ⚡ Fastest Way to Get Started

### Option 1: Interactive Menu (Recommended)
```bash
cd ~/Final-Year-Project
sudo bash scripts/quick_start.sh
```

This gives you a menu to:
1. Run quick test
2. Generate quick dataset (3 scenarios)
3. Generate full dataset (16 scenarios)
4. Validate dataset

### Option 2: Direct Commands

**Test the system** (~1 minute):
```bash
sudo $(which python3) scripts/test_dataset_generation.py
```

**Quick dataset** (3 scenarios, ~5 minutes):
```bash
sudo $(which python3) scripts/generate_dataset.py --quick
```

**Full dataset** (16 scenarios, ~20 minutes):
```bash
sudo $(which python3) scripts/generate_dataset.py
```

## 📊 Expected Output

After running, you'll get:

```
data/dataset/
├── nodes.csv              # ~288 rows (16 scenarios × ~18 nodes)
├── edges.csv              # ~320 rows (16 scenarios × ~20 edges)
├── labels.csv             # ~272 rows (16 scenarios × ~17 paths)
└── generation_stats.json  # Metadata
```

## 🔍 Verify It Worked

```bash
# Check if files were created
ls -lh data/dataset/

# Preview the data
head data/dataset/nodes.csv
head data/dataset/edges.csv
head data/dataset/labels.csv

# Validate dataset
sudo $(which python3) scripts/generate_dataset.py --validate
```

## 💡 Using the Dataset

### Load in Python
```python
import pandas as pd

nodes = pd.read_csv('data/dataset/nodes.csv')
edges = pd.read_csv('data/dataset/edges.csv')
labels = pd.read_csv('data/dataset/labels.csv')

print(f"Nodes: {len(nodes)} samples")
print(f"Edges: {len(edges)} samples")
print(f"Labels: {len(labels)} samples")
```

### Build Graph for GNN
```python
import networkx as nx

# Get data for one scenario
scenario = 0
s_nodes = nodes[nodes['scenario_idx'] == scenario]
s_edges = edges[edges['scenario_idx'] == scenario]

# Create graph
G = nx.DiGraph()

# Add nodes with features
for _, row in s_nodes.iterrows():
    G.add_node(row['node_id'],
               node_type=row['node_type'],
               cpu=row['cpu_capacity'],
               gpu=row['gpu_capacity'],
               fps=row['fps'])

# Add edges with features
for _, row in s_edges.iterrows():
    G.add_edge(row['src'], row['dst'],
               bw=row['bandwidth_mbps'],
               delay=row['delay_ms'])

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
```

### Convert to PyTorch Geometric
```python
from torch_geometric.data import Data
from torch_geometric.utils import from_networkx
import torch

# Option 1: From NetworkX
data = from_networkx(G)

# Option 2: Manual construction
node_features = torch.tensor(s_nodes[['cpu_capacity', 'gpu_capacity', 'fps']].values, dtype=torch.float)
edge_index = ... # Build from edges dataframe
edge_features = torch.tensor(s_edges[['bandwidth_mbps', 'delay_ms']].values, dtype=torch.float)

data = Data(x=node_features, edge_index=edge_index, edge_attr=edge_features)
```

## 🎓 Train Your GNN

Now you have everything needed to train a GNN that can:
- **Predict QoS satisfaction** (classification)
- **Predict latency** (regression)
- **Predict throughput** (regression)
- **Optimize resource allocation** (optimization)

Example GNN architectures to try:
- Graph Convolutional Network (GCN)
- Graph Attention Network (GAT)
- GraphSAGE
- Graph Isomorphism Network (GIN)

## 🛠️ Customization

### Add More Scenarios
Edit `scripts/topology_config.py` and append to `SCENARIOS` list.

### Change Collection Duration
```bash
sudo $(which python3) scripts/generate_dataset.py --duration 60
```

### Collect More Metrics
Edit `scripts/data_collector.py` and add new columns/calculations.

## 📚 Documentation

- **Full documentation**: [DATASET_README.md](DATASET_README.md)
- **Implementation details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Code comments**: Well-documented in all files

## 🆘 Troubleshooting

### "RTNETLINK answers: File exists"
```bash
sudo mn -c
```

### "Cannot find required executable controller"
```bash
sudo apt install openvswitch-testcontroller
sudo ovs-testcontroller ptcp:6653 &
```

### Import errors
```bash
sudo pip3 install networkx matplotlib pandas
```

## ✨ Summary

You now have:
- ✅ 16 diverse network scenarios
- ✅ Automated data collection for node/edge/performance features
- ✅ Complete GNN training dataset
- ✅ Interactive CLI tools
- ✅ Comprehensive documentation
- ✅ Test and validation scripts

**Ready to train your GNN and complete your Final Year Project!** 🎉

---

Need help? Check:
1. [DATASET_README.md](DATASET_README.md) - Complete usage guide
2. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details
3. Code comments in each file
