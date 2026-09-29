# 车型图片检索 agent：约定（规划中）

目标：让车型适配图（`02_车型适配图`）使用**真实、代际正确**的车辆图片，样式同
`renault_logan/package/02_车型适配图/Renault_Logan_3M_车型适配图_1086x1448.png`：
模糊场景底图 + 透明背景的整车抠图（前 3/4 视角）+ 信息栏。

Agent 定义：`.claude/agents/vehicle-image-scout.md`（Claude Code 项目子 agent）。

## 在流水线中的位置

```
00_extract_fitment.py      代际/尺码核验                         已实现
05  vehicle-image-scout    联网检索 → 候选图 + image_candidates.csv   agent 已定义，待试运行
    人工审批               把选中候选 status 改为 approved             人工
06  cutout（待实现）       approved 候选 → source/vehicle_<SKU>_cutout.png（RGBA）
10_build_images.py         render.py 适配图改用“场景 + 抠图”版式        待实现（当前为旧版式）
```

## 输入：`data/vehicles/<slug>/inputs/image_requests.csv`（git）

| 列 | 含义 |
|---|---|
| sku | Ozon SKU，对应 skus.csv |
| target | 审批后生成的抠图文件名，如 `vehicle_S_cutout.png` |
| make, model, generation, body, years | 要找的具体车型（代际写法与 fitment_detail.csv 一致） |
| view | 视角，默认 `front_3_4_left`（车头朝画面左，与 Logan 样式一致） |
| must_show | 必须可见的识别点（格栅、大灯、加长后窗等） |
| avoid | 需要避开的相似代际/版本 |
| notes | 选择这款代表车型的理由（如该尺码中销量最高） |

一个 SKU 覆盖多个代际时，只找**一款代表车型**（通常是该尺码销量最高的代际），其余代际由文字卡片说明。

## 输出

**图片**（资产存储，不进 git）：`assets/inputs/vehicles/<slug>/candidates/<sku>/`
- `<nn>_<来源>.<ext>` 原图
- `_review_sheet.png` 合格候选拼图

**记录**（git）：`data/vehicles/<slug>/inputs/image_candidates.csv`

| 列 | 含义 |
|---|---|
| sku | |
| candidate_id | `<sku>-<nn>` |
| file | 相对资产根目录的 key |
| image_url | 原图直链 |
| page_url | 所在页面 |
| source | 来源名称（Wikimedia Commons、VW Newsroom…） |
| author | 作者/版权方（能查到时） |
| license | 授权原文简称（CC0、CC BY-SA 4.0、Editorial only、unknown） |
| license_url | 授权条款链接 |
| usage | `direct` / `reference_only` / `rejected` |
| generation_match | 核验到的代际与依据（识别点） |
| view | 实际视角 |
| width, height, sha256 | |
| background | clean / busy（影响抠图难度） |
| score | 0–100，综合代际准确、视角、清晰度、背景、授权 |
| status | `candidate` / `rejected` / `approved`（仅人工可设 approved） |
| notes | 拒绝原因或风险说明 |

## 审批与后续（待实现部分的约定）

1. 人工在 image_candidates.csv 中把 1 张候选的 `status` 改为 `approved`。只有 `usage=direct` 的候选可以直接进上架图；`reference_only` 只能作为 AI 生图参照，再按 `source_prompts.csv` 生成。
2. `06_cutout`：读取 approved 候选 → 去背景（例如 rembg）→ 统一为 1536×1024 RGBA、车头朝左 → 写入 `source/vehicle_<SKU>_cutout.png`，在 notes 中记录来源 candidate_id。
3. `render.py` 适配图改为 Logan 重设计版式（`pipelines/renault_logan/20_redesign_fitment.py` 的参数化版本）：场景图模糊+白色蒙版、顶部标题/尺码/年份、兼容性卡片、整车抠图放在下半部、底部型号栏和提醒栏。
4. `zontar manifest` 记录候选与抠图的 sha256，保证可追溯。

## 调用方式

在 Claude Code 中：

```
用 vehicle-image-scout agent 为 volkswagen_tiguan 找车型图
```

首个待处理请求：`data/vehicles/volkswagen_tiguan/inputs/image_requests.csv`。
