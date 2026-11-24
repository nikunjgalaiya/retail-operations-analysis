SELECT store,
 COUNT(DISTINCT CASE WHEN kind='SALE' THEN receipt_id END) sale_receipts,
 SUM(CASE WHEN kind='SALE' THEN quantity ELSE 0 END) gross_units,
 SUM(CASE WHEN kind='RETURN' THEN quantity ELSE 0 END) returned_units,
 SUM(net_pence) net_pence,
 SUM(cogs_pence) cogs_pence,
 SUM(net_pence)-SUM(cogs_pence) gross_profit_pence,
 ROUND(100.0*(SUM(net_pence)-SUM(cogs_pence))/NULLIF(SUM(net_pence),0),2) margin_pct,
 ROUND(1.0*SUM(net_pence)/NULLIF(COUNT(DISTINCT CASE WHEN kind='SALE' THEN receipt_id END),0),2) net_per_sale_receipt_pence
FROM facts GROUP BY store ORDER BY net_pence DESC;
