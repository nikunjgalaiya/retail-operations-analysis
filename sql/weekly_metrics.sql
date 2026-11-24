-- Monday-based weeks, including complete Monday-to-Sunday source periods.
SELECT date(date,'-'||((CAST(strftime('%w',date) AS INTEGER)+6)%7)||' days') week_start,
 store,SUM(net_pence) net_pence,
 SUM(net_pence)-SUM(cogs_pence) gross_profit_pence
FROM facts GROUP BY week_start,store ORDER BY week_start,store;
