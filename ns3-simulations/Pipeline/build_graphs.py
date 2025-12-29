import torch
import numpy as np
import os
from torch_geometric.data import Data
from sklearn.preprocessing import LabelEncoder

IN = "dataset/slices"
OUT = "dataset/graphs"
os.makedirs(OUT, exist_ok=True)

le = LabelEncoder()

for file in os.listdir(IN):
    if not file.endswith('.npy'): 
        continue

    try:
        # Load raw object data
        raw_data = np.load(f"{IN}/{file}", allow_pickle=True)
    except Exception as e:
        print(f"Error loading file {file}: {e}")
        continue
  
    features = []
    for col_idx in range(2, 8): 
        col_data = raw_data[:, col_idx]
        if isinstance(col_data[0], str):
            try:
                numeric_col = le.fit_transform(col_data.astype(str))
            except:
                numeric_col = np.zeros(len(col_data)) # Fallback
        else:
            numeric_col = col_data
        features.append(numeric_col)
    
    
    x_data = np.column_stack(features).astype(float)
    x = torch.tensor(x_data, dtype=torch.float)

  
    y_raw = raw_data[:, -1]
    if isinstance(y_raw[0], str):
        y_data = le.fit_transform(y_raw.astype(str))
    else:
        y_data = y_raw.astype(float)
    y = torch.tensor(y_data, dtype=torch.float) 

    num_nodes = x.shape[0]
    
    edge_index = torch.tensor([[i, i] for i in range(num_nodes)], dtype=torch.long).T
    
    data_obj = Data(x=x, edge_index=edge_index, y=y)
    torch.save(data_obj, f"{OUT}/{file.replace('.npy', '.pt')}")

print("Processing complete.")