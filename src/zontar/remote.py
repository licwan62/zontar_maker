"""Remote asset stores: NAS (any mounted / UNC folder) and Aliyun OSS.

The manifest (git) says *which bytes* each key should have; the remote holds them.

* ``push``: upload every manifest entry whose remote copy is missing or different.
* ``pull``: download every manifest entry that is missing or different locally.

Nothing is ever deleted on either side by sync.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from . import layout, manifest
from .config import settings
from .hashing import sha256_file


class Remote:
    name = "remote"

    def state(self, e: manifest.Entry, verify: bool = False) -> str:
        """'missing' | 'same' | 'different'."""
        raise NotImplementedError

    def upload(self, local: Path, e: manifest.Entry) -> None:
        raise NotImplementedError

    def download(self, e: manifest.Entry, dest: Path) -> None:
        raise NotImplementedError

    def url(self, key: str) -> str:
        raise NotImplementedError


class NasRemote(Remote):
    name = "nas"

    def __init__(self, root: str):
        self.root = Path(root)

    def _p(self, key: str) -> Path:
        return self.root / PurePosixPath(key)

    def state(self, e, verify=False):
        p = self._p(e.key)
        if not p.exists():
            return "missing"
        if p.stat().st_size != e.bytes:
            return "different"
        if verify and sha256_file(p) != e.sha256:
            return "different"
        return "same"

    def upload(self, local, e):
        dest = self._p(e.key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        shutil.copy2(local, tmp)
        os.replace(tmp, dest)

    def download(self, e, dest):
        shutil.copy2(self._p(e.key), dest)

    def url(self, key):
        return str(self._p(key))


class OssRemote(Remote):
    """Aliyun OSS. Needs `pip install oss2` and env OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET.

    Each object carries its sha256 in metadata (x-oss-meta-sha256) so state checks
    never need to download content.
    """
    name = "oss"
    META = "x-oss-meta-sha256"

    def __init__(self, cfg: dict):
        try:
            import oss2
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise SystemExit("OSS backend needs the optional dependency: pip install -e .[oss]") from exc
        key_id = os.environ.get("OSS_ACCESS_KEY_ID")
        secret = os.environ.get("OSS_ACCESS_KEY_SECRET")
        if not key_id or not secret:
            raise SystemExit("Set OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET in the environment.")
        self.oss2 = oss2
        self.bucket = oss2.Bucket(oss2.Auth(key_id, secret), cfg["endpoint"], cfg["bucket"])
        self.prefix = cfg.get("prefix", "")
        self.public_base_url = cfg.get("public_base_url", "")

    def _k(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def state(self, e, verify=False):
        try:
            head = self.bucket.head_object(self._k(e.key))
        except self.oss2.exceptions.NotFound:
            return "missing"
        return "same" if head.headers.get(self.META) == e.sha256 else "different"

    def upload(self, local, e):
        self.oss2.resumable_upload(self.bucket, self._k(e.key), str(local), headers={self.META: e.sha256})

    def download(self, e, dest):
        self.oss2.resumable_download(self.bucket, self._k(e.key), str(dest))

    def url(self, key):
        if self.public_base_url:
            return self.public_base_url.rstrip("/") + "/" + quote(key)
        return self.bucket.sign_url("GET", self._k(key), 3600)


def get_remote() -> Remote:
    s = settings()
    if s.remote_backend == "nas":
        return NasRemote(s.remote["nas"]["root"])
    if s.remote_backend == "oss":
        return OssRemote(s.remote["oss"])
    raise SystemExit("No remote configured: set [remote] backend in config/storage.local.toml or ZONTAR_REMOTE.")


def _selected(prefix: str) -> list[manifest.Entry]:
    return [e for k, e in sorted(manifest.load_all().items()) if k.startswith(prefix)]


def push(prefix: str = "", dry_run: bool = False, verify: bool = False) -> dict[str, int]:
    remote = get_remote()
    stats = {"uploaded": 0, "same": 0, "stale_manifest": 0}
    for e in _selected(prefix):
        local = layout.asset(e.key)
        if not local.exists() or local.stat().st_size != e.bytes or sha256_file(local) != e.sha256:
            print(f"[stale] local file does not match manifest, run `zontar manifest` first: {e.key}")
            stats["stale_manifest"] += 1
            continue
        if remote.state(e, verify) == "same":
            stats["same"] += 1
            continue
        print(f"[push] {e.key}")
        if not dry_run:
            remote.upload(local, e)
        stats["uploaded"] += 1
    return stats


def pull(prefix: str = "", dry_run: bool = False) -> dict[str, int]:
    remote = get_remote()
    stats = {"downloaded": 0, "same": 0, "missing_remote": 0}
    for e in _selected(prefix):
        local = layout.asset(e.key)
        if local.exists() and local.stat().st_size == e.bytes and sha256_file(local) == e.sha256:
            stats["same"] += 1
            continue
        if remote.state(e) == "missing":
            print(f"[missing on remote] {e.key}")
            stats["missing_remote"] += 1
            continue
        print(f"[pull] {e.key}")
        stats["downloaded"] += 1
        if dry_run:
            continue
        local.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=local.parent, suffix=".part")
        os.close(fd)
        tmp_path = Path(tmp)
        try:
            remote.download(e, tmp_path)
            if sha256_file(tmp_path) != e.sha256:
                raise RuntimeError(f"sha256 mismatch after download: {e.key}")
            os.replace(tmp_path, local)
        finally:
            tmp_path.unlink(missing_ok=True)
    return stats
