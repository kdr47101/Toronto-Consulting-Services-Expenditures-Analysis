# Tableau workbook — what's included

Open `toronto_consulting.twb` from Tableau Desktop or Tableau Public. The
workbook expects the CSV at `../data/processed/consulting_expenditures.csv`
relative to the `.twb`, so keep the folder structure intact.

Target Tableau version: **2022.4+**. Older versions may refuse to open it;
newer versions will upgrade the schema on first save (this is normal).

## What's pre-built

**Data source** — `consulting_expenditures.csv` connected via CSV
text-scan, with column captions, types, and currency formatting set.

**Calculated fields** (already in the data pane):

| Field | Formula | What it does |
|---|---|---|
| `Is Big 4` | `IF consultant_name IN ("Deloitte LLP", "Ernst & Young LLP", "KPMG LLP") THEN "Big 4" ELSE "Other"` | Flag for the dominant consulting firms |
| `Contract Size Bucket` | Bins: <$10K / $10K-$100K / $100K-$1M / >$1M | Easy histogram dimension |
| `Spend ($M)` | `[expenditure] / 1000000` | Pre-formatted for chart labels |

**Parameters:**

* `Top N Vendors` (integer, 5-50, default 15)
* `Top N Divisions` (integer, 5-30, default 12)

**Worksheets:**

1. **Yearly Spend** — vertical bar chart, year × SUM(expenditure)
2. **Top Vendors** — horizontal bar chart, top 15, colored by Big-4 flag
3. **Top Divisions** — horizontal bar chart, top 15, colored by department
4. **Spend by Category** — stacked bar by year × expense category
5. **Big-4 Share Over Time** — stacked bar showing Big-4 vs Other per year
6. **Contract Size Buckets** — count of contracts per size bucket
7. **Anomaly Review** — text table of the 25 largest single contracts

**Dashboard:**

* **Overview Dashboard** — 2x2 grid combining Yearly Spend, Top Vendors,
  Top Divisions, and Big-4 Share Over Time, sized for 1200×800px.

## Customization tips

* **Filter by year on the dashboard** — drag `Year` from the data pane to
  the Filters shelf of any worksheet, then right-click the filter and
  choose *Apply to Worksheets → Selected Worksheets...* to make it global.
* **Hook up the parameters** — `Top N Vendors` is defined but not yet
  wired to the *Top Vendors* sheet. Edit the Top filter on that sheet and
  replace `15` with the parameter to make the count user-controlled.
* **Switch the Big-4 share to percent** — on sheet 5, right-click
  `SUM(Expenditure)` on Rows → *Quick Table Calculation → Percent of Total*
  → *Compute Using → Is Big 4*.
* **Currency labels in millions** — drop `Spend ($M)` instead of
  `Expenditure (CAD)` onto Rows/Label for cleaner chart axes.

## If Tableau complains

Hand-authored `.twb` files occasionally hit version-specific quirks. If a
single worksheet won't render:

* The **data source still works** — every other sheet, your custom sheets,
  and the calculated fields will be unaffected.
* Right-click the broken sheet → *Clear Sheet*, then rebuild it from the
  data pane using the recipe from this README.

## Worksheet recipes (for rebuilding or extending)

### Yearly Spend
* Columns: `Year` (Discrete) · Rows: `SUM(Expenditure (CAD))` · Mark: Bar
* Drop `Year` onto Color for a per-year palette.

### Top Vendors
* Rows: `Consultant Name` · Columns: `SUM(Expenditure (CAD))`
* Filter `Consultant Name` → Top → Top 15 by `SUM(Expenditure (CAD))`
* Color: `Is Big 4` · Sort: descending by sum.

### Top Divisions
* Rows: `Division / Board` · Columns: `SUM(Expenditure (CAD))`
* Filter Top 15 · Color: `Department (City/ABC)`.

### Spend by Category
* Columns: `Year` · Rows: `SUM(Expenditure (CAD))` · Mark: Bar
* Color: `Expense Category` (creates stacks).

### Big-4 Share Over Time
* Columns: `Year` · Rows: `SUM(Expenditure (CAD))` · Mark: Bar
* Color: `Is Big 4` (two-stack per year).

### Contract Size Buckets
* Columns: `Contract Size Bucket` · Rows: `COUNTD(Contract Number)`
* Mark: Bar · Color: `Contract Size Bucket`.

### Anomaly Review
* Rows: `Year`, `Consultant Name`, `Expense Category`
* Columns: `SUM(Expenditure (CAD))` · Mark: Text
* Filter the entire view → Top 25 by `SUM(Expenditure)`.

## Bonus ideas (not pre-built)

* **Geographic angle** — join a shapefile or use Tableau's built-in geo
  for vendor head-office locations.
* **Year-over-year growth labels** — add a table calc `(SUM[expenditure] -
  LOOKUP(SUM[expenditure], -1)) / LOOKUP(SUM[expenditure], -1)` formatted
  as percent.
* **Vendor concentration HHI** — define `[expenditure] / WINDOW_SUM([expenditure])
  ^ 2` and aggregate as a measure per year.
