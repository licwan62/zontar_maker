"""Named visual themes for vehicle-specific marketplace image sets.

Theme ids are stable API.  A pipeline selects one with ``render.Job(style=...)``;
the renderer owns the implementation while this module owns discovery, aliases and
human-readable constraints.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Theme:
    id: str
    name: str
    reference_preview: str
    mood: str
    best_for: str
    composition: str
    vehicle_asset: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


THEMES: dict[str, Theme] = {
    "land_cruiser": Theme(
        id="land_cruiser",
        name="Land Cruiser 冬景信息板",
        reference_preview=(
            "outputs/vehicles/toyota_land_cruiser/package/05_预览/"
            "LandCruiser_九图总览.png"
        ),
        mood="浅色冬景、紧凑、信息密度高",
        best_for="3–5 个以上 SKU，或每个 SKU 有较长兼容车型列表",
        composition="渐隐浅色页头；全幅车辆主图；适配卡片位于上部，车辆位于下部；紧凑多行选择表",
        vehicle_asset="base_<SKU>.png；适配图最好另有 vehicle_<SKU>.png",
    ),
    "renault_logan": Theme(
        id="renault_logan",
        name="Renault Logan 清晰分区",
        reference_preview=(
            "outputs/vehicles/renault_logan/package/05_预览/"
            "Renault_Logan_五图总览.png"
        ),
        mood="浅底、克制、车辆和文字严格分区",
        best_for="1–3 个 SKU，需要优先保证缩略图可读性和无元素压车",
        composition="主图为 Logan 标准页头；适配图上方信息、下方独立车辆区；选择图为浅底大卡片",
        vehicle_asset="base_<SKU>.png；透明 vehicle_<SKU>_cutout.png 可获得最佳效果",
    ),
    "toyota_rav4_v6": Theme(
        id="toyota_rav4_v6",
        name="Toyota RAV4 V6 深色全幅",
        reference_preview=(
            "outputs/vehicles/toyota_rav4/package/05_预览/"
            "V6_七图总览.png"
        ),
        mood="深蓝、全幅摄影、强渐变、高对比运动感",
        best_for="2–4 个 SKU，源图背景统一且希望强化视觉冲击力",
        composition="文字直接融入全幅摄影；适配列表使用深色条；选择图为纵向全幅车辆面板",
        vehicle_asset="base_<SKU>.png；提供 vehicle_<SKU>.png 时适配图和选择图效果更接近参考",
    ),
}


ALIASES = {
    "classic": "land_cruiser",
    "logan_reference": "renault_logan",
    "rav4_v6": "toyota_rav4_v6",
}


def resolve_style(style: str) -> str:
    resolved = ALIASES.get(style, style)
    if resolved not in THEMES and resolved != "editorial":
        choices = ", ".join(THEMES)
        raise ValueError(f"unknown image style {style!r}; choose one of: {choices}")
    return resolved


def list_styles() -> list[Theme]:
    return list(THEMES.values())
