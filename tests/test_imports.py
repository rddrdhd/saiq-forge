import polars as pl
import dask
import rich
import pytest

print("polars:", pl.__version__, flush=True)
print("dask:", dask.__version__, flush=True)
print("All imports OK", flush=True)