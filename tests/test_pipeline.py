from pathlib import Path
import pandas as pd
from src.pipeline import load_raw, clean_data, build_warehouse

def test_raw_files_exist():
    root = Path(__file__).resolve().parents[1]
    for name in ["products.csv","customers.csv","sales.csv","upi_payments.csv",
                 "purchases.csv","credit.csv","festivals.csv","suppliers.csv"]:
        assert (root / "data" / "raw" / name).exists()

def test_clean_sales_have_unique_ids():
    raw = load_raw()
    clean, _ = clean_data(raw)
    assert clean["sales"]["sale_id"].is_unique
    assert (clean["sales"]["quantity"] > 0).all()

def test_warehouse_contains_core_tables():
    raw = load_raw()
    clean, _ = clean_data(raw)
    wh = build_warehouse(clean)
    for name in ["dim_product","dim_customer","dim_date","fact_sales",
                 "fact_payments","fact_purchases","fact_credit","inventory_snapshot"]:
        assert name in wh
        assert len(wh[name]) > 0

def test_profit_is_revenue_minus_cogs():
    raw = load_raw()
    clean, _ = clean_data(raw)
    wh = build_warehouse(clean)
    sales = wh["fact_sales"]
    assert ((sales["gross_profit"] - (sales["revenue"] - sales["cogs"])).abs() < 0.001).all()
