import os
import pandas as pd

RAW = "dataset/raw"
OUT = "dataset/rag_docs"
os.makedirs(OUT, exist_ok=True)

for scenario in os.listdir(RAW):
    df = pd.read_csv(f"{RAW}/{scenario}/network_log.csv")

    summary = f"""
Scenario: {scenario}
Duration: {df.time.max():.1f}s
Nodes: {df.node_id.nunique()}
Avg Throughput: {df.throughput.mean():.2f} Mbps
Avg Delay: {df.delay.mean():.2f} ms
Packet Loss: {df.loss.mean():.4f}

Peak Congestion Time: {df.groupby('time').queue_size.mean().idxmax():.1f}s
"""

    with open(f"{OUT}/{scenario}.txt", "w") as f:
        f.write(summary)

    print(f"Saved {scenario}")
