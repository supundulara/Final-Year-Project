# scripts/queue_monitor.py

"""
Monitor queue occupancy and network interface statistics
Provides real-time monitoring of queue depths across the network
"""

import time
import re
from collections import defaultdict


def monitor_queue_occupancy(net, cameras, edge, cloud, duration=30, interval=1.0):
    """
    Monitor queue lengths on all network interfaces
    
    Args:
        net: Mininet network object
        cameras: List of camera hosts
        edge: Edge server host
        cloud: Cloud server host
        duration: Monitoring duration in seconds
        interval: Sampling interval in seconds
    
    Returns:
        dict: Average queue occupancy per node
    """
    
    print(f"  → Monitoring queue occupancy for {duration}s...")
    
    queue_data = defaultdict(list)
    iterations = int(duration / interval)
    
    for i in range(iterations):
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"    → Progress: {i+1}/{iterations} samples")
        
        # Monitor camera interfaces
        for cam in cameras:
            queue_len = get_interface_queue_length(cam, f'{cam.name}-eth0')
            queue_data[cam.name].append(queue_len)
        
        # Monitor edge interface
        queue_len = get_interface_queue_length(edge, f'{edge.name}-eth0')
        queue_data[edge.name].append(queue_len)
        
        # Monitor cloud interface
        queue_len = get_interface_queue_length(cloud, f'{cloud.name}-eth0')
        queue_data[cloud.name].append(queue_len)
        
        # Monitor switch interfaces
        for switch in net.switches:
            for intf in switch.intfList():
                if intf.name != 'lo':
                    queue_len = get_interface_queue_length(switch, intf.name)
                    queue_data[f'{switch.name}_{intf.name}'].append(queue_len)
        
        time.sleep(interval)
    
    # Calculate average queue occupancy
    avg_queue = {}
    for node, values in queue_data.items():
        if values:
            avg_queue[node] = sum(values) / len(values)
        else:
            avg_queue[node] = 0.0
    
    print(f"  → Queue monitoring complete")
    return avg_queue


def get_interface_queue_length(node, interface):
    """
    Get current queue length for a specific interface
    Uses 'tc -s qdisc show' to query queue statistics
    
    Args:
        node: Mininet node object
        interface: Interface name (e.g., 'cam1-eth0')
    
    Returns:
        int: Current queue length (packets)
    """
    try:
        # Query traffic control statistics
        result = node.cmd(f'tc -s qdisc show dev {interface} 2>/dev/null')
        
        if not result:
            return 0
        
        # Parse output for backlog
        # Example: "backlog 0b 0p requeues 0"
        match = re.search(r'backlog\s+\d+b\s+(\d+)p', result)
        if match:
            return int(match.group(1))
        
        return 0
    except Exception as e:
        return 0


def get_interface_statistics(node, interface):
    """
    Get detailed interface statistics
    
    Returns:
        dict: Interface stats (bytes, packets, drops, etc.)
    """
    try:
        # Get interface statistics using ip command
        result = node.cmd(f'ip -s link show {interface} 2>/dev/null')
        
        stats = {
            'tx_bytes': 0,
            'tx_packets': 0,
            'tx_dropped': 0,
            'rx_bytes': 0,
            'rx_packets': 0,
            'rx_dropped': 0
        }
        
        if not result:
            return stats
        
        # Parse TX stats
        tx_match = re.search(r'TX:.*?bytes\s+(\d+)\s+packets\s+(\d+).*?dropped\s+(\d+)', result, re.DOTALL)
        if tx_match:
            stats['tx_bytes'] = int(tx_match.group(1))
            stats['tx_packets'] = int(tx_match.group(2))
            stats['tx_dropped'] = int(tx_match.group(3))
        
        # Parse RX stats
        rx_match = re.search(r'RX:.*?bytes\s+(\d+)\s+packets\s+(\d+).*?dropped\s+(\d+)', result, re.DOTALL)
        if rx_match:
            stats['rx_bytes'] = int(rx_match.group(1))
            stats['rx_packets'] = int(rx_match.group(2))
            stats['rx_dropped'] = int(rx_match.group(3))
        
        return stats
        
    except Exception as e:
        return stats


def monitor_bandwidth_utilization(net, cameras, edge, cloud, duration=30, interval=2.0):
    """
    Monitor bandwidth utilization over time
    Samples interface statistics at intervals to calculate utilization
    
    Returns:
        dict: Average bandwidth utilization per interface
    """
    
    print(f"  → Monitoring bandwidth utilization for {duration}s...")
    
    utilization_data = defaultdict(list)
    iterations = int(duration / interval)
    
    # Take initial measurement
    prev_stats = {}
    for cam in cameras:
        prev_stats[cam.name] = get_interface_statistics(cam, f'{cam.name}-eth0')
    prev_stats[edge.name] = get_interface_statistics(edge, f'{edge.name}-eth0')
    prev_stats[cloud.name] = get_interface_statistics(cloud, f'{cloud.name}-eth0')
    
    time.sleep(interval)
    
    for i in range(iterations):
        # Get current measurements
        for cam in cameras:
            curr_stats = get_interface_statistics(cam, f'{cam.name}-eth0')
            if cam.name in prev_stats:
                # Calculate bytes per second
                tx_bps = (curr_stats['tx_bytes'] - prev_stats[cam.name]['tx_bytes']) / interval
                rx_bps = (curr_stats['rx_bytes'] - prev_stats[cam.name]['rx_bytes']) / interval
                
                # Convert to Mbps
                tx_mbps = (tx_bps * 8) / 1_000_000
                rx_mbps = (rx_bps * 8) / 1_000_000
                
                utilization_data[f'{cam.name}_tx'].append(tx_mbps)
                utilization_data[f'{cam.name}_rx'].append(rx_mbps)
                
                prev_stats[cam.name] = curr_stats
        
        # Similar for edge and cloud
        curr_stats = get_interface_statistics(edge, f'{edge.name}-eth0')
        if edge.name in prev_stats:
            tx_bps = (curr_stats['tx_bytes'] - prev_stats[edge.name]['tx_bytes']) / interval
            rx_bps = (curr_stats['rx_bytes'] - prev_stats[edge.name]['rx_bytes']) / interval
            utilization_data[f'{edge.name}_tx'].append((tx_bps * 8) / 1_000_000)
            utilization_data[f'{edge.name}_rx'].append((rx_bps * 8) / 1_000_000)
            prev_stats[edge.name] = curr_stats
        
        time.sleep(interval)
    
    # Calculate averages
    avg_utilization = {}
    for intf, values in utilization_data.items():
        if values:
            avg_utilization[intf] = sum(values) / len(values)
        else:
            avg_utilization[intf] = 0.0
    
    return avg_utilization


def get_switch_flow_stats(net):
    """
    Get OpenFlow statistics from switches
    Useful for understanding routing behavior
    
    Returns:
        dict: Flow statistics per switch
    """
    
    flow_stats = {}
    
    for switch in net.switches:
        # Query flow table
        result = switch.cmd('ovs-ofctl dump-flows ' + switch.name + ' 2>/dev/null')
        
        flows = []
        if result:
            # Parse flow entries
            for line in result.split('\n'):
                if 'actions' in line:
                    # Extract relevant flow info
                    match = re.search(r'n_packets=(\d+).*?n_bytes=(\d+)', line)
                    if match:
                        flows.append({
                            'packets': int(match.group(1)),
                            'bytes': int(match.group(2))
                        })
        
        flow_stats[switch.name] = {
            'num_flows': len(flows),
            'total_packets': sum(f['packets'] for f in flows),
            'total_bytes': sum(f['bytes'] for f in flows)
        }
    
    return flow_stats


def print_queue_summary(queue_data):
    """
    Print a summary of queue occupancy data
    """
    print("\n  === Queue Occupancy Summary ===")
    
    # Group by node type
    cameras = {k: v for k, v in queue_data.items() if 'cam' in k and '_' not in k}
    edge = {k: v for k, v in queue_data.items() if 'edge' == k}
    switches = {k: v for k, v in queue_data.items() if 's' in k and '_' in k}
    
    if cameras:
        avg_cam_queue = sum(cameras.values()) / len(cameras)
        print(f"  Cameras (avg): {avg_cam_queue:.2f} packets")
    
    if edge:
        print(f"  Edge: {list(edge.values())[0]:.2f} packets")
    
    if switches:
        avg_switch_queue = sum(switches.values()) / len(switches)
        print(f"  Switches (avg): {avg_switch_queue:.2f} packets")
    
    print("  " + "="*31)
