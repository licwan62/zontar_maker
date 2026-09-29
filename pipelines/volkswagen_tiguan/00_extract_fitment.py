"""Step 00: fitment evidence for the Tiguan SKUs.

in : data/reference/ru_sales_0928/RU尺寸组&销量.csv       (per-generation sizes and sales)
     data/vehicles/volkswagen_tiguan/inputs/size_map.csv   (size mapping supplied by the operator)
     data/vehicles/volkswagen_tiguan/inputs/skus.csv       (SKU definitions)
out: data/vehicles/volkswagen_tiguan/inputs/fitment_detail.csv
Fails if a generation maps to an Ozon size that has no SKU, or the ship size disagrees.
"""
import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
from collections import defaultdict

from zontar import layout, tables

sys.stdout.reconfigure(encoding="utf-8")
v = layout.vehicle("volkswagen_tiguan")
inputs = v.data_dir / "inputs"
sales = tables.read_csv(layout.data_root() / "reference/ru_sales_0928/RU尺寸组&销量.csv")
skus = {r["sku"]: r for r in tables.read_csv(inputs / "skus.csv")}
size_map = tables.read_csv(inputs / "size_map.csv")

cols = ["MAKE", "MODEL", "版本", "代际", "YEAR", "L-MM", "W-MM", "H-MM", "尺寸组销量", "自动尺码", "OZON尺码", "发货尺码", "自动长度余量"]
rows = [r for r in sales if r["MAKE"] == "Volkswagen" and r["MODEL"].startswith("Tiguan")]
rows.sort(key=lambda r: (r["OZON尺码"], r["YEAR"], r["MODEL"], r["版本"]))
tables.write_csv(inputs / "fitment_detail.csv", [cols] + [[r[c] for c in cols] for r in rows])

errors = []
sold = defaultdict(int)
for r in rows:
    sku = skus.get(r["OZON尺码"])
    if not sku:
        errors.append(f"no SKU for Ozon size {r['OZON尺码']}: {r['MODEL']} {r['版本']} {r['代际']}")
    elif sku["ship_size"] != r["发货尺码"]:
        errors.append(f"ship size mismatch for {r['MODEL']} {r['代际']}: data {r['发货尺码']} vs SKU {sku['ship_size']}")
    sold[r["OZON尺码"]] += int(r["尺寸组销量"] or 0)
for m in size_map:
    sku = skus.get(m["OZON尺码"])
    if not sku or sku["ship_size"] != m["发货尺码"]:
        errors.append(f"size_map row {m['MODEL']} {m['VERSION']} {m['YEAR']} -> {m['OZON尺码']}/{m['发货尺码']} not covered by skus.csv")

for r in rows:
    print(f"{r['OZON尺码']:2} {r['发货尺码']:3} {r['MODEL']:10} {r['版本']:9} {r['代际']:32} {r['YEAR']:10} L={r['L-MM']}")
print("sales by Ozon size:", dict(sold))
if errors:
    print("\n".join("ERROR " + e for e in errors))
    raise SystemExit(1)
print(f"ok: {len(rows)} generations -> {inputs / 'fitment_detail.csv'}")
