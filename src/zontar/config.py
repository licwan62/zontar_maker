"""Resolve repo root, asset root and remote settings.

Precedence (highest first): environment variables, config/storage.local.toml,
config/storage.toml. Env vars: ZONTAR_ASSET_ROOT, ZONTAR_REMOTE, ZONTAR_DATA_ROOT.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    asset_root: Path
    remote_backend: str
    remote: dict = field(default_factory=dict)
    data_override: Path | None = None

    @property
    def data_root(self) -> Path:
        return self.data_override or self.repo_root / "data"

    @property
    def manifest_root(self) -> Path:
        return self.repo_root / "manifests"


@lru_cache(maxsize=1)
def settings() -> Settings:
    raw: dict = {}
    for name in ("storage.toml", "storage.local.toml"):
        p = REPO_ROOT / "config" / name
        if p.exists():
            raw = _merge(raw, tomllib.loads(p.read_text(encoding="utf-8")))

    asset_root = Path(os.environ.get("ZONTAR_ASSET_ROOT") or raw.get("local", {}).get("asset_root", "assets"))
    if not asset_root.is_absolute():
        asset_root = REPO_ROOT / asset_root
    remote = raw.get("remote", {})
    backend = os.environ.get("ZONTAR_REMOTE") or remote.get("backend", "none")
    data_override = os.environ.get("ZONTAR_DATA_ROOT")  # for dry runs / tests
    return Settings(REPO_ROOT, asset_root, backend, remote, Path(data_override) if data_override else None)
