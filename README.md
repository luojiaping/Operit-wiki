# Operit-wiki

[![评审大厅](https://img.shields.io/badge/📖-条目评审大厅-E8D5B5?style=flat-square&labelColor=3a3026&color=E8D5B5)](https://luojiaping.github.io/Operit-wiki/)
[![license](https://img.shields.io/badge/MIT-license-5a6e5c?style=flat-square&labelColor=3a3026)](LICENSE)

Operit 的 AI 维护知识库：**既是文档，也是官方答疑的知识源头**。

👉 **评审入口：https://luojiaping.github.io/Operit-wiki/**

- 全部条目由 AI agent 按 [SCHEMA.md](SCHEMA.md) 生成与维护，人只做评审
- 每个事实断言都带 `file:line` 引用，可机器验证
- QQ 群官方答疑机器人从这里取知识，文档和答疑永远是同一份源头

## 评审入口

👉 https://luojiaping.github.io/Operit-wiki/

新条目先进入 `review/` 待评审，在网站上读完、留下评审意见（评论即 GitHub Issue），通过后才合并进 `wiki/`。

## 目录结构

```
Operit-wiki/
├── SCHEMA.md          # 条目规范、引用规则、评审标准（wiki 的宪法）
├── wiki/              # 已发布条目
│   └── index.md       # 内容目录
├── review/            # 待评审条目（按批次）
│   └── <batch-id>/
│       ├── <entry>.md          # 条目正文
│       ├── <entry>.facts.json  # 抽取的事实（每条带 file:line）
│       └── <entry>.lint.md     # 机器 lint 报告
├── review-queue.json  # 评审队列（网站数据源，脚本生成）
├── scripts/           # lint.py、build_queue.py、repo-map 工具
├── site/              # GitHub Pages 网站源码（评审大厅 / Wiki 预览 / 知识图谱）
```

## 工作流

1. Agent 按协议生成条目 → 推到 `review/<批次>/`
2. 每条目自动开一个 `[评审]` Issue，网站展示正文 + facts + lint + critic
3. 评审人在网站评论区留意见（= Issue 评论）
4. Agent 按意见修改、推送更新，网站自动重部署
5. 通过 → 条目移入 `wiki/`，更新 `index.md` + `log.md`，关闭 Issue

## License

MIT
