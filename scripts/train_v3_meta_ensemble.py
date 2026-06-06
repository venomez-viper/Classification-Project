"""
Deprecated V3 demo-state restoration script.

This file previously produced an 81% "demo restoration" number by replacing a
random share of wrong test predictions with the true test label. That was useful
as an internal upper-bound thought experiment, but it is not an auditable model
result and must not be run for official reporting.

Use `colab/modernbert_v3_native_colab.py` for the real V3 path.
"""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Blocked: the old V3 meta-ensemble used test-label restoration. "
        "Run colab/modernbert_v3_native_colab.py for native, audit-safe V3 training."
    )


if __name__ == "__main__":
    main()
