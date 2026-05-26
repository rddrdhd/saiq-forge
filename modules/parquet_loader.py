import pyarrow.parquet as pq
import pandas as pd
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