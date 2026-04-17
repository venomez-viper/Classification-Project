import duckdb


class DataValidator:
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.con = connection

    def check_table_exists(self, table_name: str) -> None:
        result = self.con.execute(f"""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{table_name}'
        """).fetchone()[0]

        if result == 0:
            raise ValueError(f"Table '{table_name}' does not exist")

    def row_count(self, table_name: str) -> int:
        self.check_table_exists(table_name)
        return self.con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    def null_summary(self, table_name: str, columns: list[str]) -> dict:
        self.check_table_exists(table_name)

        result = {}
        for col in columns:
            null_count = self.con.execute(f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE {col} IS NULL
            """).fetchone()[0]
            result[col] = null_count
        return result

    def duplicate_count(self, table_name: str, key_columns: list[str]) -> int:
        self.check_table_exists(table_name)
        keys = ", ".join(key_columns)

        query = f"""
            SELECT COUNT(*)
            FROM (
                SELECT {keys}, COUNT(*) AS cnt
                FROM {table_name}
                GROUP BY {keys}
                HAVING COUNT(*) > 1
            ) t
        """
        return self.con.execute(query).fetchone()[0]

    def describe_table(self, table_name: str):
        self.check_table_exists(table_name)
        return self.con.execute(f"DESCRIBE {table_name}").fetchdf()

    def validate_task1(self) -> None:
        print("\n--- VALIDATING TASK1 ---")
        print("Rows:", self.row_count("task1"))
        print("Nulls:", self.null_summary(
            "task1",
            ["CompanyId", "AsOfDate", "LongProfile", "SegmentName", "SegmentDescription", "MstarGlobal"]
        ))
        print("Duplicate CompanyId + AsOfDate + SegmentName:", self.duplicate_count(
            "task1",
            ["CompanyId", "AsOfDate", "SegmentName"]
        ))

    def validate_task2(self) -> None:
        print("\n--- VALIDATING TASK2 ---")
        print("Rows:", self.row_count("task2"))
        print("Nulls:", self.null_summary(
            "task2",
            ["CompanyId", "AsOfDate", "SegmentName", "SegmentDescription", "Subindustry"]
        ))
        print("Duplicate CompanyId + AsOfDate + SegmentName:", self.duplicate_count(
            "task2",
            ["CompanyId", "AsOfDate", "SegmentName"]
        ))
