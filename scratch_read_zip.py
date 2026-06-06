import zipfile
import json

def extract_summary(zip_path):
    print(f"Reading {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            summary_files = [f for f in z.namelist() if f.endswith('results.json') or f.endswith('summary.json')]
            if not summary_files:
                print("No summary JSON found in the zip.")
                return
            
            for file in summary_files:
                print(f"\n--- Contents of {file} ---")
                data = json.loads(z.read(file))
                print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error reading zip: {e}")

if __name__ == "__main__":
    extract_summary("modernbert_gecs_v2_full_full_outputs.zip")
