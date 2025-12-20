# scripts/traffic_generator.py

"""
Generate realistic video streaming traffic patterns
Simulates video surveillance streams from cameras to edge/cloud
"""

import time
import re


def generate_video_traffic(net, cameras, edge, cloud, config, duration=30):
    """
    Simulate video streaming traffic from cameras to edge/cloud
    
    Args:
        net: Mininet network object
        cameras: List of camera host objects
        edge: Edge server host object
        cloud: Cloud server host object
        config: Scenario configuration dict
        duration: Traffic generation duration in seconds
    
    Returns:
        dict: Traffic statistics
    """
    
    print(f"  → Starting traffic generation for {duration}s...")
    
    # Calculate video bitrate based on FPS
    fps = config["workload"]["fps"]
    # Typical HD surveillance: 1.5-5 Mbps
    bitrate_mbps = 1.5 + (fps / 30.0) * 2.5
    bitrate_str = f"{bitrate_mbps}M"
    
    # Start iperf servers on edge and cloud
    print(f"    → Starting iperf servers...")
    edge.cmd('killall -9 iperf 2>/dev/null')  # Clean up any existing
    cloud.cmd('killall -9 iperf 2>/dev/null')
    
    edge.cmd('iperf -s -u -p 5001 > /tmp/iperf_edge.log 2>&1 &')
    cloud.cmd('iperf -s -u -p 5002 > /tmp/iperf_cloud.log 2>&1 &')
    
    time.sleep(2)  # Let servers start
    
    # Generate traffic from cameras to edge
    print(f"    → Generating camera→edge traffic ({bitrate_str} per camera)...")
    client_pids = []
    
    for i, cam in enumerate(cameras):
        # Stagger start times slightly to simulate real-world deployment
        if i > 0 and i % 5 == 0:
            time.sleep(0.5)
        
        # UDP traffic to simulate video streaming
        cmd = f'iperf -c {edge.IP()} -u -b {bitrate_str} -t {duration} -p 5001 > /tmp/iperf_{cam.name}.log 2>&1 &'
        result = cam.cmd(cmd)
        client_pids.append(cam.name)
    
    # Also send aggregated traffic from edge to cloud (lower rate due to compression)
    aggregated_bitrate = bitrate_mbps * len(cameras) * 0.5  # 50% compression
    print(f"    → Generating edge→cloud traffic ({aggregated_bitrate:.1f}M aggregated)...")
    edge.cmd(f'iperf -c {cloud.IP()} -u -b {aggregated_bitrate}M -t {duration} -p 5002 > /tmp/iperf_edge_client.log 2>&1 &')
    
    # Wait for traffic to complete
    print(f"    → Waiting for traffic to complete...")
    time.sleep(duration + 5)
    
    # Collect results
    print(f"    → Collecting traffic statistics...")
    stats = collect_traffic_stats(cameras, edge, cloud)
    
    # Cleanup
    cleanup_traffic_processes(net, cameras, edge, cloud)
    
    return stats


def collect_traffic_stats(cameras, edge, cloud):
    """
    Collect traffic statistics from iperf log files
    
    Returns:
        dict: Traffic statistics per node
    """
    stats = {
        "cameras": {},
        "edge_to_cloud": {}
    }
    
    # Collect camera stats
    for cam in cameras:
        log_file = f'/tmp/iperf_{cam.name}.log'
        result = cam.cmd(f'cat {log_file} 2>/dev/null')
        
        if result:
            # Parse iperf output for bandwidth and jitter
            bandwidth = parse_iperf_bandwidth(result)
            jitter = parse_iperf_jitter(result)
            packet_loss = parse_iperf_packet_loss(result)
            
            stats["cameras"][cam.name] = {
                "bandwidth_mbps": bandwidth,
                "jitter_ms": jitter,
                "packet_loss_pct": packet_loss
            }
    
    # Collect edge-to-cloud stats
    result = edge.cmd('cat /tmp/iperf_edge_client.log 2>/dev/null')
    if result:
        stats["edge_to_cloud"] = {
            "bandwidth_mbps": parse_iperf_bandwidth(result),
            "jitter_ms": parse_iperf_jitter(result),
            "packet_loss_pct": parse_iperf_packet_loss(result)
        }
    
    return stats


def cleanup_traffic_processes(net, cameras, edge, cloud):
    """
    Kill all iperf processes and clean up log files
    """
    print(f"    → Cleaning up traffic processes...")
    
    # Kill iperf processes
    for cam in cameras:
        cam.cmd('killall -9 iperf 2>/dev/null')
    
    edge.cmd('killall -9 iperf 2>/dev/null')
    cloud.cmd('killall -9 iperf 2>/dev/null')
    
    # Clean up log files (optional - keep for debugging)
    # for cam in cameras:
    #     cam.cmd(f'rm -f /tmp/iperf_{cam.name}.log')
    # edge.cmd('rm -f /tmp/iperf_edge*.log')
    # cloud.cmd('rm -f /tmp/iperf_cloud.log')


def generate_background_traffic(net, cameras, edge, duration=30):
    """
    Generate lightweight background traffic to simulate network noise
    Uses ping with interval to create continuous low-level traffic
    """
    print(f"    → Generating background traffic...")
    
    for i, cam in enumerate(cameras):
        # Every 5th camera generates background traffic
        if i % 5 == 0:
            # Continuous ping with 0.1s interval
            cam.cmd(f'ping -i 0.1 {edge.IP()} > /dev/null 2>&1 &')
    
    time.sleep(duration)
    
    # Stop background traffic
    for cam in cameras:
        cam.cmd('killall -9 ping 2>/dev/null')


# ===== Parsing Utilities =====

def parse_iperf_bandwidth(output):
    """
    Parse bandwidth from iperf output
    Example: [ ID] Interval       Transfer     Bandwidth
             [  3]  0.0-10.0 sec  12.5 MBytes  10.5 Mbits/sec
    """
    match = re.search(r'([\d.]+)\s+Mbits/sec', output)
    if match:
        return float(match.group(1))
    return 0.0


def parse_iperf_jitter(output):
    """
    Parse jitter from iperf UDP output
    Example: [  3]  0.0-10.0 sec  12.5 MBytes  10.5 Mbits/sec  0.123 ms
    """
    match = re.search(r'([\d.]+)\s+ms\s+\d+/\d+', output)
    if match:
        return float(match.group(1))
    return 0.0


def parse_iperf_packet_loss(output):
    """
    Parse packet loss from iperf UDP output
    Example: [  3]  0.0-10.0 sec  ... (5/100)
    Returns percentage
    """
    match = re.search(r'\((\d+)/(\d+)\)', output)
    if match:
        lost = int(match.group(1))
        total = int(match.group(2))
        return (lost / total * 100) if total > 0 else 0.0
    return 0.0


def estimate_required_bandwidth(config):
    """
    Estimate required bandwidth for scenario
    Useful for validation
    """
    fps = config["workload"]["fps"]
    num_cameras = config["num_cameras"]
    
    # Per-camera bitrate
    per_camera_mbps = 1.5 + (fps / 30.0) * 2.5
    
    # Total required
    total_mbps = per_camera_mbps * num_cameras
    
    return {
        "per_camera_mbps": round(per_camera_mbps, 2),
        "total_mbps": round(total_mbps, 2),
        "available_mbps": config["bandwidth"]["cam_edge"]
    }
