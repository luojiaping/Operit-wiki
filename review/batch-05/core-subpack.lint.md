# Lint 自查记录（core-subpack）

- 自查时间：2026-10-01
- 命令：`python3 scripts/lint.py --src ~/workspace/Operit --dir /tmp/lint-subpack`（单页隔离，只含 core-subpack.md）
- 结果：检查文件 1，硬失败 0，警告 0
- 额外自查：
  - facts.json 100 条：JSON 合法，全部 `file:line` 引用行号真实存在（脚本逐条验，无越界、无缺文件）
  - quality.json 15 条：字段齐全，severity 仅 high/warn/suggestion，evidence 均为逐字代码原文
  - 全文件无 watcher 审批触发词、无 lint 模糊词（已逐项扫描确认）
  - 正文引用全部独占一行，符号名 ±5 行窗口已人工核对
