# scripts/data_collector.py

"""
Comprehensive data collection for GNN training dataset
Collects node features, edge features, and performance labels
"""

import csv
import os
import re
import time
from topology_config import MODEL_COMPLEXITY, HARDWARE_SPECS, QOS_THRESHOLDS


def collect_all_metrics(net, cameras, edge, cloud, scenario_config, scenario_idx, output_dir="data/dataset"):
    """
    Collects comprehensive metrics for GNN training
    
    Args:
        net: Mininet network object
        cameras: List of camera host objects
        edge: Edge server host object
        cloud: Cloud server host object
        scenario_config: Configuration dict for this scenario
        scenario_idx: Scenario index number
        output_dir: Directory to save collected data
    """
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"  → Collecting node features...")
    collect_node_features(cameras, edge, cloud, scenario_config, scenario_idx, output_dir)
    
    print(f"  → Collecting edge/link features...")
    collect_link_features(net, scenario_config, scenario_idx, output_dir)
    
    print(f"  → Collecting performance labels...")
    collect_performance_labels(net, cameras, edge, cloud, scenario_config, scenario_idx, output_dir)


def collect_node_features(cameras, edge, cloud, config, scenario_idx, output_dir):
    """
    Save node features to nodes.csv
    
    Node features:
    - Node ID, node type
    - CPU/GPU capacity
    - Assigned CV workload (model, FPS)
    - Average queue occupancy (simulated for now)
    """
    
    mode = 'a' if os.path.exists(f"{output_dir}/nodes.csv") else 'w'
    
    with open(f"{output_dir}/nodes.csv", mode, newline="") as f:
        writer = csv.writer(f)
        
        # Write header only on first write
        if mode == 'w':
            writer.writerow([
                "scenario_idx", "scenario_name", "node_id", "node_type",
                "cpu_capacity", "gpu_capacity", "cv_model", "fps",
                "queue_occupancy_avg", "model_gflops", "model_params"
            ])
        
        # Camera nodes
        for i, cam in enumerate(cameras):
            model_info = MODEL_COMPLEXITY.get(config["workload"]["model"], {"gflops": 0, "params": 0})
            queue_occ = simulate_queue_occupancy("camera", config, i)
            
            writer.writerow([
                scenario_idx,
                config["name"],
                cam.name,
                "camera",
                HARDWARE_SPECS["camera"]["cpu"],
                HARDWARE_SPECS["camera"]["gpu"],
                config["workload"]["model"],
                config["workload"]["fps"],
                queue_occ,
                model_info["gflops"],
                model_info["params"]
            ])
        
        # Edge node
        model_info = MODEL_COMPLEXITY.get(config["workload"]["model"], {"gflops": 0, "params": 0})
        queue_occ = simulate_queue_occupancy("edge", config, 0)
        
        writer.writerow([
            scenario_idx,
            config["name"],
            edge.name,
            "edge",
            HARDWARE_SPECS["edge"]["cpu"],
            HARDWARE_SPECS["edge"]["gpu"],
            config["workload"]["model"],
            config["workload"]["fps"],
            queue_occ,
            model_info["gflops"],
            model_info["params"]
        ])
        
        # Cloud node
        writer.writerow([
            scenario_idx,
            config["name"],
            cloud.name,
            "cloud",
            HARDWARE_SPECS["cloud"]["cpu"],
            HARDWARE_SPECS["cloud"]["gpu"],
            "none",
            0,
            0,
            0,
            0
        ])


def collect_link_features(net, config, scenario_idx, output_dir):
    """
    Save link features to edges.csv
    
    Link features:
    - Bandwidth and delay
    - Queue size and discipline
    - Source and destination IDs
    """
    
    mode = 'a' if os.path.exists(f"{output_dir}/edges.csv") else 'w'
    
    with open(f"{output_dir}/edges.csv", mode, newline="") as f:
        writer = csv.writer(f)
        
        # Write header only on first write
        if mode == 'w':
            writer.writerow([
                "scenario_idx", "scenario_name", "src", "dst",
                "bandwidth_mbps", "delay_ms", "queue_size",
                "queue_discipline", "link_type"
            ])
        
        # Extract link info from Mininet topology
        for link in net.links:
            intf1, intf2 = link.intf1, link.intf2
            node1, node2 = intf1.node.name, intf2.node.name
            
            # Determine link type
            if "cam" in node1 or "cam" in node2:
                link_type = "camera_edge"
            elif "edge" in node1 and "s" in node2:
                link_type = "edge_switch"
            elif "s" in node1 and "s" in node2:
                link_type = "switch_switch"
            else:
                link_type = "edge_cloud"
            
            bw = intf1.params.get('bw', 0)
            delay_str = intf1.params.get('delay', '0ms')
            delay = parse_delay(delay_str)
            queue_size = intf1.params.get('max_queue_size', 0)
            
            writer.writerow([
                scenario_idx,
                config["name"],
                node1,
                node2,
                bw,
                delay,
                queue_size,
                "fifo",
                link_type
            ])


def collect_performance_labels(net, cameras, edge, cloud, config, scenario_idx, output_dir):
    """
    Save performance labels to labels.csv
    
    Performance metrics:
    - End-to-end latency
    - Throughput
    - Packet loss
    - GPU utilization
    - QoS satisfied (yes/no)
    """
    
    mode = 'a' if os.path.exists(f"{output_dir}/labels.csv") else 'w'
    
    with open(f"{output_dir}/labels.csv", mode, newline="") as f:
        writer = csv.writer(f)
        
        # Write header only on first write
        if mode == 'w':
            writer.writerow([
                "scenario_idx", "scenario_name", "src_node", "dst_node",
                "e2e_latency_ms", "throughput_mbps", "packet_loss_pct",
                "gpu_utilization_pct", "qos_satisfied"
            ])
        
        # Measure latencies from cameras to edge
        print(f"    → Measuring camera→edge latencies...")
        for cam in cameras:
            result = net.pingFull([cam, edge])
            
            if result and len(result) > 0 and len(result[0]) > 2:
                latency = result[0][2][3]  # rttavg
                packet_loss = 0 if result[0][2][0] == result[0][2][1] else \
                             ((result[0][2][0] - result[0][2][1]) / result[0][2][0] * 100)
            else:
                latency = 0.0
                packet_loss = 100.0
            
            # Estimate throughput based on config
            throughput = estimate_throughput(config, "camera_edge")
            
            # Calculate GPU utilization
            gpu_util = calculate_gpu_utilization(config, len(cameras))
            
            # Determine QoS satisfaction
            qos = determine_qos_satisfaction(latency, throughput, packet_loss)
            
            writer.writerow([
                scenario_idx,
                config["name"],
                cam.name,
                edge.name,
                latency,
                throughput,
                packet_loss,
                gpu_util,
                qos
            ])
        
        # Measure latency from edge to cloud
        print(f"    → Measuring edge→cloud latency...")
        result = net.pingFull([edge, cloud])
        
        if result and len(result) > 0 and len(result[0]) > 2:
            latency = result[0][2][3]
            packet_loss = 0 if result[0][2][0] == result[0][2][1] else \
                         ((result[0][2][0] - result[0][2][1]) / result[0][2][0] * 100)
        else:
            latency = 0.0
            packet_loss = 100.0
        
        throughput = estimate_throughput(config, "edge_cloud")
        gpu_util = 0  # Cloud doesn't process, just stores
        qos = determine_qos_satisfaction(latency, throughput, packet_loss)
        
        writer.writerow([
            scenario_idx,
            config["name"],
            edge.name,
            cloud.name,
            latency,
            throughput,
            packet_loss,
            gpu_util,
            qos
        ])


# ===== Utility Functions =====

def parse_delay(delay_str):
    """Parse delay string like '5ms' to float"""
    match = re.search(r'([\d.]+)', delay_str)
    return float(match.group(1)) if match else 0.0


def simulate_queue_occupancy(node_type, config, node_idx):
    """
    Simulate average queue occupancy based on load
    Higher load = higher queue occupancy
    """
    if node_type == "camera":
        # Cameras have lighter queues
        base_occupancy = 10 + (node_idx * 2)  # Vary by camera
        load_factor = config["num_cameras"] / 15.0  # Normalized by median
        return min(base_occupancy * load_factor, config["queue_size"]["cam_edge"] * 0.7)
    
    elif node_type == "edge":
        # Edge has heavier queues due to aggregation
        base_occupancy = 50
        load_factor = (config["num_cameras"] * config["workload"]["fps"]) / 300.0
        return min(base_occupancy * load_factor, config["queue_size"]["cam_edge"] * 0.8)
    
    return 0


def estimate_throughput(config, link_type):
    """
    Estimate throughput based on video bitrate
    Typical video bitrate: 2-5 Mbps for HD surveillance
    """
    if link_type == "camera_edge":
        # Individual camera stream
        fps = config["workload"]["fps"]
        # Higher FPS = higher bitrate
        bitrate = 1.5 + (fps / 30.0) * 2.5  # 1.5 - 4 Mbps range
        return round(bitrate, 2)
    
    elif link_type == "edge_cloud":
        # Aggregated streams
        num_streams = config["num_cameras"]
        per_stream = 1.5 + (config["workload"]["fps"] / 30.0) * 2.5
        return round(num_streams * per_stream * 0.7, 2)  # Some compression
    
    return 0.0


def calculate_gpu_utilization(config, num_cameras):
    """
    Calculate GPU utilization percentage based on workload
    
    GPU utilization = (Total GFLOPs required) / (Available GPU capacity)
    """
    model = config["workload"]["model"]
    fps = config["workload"]["fps"]
    
    if model not in MODEL_COMPLEXITY:
        return 0.0
    
    # GFLOPs per frame
    gflops_per_frame = MODEL_COMPLEXITY[model]["gflops"]
    
    # Total GFLOPs per second
    total_gflops = gflops_per_frame * fps * num_cameras
    
    # Assume edge GPU can handle ~500 GFLOPs/s (simplified)
    edge_capacity = 500
    
    utilization = (total_gflops / edge_capacity) * 100
    
    return round(min(utilization, 100), 2)


def determine_qos_satisfaction(latency, throughput, packet_loss):
    """
    Determine if QoS is satisfied based on thresholds
    Returns 1 if satisfied, 0 if not
    """
    latency_ok = latency <= QOS_THRESHOLDS["max_latency_ms"]
    throughput_ok = throughput >= QOS_THRESHOLDS["min_throughput_mbps"]
    packet_loss_ok = packet_loss <= QOS_THRESHOLDS["max_packet_loss_pct"]
    
    return 1 if (latency_ok and throughput_ok and packet_loss_ok) else 0
