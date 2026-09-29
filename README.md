# ZONTAR / Tozaroa 车罩上架流水线

灰色单层 PEVA 无耳车罩的 Ozon 上架素材流水线：分类通用图库 → 车型专属主图/适配图 → 上架表格 → 交付 ZIP。

**存储原则**

| 内容 | 放在哪里 | 由谁管理 |
|---|---|---|
| 代码（`src/`、`pipelines/`、`scripts/`） | 本仓库 | git |
| 所有表格（一律 CSV，UTF-8 BOM） | `data/` | git |
| 图片、ZIP、原始 xlsx | `assets/`（资产存储） | NAS / OSS，git 只记录 `manifests/*.csv` 中的 sha256 |

`assets/` 被 `.gitignore` 忽略。它是远端（NAS 或阿里云 OSS）的本地镜像，任何一台机器 `git clone` + `zontar sync pull` 就能还原出与清单完全一致的素材。

## 目录结构

```
config/storage.toml          资产根目录与远端配置（本机覆盖写 storage.local.toml，不入库）
src/zontar/                  共享库 + CLI：路径布局、xlsx→CSV、清单、NAS/OSS 同步、打包
pipelines/<车型>/            各车型当前有效的生成脚本，按执行顺序编号
  10_*.py                      生成主图 / 适配图 / SKU 选择图（Pillow）
  20_*.py                      重新设计覆盖（如有）
  25_*.mjs, 30_*.mjs           写上架 CSV / 官方上架表 xlsx（依赖 @oai/artifact-tool）
pipelines/_shared/paths.mjs  Node 脚本通过它读取 Python 的路径布局（单一真相源）
scripts/migrate_layout.py    2026-09-29 一次性目录迁移记录
scripts/legacy/              历史一次性脚本（检查、核对、旧版本），仅供参考，路径已失效
docs/prompts/                生图总提示词、逐图提示词、来源说明

data/                        —— git：全部表格 ——
  vehicles.csv                 车型注册表（slug、包名、共用副图来源、SKU…）
  tables.csv                   每个 CSV 目录来自哪个 xlsx 资产（key + sha256）
  vehicles/<slug>/             上架内容.csv、尺码分组说明.txt、official_listing/<sheet>.csv
  reference/                   标签词库、搜索词库、俄罗斯销量、Ozon 1000 排名
  templates/                   Ozon 官方上架模板（CSV 版）
  listing_summary/snapshots/   Ozon上架链接汇总 历次快照（时间_说明/）

manifests/                   —— git：资产清单 ——
  inputs.csv outputs.csv archive.csv   key,bytes,sha256,width,height
  migration_map.csv                    迁移前旧路径 → 新路径

assets/                      —— NAS/OSS，不入 git ——
  inputs/brand/                    Logo、功能图标
  inputs/category_library/<阶段>/  五类车型通用副图、A+、秋冬首图
  inputs/vehicles/<slug>/source/   车型生成源图（base_*, vehicle_*）
  inputs/spreadsheets/             原始 xlsx 输入（模板、词库、销量…）
  outputs/vehicles/<slug>/package/ 交付包内容（01_主图 … 08_A+_移动端）
  outputs/vehicles/<slug>/dist/    交付 ZIP
  outputs/listing_summary/         汇总表写回候选
  outputs/reports/                 表格脚本生成的 QA 截图
  archive/                         备份、淘汰版本、试样、旧报告、交接包
```

## 流水线：输入 → 输出

| 步骤 | 输入 | 输出 |
|---|---|---|
| 分类图库（人工 + AI 生图） | `docs/prompts/` | `assets/inputs/category_library/` |
| `pipelines/<slug>/10_*.py`、`20_*.py` | `inputs/vehicles/<slug>/source/`、`inputs/brand/`、`category_library/` | `outputs/vehicles/<slug>/package/01–03,05–08`；`data/vehicles/<slug>/*.csv|txt` |
| `pipelines/<slug>/30_build_listing.mjs` | `data/vehicles/<slug>/上架内容.csv`、`inputs/spreadsheets/汽车罩官方上架模板.xlsx` | `package/04_上架资料/*.xlsx`、`outputs/listing_summary/*候选.xlsx`、`outputs/reports/*.png` |
| `zontar tables convert` | 任一 xlsx 资产 | `data/<目录>/<sheet>.csv` |
| `zontar pack <slug>` | `package/` + `data/vehicles/<slug>/` | `outputs/vehicles/<slug>/dist/<包名>.zip` |
| `zontar manifest` | 整个 `assets/` | `manifests/*.csv` |

ZIP 内的目录结构与历史交付包一致：`<包名>/01_主图/...`、`<包名>/04_上架资料/上架内容.csv` 等。

## 快速开始

免安装入口 `python run.py <命令>` 等同于 `zontar <命令>`（安装方式：`pip install -e .`，需要 OSS 时 `pip install -e .[oss]`）。

```bash
python run.py status                      # 每个车型的进度、缺失输入、下一步
python run.py run volkswagen_tiguan       # 按序号跑全部步骤，再打包、刷新清单
python run.py run volkswagen_tiguan --from 10
python run.py doctor                      # 检查 Logo、模板、字体、源图、远端配置
python run.py styles                      # 查看可选的车型套图主题
```

AI 代理（Codex、Claude Code）接手时先读 [AGENTS.md](AGENTS.md) 和 [docs/HANDOFF.md](docs/HANDOFF.md)。

## 常用命令

```bash
# 生成一个车型（在任意目录执行都可以）
python pipelines/toyota_land_cruiser/10_build_package.py
python pipelines/toyota_land_cruiser/20_redesign_master.py
node   pipelines/toyota_land_cruiser/30_build_listing.mjs
zontar pack toyota_land_cruiser

# 新表格进入 git
zontar tables convert "inputs/spreadsheets/xxx.xlsx" reference/xxx
zontar tables sync          # 源 xlsx 变了就重新转换所有已登记的 CSV

# 素材变更后
zontar manifest             # 更新清单；git diff manifests/ 可看到哪些图变了
zontar sync push            # 上传到 NAS / OSS
git add -A && git commit

# 新机器
git clone ... && pip install -e . && zontar sync pull
```

## 新增车型（以 volkswagen_tiguan 为范例）

新车型只需要数据和源图，不再复制整套出图脚本：

1. 在 `data/vehicles.csv` 加一行（slug、包名、上架品牌、共用副图来源）。
2. 在 `data/vehicles/<slug>/inputs/` 放 `size_map.csv`（运营给的尺码表）和 `skus.csv`（每个 SKU 的发货尺码、标题行、年份、适配卡片）。
3. `00_extract_fitment.py`：从俄罗斯销量表抽出该车型逐代车长，与尺码表交叉校验，不一致即报错。
4. `10_build_images.py`：调用 `src/zontar/render.py` 生成主图、适配图、SKU 选择图和总览，并复制分类共用副图与 A+。缺源图或 Logo 时用占位图并加 DRAFT 水印。
   在 `render.Job(style="...")` 中选择 `land_cruiser`、`renault_logan` 或 `toyota_rav4_v6`；主题说明见 [docs/IMAGE_STYLES.md](docs/IMAGE_STYLES.md)。
5. `20_build_listing.py`：生成上架内容 CSV、官方模板行 CSV（`official_listing/模板.csv`）、尺码说明和源图生图提示词（`inputs/source_prompts.csv`）。
6. （规划中）车型适配图要用真实车辆照片时，先写 `inputs/image_requests.csv`，再调用 `vehicle-image-scout` agent 联网找图，人工审批后抠图。约定见 [docs/agents/vehicle-image-scout.md](docs/agents/vehicle-image-scout.md)。
7. 按提示词生成 `base_<SKU>.png` 放进 `assets/inputs/vehicles/<slug>/source/`，重跑第 4 步，水印自动消失。
8. `zontar pack <slug>`，`zontar manifest`，提交 git。

## 切换到 NAS / OSS

复制 `config/storage.local.toml.example` 为 `config/storage.local.toml`，然后二选一：

- **NAS 直接作为工作目录**：`[local] asset_root = "Z:/zontar/assets"`，不需要同步。
- **NAS 作为远端**：`[remote] backend = "nas"`，`[remote.nas] root = "//NAS/zontar/assets"`，再用 `zontar sync push/pull`。
- **阿里云 OSS**：`[remote] backend = "oss"`，填写 `[remote.oss]` 的 endpoint、bucket、prefix。密钥只从环境变量 `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` 读取。每个对象带 `x-oss-meta-sha256` 元数据，同步时据此比对。配置 `public_base_url` 后，`zontar url <key>` 可给出图片外链，用于 Ozon 上架表中的图片 URL 列。

环境变量 `ZONTAR_ASSET_ROOT`、`ZONTAR_REMOTE`、`ZONTAR_DATA_ROOT` 可临时覆盖配置（例如在沙盒里试跑脚本）。

同步只增不删：远端或本地多出的文件不会被自动删除。

## 约定

- 资产 key = 相对 `assets/` 的 POSIX 路径，目录层级用 ASCII，交付包内部沿用中文文件夹和文件名。
- CSV：UTF-8 BOM、CRLF 行尾、单元格内换行为 LF；`.gitattributes` 禁止 git 改动 CSV 行尾。
- 带公式的工作表额外生成 `<sheet>.formulas.csv`（cell, formula）。
- 不再手工复制“xxx前备份”：表格靠 git 历史，图片靠清单 + 远端；脚本需要覆盖图片时调用 `layout.backup_before_overwrite()`，自动备份到 `archive/backups/<日期>_<说明>/`。

## 已知缺口

- **官方模板与汇总表的最新版本不在本目录**：`30_build_listing.mjs` 需要 `assets/inputs/spreadsheets/汽车罩官方上架模板.xlsx` 和 `Ozon上架链接汇总_两店对应完成.xlsx`（原位于作者桌面 / `ozon发货`）。放入后执行 `zontar tables convert` 把汇总表转成 `data/listing_summary/current/`。
- **`@oai/artifact-tool`** 是原作者环境里的 Node 包，本机未安装，`.mjs` 脚本需在有该包的环境运行，或日后改写为 openpyxl 实现。
- **RAV4 XS 图片只能视觉复现**：`10_build_images_v6.py` 输出到 `outputs/vehicles/toyota_rav4/staging/V6/`，M、S 与交付包逐像素一致，XS 视觉一致但非逐像素（交付的 XS 文件经过一次重新编码）。
- **Renault Logan 使用的是越野车共用副图和 A+**（见 `data/vehicles.csv` 备注），与三厢车类别不一致，需确认是否有意为之。
