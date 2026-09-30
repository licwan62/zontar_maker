"""Render Tiguan main images with the locked "灰色无耳首图" template, without touching the package.

in : data/vehicles/volkswagen_tiguan/inputs/hero.csv   (template fields per SKU)
     assets/inputs/vehicles/volkswagen_tiguan/source/<background>
     assets/archive/samples/首图模板.png                 (style reference, for the comparison sheet)
out: assets/outputs/vehicles/volkswagen_tiguan/hero_template_demos/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import json

from PIL import Image

from zontar import hero_template, layout, tables

REFERENCE = "archive/samples/首图模板.png"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    v = layout.vehicle("volkswagen_tiguan").ensure_dirs()
    out_dir = v.package.parent / "hero_template_demos"
    out_dir.mkdir(parents=True, exist_ok=True)
    report, outputs = {}, []
    for row in tables.read_csv(v.data_dir / "inputs" / "hero.csv"):
        fields = hero_template.HeroFields(row["model_latin"], row["model_ru_search"], row["body_ru"],
                                          row["years"], row["size_code"])
        image, report[row["sku"]] = hero_template.render_hero(Image.open(v.source / row["background"]), fields)
        out = out_dir / f"VW_Tiguan_{row['sku']}_固定模板主图_1086x1448.png"
        image.save(out, optimize=True)
        outputs.append(out)

    reference = layout.asset(REFERENCE)
    tiles = ([Image.open(reference).convert("RGB")] if reference.exists() else []) + [Image.open(p) for p in outputs]
    sheet = Image.new("RGB", (len(tiles) * 543 + (len(tiles) + 1) * 16, 724 + 32), (236, 240, 244))
    for i, tile in enumerate(tiles):
        sheet.paste(tile.resize((543, 724), Image.Resampling.LANCZOS), (16 + i * 559, 16))
    sheet.save(out_dir / "对照_参考图与固定模板.png", optimize=True)
    (out_dir / "hero_template_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"outputs": [str(p) for p in outputs], "report": report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
