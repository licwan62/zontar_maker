# 交接记录（HANDOFF）

每个接手者（人或 AI 代理）收工前更新本文件：在“进度日志”顶部加一条，并同步“工作队列”和“待用户决定”。稳定规则见 [AGENTS.md](../AGENTS.md)。

## 当前状态（2026-09-30）

| 车型 | 状态 | 说明 |
|---|---|---|
| renault_logan | 已交付 | 沙盒重跑与交付图片逐像素一致 |
| toyota_land_cruiser | 已交付 | 沙盒重跑与交付图片逐像素一致 |
| toyota_rav4 | 已交付 | M/S 逐像素一致；XS 视觉一致（交付文件经过一次重新编码），脚本输出到 `staging/V6/` |
| volkswagen_tiguan | 草稿 | S/M 完整车身与 C01 状态已完成；主图按 Land Cruiser 视觉重量重排并通过验收，待用户验收 |

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
   - 2026-09-30 按用户红线参考，将披罩开口收窄至车标上方、只露近侧一盏车灯；使用更近的广角前 3/4 构图，允许车尾裁切；主图改用大号两行车型标题。改前源图及车型图在 `assets/archive/backups/20260930_volkswagen_tiguan_before_closeup/`。新成品仍需用户目视确认。
   - 同日按 13 张首图进一步修正：S/M 车身完整入画、透视减弱；C01 掀罩状态左侧下摆垂到底盘下方、右侧升至近侧轮毂上方；Logo 和标题进一步放大，页头压紧。当前定义见 `docs/COVER_STATES.md`。两轮改前版本在 `assets/archive/backups/20260930_volkswagen_tiguan_before_C01_full_car/` 与 `assets/archive/backups/20260930_volkswagen_tiguan_before_header_spacing/`。
   - 用户进一步圈出右上和底栏空白：已把年份说明、加大的年份牌与产品说明移入右上；底栏加分隔线并放大声明。改前图片在 `assets/archive/backups/20260930_volkswagen_tiguan_before_spacing_revision/`。当前主图仍需用户验收。
   - 用户要求重新平衡视觉重量：Logo 缩为 220 px 并居中，两行标题居中；车型/年份、尺码/说明左右配对。页头严格使用 28/54/150 px 三级字号，并增加逐元素视觉重量、重心、左右比和碰撞验收。改前主图在 `assets/archive/backups/20260930_volkswagen_tiguan_before_weight_balance/`。
   - 进一步按 Land Cruiser L 主图校准：车型标题恢复单行 76 px，Logo 右上 187 px；车型/年份、尺码/说明保持三条横向信息带，字号改为 30/50/76 px。验收增加胶囊文字墨迹高度占比 44%–58%；当前年份为 53.2%，尺码为 46.7%。改前版本在 `assets/archive/backups/20260930_volkswagen_tiguan_before_land_cruiser_weight/`。

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

6. **背景图库**（节点已实现，5 张 demo 待用户验收）
   - 目录、元数据、随机选择与复现规则，以及背景生图节点用法见 `docs/BACKGROUND_LIBRARY.md`。
   - 选择、按需请求、登记、审核、写回均已实现（`src/zontar/backgrounds.py`、`python run.py bg ...`、Tiguan `05_background.py`）。
   - 已生成并登记 5 个不同场景：冬季湖畔、秋季石材住宅、霜冻森林、雨后城市公园、初冬河畔；均为 `generated`，QA 为 ok，尚未代替用户 approve。
   - Tiguan S 对照成品及总览位于 `assets/outputs/vehicles/volkswagen_tiguan/background_demos/`；正式 `package/01_主图` 未覆盖。重绘脚本为 `pipelines/volkswagen_tiguan/background_demo.py`。
   - 完成标准：至少一张 approved 背景；Tiguan `status` 显示 `backgrounds 1/1 ready`。

## 待用户决定

- 上架品牌：总提示词要求 ZONTAR，已交付车型均用 Tozaroa（`data/vehicles.csv` 的 `listing_brand`）。
- 官方模板第 33 列表头为“尺寸(LxWxH),厘米”，历史上填的是商品标题，可能是原脚本错误。
- Renault Logan（三厢车）使用了越野车共用副图与 A+。
- Tiguan M 码是否保留北美版 Tiguan III（`inputs/skus.csv`）。

## 进度日志

### 2026-09-30 · Codex（三主题车辆统一与投影裁剪修复）
- 修复 `hero_template._place()`：文字投影先放入四周 18 px 的扩展 alpha 画布再膨胀和模糊，消除紧字形图层造成的投影硬裁边。
- 三套颜色主题对照统一使用原中间图 `bg_snowy_alpine_lodge_001` 的同一 Tiguan S、同一构图和同一下摆状态，仅比较配色；不再混用三张不同车辆合成源图。
- 重绘 `VW_Tiguan_三套颜色主题对照.png`，目视确认三车完全一致、左侧下摆采用用户认可的中间图状态，标题投影四周连续。

### 2026-09-30 · Codex（车罩下摆与固定母版可读性修正）
- 按用户标注用内置 imagegen 编辑 Tiguan S/M：左前下摆仅窄点轻触地面，不再堆积拖尾；近侧下摆自然降低，遮住绝大部分门槛和底盘，同时保留前轮完整可见。旧源图已归档到 `assets/archive/backups/20260930_volkswagen_tiguan_cover_hem_revision/`。
- 同步更新 `source_prompts.csv` 与 `docs/COVER_STATES.md`，把上述两项纳入 C01 固定约束。
- 固定首图母版的浅色/深色投影由 3 px 扩至 7 px，提升不透明度与模糊半径；车型标题、俄文条、年份、尺码牌和辅助行的纵向间距拉开约 8–33 px，允许与背景车辆少量重叠。
- 已重绘 S/M 固定模板及三套颜色主题 demo；目视确认车罩物理关系、标题可读性与固定底栏正常。正式 package 尚未覆盖。

### 2026-09-30 · Codex（固定首图三套颜色主题）
- 保留现有 `midnight_orange` 深夜蓝橙主题，新增 `arctic_blue` 冰川蓝与 `forest_gold` 松林金；分别面向深色蓝调、冰雪浅灰和秋景石材背景。
- 三主题只改变文字、强调色、尺码牌及底栏配色，不改变固定母版坐标、字号层级、Logo 或四栏结构。未显式指定时按标题区明度和冷暖自动选择。
- Tiguan S 三主题单图及对照图输出到 `assets/outputs/vehicles/volkswagen_tiguan/hero_palette_demos/`；正式 package 未修改。

### 2026-09-30 · Claude Code（灰色无耳首图固定排版母版）
- 按 `data/backgrounds/05_灰色无耳首图_固定排版母版提示词.md` 新增 `src/zontar/hero_template.py`：页头六级文字、橙色俄文条、КОД 尺码牌、右上透明 Logo、四栏功能底栏 + 两行声明全部由代码按参考图 `assets/archive/samples/首图模板.png` 实测坐标叠加；背景明暗自动切换白字/海军蓝字。说明见 `docs/IMAGE_STYLES.md`。
- 用 LADA PRIORA 字段叠在参考图上核对，位置与字宽基本重合。Tiguan 字段表 `data/vehicles/volkswagen_tiguan/inputs/hero.csv`，示例脚本 `pipelines/volkswagen_tiguan/hero_template_demo.py`，S/M 成品和对照图在 `assets/outputs/vehicles/volkswagen_tiguan/hero_template_demos/`；正式 package 未改。
- 待用户确认：M 码俄文条暂写 `ТИГУАН ALLSPACE • КРОССОВЕР`；是否把该母版接入 `render_vehicle` 替换现有主图。规格 md 文件为只读，未修改。

### 2026-09-30 · Codex（Tiguan 再增 10 个背景 demo）
- 用户确认当前背景方向满意后，使用内置 imagegen 新增雪山木屋、海岸悬崖、霜冻白桦林、现代别墅、雾谷、草原湖岸、秋季庄园、石桥河谷、冬季城市广场、松林营地 10 张 1086×1448 纯环境背景。
- 新背景均登记为 `generated/direct`、自动 QA 为 `ok`，等待用户逐张 approve/reject；正式主图未覆盖。
- 以当前 `base_S.png` 锁定车辆、披罩状态和构图，将 10 张纯背景分别合成为车型源图；`background_demo.py` 已扩展为 15 张 demo，并按 5 列 × 3 行生成总览。目视确认 15 张均含车辆、文字无碰撞，版式审计通过。

### 2026-09-30 · Codex（Tiguan 五背景 demo）
- 在背景图库新增秋季石材住宅、霜冻森林、雨后城市公园和初冬河畔四个场景，加上既有冬季湖畔共生成 5 张 1086×1448 纯环境背景；全部登记为 `generated/direct`，自动 QA 为 ok，等待用户 approve/reject。
- 以当前 Tiguan S 披罩源图锁定车型、C01 状态和构图，把 5 个背景分别合成为源照片，再用标准主图渲染器绘制相同标题、Logo、胶囊与底栏。排版审计通过，正式主图未覆盖。
- 新增可重复执行的 `pipelines/volkswagen_tiguan/background_demo.py`，输出 5 张 demo 和横向 contact sheet 到 `assets/outputs/vehicles/volkswagen_tiguan/background_demos/`。

### 2026-09-30 · Codex（Tiguan 对齐 Land Cruiser 主图重量）
- 参考 `LandCruiser_L_主图_1086x1448.png`，把 Tiguan 页头恢复为三条横向信息带；超大双行标题改为 76 px 单行标题，Logo 改为右上 187 px。
- 小/中/大字号调整为 30/50/76 px。年份与尺码胶囊均用 50 px 字体；文字墨迹高度占胶囊高度分别为 53.2% 和 46.7%，落在 44%–58% 验收范围内。
- 视觉重量验收改用 Land Cruiser 同构版式的参考区间；S/M 左右比为 1.875/1.920，重心为 40.8%/40.6%，无碰撞或越界，均通过。新版待用户验收。
- Tiguan 从步骤 10 重跑成功，包与 zip 为 current；Python 编译、`status`、`manifest --check` 通过。`git diff --check` 仅报告项目 CSV 的 CRLF 行尾为尾随空白及既有换行警告。

### 2026-09-30 · Codex（Tiguan 视觉重量平衡验收）
- 缩小并居中品牌 Logo；两行车型标题居中，车型/年份及尺码/说明左右配对，页头统一小 28、中 54、大 150 px 三级字号。
- 启用 `main_title_lines` 的主图增加出图验收：逐元素计算着色面积与亮度对比，页头与底栏分别检查左右比、水平重心及碰撞，并校验实际字号；失败即中止。结果写入 `render_report.json`。
- Pillow 12.3 的字形掩码接口报错已修复。Tiguan 步骤 10 重跑通过；S/M 页头左右比 1.179/1.200、重心 47.1%/47.0%；底栏左右比 1.002、重心 48.9%，均无碰撞。新版仍待用户验收。
- Tiguan 完整流水线、Python 编译与 `manifest --check` 通过；24 个包内文件及 zip 为 current。背景节点当前为 `0/1 ready`，按需生图待办独立于本次主图排版。

### 2026-09-30 · Claude Code（背景生图节点）
- 按 `docs/背景生图节点.md` 新增背景节点：提示词模板 `data/backgrounds/prompt_template.md` + 场景表 `data/backgrounds/scenes.csv`（`winter_lakeside`），库索引 `data/backgrounds.csv`，模块 `src/zontar/backgrounds.py`，CLI `python run.py bg ...`，主题字段 `Theme.background_scene`，`status` 显示 `backgrounds N/M ready` 及待办。
- Tiguan 新增 `pipelines/volkswagen_tiguan/05_background.py` 与 `inputs/backgrounds.csv`（S;M 共用、random、seed 1）；图库为空，已按需生成请求 `bg_winter_lakeside_001`。本机无生图工具，图片尚未生成。
- 沙盒验证：请求、幂等重跑、非 3:4 拒绝、纯白图 QA 报警、1536×2048 裁切缩放、覆盖前备份、approve 后 ready、种子随机选择两次结果一致、reject 后自动换新请求、`toyota_rav4_v6` 无默认场景时报错。
- 顺带修复：沙盒 `ZONTAR_DATA_ROOT` 在仓库外时 `status` 因 `relative_to` 崩溃。
- 正式运行 Tiguan：05 通过；10 因他人进行中的 render.py 改动失败（见工作队列 7），因此未刷新清单，`manifest --check` 显示 archive 有 6 个新备份文件未入清单（同样来自那次改动）。

### 2026-09-30 · Codex（Tiguan 主图留白调整）
- 右上角重排为 Logo、年份说明、加大年份牌和两行俄文产品说明；原左下尺码保留。底栏增加分隔线并放大两行品牌声明。
- 仅启用 `main_title_lines` 的 Tiguan 主图使用此排版；S/M 已重跑并目视确认无文字碰撞。改前主图等已备份到资产归档。

### 2026-09-30 · Codex（Tiguan 完整车身与 C01 掀罩状态）
- 参考 `assets/archive/samples/.../13张首图`，重做 S/M 披罩源图：完整展示车身，改为适中透视，并将掀罩状态命名为 `C01「左垂右提」`，定义写入 `docs/COVER_STATES.md` 与源图提示词 CSV。
- 扩大主图 Logo 与两行车型标题，收紧页头及车身之间的留白；发现首轮橙色车型说明与标题相碰后调整间距并复查。
- Tiguan 仍保持 draft；当前主图 S/M 等待用户验收。
- 目视检查 S/M 完整车身、C01 下摆与大标题无重叠；全流水线、Python 编译、`status`、`manifest --check` 均通过，24 个包内文件及 zip 为 current。

### 2026-09-30 · Codex（Tiguan 车罩开口、透视与主图标题）
- 更新 Tiguan S/M 生图提示词：车罩前缘刚掀过车标，只露靠镜头一侧车灯，另一盏保持覆盖；28–35 mm 近距离前 3/4 透视，车尾可裁切。
- 使用 imagegen 编辑 S/M 披罩源图，覆盖前经 `layout.backup_before_overwrite()` 归档；主图标题改为大号两行，其他车型版式不受影响。
- 重跑 Tiguan 全流水线并刷新包与清单；背景图库的资产布局、授权、随机选图及复现方案记录在 `docs/BACKGROUND_LIBRARY.md`。
- 目视检查 S/M 主图：只见近侧一盏车灯，远侧仍被罩住，车尾出画，标题无溢出；`py_compile`、全流水线、`status`、`manifest --check` 通过。Tiguan 保持 draft。

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
