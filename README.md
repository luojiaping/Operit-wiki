# Operit-wiki

Operit 的知识库：**既是正式 wiki 站，也是 AI 答疑的知识源头**。

[![Wiki](https://img.shields.io/badge/📖-Operit_Wiki-E8D5B5?style=flat-square&labelColor=3a3026&color=E8D5B5)](https://luojiaping.github.io/Operit-wiki)
[![license](https://img.shields.io/badge/MIT-license-5a6e5c?style=flat-square&labelColor=3a3026)](LICENSE)

👉 **在线阅读：https://luojiaping.github.io/Operit-wiki**

- 123 个知识页面，全部条目由 AI agent 按 [SCHEMA.md](SCHEMA.md) 生成与维护
- 每个事实断言都带 `file:line` 引用，可机器验证
- QQ 群官方答疑机器人从这里取知识，文档和答疑永远是同一份源头

## AI 使用（推荐：拉到本地）

```bash
git clone https://github.com/luojiaping/Operit-wiki.git
```

1. 先读 `AGENTS.md`（入口，一页纸）
2. 完整检索协议见 `wiki/AI_USAGE.md`：索引 → grep → 限量精读 → facts 引用
3. 条目索引：`review-queue.json`（id / 标题 / 模块）
4. 条目正文：`review/<批次>/<id>.md`，原子事实：同名 `.facts.json`

不许把页面打碎做向量切块 / embedding 检索；wiki 没写的就说没写。

## 参与：提交改动与意见

- **内容勘误 / 补充 / 意见**：直接在 [GitHub 提 Issue](https://github.com/luojiaping/Operit-wiki/issues/new)，注明页面标题和正确内容（代码类请带源码 `file:line`）。
- **评审中的条目**：每条目有专属 `[评审]` Issue，在网站条目页评论区留言即同步到 Issue；评论"通过"即批准。
- **教程投稿**：用仓库的 tutorial Issue 模板投稿，通过审核（`tutorial-approved` 标签）后自动收录进网站教程区。
- **直接改代码 / 网站**：欢迎提 PR（MIT 协议）；网站改动请先跑 `python3 scripts/build_queue.py` 验证构建。

## 目录结构

```
Operit-wiki/
├── AGENTS.md          # AI 入口：怎么用这个仓库（一页纸）
├── wiki/AI_USAGE.md   # AI 检索协议全文（索引→grep→限量精读→引用铁律）
├── review-queue.json  # 全库索引（id / 标题 / 模块 / 状态）
├── review/            # 全部条目正文（按批次）
│   └── <batch-id>/
│       ├── <entry>.md          # 条目正文
│       ├── <entry>.facts.json  # 原子事实（每条带 file:line）
│       └── <entry>.status.json # 状态（approved / review-pending）
├── site/              # 网站源码（正式 wiki / 知识图谱 / 教程分享）
├── scripts/           # lint、构建、部署工具
└── SCHEMA.md          # 条目规范（wiki 的宪法）
```

## 工作流（维护者）

1. Agent 按协议生成条目 → 推到 `review/<批次>/`
2. 每条目自动开一个 `[评审]` Issue，网站条目页展示正文 + facts + lint
3. 评审人在评论区留意见（= Issue 评论），约 15 分钟自动同步状态
4. 通过 → 状态翻 `approved`，正式 wiki 站自动收录

## License

MIT
