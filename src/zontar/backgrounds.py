"""Background node: on-demand environment backgrounds for vehicle image themes.

Images are generated outside Python (the agent's built-in imagegen, or a human), so
this node never calls an image API. It does the bookkeeping around generation:

* ``request``  - render the prompt (``data/backgrounds/prompt_template.md`` filled with a
  scene from ``data/backgrounds/scenes.csv``) into ``data/backgrounds/prompts/<id>.md``
  and add a ``requested`` row to the library index ``data/backgrounds.csv``.
* ``register`` - validate a generated image (3:4, normalised to 1086x1448 RGB), store it at
  ``assets/inputs/background_library/<id>.png`` and run a cheap layout QA.
* ``approve`` / ``reject`` - human review; only ``approved`` + ``usage=direct`` rows are usable.
* ``resolve_vehicle`` - the pipeline step. Reads ``data/vehicles/<slug>/inputs/backgrounds.csv``
  (``sku,mode,scene,background_id,seed,notes``), picks or requests a background per row
  and writes the chosen ``background_id`` back, so re-runs never re-roll.

Modes: ``fixed`` (use background_id as given), ``random`` (seeded pick from approved
backgrounds of the scene; requests one if the pool is empty), ``generate`` (always a
dedicated new background). A bound background that was rejected is replaced on the
next run (random/generate only). See docs/BACKGROUND_LIBRARY.md.
"""
from __future__ import annotations

import random
from datetime import date
from pathlib import Path

from PIL import Image, ImageStat

from . import layout, tables, themes
from .config import settings
from .hashing import sha256_file

WIDTH, HEIGHT = 1086, 1448
RATIO_TOLERANCE = 0.02
INDEX_FIELDS = ["background_id", "scene_id", "theme", "vehicle", "width", "height", "file", "source",
                "license", "usage", "status", "sha256", "qa", "requested", "notes"]
VEHICLE_FIELDS = ["sku", "mode", "scene", "background_id", "seed", "notes"]
MODES = ("fixed", "random", "generate")
STATUSES = ("requested", "generated", "approved", "rejected")

# body_type (data/vehicles.csv) -> (platform capacity wording, body noun)
BODY_WORDS = {
    "越野车": ("中型 SUV / Crossover", "SUV"),
    "三厢车/旅行车": ("中型轿车 / 旅行车", "轿车"),
}


# --- locations -------------------------------------------------------------------
def _dir() -> Path:
    return layout.data_root() / "backgrounds"


def index_path() -> Path:
    return layout.data_root() / "backgrounds.csv"


def prompt_path(bg_id: str) -> Path:
    return _dir() / "prompts" / f"{bg_id}.md"


def image_path(bg_id: str) -> Path:
    return layout.background_library() / f"{bg_id}.png"


def vehicle_csv(v: layout.Vehicle) -> Path:
    return v.data_dir / "inputs" / "backgrounds.csv"


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(settings().repo_root.resolve()).as_posix()
    except ValueError:
        return str(p)


# --- tables ----------------------------------------------------------------------
def scenes() -> dict[str, dict[str, str]]:
    return {r["scene_id"]: r for r in tables.read_csv(_dir() / "scenes.csv")}


def load_index() -> dict[str, dict[str, str]]:
    p = index_path()
    return {r["background_id"]: r for r in tables.read_csv(p)} if p.exists() else {}


def save_index(index: dict[str, dict[str, str]]) -> None:
    rows = [INDEX_FIELDS] + [[r.get(k, "") for k in INDEX_FIELDS] for _, r in sorted(index.items())]
    tables.write_csv(index_path(), rows)


def _get(index: dict[str, dict[str, str]], bg_id: str) -> dict[str, str]:
    if bg_id not in index:
        raise SystemExit(f"unknown background {bg_id!r}; see `python run.py bg list`")
    return index[bg_id]


# --- prompt ----------------------------------------------------------------------
def _scene(scene_id: str) -> dict[str, str]:
    table = scenes()
    if scene_id not in table:
        raise SystemExit(f"unknown scene {scene_id!r}; choose one of: {', '.join(table)} (data/backgrounds/scenes.csv)")
    return table[scene_id]


def theme_scene(style: str) -> str:
    theme = themes.THEMES.get(themes.resolve_style(style))
    if not theme or not theme.background_scene:
        raise SystemExit(f"theme {style!r} has no default background scene; pass a scene explicitly")
    return theme.background_scene


def render_prompt(scene_id: str, vehicle: str = "") -> str:
    """Fill the template. ``vehicle`` is a registry slug; empty = generic mid-size SUV."""
    values = dict(_scene(scene_id))
    body_class, body_noun = BODY_WORDS["越野车"]
    fit, forbidden_brand = f"中型 {body_noun}", ""
    if vehicle:
        reg = layout.vehicle_registry()[vehicle]
        body_class, body_noun = BODY_WORDS.get(reg["body_type"], BODY_WORDS["越野车"])
        fit = f" {reg['brand']} {reg['model']} 尺寸的 {body_noun}"
        forbidden_brand = f"{reg['brand']} 标志、"
    values |= {"width": str(WIDTH), "height": str(HEIGHT), "vehicle_class": f"{body_class} ",
               "vehicle_fit": fit, "vehicle_view": f"前左 3/4 视角的 {body_noun}",
               "forbidden_brand": forbidden_brand}
    text = (_dir() / "prompt_template.md").read_text(encoding="utf-8")
    for k, val in values.items():
        text = text.replace("{{" + k + "}}", val)
    if "{{" in text:
        raise SystemExit("prompt template has unfilled placeholders: " + text[text.index("{{"):][:40])
    return text


def _references(style: str, vehicle: str) -> list[str]:
    refs = []
    theme = themes.THEMES.get(themes.resolve_style(style)) if style else None
    if theme and layout.asset(theme.reference_preview).exists():
        refs.append(f"assets/{theme.reference_preview}（主题版式参考）")
    if vehicle:
        v = layout.vehicle(vehicle)
        refs += [f"assets/{layout.key_of(p)}（当前主图，参考标题区与车身占比）" for p in sorted(v.main.glob("*.png"))[:1]]
    return refs


def _next_id(index: dict[str, dict[str, str]], scene_id: str) -> str:
    n = 1
    while f"bg_{scene_id}_{n:03d}" in index:
        n += 1
    return f"bg_{scene_id}_{n:03d}"


def request(scene_id: str = "", style: str = "", vehicle: str = "", note: str = "") -> dict[str, str]:
    """Create a generation request for a theme (and optionally a vehicle). Returns the index row."""
    scene_id = scene_id or theme_scene(style)
    prompt = render_prompt(scene_id, vehicle)
    index = load_index()
    bg_id = _next_id(index, scene_id)
    refs = _references(style, vehicle)
    header = [f"# {bg_id} 背景生图请求", "",
              f"- 场景：`{scene_id}` {_scene(scene_id)['name']}",
              f"- 主题：`{style or '-'}`；车型：`{vehicle or '-'}`",
              f"- 输出：{WIDTH}×{HEIGHT} px 竖版 PNG，仅环境背景",
              "- 参考图（只借鉴版式结构，不复制其中车辆、文字或 Logo）：" + ("" if refs else "无"),
              *[f"  - {r}" for r in refs],
              f"- 生成后登记：`python run.py bg register {bg_id} <生成的图片>`，目视通过后 `python run.py bg approve {bg_id}`",
              "", "---", "", ""]
    p = prompt_path(bg_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(header) + prompt, encoding="utf-8", newline="\n")
    row = {"background_id": bg_id, "scene_id": scene_id, "theme": themes.resolve_style(style) if style else "",
           "vehicle": vehicle, "width": str(WIDTH), "height": str(HEIGHT), "file": f"inputs/background_library/{bg_id}.png",
           "source": "imagegen", "license": "ai_generated", "usage": "direct", "status": "requested",
           "sha256": "", "qa": "", "requested": f"{date.today():%Y-%m-%d}", "notes": note}
    index[bg_id] = row
    save_index(index)
    return row


# --- register / review ----------------------------------------------------------------
def qa(img: Image.Image) -> list[str]:
    """Layout warnings for a 3:4 background (title zone on top, platform at the bottom)."""
    g = img.convert("L").resize((WIDTH // 4, HEIGHT // 4))
    w, h = g.size
    top = ImageStat.Stat(g.crop((0, 0, w, int(h * 0.38))))
    bottom = ImageStat.Stat(g.crop((0, int(h * 0.55), w, h)))
    warnings = []
    if ImageStat.Stat(g).stddev[0] < 5:
        warnings.append("画面几乎纯色")
    if top.mean[0] >= 247 and top.stddev[0] < 3:
        warnings.append("上方标题区接近纯白空白")
    if top.stddev[0] > 55:
        warnings.append("上方标题区对比过强，可能干扰文字")
    if bottom.stddev[0] < 8:
        warnings.append("下方平台区过于单调")
    return warnings


def _normalise(src: Path) -> tuple[Image.Image, list[str]]:
    img = Image.open(src)
    img.load()
    notes = []
    if img.mode != "RGB":
        if "A" in img.getbands() and img.getchannel("A").getextrema()[0] < 255:
            raise SystemExit(f"{src}: background must be opaque (found transparent pixels)")
        img = img.convert("RGB")
    w, h = img.size
    if abs((w / h) / (WIDTH / HEIGHT) - 1) > RATIO_TOLERANCE:
        raise SystemExit(f"{src}: {w}x{h} is not 3:4 portrait; regenerate at {WIDTH}x{HEIGHT}")
    if (w, h) != (WIDTH, HEIGHT):
        target_w = min(w, round(h * WIDTH / HEIGHT))
        target_h = min(h, round(w * HEIGHT / WIDTH))
        left, top = (w - target_w) // 2, (h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h)).resize((WIDTH, HEIGHT), Image.LANCZOS)
        notes.append(f"由 {w}x{h} 居中裁切缩放" + ("（放大，注意清晰度）" if w < WIDTH else ""))
    return img, notes


def register(bg_id: str, src: Path, source: str = "", license_: str = "", usage: str = "") -> dict[str, str]:
    index = load_index()
    row = _get(index, bg_id)
    img, notes = _normalise(src)
    dst = image_path(bg_id)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        layout.backup_before_overwrite([dst.parent], f"background_{bg_id}")
    img.save(dst, optimize=True)
    row.update({"status": "generated", "sha256": sha256_file(dst), "qa": "; ".join(qa(img)) or "ok",
                "width": str(WIDTH), "height": str(HEIGHT)})
    for key, val in (("source", source), ("license", license_), ("usage", usage)):
        if val:
            row[key] = val
    if notes:
        row["notes"] = "; ".join(filter(None, [row.get("notes", ""), *notes]))
    save_index(index)
    return row


def set_status(bg_id: str, status: str, note: str = "") -> dict[str, str]:
    index = load_index()
    row = _get(index, bg_id)
    if status == "approved" and not image_path(bg_id).exists():
        raise SystemExit(f"{bg_id}: no image yet; register it first")
    row["status"] = status
    if note:
        row["notes"] = "; ".join(filter(None, [row.get("notes", ""), note]))
    save_index(index)
    return row


def is_ready(row: dict[str, str] | None) -> bool:
    return bool(row) and row["status"] == "approved" and row["usage"] == "direct" and image_path(row["background_id"]).exists()


# --- pipeline step -------------------------------------------------------------------
def resolve_vehicle(slug: str, style: str) -> list[dict[str, str]]:
    """Bind a background to every row of the vehicle's backgrounds.csv; request missing ones.

    Returns one dict per row: sku, background_id, state (ready/generated/requested/missing), action.
    A vehicle without backgrounds.csv does not use the node and gets an empty list.
    """
    v = layout.vehicle(slug)
    path = vehicle_csv(v)
    if not path.exists():
        return []
    rows = tables.read_csv(path)
    index = load_index()
    out = []
    for r in rows:
        mode = r.get("mode") or "generate"
        if mode not in MODES:
            raise SystemExit(f"{_rel(path)}: sku {r['sku']}: mode must be one of {MODES}")
        scene_id = r.get("scene") or theme_scene(style)
        bg_id = r.get("background_id", "")
        action = "kept"
        if bg_id and bg_id not in index:
            raise SystemExit(f"{_rel(path)}: sku {r['sku']}: unknown background {bg_id!r}")
        if bg_id and index[bg_id]["status"] == "rejected" and mode != "fixed":
            r["notes"] = "; ".join(filter(None, [r.get("notes", ""), f"{bg_id} rejected"]))
            bg_id = ""
        if not bg_id:
            if mode == "fixed":
                raise SystemExit(f"{_rel(path)}: sku {r['sku']}: mode=fixed needs a background_id")
            pool = sorted(k for k, row in index.items() if row["scene_id"] == scene_id and is_ready(row))
            if mode == "random" and pool:
                bg_id = random.Random(f"{slug}|{r['sku']}|{r.get('seed', '')}").choice(pool)
                action = "picked"
            else:
                bg_id = request(scene_id, style, slug, note=f"{slug} sku {r['sku']}")["background_id"]
                index = load_index()
                action = "requested"
            r["background_id"] = bg_id
        row = index[bg_id]
        state = "ready" if is_ready(row) else (row["status"] if row["status"] != "approved" else "missing")
        out.append({"sku": r["sku"], "background_id": bg_id, "state": state, "action": action})
    tables.write_csv(path, [VEHICLE_FIELDS] + [[r.get(k, "") for k in VEHICLE_FIELDS] for r in rows])
    return out


def todo(slug: str, bindings: list[dict[str, str]] | None = None) -> list[str]:
    """Human/agent next steps for a vehicle's background bindings (read-only)."""
    if bindings is None:
        v = layout.vehicle(slug)
        if not vehicle_csv(v).exists():
            return []
        index = load_index()
        bindings = []
        for r in tables.read_csv(vehicle_csv(v)):
            row = index.get(r.get("background_id", ""))
            state = "unbound" if not row else ("ready" if is_ready(row) else row["status"])
            bindings.append({"sku": r["sku"], "background_id": r.get("background_id", ""), "state": state})
    steps = []
    for b in {b["background_id"]: b for b in bindings}.values():
        bid, state = b["background_id"], b["state"]
        if state == "unbound":
            steps.append(f"background for sku {b['sku']} not resolved: python run.py run {slug} --from 05 --to 05")
        elif state == "requested":
            steps.append(f"generate background {bid} with imagegen (prompt: {_rel(prompt_path(bid))}), "
                         f"then python run.py bg register {bid} <image>")
        elif state == "generated":
            steps.append(f"review {bid} (assets/inputs/background_library/{bid}.png): python run.py bg approve|reject {bid}")
        elif state == "rejected":
            steps.append(f"{bid} rejected: re-run step 05 to request a replacement")
        elif state != "ready":
            steps.append(f"{bid}: image file missing, pull assets or re-register")
    return steps
