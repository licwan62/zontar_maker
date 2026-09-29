# 交接记录（HANDOFF）

每个接手者（人或 AI 代理）收工前更新本文件：在“进度日志”顶部加一条，并同步“工作队列”和“待用户决定”。稳定规则见 [AGENTS.md](../AGENTS.md)。

## 当前状态（2026-09-29）

| 车型 | 状态 | 说明 |
|---|---|---|
| renault_logan | 已交付 | 沙盒重跑与交付图片逐像素一致 |
| toyota_land_cruiser | 已交付 | 沙盒重跑与交付图片逐像素一致 |
| toyota_rav4 | 已交付 | M/S 逐像素一致；XS 视觉一致（交付文件经过一次重新编码），脚本输出到 `staging/V6/` |
| volkswagen_tiguan | 草稿 | 数据、文案、官方模板行及 2 张 AI 源图已完成；套图已重建且无 DRAFT 水印，待用户最终确认后更新交付状态 |

共享输入缺失：`assets/inputs/spreadsheets/汽车罩官方上架模板.xlsx`、`Ozon上架链接汇总_两店对应完成.xlsx`（最新版在用户桌面，未放入）。

## 环境备注

- PATH 里的 `codex` 是 0.146 版 CLI，缺少 Windows 沙箱组件。在 `-s read-only` 或 `workspace-write` 下所有命令都会失败，报错 `codex-windows-sandbox-setup.exe ... program not found`。请用 Codex 桌面应用，或 `C:\Users\cc\AppData\Local\OpenAI\Codex\bin\8fffe69425752027\codex.exe`（0.149，沙箱可用）。
- 2026-09-29 已用后者做只读接手演练：Codex 能读懂 AGENTS.md，正确执行 `python run.py status`，并给出正确的下一步，工作区未被修改。
- 沙箱里 `git status` 可能提示无法读取 `C:\Users\cc\.config\git\ignore`，可忽略。

## 工作队列（按优先级）

每项都给出完成标准。开工前用 `python run.py status` 确认是否仍然需要。

1. **Tiguan 生图套图最终确认**（待用户验收）
   - `base_S.png`、`base_M.png` 已用内置 imagegen 生成并放入 `assets/inputs/vehicles/volkswagen_tiguan/source/`；均为 1086×1448 RGB。
   - 针对适配图另生成 `vehicle_S_cutout.png`、`vehicle_M_cutout.png`；均为 1536×1024 RGBA，四角透明，分别对应 Tiguan II 标准版和 Allspace 加长版。它们只用于适配图和 SKU 选择图，主图仍使用披罩车辆。
   - 已目视确认：S 为 Tiguan II 标准版、M 为 Allspace 加长版；灰色哑光单层罩布，无耳袋、反光条、金属光泽、文字或水印；后视镜由连续罩布覆盖；上部留白充足。
   - 2026-09-29 按用户反馈再次收敛到 Renault Logan 的结构语言：主图沿用同款层级；适配图采用轻微透出场景的白色蒙版底、上方信息区、下方独立透明整车和底部型号栏；选择图直接使用透明整车浅底双卡。文字与车辆不重叠。共享副图与 A+ 未改。`status` 显示 `source_photos 2/2`、`draft_images False`。
   - 最初旧版在 `assets/archive/backups/20260929_volkswagen_tiguan_layout_v1/`；中间 editorial 版在 `assets/archive/backups/20260929_volkswagen_tiguan_editorial_v2/`；加入透明车型前的版本在 `assets/archive/backups/20260929_volkswagen_tiguan_before_cutout/`。完成标准：用户确认新版成品后将 `data/vehicles.csv` 中状态更新为 delivered。

2. **Tiguan 车型图片检索**（需要联网）
   - 按 `docs/agents/vehicle-image-scout.md` 处理 `data/vehicles/volkswagen_tiguan/inputs/image_requests.csv`。
   - 完成标准：每个 SKU 至少 3 个合格候选写入 `image_candidates.csv`，`_review_sheet.png` 已生成，授权结论齐全；**不得**自行设为 approved。

3. **抠图步骤 `06_cutout`**（未实现）
   - Tiguan 已有本次用 imagegen 单独生成的透明车型图，但这是车型级资产，不等于通用自动抠图步骤已经实现。
   - 输入：`image_candidates.csv` 中 `status=approved` 且 `usage=direct` 的候选。输出：`source/vehicle_<SKU>_cutout.png`，1536×1024 RGBA，车头朝左，四周留白一致。
   - 放在 `src/zontar/cutout.py`，由各车型的 `06_*.py` 调用。允许新增去背景依赖（如 rembg），但只能作为可选依赖 `[project.optional-dependencies] cutout = [...]`；基础流水线仍只依赖 Pillow 与 openpyxl。未安装时 06 步骤要给出安装提示并以非零退出。
   - 完成标准：对 Logan 现有 `vehicle_sedan_cutout.png` 的原始来源不可得，因此以视觉检查为准；输出透明通道干净、无残留背景。

4. **Logan 版式逐像素参数化验证**（结构已实现，精确验证未完成）
   - 已完成主题注册与可选调用：`land_cruiser`、`renault_logan`、`toyota_rav4_v6`，见 `docs/IMAGE_STYLES.md` 和 `python run.py styles`。Tiguan 已使用 `renault_logan`。
   - 通用渲染器已实现 Logan 的核心结构（场景模糊底图 + 白色蒙版 + 兼容性信息 + 下半部整车透明图 + 型号栏），Tiguan 已实际调用；仍需用 Logan 自身数据验证精确像素一致性。
   - 完成标准：用通用渲染器配 Logan 数据，在沙盒中生成的两张 Logan 适配图与交付文件**逐像素一致**（`ImageChops.difference(a, b).getbbox()` 为 None）。做不到时报告差异像素占比（阈值 24）并附差异图，交用户判断，不要自行放宽标准。Tiguan 缺抠图时回退到当前版式。

5. **上架表 xlsx 导出去掉 `@oai/artifact-tool` 依赖**（未实现）
   - 用 openpyxl 把 `data/vehicles/<slug>/official_listing/模板.csv` 的数据行写入官方模板 xlsx 的副本，保留模板的数据验证。
   - 完成标准：Land Cruiser 导出结果与 `data/vehicles/toyota_land_cruiser/official_listing/模板.csv` 转回 CSV 后一致。前提：用户提供最新模板。

## 待用户决定

- 上架品牌：总提示词要求 ZONTAR，已交付车型均用 Tozaroa（`data/vehicles.csv` 的 `listing_brand`）。
- 官方模板第 33 列表头为“尺寸(LxWxH),厘米”，历史上填的是商品标题，可能是原脚本错误。
- Renault Logan（三厢车）使用了越野车共用副图与 A+。
- Tiguan M 码是否保留北美版 Tiguan III（`inputs/skus.csv`）。

## 进度日志

### 2026-09-29 · Codex（Tiguan 透明车型与 Logan 适配结构）
- 根据用户指出的关键差异，为 Tiguan S/M 分别生成无车罩、透明背景的独立车型资产 `vehicle_S_cutout.png` 与 `vehicle_M_cutout.png`，并在 SKU 数据中通过 `vehicle_image` 显式绑定；两图均为 1536×1024 RGBA，四角 alpha 为 0。
- 适配图改为 Logan 的实际合成逻辑：场景图仅作为模糊且高白色蒙版的轻背景，未披罩整车作为独立透明层完整呈现，信息与车辆分区，底部保留型号栏；SKU 选择图也直接合成透明整车，不再嵌入场景照片。
- 覆盖前版本已归档至 `assets/archive/backups/20260929_volkswagen_tiguan_before_cutout/`；重新运行 Tiguan 流水线成功，5 张核心图已更新，包和 zip 均为 current。
- 已完成目视检查、Python 编译、透明通道检查、资产清单刷新与 `manifest --check`；Tiguan 保持 draft，等待用户最终确认。

### 2026-09-29 · Codex（套图主题注册）
- 将三套已交付参考样式定义为稳定主题 ID：`land_cruiser`、`renault_logan`、`toyota_rav4_v6`；主题元数据集中在 `src/zontar/themes.py`，视觉说明在 `docs/IMAGE_STYLES.md`。
- `render.Job` 新增正式参数 `style="..."`；`Sku` 新增可选 `vehicle_image`，适配图和选择图在提供独立车辆图时优先使用，缺失时回退 `base_image`。旧名称 `classic`、`logan_reference`、`rav4_v6` 保留兼容。
- 新增 `python run.py styles [--json]`；Tiguan 从临时 `logan_reference` 名称迁移到正式 `renault_logan`，重跑后 5 张核心图逐字节不变。
- 三个主题均以 Tiguan 数据完成内存烟雾测试，主图、适配图、选择图均成功输出 1086×1448；Python 编译、Tiguan 流水线及清单检查通过。

### 2026-09-29 · Codex（Tiguan 核心套图重新排版）
- 第一轮对比 Tiguan 旧版、Logan/Land Cruiser 已交付版以及公开汽车罩商品信息图，确认旧版存在顶部信息竞争、适配页表格感过强、选择页车型图过小等问题；第一轮 editorial 版随后因风格不统一、信息卡压住车辆主体被用户否决。
- 根据用户反馈改为 `logan_reference` 版式：主图直接采用 Logan 同款结构；适配页使用独立的上方信息区和下方车辆照片区；选择页采用 Logan 同款浅色双卡结构，并去掉所有压在车辆照片上的文字标签。
- `src/zontar/render.py` 中版式为显式可选项，默认仍为 `classic`，其他车型不会自动改变；Tiguan 流水线显式启用 `logan_reference`。共享副图和 A+ 保持不变。
- 最初旧版归档至 `assets/archive/backups/20260929_volkswagen_tiguan_layout_v1/`，第一轮 editorial 版归档至 `assets/archive/backups/20260929_volkswagen_tiguan_editorial_v2/`。
- 目视检查确认文字无溢出、车型与年份完整、图片与文字不重叠、S/M 区分清楚；Python 编译、Tiguan 全流水线、图片尺寸检查、`status` 与 `manifest --check` 均通过。

### 2026-09-29 · Codex（Tiguan 正式生图）
- 使用 Volkswagen Newsroom 等联网资料核对 Tiguan II 标准轴距与 Allspace 长轴车型比例；网络图片只用于外观参考，没有直接用于商品资产。
- 使用内置 imagegen 分别生成 `base_S.png`、`base_M.png`；S 初稿有独立后视镜袋，已做定向修正。最终两图均通过车型、罩布、构图、尺寸与无文字水印的目视验收。
- 重跑 `python run.py run volkswagen_tiguan` 成功，5 张车型相关套图已重建，`drafts: []`；包内 24 个文件，zip current。`python run.py manifest --check` 通过，inputs/outputs/archive 均无漂移。

### 2026-09-29 · Codex
- 按用户要求原地重跑草稿车型 `volkswagen_tiguan`：`00_extract_fitment.py`、`10_build_images.py`、`20_build_listing.py` 均成功，随后重新打包并刷新资产清单。
- 重跑后 `python run.py status` 显示包内 24 个文件、zip 为 current；因 `base_S.png` 和 `base_M.png` 仍缺失，SKU 图片继续带 DRAFT 水印，车型状态仍为 draft。
- `python run.py manifest --check` 通过（inputs/outputs/archive 均无漂移）。实际输出路径是 `assets/outputs/vehicles/volkswagen_tiguan/`。

### 2026-09-29 · Claude Code
- 项目重组为 输入/输出/归档 资产树 + git 管理代码与 CSV；全部 xlsx 转为 CSV（`data/tables.csv` 记录来源）。
- 新增 `run.py`（免安装入口）、`run`/`status` 命令、确定性打包、按 mtime 加速的清单刷新、`ZONTAR_FONT_DIR`。
- Tiguan 流水线（00 适配核验 / 10 出图 / 20 文案与模板行）重跑两次，输出逐字节一致，zip 哈希一致。
- 已交付车型沙盒重跑：Logan、Land Cruiser 全部逐像素一致；RAV4 见上表。RAV4 脚本改为直接输出 XS 命名。
- 定义联网找图代理（`.claude/agents/vehicle-image-scout.md`，流程在 `docs/agents/vehicle-image-scout.md`），尚未运行。
- 新增 AGENTS.md、CLAUDE.md 和本文件。Codex 只读接手演练通过，并按其反馈补充了源图验收清单、依赖规则和量化的完成标准。
- 本次改动尚未提交（上一个提交 8f240ee 由用户完成）。
