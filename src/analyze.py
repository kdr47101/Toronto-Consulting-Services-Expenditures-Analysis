"""Reusable analysis functions and a CLI entrypoint that renders all figures.

Functions take a tidy DataFrame and return a DataFrame; the CLI saves charts
to reports/figures/.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = _ROOT / "data" / "processed" / "consulting_expenditures.parquet"
FIG_DIR = _ROOT / "reports" / "figures"


def load() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"{DATA_FILE} not found — run clean_data.py first")
    return pd.read_parquet(DATA_FILE)


# ---------- analysis functions ----------

def yearly_totals(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("year").agg(
        total_spend=("expenditure", "sum"),
        contracts=("expenditure", "size"),
        median_contract=("expenditure", "median"),
        unique_vendors=("consultant_name", "nunique"),
    )
    g["yoy_growth"] = g["total_spend"].pct_change()
    return g.reset_index()


def top_vendors(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    g = df.groupby("consultant_name").agg(
        total_spend=("expenditure", "sum"),
        contracts=("expenditure", "size"),
        years_active=("year", "nunique"),
    )
    g = g.sort_values("total_spend", ascending=False).head(n)
    g["share_of_total"] = g["total_spend"] / df["expenditure"].sum()
    return g.reset_index()


def vendor_concentration(df: pd.DataFrame) -> pd.DataFrame:
    """Per-year top-10 share + HHI on total vendor spend (× 10,000)."""
    out = []
    for year, sub in df.groupby("year"):
        totals = sub.groupby("consultant_name")["expenditure"].sum()
        total = totals.sum()
        if total == 0:
            continue
        shares = totals / total
        top10_share = shares.sort_values(ascending=False).head(10).sum()
        hhi = (shares ** 2).sum() * 10_000
        out.append({"year": year, "top10_share": top10_share, "hhi": hhi, "num_vendors": len(totals)})
    return pd.DataFrame(out)


def by_division(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    g = df.groupby("division_board")["expenditure"].agg(["sum", "size"]).sort_values("sum", ascending=False)
    g.columns = ["total_spend", "contracts"]
    return g.head(n).reset_index()


def by_city_abc(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("city_abc")["expenditure"].agg(["sum", "size"]).sort_values("sum", ascending=False)
    g.columns = ["total_spend", "contracts"]
    return g.reset_index()


def by_expense_category(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("expense_category")["expenditure"].agg(["sum", "size"]).sort_values("sum", ascending=False)
    g.columns = ["total_spend", "contracts"]
    return g.reset_index()


def division_growth(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """Yearly spend for the top-N divisions by total spend."""
    top = (
        df.groupby("division_board")["expenditure"].sum().sort_values(ascending=False).head(top_n).index
    )
    sub = df[df["division_board"].isin(top)]
    pivot = sub.pivot_table(index="year", columns="division_board", values="expenditure", aggfunc="sum").fillna(0)
    return pivot


# ---------- chart helpers ----------

def _style():
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "font.size": 11,
    })


def _fmt_millions(x, _pos):
    if x >= 1e6:
        return f"${x/1e6:.0f}M"
    if x >= 1e3:
        return f"${x/1e3:.0f}K"
    return f"${x:.0f}"


def _save(fig, name: str):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path}")


def plot_yearly_totals(df: pd.DataFrame):
    yt = yearly_totals(df)
    fig, ax = plt.subplots()
    bars = ax.bar(yt["year"], yt["total_spend"] / 1e6, color="#1f4e79")
    for b, v in zip(bars, yt["total_spend"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8, f"${v/1e6:.1f}M",
                ha="center", fontsize=9)
    ax.set_title("Toronto consulting spend by year, 2017-2024")
    ax.set_ylabel("Total spend")
    ax.set_xlabel("Year")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.0f}M"))
    _save(fig, "01_yearly_totals.png")


def plot_top_vendors(df: pd.DataFrame, n: int = 15):
    tv = top_vendors(df, n=n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(tv["consultant_name"], tv["total_spend"] / 1e6, color="#c0504d")
    ax.set_title(f"Top {n} consulting vendors by cumulative spend, 2017-2024")
    ax.set_xlabel("Total spend")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.0f}M"))
    for i, v in enumerate(tv["total_spend"]):
        ax.text(v / 1e6 + 0.3, i, f"${v/1e6:.1f}M", va="center", fontsize=9)
    _save(fig, "02_top_vendors.png")


def plot_concentration(df: pd.DataFrame):
    vc = vendor_concentration(df)
    fig, ax1 = plt.subplots()
    ax1.plot(vc["year"], vc["top10_share"] * 100, marker="o", color="#1f4e79", label="Top-10 vendor share (%)")
    ax1.set_ylabel("Top-10 share (%)", color="#1f4e79")
    ax1.set_xlabel("Year")
    ax1.set_ylim(0, 100)

    ax2 = ax1.twinx()
    ax2.plot(vc["year"], vc["hhi"], marker="s", color="#c0504d", label="HHI")
    ax2.set_ylabel("HHI (vendor concentration)", color="#c0504d")
    ax2.spines["top"].set_visible(False)

    ax1.set_title("Vendor concentration over time")
    _save(fig, "03_concentration.png")


def plot_by_division(df: pd.DataFrame, n: int = 15):
    bd = by_division(df, n=n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(bd["division_board"], bd["total_spend"] / 1e6, color="#2e7d32")
    ax.set_title(f"Top {n} divisions/boards by consulting spend, 2017-2024")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.0f}M"))
    ax.set_xlabel("Total spend")
    _save(fig, "04_top_divisions.png")


def plot_expense_category(df: pd.DataFrame):
    ec = by_expense_category(df).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(ec["expense_category"], ec["total_spend"] / 1e6, color="#6a3d9a")
    ax.set_title("Spend by expense category, 2017-2024")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.0f}M"))
    ax.set_xlabel("Total spend")
    _save(fig, "05_expense_category.png")


def plot_division_growth(df: pd.DataFrame):
    p = division_growth(df, top_n=6)
    fig, ax = plt.subplots()
    for col in p.columns:
        ax.plot(p.index, p[col] / 1e6, marker="o", label=col)
    ax.set_title("Annual spend trajectory — top 6 divisions")
    ax.set_ylabel("Spend")
    ax.set_xlabel("Year")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.0f}M"))
    ax.legend(fontsize=8, loc="upper left")
    _save(fig, "06_division_growth.png")


def plot_contract_size_distribution(df: pd.DataFrame):
    vals = df["expenditure"].clip(lower=1)
    fig, ax = plt.subplots()
    ax.hist(np.log10(vals), bins=40, color="#1f4e79", alpha=0.85)
    ax.set_title("Distribution of contract sizes (log10 scale)")
    ax.set_xlabel("log10(contract amount, CAD)")
    ax.set_ylabel("Number of contracts")
    ax.axvline(np.log10(df["expenditure"].median()), color="orange", linestyle="--",
               label=f"median ${df['expenditure'].median():,.0f}")
    ax.legend()
    _save(fig, "07_contract_size_distribution.png")


def render_all():
    _style()
    df = load()
    plot_yearly_totals(df)
    plot_top_vendors(df)
    plot_concentration(df)
    plot_by_division(df)
    plot_expense_category(df)
    plot_division_growth(df)
    plot_contract_size_distribution(df)


if __name__ == "__main__":
    render_all()
