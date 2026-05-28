# Power BI — recreate the dashboard in ~10 minutes

Power BI files (`.pbix`) cannot reliably be hand-generated outside Power BI
Desktop, so this folder ships the data and a recipe instead. The whole flow
takes about ten minutes.

## 1. Connect to the data

1. Open Power BI Desktop -> **Get Data** -> **Text/CSV**.
2. Select `../data/processed/consulting_expenditures.csv`.
3. Click **Transform Data** to open Power Query.

## 2. Set column types in Power Query

In the Power Query editor, set:

| Column | Type |
|---|---|
| `year` | Whole Number |
| `expenditure` | Decimal Number |
| `contract_date` | Date |
| everything else | Text |

Then **Close & Apply**.

## 3. Build the report pages

### Page 1 — Overview

* **Card visual:** Total spend = `SUM(consulting_expenditures[expenditure])`.
  Format as `$#,0,.0M`.
* **Card visual:** Contract count = `COUNTROWS(consulting_expenditures)`.
* **Card visual:** Vendor count =
  `DISTINCTCOUNT(consulting_expenditures[consultant_name])`.
* **Clustered column chart:** Axis = `year`, Value =
  `SUM(expenditure)`. Title: "Toronto consulting spend by year, 2017-2024".

### Page 2 — Vendors

* **Bar chart (clustered):** Axis = `consultant_name`, Value =
  `SUM(expenditure)`. In the visual's filter pane apply Top N filter:
  Top 15 by `SUM(expenditure)`. Sort descending.
* **Table:** `consultant_name`, `SUM(expenditure)`, `COUNT(contract_number)`.

### Page 3 — Divisions

* **Treemap:** Group = `division_board`, Values = `SUM(expenditure)`.
* **Line chart:** Axis = `year`, Legend =
  Top-6 divisions (use a measure with TOPN or a manual filter), Value =
  `SUM(expenditure)`.

### Page 4 — Anomaly review

* **Get Data -> Text/CSV** again, this time selecting
  `../data/processed/anomalies.csv`.
* Drop a **Table** visual with `year`, `consultant_name`, `division_board`,
  `expense_category`, `expenditure`, `anomaly_score`.
* Sort by `anomaly_score` descending.

## 4. A few useful DAX measures

```dax
Total Spend       = SUM(consulting_expenditures[expenditure])
Contracts         = COUNTROWS(consulting_expenditures)
Unique Vendors    = DISTINCTCOUNT(consulting_expenditures[consultant_name])
Median Contract   = MEDIAN(consulting_expenditures[expenditure])

Big4 Share % =
DIVIDE(
    CALCULATE(
        [Total Spend],
        consulting_expenditures[consultant_name]
            IN { "Deloitte LLP", "Ernst & Young LLP", "KPMG LLP" }
    ),
    [Total Spend]
)
```

## 5. Slicers and cross-filtering

Add a **Slicer** for `year` and another for `budget_type` on the
overview page. Power BI applies them across all visuals on the page
automatically.

## Expected numbers (sanity check)

If the import worked, the overview cards should show approximately:

* Total spend: **$350.2M**
* Contracts: **3,678**
* Unique vendors: **960**
* 2017 column: ~$21.4M, 2024 column: ~$60.2M
