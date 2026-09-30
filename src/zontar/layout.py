"""Single source of truth for where pipeline artifacts live.

Two parallel trees:

* ``data/``   (git)          - every table as CSV, plus small text notes.
* ``assets/`` (asset store)  - images, zips, original .xlsx; synced to NAS/OSS.

Asset tree (keys are POSIX paths relative to the asset root)::

    inputs/brand/                          logo + icon sprites
    inputs/category_library/<stage>/       generic per-body-type gallery & A+ images
    inputs/background_library/<id>.png     generated environment backgrounds (data/backgrounds.csv)
    inputs/vehicles/<slug>/source/         generated base / cutout photos for one vehicle
    inputs/spreadsheets/                   original .xlsx inputs (template, tag bank, sales...)
    outputs/vehicles/<slug>/package/       deliverable images, laid out as the upload package
    outputs/vehicles/<slug>/dist/          zipped package
    archive/                               backups, rejected versions, one-off QA screenshots

The per-vehicle registry lives in ``data/vehicles.csv``.
"""
from __future__ import annotations

import csv
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath

from .config import settings

# Package sub-folders (names are what operators see inside the delivered zip).
MAIN = "01_主图"
FITMENT = "02_车型适配图"
SELECTOR = "03_SKU共用图"
INFO = "04_上架资料"
PREVIEW = "05_预览"
APLUS_PC = "07_A+_PC端"
APLUS_MOBILE = "08_A+_移动端"


def asset_root() -> Path:
    return settings().asset_root


def data_root() -> Path:
    return settings().data_root


def asset(key: str | PurePosixPath) -> Path:
    """Local path of an asset key (inside the configured asset root)."""
    return asset_root() / PurePosixPath(key)


def key_of(path: Path) -> str:
    """Asset key for a local path inside the asset root."""
    return path.resolve().relative_to(asset_root().resolve()).as_posix()


# --- shared inputs -----------------------------------------------------------
def brand_logo() -> Path:
    return asset("inputs/brand/logo_tozaroa.png")


def brand_icons() -> Path:
    return asset("inputs/brand/功能图标_雨雪阳光四季.png")


def category_library(stage: str) -> Path:
    return asset(f"inputs/category_library/{stage}")


def background_library() -> Path:
    """Environment backgrounds indexed by data/backgrounds.csv (see zontar.backgrounds)."""
    return asset("inputs/background_library")


def input_spreadsheet(name: str) -> Path:
    return asset(f"inputs/spreadsheets/{name}")


# --- vehicles ------------------------------------------------------------------
def vehicle_registry() -> dict[str, dict[str, str]]:
    with (data_root() / "vehicles.csv").open(encoding="utf-8-sig", newline="") as f:
        return {row["slug"]: row for row in csv.DictReader(f)}


@dataclass(frozen=True)
class Vehicle:
    slug: str
    package_name: str
    gallery_folder: str
    gallery_source: str
    aplus_source: str

    # inputs
    @property
    def source(self) -> Path:
        return asset(f"inputs/vehicles/{self.slug}/source")

    @property
    def candidates(self) -> Path:
        """Web-sourced vehicle photos awaiting review (vehicle-image-scout agent). Never read by renderers."""
        return asset(f"inputs/vehicles/{self.slug}/candidates")

    # outputs (asset store)
    @property
    def package(self) -> Path:
        return asset(f"outputs/vehicles/{self.slug}/package")

    @property
    def main(self) -> Path:
        return self.package / MAIN

    @property
    def fitment(self) -> Path:
        return self.package / FITMENT

    @property
    def selector(self) -> Path:
        return self.package / SELECTOR

    @property
    def info(self) -> Path:
        """Binary listing files (official .xlsx). Their CSV twins live in ``data_dir``."""
        return self.package / INFO

    @property
    def preview(self) -> Path:
        return self.package / PREVIEW

    @property
    def gallery(self) -> Path:
        return self.package / self.gallery_folder

    @property
    def aplus_pc(self) -> Path:
        return self.package / APLUS_PC

    @property
    def aplus_mobile(self) -> Path:
        return self.package / APLUS_MOBILE

    @property
    def dist(self) -> Path:
        return asset(f"outputs/vehicles/{self.slug}/dist")

    @property
    def zip_path(self) -> Path:
        return self.dist / f"{self.package_name}.zip"

    # tables (git)
    @property
    def data_dir(self) -> Path:
        return data_root() / "vehicles" / self.slug

    def ensure_dirs(self) -> "Vehicle":
        for d in (self.main, self.fitment, self.selector, self.info, self.preview,
                  self.gallery, self.aplus_pc, self.aplus_mobile, self.dist, self.data_dir):
            d.mkdir(parents=True, exist_ok=True)
        return self


def vehicle(slug: str) -> Vehicle:
    row = vehicle_registry()[slug]
    return Vehicle(slug, row["package_name"], row["gallery_folder"], row["gallery_source"], row["aplus_source"])


def backup_before_overwrite(folders: list[Path], label: str) -> Path | None:
    """Copy folders to archive/backups/<date>_<label>/ once, before a destructive re-render."""
    target = asset(f"archive/backups/{date.today():%Y%m%d}_{label}")
    if target.exists():
        return None
    for folder in folders:
        if folder.exists():
            shutil.copytree(folder, target / folder.name)
    return target
