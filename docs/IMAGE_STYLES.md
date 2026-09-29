# 车型套图主题（styles）

主题用于统一主图、车型适配图和 SKU 选择图的视觉语言。新车型通过
`render.Job(style="主题 ID")` 选择；可用主题以 `python run.py styles` 为准。

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
