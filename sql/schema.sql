PRAGMA foreign_keys=ON;
CREATE TABLE products(sku TEXT PRIMARY KEY, product TEXT NOT NULL, category TEXT NOT NULL);
CREATE TABLE transactions(
 line_id TEXT PRIMARY KEY,receipt_id TEXT NOT NULL,date TEXT NOT NULL,store TEXT NOT NULL,
 sku TEXT NOT NULL REFERENCES products(sku),kind TEXT CHECK(kind IN ('SALE','RETURN')),
 quantity INTEGER CHECK(quantity>0),unit_price_pence INTEGER,discount_pence INTEGER,
 unit_cost_pence INTEGER,original_line_id TEXT,resalable INTEGER CHECK(resalable IN (0,1))
);
CREATE TABLE inventory(
 store TEXT,sku TEXT REFERENCES products(sku),snapshot_date TEXT,on_hand INTEGER,
 on_order INTEGER,lead_days INTEGER,pack_size INTEGER,safety_units INTEGER,
 PRIMARY KEY(store,sku)
);
CREATE VIEW facts AS
 SELECT *,CASE WHEN kind='SALE' THEN 1 ELSE -1 END*quantity signed_units,
 CASE WHEN kind='SALE' THEN 1 ELSE -1 END*quantity*(unit_price_pence-discount_pence) net_pence,
 CASE WHEN kind='SALE' THEN quantity*unit_cost_pence
      WHEN resalable=1 THEN -quantity*unit_cost_pence ELSE 0 END cogs_pence
 FROM transactions;
