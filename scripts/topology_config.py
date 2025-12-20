# scripts/topology_config.py

"""
Configuration scenarios for generating diverse network topologies
Each scenario represents a different network condition to train the GNN
"""

SCENARIOS = [
    # Low load scenarios
    {
        "name": "low_load_small",
        "num_cameras": 5,
        "workload": {"model": "yolov5s", "fps": 10},
        "bandwidth": {"cam_edge": 20, "edge_cloud": 100},
        "delay": {"cam_edge": "2ms", "edge_cloud": "10ms"},
        "queue_size": {"cam_edge": 200, "edge_cloud": 1000}
    },
    {
        "name": "low_load_medium",
        "num_cameras": 10,
        "workload": {"model": "yolov5s", "fps": 15},
        "bandwidth": {"cam_edge": 15, "edge_cloud": 80},
        "delay": {"cam_edge": "3ms", "edge_cloud": "15ms"},
        "queue_size": {"cam_edge": 250, "edge_cloud": 1200}
    },
    
    # Medium load scenarios
    {
        "name": "medium_load_standard",
        "num_cameras": 15,
        "workload": {"model": "yolov5m", "fps": 20},
        "bandwidth": {"cam_edge": 10, "edge_cloud": 50},
        "delay": {"cam_edge": "5ms", "edge_cloud": "25ms"},
        "queue_size": {"cam_edge": 200, "edge_cloud": 1000}
    },
    {
        "name": "medium_load_constrained",
        "num_cameras": 12,
        "workload": {"model": "yolov5m", "fps": 25},
        "bandwidth": {"cam_edge": 8, "edge_cloud": 40},
        "delay": {"cam_edge": "7ms", "edge_cloud": "30ms"},
        "queue_size": {"cam_edge": 150, "edge_cloud": 800}
    },
    
    # High load scenarios
    {
        "name": "high_load_standard",
        "num_cameras": 20,
        "workload": {"model": "yolov8x", "fps": 30},
        "bandwidth": {"cam_edge": 5, "edge_cloud": 30},
        "delay": {"cam_edge": "10ms", "edge_cloud": "50ms"},
        "queue_size": {"cam_edge": 100, "edge_cloud": 500}
    },
    {
        "name": "high_load_extreme",
        "num_cameras": 25,
        "workload": {"model": "yolov8x", "fps": 30},
        "bandwidth": {"cam_edge": 3, "edge_cloud": 20},
        "delay": {"cam_edge": "15ms", "edge_cloud": "70ms"},
        "queue_size": {"cam_edge": 80, "edge_cloud": 400}
    },
    
    # Edge cases
    {
        "name": "asymmetric_low_bandwidth",
        "num_cameras": 15,
        "workload": {"model": "yolov5m", "fps": 20},
        "bandwidth": {"cam_edge": 5, "edge_cloud": 100},
        "delay": {"cam_edge": "5ms", "edge_cloud": "10ms"},
        "queue_size": {"cam_edge": 100, "edge_cloud": 2000}
    },
    {
        "name": "high_latency_network",
        "num_cameras": 10,
        "workload": {"model": "yolov5s", "fps": 15},
        "bandwidth": {"cam_edge": 20, "edge_cloud": 50},
        "delay": {"cam_edge": "20ms", "edge_cloud": "100ms"},
        "queue_size": {"cam_edge": 300, "edge_cloud": 1500}
    },
    {
        "name": "mixed_workload_light",
        "num_cameras": 8,
        "workload": {"model": "yolov5s", "fps": 10},
        "bandwidth": {"cam_edge": 12, "edge_cloud": 60},
        "delay": {"cam_edge": "4ms", "edge_cloud": "20ms"},
        "queue_size": {"cam_edge": 200, "edge_cloud": 1000}
    },
    {
        "name": "mixed_workload_heavy",
        "num_cameras": 18,
        "workload": {"model": "yolov8m", "fps": 25},
        "bandwidth": {"cam_edge": 7, "edge_cloud": 35},
        "delay": {"cam_edge": "8ms", "edge_cloud": "40ms"},
        "queue_size": {"cam_edge": 120, "edge_cloud": 600}
    },
    
    # Balanced scenarios
    {
        "name": "balanced_optimal",
        "num_cameras": 15,
        "workload": {"model": "yolov5m", "fps": 20},
        "bandwidth": {"cam_edge": 15, "edge_cloud": 75},
        "delay": {"cam_edge": "3ms", "edge_cloud": "15ms"},
        "queue_size": {"cam_edge": 300, "edge_cloud": 1500}
    },
    {
        "name": "balanced_suboptimal",
        "num_cameras": 15,
        "workload": {"model": "yolov5m", "fps": 20},
        "bandwidth": {"cam_edge": 8, "edge_cloud": 40},
        "delay": {"cam_edge": "10ms", "edge_cloud": "50ms"},
        "queue_size": {"cam_edge": 150, "edge_cloud": 750}
    },
    
    # Variable camera counts
    {
        "name": "few_cameras_high_quality",
        "num_cameras": 3,
        "workload": {"model": "yolov8x", "fps": 30},
        "bandwidth": {"cam_edge": 25, "edge_cloud": 100},
        "delay": {"cam_edge": "2ms", "edge_cloud": "10ms"},
        "queue_size": {"cam_edge": 400, "edge_cloud": 2000}
    },
    {
        "name": "many_cameras_low_quality",
        "num_cameras": 30,
        "workload": {"model": "yolov5n", "fps": 10},
        "bandwidth": {"cam_edge": 5, "edge_cloud": 25},
        "delay": {"cam_edge": "15ms", "edge_cloud": "75ms"},
        "queue_size": {"cam_edge": 80, "edge_cloud": 400}
    },
    
    # Different model complexities
    {
        "name": "lightweight_model",
        "num_cameras": 20,
        "workload": {"model": "yolov5n", "fps": 30},
        "bandwidth": {"cam_edge": 10, "edge_cloud": 50},
        "delay": {"cam_edge": "5ms", "edge_cloud": "25ms"},
        "queue_size": {"cam_edge": 200, "edge_cloud": 1000}
    },
    {
        "name": "heavyweight_model",
        "num_cameras": 8,
        "workload": {"model": "yolov8x", "fps": 15},
        "bandwidth": {"cam_edge": 15, "edge_cloud": 75},
        "delay": {"cam_edge": "5ms", "edge_cloud": "25ms"},
        "queue_size": {"cam_edge": 250, "edge_cloud": 1250}
    }
]

# Model complexity parameters for GPU utilization calculation
MODEL_COMPLEXITY = {
    "yolov5n": {"gflops": 4.5, "params": 1.9e6},
    "yolov5s": {"gflops": 16.5, "params": 7.2e6},
    "yolov5m": {"gflops": 49.0, "params": 21.2e6},
    "yolov8m": {"gflops": 78.9, "params": 25.9e6},
    "yolov8x": {"gflops": 257.8, "params": 68.2e6}
}

# Hardware capacity constants
HARDWARE_SPECS = {
    "camera": {"cpu": 0.1, "gpu": 0.0},  # Minimal processing
    "edge": {"cpu": 0.8, "gpu": 1.0},    # 1 GPU (normalized)
    "cloud": {"cpu": 1.0, "gpu": 4.0}    # 4 GPUs (normalized)
}

# QoS thresholds for labeling
QOS_THRESHOLDS = {
    "max_latency_ms": 100,      # Maximum acceptable E2E latency
    "min_throughput_mbps": 2,   # Minimum required throughput per stream
    "max_packet_loss_pct": 5    # Maximum acceptable packet loss
}
