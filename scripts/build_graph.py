#!/usr/bin/env python3
"""为 Operit-wiki 生成知识图谱。

流程：
  1. 读取 wiki-work/outline.yaml（24 个规划条目、8 章）与 dep-graph.json
  2. 在 wiki-work/graph-kb/ 暂存一个 llm-wiki 兼容的知识库：
     wiki/topics/<id>.md（条目） + wiki/entities/<module>.md（代码模块）
     边全部由确定性规则生成：
       - 同章条目互链            -> confidence: INFERRED
       - 条目 -> 所属模块实体     -> confidence: EXTRACTED（来自 outline.yaml module 字段）
       - 跨章语义关联（脚本内白名单）-> confidence: INFERRED
       - 模块 -> 模块（dep-graph） -> confidence: EXTRACTED
  3. 调用 vendor/llm-wiki-skill 的 build-graph-data.sh / build-graph-html.sh
     生成离线单文件图谱（数字山水前端）
  4. 拷贝到 site/data/graph/knowledge-graph.html，供 site/graph.html 内嵌

注意：vendor/llm-wiki-skill 为 MIT 协议第三方代码，仅作构建工具使用。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "wiki-work"
def _canonical_outline() -> Path:
    v3 = ROOT / "outline" / "outline-v3.yaml"
    return v3 if v3.exists() else (WORK / "outline.yaml")


OUTLINE = _canonical_outline()
KB = WORK / "graph-kb"
SITE_GRAPH = ROOT / "site" / "data" / "graph"
VENDOR = Path.home() / "workspace" / "vendor" / "llm-wiki-skill"

# 模块统计：来自 wiki-work/modules.md（2026-09-30，repo_map.py 确定性统计）
MODULES = {
    "app": {"files": 1815, "kt": 1362, "symbols": 4961, "note": "主应用模块，占 Kotlin 代码约 97%"},
    "dragonbones": {"files": 14, "kt": 3, "symbols": 11, "note": "Avatar 骨骼动画 native 模块"},
    "mmd": {"files": 78, "kt": 4, "symbols": 8, "note": "Avatar MMD 渲染 native 模块"},
    "fbx": {"files": 10, "kt": 4, "symbols": 12, "note": "Avatar FBX 渲染 native 模块"},
    "mnn": {"files": 21, "kt": 10, "symbols": 10, "note": "端侧推理 native 模块"},
    "llama": {"files": 9, "kt": 3, "symbols": 3, "note": "端侧推理 native 模块"},
    "showerclient": {"files": 14, "kt": 6, "symbols": 11, "note": "Shower 客户端库"},
    "quickjs": {"files": 10, "kt": 4, "symbols": 8, "note": "QuickJS 脚本引擎"},
    "terminal": {"files": 0, "kt": 0, "symbols": 0, "note": "空模块（settings.gradle.kts 注册但无文件）"},
}

# outline.yaml 的 module 字段 -> 实体标题
MODULE_OF = {
    "app": ["模块 app"],
    "llm": ["模块 mnn", "模块 llama"],
    "quickjs": ["模块 quickjs"],
    "showerclient": ["模块 showerclient"],
    "terminal": ["模块 terminal"],
    "unassigned": [],
}

# 跨章语义关联（双向），依据大纲 questions/seed_files 人工整理，确定性白名单
CROSS_LINKS: dict[str, list[str]] = {
    "core-tools": ["data-mcp", "ext-plugins", "core-workflow", "ext-quickjs"],
    "core-chat": ["api-chat", "api-voice", "ui-chat", "core-tools"],
    "core-workflow": ["core-chat"],
    "core-avatar": ["ui-chat"],
    "core-config": ["ui-settings", "api-oauth"],
    "api-chat": ["api-oauth", "mod-showerclient"],
    "api-voice": ["ui-chat"],
    "data-model": ["data-mcp", "data-backup"],
    "data-mcp": ["ext-plugins"],
    "ui-chat": ["ui-floating", "core-avatar"],
    "ui-toolbox": ["ext-plugins", "core-tools"],
    "ui-settings": ["core-config"],
    "ui-floating": ["ui-chat"],
    "ui-misc": ["ui-settings"],
    "ext-quickjs": ["core-tools", "ext-plugins"],
    "ext-plugins": ["data-mcp"],
    "mod-showerclient": ["api-chat"],
    "mod-webchat": ["api-chat", "ui-chat"],
    "appendix-util": ["arch-overview"],
}
# 架构总览页作为各章枢纽
CHAPTER_HUBS = ["core-tools", "api-chat", "data-model", "ui-chat",
                "ext-quickjs", "mod-showerclient", "appendix-util"]


def load_outline() -> dict:
    import yaml
    return yaml.safe_load(OUTLINE.read_text(encoding="utf-8"))


def page_title(pages: dict[str, dict], pid: str) -> str:
    return pages.get(pid, {}).get("title", pid)


def _known(pages: dict[str, dict], ids: list[str]) -> list[str]:
    """只保留大纲中真实存在的 id（v2->v3 换页时旧关联自动失效）。"""
    return [i for i in ids if i in pages]


def link_line(target: str, display: str, conf: str) -> str:
    # llm-wiki 的 wikilink 按文件名解析（不是按 # 标题），用 [[文件名|显示标题]] 写法
    return f"- [[{target}|{display}]] <!-- confidence: {conf} -->"


def write_topic(path: Path, info: dict, pages: dict[str, dict],
                chapter_pages: list[str]) -> None:
    pid = info["id"]
    links: list[tuple[str, str, str]] = []
    # 1. 同章互链（INFERRED）
    for other in chapter_pages:
        if other != pid:
            links.append((other, page_title(pages, other), "INFERRED"))
    # 2. 章节枢纽（INFERRED）
    if pid == "arch-overview":
        for hub in _known(pages, CHAPTER_HUBS):
            links.append((hub, page_title(pages, hub), "INFERRED"))
    # 3. 跨章语义关联（INFERRED）
    for other in _known(pages, CROSS_LINKS.get(pid, [])):
        links.append((other, page_title(pages, other), "INFERRED"))
    # 4. 所属模块实体（EXTRACTED）
    for ent in MODULE_OF.get(info["module"], []):
        mod_name = ent.replace("模块 ", "")
        links.append((mod_name, ent, "EXTRACTED"))
    # core-avatar 额外关联三个 avator native 模块
    if pid == "core-avatar":
        for mod_name in ("dragonbones", "mmd", "fbx"):
            links.append((mod_name, f"模块 {mod_name}", "EXTRACTED"))

    lines = [
        f"# {info['title']}",
        "",
        f"> 状态：规划中｜章节：{info['chapter']}｜模块：{info['module']}"
        f"｜大纲 v1（待人评审，{date.today().isoformat()}）",
        "",
        "## 计划覆盖的问题",
        "",
    ]
    lines += [f"- {q}" for q in info.get("questions", [])]
    lines += ["", "## 种子文件", ""]
    lines += [f"- `{s}`" for s in info.get("seed_files", [])]
    lines += ["", "## 关联条目", ""]
    seen = set()
    for target, display, conf in links:
        if target in seen:
            continue
        seen.add(target)
        lines.append(link_line(target, display, conf))
    lines += [
        "",
        "> 本页为大纲规划占位：正文尚未生成，内容仅来自 outline.yaml 的确定性字段，"
        "未引入任何推测。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_entity(path: Path, name: str, stat: dict, pages: dict[str, dict]) -> None:
    title = f"模块 {name}"
    lines = [
        f"# {title}",
        "",
        "> 来自阶段 0 repo_map.py 确定性统计（wiki-work/modules.md）",
        "",
        f"- 文件数：{stat['files']}（其中 .kt {stat['kt']}）",
        f"- 顶层符号数：{stat['symbols']}",
        f"- 说明：{stat['note']}",
        "",
        "## 关联条目",
        "",
    ]
    for pid, info in pages.items():
        ents = [e.replace("模块 ", "") for e in MODULE_OF.get(info["module"], [])]
        if pid == "core-avatar" and name in ("dragonbones", "mmd", "fbx"):
            ents.append(name)
        if name in ents:
            lines.append(link_line(pid, info["title"], "EXTRACTED"))
    # 模块间依赖：dep-graph 显示 Kotlin 层 import 全部以 app 为起点
    if name != "app":
        lines.append(link_line("app", "模块 app", "EXTRACTED"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def stage_kb(outline: dict) -> tuple[dict[str, dict], int, int]:
    if KB.exists():
        shutil.rmtree(KB)
    topics = KB / "wiki" / "topics"
    entities = KB / "wiki" / "entities"
    topics.mkdir(parents=True)
    entities.mkdir(parents=True)

    (KB / "purpose.md").write_text(
        "# Operit-wiki 知识图谱\n\n> 由 Operit-wiki 大纲 v1 与阶段 0 repo-map "
        "确定性数据生成；节点为规划条目与代码模块，边全部标注置信度。\n",
        encoding="utf-8",
    )

    pages: dict[str, dict] = {}
    chapters: dict[str, list[str]] = {}
    for ch in outline["chapters"]:
        cname = ch["chapter"]
        chapters[cname] = []
        for p in ch["pages"]:
            info = dict(p)
            info["chapter"] = cname
            pages[p["id"]] = info
            chapters[cname].append(p["id"])

    for pid, info in pages.items():
        cname = info["chapter"]
        write_topic(topics / f"{pid}.md", info, pages, chapters[cname])
    for name, stat in MODULES.items():
        write_entity(entities / f"{name}.md", name, stat, pages)

    n_edges = sum(
        1 for pid in pages
        for _ in _known(pages, CROSS_LINKS.get(pid, []))
    )
    return pages, len(pages), len(MODULES)


def run_graph_pipeline() -> Path:
    engine = VENDOR / "packages" / "graph-engine" / "dist" / "engine.iife.js"
    if not engine.exists():
        raise RuntimeError(
            f"图谱引擎未构建：{engine} 不存在，"
            "请先在 vendor/llm-wiki-skill 执行 npm run build -w @llm-wiki/graph-engine"
        )
    scripts = VENDOR / "scripts"
    for script, args in [
        ("build-graph-data.sh", [str(KB)]),
        ("build-graph-html.sh", [str(KB)]),
    ]:
        r = subprocess.run(
            ["bash", str(scripts / script), *args],
            capture_output=True, text=True, timeout=300,
        )
        if r.returncode != 0:
            raise RuntimeError(f"{script} 失败：{r.stderr[-2000:]}")
    html = KB / "wiki" / "knowledge-graph.html"
    if not html.exists():
        raise RuntimeError("knowledge-graph.html 未生成")
    return html


def main() -> int:
    outline = load_outline()
    pages, n_topics, n_entities = stage_kb(outline)
    print(f"暂存知识库：{n_topics} 个条目 + {n_entities} 个模块实体 -> {KB}")

    try:
        html = run_graph_pipeline()
    except RuntimeError as e:
        print(f"WARN: {e}\n跳过图谱构建（保留旧版）。", file=sys.stderr)
        return 2

    SITE_GRAPH.mkdir(parents=True, exist_ok=True)
    dest = SITE_GRAPH / "knowledge-graph.html"
    shutil.copy2(html, dest)

    data = json.loads((KB / "wiki" / "graph-data.json").read_text(encoding="utf-8"))
    ins = data.get("insights", {})
    meta = {
        "built": date.today().isoformat(),
        "nodes": len(data.get("nodes", [])),
        "edges": len(data.get("edges", [])),
        "isolated_nodes": len(ins.get("isolated_nodes", [])),
        "bridge_nodes": len(ins.get("bridge_nodes", [])),
        "source": "outline.yaml v1 + repo-map.json（确定性生成）",
    }
    (SITE_GRAPH / "graph-meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"图谱已生成：{dest}（{meta['nodes']} 节点 / {meta['edges']} 边）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
