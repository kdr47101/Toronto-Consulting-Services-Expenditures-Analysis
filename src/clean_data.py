"""Harmonize the raw Toronto consulting-expenditures workbooks into one tidy table.

Each workbook has one sheet per year. Header rows live at index 1 or 2.
Column names drift across years (case, whitespace, embedded newlines) but the
semantic columns are stable, so we map them to a canonical schema.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
OUT_FILE = OUT_DIR / "consulting_expenditures.parquet"
OUT_CSV = OUT_DIR / "consulting_expenditures.csv"

CANONICAL_COLUMNS = [
    "year",
    "budget_type",
    "city_abc",
    "expense_category",
    "division_board",
    "contract_date",
    "contract_number",
    "consultant_name",
    "description",
    "expenditure",
]

# Map normalized header tokens to canonical column names.
HEADER_MAP = {
    "year": "year",
    "budget type": "budget_type",
    "city / abc": "city_abc",
    "expense category": "expense_category",
    "division / board": "division_board",
    "division/board": "division_board",
    "contract date dd-mm-yyyy": "contract_date",
    "contract date mm-dd-yy": "contract_date",
    "contract / po / dpo date mm-dd-yr": "contract_date",
    "contract / po number": "contract_number",
    "contract / po / dpo no(s).": "contract_number",
    "consultant's name": "consultant_name",
    "description of the work": "description",
    "description of work": "description",
}

EXPENDITURE_RE = re.compile(r"^\d{4}\s*expenditure\s*\$?$")
KEYWORDS = {"year", "consultant", "expenditure", "division"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def _find_header_row(df: pd.DataFrame) -> int:
    for i in range(min(8, len(df))):
        row = df.iloc[i]
        vals = [_normalize(v) for v in row.tolist() if pd.notna(v)]
        if len(vals) < 5:
            continue
        if any(any(k in v for k in KEYWORDS) for v in vals):
            return i
    raise ValueError("no header row found in first 8 rows")


def _rename_columns(columns: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for col in columns:
        key = _normalize(col)
        if key in HEADER_MAP:
            out[col] = HEADER_MAP[key]
        elif EXPENDITURE_RE.match(key):
            out[col] = "expenditure"
    return out


def _load_sheet(xl: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    probe = xl.parse(sheet, header=None, nrows=8)
    header_row = _find_header_row(probe)
    df = xl.parse(sheet, header=header_row)
    df = df.rename(columns=_rename_columns(list(df.columns)))
    keep = [c for c in CANONICAL_COLUMNS if c in df.columns]
    df = df[keep].copy()
    # Drop rows where expenditure and consultant are both missing — these are
    # blank trailing rows or footnotes.
    df = df.dropna(subset=["expenditure", "consultant_name"], how="all")
    return df


def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["expenditure"] = pd.to_numeric(df["expenditure"], errors="coerce")
    df["contract_date"] = pd.to_datetime(df["contract_date"], errors="coerce")

    str_cols = [
        "budget_type",
        "city_abc",
        "expense_category",
        "division_board",
        "consultant_name",
        "description",
    ]
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip()
            # collapse internal whitespace
            df[c] = df[c].str.replace(r"\s+", " ", regex=True)

    if "contract_number" in df.columns:
        df["contract_number"] = df["contract_number"].astype("string").str.strip()

    # Normalize categorical values
    if "budget_type" in df.columns:
        df["budget_type"] = df["budget_type"].str.title()

    # Canonicalize ampersand/and inconsistencies in division/department names.
    for c in ("city_abc", "division_board"):
        if c in df.columns:
            df[c] = df[c].str.replace(" & ", " and ", regex=False)

    return df


def build() -> pd.DataFrame:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []

    for path in sorted(RAW_DIR.glob("*.xlsx")):
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names:
            df = _load_sheet(xl, sheet)
            df["source_file"] = path.name
            df["source_sheet"] = sheet
            frames.append(df)
            print(f"  loaded {path.name}::{sheet} -> {len(df)} rows")

    full = pd.concat(frames, ignore_index=True)
    full = _coerce(full)

    # Drop rows missing the critical fields
    before = len(full)
    full = full.dropna(subset=["year", "expenditure", "consultant_name"])
    full = full[full["expenditure"] > 0]
    print(f"  dropped {before - len(full)} rows with missing/zero year/exp/vendor")

    full = full.reset_index(drop=True)
    full.to_parquet(OUT_FILE, index=False)
    full.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {len(full)} rows to {OUT_FILE}")
    print(f"      year range: {int(full['year'].min())} - {int(full['year'].max())}")
    print(f"      total spend: ${full['expenditure'].sum():,.0f}")
    return full


if __name__ == "__main__":
    build()
