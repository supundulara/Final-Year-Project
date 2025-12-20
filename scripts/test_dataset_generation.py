#!/usr/bin/env python3
# scripts/test_dataset_generation.py

"""
Quick test script to verify dataset generation system
Runs a single scenario to test all components
"""

import sys
import os
from mininet.clean import cleanup
from mininet.log import setLogLevel

from topology_config import SCENARIOS
from topology import create_topology_from_config
from data_collector import collect_all_metrics

def test_single_scenario():
    """
    Test dataset generation with a single small scenario
    """
    
    print("="*70)
    print(" TESTING DATASET GENERATION SYSTEM")
    print("="*70)
    
    # Use the smallest scenario for testing
    test_scenario = {
        "name": "test_scenario",
        "num_cameras": 3,
        "workload": {"model": "yolov5s", "fps": 10},
        "bandwidth": {"cam_edge": 20, "edge_cloud": 50},
        "delay": {"cam_edge": "2ms", "edge_cloud": "10ms"},
        "queue_size": {"cam_edge": 200, "edge_cloud": 1000}
    }
    
    print(f"\n📋 Test Scenario:")
    print(f"  - Cameras: {test_scenario['num_cameras']}")
    print(f"  - Model: {test_scenario['workload']['model']}")
    print(f"  - FPS: {test_scenario['workload']['fps']}")
    
    output_dir = "data/test_dataset"
    
    try:
        # Clean up
        print(f"\n🧹 Cleaning up Mininet...")
        cleanup()
        
        # Set log level
        setLogLevel('info')
        
        # Create topology
        print(f"\n🌐 Creating topology...")
        net, cameras, edge, cloud = create_topology_from_config(test_scenario)
        net.start()
        print(f"✓ Topology created with {len(cameras)} cameras")
        
        # Collect metrics
        print(f"\n📊 Collecting metrics...")
        collect_all_metrics(net, cameras, edge, cloud, test_scenario, 0, output_dir)
        print(f"✓ Metrics collected")
        
        # Stop network
        print(f"\n🛑 Stopping network...")
        net.stop()
        print(f"✓ Network stopped")
        
        # Verify files
        print(f"\n✅ Verifying output files...")
        for filename in ['nodes.csv', 'edges.csv', 'labels.csv']:
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                with open(filepath, 'r') as f:
                    lines = len(f.readlines())
                print(f"  ✓ {filename}: {lines} rows, {size} bytes")
            else:
                print(f"  ✗ Missing: {filename}")
                return False
        
        print(f"\n{'='*70}")
        print(" ✓ TEST PASSED - System is working correctly!")
        print(f"{'='*70}\n")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        print(f"\n{'='*70}\n")
        
        # Cleanup on failure
        try:
            if 'net' in locals():
                net.stop()
            cleanup()
        except:
            pass
        
        return False


if __name__ == "__main__":
    success = test_single_scenario()
    sys.exit(0 if success else 1)
