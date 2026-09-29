"""One-off: reorganise the flat 2026-09 handoff folder into the pipeline layout.

    python scripts/migrate_layout.py            # dry run: print the plan
    python scripts/migrate_layout.py --apply    # move files, write manifests/migration_map.csv

Only moves; never deletes. Every moved file is recorded (old path -> new path).
Kept in the repo as the record of where each legacy file went.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = "assets"

VEHICLES = {
    "Renault_Logan_Tozaroa_最终上架包": "renault_logan",
    "Toyota_Land_Cruiser_Tozaroa_最终上架包": "toyota_land_cruiser",
    "Toyota_RAV4_Tozaroa_最终上架包": "toyota_rav4",
}

PIPELINE_SCRIPTS = {
    "build_logan_package.py": "pipelines/renault_logan/10_build_images.py",
    "redesign_logan_fitment.py": "pipelines/renault_logan/20_redesign_fitment.py",
    "build_logan_spreadsheets.mjs": "pipelines/renault_logan/30_build_listing.mjs",
    "build_landcruiser_package.py": "pipelines/toyota_land_cruiser/10_build_package.py",
    "redesign_landcruiser_master.py": "pipelines/toyota_land_cruiser/20_redesign_master.py",
    "build_landcruiser_spreadsheets.mjs": "pipelines/toyota_land_cruiser/30_build_listing.mjs",
    "build_rav4_v6.py": "pipelines/toyota_rav4/10_build_images_v6.py",
    "update_rav4_listing_csv.mjs": "pipelines/toyota_rav4/25_update_listing_tags.mjs",
    "sync_rav4_artifact.mjs": "pipelines/toyota_rav4/30_build_listing.mjs",
}

PROMPT_DOCS = {"00_新项目开场.txt", "01_完整执行总提示词.md", "02_逐图生成提示词.json",
               "03_逐图提示词_可阅读版.md", "04_来源与转换说明.md",
               "Tozaroa_灰色单层PEVA无耳车罩_完整提示词_v01.md"}

INPUT_SHEETS = {"ozon1000排名.xlsx", "ozon汽车车罩搜索词词库 - - 副本.xlsx",
                "汽车车罩标签词 - 副本.xlsx", "俄罗斯带销量数据_0928.xlsx"}

DIST_ZIPS = {
    "Renault_Logan_Tozaroa_最终上架包.zip": f"{A}/outputs/vehicles/renault_logan/dist/Renault_Logan_Tozaroa_最终上架包.zip",
    "Toyota_Land_Cruiser_Tozaroa_最终上架包.zip": f"{A}/outputs/vehicles/toyota_land_cruiser/dist/Toyota_Land_Cruiser_Tozaroa_最终上架包.zip",
    # Pre-XS V6 build from 2026-09-27, not the final package: archived.
    "Toyota_RAV4_Tozaroa_最终上架包_V6.zip": f"{A}/archive/dist_legacy/Toyota_RAV4_Tozaroa_最终上架包_V6.zip",
}

BACKUP_DIRS = {"原图备份_平面视角_20260920", "Toyota_RAV4_淘汰版本备份_20260927",
               "Toyota_Land_Cruiser_旧版备份_20260928", "Toyota_Land_Cruiser_文字升级前备份_20260929"}
SAMPLE_DIRS = {"阶段01_试样", "阶段02_两厢车A+试样"}


def plan() -> list[tuple[Path, Path]]:
    """(source, destination) pairs, relative to REPO. Directories move as a whole unless split below."""
    moves: list[tuple[str, str]] = []
    for item in sorted(REPO.iterdir(), key=lambda p: p.name):
        n = item.name
        if item.is_dir():
            if n in VEHICLES:
                slug = VEHICLES[n]
                for sub in sorted(item.iterdir()):
                    if sub.name == "00_生成源图":
                        moves.append((f"{n}/{sub.name}", f"{A}/inputs/vehicles/{slug}/source"))
                    elif sub.name == "04_上架资料":
                        for f in sorted(sub.iterdir()):
                            if f.suffix in {".csv", ".txt"}:
                                moves.append((f"{n}/04_上架资料/{f.name}", f"data/vehicles/{slug}/{f.name}"))
                            elif f.name.endswith(".inspect.ndjson"):
                                moves.append((f"{n}/04_上架资料/{f.name}", f"{A}/archive/inspect_dumps/{f.name}"))
                            else:
                                moves.append((f"{n}/04_上架资料/{f.name}", f"{A}/outputs/vehicles/{slug}/package/04_上架资料/{f.name}"))
                    else:
                        moves.append((f"{n}/{sub.name}", f"{A}/outputs/vehicles/{slug}/package/{sub.name}"))
            elif n == "Toyota_RAV4_淘汰版本备份_20260927":
                # The RAV4 generation sources (base_*/vehicle_*) are live inputs for the V6 script.
                src_dir = item / "01_SKU专属图"
                for f in sorted(src_dir.glob("*.png")):
                    if f.name.startswith(("base_", "vehicle_")):
                        moves.append((f"{n}/01_SKU专属图/{f.name}", f"{A}/inputs/vehicles/toyota_rav4/source/{f.name}"))
                moves.append((n, f"{A}/archive/backups/{n}"))
            elif n in BACKUP_DIRS:
                moves.append((n, f"{A}/archive/backups/{n}"))
            elif n in SAMPLE_DIRS:
                moves.append((n, f"{A}/archive/samples/{n}"))
            elif n.startswith("阶段"):
                moves.append((n, f"{A}/inputs/category_library/{n}"))
            continue

        if n in PIPELINE_SCRIPTS:
            moves.append((n, PIPELINE_SCRIPTS[n]))
        elif item.suffix in {".py", ".mjs", ".ps1"}:
            moves.append((n, f"scripts/legacy/{n}"))
        elif n in PROMPT_DOCS:
            moves.append((n, f"docs/prompts/{n}"))
        elif n == "功能图标_雨雪阳光四季.png":
            moves.append((n, f"{A}/inputs/brand/{n}"))
        elif n in INPUT_SHEETS:
            moves.append((n, f"{A}/inputs/spreadsheets/{n}"))
        elif n.startswith("Ozon上架链接汇总_"):
            moves.append((n, f"{A}/archive/spreadsheets/listing_summary/{n}"))
        elif n.startswith("汽车罩官方上架模板_"):
            moves.append((n, f"{A}/archive/spreadsheets/official_template/{n}"))
        elif n in DIST_ZIPS:
            moves.append((n, DIST_ZIPS[n]))
        elif n.startswith("ZONTAR_") and n.endswith(".zip"):
            moves.append((n, f"{A}/archive/handoff/{n}"))
        elif item.suffix == ".png":
            moves.append((n, f"{A}/archive/reports/{n}"))
    return [(REPO / s, REPO / d) for s, d in moves]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    moves = plan()
    for s, d in moves:
        if d.exists():
            print(f"CONFLICT destination exists: {d.relative_to(REPO)}")
            return 1
    records: list[tuple[str, str]] = []
    for s, d in moves:
        if not s.exists():
            continue
        files = [s] if s.is_file() else [p for p in sorted(s.rglob("*")) if p.is_file()]
        for f in files:
            records.append((f.relative_to(REPO).as_posix(), (d / f.relative_to(s)).relative_to(REPO).as_posix()
                            if s.is_dir() else d.relative_to(REPO).as_posix()))
        print(f"{s.relative_to(REPO).as_posix()}  ->  {d.relative_to(REPO).as_posix()}  ({len(files)} files)")
        if args.apply:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(s), str(d))

    if args.apply:
        # Drop package folders left empty after their children were split out.
        for n in list(VEHICLES) + ["Toyota_RAV4_淘汰版本备份_20260927"]:
            p = REPO / n
            if p.exists():
                for sub in sorted(p.rglob("*"), reverse=True):
                    if sub.is_dir() and not any(sub.iterdir()):
                        sub.rmdir()
                if not any(p.iterdir()):
                    p.rmdir()
        out = REPO / "manifests" / "migration_map.csv"
        out.parent.mkdir(exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["old_path", "new_path"])
            w.writerows(records)
        print(f"moved {len(records)} files; map written to {out.relative_to(REPO)}")
    else:
        print(f"dry run: {len(records)} files would move. Re-run with --apply.")
    leftovers = [p.name for p in REPO.iterdir() if p.name not in {
        ".git", ".gitignore", ".gitattributes", "README.md", "pyproject.toml", "config", "data", "docs",
        "manifests", "pipelines", "scripts", "src", "assets", ".claude", ".vscode"}
        and not any(s == p for s, _ in moves)]
    if leftovers:
        print("unplanned top-level items:", leftovers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
