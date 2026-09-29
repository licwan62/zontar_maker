"""Asset manifests: the git-tracked record of every binary in the asset store.

One CSV per top-level area (manifests/inputs.csv, outputs.csv, archive.csv) with
columns key, bytes, sha256, width, height. A fresh clone plus the remote store is
enough to reproduce the exact asset tree (`zontar sync pull`).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from . import layout
from .config import settings
from .hashing import sha256_file

AREAS = ("inputs", "outputs", "archive")
FIELDS = ["key", "bytes", "sha256", "width", "height"]
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
IGNORED_NAMES = {"Thumbs.db", "desktop.ini", ".DS_Store"}


@dataclass
class Entry:
    key: str
    bytes: int
    sha256: str
    width: str = ""
    height: str = ""


def manifest_path(area: str) -> Path:
    return settings().manifest_root / f"{area}.csv"


def load(area: str) -> dict[str, Entry]:
    p = manifest_path(area)
    if not p.exists():
        return {}
    with p.open(encoding="utf-8", newline="") as f:
        return {r["key"]: Entry(r["key"], int(r["bytes"]), r["sha256"], r["width"], r["height"])
                for r in csv.DictReader(f)}


def load_all() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    for a in AREAS:
        out.update(load(a))
    return out


def save(area: str, entries: dict[str, Entry]) -> None:
    p = manifest_path(area)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(FIELDS)
        for k in sorted(entries):
            e = entries[k]
            w.writerow([e.key, e.bytes, e.sha256, e.width, e.height])


def area_of(key: str) -> str:
    area = key.split("/", 1)[0]
    if area not in AREAS:
        raise ValueError(f"asset key must start with one of {AREAS}: {key}")
    return area


def local_files(area: str):
    base = layout.asset(area)
    if not base.exists():
        return
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.name not in IGNORED_NAMES:
            yield p


def scan(area: str, previous: dict[str, Entry] | None = None) -> dict[str, Entry]:
    """Hash the local asset tree for ``area``; image dimensions are reused when the hash is unchanged."""
    previous = previous or {}
    out: dict[str, Entry] = {}
    for p in local_files(area):
        key = layout.key_of(p)
        digest = sha256_file(p)
        prev = previous.get(key)
        if prev and prev.sha256 == digest:
            out[key] = prev
            continue
        w = h = ""
        if p.suffix.lower() in IMAGE_EXT:
            try:
                with Image.open(p) as im:
                    w, h = str(im.width), str(im.height)
            except OSError:
                pass
        out[key] = Entry(key, p.stat().st_size, digest, w, h)
    return out


def diff(old: dict[str, Entry], new: dict[str, Entry]) -> tuple[list[str], list[str], list[str]]:
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(k for k in set(old) & set(new) if old[k].sha256 != new[k].sha256)
    return added, removed, changed
