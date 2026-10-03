import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import text
from src.config import RAW_DIR, PROCESSED_DIR
from src.db import get_engine
from src.quality import quality_result, write_quality_report

def load_raw():
    return {
        "products": pd.read_csv(RAW_DIR / "products.csv"),
        "customers": pd.read_csv(RAW_DIR / "customers.csv"),
        "suppliers": pd.read_csv(RAW_DIR / "suppliers.csv"),
        "sales": pd.read_csv(RAW_DIR / "sales.csv"),
        "payments": pd.read_csv(RAW_DIR / "upi_payments.csv"),
        "purchases": pd.read_csv(RAW_DIR / "purchases.csv"),
        "credit": pd.read_csv(RAW_DIR / "credit.csv"),
        "festivals": pd.read_csv(RAW_DIR / "festivals.csv"),
    }

def clean_data(raw):
    results = []

    products = raw["products"].copy()
    products["cost_price"] = pd.to_numeric(products["cost_price"], errors="coerce")
    products["selling_price"] = pd.to_numeric(products["selling_price"], errors="coerce")
    products = products.drop_duplicates("product_id")
    results.append(quality_result("products", len(raw["products"]), len(products), len(raw["products"])-len(products), 0, int(products[["product_id","product_name"]].isna().any(axis=1).sum())))

    customers = raw["customers"].copy().drop_duplicates("customer_id")
    results.append(quality_result("customers", len(raw["customers"]), len(customers), len(raw["customers"])-len(customers), 0, int(customers[["customer_id","customer_name"]].isna().any(axis=1).sum())))

    suppliers = raw["suppliers"].copy().drop_duplicates("supplier_id")
    results.append(quality_result("suppliers", len(raw["suppliers"]), len(suppliers), len(raw["suppliers"])-len(suppliers), 0, int(suppliers[["supplier_id","supplier_name"]].isna().any(axis=1).sum())))

    sales = raw["sales"].copy()
    input_n = len(sales)
    sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce")
    sales["quantity"] = pd.to_numeric(sales["quantity"], errors="coerce")
    sales["discount_per_unit"] = pd.to_numeric(sales["discount_per_unit"], errors="coerce").fillna(0)
    sales["sales_amount"] = pd.to_numeric(sales["sales_amount"], errors="coerce")
    invalid_mask = sales["sale_id"].isna() | sales["product_id"].isna() | sales["sale_date"].isna() | (sales["quantity"] <= 0) | (sales["sales_amount"] <= 0)
    invalid_n = int(invalid_mask.sum())
    sales = sales.loc[~invalid_mask].copy()
    before = len(sales)
    sales = sales.drop_duplicates("sale_id")
    dup_n = before - len(sales)
    sales["sale_date"] = sales["sale_date"].dt.date
    results.append(quality_result("sales", input_n, len(sales), dup_n, invalid_n, 0))

    payments = raw["payments"].copy()
    input_n = len(payments)
    payments["transaction_date"] = pd.to_datetime(payments["transaction_date"], errors="coerce")
    payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce")
    invalid_mask = payments["transaction_id"].isna() | payments["sale_id"].isna() | payments["transaction_date"].isna() | (payments["amount"] <= 0)
    invalid_n = int(invalid_mask.sum())
    payments = payments.loc[~invalid_mask].drop_duplicates("transaction_id").copy()
    payments["transaction_date"] = payments["transaction_date"].dt.date
    results.append(quality_result("payments", input_n, len(payments), input_n-invalid_n-len(payments), invalid_n, 0))

    purchases = raw["purchases"].copy()
    input_n = len(purchases)
    purchases["purchase_date"] = pd.to_datetime(purchases["purchase_date"], errors="coerce")
    purchases["quantity"] = pd.to_numeric(purchases["quantity"], errors="coerce")
    purchases["unit_cost"] = pd.to_numeric(purchases["unit_cost"], errors="coerce")
    purchases["purchase_amount"] = pd.to_numeric(purchases["purchase_amount"], errors="coerce")
    invalid_mask = purchases["purchase_id"].isna() | purchases["product_id"].isna() | purchases["purchase_date"].isna() | (purchases["quantity"] <= 0)
    invalid_n = int(invalid_mask.sum())
    purchases = purchases.loc[~invalid_mask].drop_duplicates("purchase_id").copy()
    missing_cost = int(purchases["unit_cost"].isna().sum())
    # Fill missing supplier cost from product master cost price
    cost_map = products.set_index("product_id")["cost_price"]
    purchases["unit_cost"] = purchases["unit_cost"].fillna(purchases["product_id"].map(cost_map))
    purchases["purchase_amount"] = purchases["quantity"] * purchases["unit_cost"]
    purchases["purchase_date"] = purchases["purchase_date"].dt.date
    results.append(quality_result("purchases", input_n, len(purchases), input_n-invalid_n-len(purchases), invalid_n, missing_cost))

    credit = raw["credit"].copy()
    input_n = len(credit)
    credit["credit_date"] = pd.to_datetime(credit["credit_date"], errors="coerce")
    credit["due_date"] = pd.to_datetime(credit["due_date"], errors="coerce")
    credit["credit_amount"] = pd.to_numeric(credit["credit_amount"], errors="coerce")
    credit["amount_paid"] = pd.to_numeric(credit["amount_paid"], errors="coerce").fillna(0)
    invalid_mask = credit["credit_id"].isna() | credit["customer_id"].isna() | credit["credit_date"].isna() | (credit["credit_amount"] <= 0)
    invalid_n = int(invalid_mask.sum())
    credit = credit.loc[~invalid_mask].drop_duplicates("credit_id").copy()
    credit["outstanding_amount"] = (credit["credit_amount"] - credit["amount_paid"]).clip(lower=0)
    credit["credit_date"] = credit["credit_date"].dt.date
    credit["due_date"] = credit["due_date"].dt.date
    results.append(quality_result("credit", input_n, len(credit), input_n-invalid_n-len(credit), invalid_n, 0))

    festivals = raw["festivals"].copy()
    festivals["start_date"] = pd.to_datetime(festivals["start_date"], errors="coerce").dt.date
    festivals["end_date"] = pd.to_datetime(festivals["end_date"], errors="coerce").dt.date

    return {
        "products": products, "customers": customers, "suppliers": suppliers,
        "sales": sales, "payments": payments, "purchases": purchases,
        "credit": credit, "festivals": festivals
    }, results

def build_warehouse(clean):
    products = clean["products"].copy()
    customers = clean["customers"].copy()
    suppliers = clean["suppliers"].copy()
    sales = clean["sales"].copy()
    payments = clean["payments"].copy()
    purchases = clean["purchases"].copy()
    credit = clean["credit"].copy()
    festivals = clean["festivals"].copy()

    # Date dimension
    all_dates = pd.concat([
        sales["sale_date"].astype(str),
        payments["transaction_date"].astype(str),
        purchases["purchase_date"].astype(str),
        credit["credit_date"].astype(str)
    ])
    dmin = pd.to_datetime(all_dates.min())
    dmax = pd.to_datetime(all_dates.max())
    date_range = pd.date_range(dmin, dmax, freq="D")
    dim_date = pd.DataFrame({
        "date_id": date_range.strftime("%Y%m%d").astype(int),
        "full_date": date_range.date,
        "year": date_range.year,
        "month": date_range.month,
        "month_name": date_range.strftime("%B"),
        "week": date_range.isocalendar().week.astype(int),
        "day": date_range.day,
        "day_name": date_range.strftime("%A"),
        "is_weekend": date_range.weekday >= 5
    })

    # Sales fact with product cost and profit
    sales = sales.merge(products[["product_id","cost_price"]], on="product_id", how="left")
    sales["revenue"] = sales["sales_amount"]
    sales["cogs"] = sales["cost_price"] * sales["quantity"]
    sales["gross_profit"] = sales["revenue"] - sales["cogs"]
    sales["date_id"] = pd.to_datetime(sales["sale_date"]).dt.strftime("%Y%m%d").astype(int)

    payments["date_id"] = pd.to_datetime(payments["transaction_date"]).dt.strftime("%Y%m%d").astype(int)
    purchases["date_id"] = pd.to_datetime(purchases["purchase_date"]).dt.strftime("%Y%m%d").astype(int)
    credit["date_id"] = pd.to_datetime(credit["credit_date"]).dt.strftime("%Y%m%d").astype(int)

    # Inventory snapshot
    sold = sales.groupby("product_id", as_index=False)["quantity"].sum().rename(columns={"quantity":"units_sold"})
    bought = purchases.groupby("product_id", as_index=False)["quantity"].sum().rename(columns={"quantity":"units_purchased"})
    inv = products[["product_id","product_name","category","reorder_level"]].merge(bought, on="product_id", how="left").merge(sold, on="product_id", how="left").fillna(0)
    inv["current_stock_estimate"] = (inv["units_purchased"] - inv["units_sold"]).clip(lower=0)
    sales_days = max((pd.to_datetime(sales["sale_date"]).max() - pd.to_datetime(sales["sale_date"]).min()).days + 1, 1)
    inv["avg_daily_sales"] = inv["units_sold"] / sales_days
    inv["estimated_days_remaining"] = np.where(inv["avg_daily_sales"] > 0, inv["current_stock_estimate"] / inv["avg_daily_sales"], 9999)
    inv["stock_status"] = np.select(
        [inv["estimated_days_remaining"] <= 3, inv["estimated_days_remaining"] <= 7, inv["current_stock_estimate"] <= inv["reorder_level"]],
        ["CRITICAL","LOW","REORDER"],
        default="HEALTHY"
    )

    # Sales/payment reconciliation
    non_credit = sales[sales["payment_method"] != "CREDIT"].groupby("sale_date", as_index=False)["revenue"].sum().rename(columns={"revenue":"sales_total"})
    pay = payments.groupby("transaction_date", as_index=False)["amount"].sum().rename(columns={"amount":"payment_total"})
    recon = non_credit.merge(pay, left_on="sale_date", right_on="transaction_date", how="outer").fillna(0)
    recon["date"] = recon["sale_date"].where(recon["sale_date"] != 0, recon["transaction_date"])
    recon["difference"] = recon["sales_total"] - recon["payment_total"]
    recon["status"] = np.where(recon["difference"].abs() <= 1.0, "RECONCILED", "MISMATCH")
    recon = recon[["date","sales_total","payment_total","difference","status"]]

    # Festival demand analysis: 7-day pre-festival window vs 7-day baseline before it
    festival_rows = []
    sale_dates = pd.to_datetime(sales["sale_date"])
    for f in festivals.itertuples(index=False):
        fs = pd.Timestamp(f.start_date)
        before_start = fs - pd.Timedelta(days=14)
        baseline_end = fs - pd.Timedelta(days=8)
        promo_start = fs - pd.Timedelta(days=7)
        promo_end = fs
        base = sales[(sale_dates >= before_start) & (sale_dates <= baseline_end)]
        pre = sales[(sale_dates >= promo_start) & (sale_dates <= promo_end)]
        b = base.groupby("product_id")["quantity"].sum()
        p = pre.groupby("product_id")["quantity"].sum()
        for pid in products.product_id:
            base_qty = float(b.get(pid, 0))
            pre_qty = float(p.get(pid, 0))
            festival_rows.append((f.festival_id, f.festival_name, pid, base_qty, pre_qty,
                                  round(((pre_qty-base_qty)/base_qty*100),2) if base_qty else None))
    festival_demand = pd.DataFrame(festival_rows, columns=["festival_id","festival_name","product_id","baseline_units","festival_window_units","demand_change_pct"])

    return {
        "dim_date": dim_date,
        "dim_product": products,
        "dim_customer": customers,
        "dim_supplier": suppliers,
        "fact_sales": sales,
        "fact_payments": payments,
        "fact_purchases": purchases,
        "fact_credit": credit,
        "inventory_snapshot": inv,
        "payment_reconciliation": recon,
        "festival_demand": festival_demand
    }

def load_database(warehouse):
    engine = get_engine()
    with engine.begin() as conn:
        # Fresh rebuild for reproducibility
        for table in [
            "festival_demand","payment_reconciliation","inventory_snapshot","fact_credit",
            "fact_purchases","fact_payments","fact_sales","dim_supplier","dim_customer",
            "dim_product","dim_date","data_quality_log"
        ]:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
    for name, df in warehouse.items():
        df.to_sql(name, engine, if_exists="replace", index=False)
    return engine

def main():
    PROCESSED_DIR.mkdir(exist_ok=True)
    raw = load_raw()
    clean, results = clean_data(raw)
    warehouse = build_warehouse(clean)
    load_database(warehouse)
    write_quality_report(results, PROCESSED_DIR / "data_quality_report.csv")
    warehouse["payment_reconciliation"].to_csv(PROCESSED_DIR / "payment_reconciliation.csv", index=False)
    warehouse["inventory_snapshot"].to_csv(PROCESSED_DIR / "inventory_snapshot.csv", index=False)
    warehouse["festival_demand"].to_csv(PROCESSED_DIR / "festival_demand.csv", index=False)
    print("DukaanPulse ETL completed successfully.")
    print("Database:", get_engine().url)
    print("Quality report:", PROCESSED_DIR / "data_quality_report.csv")
    print("Tables:", ", ".join(warehouse.keys()))

if __name__ == "__main__":
    main()
