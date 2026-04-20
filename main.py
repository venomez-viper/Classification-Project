# main.py
# Entry point for the full Week 2 pipeline
#
# Run this FIRST before any team scripts.
# It loads the raw CSVs into DuckDB, validates them, cleans them,
# then exports the cleaned tables to data/cleaned/ as CSVs
# so everyone else's scripts can find them.
#
# Usage:
#   cd "C:\Users\akash\Desktop\capstone MGT 599"
#   python main.py

from pathlib import Path

from data.loader    import DataLoader
from data.validator import DataValidator
from data.cleaner   import DataCleaner


BASE_PATH   = r"C:\Users\akash\Desktop\capstone MGT 599"
DB_PATH     = r"C:\Users\akash\Desktop\capstone MGT 599\data\db\analytics.duckdb"
CLEANED_DIR = r"C:\Users\akash\Desktop\capstone MGT 599\data\cleaned"


if __name__ == "__main__":
    print("Capstone MGT 599 - Week 2 Pipeline")
    print("-" * 40)

    # Step 1 - load raw CSVs into DuckDB
    print("\n[Step 1] Loading raw data into DuckDB...")
    loader = DataLoader(BASE_PATH)
    loader.connect()
    loader.load_data()
    loader.validate_tables()

    # Step 2 - validate the raw tables
    print("\n[Step 2] Validating raw tables...")
    validator = DataValidator(loader.con)
    validator.validate_task1()
    validator.validate_task2()

    loader.con.close()
    print("validation done")

    # Step 3 - clean both tables and write cleaned tables to DuckDB
    print("\n[Step 3] Cleaning data...")
    cleaner = DataCleaner(DB_PATH)
    cleaner.connect()
    cleaner.clean_task1()
    cleaner.clean_task2()

    # Step 4 - export cleaned tables to data/cleaned/ so team scripts can use them
    print("\n[Step 4] Exporting cleaned CSVs to data/cleaned/...")
    cleaner.export_to_cleaned(CLEANED_DIR)
    cleaner.con.close()

    print("\ndone! cleaned files are in data/cleaned/")
    print("now run the scripts from the scripts/ folder:")
    print("  python lead_tracking.py")
    print("  python dashboard.py")
    print("  python task1_features.py")
    print("  python task2_features.py")
    print("  python model_ready.py  (run this last)")