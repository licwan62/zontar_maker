"""Render Tiguan S background-library demos without changing the formal package."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from PIL import Image, ImageDraw, ImageFont

from zontar import layout, render, tables


BACKGROUND_IDS = [
    "bg_winter_lakeside_001",
    "bg_autumn_stone_residence_001",
    "bg_frosty_forest_overlook_001",
    "bg_wet_urban_park_001",
    "bg_riverside_promenade_001",
    "bg_snowy_alpine_lodge_001",
    "bg_coastal_cliff_overlook_001",
    "bg_frosted_birch_grove_001",
    "bg_modern_villa_courtyard_001",
    "bg_misty_mountain_valley_001",
    "bg_meadow_lakeshore_001",
    "bg_autumn_manor_drive_001",
    "bg_stone_bridge_valley_001",
    "bg_winter_city_plaza_001",
    "bg_pine_forest_retreat_001",
]


def main() -> None:
    v = layout.vehicle("volkswagen_tiguan").ensure_dirs()
    reg = layout.vehicle_registry()[v.slug]
    rows = tables.read_csv(v.data_dir / "inputs" / "skus.csv")
    row = next(item for item in rows if item["sku"] == "S")
    source_sku = render.Sku(
        code=row["sku"], ship_size=row["ship_size"], body=row["body"], years=row["years"],
        base_image=row["base_image"], vehicle_image=row.get("vehicle_image") or None,
        cards=[tuple(card.split("=", 1)) for card in row["cards"].split("|")],
    )
    job = render.Job(
        brand=reg["listing_brand"], title="VOLKSWAGEN TIGUAN", file_prefix="VW_Tiguan",
        subtitle=("ВСЕСЕЗОННЫЙ ЧЕХОЛ", "ДЛЯ КРОССОВЕРА"), skus=[source_sku],
        style="renault_logan", main_title_lines=("VOLKSWAGEN", "TIGUAN"),
    )
    out_dir = v.package.parent / "background_demos"
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for background_id in BACKGROUND_IDS:
        sku = render.Sku(
            code=source_sku.code, ship_size=source_sku.ship_size, body=source_sku.body,
            years=source_sku.years, cards=source_sku.cards,
            base_image=f"background_demos/{background_id}.png",
            vehicle_image=source_sku.vehicle_image,
        )
        image = render.main_image(job, v, render._logo(job), render._icons(), sku)
        target = out_dir / f"{background_id}__VW_Tiguan_S_主图_1086x1448.png"
        image.convert("RGB").save(target, quality=95)
        rendered.append((background_id, target))

    thumb_w, thumb_h = 217, 290
    columns = 5
    rows_count = (len(rendered) + columns - 1) // columns
    gap_x, gap_y, margin = 32, 68, 32
    sheet = Image.new(
        "RGB",
        (thumb_w * columns + gap_x * (columns - 1) + margin * 2,
         thumb_h * rows_count + gap_y * rows_count + margin),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(render.FONT_DIR / "arial.ttf"), 17)
    for index, (background_id, target) in enumerate(rendered):
        column, row_index = index % columns, index // columns
        x = margin + column * (thumb_w + gap_x)
        y = 18 + row_index * (thumb_h + gap_y)
        thumb = Image.open(target).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        label = background_id.removeprefix("bg_").removesuffix("_001").replace("_", " ")
        draw.text((x, y + thumb_h + 10), label, font=font, fill=(3, 37, 67))
    sheet_path = out_dir / f"VW_Tiguan_S_{len(rendered)}背景_demo_contact_sheet.png"
    sheet.save(sheet_path, quality=95)
    print(f"rendered {len(rendered)} demos -> {out_dir}")
    print(f"contact sheet -> {sheet_path}")
    print(f"layout audit passed: {job.layout_audits['S']['passed']}")


if __name__ == "__main__":
    main()
