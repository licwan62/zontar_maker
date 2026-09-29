# AGENTS.md: 给接手此仓库的 AI 编程代理（Codex、Claude Code 等）

本文件是稳定规则。**当前进度、待办和未决问题在 [docs/HANDOFF.md](docs/HANDOFF.md)**。人类可读的完整说明在 [README.md](README.md)。

## 每次开工

1. `python run.py status`：查看每个车型已完成什么、缺什么、下一步是什么（只读，几秒完成）。
2. 读 `docs/HANDOFF.md` 的“工作队列”和“待用户决定”。
3. `git log --oneline -10` 与 `git status`：确认从哪里接手。

## 环境

- Windows + Python ≥ 3.11，依赖只有 `pillow`、`openpyxl`。**不需要** `pip install`：`python run.py <命令>` 会自动把 `src/` 加进路径。
- 字体取 `C:\Windows\Fonts`（arial、arialbd、ariblk、impact、tahoma、tahomabd）。其他系统用环境变量 `ZONTAR_FONT_DIR` 指向含这些字体的目录。
- `pipelines/*/*.mjs` 需要 Node 和 `@oai/artifact-tool`，本机没有。`run.py` 会自动跳过并提示，不要尝试从网上安装替代品。
- 终端输出含中文和俄文：子进程已设 `PYTHONIOENCODING=utf-8`；自己写脚本时也要 `sys.stdout.reconfigure(encoding="utf-8")`。

## 常用命令

```
python run.py status                         # 状态与下一步
python run.py styles                         # 可选套图主题及参考图
python run.py run <slug>                     # 依次跑 pipelines/<slug>/NN_*，再打包 + 刷新清单
python run.py run <slug> --from 10           # 从某一步继续
python run.py doctor                         # 检查输入、字体、远端配置
python run.py manifest --check               # 资产清单是否与本地一致（非零退出 = 需要 python run.py manifest）
python run.py pack <slug>                    # 只重新打包（确定性 zip，同内容同字节）
python run.py tables convert <asset-key> <data 子目录>   # xlsx -> CSV
python run.py paths --vehicle <slug> --json  # 解析后的所有路径
```

## 目录与存储（摘要）

- git：`src/zontar/`（共享库）、`pipelines/<slug>/NN_*`（按序号执行的步骤）、`data/`（**所有表格，一律 CSV**）、`manifests/`（资产 sha256 清单）、`docs/`。
- `assets/`（gitignore，将来在 NAS/OSS）：`inputs/`（品牌、分类图库、车型源图、原始 xlsx）、`outputs/vehicles/<slug>/package|dist`、`archive/`。
- 路径一律通过 `zontar.layout`（Python）或 `pipelines/_shared/paths.mjs`（Node）取得，不要写死路径或假设当前工作目录。
- 车型注册表 `data/vehicles.csv`：`status` 为 `delivered` 的车型已交付。

## 硬性规则

1. **不把二进制放进 git**（png/jpg/zip/xlsx）。表格转 CSV 用 `zontar.tables.write_csv`（UTF-8 BOM、CRLF 行尾）。
2. **不原地重跑已交付车型**（`run.py` 会拒绝）。要验证它们，用沙盒：把 `assets/inputs` 相关部分和 `data/` 复制到临时目录，设置 `ZONTAR_ASSET_ROOT`、`ZONTAR_DATA_ROOT` 后再运行，然后和正式输出逐像素比较。
3. **只移动或新增，不删除**资产。需要覆盖图片时先调用 `layout.backup_before_overwrite()`。
4. 改动 `assets/` 后运行 `python run.py manifest`，并把 `manifests/*.csv` 的变化一并提交。
5. 上架文案：俄文标题 ≤ 200 字符；标签唯一、每个 ≤ 30 字符、每个 SKU ≤ 30 个；只写允许的功能表述（普通雨雪、灰尘、阳光、落叶），不写 100% 防水、保温、抗冰雹等。产品事实见 `docs/prompts/01_完整执行总提示词.md`。
6. 网络图片的版权规则见 `docs/agents/vehicle-image-scout.md`：授权不明一律只作参照（reference_only），不得直接用于上架图。
7. 不推送、不连接远端存储、不上传到外部服务，除非用户明确要求。提交信息写清楚改了哪个车型或模块。

## 收工前

- `python run.py status` 与 `python run.py manifest --check` 均无意外。
- 改过的 Python 文件能 `python -m py_compile` 通过；改过哪个车型就 `python run.py run <slug>`（已交付车型用沙盒）。
- **更新 `docs/HANDOFF.md`**：完成了什么、验证结果、下一步、新增的待决问题。这是下一个接手者（人或代理）唯一需要读的进度记录。

## 专项任务说明

- 新增车型：README“新增车型”一节，范例 `pipelines/volkswagen_tiguan/`。
- 联网找车型图片：`docs/agents/vehicle-image-scout.md`（需要联网；Codex 需开启网络搜索，例如以 `codex --search` 启动）。
