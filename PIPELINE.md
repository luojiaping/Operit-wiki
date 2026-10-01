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

## 8. 评审站同步铁律（2026-09-30 用户指令，长期有效）

- writer 交付的每个条目必须同步上网页评审：`review/batch-NN/<id>.*` 落盘后，依次跑
  `scripts/build_queue.py` → `scripts/build_wiki_data.py`（由 deploy_site.sh 自动调）→ `scripts/deploy_site.sh`，
  全部成功后才能汇报"已上评审站"。
- 状态唯一来源是各条目的 `<id>.status.json`；**禁止手工改 `review-queue.json`**（每次 deploy 会被 build_queue.py 重建覆盖）。
- 新条目落盘前必须先建 GitHub Issue（label `review`），issue 号写进 `.status.json` 的 `issue` 字段；
  没有 issue 号的条目评论区无处可评，视为未完成同步。
- 同步完成的定义：公网 entry 页能打开、评论区连通到对应 Issue（live browser 实地验证为准，
  不只看本地构建成功）。

## 9. 评审批准自动检测（2026-09-30 用户需求）
- 条目页右侧新增「评审动态」栏：从 GitHub 公开 API 实时读取 Issue 评论数与 owner 最新表态。
- owner 在评论区发表「通过/批准/LGTM」即批准（「不通过/需修改/打回」不算）。
- **批准唯一口径（2026-10-01 用户铁律）：最终是否通过，只以 owner（luojiaping）账号的意见为准；**
  **其他任何人的评论（包括审核人）只作参考，不触发状态翻转。**`watch_reviews.py` 已硬编码按评论作者 login == luojiaping 过滤。
- `scripts/watch_reviews.py` 每 15 分钟由 cron（wiki-review-watcher）运行：检测到新批准评论后自动
  `.status.json` -> approved（含 approved_by_comment_id 水位线，防重复翻转）-> Issue 留言确认
  -> git push -> build_queue.py -> deploy_site.sh。
- 注意：gh 留言用的 token 即 owner 本人身份，bot 留言与 owner 留言无法区分；
  因此 Issue 留言正文禁止出现"通过/批准/LGTM"字样（确认留言已改写），且回炉重写把条目
  打回 review-pending 时，必须把 approved_by_comment_id 重置为当时最新评论 id。
