# 背景图库方案

## 资产与索引

- 背景原图放在 `assets/inputs/background_library/<background_id>.png`，不进入 git；对应的 SHA-256 由资产清单追踪。
- 元数据放在 `data/backgrounds.csv`：`background_id,scene_id,theme,vehicle,width,height,file,source,license,usage,status,sha256,qa,requested,notes`。只有 `status=approved` 且 `usage=direct` 的图进入可选池；授权不明的外部图片登记为 `usage=reference_only`，只作生图参照。
- 每个车型在 `data/vehicles/<slug>/inputs/backgrounds.csv` 指定 `sku,mode,scene,background_id,seed,notes`。`sku` 可写 `S;M` 表示多个 SKU 共用一张。`mode=fixed` 指定一张；`mode=random` 从同场景的可选池中按种子选一张；`mode=generate` 总是为该行单独生成一张。`scene` 留空时取主题默认场景。

## 背景生图节点（`zontar.backgrounds`）

生图由代理内置 imagegen 或人工完成，Python 不调用任何生图接口；节点负责按需出请求、登记和选择。

- **场景与提示词**：提示词模板 `data/backgrounds/prompt_template.md` 来自 [背景生图节点.md](背景生图节点.md)，场景相关段落放在 `data/backgrounds/scenes.csv`。当前包含冬季湖畔、秋季石材住宅、霜冻森林、雨后城市公园和初冬河畔；新增场景只需加一行 CSV，不改代码。
- **主题默认场景**：`src/zontar/themes.py` 的 `Theme.background_scene`。`land_cruiser`、`renault_logan` 为 `winter_lakeside`；`toyota_rav4_v6`（深蓝全幅）暂无，需要时显式传 `--scene`。
- **流水线步骤**：车型的 `pipelines/<slug>/05_background.py` 调用 `backgrounds.resolve_vehicle(slug, style)`。没有 `backgrounds.csv` 的车型不使用该节点。已有 `background_id` 的行保持不变；缺失时先从可选池选，池为空则生成请求（写入 `data/backgrounds/prompts/<id>.md`，索引状态为 `requested`），并把 id 写回车型 CSV。已驳回（rejected）的背景在下次运行时自动换新请求（`fixed` 行除外）。该步骤不阻断后续出图，`python run.py status` 会列出待办。
- **状态流转**：`requested` → `bg register`（校验 3:4、居中裁切缩放为 1086×1448 RGB、覆盖前备份、做版式 QA）→ `generated` → 人工目视 → `bg approve` / `bg reject`。

```
python run.py bg scenes                               # 可用场景
python run.py bg request --theme renault_logan        # 按主题按需出一张背景请求（可加 --vehicle SLUG / --scene ID）
python run.py bg prompt <id>                          # 查看提示词（交给 imagegen，连同文件头里的参考图）
python run.py bg register <id> <生成的图片>            # 登记
python run.py bg approve <id>  |  bg reject <id> --note 原因
python run.py bg resolve <slug> --theme <主题>         # 与 05 步骤相同
python run.py bg list
```

版式 QA 只是提示，写入索引 `qa` 列：画面几乎纯色、上方标题区接近纯白、上方对比过强、下方平台区过于单调。是否通过仍以目视为准。

## 选择与复现

- 随机选择发生在源图生成前，而不是每次 `run.py run` 时。按车型、SKU 和 `seed` 选择后，把实际 `background_id` 写回车型 CSV；同一次项目的多张主图可共用一个背景，也可逐 SKU 指定。
- 使用背景生成披罩车辆时，把选中背景作为 imagegen 参照，并保存最终合成的 `source/base_<SKU>.png`。常规流水线只读取已审核的源图，重复打包不会随机变图。
- 背景与车的地平线、光向、阴影、天气要匹配；必须保留上方标题空间，不能让画面元素遮挡车辆或文字。近景车可从边缘裁切；背景本身不能引入未经授权的商标、车牌或人物。

## 落地顺序

1. ~~实现按车型与 SKU 选择、持久化结果的小工具，再接入生图准备步骤。~~ 已完成（上节）。
2. 按请求生成首张背景并审核；如需外部素材，登记授权后再入池。
3. 用 Tiguan S/M 各做一张对照图，检查标题可读性、场景一致性和可复现性后启用。

2026-09-30 已为 Tiguan S 生成并登记 15 个场景（首轮 5 个，加测雪山木屋、海岸悬崖、霜冻白桦林、现代别墅、雾谷、草原湖岸、秋季庄园、石桥河谷、冬季城市广场、松林营地 10 个），状态均为 `generated`，等待人工 approve/reject。对照成品与总览位于 `assets/outputs/vehicles/volkswagen_tiguan/background_demos/`；正式主图未替换。可用 `python pipelines/volkswagen_tiguan/background_demo.py` 以当前标准排版重绘 demo。
