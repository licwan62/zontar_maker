# 车型套图主题（styles）

主题用于统一主图、车型适配图和 SKU 选择图的视觉语言。新车型通过
`render.Job(style="主题 ID")` 选择；可用主题以 `python run.py styles` 为准。
新车源图的默认完整入画构图与掀罩状态编号见 [COVER_STATES.md](COVER_STATES.md)。

## `land_cruiser`

- 参考：`assets/outputs/vehicles/toyota_land_cruiser/package/05_预览/LandCruiser_九图总览.png`
- 特征：浅色冬景、紧凑页头、信息密度高、适配列表和车辆上下组合。
- 适用：3–5 个以上 SKU，或每个 SKU 有较多兼容车型。
- 输入：`base_<SKU>.png`；适配图最好另有 `vehicle_<SKU>.png`。

## `renault_logan`

- 参考：`assets/outputs/vehicles/renault_logan/package/05_预览/Renault_Logan_五图总览.png`
- 特征：浅底、明确分区、文字与车辆互不覆盖、缩略图可读性优先。
- 适用：1–3 个 SKU，尤其适合需要清晰区分车身和年份的套图。
- 输入：`base_<SKU>.png`；透明整车抠图能获得最接近参考的效果，没有抠图时使用独立照片区。

## `toyota_rav4_v6`

- 参考：`assets/outputs/vehicles/toyota_rav4/package/05_预览/V6_七图总览.png`
- 特征：深蓝全幅摄影、强渐变、高对比文字、纵向车辆面板。
- 适用：2–4 个 SKU，且各 SKU 源图的摄影背景和视角较统一。
- 输入：`base_<SKU>.png`；可选 `vehicle_<SKU>.png` 用于适配图和选择图。

## 固定排版首图母版（`hero_template`）

- 规格：`data/backgrounds/05_灰色无耳首图_固定排版母版提示词.md`；样式参考：`assets/archive/samples/首图模板.png`。
- 代码：`zontar.hero_template.render_hero(background, HeroFields(...))`，版式锁定，只换车型字段和背景；目前为独立主图方案，尚未接入 `render_vehicle`。
- 分工：生图只出背景（或已合成车辆的背景）；文字、Logo、尺码牌、底栏由代码按固定坐标叠加。
- 坐标、字高、面板形状从参考图实测，集中在模块顶部常量；改版式只改常量。
- 字体：标题、俄文条、年份、尺码用 Arial Black 按参考图逐元素横向收窄；辅助行与底栏标签用 Impact；声明用 Arial。
- 配色：页头区平均亮度 > 150 用海军蓝字 + 白色柔光，否则白字 + 暗影；橙色条、尺码牌、底栏固定。深色背景下 Logo 加细白描边，浅色背景保持原图，均无底板。
- 超长车型名先收窄到 0.50，再降低字高（报告 `model_cap`），仍是全图最大字。
- 字段表：`data/vehicles/<slug>/inputs/hero.csv`（`sku, model_latin, model_ru_search, body_ru, years, size_code, background`）。
- 示例：`python pipelines/volkswagen_tiguan/hero_template_demo.py` → `assets/outputs/vehicles/volkswagen_tiguan/hero_template_demos/`（含参考图对照），不覆盖正式 package。

## 调用

```python
job = render.Job(
    brand="Tozaroa",
    title="VOLKSWAGEN TIGUAN",
    file_prefix="VW_Tiguan",
    subtitle=("ВСЕСЕЗОННЫЙ ЧЕХОЛ", "ДЛЯ КРОССОВЕРА"),
    skus=skus,
    style="renault_logan",
)
render.render_vehicle(job, vehicle)
```

`Sku.vehicle_image` 是可选字段；未提供时自动回退到 `base_image`。旧名称
`classic`、`logan_reference`、`rav4_v6` 仍可使用，但新脚本应写正式主题 ID。
需要在主图放大车型名称时，可选用 `Job(main_title_lines=("VOLKSWAGEN", "TIGUAN"))`；
该参数仅改变主图页头，不影响适配图与选择图。

此页头以 Land Cruiser 主图为视觉重量参考，采用三条横向信息带：车型名与 Logo、车型范围与年份、尺码与产品说明。字号固定为小 30、中 50、大 76 px，Logo 位于右上且宽 187 px。出图后自动计算逐元素视觉重量代理值（着色像素面积 × 与底色的亮度对比），检查参考校准后的左右重量和重心、元素碰撞、越界、实际字号，以及年份/尺码文字墨迹高度占胶囊高度 44%–58%。检查失败会中止出图。数值与元素占比保存在 `assets/outputs/vehicles/<slug>/render_report.json` 的 `main_layout_audit` 中；最后仍需目视检查可读性和车辆构图。
# 固定首图颜色主题

`src/zontar/hero_template.py` 在固定版式不变的前提下提供三套稳定颜色主题：

- `midnight_orange`：白色标题、橙色强调、深夜蓝面板；用于深色蓝调、雨夜与城市夜景。
- `arctic_blue`：深海军蓝标题、钴蓝强调、深蓝面板；用于雪景、浅灰天空与冷色明亮背景。
- `forest_gold`：深森林绿标题、暖金强调、森林绿面板；用于秋景、石材、木屋与暖色自然背景。

调用 `hero_template.palette_by_name(...)` 可显式指定；不指定时按标题区明度与冷暖自动选择。颜色主题只改变文字、强调色、尺码牌与底栏配色，不改变固定坐标、字号、Logo 或底栏结构。
