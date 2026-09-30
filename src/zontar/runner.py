"""Run a vehicle pipeline end to end, and report where every vehicle stands.

Steps are the files ``pipelines/<slug>/NN_*.py|mjs`` in numeric order, followed by
``pack`` and a manifest refresh. Every step runs in a fresh process with the repo's
``src`` on PYTHONPATH and UTF-8 I/O, from any working directory, so another agent
(Codex, Claude Code, a human) can resume from any step with ``--from NN``.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import backgrounds, layout, manifest, pack, tables
from .config import settings

STEP_RE = re.compile(r"^(\d{2})_.+\.(py|mjs)$")


def steps(slug: str) -> list[Path]:
    d = settings().repo_root / "pipelines" / slug
    if not d.is_dir():
        raise SystemExit(f"no pipeline folder: {d}")
    return sorted(p for p in d.iterdir() if STEP_RE.match(p.name))


def _env() -> dict[str, str]:
    env = dict(os.environ)
    src = str(settings().repo_root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _node_has_artifact_tool() -> bool:
    if not shutil.which("node"):
        return False
    r = subprocess.run(["node", "-e", "import('@oai/artifact-tool').then(()=>process.exit(0),()=>process.exit(1))"],
                       cwd=settings().repo_root, capture_output=True)
    return r.returncode == 0


def run(slug: str, start: int | None = None, stop: int | None = None, force: bool = False,
        skip_pack: bool = False) -> int:
    reg = layout.vehicle_registry()
    if slug not in reg:
        raise SystemExit(f"unknown vehicle {slug!r}; registered: {', '.join(reg)}")
    sandboxed = bool(os.environ.get("ZONTAR_ASSET_ROOT"))
    if reg[slug]["status"] == "delivered" and not force and not sandboxed:
        raise SystemExit(
            f"{slug} is marked delivered: re-running would overwrite delivered images.\n"
            "Use a sandbox (set ZONTAR_ASSET_ROOT and ZONTAR_DATA_ROOT to copies) or pass --force.")
    mjs_ok = None
    for p in steps(slug):
        n = int(STEP_RE.match(p.name).group(1))
        if (start is not None and n < start) or (stop is not None and n > stop):
            continue
        if p.suffix == ".mjs":
            mjs_ok = _node_has_artifact_tool() if mjs_ok is None else mjs_ok
            if not mjs_ok:
                print(f"[skip] {p.name}: needs node + @oai/artifact-tool (not available here)")
                continue
            cmd = ["node", str(p)]
        else:
            cmd = [sys.executable, str(p)]
        print(f"[run ] {p.relative_to(settings().repo_root).as_posix()}", flush=True)
        t = time.time()
        r = subprocess.run(cmd, env=_env(), cwd=settings().repo_root)
        if r.returncode:
            print(f"[fail] {p.name} exited {r.returncode}. Fix it, then resume with: python run.py run {slug} --from {n:02d}")
            return r.returncode
        print(f"[ ok ] {p.name} ({time.time() - t:.1f}s)", flush=True)
    if not skip_pack:
        print(f"[pack] {pack.build(slug)}")
        for area in ("inputs", "outputs"):
            manifest.save(area, manifest.scan(area, manifest.load(area)))
        print("[ ok ] manifests/inputs.csv, manifests/outputs.csv refreshed")
    return 0


# --- status ------------------------------------------------------------------------
def _newest(paths) -> float:
    return max((p.stat().st_mtime for p in paths if p.is_file()), default=0.0)


def vehicle_status(slug: str) -> dict:
    reg = layout.vehicle_registry()[slug]
    v = layout.vehicle(slug)
    st: dict = {"slug": slug, "status": reg["status"], "todo": []}

    skus_csv = v.data_dir / "inputs" / "skus.csv"
    if skus_csv.exists():
        need = [r["base_image"] for r in tables.read_csv(skus_csv)]
        missing = [n for n in need if not (v.source / n).exists()]
        st["source_photos"] = f"{len(need) - len(missing)}/{len(need)}"
        if missing:
            prompts = v.data_dir / "inputs" / "source_prompts.csv"
            st["todo"].append(f"generate source photos {missing} into {layout.key_of(v.source) if v.source.exists() else v.source} "
                              + (f"(prompts: {backgrounds._rel(prompts)})" if prompts.exists() else ""))
    else:
        st["source_photos"] = f"{len(list(v.source.glob('*.png'))) if v.source.exists() else 0} files (legacy script)"

    report = v.package.parent / "render_report.json"
    if report.exists():
        drafts = json.loads(report.read_text(encoding="utf-8")).get("drafts", [])
        st["draft_images"] = bool(drafts)
        if drafts:
            st["todo"].append("images carry DRAFT watermark: " + "; ".join(drafts))

    listing = list(v.data_dir.glob("*上架内容.csv"))
    st["listing_csv"] = listing[0].name if listing else None
    if not listing:
        st["todo"].append("listing CSV missing")

    pkg_files = [p for p in v.package.rglob("*") if p.is_file()] if v.package.exists() else []
    st["package_files"] = len(pkg_files)
    data_files = [p for p in v.data_dir.iterdir() if p.is_file()] if v.data_dir.exists() else []
    if not v.zip_path.exists():
        st["zip"] = "missing"
        st["todo"].append(f"python run.py pack {slug}")
    else:
        stale = _newest(pkg_files + data_files) > v.zip_path.stat().st_mtime
        st["zip"] = "stale" if stale else "current"
        if stale:
            st["todo"].append(f"zip older than its contents: python run.py pack {slug}")

    if backgrounds.vehicle_csv(v).exists():
        bindings = tables.read_csv(backgrounds.vehicle_csv(v))
        index = backgrounds.load_index()
        ready = sum(backgrounds.is_ready(index.get(b.get("background_id", ""))) for b in bindings)
        st["backgrounds"] = f"{ready}/{len(bindings)} ready"
        st["todo"] += backgrounds.todo(slug)

    req = v.data_dir / "inputs" / "image_requests.csv"
    if req.exists():
        cands = tables.read_csv(v.data_dir / "inputs" / "image_candidates.csv") if (v.data_dir / "inputs" / "image_candidates.csv").exists() else []
        n_req = len(tables.read_csv(req))
        approved = [c for c in cands if c.get("status") == "approved"]
        st["image_scout"] = f"{n_req} requests, {len(cands)} candidates, {len(approved)} approved"
        if not cands:
            st["todo"].append("run the vehicle image scout (docs/agents/vehicle-image-scout.md)")
        elif not approved:
            st["todo"].append("human review: approve one candidate per SKU in inputs/image_candidates.csv")
    return st


def quick_manifest_drift() -> dict[str, int]:
    """Cheap drift check (keys and sizes only, no hashing)."""
    out = {}
    for area in manifest.AREAS:
        old = manifest.load(area)
        local = {layout.key_of(p): p.stat().st_size for p in manifest.local_files(area)}
        drift = set(old) ^ set(local) | {k for k in set(old) & set(local) if old[k].bytes != local[k]}
        out[area] = len(drift)
    return out


def status(as_json: bool = False) -> int:
    s = settings()
    report = {
        "asset_root": str(s.asset_root),
        "remote": s.remote_backend,
        "missing_shared_inputs": [str(layout.key_of(p)) for p in (layout.brand_logo(), layout.brand_icons()) if not p.exists()]
        + [f"inputs/spreadsheets/{n}" for n in ("汽车罩官方上架模板.xlsx", "Ozon上架链接汇总_两店对应完成.xlsx")
           if not layout.input_spreadsheet(n).exists()],
        "node_artifact_tool": _node_has_artifact_tool(),
        "manifest_drift": quick_manifest_drift(),
        "vehicles": [vehicle_status(slug) for slug in layout.vehicle_registry()],
    }
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    print(f"asset root : {report['asset_root']}  (remote: {report['remote']})")
    print(f"shared inputs missing: {report['missing_shared_inputs'] or 'none'}")
    print(f".mjs steps runnable  : {report['node_artifact_tool']}")
    drift = report["manifest_drift"]
    print(f"manifest drift (files): {drift}" + ("  -> python run.py manifest" if any(drift.values()) else ""))
    for vs in report["vehicles"]:
        print(f"\n[{vs['status']:9}] {vs['slug']}")
        for k in ("source_photos", "draft_images", "listing_csv", "package_files", "zip", "backgrounds", "image_scout"):
            if k in vs:
                print(f"    {k:14} {vs[k]}")
        for t in vs["todo"]:
            print(f"    TODO  {t}")
    return 0
