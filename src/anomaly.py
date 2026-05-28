"""Flag consulting contracts worth a second look.

Two complementary signals:
1) **Z-score within (year, expense_category)** — contracts that are unusually
   large *given the category baseline*. Log-transformed, so we score how many
   orders of magnitude a contract sits above its peer group.
2) **Isolation Forest** — multivariate anomaly score using amount, category,
   division, budget type, vendor frequency, and contract-date offset. Catches
   weird combinations even when the dollar amount looks ordinary on its own.

Output: data/processed/anomalies.csv, ranked by combined score.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = _ROOT / "data" / "processed" / "consulting_expenditures.parquet"
OUT_FILE = _ROOT / "data" / "processed" / "anomalies.csv"


def _category_zscore(df: pd.DataFrame) -> pd.Series:
    log_amt = np.log10(df["expenditure"].clip(lower=1.0))
    grouper = [df["year"], df["expense_category"]]
    mean = log_amt.groupby(grouper).transform("mean")
    std = log_amt.groupby(grouper).transform("std")
    z = (log_amt - mean) / std.replace(0, np.nan)
    return z.fillna(0)


def _isoforest_scores(df: pd.DataFrame, random_state: int = 0) -> np.ndarray:
    feats = pd.DataFrame(index=df.index)
    feats["log_amt"] = np.log10(df["expenditure"].clip(lower=1.0))

    # vendor frequency — many anomalies sit with one-off vendors
    vendor_freq = df["consultant_name"].map(df["consultant_name"].value_counts())
    feats["vendor_freq"] = vendor_freq.fillna(0)

    # contract age = years between contract_date and the spend year (negative if backdated long ago)
    cd = df["contract_date"]
    feats["contract_age_yrs"] = (df["year"] - cd.dt.year).fillna(0).astype(float)

    # categorical encodings — Isolation Forest tolerates integer codes
    for c in ("expense_category", "division_board", "budget_type", "city_abc"):
        feats[c] = LabelEncoder().fit_transform(df[c].fillna("__missing__").astype(str))

    model = IsolationForest(
        n_estimators=300,
        contamination=0.03,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(feats)
    # higher = more anomalous
    return -model.score_samples(feats)


def find_anomalies(df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    out = df.copy()
    out["category_zscore"] = _category_zscore(out)
    out["isoforest_score"] = _isoforest_scores(out)

    # combine: rank-based mean so the two signals share a comparable scale
    out["z_rank"] = out["category_zscore"].rank(pct=True)
    out["if_rank"] = out["isoforest_score"].rank(pct=True)
    out["anomaly_score"] = (out["z_rank"] + out["if_rank"]) / 2

    flagged = out.sort_values("anomaly_score", ascending=False).head(top_n)
    return flagged[
        [
            "year",
            "consultant_name",
            "division_board",
            "expense_category",
            "budget_type",
            "expenditure",
            "description",
            "category_zscore",
            "isoforest_score",
            "anomaly_score",
        ]
    ]


def run(top_n: int = 50) -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"{DATA_FILE} not found — run clean_data.py first")
    df = pd.read_parquet(DATA_FILE)
    flagged = find_anomalies(df, top_n=top_n)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    flagged.to_csv(OUT_FILE, index=False)
    print(f"wrote {len(flagged)} flagged contracts to {OUT_FILE}")
    print("\nTop 10 anomalies:")
    print(flagged.head(10)[["year", "consultant_name", "expenditure", "expense_category", "anomaly_score"]].to_string(index=False))
    return flagged


if __name__ == "__main__":
    run()
