# Lint 自查记录（data-backup-export）

- 自查时间：2026-10-01
- 自查方式：`python3 scripts/lint.py --src ~/workspace/Operit --dir <单页隔离目录>`（隔离目录只放本页 .md，避免 batch-05 其他在写条目干扰）
- 结果：检查文件 1，硬失败 0，警告 0
- 迭代记录：首轮 0 硬失败 / 1 警告（正文含模糊词"可能"），已改写为确定性表述并复跑，0/0
- 引用核验：facts.json 182 条引用已用独立脚本全量验真（文件存在、行号不越界、断言符号在 ±5 行内），quality.json 13 条 evidence 逐字原文命中
- 禁用词：五个交付文件全文无 watcher 敏感词、无模糊词（可能/大概/似乎/应该/也许）
