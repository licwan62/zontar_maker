"""Step 10: SKU images + shared SUV gallery/A+.

in : data/vehicles/volkswagen_tiguan/inputs/skus.csv
     assets/inputs/vehicles/volkswagen_tiguan/source/base_<SKU>.png   (placeholder + DRAFT watermark if missing)
     assets/inputs/brand/*, assets/inputs/category_library/阶段09_越野车副图, 阶段10_越野车A+
out: assets/outputs/vehicles/volkswagen_tiguan/package/01_主图, 02_车型适配图, 03_SKU共用图, 05_预览, 06-08
"""
import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
import json
import shutil

from zontar import layout, render, tables

sys.stdout.reconfigure(encoding="utf-8")
v = layout.vehicle("volkswagen_tiguan").ensure_dirs()
reg = layout.vehicle_registry()[v.slug]

skus = [render.Sku(code=r["sku"], ship_size=r["ship_size"], body=r["body"], years=r["years"], base_image=r["base_image"],
                   vehicle_image=r.get("vehicle_image") or None,
                   cards=[tuple(c.split("=", 1)) for c in r["cards"].split("|")])
        for r in tables.read_csv(v.data_dir / "inputs" / "skus.csv")]
job = render.Job(brand=reg["listing_brand"], title="VOLKSWAGEN TIGUAN", file_prefix="VW_Tiguan",
                 subtitle=("ВСЕСЕЗОННЫЙ ЧЕХОЛ", "ДЛЯ КРОССОВЕРА"), skus=skus,
                 style="renault_logan")
result = render.render_vehicle(job, v)

for src, dst in [(layout.category_library(v.gallery_source), v.gallery),
                 (layout.category_library(v.aplus_source) / "01_PC端_5张", v.aplus_pc),
                 (layout.category_library(v.aplus_source) / "02_手机端_5张", v.aplus_mobile)]:
    for p in sorted(src.glob("*.png")):
        shutil.copy2(p, dst / p.name)

print(json.dumps(result, ensure_ascii=False, indent=2))
