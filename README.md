# DukaanPulse

DukaanPulse is a data engineering project that turns the scattered records of a small retail shop into clean, checked data stored in a star-schema database, with a dashboard on top.

A small shop usually keeps sales, UPI/card/cash payments, supplier purchases and credit (udhaar) records in different notebooks, apps and spreadsheets. DukaanPulse brings these sources into one ETL pipeline, checks their quality, and shows revenue, profit, stock risk and pending credit in one place.

> **Data note:** all data in this repository is synthetic (made up for learning). It contains no real customer, payment or business information.

## What it does

- Reads 8 CSV source files (sales, payments, purchases, credit, products, customers, suppliers, festivals)
- Validates and cleans the data, and writes a data quality report
- Builds dimension and fact tables (star schema) with Pandas
- Loads the tables into SQLite by default, or PostgreSQL if configured
- Calculates gross profit, estimated stock, daily sales-vs-payment reconciliation, outstanding credit and festival demand change
- Shows the results in a Streamlit dashboard
- Includes unit tests written with pytest

## Pipeline

```text
data/raw/*.csv
      |
      v
 load_raw()          read the 8 source files
      |
      v
 clean_data()        validate, remove duplicates, fix types  --> data/processed/data_quality_report.csv
      |
      v
 build_warehouse()   dimensions, facts, inventory, reconciliation, festival demand
      |
      v
 load_database()     SQLite (default) or PostgreSQL
      |
      +--> SQL queries (sql/analytics.sql)
      +--> Streamlit dashboard (dashboard/app.py)
```

## Tech stack

Python, Pandas, NumPy, SQL, SQLAlchemy, SQLite, PostgreSQL (optional), Streamlit, pytest, Docker Compose (PostgreSQL only).
An example Apache Airflow DAG is included in `airflow/dags/`. It has not been run yet.

## Data used

The included data covers 1 January 2026 to 30 September 2026:

| File | Rows | Contents |
|------|------|----------|
| `sales.csv` | 10,333 | Retail sales (cash, UPI, card, credit) |
| `upi_payments.csv` | 7,652 | Payment transactions for non-credit sales |
| `purchases.csv` | 315 | Supplier purchases |
| `credit.csv` | 2,656 | Udhaar (credit) records |
| `products.csv` | 24 | Product master |
| `customers.csv` | 100 | Customer master |
| `suppliers.csv` | 4 | Supplier master |
| `festivals.csv` | 4 | Festival dates |

## Data quality checks

For each dataset the pipeline:

- Drops rows with a missing ID or an invalid date
- Drops rows with a quantity or amount that is zero or negative
- Removes duplicate IDs (for example, duplicate `sale_id`)
- Fills a missing purchase `unit_cost` from the product's cost price

It then writes one summary row per dataset to `data/processed/data_quality_report.csv`, with the input rows, output rows, duplicates removed, invalid rows, missing values and a `PASS`/`WARN` status.

On the included data, the pipeline removes 25 duplicate sales and fixes 1 purchase with a missing unit cost.

## Business calculations

- **Gross profit** = revenue − cost of goods sold (product cost price × quantity)
- **Stock estimate** = units purchased − units sold, and days remaining = stock ÷ average daily sales. Items are marked `CRITICAL` (3 days or less), `LOW` (7 days or less), `REORDER` (at or below reorder level) or `HEALTHY`.
- **Payment reconciliation:** for each day, non-credit sales are compared with payments received. A difference of ₹1 or less is `RECONCILED`; otherwise `MISMATCH`.
- **Outstanding udhaar** = credit amount − amount paid
- **Festival demand:** units sold in the 7 days before each festival (up to the festival day) compared with the 7 days before that

## Output tables

| Type | Tables |
|------|--------|
| Dimensions | `dim_date`, `dim_product`, `dim_customer`, `dim_supplier` |
| Facts | `fact_sales`, `fact_payments`, `fact_purchases`, `fact_credit` |
| Analysis | `inventory_snapshot`, `payment_reconciliation`, `festival_demand` |

## Project structure

```text
DukaanPulse/
├── airflow/dags/dukaanpulse_daily.py   example Airflow DAG (not tested)
├── dashboard/app.py                    Streamlit dashboard
├── data/
│   ├── raw/                            source CSV files
│   └── processed/                      quality report and CSV outputs
├── docs/                               data dictionary and walkthrough
├── sql/
│   ├── analytics.sql                   example queries (SQLite syntax)
│   └── schema_postgres.sql             reference PostgreSQL schema
├── src/
│   ├── config.py                       paths and database URL
│   ├── db.py                           database engine
│   ├── pipeline.py                     extract, clean, transform, load
│   └── quality.py                      quality report helpers
├── tests/                              pytest tests
├── docker-compose.yml                  PostgreSQL container
├── requirements.txt
└── run_project.bat                     one-click run on Windows
```

## Getting started

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the pipeline

```bash
python -m src.pipeline
```

This rebuilds the SQLite database at `data/dukaanpulse.db` and writes the CSV reports to `data/processed/`.

### 4. Open the dashboard

```bash
streamlit run dashboard/app.py
```

### 5. Run the tests

```bash
pytest -q
```

On Windows, `run_project.bat` runs steps 2 to 4 in one go.

## Using PostgreSQL instead of SQLite

1. Start PostgreSQL:

   ```bash
   docker compose up -d
   ```

2. Copy `.env.example` to `.env` and set:

   ```env
   DATABASE_URL=postgresql+psycopg2://dukaan:dukaan@localhost:5432/dukaanpulse
   ```

3. Run the pipeline and dashboard as above.

The queries in `sql/analytics.sql` use SQLite date functions. The weekly revenue query needs small changes to run on PostgreSQL.

## Limitations

- The pipeline rebuilds all tables on every run. It does not load only new records.
- Rows that fail validation are counted in the quality report but are not saved separately.
- The dashboard's udhaar aging uses a fixed date (30 September 2026, the last date in the data).
- Durga Puja (19 October 2026) falls after the last date in the data, so it has no sales to compare.
- The Airflow DAG is only an example and has not been run.
- The data is synthetic, so the numbers do not describe a real shop.

## Future improvements

- Incremental loads, so each run processes only new records
- Save rejected rows to a separate table for review
- Run the pipeline on a schedule with Airflow and Docker
- Add stronger data quality checks, for example with Great Expectations
- Add a dashboard screenshot to this README

## Author

Anwesha Daw, B.Tech Computer Science and Engineering student
[LinkedIn](https://www.linkedin.com/in/anwesha-daw)

## License

This project is released under the MIT License. See `LICENSE` for details.
