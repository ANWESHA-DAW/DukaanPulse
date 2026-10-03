import streamlit as st
import pandas as pd
from sqlalchemy import text
from src.db import get_engine

st.set_page_config(page_title="DukaanPulse", page_icon="🛒", layout="wide")
st.title("🛒 DukaanPulse")
st.caption("Retail Data Engineering & Analytics Dashboard")

engine = get_engine()

def q(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

try:
    sales = q("SELECT * FROM fact_sales")
    inv = q("SELECT * FROM inventory_snapshot")
    credit = q("SELECT * FROM fact_credit")
    recon = q("SELECT * FROM payment_reconciliation")
    festival = q("SELECT * FROM festival_demand")
except Exception as e:
    st.error("Database not found. Run `python -m src.pipeline` first.")
    st.exception(e)
    st.stop()

sales["sale_date"] = pd.to_datetime(sales["sale_date"])
total_revenue = sales["revenue"].sum()
total_profit = sales["gross_profit"].sum()
outstanding = credit["outstanding_amount"].sum()
low_stock = int((inv["stock_status"].isin(["CRITICAL","LOW","REORDER"])).sum())

c1,c2,c3,c4 = st.columns(4)
c1.metric("Revenue", f"₹{total_revenue:,.0f}")
c2.metric("Gross Profit", f"₹{total_profit:,.0f}")
c3.metric("Outstanding Udhaar", f"₹{outstanding:,.0f}")
c4.metric("Low/Reorder Items", low_stock)

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("📈 Daily Revenue")
    daily = sales.groupby("sale_date", as_index=False)["revenue"].sum()
    st.line_chart(daily.set_index("sale_date"))

with right:
    st.subheader("🏆 Top Products")
    top = sales.groupby("product_id", as_index=False).agg(
        units=("quantity","sum"), revenue=("revenue","sum")
    ).sort_values("revenue", ascending=False).head(10)
    st.dataframe(top, use_container_width=True, hide_index=True)

st.subheader("📦 Inventory Risk")
st.dataframe(
    inv[["product_id","product_name","units_purchased","units_sold","current_stock_estimate",
         "avg_daily_sales","estimated_days_remaining","stock_status"]]
    .sort_values("estimated_days_remaining")
    .head(15),
    use_container_width=True, hide_index=True
)

st.subheader("💰 Payment Reconciliation")
st.dataframe(recon.sort_values("difference", key=lambda s: s.abs(), ascending=False).head(15),
             use_container_width=True, hide_index=True)

st.subheader("👥 Udhaar Aging")
credit["credit_date"] = pd.to_datetime(credit["credit_date"])
credit["due_date"] = pd.to_datetime(credit["due_date"])
today = pd.Timestamp("2026-09-30")
credit["days_outstanding"] = (today - credit["credit_date"]).dt.days.clip(lower=0)
aging = credit[credit["outstanding_amount"] > 0].groupby("customer_id", as_index=False).agg(
    outstanding=("outstanding_amount","sum"),
    max_days=("days_outstanding","max")
).sort_values("outstanding", ascending=False)
st.dataframe(aging.head(15), use_container_width=True, hide_index=True)

st.subheader("🎉 Festival Demand")
festival_view = festival.merge(
    sales.groupby("product_id", as_index=False)["revenue"].sum(),
    on="product_id", how="left"
)
st.dataframe(
    festival_view.sort_values("demand_change_pct", ascending=False).head(20),
    use_container_width=True, hide_index=True
)

st.caption("Synthetic portfolio data only — no real customer/payment information.")
