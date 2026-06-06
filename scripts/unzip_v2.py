import zipfile
import os

zip_path = "modernbert_gecs_v2_full_full_outputs.zip"
extract_dir = "models_v18/modernbert_v2_outputs"

print(f"Extracting {zip_path}...")
os.makedirs(extract_dir, exist_ok=True)

try:
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)
    print(f"Successfully extracted to {extract_dir}")
    
    print("\nFiles available for V3 Ensemble:")
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            print(os.path.join(root, f))
            
except Exception as e:
    print(f"Error during extraction: {e}")
