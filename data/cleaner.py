import duckdb


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
                NULLIF(TRIM(CAST(MstarGlobal AS VARCHAR)), '') AS MstarGlobal
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

    def run(self):
        self.connect()
        self.clean_task1()
        self.clean_task2()
        self.con.close()
        print("\nCleaning complete")