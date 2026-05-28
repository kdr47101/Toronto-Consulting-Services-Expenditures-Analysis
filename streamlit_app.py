"""Interactive explorer for Toronto consulting expenditures.

Run with:  streamlit run streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
import analyze  # noqa: E402
import anomaly  # noqa: E402

st.set_page_config(
    page_title="Toronto Consulting Spend",
    layout="wide",
    page_icon=":bar_chart:",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    return analyze.load()


df = load_data()

# ----- sidebar filters -----
st.sidebar.title("Filters")
years = sorted(df["year"].dropna().unique().tolist())
yr_min, yr_max = st.sidebar.select_slider(
    "Year range",
    options=years,
    value=(min(years), max(years)),
)
divisions = ["(All)"] + sorted(df["division_board"].dropna().unique().tolist())
division_sel = st.sidebar.selectbox("Division / Board", divisions)
budget_sel = st.sidebar.multiselect(
    "Budget type",
    sorted(df["budget_type"].dropna().unique().tolist()),
    default=sorted(df["budget_type"].dropna().unique().tolist()),
)

mask = (df["year"] >= yr_min) & (df["year"] <= yr_max)
if division_sel != "(All)":
    mask &= df["division_board"] == division_sel
if budget_sel:
    mask &= df["budget_type"].isin(budget_sel)
filtered = df[mask]

# ----- header -----
st.title("Toronto Consulting Services Expenditures")
st.caption(
    "City of Toronto external consulting spend, 2017-2024. "
    "Source: open.toronto.ca / consulting-services-expenditures."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total spend", f"${filtered['expenditure'].sum()/1e6:,.1f}M")
c2.metric("Contracts", f"{len(filtered):,}")
c3.metric("Unique vendors", f"{filtered['consultant_name'].nunique():,}")
c4.metric("Median contract", f"${filtered['expenditure'].median():,.0f}")

# ----- charts -----
tab1, tab2, tab3, tab4 = st.tabs(["Trend", "Vendors", "Divisions", "Anomalies"])

with tab1:
    yt = analyze.yearly_totals(filtered)
    fig = px.bar(yt, x="year", y="total_spend", text_auto=".2s",
                 title="Annual consulting spend")
    fig.update_layout(yaxis_tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(yt, use_container_width=True)

with tab2:
    n = st.slider("Top N vendors", 5, 50, 15)
    tv = analyze.top_vendors(filtered, n=n)
    fig = px.bar(tv.iloc[::-1], x="total_spend", y="consultant_name",
                 orientation="h", title=f"Top {n} vendors")
    fig.update_layout(xaxis_tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(tv, use_container_width=True)

with tab3:
    bd = analyze.by_division(filtered, n=20)
    fig = px.bar(bd.iloc[::-1], x="total_spend", y="division_board",
                 orientation="h", title="Top divisions/boards")
    fig.update_layout(xaxis_tickformat="$,.0f")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(bd, use_container_width=True)

with tab4:
    n = st.slider("Top N flagged contracts", 10, 100, 30)
    flagged = anomaly.find_anomalies(filtered, top_n=n)
    st.markdown(
        "These are the contracts whose dollar amount looks most unusual "
        "relative to their (year, expense_category) peer group, combined with "
        "an Isolation Forest score over multivariate features. **Use them as "
        "a starting point for review, not as accusations.**"
    )
    st.dataframe(
        flagged.style.format({
            "expenditure": "${:,.0f}",
            "anomaly_score": "{:.3f}",
            "category_zscore": "{:.2f}",
            "isoforest_score": "{:.3f}",
        }),
        use_container_width=True,
    )
