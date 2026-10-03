-- Useful interview/demo queries for DukaanPulse

-- 1. Top 10 products by revenue
SELECT product_id, SUM(revenue) AS revenue
FROM fact_sales
GROUP BY product_id
ORDER BY revenue DESC
LIMIT 10;

-- 2. Weekly revenue and gross profit
SELECT
    strftime('%Y-%W', sale_date) AS year_week,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(gross_profit), 2) AS gross_profit
FROM fact_sales
GROUP BY strftime('%Y-%W', sale_date)
ORDER BY year_week;

-- 3. Outstanding udhaar
SELECT customer_id,
       ROUND(SUM(outstanding_amount),2) AS outstanding
FROM fact_credit
WHERE outstanding_amount > 0
GROUP BY customer_id
ORDER BY outstanding DESC;

-- 4. Inventory items that may run out within 7 days
SELECT product_id, product_name, current_stock_estimate,
       estimated_days_remaining
FROM inventory_snapshot
WHERE estimated_days_remaining <= 7
ORDER BY estimated_days_remaining;

-- 5. Reconciliation mismatches
SELECT *
FROM payment_reconciliation
WHERE status = 'MISMATCH'
ORDER BY ABS(difference) DESC;
