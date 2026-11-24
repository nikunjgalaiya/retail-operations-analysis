"""Validated CSV import and SQLite reporting. All money is stored in pence."""
import csv
import json
import math
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["line_id", "receipt_id", "date", "store", "sku", "kind", "quantity",
          "unit_price_pence", "discount_pence", "unit_cost_pence", "original_line_id",
          "resalable"]


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validated_rows(rows, products):
    """Validate the entire import before changing a database."""
    skus = {p["sku"] for p in products}
    clean, seen, returned = [], {}, {}
    for n, row in enumerate(rows, 2):
        if set(row) != set(FIELDS):
            raise ValueError("Transaction columns do not match the documented schema")
        r = dict(row)
        for k in ["quantity", "unit_price_pence", "discount_pence", "unit_cost_pence", "resalable"]:
            try:
                r[k] = int(r[k])
            except (ValueError, TypeError):
                raise ValueError(f"Row {n}: {k} must be an integer") from None
        try:
            date.fromisoformat(r["date"])
        except ValueError:
            raise ValueError(f"Row {n}: invalid ISO date") from None
        if not r["line_id"] or r["line_id"] in seen:
            raise ValueError(f"Row {n}: missing or duplicate line_id")
        if not r["receipt_id"] or not r["store"] or r["sku"] not in skus:
            raise ValueError(f"Row {n}: missing receipt/store or unknown SKU")
        if r["kind"] not in {"SALE", "RETURN"} or r["quantity"] <= 0:
            raise ValueError(f"Row {n}: invalid transaction kind or quantity")
        if r["unit_price_pence"] < 0 or r["unit_cost_pence"] < 0 or not 0 <= r["discount_pence"] <= r["unit_price_pence"]:
            raise ValueError(f"Row {n}: invalid price, cost or discount")
        if r["resalable"] not in {0, 1}:
            raise ValueError(f"Row {n}: resalable must be 0 or 1")
        seen[r["line_id"]] = r
        clean.append(r)
    receipts = {}
    for r in clean:
        key = (r["date"], r["store"], r["kind"])
        if r["receipt_id"] in receipts and receipts[r["receipt_id"]] != key:
            raise ValueError("A receipt must belong to one date, store and transaction kind")
        receipts[r["receipt_id"]] = key
        if r["kind"] == "SALE":
            if r["original_line_id"]:
                raise ValueError("Sale lines cannot reference another sale")
            continue
        original = seen.get(r["original_line_id"])
        if not original or original["kind"] != "SALE":
            raise ValueError("Return must reference a sale in this import")
        if any(original[k] != r[k] for k in ["store", "sku", "unit_price_pence", "discount_pence", "unit_cost_pence"]):
            raise ValueError("Return must match the original store, SKU and unit values")
        if r["date"] < original["date"]:
            raise ValueError("Return cannot precede its sale")
        returned[original["line_id"]] = returned.get(original["line_id"], 0) + r["quantity"]
        if returned[original["line_id"]] > original["quantity"]:
            raise ValueError("Cumulative returns exceed the original quantity")
    return clean


def build_database(data_dir=ROOT / "data", db_path=":memory:"):
    products = read_csv(Path(data_dir) / "products.csv")
    inventory = read_csv(Path(data_dir) / "inventory.csv")
    if not products or len({p["sku"] for p in products}) != len(products):
        raise ValueError("Product SKUs must be populated and unique")
    rows = validated_rows(read_csv(Path(data_dir) / "transactions.csv"), products)
    if not rows:
        raise ValueError("No transactions to analyse")
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    c.executescript((ROOT / "sql" / "schema.sql").read_text())
    with c:
        c.executemany("INSERT INTO products VALUES (?,?,?)",
                      [(p["sku"], p["product"], p["category"]) for p in products])
        c.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      [tuple(r[k] for k in FIELDS) for r in rows])
        inv_keys = set()
        last_day = max(r["date"] for r in rows)
        for r in inventory:
            key = (r["store"], r["sku"])
            if key in inv_keys or r["sku"] not in {p["sku"] for p in products}:
                raise ValueError("Duplicate inventory key or unknown SKU")
            inv_keys.add(key)
            nums = [int(r[k]) for k in ["on_hand", "on_order", "lead_days", "pack_size", "safety_units"]]
            if min(nums) < 0 or nums[3] == 0 or r["snapshot_date"] != last_day:
                raise ValueError("Inventory quantities must be non-negative; pack size positive; snapshot must match period end")
            c.execute("INSERT INTO inventory VALUES (?,?,?,?,?,?,?,?)",
                      (*key, r["snapshot_date"], *nums))
        expected = {(r["store"], r["sku"]) for r in rows}
        if not expected.issubset(inv_keys):
            raise ValueError("Inventory snapshot is missing a store/SKU in the transactions")
    return c


def report(c, review_days=7):
    if type(review_days) is not int or review_days < 1:
        raise ValueError("review_days must be a positive integer")
    start, end = c.execute("SELECT MIN(date),MAX(date) FROM transactions").fetchone()
    period_days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    stores = [dict(r) for r in c.execute((ROOT / "sql" / "store_metrics.sql").read_text())]
    weekly = [dict(r) for r in c.execute((ROOT / "sql" / "weekly_metrics.sql").read_text())]
    stock = []
    for r in c.execute("""
      SELECT i.*, p.product, COALESCE(SUM(CASE WHEN t.kind='SALE' THEN t.quantity ELSE 0 END),0) sold_units
      FROM inventory i JOIN products p USING(sku)
      LEFT JOIN transactions t ON t.store=i.store AND t.sku=i.sku
      GROUP BY i.store,i.sku ORDER BY i.store,i.sku
    """):
        x = dict(r)
        daily = x["sold_units"] / period_days
        position = x["on_hand"] + x["on_order"]
        point = daily * x["lead_days"] + x["safety_units"]
        target = math.ceil((daily * (x["lead_days"] + review_days) + x["safety_units"]) / x["pack_size"]) * x["pack_size"]
        order = math.ceil(max(0, target-position) / x["pack_size"]) * x["pack_size"] if position <= point else 0
        x.update(daily_units=daily, inventory_position=position, reorder_point=point,
                 target_units=target, reorder_units=order,
                 cover_days=x["on_hand"]/daily if daily else None)
        stock.append(x)
    return {"data_type": "Synthetic portfolio scenario", "currency": "GBP",
            "start": start, "end": end, "period_days": period_days, "review_days": review_days,
            "stores": stores, "weekly": weekly, "inventory": stock}


def write_report(c, output=ROOT / "reports"):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    result = report(c)
    (output / "metrics.json").write_text(json.dumps(result, indent=2))
    for key in ["stores", "weekly", "inventory"]:
        rows = result[key]
        with (output / f"{key}.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)
    template = (ROOT / "retail_ops" / "dashboard_template.html").read_text()
    # Dataset is generated locally; escape HTML-significant characters in JSON before embedding.
    payload = json.dumps(result).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    (output / "dashboard.html").write_text(template.replace("__METRICS__", payload))
    return result
