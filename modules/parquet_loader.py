import pyarrow.parquet as pq
import pandas as pd
from typing import Generator # for batch shard
def load_full_parquet(path: str):
    parquet_file = pd.read_parquet(path)
    return parquet_file
def load_sharded_parquet(path: str, rank: int, world_size: int) -> pd.DataFrame:
    # load metadata
    parquet_file = pq.ParquetFile(path)
    total_row_groups = parquet_file.num_row_groups

    # round-robin between processes
    my_row_groups = [i for i in range(total_row_groups) if i % world_size == rank]

    if not my_row_groups:
        return parquet_file.schema.to_arrow_schema().empty_table().to_pandas()

    table = parquet_file.read_row_groups(my_row_groups)
    return table.to_pandas()

def batch_sharded_parquet(
    path: str, rank: int, world_size: int, groups_per_batch: int = 1
) -> Generator[pd.DataFrame, None, None]:
    """
    Generator loads batches for rank
    groups_per_batch: How many Row Groups goes to one batch.
    """
    parquet_file = pq.ParquetFile(path)
    total_row_groups = parquet_file.num_row_groups
    my_row_groups = [i for i in range(total_row_groups) if i % world_size == rank]

    if not my_row_groups:
        print(f"[R{rank}]: No Row Groups.")
        return

    print(
        f"[R{rank}] working on {len(my_row_groups)} row groups divided to batches."
    )

    for i in range(0, len(my_row_groups), groups_per_batch):
        batch_groups = my_row_groups[i : i + groups_per_batch]
        
        # load just one batch
        table = parquet_file.read_row_groups(batch_groups)
        df_batch = table.to_pandas()
        
        yield df_batch