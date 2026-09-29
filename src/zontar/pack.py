"""Assemble the deliverable zip for one vehicle.

Zip layout (unchanged from the historical packages)::

    <package_name>/01_主图/...           <- assets/outputs/vehicles/<slug>/package/
    <package_name>/04_上架资料/*.xlsx     <- assets/outputs/vehicles/<slug>/package/04_上架资料/
    <package_name>/04_上架资料/*.csv|txt  <- data/vehicles/<slug>/   (git is the source of truth)
    ...

Excluded: generation sources, tool dumps (*.inspect.ndjson) and the per-sheet CSV folders.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from . import layout

TEXT_EXT = {".csv", ".txt", ".md"}
EXCLUDE_SUFFIXES = (".inspect.ndjson", ".part")


def files_for(v: layout.Vehicle) -> list[tuple[Path, str]]:
    items: list[tuple[Path, str]] = []
    for p in sorted(v.package.rglob("*")):
        if p.is_file() and not p.name.endswith(EXCLUDE_SUFFIXES):
            items.append((p, f"{v.package_name}/{p.relative_to(v.package).as_posix()}"))
    for p in sorted(v.data_dir.iterdir()) if v.data_dir.exists() else []:
        if p.is_file() and p.suffix.lower() in TEXT_EXT:
            items.append((p, f"{v.package_name}/{layout.INFO}/{p.name}"))
    return items


def build(slug: str) -> Path:
    v = layout.vehicle(slug)
    v.dist.mkdir(parents=True, exist_ok=True)
    tmp = v.zip_path.with_suffix(".zip.part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in files_for(v):
            z.write(src, arc)
    tmp.replace(v.zip_path)
    return v.zip_path
