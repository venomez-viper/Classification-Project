# export_notebooks.py
# Run this from the project root to export both notebooks to HTML/PDF
# Usage: python export_notebooks.py

import subprocess
import sys
import json
import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DOCS_DIR = PROJECT_ROOT / "docs"

notebooks = [
    "week2_submission.ipynb",
    "descriptive_analytics.ipynb",
]


def clean_notebook(nb_path):
    # JetBrains IDEs add a 'jetTransient' key to cell outputs
    # which nbconvert's validator rejects - strip it before converting
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    for cell in nb.get('cells', []):
        for output in cell.get('outputs', []):
            output.pop('jetTransient', None)

    tmp = tempfile.NamedTemporaryFile(
        suffix='.ipynb', delete=False,
        dir=nb_path.parent, mode='w', encoding='utf-8'
    )
    json.dump(nb, tmp, ensure_ascii=False, indent=1)
    tmp.close()
    return Path(tmp.name)


def export_notebook(nb_name):
    nb_path = NOTEBOOKS_DIR / nb_name
    out_name = nb_name.replace(".ipynb", "")

    if not nb_path.exists():
        print(f"not found: {nb_path}")
        return

    print(f"exporting {nb_name}...")
    clean_path = clean_notebook(nb_path)

    try:
        # try PDF first (needs LaTeX)
        result_pdf = subprocess.run([
            sys.executable, "-m", "nbconvert",
            "--to", "pdf",
            "--execute",
            "--ExecutePreprocessor.timeout=300",
            "--output-dir", str(DOCS_DIR),
            "--output", out_name,
            str(clean_path)
        ], capture_output=True, text=True)

        if result_pdf.returncode == 0:
            print(f"  saved PDF -> docs/{out_name}.pdf")
            return

        # fall back to HTML
        print("  LaTeX not found, exporting to HTML...")
        result_html = subprocess.run([
            sys.executable, "-m", "nbconvert",
            "--to", "html",
            "--execute",
            "--ExecutePreprocessor.timeout=300",
            "--output-dir", str(DOCS_DIR),
            "--output", out_name,
            str(clean_path)
        ], capture_output=True, text=True)

        if result_html.returncode == 0:
            print(f"  saved -> docs/{out_name}.html")
            print(f"  for PDF: open in Chrome -> Ctrl+P -> Save as PDF")
        else:
            print(f"  export failed:\n{result_html.stderr[-800:]}")

    finally:
        # always clean up the temp file
        try:
            os.unlink(clean_path)
        except Exception:
            pass


if __name__ == "__main__":
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for nb in notebooks:
        export_notebook(nb)
    print("\ndone. check the docs/ folder.")
