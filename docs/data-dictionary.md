# Data dictionary and calculations

| File or field | Grain and meaning | Control |
|---|---|---|
| products.csv | One row per SKU; product and category | Unique non-empty SKU |
| transactions.csv | One row per sale or return line | Unique line_id, known SKU, valid ISO date |
| receipt_id | One receipt within one store, date and transaction kind | Cross-store/date/kind reuse rejected |
| quantity | Positive integer units on the line | Sign comes from SALE or RETURN |
| unit_price_pence | Price per unit, integer GBP pence | Non-negative |
| discount_pence | Discount per unit, integer pence | Between zero and unit price |
| unit_cost_pence | Acquisition cost per unit | Non-negative |
| original_line_id | Return's originating sale | Match store, SKU and unit values; cumulative refunds cannot exceed sale |
| resalable | 0 or 1 | Determines whether a returned item's cost is reversed |
| inventory.csv | One store/SKU snapshot at period end | Unique key; complete coverage; pack size positive |

Net revenue = signed quantity × (unit price − per-unit discount).

COGS = sale quantity × unit cost, minus return quantity × unit cost **only for resalable returns**. Damaged returns retain their original cost. Gross profit = net revenue − COGS. Gross margin = gross profit / net revenue; undefined if revenue is zero.

Gross units sold excludes returns. Returned units are reported separately. A sale receipt count is distinct receipt IDs for SALE only. Net revenue per sale receipt includes in-period refunds; it is not a conventional gross basket-value metric.

The complete dataset contains the original sales for all returns. A real periodic feed needs a historical sale lookup for returns from earlier periods.

Average daily demand = gross sale units / inclusive period calendar days (42). Inventory position = on-hand + on-order. Reorder point = average daily demand × lead days + safety units. Target = demand × (lead days + review days) + safety units, rounded up to supplier packs. If position ≤ reorder point, recommendation = max(0, target − position), rounded up to supplier packs; otherwise zero. Default review period is 7 days. Coverage = on-hand / daily demand; zero demand yields no numeric coverage rather than division by zero.

All stock values and timings are fictional. On-order quantities are assumed to arrive within the relevant planning horizon; no purchase order dates or supplier reliability are available.
