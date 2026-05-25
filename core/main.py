"""
core/main.py
"""
import pandas as pd
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import load_config

if __name__ == "__main__":
    cfg = load_config("config/my_default.yml")
    
    df_geo = pd.read_parquet(cfg["input"]["path_geo"])
    df_data = pd.read_parquet(cfg["input"]["path_data"])
    
    print(f"Shape: {df_geo.shape}")
    print(df_geo.head())  
    print("\n" + "="*30 + "\n")
    
    print(f"Shape: {df_data.shape}")
    print(df_data.head(3))