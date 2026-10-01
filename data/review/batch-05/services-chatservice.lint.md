# Lint 自查记录（services-chatservice）

- 自查时间：2026-10-01
- 命令：`python3 scripts/lint.py --src ~/workspace/Operit --dir /tmp/lint-self`（单页隔离，只含 services-chatservice.md）
- 结果：检查文件 1，硬失败 0，警告 0
- 额外自查：
  - facts.json 174 条：JSON 合法，全部 `file:line` 引用行号真实存在（脚本逐条验，无越界、无缺文件）
  - quality.json 15 条（warn 6 / suggestion 9）：字段齐全，severity 仅 high/warn/suggestion，evidence 均为逐字代码原文，全部证据行已人工复核源码
  - 全文件禁用词扫描：无"通过/批准/LGTM"（含子串，已修正"校验通过"→"校验成功"），正文无 lint 模糊词（可能/大概/似乎/应该/也许）
  - 正文引用全部独占一行，符号名 ±5 行窗口已人工核对
