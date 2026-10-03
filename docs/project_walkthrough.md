# DukaanPulse Project Walkthrough

## 1. Problem
Small retailers often keep sales, payments, purchases and credit records in different places. Manual consolidation causes duplicate, missing and inconsistent numbers.

## 2. Solution
DukaanPulse creates a repeatable pipeline that ingests source files, validates them, cleans them, transforms them into analytical tables and exposes business metrics through a dashboard.

## 3. Data Engineering concepts demonstrated

### ETL
Extract → Validate → Transform → Load.

### Data Quality
Duplicates, missing values, invalid dates/amounts and payment mismatches are detected.

### Data Modeling
Dimension tables describe entities; fact tables contain business events.

### Reconciliation
Sales are compared with recorded non-credit payments by day.

### Inventory
Purchases minus sales are used to estimate stock; average daily sales are used to estimate days remaining.

### Udhaar
Outstanding credit is calculated as credit amount minus payments made.

### Festival demand
A 7-day pre-festival window is compared with an earlier 7-day baseline.

## 4. How to explain the project in an interview

"I built DukaanPulse as an end-to-end retail data engineering pipeline. I generated realistic source data for sales, UPI, purchases and credit, then used Python and Pandas for ingestion, validation and transformation. I loaded analytical tables into a relational database and created metrics for revenue, profit, inventory risk, credit aging, payment reconciliation and festival demand. I also designed the project so the ETL can be orchestrated by Airflow and later moved to cloud storage and Spark for scale."

## 5. Scalability plan

Current:
CSV → Python/Pandas → PostgreSQL → Streamlit

Production-style extension:
API/DB → S3 Data Lake → Airflow → PySpark → Warehouse → BI

## 6. Security note

Only synthetic data is included. Never upload real customer names, phone numbers, UPI references or financial records to a public repository.
