"""Render the locked Tiguan hero template in its three supported color themes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from PIL import Image, ImageDraw, ImageFont

from zontar import hero_template, layout


DEMOS = (
    ("midnight_orange", "background_demos/bg_snowy_alpine_lodge_001.png", "MIDNIGHT ORANGE / DARK SCENES"),
    ("arctic_blue", "background_demos/bg_snowy_alpine_lodge_001.png", "ARCTIC BLUE / SNOW & LIGHT GRAY"),
    ("forest_gold", "background_demos/bg_snowy_alpine_lodge_001.png", "FOREST GOLD / AUTUMN & STONE"),
)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    v = layout.vehicle("volkswagen_tiguan").ensure_dirs()
    out_dir = v.package.parent / "hero_palette_demos"
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = hero_template.HeroFields(
        "VOLKSWAGEN TIGUAN", "ФОЛЬКСВАГЕН ТИГУАН", "КРОССОВЕР", "2007–2026", "S"
    )
    rendered = []
    for palette_name, source_name, label in DEMOS:
        image, report = hero_template.render_hero(
            Image.open(v.source / source_name), fields, hero_template.palette_by_name(palette_name)
        )
        target = out_dir / f"VW_Tiguan_S_{palette_name}_1086x1448.png"
        image.save(target, optimize=True)
        rendered.append((target, label, report["palette"]))

    thumb_w, thumb_h, gap, label_h = 543, 724, 22, 58
    sheet = Image.new("RGB", (thumb_w * 3 + gap * 4, thumb_h + label_h + gap * 2), (238, 241, 244))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(hero_template.FONT_DIR / "arialbd.ttf"), 16)
    for index, (target, label, _) in enumerate(rendered):
        x = gap + index * (thumb_w + gap)
        sheet.paste(Image.open(target).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, gap))
        draw.text((x, gap + thumb_h + 14), label, font=font, fill=hero_template.NAVY)
    sheet_path = out_dir / "VW_Tiguan_三套颜色主题对照.png"
    sheet.save(sheet_path, optimize=True)
    print(f"rendered {len(rendered)} palette demos -> {out_dir}")
    print(f"comparison -> {sheet_path}")


if __name__ == "__main__":
    main()
