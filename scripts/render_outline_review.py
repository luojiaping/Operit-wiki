#!/usr/bin/env python3
"""从 wiki-work/outline.yaml 确定性渲染 review/batch-00/outline.md。

v2 起评审正文不再手写，避免与 outline.yaml 脱节。
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "review" / "batch-00" / "outline.md"


def main() -> None:
    d = yaml.safe_load((ROOT / "wiki-work" / "outline.yaml").read_text(encoding="utf-8"))
    chapters = d["chapters"]
    total = sum(len(c["pages"]) for c in chapters)
    ver = d.get("version", "?")

    L: list[str] = []
    is_approved = bool(d.get("approved"))
    L.append("---")
    L.append(f"title: Operit-wiki 大纲（{'定稿' if is_approved else '草案'}）")
    L.append("module: meta")
    L.append("sources: [repo-map.json, dep-graph.json, modules.md, outline.yaml]")
    L.append("date: 2026-09-30")
    L.append("---")
    L.append("")
    L.append(f"# Operit-wiki 大纲（{'定稿' if is_approved else '草案'} v{ver}）")
    L.append("")
    if is_approved:
        L.append(f"> 状态：已批准（{d['approved']}，用户评审通过，git tag `outline-v2`）。mnn/llama/mmd 等端侧推理模块已停止维护，不再覆盖。")
        L.append("")
    L.append("> 生成依据：阶段 0 确定性脚本统计（`scripts/repo_map.py`）+ 人工通读仓库补遗，全部数字来自实际扫描，未做推测。")
    L.append("> 仓库事实：**app 模块占 1362/1402 个 kt 文件、4961/5039 个符号**，是绝对主体；其余 8 个模块合计 40 个 kt 文件。")
    L.append("> terminal 模块代码在独立仓库 `AAswordman/OperitTerminalCore`（47 kt），主仓库 settings 仅注册 `:terminal`。")
    L.append("")
    L.append(f"## 章节与页面（共 {total} 页）")
    L.append("")
    n = 0
    for c in chapters:
        L.append(f"### {c['chapter']}")
        for p in c["pages"]:
            n += 1
            qs = "；".join(p.get("questions", [])[:2])
            L.append(f"{n}. **{p['title']}** —— {qs}")
        L.append("")
    L.append("## 请你重点评审")
    L.append("")
    L.append("1. 章节切分是否合理？有没有漏掉你关心的部分？")
    L.append("2. v2 新增的 4 页（记忆系统、角色卡与人设、应用包编辑、系统集成）粒度合适吗？")
    L.append("3. `terminal` 现已确认为独立仓库 `AAswordman/OperitTerminalCore`，说明页这样写可以吗？")
    L.append("4. `ui/features` 下 21 个功能目录合并为 5 页，粒度合适吗？")
    L.append("5. 以下模块职责脚本找不到出处，标了\"未知，需人工确认\"，你方便各补一句话吗：**app、mnn、llama、mmd、fbx**")
    L.append("")
    L.append("## 来源")
    L.append("")
    L.append("- `wiki-work/repo-map.json`（3067 文件 / 1402 kt / 5039 顶层符号，零声明文件 0%）")
    L.append("- `wiki-work/dep-graph.json`（8 条模块依赖边，全部以 app 为起点）")
    L.append("- `wiki-work/modules.md`")
    L.append("- `~/workspace/Operit/Repo_Arch_Basic.md`、`README.md`（项目介绍原文引用）")
    L.append("- `AAswordman/OperitTerminalCore` 的 README（终端模块职责原文）")
    L.append("- `AAswordman/OperitWeb/docs/`（插件市场接口、审核规范、拒绝名单、GitHub OAuth Broker）")
    L.append("")
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT} ({total} pages)")


if __name__ == "__main__":
    main()
