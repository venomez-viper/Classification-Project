import duckdb
import os
from pathlib import Path

base_path = Path(__file__).resolve().parent
db_path = base_path / "data" / "db" / "analytics.duckdb"
output_path = base_path / "outputs"

output_path.mkdir(exist_ok=True)

con = duckdb.connect(str(db_path))

con.execute(f"COPY task1_clean TO '{(output_path / 'task1_clean.csv').as_posix()}' (HEADER, DELIMITER ',')")
con.execute(f"COPY task2_clean TO '{(output_path / 'task2_clean.csv').as_posix()}' (HEADER, DELIMITER ',')")

con.close()

print("Export complete!")
print(f"Files saved in: {output_path}")