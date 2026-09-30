"""`python -m zontar <command>` / `zontar <command>`.

    paths [--vehicle SLUG] [--json]   show resolved locations (used by the .mjs pipelines)
    doctor                            check inputs, fonts and remote configuration
    tables convert KEY CSV_DIR        convert one .xlsx asset into data/CSV_DIR/*.csv
    tables sync [--force]             re-convert every registered workbook whose source changed
    manifest [--check]                re-hash the asset tree into manifests/*.csv
    sync push|pull [--prefix P]       mirror assets to/from the NAS or OSS remote
    url KEY                           public/signed URL of an asset on the remote
    pack SLUG | --all                 zip a vehicle package into outputs/vehicles/SLUG/dist/
    run SLUG [--from NN] [--to NN]    run pipelines/SLUG/NN_* in order, then pack + manifest
    status [--json]                   what is done / missing / next for every vehicle
    styles [--json]                   list selectable vehicle-image themes
    bg list|scenes                    background library index / available scenes
    bg request --theme T|--scene S [--vehicle SLUG]   on-demand prompt for a theme background
    bg prompt ID                      print the generation prompt of a background
    bg register ID IMAGE              store a generated image (normalised to 1086x1448) + QA
    bg approve|reject ID [--note N]   human review; only approved backgrounds are used
    bg resolve SLUG --theme T         bind backgrounds for a vehicle (the NN_background step)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import layout, manifest, pack, tables, themes
from .config import settings

FONT_DIR = Path(os.environ.get("ZONTAR_FONT_DIR") or Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts")
REQUIRED_FONTS = ["arial.ttf", "arialbd.ttf", "ariblk.ttf", "impact.ttf", "tahoma.ttf", "tahomabd.ttf"]


def _paths(args) -> int:
    s = settings()
    out: dict = {
        "repo_root": str(s.repo_root),
        "asset_root": str(s.asset_root),
        "data_root": str(s.data_root),
        "remote_backend": s.remote_backend,
        "brand_logo": str(layout.brand_logo()),
        "brand_icons": str(layout.brand_icons()),
        "official_template": str(layout.input_spreadsheet("汽车罩官方上架模板.xlsx")),
        "listing_summary": str(layout.input_spreadsheet("Ozon上架链接汇总_两店对应完成.xlsx")),
        "tag_bank": str(layout.input_spreadsheet("汽车车罩标签词 - 副本.xlsx")),
        # write-back candidates of the summary workbook; convert to CSV with `zontar tables convert`
        "listing_summary_candidates": str(layout.asset("outputs/listing_summary")),
        # QA screenshots produced by listing scripts
        "reports": str(layout.asset("outputs/reports")),
    }
    if args.vehicle:
        v = layout.vehicle(args.vehicle)
        out["vehicle"] = {k: str(getattr(v, k)) for k in (
            "source", "candidates", "package", "main", "fitment", "selector", "info", "preview",
            "gallery", "aplus_pc", "aplus_mobile", "dist", "zip_path", "data_dir")} | {
            "slug": v.slug, "package_name": v.package_name}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for k, v in out.items():
            print(f"{k:18} {v}")
    return 0


def _doctor(_args) -> int:
    s = settings()
    problems = 0

    def check(ok: bool, label: str, hint: str = "") -> None:
        nonlocal problems
        print(f"[{'ok' if ok else 'MISSING'}] {label}" + ("" if ok else f"  -> {hint}"))
        problems += 0 if ok else 1

    check(s.asset_root.exists(), f"asset root {s.asset_root}", "create it or pull from the remote")
    check(layout.brand_logo().exists(), f"brand logo {layout.key_of(layout.brand_logo()) if s.asset_root.exists() else ''}",
          "copy the Tozaroa logo PNG (was C:\\Users\\Lenovo\\Desktop\\exec-d3683c74-....png) here")
    check(layout.brand_icons().exists(), "brand icon sprite", "pull from remote")
    for name, why in [("汽车罩官方上架模板.xlsx", "needed by */30_build_listing.mjs"),
                      ("Ozon上架链接汇总_两店对应完成.xlsx", "live summary workbook, needed by summary sync steps")]:
        check(layout.input_spreadsheet(name).exists(), f"inputs/spreadsheets/{name}", why)
    for font in REQUIRED_FONTS:
        check((FONT_DIR / font).exists(), f"font {font}", "install the Windows core font")
    for slug in layout.vehicle_registry():
        v = layout.vehicle(slug)
        check(v.source.exists(), f"{slug}: source images", f"expected at {v.source}")
    if s.remote_backend == "oss":
        check(bool(os.environ.get("OSS_ACCESS_KEY_ID")), "OSS credentials in env", "set OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET")
    print(f"remote backend: {s.remote_backend}")
    return 1 if problems else 0


def _tables(args) -> int:
    if args.action == "convert":
        changed = tables.convert(args.key, args.csv_dir, force=True)
        print(("converted " if changed else "unchanged ") + args.csv_dir)
    else:
        for d in tables.sync_all(force=args.force):
            print(f"converted {d}")
    return 0


def _manifest(args) -> int:
    stale = False
    for area in manifest.AREAS:
        old = manifest.load(area)
        new = manifest.scan(area, old)
        added, removed, changed = manifest.diff(old, new)
        if added or removed or changed:
            stale = True
            print(f"{area}: +{len(added)} -{len(removed)} ~{len(changed)}")
            for k in (added + changed)[:20]:
                print(f"   {k}")
        if not args.check:
            manifest.save(area, new)
    if args.check and stale:
        print("manifests are stale: run `zontar manifest`")
        return 1
    return 0


def _sync(args) -> int:
    from . import remote
    fn = remote.push if args.direction == "push" else remote.pull
    kwargs = {"prefix": args.prefix, "dry_run": args.dry_run}
    if args.direction == "push":
        kwargs["verify"] = args.verify
    print(fn(**kwargs))
    return 0


def _url(args) -> int:
    from . import remote
    print(remote.get_remote().url(args.key))
    return 0


def _pack(args) -> int:
    slugs = list(layout.vehicle_registry()) if args.all else [args.slug]
    for slug in slugs:
        print(pack.build(slug))
    return 0


def _styles(args) -> int:
    items = [theme.to_dict() for theme in themes.list_styles()]
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    for theme in themes.list_styles():
        print(f"{theme.id:18} {theme.name}")
        print(f"{'':18} {theme.best_for}")
        print(f"{'':18} reference: {theme.reference_preview}")
    return 0


def _bg(args) -> int:
    from . import backgrounds as bg
    if args.action == "list":
        for bid, r in bg.load_index().items():
            print(f"{bid:28} {r['status']:9} {r['usage']:14} theme={r['theme'] or '-'} vehicle={r['vehicle'] or '-'} qa={r['qa'] or '-'}")
    elif args.action == "scenes":
        for sid, r in bg.scenes().items():
            print(f"{sid:20} {r['name']}  ({r['notes']})")
    elif args.action == "request":
        if not (args.theme or args.scene):
            raise SystemExit("bg request needs --theme or --scene")
        r = bg.request(args.scene or "", args.theme or "", args.vehicle or "", note=args.note or "")
        print(f"requested {r['background_id']}: prompt {bg.prompt_path(r['background_id'])}")
    elif args.action == "prompt":
        print(bg.prompt_path(args.id).read_text(encoding="utf-8"))
    elif args.action == "register":
        r = bg.register(args.id, Path(args.image), args.source or "", args.license or "", args.usage or "")
        print(f"registered {args.id} -> {bg.image_path(args.id)}  qa: {r['qa']}")
    elif args.action in ("approve", "reject"):
        r = bg.set_status(args.id, args.action + "d" if args.action == "approve" else "rejected", args.note or "")
        print(f"{args.id}: {r['status']}")
    elif args.action == "resolve":
        for b in bg.resolve_vehicle(args.slug, args.theme):
            print(f"sku {b['sku']:4} {b['background_id']:28} {b['state']:10} ({b['action']})")
        for t in bg.todo(args.slug):
            print(f"TODO  {t}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="zontar", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("paths"); sp.add_argument("--vehicle"); sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=_paths)
    sub.add_parser("doctor").set_defaults(fn=_doctor)

    sp = sub.add_parser("tables"); tsub = sp.add_subparsers(dest="action", required=True)
    c = tsub.add_parser("convert"); c.add_argument("key"); c.add_argument("csv_dir")
    s_ = tsub.add_parser("sync"); s_.add_argument("--force", action="store_true")
    sp.set_defaults(fn=_tables)

    sp = sub.add_parser("manifest"); sp.add_argument("--check", action="store_true"); sp.set_defaults(fn=_manifest)

    sp = sub.add_parser("sync"); sp.add_argument("direction", choices=["push", "pull"])
    sp.add_argument("--prefix", default=""); sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--verify", action="store_true", help="NAS push: compare sha256, not just size")
    sp.set_defaults(fn=_sync)

    sp = sub.add_parser("url"); sp.add_argument("key"); sp.set_defaults(fn=_url)

    sp = sub.add_parser("pack"); g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("slug", nargs="?"); g.add_argument("--all", action="store_true"); sp.set_defaults(fn=_pack)

    sp = sub.add_parser("run"); sp.add_argument("slug")
    sp.add_argument("--from", dest="start", type=int); sp.add_argument("--to", dest="stop", type=int)
    sp.add_argument("--force", action="store_true", help="allow re-running a delivered vehicle in place")
    sp.add_argument("--skip-pack", action="store_true")
    sp.set_defaults(fn=lambda a: __import__("zontar.runner", fromlist=["run"]).run(a.slug, a.start, a.stop, a.force, a.skip_pack))
    sp = sub.add_parser("status"); sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=lambda a: __import__("zontar.runner", fromlist=["status"]).status(a.json))
    sp = sub.add_parser("styles"); sp.add_argument("--json", action="store_true"); sp.set_defaults(fn=_styles)

    sp = sub.add_parser("bg"); bsub = sp.add_subparsers(dest="action", required=True)
    bsub.add_parser("list"); bsub.add_parser("scenes")
    c = bsub.add_parser("request"); c.add_argument("--theme"); c.add_argument("--scene")
    c.add_argument("--vehicle"); c.add_argument("--note")
    bsub.add_parser("prompt").add_argument("id")
    c = bsub.add_parser("register"); c.add_argument("id"); c.add_argument("image")
    c.add_argument("--source", help="default imagegen"); c.add_argument("--license", help="default ai_generated")
    c.add_argument("--usage", choices=["direct", "reference_only"])
    for name in ("approve", "reject"):
        c = bsub.add_parser(name); c.add_argument("id"); c.add_argument("--note")
    c = bsub.add_parser("resolve"); c.add_argument("slug"); c.add_argument("--theme", required=True)
    sp.set_defaults(fn=_bg)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
