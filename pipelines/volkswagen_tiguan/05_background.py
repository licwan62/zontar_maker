"""Step 05: bind an environment background to each SKU (on demand).

in : data/vehicles/volkswagen_tiguan/inputs/backgrounds.csv   (sku,mode,scene,background_id,seed,notes)
     data/backgrounds.csv, data/backgrounds/scenes.csv, data/backgrounds/prompt_template.md
out: background_id written back to backgrounds.csv; for missing ones a generation request
     data/backgrounds/prompts/<id>.md (generate with imagegen, then `python run.py bg register <id> <image>`)

Does not block later steps: the current base_<SKU>.png already contain a scene. An approved
background is the imagegen reference for the next regeneration of base_<SKU>.png.
"""
import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))

from zontar import backgrounds

sys.stdout.reconfigure(encoding="utf-8")
SLUG, STYLE = "volkswagen_tiguan", "renault_logan"   # keep STYLE in sync with 10_build_images.py

for b in backgrounds.resolve_vehicle(SLUG, STYLE):
    print(f"sku {b['sku']:4} {b['background_id']:28} {b['state']:10} ({b['action']})")
for t in backgrounds.todo(SLUG):
    print(f"TODO  {t}")
