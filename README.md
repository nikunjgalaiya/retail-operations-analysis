# Retail Operations Analysis

A decision-focused business analysis case study: reconcile sales and refunds, compare store performance, and prioritise stock replenishment with transparent rules.

**Independent portfolio scenario. All transactions, products, stores and results are synthetic. No employer data or realised commercial savings are claimed.**

## Run in two minutes

Requires Python 3.11+; no external dependencies.

```bash
python generate_demo_data.py
python -m retail_ops
python -m unittest discover -s tests -v
```

Open `reports/dashboard.html` in your browser. The dashboard is self-contained, works offline, supports store selection and a reorder-only filter. Downloadable output is in `reports/stores.csv`, `weekly.csv`, `inventory.csv` and `metrics.json`.

## Business question

Which stores need investigation, and which stock positions should be reviewed first? A report must explain refunds and inventory already on order rather than simply rank gross sales or low on-hand stock.

## Reproducible scenario

- 1,850 transaction lines, 3 fictional stores, 8 products, 42 calendar days.
- Seed 724; period 7 September–18 October 2026, inclusive.
- £41,439 net revenue, £24,002.60 gross profit, 56 units returned across the synthetic period.
- Riverside has the largest net revenue (£14,614); investigate the underlying product mix before recommending an intervention. This is descriptive evidence, not proof of causation.
- 14 automated tests cover monetary reconciliation, returns, invalid input, boundaries and stock policy.

## Evidence chain

[Business brief and requirements](docs/business-analysis.md) · [Data dictionary and metric definitions](docs/data-dictionary.md) · [UAT and traceability](docs/uat.md) · [SQL queries](sql/)

CSV → validated import → SQLite facts → SQL aggregation → replenishment policy → offline dashboard.

The project demonstrates requirements documentation, acceptance criteria, SQL, KPI definitions, data-quality controls, prioritisation and test traceability. It is a prototype for discussing decisions with a business stakeholder, not an automated procurement system.

## Limitations

Constant historical daily demand is a simple planning assumption; seasonality, lost sales, lead-time variability, supplier capacity and working-capital constraints are out of scope. Gross margin excludes wages, rent and other operating expenses. Currency values assume GBP excluding VAT. Review recommendations with a buyer before placing any order. See the data dictionary for return accounting and edge cases.

## Online project

[Portfolio and interactive demonstrations](https://nikunjgalaiya.github.io/) · [Source repository](https://github.com/nikunjgalaiya/retail-operations-analysis)
