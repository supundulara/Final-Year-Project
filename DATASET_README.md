# GNN Dataset Generation System

This system generates comprehensive network datasets for training Graph Neural Networks (GNNs) to predict and optimize network performance in edge computing scenarios.

## 🎯 Overview

The dataset captures:
- **Node-level features**: Hardware specs, workloads, queue occupancy
- **Edge-level features**: Bandwidth, delay, queue configuration
- **Performance labels**: Latency, throughput, packet loss, GPU utilization, QoS satisfaction

## 📁 Project Structure

```
scripts/
├── topology_config.py      # 16 diverse network scenarios
├── topology.py             # Network topology creation (original + config-based)
├── data_collector.py       # Comprehensive metrics collection
├── traffic_generator.py    # Video streaming traffic simulation
├── queue_monitor.py        # Queue occupancy monitoring
├── generate_dataset.py     # Main orchestrator script
├── graph_builder.py        # NetworkX graph construction
├── metrics.py              # Basic ping/latency metrics
└── run_experiments.py      # Simple experiment runner

data/
└── dataset/
    ├── nodes.csv           # Node features for all scenarios
    ├── edges.csv           # Edge/link features for all scenarios
    ├── labels.csv          # Performance labels for all scenarios
    └── generation_stats.json  # Generation statistics and metadata
```

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have:
- Mininet installed (`sudo apt install mininet`)
- OpenFlow controller running (`sudo ovs-testcontroller ptcp:6653 &`)
- Python packages: `networkx`, `matplotlib`, `pandas`

### 2. Quick Test (3 scenarios)

```bash
# Run in WSL terminal
cd ~/Final-Year-Project
sudo $(which python3) scripts/generate_dataset.py --quick
```

This runs only 3 scenarios for testing (~3 minutes).

### 3. Full Dataset Generation

```bash
# Generate full dataset (16 scenarios, ~20 minutes)
sudo $(which python3) scripts/generate_dataset.py
```

### 4. Custom Options

```bash
# Run specific number of scenarios
sudo $(which python3) scripts/generate_dataset.py --scenarios 5

# Change traffic duration
sudo $(which python3) scripts/generate_dataset.py --duration 60

# Custom output directory
sudo $(which python3) scripts/generate_dataset.py --output data/my_dataset

# Validate existing dataset
sudo $(which python3) scripts/generate_dataset.py --validate
```

## 📊 Dataset Schema

### nodes.csv

| Column | Description | Type |
|--------|-------------|------|
| scenario_idx | Scenario index (0-15) | int |
| scenario_name | Scenario name | string |
| node_id | Node identifier (cam1, edge, cloud) | string |
| node_type | camera / edge / cloud | string |
| cpu_capacity | CPU capacity (normalized) | float |
| gpu_capacity | GPU capacity (normalized) | float |
| cv_model | Computer vision model name | string |
| fps | Frames per second | int |
| queue_occupancy_avg | Average queue occupancy | float |
| model_gflops | Model complexity (GFLOPs) | float |
| model_params | Model parameters count | int |

### edges.csv

| Column | Description | Type |
|--------|-------------|------|
| scenario_idx | Scenario index | int |
| scenario_name | Scenario name | string |
| src | Source node ID | string |
| dst | Destination node ID | string |
| bandwidth_mbps | Link bandwidth (Mbps) | float |
| delay_ms | Link delay (ms) | float |
| queue_size | Max queue size (packets) | int |
| queue_discipline | Queue discipline (fifo) | string |
| link_type | camera_edge / edge_cloud / etc | string |

### labels.csv

| Column | Description | Type |
|--------|-------------|------|
| scenario_idx | Scenario index | int |
| scenario_name | Scenario name | string |
| src_node | Source node ID | string |
| dst_node | Destination node ID | string |
| e2e_latency_ms | End-to-end latency (ms) | float |
| throughput_mbps | Throughput (Mbps) | float |
| packet_loss_pct | Packet loss percentage | float |
| gpu_utilization_pct | GPU utilization | float |
| qos_satisfied | QoS satisfied (0/1) | int |

## 🔧 Configuration

### Scenarios

Edit `scripts/topology_config.py` to add/modify scenarios:

```python
{
    "name": "my_scenario",
    "num_cameras": 15,
    "workload": {"model": "yolov5m", "fps": 20},
    "bandwidth": {"cam_edge": 10, "edge_cloud": 50},
    "delay": {"cam_edge": "5ms", "edge_cloud": "25ms"},
    "queue_size": {"cam_edge": 200, "edge_cloud": 1000}
}
```

### QoS Thresholds

Edit thresholds in `topology_config.py`:

```python
QOS_THRESHOLDS = {
    "max_latency_ms": 100,
    "min_throughput_mbps": 2,
    "max_packet_loss_pct": 5
}
```

## 📈 Scenarios Included

1. **Low Load** (2 scenarios): Few cameras, high bandwidth
2. **Medium Load** (2 scenarios): Balanced configurations
3. **High Load** (2 scenarios): Many cameras, constrained bandwidth
4. **Edge Cases** (4 scenarios): Asymmetric, high latency, mixed workloads
5. **Balanced** (2 scenarios): Optimal and suboptimal configs
6. **Variable** (2 scenarios): Different camera counts
7. **Model Variants** (2 scenarios): Different CV model complexities

Each scenario varies:
- Number of cameras: 3-30
- Bandwidth: 3-25 Mbps (cam→edge), 20-100 Mbps (edge→cloud)
- Latency: 2-20ms (cam→edge), 10-100ms (edge→cloud)
- CV models: YOLOv5n/s/m, YOLOv8m/x
- FPS: 10-30

## 🔍 Data Validation

```bash
# Validate dataset integrity
sudo $(which python3) scripts/generate_dataset.py --validate
```

Checks:
- ✓ File existence
- ✓ Row counts
- ✓ Column completeness
- ✓ Node/edge type distribution
- ✓ QoS satisfaction rate

## 🐛 Troubleshooting

### Problem: "RTNETLINK answers: File exists"

**Solution**: Clean up Mininet state
```bash
sudo mn -c
```

### Problem: "Cannot find required executable controller"

**Solution**: Start OpenFlow controller
```bash
sudo ovs-testcontroller ptcp:6653 &
```

### Problem: Import errors

**Solution**: Install system-wide packages
```bash
sudo pip3 install networkx matplotlib pandas
```

### Problem: Permission denied

**Solution**: Run with sudo
```bash
sudo $(which python3) scripts/generate_dataset.py
```

## 📊 Expected Output

After successful generation:

```
📁 Generated files:
  - nodes.csv: ~150 KB (16 scenarios × ~18 nodes each)
  - edges.csv: ~80 KB (16 scenarios × ~20 links each)  
  - labels.csv: ~180 KB (16 scenarios × ~17 node pairs each)
  - generation_stats.json: ~5 KB (metadata)
```

## 🎓 Using the Dataset

### Load in Python

```python
import pandas as pd

# Load data
nodes = pd.read_csv('data/dataset/nodes.csv')
edges = pd.read_csv('data/dataset/edges.csv')
labels = pd.read_csv('data/dataset/labels.csv')

# Filter by scenario
scenario_0_nodes = nodes[nodes['scenario_idx'] == 0]
```

### Build NetworkX Graph

```python
import networkx as nx

# Create graph for scenario
G = nx.DiGraph()

# Add nodes with features
for _, row in nodes.iterrows():
    G.add_node(row['node_id'], 
               node_type=row['node_type'],
               cpu=row['cpu_capacity'],
               gpu=row['gpu_capacity'])

# Add edges with features
for _, row in edges.iterrows():
    G.add_edge(row['src'], row['dst'],
               bandwidth=row['bandwidth_mbps'],
               delay=row['delay_ms'])
```

### PyTorch Geometric Format

```python
from torch_geometric.data import Data
import torch

# Convert to PyG format
node_features = torch.tensor(nodes[['cpu_capacity', 'gpu_capacity', ...]].values)
edge_index = torch.tensor([[src_indices], [dst_indices]])
edge_features = torch.tensor(edges[['bandwidth_mbps', 'delay_ms', ...]].values)
labels = torch.tensor(labels['qos_satisfied'].values)

data = Data(x=node_features, edge_index=edge_index, 
            edge_attr=edge_features, y=labels)
```

## 📚 Next Steps

1. **Train GNN Model**: Use dataset to train predictive models
2. **Add More Scenarios**: Expand `topology_config.py` with more diverse configs
3. **Enable Traffic Generation**: Uncomment traffic simulation in `generate_dataset.py`
4. **Real Queue Monitoring**: Uncomment queue monitoring for actual measurements
5. **Extend Metrics**: Add more performance indicators (jitter, etc.)

## 🤝 Contributing

To add new scenarios or metrics:
1. Edit `scripts/topology_config.py` for new scenarios
2. Edit `scripts/data_collector.py` for new metrics
3. Update this README with changes

## 📄 License

Part of Final Year Project - Network Optimization with GNNs
