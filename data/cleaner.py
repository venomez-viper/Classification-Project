import duckdb
from pathlib import Path


class DataCleaner:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.con = None

    def connect(self):
        self.con = duckdb.connect(self.db_path)
        print("Connected to DuckDB")

    def clean_task1(self):
        print("\nCleaning task1 → task1_clean")

        self.con.execute("""
            CREATE OR REPLACE TABLE task1_clean AS
            SELECT
                CompanyId,
                AsOfDate,
                NULLIF(TRIM(CAST(LongProfile AS VARCHAR)), '') AS LongProfile,
                NULLIF(TRIM(CAST(SegmentName AS VARCHAR)), '') AS SegmentName,
                NULLIF(TRIM(CAST(SegmentDescription AS VARCHAR)), '') AS SegmentDescription,
                Revenue,
                total_revenue_company_as_of,
                revenue_share,
                is_largest_share_segment,
                MstarGlobal
            FROM task1
        """)

    def clean_task2(self):
        print("\nCleaning task2 → task2_clean")

        self.con.execute("""
            CREATE OR REPLACE TABLE task2_clean AS
            SELECT
                CompanyId,
                AsOfDate,
                NULLIF(TRIM(CAST(SegmentName AS VARCHAR)), '') AS SegmentName,
                NULLIF(TRIM(CAST(SegmentDescription AS VARCHAR)), '') AS SegmentDescription,
                NULLIF(TRIM(CAST(Subindustry AS VARCHAR)), '') AS Subindustry
            FROM task2
        """)

    def export_to_cleaned(self, cleaned_dir: str):
        """Export cleaned tables to CSV so the team scripts can read them.
        This creates data/cleaned/task1_clean.csv and task2_clean.csv."""
        out = Path(cleaned_dir)
        out.mkdir(parents=True, exist_ok=True)

        t1_path = (out / "task1_clean.csv").as_posix()
        t2_path = (out / "task2_clean.csv").as_posix()

        print(f"Exporting task1_clean -> {t1_path}")
        self.con.execute(f"COPY task1_clean TO '{t1_path}' (HEADER, DELIMITER ',')")

        print(f"Exporting task2_clean -> {t2_path}")
        self.con.execute(f"COPY task2_clean TO '{t2_path}' (HEADER, DELIMITER ',')")

        print("Export to data/cleaned/ done.")

    def run(self):
        self.connect()
        self.clean_task1()
        self.clean_task2()
        self.con.close()
        print("\nCleaning complete")