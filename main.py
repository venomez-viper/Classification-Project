import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from data.loader import DataLoader
from data.validator import DataValidator
from data.cleaner import DataCleaner


if __name__ == "__main__":
    base_path = r"C:\Users\akash\Desktop\capstone MGT 599"
    db_path = r"C:\Users\akash\Desktop\capstone MGT 599\data\db\analytics.duckdb"

    loader = DataLoader(base_path)
    loader.connect()
    loader.load_data()
    loader.validate_tables()

    validator = DataValidator(loader.con)
    validator.validate_task1()
    validator.validate_task2()

    loader.con.close()
    print("\nValidation complete")

    cleaner = DataCleaner(db_path)
    cleaner.run()