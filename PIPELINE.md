# Operit-wiki 全量流水线（7 天并发）

目标：1402 个 kt 文件 100% 读完（扣除停止维护的 mnn/llama/mmd 后 1385 个 / 约 48.2 万行），
按 `outline/outline-v3.yaml` 产出细粒度 wiki 页面。源码版本钉住 `dbf71916`（v1.12.2）。

## 口径

- **严格已读**：整文件 100% 读完，记录进 `tracking/read-status.json`（`record_read.py`），证据为当页的
  `.quality.json` 或 worker 阅读报告。主页进度条只认这个口径。
- **已触及**：被 facts 引用或列为 seed，但无全读记录。派生口径，不存。
- **已审批**：页面状态 approved（用户在评审站确认）。

## 阶段

### Phase 0 — 冻结（已完成）

- `repo-map.json` 基线（3067 文件 / 1402 kt）
- `outline-v3` 打 tag，大纲本体进 Git 跟踪（`outline/outline-v3.yaml`）
- 旧 27 页大纲（outline-v2）降级为历史骨架；batch-01 的 5 页保留为"总览"页，不重做

### Phase 1 — 分片

按 outline-v3 的 `est_lines` 把页面排成 7 个日批次，每批 ~65k 行 / ~18 页。
分片脚本：`scripts/shard_outline.py`（待写）→ `tracking/shards/day-N.json`。
原则：同一子系统尽量同天（critic 可交叉验证）；大页（>12k 行）独占 worker。

### Phase 2 — 阅读（worker 协议）

每个 worker 领一页，按以下协议执行（这是 worker brief 的正文模板）：

1. 把该页全部 seed 文件 100% 读完，不跳读。目录型 seed 要展开到文件逐个确认。
2. `python3 scripts/record_read.py --batch <day-N> --evidence <id>.quality.json --files <清单>` 登记严格已读。
3. 产出 `review/<batch>/<id>.facts.json`（引用铁律：file:line ±5 行，见 SCHEMA.md §2）。
4. 顺手产出 `review/<batch>/<id>.quality.json`（走查轨道，SCHEMA.md §8）。
5. 写正文 `review/<batch>/<id>.md`，跑 `lint.py` 自检到 0 硬失败。
6. 产物全部提交到 wiki 仓库分支，不直接合 main。

### Phase 3 — 独立 critic

每页派与 writer 无关的 critic：逐条核 facts.json 的引用（文件存在、行号有效、±5 行内可见断言），
结论写 `<id>.critic.md`。不通过打回 writer，不许"差不多"。

### Phase 4 — 日终评审（用户）

每天交付一批（~18 页）到评审站：用户在站内逐页看正文 + 抽查 facts，
点"通过"→ 状态 approved。走查发现（quality）在「代码走查」tab 独立逐条审，不阻塞正文。
审批阻塞时：成文暂停，阅读可继续，不堆积待审。

### Phase 5 — 发布

`deploy_site.sh` 一键：重算 coverage（含严格已读）→ 聚合 quality → 部署 gh-pages。
主页进度条、走查 tab、知识图谱同步更新。

### Phase 6 — 持续维护

Operit 仓库有新 commit → 跑 `check_staleness.py`，STALE 页的命中 facts 重核（走 critic）后标回 OK。
与流水线正交，不重置进度。

## 吞吐量估算

- 总量：1385 文件 / 481,930 行；已完成：64 文件 / 39,665 行（8.2%）
- 剩余：1321 文件 / 442,265 行，约 63k 行/天
- 并发：6 worker × ~11k 行/天（含抽取、成文、走查），critic 另起 2-3 并行
- 瓶颈是用户审批速度：建议每天固定时段批 ~18 页，不过夜

## 目录

- 大纲：`outline/outline-v3.yaml`（Git 跟踪，已打 tag）
- 阅读记录：`tracking/read-status.json`（Git 跟踪）
- 分片计划：`tracking/shards/`（流水线启动时生成）
- 机制宪法：`SCHEMA.md`；单页产物规范见 `review/batch-01/` 样例
