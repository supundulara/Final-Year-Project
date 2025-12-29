import pandas as pd
import os
import numpy as np
import json

IN = "dataset/parsed"
OUT = "dataset/slices"
os.makedirs(OUT, exist_ok=True)

SLICE = 1.0
STEP  = 0.5

for file in os.listdir(IN):
    if file.endswith('.json'):
        with open(f"{IN}/{file}", 'r') as f:
            data = json.load(f)

        if 'nodes' in data:
            df = pd.json_normalize(data['nodes'])
            df['cumulative_time'] = df['frame_interval'].cumsum()
        else:
            continue

        tmax = df['cumulative_time'].max()
        print(f"Processing file: {file}, tmax: {tmax}")
        start = 0

        while start < tmax:
            window = df[(df['cumulative_time'] >= start) & (df['cumulative_time'] < start + SLICE)]
            print(f"Start: {start}, Window size: {len(window)}")
            if not window.empty:
                np.save(f"{OUT}/{file}_{start:.1f}.npy", window.to_numpy())
            start += STEP
