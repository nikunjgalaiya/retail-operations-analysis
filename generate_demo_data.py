"""Generate a reproducible, fictional six-week retail scenario."""
import csv
import random
from datetime import date,timedelta
from pathlib import Path
from retail_ops.core import FIELDS

OUT=Path(__file__).parent/"data"; OUT.mkdir(exist_ok=True)
rng=random.Random(724)
products=[
 ("B01","Steel bottle","Drinkware",2400,1050),("B02","Glass bottle","Drinkware",1800,800),
 ("T01","Travel cup","Drinkware",2100,900),("P01","Citrus refill","Refills",850,330),
 ("P02","Berry refill","Refills",850,330),("P03","Mint refill","Refills",750,290),
 ("G01","Gift sleeve","Accessories",350,110),("G02","Gift box","Accessories",550,190)]
stores=["Central","Riverside","Market"]
def write(name,fields,rows):
 with (OUT/name).open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
write("products.csv",["sku","product","category"],[dict(zip(["sku","product","category"],p[:3])) for p in products])
rows=[]; sales=[];count=0
for day in range(42):
 current=date(2026,9,7)+timedelta(days=day)
 for store in stores:
  for receipt in range(rng.randint(5,9)):
   receipt_id=f"S-{day:02d}-{store[0]}-{receipt}"
   for product in rng.sample(products,rng.randint(1,3)):
    count+=1;qty=rng.randint(1,3)
    row=dict(zip(FIELDS,[f"L{count:05d}",receipt_id,current.isoformat(),store,product[0],
       "SALE",qty,product[3],rng.choice([0,0,0,50]),product[4],"",1]))
    rows.append(row);sales.append(row)
  eligible=[s for s in sales if s["store"]==store and s["date"]<current.isoformat() and s["line_id"] not in {x["original_line_id"] for x in rows if x["kind"]=="RETURN"}]
  if eligible and rng.random()<.45:
   sale=rng.choice(eligible);count+=1
   rows.append({**sale,"line_id":f"L{count:05d}","receipt_id":f"R-{day:02d}-{store[0]}",
     "date":current.isoformat(),"kind":"RETURN","quantity":1,"original_line_id":sale["line_id"],
     "resalable":rng.choice([0,1,1])})
write("transactions.csv",FIELDS,rows)
inventory=[]
for store in stores:
 for sku,*_ in products:
  inventory.append(dict(zip(["store","sku","snapshot_date","on_hand","on_order","lead_days","pack_size","safety_units"],
      [store,sku,"2026-10-18",rng.randint(2,100),rng.choice([0,0,12]),rng.choice([3,5,7]),6,6])))
write("inventory.csv",list(inventory[0]),inventory)
print(f"Generated {len(rows)} transaction lines, {len(inventory)} inventory positions")
