"""Shared paths for the book's scripts.

Every script that reads the dataset or the chapters imports its paths from here,
so nothing hard-codes a machine path. Scripts in subfolders add this folder to
sys.path first:

    sys.path.insert(0, str(Path(__file__).resolve().parents[N]))  # the scripts folder
    from paths import DB, REPO, XLSX

The dataset folder can be overridden with the CHARLESRIVER_DATA environment
variable (for example, to test a new build before it replaces datasets/).
"""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATASETS = Path(os.environ.get("CHARLESRIVER_DATA", REPO / "datasets")).resolve()
DB = DATASETS / "CharlesRiver.sqlite"
XLSX = DATASETS / "CharlesRiver.xlsx"
SUPPORT_XLSX = DATASETS / "CharlesRiver_support.xlsx"

SCRIPTS = REPO / "scripts"
FIGURES = SCRIPTS / "figures"
VERIFY = SCRIPTS / "verify"
COMPANION = SCRIPTS / "companion"
REFERENCE_MODELS = COMPANION / "pbi" / "reference"


def db_uri(read_only: bool = True) -> str:
    """The sqlite3 URI for the dataset, read-only by default."""
    return f"{DB.as_uri()}?mode=ro" if read_only else DB.as_uri()


def require_dataset() -> None:
    if not DB.is_file():
        raise SystemExit(f"Dataset not found: {DB}. Put CharlesRiver.sqlite in datasets/ "
                         "or set CHARLESRIVER_DATA.")
