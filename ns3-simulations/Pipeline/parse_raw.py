import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path

RAW_DIR = Path("outputs/airport2_scenarios")
OUT_DIR = Path("dataset2")  

def parse_ns3_val(val, type_func, default=0):
    """Helper to strip 'ns' suffix and convert type safely."""
    if val is None:
        return default
    if val.endswith('ns'):
        val = val[:-2]
    try:
        return type_func(val)
    except:
        return default

def parse_flow(flow):
    t_first_tx = parse_ns3_val(flow.get("timeFirstTxPacket"), float)
    t_last_rx = parse_ns3_val(flow.get("timeLastRxPacket"), float)
    rx_bytes = parse_ns3_val(flow.get("rxBytes"), float)
    
    duration = t_last_rx - t_first_tx
    if duration <= 1e-9: 
        duration = 1.0 

    return {
        "flow_id": parse_ns3_val(flow.get("flowId"), int),
        "tx_packets": parse_ns3_val(flow.get("txPackets"), int),
        "rx_packets": parse_ns3_val(flow.get("rxPackets"), int),
        "lost_packets": parse_ns3_val(flow.get("lostPackets"), int),
        "delay_sum": parse_ns3_val(flow.get("delaySum"), float),
        "jitter_sum": parse_ns3_val(flow.get("jitterSum"), float),
        "first_tx_time": t_first_tx,
        "last_tx_time": parse_ns3_val(flow.get("timeLastTxPacket"), float),
        "first_rx_time": parse_ns3_val(flow.get("timeFirstRxPacket"), float),
        "last_rx_time": t_last_rx,
        "throughput": (rx_bytes * 8) / duration 
    }

def parse_scenario(path):
    config_path = path / "config.json"
    
    if config_path.exists():
        config = json.load(open(config_path))
    else:
        config = {"scenario": "unknown", "cameras": []}

    tree = ET.parse(path / "flow.xml")
    root = tree.getroot()

    # FIX: Select only statistical flows
    flows = [parse_flow(f) for f in root.findall("./FlowStats/Flow")]

    return {
        "scenario": config.get("scenario", "unknown"),
        "nodes": config.get("cameras", []),
        "flows": flows
    }

OUT_DIR.mkdir(parents=True, exist_ok=True)

if not RAW_DIR.exists():
    print(f"Error: Input directory {RAW_DIR} not found.")
else:
    count = 0
    for scenario_dir in sorted(RAW_DIR.iterdir()):
        if not scenario_dir.is_dir():
            continue

        try:
            data = parse_scenario(scenario_dir)
            
            out_file = OUT_DIR / f"{scenario_dir.name}.json"
            
            with open(out_file, "w") as f:
                json.dump(data, f, indent=2)
                
            print(f"Saved {out_file}")
            count += 1
            
        except Exception as e:
            print(f"Skipping {scenario_dir.name}: {e}")

    print(f"\nProcessing complete. {count} files saved to '{OUT_DIR}'")