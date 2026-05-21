"""
tests/test_00_imports.py
───────────────────────────
Just tries to import stuff. 

Expected output:

polars: 1.3.0
dask: 2024.8.2
All imports OK
"""
import polars as pl
import dask
import rich
import pytest

print("polars:", pl.__version__, flush=True)
print("dask:", dask.__version__, flush=True)
print("All imports OK", flush=True)