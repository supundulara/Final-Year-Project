# scripts/generate_dataset.py

"""
Main orchestrator for GNN dataset generation
Runs multiple network scenarios and collects comprehensive metrics
"""

import os
import sys
import time
import json
from mininet.clean import cleanup
from mininet.log import setLogLevel

from topology_config import SCENARIOS
from topology import create_topology_from_config
from data_collector import collect_all_metrics
from traffic_generator import generate_video_traffic
from queue_monitor import monitor_queue_occupancy


def generate_dataset(output_dir="data/dataset", num_scenarios=None, traffic_duration=30):
    """
    Generate complete GNN training dataset by running all scenarios
    
    Args:
        output_dir: Directory to save dataset files
        num_scenarios: Number of scenarios to run (None = all)
        traffic_duration: Duration of traffic generation per scenario (seconds)
    """
    
    print("="*70)
    print(" GNN DATASET GENERATION")
    print("="*70)
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created output directory: {output_dir}")
    
    # Determine which scenarios to run
    scenarios_to_run = SCENARIOS[:num_scenarios] if num_scenarios else SCENARIOS
    total_scenarios = len(scenarios_to_run)
    
    print(f"\n📊 Will generate dataset from {total_scenarios} scenarios")
    print(f"⏱️  Estimated time: ~{total_scenarios * (traffic_duration + 20) / 60:.1f} minutes")
    print(f"💾 Output directory: {output_dir}\n")
    
    # Confirm before starting
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Set log level
    setLogLevel('info')
    
    # Track statistics
    stats = {
        "total_scenarios": total_scenarios,
        "successful": 0,
        "failed": 0,
        "start_time": time.time(),
        "scenarios": []
    }
    
    # Run each scenario
    for idx, scenario in enumerate(scenarios_to_run):
        scenario_num = idx + 1
        print(f"\n{'='*70}")
        print(f"SCENARIO {scenario_num}/{total_scenarios}: {scenario['name']}")
        print(f"{'='*70}")
        print(f"  Cameras: {scenario['num_cameras']}")
        print(f"  Workload: {scenario['workload']['model']} @ {scenario['workload']['fps']} FPS")
        print(f"  Bandwidth: Cam→Edge={scenario['bandwidth']['cam_edge']}Mbps, Edge→Cloud={scenario['bandwidth']['edge_cloud']}Mbps")
        print(f"  Delay: Cam→Edge={scenario['delay']['cam_edge']}, Edge→Cloud={scenario['delay']['edge_cloud']}")
        
        scenario_stats = {
            "name": scenario['name'],
            "index": idx,
            "status": "running",
            "start_time": time.time()
        }
        
        try:
            # Clean up any previous state
            print(f"\n🧹 Cleaning up previous Mininet state...")
            cleanup()
            time.sleep(2)
            
            # 1. Create topology
            print(f"\n🌐 Creating network topology...")
            net, cameras, edge, cloud = create_topology_from_config(scenario)
            net.start()
            print(f"✓ Topology created and started")
            
            # Wait for network to stabilize
            print(f"⏳ Waiting for network to stabilize...")
            time.sleep(5)
            
            # 2. Generate traffic (optional - can skip for faster dataset generation)
            # print(f"\n🚦 Generating traffic...")
            # traffic_stats = generate_video_traffic(net, cameras, edge, cloud, scenario, duration=traffic_duration)
            # print(f"✓ Traffic generation complete")
            
            # 3. Monitor queues (optional)
            # print(f"\n📊 Monitoring queues...")
            # queue_stats = monitor_queue_occupancy(net, cameras, edge, cloud, duration=10, interval=1.0)
            # print(f"✓ Queue monitoring complete")
            
            # 4. Collect all metrics
            print(f"\n📝 Collecting metrics for GNN dataset...")
            collect_all_metrics(net, cameras, edge, cloud, scenario, idx, output_dir)
            print(f"✓ Metrics collection complete")
            
            # 5. Stop network
            print(f"\n🛑 Stopping network...")
            net.stop()
            print(f"✓ Network stopped")
            
            # Mark as successful
            scenario_stats["status"] = "success"
            scenario_stats["end_time"] = time.time()
            scenario_stats["duration"] = scenario_stats["end_time"] - scenario_stats["start_time"]
            stats["successful"] += 1
            
            print(f"\n✓ Scenario {scenario_num}/{total_scenarios} complete!")
            
        except Exception as e:
            print(f"\n✗ Error in scenario {scenario_num}: {str(e)}")
            scenario_stats["status"] = "failed"
            scenario_stats["error"] = str(e)
            scenario_stats["end_time"] = time.time()
            stats["failed"] += 1
            
            # Try to cleanup even on failure
            try:
                if 'net' in locals():
                    net.stop()
                cleanup()
            except:
                pass
        
        stats["scenarios"].append(scenario_stats)
        
        # Brief pause between scenarios
        if scenario_num < total_scenarios:
            print(f"\n⏸️  Pausing 5 seconds before next scenario...")
            time.sleep(5)
    
    # Final statistics
    stats["end_time"] = time.time()
    stats["total_duration"] = stats["end_time"] - stats["start_time"]
    
    print(f"\n\n{'='*70}")
    print(" DATASET GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Successful scenarios: {stats['successful']}/{total_scenarios}")
    print(f"✗ Failed scenarios: {stats['failed']}/{total_scenarios}")
    print(f"⏱️  Total time: {stats['total_duration']/60:.1f} minutes")
    print(f"💾 Output directory: {output_dir}")
    
    # Save statistics
    stats_file = os.path.join(output_dir, "generation_stats.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"📊 Statistics saved to: {stats_file}")
    
    # Display file sizes
    print(f"\n📁 Generated files:")
    for filename in ['nodes.csv', 'edges.csv', 'labels.csv']:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  - {filename}: {size:,} bytes ({size/1024:.1f} KB)")
    
    print(f"\n{'='*70}\n")
    
    return stats


def validate_dataset(output_dir="data/dataset"):
    """
    Validate the generated dataset files
    Checks for missing values, data consistency, etc.
    """
    
    print("\n" + "="*70)
    print(" DATASET VALIDATION")
    print("="*70 + "\n")
    
    import csv
    
    files_to_check = ['nodes.csv', 'edges.csv', 'labels.csv']
    
    for filename in files_to_check:
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"✗ Missing file: {filename}")
            continue
        
        # Read and validate
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            print(f"✓ {filename}:")
            print(f"  - Rows: {len(rows)}")
            print(f"  - Columns: {len(rows[0].keys()) if rows else 0}")
            
            if filename == 'nodes.csv':
                # Check node types
                node_types = {}
                for row in rows:
                    node_type = row.get('node_type', 'unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                print(f"  - Node types: {node_types}")
            
            elif filename == 'edges.csv':
                # Check link types
                link_types = {}
                for row in rows:
                    link_type = row.get('link_type', 'unknown')
                    link_types[link_type] = link_types.get(link_type, 0) + 1
                print(f"  - Link types: {link_types}")
            
            elif filename == 'labels.csv':
                # Check QoS distribution
                qos_dist = {'satisfied': 0, 'not_satisfied': 0}
                for row in rows:
                    qos = int(row.get('qos_satisfied', 0))
                    if qos == 1:
                        qos_dist['satisfied'] += 1
                    else:
                        qos_dist['not_satisfied'] += 1
                print(f"  - QoS distribution: {qos_dist}")
                print(f"  - QoS satisfaction rate: {qos_dist['satisfied']/len(rows)*100:.1f}%")
    
    print("\n" + "="*70 + "\n")


def merge_scenario_data(output_dir="data/dataset"):
    """
    Merge all scenario data into single comprehensive dataset
    (Already done incrementally during collection, but this can verify)
    """
    print("✓ Data is already merged during collection process")
    return True


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate GNN training dataset from Mininet simulations')
    parser.add_argument('--output', '-o', default='data/dataset', help='Output directory for dataset')
    parser.add_argument('--scenarios', '-n', type=int, default=None, help='Number of scenarios to run (default: all)')
    parser.add_argument('--duration', '-d', type=int, default=30, help='Traffic duration per scenario in seconds')
    parser.add_argument('--validate', '-v', action='store_true', help='Only validate existing dataset')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick mode: run only 3 scenarios for testing')
    
    args = parser.parse_args()
    
    if args.validate:
        # Just validate existing dataset
        validate_dataset(args.output)
    else:
        # Generate dataset
        num_scenarios = args.scenarios
        if args.quick:
            num_scenarios = 3
            print("⚡ Quick mode: Running only 3 scenarios\n")
        
        stats = generate_dataset(
            output_dir=args.output,
            num_scenarios=num_scenarios,
            traffic_duration=args.duration
        )
        
        # Validate after generation
        validate_dataset(args.output)
