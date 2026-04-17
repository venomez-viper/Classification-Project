from pathlib import Path
import duckdb


class DataLoader:
    def __init__(self, base_path: str):
        self.base = Path(base_path)
        self.raw_dir = self.base / "data" / "raw"
        self.db_path = self.base / "data" / "db" / "analytics.duckdb"

        self.con = None

    def connect(self):
        """Connect to DuckDB"""
        self.con = duckdb.connect(str(self.db_path))
        print("Connected to DuckDB")

    def _validate_files(self):
        """Check if required files exist"""
        task1 = self.raw_dir / "task1_gecs_classification_final (2).csv"
        task2 = self.raw_dir / "task2_subindustry_classification_final (2).csv"

        if not task1.exists():
            raise FileNotFoundError(f"Missing file: {task1}")

        if not task2.exists():
            raise FileNotFoundError(f"Missing file: {task2}")

        return task1, task2

    def load_data(self):
        """Load CSV files into DuckDB tables"""
        if self.con is None:
            raise Exception("Database not connected. Call connect() first.")

        task1_file, task2_file = self._validate_files()

        print("Loading Task 1...")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE task1 AS
            SELECT *
            FROM read_csv_auto('{task1_file.as_posix()}', header=True)
        """)

        print("Loading Task 2...")
        self.con.execute(f"""
            CREATE OR REPLACE TABLE task2 AS
            SELECT *
            FROM read_csv_auto('{task2_file.as_posix()}', header=True)
        """)

        print("Data loaded successfully")

    def validate_tables(self):
        """Check if tables were created correctly"""
        if self.con is None:
            raise Exception("Database not connected.")

        task1_count = self.con.execute("SELECT COUNT(*) FROM task1").fetchone()[0]
        task2_count = self.con.execute("SELECT COUNT(*) FROM task2").fetchone()[0]

        print(f"Task1 rows: {task1_count}")
        print(f"Task2 rows: {task2_count}")

    def run(self):
        """Run full pipeline"""
        self.connect()
        self.load_data()
        self.validate_tables()