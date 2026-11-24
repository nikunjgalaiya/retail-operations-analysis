import copy
import unittest
from retail_ops.core import ROOT, build_database, read_csv, report, validated_rows

class RetailTests(unittest.TestCase):
    def setUp(self):
        self.products=read_csv(ROOT/"data/products.csv")
        self.rows=read_csv(ROOT/"data/transactions.csv")

    def test_period_and_grain(self):
        with build_database() as c:
            result=report(c)
            self.assertEqual(result["period_days"],42)
            self.assertEqual(len(result["stores"]),3)
            self.assertEqual(len(result["inventory"]),24)
            self.assertEqual(len(result["weekly"]),18)

    def test_independent_money_reconciliation(self):
        # Independent Python calculation checks both SQLite summaries.
        expected=sum((1 if r["kind"]=="SALE" else -1)*int(r["quantity"])*
                     (int(r["unit_price_pence"])-int(r["discount_pence"])) for r in self.rows)
        cost=sum(int(r["quantity"])*int(r["unit_cost_pence"])*
                 (1 if r["kind"]=="SALE" else -int(r["resalable"])) for r in self.rows)
        with build_database() as c:
            result=report(c)
            self.assertEqual(sum(x["net_pence"] for x in result["stores"]),expected)
            self.assertEqual(sum(x["net_pence"] for x in result["weekly"]),expected)
            self.assertEqual(sum(x["gross_profit_pence"] for x in result["stores"]),expected-cost)

    def test_duplicate_line_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            validated_rows(self.rows+[self.rows[0]],self.products)

    def test_unknown_sku_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]["sku"]="MISSING"
        with self.assertRaisesRegex(ValueError,"SKU"):validated_rows(rows,self.products)

    def test_bad_date_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]["date"]="2026-02-30"
        with self.assertRaisesRegex(ValueError,"date"):validated_rows(rows,self.products)

    def test_excess_discount_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]["discount_pence"]="999999"
        with self.assertRaisesRegex(ValueError,"discount"):validated_rows(rows,self.products)

    def test_missing_return_reference_rejected(self):
        rows=copy.deepcopy(self.rows);r=next(r for r in rows if r["kind"]=="RETURN");r["original_line_id"]="UNKNOWN"
        with self.assertRaisesRegex(ValueError,"reference"):validated_rows(rows,self.products)

    def test_excess_return_rejected(self):
        rows=copy.deepcopy(self.rows);r=next(r for r in rows if r["kind"]=="RETURN");r["quantity"]="99999"
        with self.assertRaisesRegex(ValueError,"exceed"):validated_rows(rows,self.products)

    def test_return_values_must_match_sale(self):
        rows=copy.deepcopy(self.rows);r=next(r for r in rows if r["kind"]=="RETURN");r["unit_cost_pence"]="1"
        with self.assertRaisesRegex(ValueError,"match"):validated_rows(rows,self.products)

    def test_on_order_prevents_unnecessary_reorder(self):
        with build_database() as c:
            c.execute("UPDATE inventory SET on_order=100000 WHERE store='Central'")
            self.assertTrue(all(x["reorder_units"]==0 for x in report(c)["inventory"] if x["store"]=="Central"))

    def test_reorder_boundary_is_inclusive(self):
        with build_database() as c:
            c.execute("UPDATE inventory SET on_hand=6,on_order=0,lead_days=0,safety_units=6")
            self.assertTrue(all(x["reorder_units"]>0 for x in report(c)["inventory"]))

    def test_zero_demand_has_no_infinite_coverage(self):
        with build_database() as c:
            c.execute("DELETE FROM transactions WHERE sku='B01'")
            for x in report(c)["inventory"]:
                if x["sku"]=="B01":self.assertIsNone(x["cover_days"])

    def test_invalid_review_period(self):
        with build_database() as c:
            with self.assertRaises(ValueError):report(c,0)

    def test_suggested_orders_are_whole_supplier_packs(self):
        with build_database() as c:
            for row in report(c)["inventory"]:
                self.assertEqual(row["reorder_units"] % row["pack_size"],0)

if __name__=="__main__":unittest.main()
