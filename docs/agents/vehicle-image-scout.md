# 车型图片检索：流程与约定（任何代理通用）

目标：让车型适配图（`02_车型适配图`）使用**真实、代际正确**的车辆图片，样式同
`renault_logan/package/02_车型适配图/Renault_Logan_3M_车型适配图_1086x1448.png`：
模糊场景底图 + 透明背景的整车抠图（前 3/4 视角）+ 信息栏。

本文件是唯一的流程说明。Codex 直接按本文执行（需联网搜索，例如 `codex --search`）；
Claude Code 可用项目子代理 `.claude/agents/vehicle-image-scout.md`，它也只是指向本文。

## 执行流程

输入参数：车型 `slug`，可选 `sku`。路径用 `python run.py paths --vehicle <slug> --json` 解析（其中 `vehicle.candidates` 目录由 `zontar.layout.Vehicle.candidates` 给出）。

1. **读请求**：`data/vehicles/<slug>/inputs/image_requests.csv` 的目标行和 `fitment_detail.csv`。先写下该代际的外观识别点（格栅、大灯、C 柱、尾部、车长级别），作为核验依据。查看参考样式图，理解需要的构图。
2. **检索**：网络搜索，俄文、英文关键词都试（如 `Volkswagen Tiguan II 2018 press photo`、`Фольксваген Тигуан 2 фото`）。按下文“来源优先级”。每行请求收集 6–12 个候选。
3. **下载**：`curl -L --max-filesize 20000000 -o <文件>` 下载原图到 `<candidates>/<sku>/<nn>_<来源简称>.<ext>`。网页阅读工具只用来读页面和授权条款。不绕过登录、付费墙、防盗链或 robots 限制。
4. **逐张目视核验**（必须真正打开图片查看）：
   - 代际/改款正确（对照第 1 步识别点，写明依据）；
   - 车身形式正确（标准轴距与加长版、轿车与旅行车）；
   - 视角为前 3/4（或请求指定的视角），整车完整不裁切，轮子落地；
   - 长边 ≥ 1500 px，清晰；
   - 无水印、无文字叠加、无遮挡；背景越干净越利于抠图；
   - 车漆中性（银、白、灰优先），无改装、贴膜、特殊涂装。
   不合格的也记录（`status=rejected` 并写原因），其文件可删除。
5. **记录**：追加到 `data/vehicles/<slug>/inputs/image_candidates.csv`，列定义见下文；计算 sha256、宽高。
6. **审查拼图**：
   ```
   python -c "import sys; sys.path.insert(0,'src'); from pathlib import Path; from zontar import render; d=Path(sys.argv[1]); render.contact_sheet(sorted(p for p in d.iterdir() if p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'} and not p.name.startswith('_')), d/'_review_sheet.png')" <candidates>/<sku>
   ```
7. **汇报并更新 `docs/HANDOFF.md`**：每个 SKU 推荐最多 3 个候选（按 score），各自的授权结论与风险，未满足的请求。

**禁止**：写入 `source/`；覆盖已有文件；把候选设为 `approved`（只能由人工设定）；抠图、改上架图或文案；上传、推送、同步远端。不虚构来源、授权或尺寸，未核验的字段留空并在 notes 说明。

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
