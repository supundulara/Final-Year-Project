# scripts/metrics.py

import csv
import os

def run_ping(net, hosts, filename="data/ping_results.csv"):
    """
    Measures latency from cameras to edge and edge to cloud
    and stores results in CSV.
    """
    if not os.path.exists("data"):
        os.makedirs("data")

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["src", "dst", "latency_ms"])

        # Camera -> Edge
        for cam in hosts:
            result = net.pingFull([cam, net.get('edge')])
            
            # result[0] = (src_host, dst_host, (sent, received, rttmin, rttavg, rttmax, rttdev))
            # Extract rttavg from result[0][2][3]
            if result and len(result) > 0 and len(result[0]) > 2:
                latency = result[0][2][3]  # rttavg
            else:
                latency = 0.0
                    
            writer.writerow([cam.name, "edge", latency])

        # Edge -> Cloud
        result = net.pingFull([net.get('edge'), net.get('cloud')])
        
        if result and len(result) > 0 and len(result[0]) > 2:
            latency = result[0][2][3]  # rttavg
        else:
            latency = 0.0
                
        writer.writerow(["edge", "cloud", latency])