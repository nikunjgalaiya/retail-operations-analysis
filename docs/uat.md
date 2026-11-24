# UAT and traceability

These are executable acceptance checks for an independent scenario. They are not stakeholder sign-off.

Run `python -m unittest discover -s tests -v` from the repository root.

| Requirement | Checks in tests/test_retail.py | Expected outcome |
|---|---|---|
| R1 | Independent revenue/COGS reconciliation | Exact integer-pence equality |
| R2 | Unknown/mismatched/excess/early return, duplicate IDs, invalid price/date/SKU | Import rejected |
| R3 | On-order stock, inclusive reorder boundary, zero demand | Correct exception queue and safe zero-demand behaviour |
| R4 | Whole-pack replenishment | Suggested quantity divisible by supplier pack |
| R5–R6 | Period/grain and report generation | Three stores, 42 days, repeatable report outputs |

14 automated checks pass on 23 November 2026. Manual UI review and business-owner sign-off are separate activities. Do not infer browser accessibility compliance or commercial impact from unit tests.

## Manager walkthrough

1. Run the report and open reports/dashboard.html.
2. Compare all stores, then choose one store.
3. Inspect weekly net revenue and explain the effect of refunds.
4. Show only items requiring replenishment review.
5. Select one item and independently reproduce its inventory position, reorder point and whole-pack order.
6. Discuss seasonality and the missing supplier arrival dates before recommending live adoption.
