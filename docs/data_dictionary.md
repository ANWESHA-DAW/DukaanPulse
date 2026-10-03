# Data Dictionary

| Dataset | Important columns | Purpose |
|---|---|---|
| products.csv | product_id, category, cost_price, selling_price | Product master |
| customers.csv | customer_id, customer_type | Customer master |
| sales.csv | sale_id, sale_date, product_id, quantity, sales_amount | Retail sales |
| upi_payments.csv | transaction_id, sale_id, amount, status | Digital payments |
| purchases.csv | purchase_id, supplier_id, product_id, quantity, unit_cost | Supplier purchases |
| credit.csv | credit_id, customer_id, credit_amount, amount_paid, due_date | Udhaar |
| suppliers.csv | supplier_id, supplier_name | Supplier master |
| festivals.csv | festival_name, start_date, end_date | Festival windows |
